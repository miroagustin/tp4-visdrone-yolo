"""Configuración, ejecución y artefactos de experimentos."""
from __future__ import annotations

import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .data import smoke_yaml


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_config(root: Path | None = None) -> dict:
    root = root or project_root()
    return yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))


def resolve(root: Path, profile: str, *, batch: int | None = None, imgsz: int | None = None, use_yolo26: bool | None = None) -> dict:
    config = load_config(root)
    if profile not in ("smoke", "full", "presentation"):
        raise ValueError(profile)
    data_dir = (root / config["data_dir"]).resolve()
    runs_dir = (root / config["runs_dir"]).resolve()
    result = {**config, **config["profiles"][profile], "profile": profile, "data_dir": str(data_dir), "runs_dir": str(runs_dir)}
    selected = config.get("use_yolo26", True) if use_yolo26 is None else use_yolo26
    if not isinstance(selected, bool):
        raise ValueError("use_yolo26 debe ser true o false")
    result["use_yolo26"] = selected
    result["pretrained"] = config.get("pretrained", True)
    result["model"] = ("yolo26n" if selected else "yolo11n") + (".pt" if result["pretrained"] else ".yaml")
    if batch is not None:
        result["batch"] = batch
    if imgsz is not None:
        result["imgsz"] = imgsz
    result.pop("profiles")
    if profile == "smoke":
        result["data_yaml"] = str(smoke_yaml(data_dir, result["seed"], result["train_images"], result["val_images"]))
    elif profile == "full":
        result["data_yaml"] = str(data_dir / "visdrone.yaml")
    return result


def training_settings(root: Path, profile: str, *, batch=None, imgsz=None, use_yolo26=None, resume=None):
    """En reanudación, conservar el protocolo del run, no el nuevo predeterminado."""
    if resume is None:
        return resolve(root, profile, batch=batch, imgsz=imgsz, use_yolo26=use_yolo26), None
    if any(value is not None for value in (batch, imgsz, use_yolo26)):
        raise ValueError("--resume conserva la configuración original; no combinar con --batch, --imgsz ni flags de modelo.")
    checkpoint = Path(resume).resolve()
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    run = checkpoint.parents[2]
    settings = json.loads((run / "run.json").read_text(encoding="utf-8"))["settings"]
    if settings["profile"] != profile:
        raise ValueError(f"El checkpoint pertenece al perfil {settings['profile']}, no a {profile}")
    return settings, run


def device_or_raise(requested="auto") -> str:
    import torch
    available = torch.cuda.is_available()
    if not available:
        raise RuntimeError("CUDA no está disponible. Se bloqueó el entrenamiento en CPU. Revisá torch y el driver; la exploración y presentación sí pueden correr en CPU.")
    if requested not in ("auto", "cuda", "cuda:0", "0"):
        raise ValueError(f"Dispositivo no admitido para entrenar: {requested}")
    test = torch.ones((32, 32), device="cuda") @ torch.ones((32, 32), device="cuda")
    torch.cuda.synchronize()
    assert float(test[0, 0]) == 32.0
    return "0"


def versions() -> dict:
    import torch
    import ultralytics
    import torchvision
    return {"python": platform.python_version(), "system": platform.platform(), "torch": torch.__version__, "torchvision": torchvision.__version__, "torch_cuda": torch.version.cuda, "ultralytics": ultralytics.__version__, "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}


def start_run(root: Path, profile: str, settings: dict) -> Path:
    runs = Path(settings["runs_dir"])
    runs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = runs / profile / stamp
    path.mkdir(parents=True, exist_ok=False)
    (path / "run.json").write_text(json.dumps({"settings": settings, "versions": versions(), "started_utc": stamp, "status": "running"}, indent=2), encoding="utf-8")
    return path


def finish_run(path: Path, *, elapsed: float, metrics=None, error=None) -> dict:
    manifest = path / "run.json"
    info = json.loads(manifest.read_text(encoding="utf-8"))
    info.update({"elapsed_seconds": elapsed, "status": "failed" if error else "finished", "error": str(error) if error else None})
    if metrics is not None:
        info["metrics"] = metrics
    manifest.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    return info


def metrics_dict(results) -> dict:
    names = results.names
    box = results.box
    per_class = {}
    for i, cls in enumerate(box.ap_class_index):
        p, r, ap50, ap = box.class_result(i)
        per_class[str(names[int(cls)])] = {"precision": float(p), "recall": float(r), "map50": float(ap50), "map50_95": float(ap)}
    return {"precision": float(box.mp), "recall": float(box.mr), "map50": float(box.map50), "map50_95": float(box.map), "per_class": per_class, "evaluator": "Ultralytics; no es el evaluador oficial de VisDrone"}


def train(root: Path, profile="smoke", *, batch=None, imgsz=None, use_yolo26=None, resume: Path | None = None) -> Path:
    root = root.resolve()
    settings, resumed_run = training_settings(root, profile, batch=batch, imgsz=imgsz, use_yolo26=use_yolo26, resume=resume)
    import ultralytics.utils as ultralytics_utils
    from ultralytics import YOLO
    ultralytics_utils.WEIGHTS_DIR = root / "weights"
    ultralytics_utils.WEIGHTS_DIR.mkdir(exist_ok=True)
    device = device_or_raise(settings["device"])
    path = resumed_run if resumed_run is not None else start_run(root, profile, settings)
    model = YOLO(str(resume) if resume else settings["model"])
    began = time.perf_counter()
    try:
        from .epoch_preview import attach_epoch_preview
        attach_epoch_preview(model, settings, path)
        model.train(data=settings["data_yaml"], epochs=settings["epochs"], patience=settings.get("patience", 100), imgsz=settings["imgsz"], batch=settings["batch"], workers=settings["workers"], seed=settings["seed"], device=device, project=str(path), name="train", exist_ok=True, plots=True, pretrained=settings.get("pretrained", True), resume=bool(resume))
        best = path / "train" / "weights" / "best.pt"
        if not best.exists():
            raise RuntimeError(f"No se creó {best}")
        val = YOLO(str(best)).val(data=settings["data_yaml"], split="val", imgsz=settings["imgsz"], batch=settings["batch"], workers=settings["workers"], device=device, project=str(path), name="validation", exist_ok=True, plots=True)
        finish_run(path, elapsed=time.perf_counter()-began, metrics=metrics_dict(val))
    except Exception as exc:
        finish_run(path, elapsed=time.perf_counter()-began, error=exc)
        raise
    return path


def evaluate_test(run: Path, data_yaml: Path) -> dict:
    from ultralytics import YOLO
    settings = json.loads((run / "run.json").read_text(encoding="utf-8"))["settings"]
    result = YOLO(str(run / "train" / "weights" / "best.pt")).val(data=str(data_yaml), split="test", imgsz=settings["imgsz"], batch=settings["batch"], workers=settings["workers"], device=device_or_raise(), project=str(run), name="test_dev", exist_ok=True, plots=True)
    metrics = metrics_dict(result)
    (run / "test_dev.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def latest_run(root: Path, profile="full") -> Path | None:
    dirs = sorted((root / "runs" / profile).glob("*/run.json"))
    finished = [p.parent for p in dirs if json.loads(p.read_text(encoding="utf-8")).get("status") == "finished"]
    return finished[-1] if finished else None
