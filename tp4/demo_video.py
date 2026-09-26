"""Video de demostración: el detector sobre una secuencia limpia de VisDrone-VID.

Dibuja las detecciones de la misión y lleva la cuenta de la métrica por pasada: cuántos de los
objetos vistos hasta ese cuadro fueron detectados al menos una vez. Usa las predicciones del
caché de `tp4.video` (correr antes `python -m tp4.cli video`).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .mission import MISSION_CLASSES, TO_MISSION, box_iou, match_pairs, merge_duplicates
from .video import NOMINAL_FPS, load_annotations, vid_root

COLORS = {"persona": (255, 150, 0), "vehiculo": (0, 200, 255)}  # RGB
MISSED = (230, 40, 40)
HUD = {"persona": "Personas detectadas", "vehiculo": "Vehículos detectados"}


def _font(size):
    """DejaVu Sans viene con matplotlib: tiene tildes y está en todas las máquinas del equipo."""
    from PIL import ImageFont
    import matplotlib
    return ImageFont.truetype(str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"), size)


def _cached_predictions(run: Path, variant: str, sequence: str) -> dict:
    path = run / "mission_eval" / "video_cache" / f"{variant}_{sequence}.npz"
    if not path.exists():
        raise FileNotFoundError(f"Falta {path}: correr python -m tp4.cli video {run} --variants {variant}")
    data = np.load(path)
    order = np.argsort(data["frame"], kind="stable")
    frames = data["frame"][order]
    keys, starts = np.unique(frames, return_index=True)
    ends = list(starts[1:]) + [len(frames)]
    return {int(k): (data["boxes"][order][a:b], data["conf"][order][a:b], data["cls"][order][a:b]) for k, a, b in zip(keys, starts, ends)}


def _writer(path: Path, fps: float, size: tuple[int, int]):
    import cv2
    for suffix, codec in ((".mp4", "avc1"), (".webm", "VP80")):
        target = path.with_suffix(suffix)
        writer = cv2.VideoWriter(str(target), cv2.VideoWriter_fourcc(*codec), fps, size)
        if writer.isOpened():
            return writer, target
    raise RuntimeError("OpenCV no puede escribir MP4 H.264 ni WebM VP8 en este entorno.")


def render_demo(root: Path, run: Path, *, sequence="uav0000117_02622_v", variant="full1280", conf=0.25, stride=3, width=960) -> dict:
    """Escribe mission_eval/demo_<secuencia>.mp4 y un JSON con las cuentas finales."""
    import cv2
    from PIL import Image, ImageDraw
    base = vid_root(root)
    files = sorted((base / "sequences" / sequence).glob("*.jpg"))
    height0, width0 = cv2.imread(str(files[0])).shape[:2]
    gt, ign = load_annotations(base / "annotations" / f"{sequence}.txt", width0, height0)
    preds = _cached_predictions(run, variant, sequence)
    scale = width / width0
    size = (width, round(height0 * scale))
    fps = NOMINAL_FPS / stride
    out_dir = run / "mission_eval"
    writer, target = _writer(out_dir / f"demo_{sequence}", fps, size)
    font = _font(max(14, width // 58))
    small = _font(max(11, width // 90))
    seen = {g: set() for g in range(len(MISSION_CLASSES))}
    found = {g: set() for g in range(len(MISSION_CLASSES))}
    empty = (np.zeros((0, 4)), np.zeros(0, int), np.zeros(0, int), np.zeros(0))
    for path in files[::stride]:
        frame = int(path.stem)
        g_boxes, g_ids, g_groups, _ = gt.get(frame, empty)
        boxes, scores, classes = preds.get(frame, (np.zeros((0, 4)), np.zeros(0), np.zeros(0, int)))
        keep = scores >= conf
        boxes, scores, groups = boxes[keep], scores[keep], TO_MISSION[classes[keep]]
        keep = merge_duplicates(boxes, scores, groups, 0.7)
        boxes, scores, groups = boxes[keep], scores[keep], groups[keep]
        pairs = match_pairs(box_iou(g_boxes, boxes), groups, g_groups, 0.5)
        for tid, grp in zip(g_ids, g_groups):
            seen[grp].add(int(tid))
        for label in pairs[:, 0]:
            found[g_groups[label]].add(int(g_ids[label]))
        image = Image.fromarray(cv2.cvtColor(cv2.resize(cv2.imread(str(path)), size, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(image)
        # Personas anotadas que todavía no se detectaron en ningún cuadro: lo que la pasada aún no encontró.
        for box, tid, grp in zip(g_boxes, g_ids, g_groups):
            if MISSION_CLASSES[grp] == "persona" and int(tid) not in found[grp]:
                draw.rectangle(list(box * scale), outline=MISSED, width=1)
        for box, score, grp in zip(boxes, scores, groups):
            name = MISSION_CLASSES[grp]
            draw.rectangle(list(box * scale), outline=COLORS[name], width=2)
        lines = [f"YOLO26n · entrada {variant.replace('full', '')} px · {fps:.0f} FPS simulados · confianza {conf}".replace(".", ","),
                 *(f"{HUD[n]} al menos una vez: {len(found[g])} de {len(seen[g])}"
                   f" ({100 * len(found[g]) / max(1, len(seen[g])):.0f} %)" for g, n in enumerate(MISSION_CLASSES))]
        band = 12 + len(lines) * (font.size + 8)
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        ImageDraw.Draw(overlay).rectangle([0, 0, image.width, band], fill=(10, 20, 35, 190))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(image)
        for i, line in enumerate(lines):
            draw.text((14, 8 + i * (font.size + 8)), line, fill=(237, 242, 248), font=font)
        legend = [("persona", COLORS["persona"]), ("vehículo", COLORS["vehiculo"]), ("persona aún no detectada", MISSED)]
        x = 14
        for text, color in legend:
            y = image.height - small.size - 12
            draw.rectangle([x, y, x + small.size, y + small.size], outline=color, width=2)
            draw.text((x + small.size + 6, y - 2), text, fill=(255, 255, 255), font=small, stroke_width=2, stroke_fill=(0, 0, 0))
            x += int(draw.textlength(text, font=small)) + small.size + 30
        writer.write(cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR))
    writer.release()
    stats = {"video": target.name, "sequence": sequence, "variant": variant, "conf": conf, "fps": fps, "frames": len(files[::stride]),
             "detected_once": {n: {"found": len(found[g]), "seen": len(seen[g])} for g, n in enumerate(MISSION_CLASSES)}}
    (out_dir / f"demo_{sequence}.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    return stats
