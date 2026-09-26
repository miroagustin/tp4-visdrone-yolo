"""Clases de la misión (persona y vehículo) y evaluación agrupada sin reentrenar.

El detector conserva sus 10 clases VisDrone; predicciones y etiquetas se reagrupan después
de la inferencia. El emparejamiento y el AP replican al validador de Ultralytics para que la
variante de 10 clases reproduzca las métricas registradas en run.json.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from .data import CLASSES

MISSION_GROUPS = {
    "persona": ("pedestrian", "people"),
    # Bicicletas y motos son vehículos; quien las conduce está anotado aparte como "people".
    "vehiculo": ("car", "van", "truck", "bus", "tricycle", "awning-tricycle", "bicycle", "motor"),
}
MISSION_CLASSES = tuple(MISSION_GROUPS)
TO_MISSION = np.array([next(i for i, members in enumerate(MISSION_GROUPS.values()) if name in members) for name in CLASSES])
IOUV = np.linspace(0.5, 0.95, 10)
CONF_GRID = (0.05, 0.1, 0.15, 0.25, 0.4, 0.5)
# Lado equivalente sqrt(w*h) de cada objeto medido en la entrada de la red, en píxeles.
SIZE_EDGES = (0, 4, 8, 16, 32, float("inf"))
SIZE_LABELS = ("<4", "4-8", "8-16", "16-32", ">=32")


def box_iou(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """IoU entre cajas xyxy: (N, 4) x (M, 4) -> (N, M)."""
    if not len(a) or not len(b):
        return np.zeros((len(a), len(b)))
    lt = np.maximum(a[:, None, :2], b[None, :, :2])
    rb = np.minimum(a[:, None, 2:], b[None, :, 2:])
    inter = np.clip(rb - lt, 0, None).prod(2)
    area_a = (a[:, 2:] - a[:, :2]).prod(1)
    area_b = (b[:, 2:] - b[:, :2]).prod(1)
    return inter / (area_a[:, None] + area_b[None, :] - inter + 1e-7)


def match_pairs(iou: np.ndarray, pred_cls: np.ndarray, gt_cls: np.ndarray, threshold: float) -> np.ndarray:
    """Pares (etiqueta, detección) como BaseValidator.match_predictions sin scipy."""
    iou = iou * (gt_cls[:, None] == pred_cls[None, :])
    matches = np.argwhere(iou >= threshold)
    if len(matches) > 1:
        matches = matches[iou[matches[:, 0], matches[:, 1]].argsort()[::-1]]
        matches = matches[np.unique(matches[:, 1], return_index=True)[1]]
        matches = matches[np.unique(matches[:, 0], return_index=True)[1]]
    return matches.reshape(-1, 2)


def merge_duplicates(boxes: np.ndarray, conf: np.ndarray, cls: np.ndarray, iou: float) -> np.ndarray:
    """Índices que sobreviven a un NMS por grupo: une, p. ej., car y van sobre el mismo objeto."""
    if not len(boxes):
        return np.zeros(0, dtype=int)
    import torch
    from torchvision.ops import batched_nms
    keep = batched_nms(torch.from_numpy(boxes).float(), torch.from_numpy(conf).float(), torch.from_numpy(cls).long(), iou)
    return np.sort(keep.numpy())


def size_bins(sides: np.ndarray) -> np.ndarray:
    return np.digitize(sides, SIZE_EDGES[1:-1], right=False)


class Stats:
    """Acumula detecciones de una taxonomía para AP y para puntos de operación."""

    def __init__(self, names, conf_grid=CONF_GRID):
        self.names = tuple(names)
        self.grid = tuple(conf_grid)
        nc, nb = len(self.names), len(SIZE_LABELS)
        self.tp, self.conf, self.pred_cls, self.target_cls = [], [], [], []
        self.op_tp = np.zeros((len(self.grid), nc), dtype=int)
        self.op_kept = np.zeros((len(self.grid), nc), dtype=int)
        self.gt_total = np.zeros((nc, nb), dtype=int)
        self.gt_hit = np.zeros((len(self.grid), nc, nb), dtype=int)

    def add(self, pred_boxes, conf, pred_cls, gt_boxes, gt_cls, gt_bins):
        iou = box_iou(gt_boxes, pred_boxes)
        correct = np.zeros((len(pred_cls), len(IOUV)), dtype=bool)
        for i, threshold in enumerate(IOUV):
            pairs = match_pairs(iou, pred_cls, gt_cls, threshold)
            correct[pairs[:, 1], i] = True
        self.tp.append(correct)
        self.conf.append(conf)
        self.pred_cls.append(pred_cls)
        self.target_cls.append(gt_cls)
        np.add.at(self.gt_total, (gt_cls, gt_bins), 1)
        for k, threshold in enumerate(self.grid):
            kept = np.flatnonzero(conf >= threshold)
            pairs = match_pairs(iou[:, kept], pred_cls[kept], gt_cls, 0.5)
            np.add.at(self.op_kept[k], pred_cls[kept], 1)
            np.add.at(self.op_tp[k], pred_cls[kept[pairs[:, 1]]], 1)
            np.add.at(self.gt_hit[k], (gt_cls[pairs[:, 0]], gt_bins[pairs[:, 0]]), 1)

    def summary(self) -> dict:
        from ultralytics.utils.metrics import ap_per_class
        tp = np.concatenate(self.tp) if self.tp else np.zeros((0, len(IOUV)), dtype=bool)
        conf, pred_cls, target_cls = (np.concatenate(x) if x else np.zeros(0) for x in (self.conf, self.pred_cls, self.target_cls))
        per_class = {name: {"objects": int(self.gt_total[i].sum())} for i, name in enumerate(self.names)}
        map50 = map50_95 = 0.0
        if len(target_cls):
            result = ap_per_class(tp, conf, pred_cls, target_cls)
            ap, classes = result[5], result[6]
            for row, c in zip(ap, classes):
                per_class[self.names[int(c)]].update({"ap50": float(row[0]), "ap50_95": float(row.mean())})
            map50, map50_95 = float(ap[:, 0].mean()), float(ap.mean())
        operating = []
        for k, threshold in enumerate(self.grid):
            tp_k, kept_k = self.op_tp[k], self.op_kept[k]
            hits, totals = self.gt_hit[k].sum(1), self.gt_total.sum(1)
            classes = {name: {"precision": _ratio(tp_k[i], kept_k[i]), "recall": _ratio(hits[i], totals[i]), "tp": int(tp_k[i]), "fp": int(kept_k[i] - tp_k[i]), "fn": int(totals[i] - hits[i])} for i, name in enumerate(self.names)}
            overall = {"precision": _ratio(tp_k.sum(), kept_k.sum()), "recall": _ratio(hits.sum(), totals.sum())}
            by_size = {name: {label: {"objects": int(self.gt_total[i, b]), "recall": _ratio(self.gt_hit[k, i, b], self.gt_total[i, b])} for b, label in enumerate(SIZE_LABELS)} for i, name in enumerate(self.names)}
            operating.append({"conf": threshold, "iou": 0.5, "all_objects": overall, "per_class": classes, "recall_by_size": by_size})
        return {"classes": list(self.names), "map50": map50, "map50_95": map50_95, "per_class": per_class, "operating_points": operating}


def _ratio(a, b):
    return float(a / b) if b else None


def evaluate_samples(samples, *, merge_iou=0.7, conf_grid=CONF_GRID) -> dict:
    """samples: (pred_boxes, conf, pred_cls10, gt_boxes, gt_cls10, gt_side_px) por imagen."""
    variants = {"visdrone10": Stats(CLASSES, conf_grid), "mision": Stats(MISSION_CLASSES, conf_grid), "mision_fusion": Stats(MISSION_CLASSES, conf_grid)}
    for boxes, conf, cls, gt_boxes, gt_cls, sides in samples:
        bins = size_bins(sides)
        variants["visdrone10"].add(boxes, conf, cls, gt_boxes, gt_cls, bins)
        grouped, gt_grouped = TO_MISSION[cls], TO_MISSION[gt_cls]
        variants["mision"].add(boxes, conf, grouped, gt_boxes, gt_grouped, bins)
        keep = merge_duplicates(boxes, conf, grouped, merge_iou)
        variants["mision_fusion"].add(boxes[keep], conf[keep], grouped[keep], gt_boxes, gt_grouped, bins)
    return {name: stats.summary() for name, stats in variants.items()}


def evaluate_run(root: Path, run: Path, *, split="val", device=None, merge_iou=0.7) -> dict:
    """Valida best.pt con el pipeline de Ultralytics y reagrupa sus predicciones por misión.

    Se capturan las predicciones del propio validador (letterbox rectangular, conf 0,001, max_det 300),
    así la variante de 10 clases reproduce las métricas oficiales del run.
    """
    import torch
    import ultralytics
    from ultralytics import YOLO
    from ultralytics.models.yolo.detect import DetectionValidator
    if split not in ("val", "test"):
        raise ValueError(split)
    info = json.loads((run / "run.json").read_text(encoding="utf-8"))
    settings = info["settings"]
    device = device or ("0" if torch.cuda.is_available() else "cpu")
    weights = run / "train" / "weights" / "best.pt"
    out = run / "mission_eval"
    out.mkdir(exist_ok=True)
    captured = []

    class CaptureValidator(DetectionValidator):
        def update_metrics(self, preds, batch):
            super().update_metrics(preds, batch)
            for si, pred in enumerate(preds):
                gt = self._prepare_batch(si, batch)
                gt_boxes = gt["bboxes"].cpu().numpy().astype(float).reshape(-1, 4)
                # Cajas en el espacio de entrada de la red: su lado es el tamaño que "ve" el modelo.
                sides = np.sqrt(np.clip((gt_boxes[:, 2:] - gt_boxes[:, :2]).prod(1), 0, None))
                captured.append((pred["bboxes"].cpu().numpy().astype(float), pred["conf"].cpu().numpy().astype(float), pred["cls"].cpu().numpy().astype(int), gt_boxes, gt["cls"].cpu().numpy().astype(int), sides))

    began = time.perf_counter()
    official = YOLO(str(weights)).val(validator=CaptureValidator, data=settings["data_yaml"], split=split, imgsz=settings["imgsz"], batch=settings["batch"], workers=settings["workers"], device=device, plots=False, verbose=False, project=str(out), name="ultralytics_val", exist_ok=True)
    scratch = out / "ultralytics_val"
    if scratch.is_dir() and not any(scratch.iterdir()):
        scratch.rmdir()
    variants = evaluate_samples(captured, merge_iou=merge_iou)
    reference = info.get("metrics", {}) if split == "val" else {}
    result = {
        "run": run.name,
        "weights": str(weights.relative_to(root)),
        "split": split,
        "images": len(captured),
        "imgsz": settings["imgsz"],
        "device": device,
        "ultralytics": ultralytics.__version__,
        "elapsed_seconds": time.perf_counter() - began,
        "protocol": {"pipeline": "DetectionValidator de Ultralytics (rect, batch del run)", "conf": 0.001, "max_det": 300, "iou_thresholds": "0.50:0.05:0.95", "operating_iou": 0.5, "merge_iou": merge_iou, "size": "sqrt(w*h) en píxeles de la entrada de la red"},
        "groups": MISSION_GROUPS,
        "reference_run_json": {k: reference.get(k) for k in ("map50", "map50_95")},
        "reference_ultralytics_now": {"map50": float(official.box.map50), "map50_95": float(official.box.map)},
        "variants": variants,
        "note": "Evaluación agrupada post hoc del modelo de 10 clases; no reemplaza un reentrenamiento. Métricas estilo Ultralytics; no es el evaluador oficial de VisDrone.",
    }
    (out / f"{split}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / f"{split}.md").write_text(markdown(result), encoding="utf-8")
    return result


def _pct(value):
    return "—" if value is None else f"{100 * value:.1f} %"


def markdown(result: dict, conf=0.25) -> str:
    v = result["variants"]
    ref = result["reference_run_json"]
    lines = [f"# Evaluación agrupada por misión · {result['run']} · {result['split']}", "",
             f"{result['images']} imágenes, entrada {result['imgsz']} px. {result['note']}", "",
             "| Variante | mAP50 | mAP50-95 |", "|---|---:|---:|"]
    labels = {"visdrone10": "10 clases VisDrone (control)", "mision": "Misión, agrupado directo", "mision_fusion": f"Misión, agrupado + fusión IoU {result['protocol']['merge_iou']}"}
    for key, label in labels.items():
        lines.append(f"| {label} | {_pct(v[key]['map50'])} | {_pct(v[key]['map50_95'])} |")
    now = result["reference_ultralytics_now"]
    lines += ["", f"Control: el validador de Ultralytics en esta misma pasada dio mAP50 {_pct(now['map50'])} y mAP50-95 {_pct(now['map50_95'])}."]
    if ref.get("map50") is not None:
        lines[-1] += f" run.json registra {_pct(ref['map50'])} y {_pct(ref['map50_95'])}."
    best = v["mision_fusion"]
    point = next(p for p in best["operating_points"] if p["conf"] == conf)
    lines += ["", f"## Clases de la misión (agrupado + fusión), confianza {conf}, IoU 0,5", "",
              "| Clase | Objetos | AP50 | AP50-95 | Precisión | Recall |", "|---|---:|---:|---:|---:|---:|"]
    for name in best["classes"]:
        c, op = best["per_class"][name], point["per_class"][name]
        lines.append(f"| {name} | {c['objects']} | {_pct(c.get('ap50'))} | {_pct(c.get('ap50_95'))} | {_pct(op['precision'])} | {_pct(op['recall'])} |")
    lines.append(f"| todos | {sum(best['per_class'][n]['objects'] for n in best['classes'])} | | | {_pct(point['all_objects']['precision'])} | {_pct(point['all_objects']['recall'])} |")
    lines += ["", "## Precisión y recall según el umbral de confianza", "", "| Confianza | " + " | ".join(f"{n} P / R" for n in best["classes"]) + " | todos P / R |", "|---:|" + "---:|" * (len(best["classes"]) + 1)]
    for p in best["operating_points"]:
        cells = [f"{_pct(p['per_class'][n]['precision'])} / {_pct(p['per_class'][n]['recall'])}" for n in best["classes"]]
        lines.append(f"| {p['conf']} | " + " | ".join(cells) + f" | {_pct(p['all_objects']['precision'])} / {_pct(p['all_objects']['recall'])} |")
    lines += ["", f"## Recall por tamaño en la entrada de la red (confianza {conf})", "", "| Clase | " + " | ".join(f"{s} px" for s in SIZE_LABELS) + " |", "|---|" + "---:|" * len(SIZE_LABELS)]
    for name in best["classes"]:
        cells = [f"{_pct(b['recall'])} ({b['objects']})" for b in point["recall_by_size"][name].values()]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines += ["", "Entre paréntesis, cantidad de objetos anotados en cada tamaño."]
    return "\n".join(lines) + "\n"
