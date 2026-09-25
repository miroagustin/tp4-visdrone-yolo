"""Gráficos de auditoría, revisión visual y presentación autónoma."""
from __future__ import annotations

import base64
import html
import json
from pathlib import Path


def review_boxes(data_dir: Path, split="val", count=3, output: Path | None = None) -> Path:
    from PIL import Image, ImageDraw
    from .data import CLASSES
    import matplotlib.pyplot as plt
    images = sorted((data_dir / "yolo" / "images" / split).glob("*.jpg"))[:count]
    if not images:
        raise FileNotFoundError(f"Sin imágenes en {split}")
    fig, axes = plt.subplots(1, len(images), figsize=(7 * len(images), 6))
    if len(images) == 1:
        axes = [axes]
    for ax, image in zip(axes, images):
        picture = Image.open(image).convert("RGB")
        draw = ImageDraw.Draw(picture)
        w, h = picture.size
        labels = data_dir / "yolo" / "labels" / split / f"{image.stem}.txt"
        for row in labels.read_text(encoding="utf-8").splitlines():
            c, xc, yc, bw, bh = map(float, row.split())
            x1, y1, x2, y2 = (xc-bw/2)*w, (yc-bh/2)*h, (xc+bw/2)*w, (yc+bh/2)*h
            draw.rectangle((x1, y1, x2, y2), outline="yellow", width=2)
            draw.text((x1, max(0, y1-10)), CLASSES[int(c)], fill="yellow")
        ax.imshow(picture)
        ax.set_title(image.name)
        ax.axis("off")
    fig.tight_layout()
    output = output or data_dir / "box_review.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=130)
    plt.close(fig)
    return output


def audit_plot(data_dir: Path, output: Path | None = None) -> Path:
    import matplotlib.pyplot as plt
    from .data import CLASSES
    info = json.loads((data_dir / "audit.json").read_text(encoding="utf-8"))
    counts = [info["train"]["class_counts"].get(name, 0) for name in CLASSES]
    areas = info["train"]["relative_box_areas"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].barh(CLASSES, counts)
    axes[0].set_xscale("log")
    axes[0].set_title("Cajas por clase · train")
    axes[1].hist(areas, bins=50, range=(0, min(.05, max(areas) if areas else .05)))
    axes[1].set_xlabel("Área de caja / área de imagen")
    axes[1].set_title("Tamaños relativos · train")
    fig.tight_layout()
    output = output or data_dir / "audit.png"
    fig.savefig(output, dpi=130)
    plt.close(fig)
    return output


def error_gallery(root: Path, run: Path, *, limit=8) -> dict:
    """Audita una muestra de validación con IoU 0.5 y guarda ejemplos FP/FN."""
    from PIL import Image, ImageDraw
    from ultralytics import YOLO
    import torch
    data = root / "data" / "yolo"
    settings = json.loads((run / "run.json").read_text(encoding="utf-8"))["settings"]
    if settings["profile"] == "smoke":
        images = [Path(line) for line in (root / "data" / "smoke_val.txt").read_text(encoding="utf-8").splitlines()[:limit]]
    else:
        images = sorted((data / "images" / "val").glob("*.jpg"))[:limit]
    if not images:
        raise FileNotFoundError("Faltan imágenes de validación")
    detector = YOLO(str(run / "train" / "weights" / "best.pt"))
    panels = []
    summary = {"images": len(images), "tp": 0, "fp": 0, "fn": 0, "iou": .5, "confidence": .25}

    def iou(a, b):
        left, top, right, bottom = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
        intersection = max(0, right-left) * max(0, bottom-top)
        area_a = max(0, a[2]-a[0]) * max(0, a[3]-a[1])
        area_b = max(0, b[2]-b[0]) * max(0, b[3]-b[1])
        union = area_a + area_b - intersection
        return intersection / union if union else 0

    for path in images:
        picture = Image.open(path).convert("RGB")
        w, h = picture.size
        truth = []
        for line in (data / "labels" / "val" / f"{path.stem}.txt").read_text(encoding="utf-8").splitlines():
            cls, xc, yc, bw, bh = map(float, line.split())
            truth.append((int(cls), ((xc-bw/2)*w, (yc-bh/2)*h, (xc+bw/2)*w, (yc+bh/2)*h)))
        result = detector.predict(str(path), imgsz=settings["imgsz"], conf=.25, device="0" if torch.cuda.is_available() else "cpu", verbose=False)[0]
        predicted = [(int(c), tuple(map(float, box))) for c, box in zip(result.boxes.cls.tolist(), result.boxes.xyxy.tolist())]
        matched = set()
        fp = []
        for cls, box in predicted:
            options = [(iou(box, real), index) for index, (real_cls, real) in enumerate(truth) if real_cls == cls and index not in matched]
            best = max(options, default=(0, -1))
            if best[0] >= .5:
                matched.add(best[1])
            else:
                fp.append(box)
        fn = [box for index, (_, box) in enumerate(truth) if index not in matched]
        summary["tp"] += len(matched)
        summary["fp"] += len(fp)
        summary["fn"] += len(fn)
        draw = ImageDraw.Draw(picture)
        for box in fn:
            draw.rectangle(box, outline="#ff5252", width=3)
        for box in fp:
            draw.rectangle(box, outline="#48d9ff", width=3)
        picture.thumbnail((720, 460))
        panel = Image.new("RGB", (740, 500), "#13283a")
        panel.paste(picture, ((740-picture.width)//2, 30))
        ImageDraw.Draw(panel).text((15, 8), f"{path.name} · FP {len(fp)} · FN {len(fn)}", fill="white")
        panels.append(panel)
    gallery = Image.new("RGB", (1480, 500 * ((len(panels)+1)//2)), "#13283a")
    for i, panel in enumerate(panels):
        gallery.paste(panel, ((i%2)*740, (i//2)*500))
    output = run / "error_gallery.jpg"
    gallery.save(output, quality=88)
    summary["note"] = "Auditoría de muestra, no métrica oficial ni de todo val. Rojo=FN; cian=FP."
    (run / "error_sample.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def measure_latency(root: Path, run: Path, *, warmup=5, repeats=20) -> dict:
    """Tiempo total por imagen (preprocesado + inferencia + postprocesado)."""
    import time
    import torch
    from ultralytics import YOLO
    sample = next((root / "data" / "yolo" / "images" / "val").glob("*.jpg"))
    settings = json.loads((run / "run.json").read_text(encoding="utf-8"))["settings"]
    device = "0" if torch.cuda.is_available() else "cpu"
    detector = YOLO(str(run / "train" / "weights" / "best.pt"))
    for _ in range(warmup):
        detector.predict(str(sample), imgsz=settings["imgsz"], device=device, verbose=False)
    if device == "0":
        torch.cuda.synchronize()
    begin = time.perf_counter()
    for _ in range(repeats):
        detector.predict(str(sample), imgsz=settings["imgsz"], device=device, verbose=False)
    if device == "0":
        torch.cuda.synchronize()
    result = {"ms_per_image": (time.perf_counter()-begin)*1000/repeats, "gpu": torch.cuda.get_device_name(0) if device == "0" else None, "device": device, "imgsz": settings["imgsz"], "batch": 1, "warmup": warmup, "repeats": repeats, "scope": "predict completo, una imagen repetida"}
    (run / "latency.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def image_data(path: Path) -> str:
    mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def presentation(root: Path, run: Path | None = None, output: Path | None = None) -> Path:
    """Exporta el recorrido del notebook desde un kernel limpio, sin entrenar."""
    from .notebook_export import export
    return export(root, run, output)
