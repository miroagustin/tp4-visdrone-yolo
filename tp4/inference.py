"""Inferencia con imagen completa a distintas resoluciones o por mosaicos (estilo SAHI).

Devuelve cajas en píxeles de la imagen original con las 10 clases VisDrone, para evaluarlas
con tp4.mission (clases de la misión) o tp4.video (detección por objeto).
"""
from __future__ import annotations

import time

import numpy as np

# Variantes: nombre -> (lado de la pasada completa, usar mosaicos, lado máximo de la imagen que se corta en mosaicos).
# Sin lado máximo, los mosaicos se cortan a resolución nativa; con él, la imagen se reduce antes si es más grande.
VARIANTS = {"full640": (640, False, None), "full960": (960, False, None), "full1280": (1280, False, None),
            "mosaicos": (640, True, None), "mosaicos1280": (1280, True, None),
            "mosaicos1920": (640, True, 1920), "mosaicos2560": (640, True, 2560)}
TILE, OVERLAP, EDGE = 640, 0.2, 2.0


def tile_grid(width: int, height: int, tile=TILE, overlap=OVERLAP) -> list[tuple[int, int, int, int]]:
    """Mosaicos de `tile` px que cubren la imagen con solapamiento; los del borde se alinean al borde."""
    def starts(size):
        if size <= tile:
            return [0]
        step = int(tile * (1 - overlap))
        n = int(np.ceil((size - tile) / step)) + 1
        return sorted({min(i * step, size - tile) for i in range(n)})
    return [(x, y, min(x + tile, width), min(y + tile, height)) for y in starts(height) for x in starts(width)]


def _boxes(result):
    b = result.boxes
    return b.xyxy.cpu().numpy().astype(float), b.conf.cpu().numpy().astype(float), b.cls.cpu().numpy().astype(int)


def tiling_scale(width: int, height: int, max_side: int | None) -> float:
    """Factor con que se reduce la imagen antes de cortarla en mosaicos (1 si no hace falta)."""
    return min(1.0, max_side / max(width, height)) if max_side else 1.0


def detect(model, image: np.ndarray, *, imgsz=640, tiles=False, tile_max_side=None, conf=0.01, device="0", merge_iou=0.5):
    """Detecta sobre una imagen BGR. Con tiles=True suma mosaicos a la pasada completa; con tile_max_side,
    la imagen se reduce a ese lado mayor antes de cortarla."""
    import cv2
    boxes, scores, classes = _boxes(model.predict(image, imgsz=imgsz, conf=conf, max_det=300, device=device, verbose=False)[0])
    if not tiles:
        return boxes, scores, classes
    scale = tiling_scale(image.shape[1], image.shape[0], tile_max_side)
    source = image if scale == 1.0 else cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    height, width = source.shape[:2]
    grid = tile_grid(width, height)
    results = model.predict([np.ascontiguousarray(source[y0:y1, x0:x1]) for x0, y0, x1, y1 in grid], imgsz=TILE, conf=conf,
                            max_det=300, device=device, verbose=False)
    parts = [(boxes, scores, classes)]
    for (x0, y0, x1, y1), result in zip(grid, results):
        b, s, c = _boxes(result)
        # Una caja pegada a un borde interno del mosaico está cortada: la ve entera el mosaico vecino o la pasada completa.
        cut = ((b[:, 0] < EDGE) & (x0 > 0)) | ((b[:, 1] < EDGE) & (y0 > 0)) | \
              ((b[:, 2] > (x1 - x0) - EDGE) & (x1 < width)) | ((b[:, 3] > (y1 - y0) - EDGE) & (y1 < height))
        parts.append(((b[~cut] + [x0, y0, x0, y0]) / scale, s[~cut], c[~cut]))
    boxes, scores, classes = (np.concatenate(x) for x in zip(*parts))
    from .mission import merge_duplicates
    keep = merge_duplicates(boxes, scores, classes, merge_iou)
    return boxes[keep], scores[keep], classes[keep]


def timed_detect(model, image, variant: str, device="0", conf=0.01):
    """Detección con una variante de VARIANTS y su tiempo en ms (sin incluir la lectura del archivo)."""
    import torch
    imgsz, tiles, max_side = VARIANTS[variant]
    began = time.perf_counter()
    out = detect(model, image, imgsz=imgsz, tiles=tiles, tile_max_side=max_side, conf=conf, device=device)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    return out, (time.perf_counter() - began) * 1000


def inferences_per_image(width: int, height: int, variant: str) -> int:
    _, tiles, max_side = VARIANTS[variant]
    if not tiles:
        return 1
    scale = tiling_scale(width, height, max_side)
    return 1 + len(tile_grid(round(width * scale), round(height * scale)))


def evaluate_resolution(root, run, *, variants=tuple(VARIANTS), split="val", device=None) -> dict:
    """Evalúa best.pt en DET con cada variante, con las clases de la misión y el recall por tamaño."""
    import json
    import cv2
    import torch
    from ultralytics import YOLO
    from .mission import evaluate_samples
    device = device or ("0" if torch.cuda.is_available() else "cpu")
    model = YOLO(str(run / "train" / "weights" / "best.pt"))
    images = sorted((root / "data" / "yolo" / "images" / split).glob("*.jpg"))
    labels = root / "data" / "yolo" / "labels" / split
    detect(model, cv2.imread(str(images[0])), device=device)  # calentamiento
    previous = run / "mission_eval" / f"resolution_{split}.json"
    results = json.loads(previous.read_text(encoding="utf-8"))["variants"] if previous.exists() else {}
    for variant in variants:
        samples, times, calls = [], [], []
        for path in images:
            image = cv2.imread(str(path))
            height, width = image.shape[:2]
            (boxes, scores, classes), ms = timed_detect(model, image, variant, device)
            rows = np.loadtxt(labels / f"{path.stem}.txt", ndmin=2) if (labels / f"{path.stem}.txt").stat().st_size else np.zeros((0, 5))
            xc, yc, w, h = rows[:, 1] * width, rows[:, 2] * height, rows[:, 3] * width, rows[:, 4] * height
            gt = np.stack([xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2], 1)
            sides = np.sqrt(w * h) * 640 / max(width, height)  # tamaño referido a la entrada de 640 px
            samples.append((boxes, scores, classes, gt, rows[:, 0].astype(int), sides))
            times.append(ms)
            calls.append(inferences_per_image(width, height, variant))
        summary = evaluate_samples(samples)
        results[variant] = {"ms_per_image": float(np.mean(times)), "ms_p95": float(np.percentile(times, 95)),
                            "inferences_per_image": float(np.mean(calls)), "mision": summary["mision_fusion"],
                            "visdrone10": {k: summary["visdrone10"][k] for k in ("map50", "map50_95")}}
        print(variant, f"{results[variant]['ms_per_image']:.1f} ms", f"mAP50 misión {summary['mision_fusion']['map50']:.3f}")
    out = {"run": run.name, "split": split, "images": len(images), "device": torch.cuda.get_device_name(0) if device != "cpu" else "cpu",
           "protocol": {"conf": 0.01, "max_det": 300, "tile": TILE, "overlap": OVERLAP, "merge_iou": 0.5,
                        "size": "sqrt(w*h) referido a la entrada de 640 px de la imagen completa",
                        "note": "Pipeline predict; conf 0,01 subestima levemente el mAP frente al validador (conf 0,001)."},
           "variants": results}
    target = run / "mission_eval"
    target.mkdir(exist_ok=True)
    (target / f"resolution_{split}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
