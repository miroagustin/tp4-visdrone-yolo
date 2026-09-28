"""Detección por objeto durante la pasada, sobre VisDrone2019-VID (validación).

Cada objeto anotado tiene un target_id. Un objeto cuenta como detectado si, en alguno de los
cuadros evaluados, una detección de su clase de la misión lo cubre con IoU >= 0,5. Los cuadros
se submuestrean para simular los FPS que alcanza cada placa.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from .mission import MISSION_CLASSES, SIZE_EDGES, SIZE_LABELS, TO_MISSION, box_iou, match_pairs, merge_duplicates, size_bins, to_mission

NOMINAL_FPS = 30.0  # los archivos no traen FPS; se asume el nominal de la cámara
STRIDES = (1, 3, 6, 15)  # 30, 10, 5 y 2 FPS con el supuesto nominal
CONFS = (0.1, 0.25, 0.4)
STORE_CONF = 0.05
# Secuencias cuyo video de origen aporta imágenes al entrenamiento de DET (ver wiki/datos/visdrone-vid.md).
SEEN_IN_TRAIN = {"uav0000137_00458_v", "uav0000182_00000_v", "uav0000305_00000_v", "uav0000339_00001_v"}


def vid_root(root: Path) -> Path:
    path = root / "data" / "raw" / "VisDrone2019-VID-val"
    if not (path / "sequences").is_dir():
        raise FileNotFoundError(f"Falta {path}: extraer VisDrone2019-VID-val.zip en data/raw/")
    return path


def load_annotations(path: Path, width: int, height: int):
    """Devuelve {cuadro: (cajas, ids, grupos, lados)} y {cuadro: cajas ignoradas}."""
    rows = np.loadtxt(path, delimiter=",", dtype=int, ndmin=2)
    valid = rows[(rows[:, 7] >= 1) & (rows[:, 7] <= 10) & (rows[:, 6] == 1)]
    ignored = rows[(rows[:, 7] == 0) | (rows[:, 7] == 11)]
    # Grupo de cada objeto: el más frecuente en su trayectoria.
    group_of = {}
    for tid in np.unique(valid[:, 1]):
        groups = TO_MISSION[valid[valid[:, 1] == tid][:, 7] - 1]
        group_of[int(tid)] = int(np.bincount(groups).argmax())
    def xyxy(r):
        return np.stack([r[:, 2], r[:, 3], r[:, 2] + r[:, 4], r[:, 3] + r[:, 5]], 1).astype(float)
    scale = 640 / max(width, height)
    gt = {}
    for frame in np.unique(valid[:, 0]):
        r = valid[valid[:, 0] == frame]
        gt[int(frame)] = (xyxy(r), r[:, 1].astype(int), np.array([group_of[int(t)] for t in r[:, 1]]),
                          np.sqrt(r[:, 4] * r[:, 5]) * scale)
    ign = {int(f): xyxy(ignored[ignored[:, 0] == f]) for f in np.unique(ignored[:, 0])}
    return gt, ign


def evaluate_sequence(frames: list[int], gt: dict, ign: dict, preds: dict, conf: float, nc: int) -> dict:
    """Recorre los cuadros evaluados y acumula, por objeto, en qué cuadros fue visto y detectado."""
    seen, detected, group, side = defaultdict(list), defaultdict(list), {}, defaultdict(float)
    fp = np.zeros(len(MISSION_CLASSES), dtype=int)
    instances = np.zeros(len(MISSION_CLASSES), dtype=int)
    hits = np.zeros(len(MISSION_CLASSES), dtype=int)
    empty = (np.zeros((0, 4)), np.zeros(0, int), np.zeros(0, int), np.zeros(0))
    for frame in frames:
        g_boxes, g_ids, g_groups, g_sides = gt.get(frame, empty)
        boxes, scores, classes = preds.get(frame, (np.zeros((0, 4)), np.zeros(0), np.zeros(0, int)))
        keep = scores >= conf
        boxes, scores, groups = boxes[keep], scores[keep], to_mission(classes[keep], nc)
        keep = merge_duplicates(boxes, scores, groups, 0.7)
        boxes, groups = boxes[keep], groups[keep]
        pairs = match_pairs(box_iou(g_boxes, boxes), groups, g_groups, 0.5)
        for tid, grp, s in zip(g_ids, g_groups, g_sides):
            seen[tid].append(frame)
            group[tid] = grp
            side[tid] = max(side[tid], s)
        np.add.at(instances, g_groups, 1)
        np.add.at(hits, g_groups[pairs[:, 0]], 1)
        for label in pairs[:, 0]:
            detected[g_ids[label]].append(frame)
        unmatched = np.setdiff1d(np.arange(len(boxes)), pairs[:, 1])
        if len(unmatched) and frame in ign:
            covered = _ioa(boxes[unmatched], ign[frame]).max(1) > 0.5
            unmatched = unmatched[~covered]
        np.add.at(fp, groups[unmatched], 1)
    objects = {tid: {"group": int(group[tid]), "seen": seen[tid], "detected": detected.get(tid, []), "max_side": float(side[tid])} for tid in seen}
    return {"objects": objects, "fp": fp, "instances": instances, "hits": hits, "frames": len(frames)}


def _ioa(boxes: np.ndarray, regions: np.ndarray) -> np.ndarray:
    """Fracción del área de cada caja que cae dentro de cada región ignorada."""
    lt = np.maximum(boxes[:, None, :2], regions[None, :, :2])
    rb = np.minimum(boxes[:, None, 2:], regions[None, :, 2:])
    inter = np.clip(rb - lt, 0, None).prod(2)
    return inter / np.maximum((boxes[:, 2:] - boxes[:, :2]).prod(1)[:, None], 1e-7)


def summarize(parts: list[dict], seconds: float, fps: float) -> dict:
    """Métricas por clase de la misión a partir de varias secuencias ya evaluadas."""
    out = {}
    for g, name in enumerate(MISSION_CLASSES):
        objs = [o for p in parts for o in p["objects"].values() if o["group"] == g]
        n = len(objs)
        once = [o for o in objs if o["detected"]]
        thrice = [o for o in objs if len(o["detected"]) >= 3]
        delays = [(o["detected"][0] - o["seen"][0]) / fps for o in once]
        sides = np.array([o["max_side"] for o in objs]) if objs else np.zeros(0)
        bins = size_bins(sides)
        by_size = {label: {"objects": int((bins == b).sum()),
                           "detected_once": _ratio(sum(1 for o, bb in zip(objs, bins) if bb == b and o["detected"]), int((bins == b).sum()))}
                   for b, label in enumerate(SIZE_LABELS)}
        instances = sum(int(p["instances"][g]) for p in parts)
        hits = sum(int(p["hits"][g]) for p in parts)
        fp = sum(int(p["fp"][g]) for p in parts)
        frames = sum(p["frames"] for p in parts)
        out[name] = {"objects": n, "detected_once": _ratio(len(once), n), "detected_3": _ratio(len(thrice), n),
                     "first_detection_s_median": float(np.median(delays)) if delays else None,
                     "first_detection_s_p90": float(np.percentile(delays, 90)) if delays else None,
                     "frame_recall": _ratio(hits, instances), "frame_precision": _ratio(hits, hits + fp),
                     "false_alarms_per_frame": _ratio(fp, frames),
                     "false_alarms_per_min": float(fp / (seconds / 60)),
                     "detected_once_by_max_size": by_size}
    return out


def _ratio(a, b):
    return float(a / b) if b else None


def predict_sequences(model, root: Path, variant: str, cache: Path, device="0") -> dict:
    """Predice (o lee del caché) todos los cuadros de cada secuencia con una variante de tp4.inference."""
    import cv2
    from .inference import timed_detect
    base = vid_root(root)
    cache.mkdir(parents=True, exist_ok=True)
    out = {}
    for seq_dir in sorted((base / "sequences").iterdir()):
        target = cache / f"{variant}_{seq_dir.name}.npz"
        if target.exists():
            data = np.load(target)
        else:
            frames, boxes, scores, classes, times = [], [], [], [], []
            for path in sorted(seq_dir.glob("*.jpg")):
                (b, s, c), ms = timed_detect(model, cv2.imread(str(path)), variant, device, conf=STORE_CONF)
                frames.append(np.full(len(s), int(path.stem)))
                boxes.append(b), scores.append(s), classes.append(c), times.append(ms)
            data = {"frame": np.concatenate(frames), "boxes": np.concatenate(boxes).reshape(-1, 4), "conf": np.concatenate(scores),
                    "cls": np.concatenate(classes).astype(int), "ms": np.array(times)}
            np.savez_compressed(target, **data)
            print(variant, seq_dir.name, f"{np.mean(times):.0f} ms/cuadro")
        preds = {int(f): (data["boxes"][data["frame"] == f], data["conf"][data["frame"] == f], data["cls"][data["frame"] == f])
                 for f in np.unique(data["frame"])}
        out[seq_dir.name] = {"preds": preds, "ms": float(np.mean(data["ms"]))}
    return out


def evaluate_video(root: Path, run: Path, *, variants=("full640", "full1280", "mosaicos"), device=None) -> dict:
    import cv2
    import torch
    from ultralytics import YOLO
    device = device or ("0" if torch.cuda.is_available() else "cpu")
    base = vid_root(root)
    model = YOLO(str(run / "train" / "weights" / "best.pt"))
    sequences = {}
    for seq_dir in sorted((base / "sequences").iterdir()):
        files = sorted(seq_dir.glob("*.jpg"))
        height, width = cv2.imread(str(files[0])).shape[:2]
        gt, ign = load_annotations(base / "annotations" / f"{seq_dir.name}.txt", width, height)
        sequences[seq_dir.name] = {"frames": [int(p.stem) for p in files], "gt": gt, "ign": ign, "size": [width, height]}
    cache = run / "mission_eval" / "video_cache"
    groups = {"todas": list(sequences), "limpias": [s for s in sequences if s not in SEEN_IN_TRAIN],
              "vistas_en_entrenamiento": [s for s in sequences if s in SEEN_IN_TRAIN]}
    results = {}
    for variant in variants:
        preds = predict_sequences(model, root, variant, cache, device)
        results[variant] = {"ms_per_frame": {s: preds[s]["ms"] for s in sequences}, "evaluations": []}
        for stride in STRIDES:
            for conf in CONFS:
                parts = {s: evaluate_sequence(sequences[s]["frames"][::stride], sequences[s]["gt"], sequences[s]["ign"], preds[s]["preds"], conf, len(model.names))
                         for s in sequences}
                entry = {"stride": stride, "fps": NOMINAL_FPS / stride, "conf": conf}
                for name, members in groups.items():
                    seconds = sum(len(sequences[s]["frames"]) for s in members) / NOMINAL_FPS
                    entry[name] = summarize([parts[s] for s in members], seconds, NOMINAL_FPS)
                results[variant]["evaluations"].append(entry)
    out = {"run": run.name, "dataset": "VisDrone2019-VID val", "nominal_fps": NOMINAL_FPS,
           "sequences": {s: {"frames": len(v["frames"]), "size": v["size"], "seen_in_det_train": s in SEEN_IN_TRAIN} for s, v in sequences.items()},
           "protocol": {"iou": 0.5, "merge_iou": 0.7, "ignored_ioa": 0.5, "store_conf": STORE_CONF,
                        "detected_once": "al menos un cuadro evaluado con detección de su clase de la misión",
                        "size": "lado máximo sqrt(w*h) del objeto, referido a la entrada de 640 px"},
           "variants": results}
    (run / "mission_eval" / "video_val.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
