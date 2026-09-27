"""Descarga, preservación, conversión y auditoría de VisDrone2019-DET."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from collections import Counter
from pathlib import Path

import requests
from PIL import Image

CLASSES = ("pedestrian", "people", "bicycle", "car", "van", "truck", "tricycle", "awning-tricycle", "bus", "motor")
# Clases del TP (entrenamiento, evaluación local y placas): cada categoría VisDrone se convierte a su grupo.
MISSION_GROUPS = {
    "persona": ("pedestrian", "people"),
    # Bicicletas y motos son vehículos; quien las conduce está anotado aparte como "people".
    "vehiculo": ("car", "van", "truck", "bus", "tricycle", "awning-tricycle", "bicycle", "motor"),
}
MISSION_CLASSES = tuple(MISSION_GROUPS)
TO_MISSION = tuple(next(i for i, members in enumerate(MISSION_GROUPS.values()) if name in members) for name in CLASSES)
SPLITS = {"train": 6471, "val": 548, "test-dev": 1610}
BASE = "https://github.com/ultralytics/assets/releases/download/v0.0.0/VisDrone2019-DET-"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def labels_digest(folder: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(folder.glob("*.txt")):
        h.update(path.name.encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def download_archive(root: Path, split: str) -> Path:
    if split not in SPLITS:
        raise ValueError(split)
    folder = root / "archives"
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"VisDrone2019-DET-{split}.zip"
    manifest = dest.with_suffix(".json")
    if dest.exists() and manifest.exists():
        info = json.loads(manifest.read_text(encoding="utf-8"))
        if info.get("sha256") == digest(dest) and zipfile.is_zipfile(dest):
            return dest
    url = BASE + split + ".zip"
    tmp = dest.with_suffix(".part")
    # Una descarga parcial se reanuda únicamente si el servidor confirma Range.
    offset = tmp.stat().st_size if tmp.exists() else 0
    with requests.get(url, stream=True, timeout=90, headers={"Range": f"bytes={offset}-"} if offset else {}) as response:
        response.raise_for_status()
        append = bool(offset and response.status_code == 206)
        with tmp.open("ab" if append else "wb") as out:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    out.write(chunk)
    if not zipfile.is_zipfile(tmp):
        raise RuntimeError(f"Descarga ZIP incompleta: {tmp}")
    with zipfile.ZipFile(tmp) as z:
        bad = z.testzip()
        if bad:
            raise RuntimeError(f"ZIP corrupto, entrada {bad}: {tmp}")
    tmp.replace(dest)
    manifest.write_text(json.dumps({"url": url, "bytes": dest.stat().st_size, "sha256": digest(dest)}, indent=2), encoding="utf-8")
    return dest


def extract_archive(root: Path, split: str) -> Path:
    archive = download_archive(root, split)
    dest = root / "raw" / f"VisDrone2019-DET-{split}"
    marker = dest / ".archive_sha256"
    sha = digest(archive)
    if marker.exists() and marker.read_text(encoding="ascii") == sha:
        return dest
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with zipfile.ZipFile(archive) as z:
        prefix = f"VisDrone2019-DET-{split}/"
        for member in z.infolist():
            name = member.filename.replace("\\", "/")
            if not name.startswith(prefix) or ".." in Path(name).parts:
                raise RuntimeError(f"Ruta insegura o inesperada: {name}")
            relative = Path(name[len(prefix):])
            if not relative.parts:
                continue
            target = dest / relative
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
    marker.write_text(sha, encoding="ascii")
    return dest


def convert_row(line: str, width: int, height: int):
    parts = line.strip().split(",")
    if len(parts) < 6:
        raise ValueError(f"Fila incompleta: {line!r}")
    x, y, w, h = map(float, parts[:4])
    score, category = int(parts[4]), int(parts[5])
    if score not in (0, 1):
        raise ValueError(f"Score inesperado: {score}")
    if score == 0:
        return None, "ignored_score"
    if not 1 <= category <= 10:
        return None, "excluded_category"
    if w <= 0 or h <= 0:
        return None, "invalid_box"
    x1, y1 = max(0.0, x), max(0.0, y)
    x2, y2 = min(float(width), x + w), min(float(height), y + h)
    if x2 <= x1 or y2 <= y1:
        return None, "outside_image"
    clipped = x1 != x or y1 != y or x2 != x + w or y2 != y + h
    values = ((x1 + x2) / (2 * width), (y1 + y2) / (2 * height), (x2 - x1) / width, (y2 - y1) / height)
    if not all(0 <= n <= 1 for n in values):
        raise ValueError(f"Caja normalizada inválida: {values}")
    return f"{TO_MISSION[category - 1]} " + " ".join(f"{v:.8f}" for v in values), "clipped" if clipped else "included"


def prepare_split(root: Path, split: str) -> dict:
    raw = extract_archive(root, split)
    images = sorted((raw / "images").glob("*.jpg"))
    annotations = {p.stem: p for p in (raw / "annotations").glob("*.txt")}
    if not images or {p.stem for p in images} != set(annotations):
        raise RuntimeError(f"Imágenes/anotaciones incompletas en {split}: {len(images)}/{len(annotations)}")
    output_split = "test" if split == "test-dev" else split
    img_out = root / "yolo" / "images" / output_split
    lab_out = root / "yolo" / "labels" / output_split
    img_out.mkdir(parents=True, exist_ok=True)
    lab_out.mkdir(parents=True, exist_ok=True)
    marker = lab_out / "manifest.json"
    raw_sha = (raw / ".archive_sha256").read_text(encoding="ascii")
    if marker.exists():
        saved = json.loads(marker.read_text(encoding="utf-8"))
        if saved.get("archive_sha256") == raw_sha and len(list(lab_out.glob("*.txt"))) == len(images) and len(list(img_out.glob("*.jpg"))) == len(images) and saved.get("labels_sha256") == labels_digest(lab_out) and saved.get("classes") == list(MISSION_CLASSES):
            return saved
    counts = Counter()
    class_counts = Counter()
    areas = []
    densities = []
    for image in images:
        with Image.open(image) as im:
            im.verify()
        with Image.open(image) as im:
            width, height = im.size
        if width <= 0 or height <= 0:
            raise RuntimeError(f"Imagen sin dimensiones: {image}")
        rows = []
        for line_no, line in enumerate(annotations[image.stem].read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row, reason = convert_row(line, width, height)
            except (ValueError, TypeError) as exc:
                raise RuntimeError(f"{annotations[image.stem]}:{line_no}: {exc}") from exc
            counts[reason] += 1
            if row:
                rows.append(row)
                fields = row.split()
                class_counts[fields[0]] += 1
                areas.append(float(fields[3]) * float(fields[4]))
        densities.append(len(rows))
        label = lab_out / (image.stem + ".txt")
        label.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
        linked = img_out / image.name
        if not linked.exists():
            try:
                os.link(image, linked)
            except OSError:
                shutil.copy2(image, linked)
    summary = {"split": split, "images": len(images), "expected_images": SPLITS[split], "annotations": len(annotations), "rows": dict(counts), "classes": list(MISSION_CLASSES), "class_counts": {MISSION_CLASSES[int(k)]: v for k, v in class_counts.items()}, "mean_objects_per_image": sum(densities) / len(densities), "relative_box_areas": areas, "archive_sha256": raw_sha, "labels_sha256": labels_digest(lab_out)}
    marker.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
    return summary


def write_yaml(root: Path, path: Path, train="images/train", val="images/val") -> None:
    import yaml
    path.write_text(yaml.safe_dump({"path": str((root / "yolo").resolve()), "train": train, "val": val, "test": "images/test", "names": dict(enumerate(MISSION_CLASSES))}, sort_keys=False), encoding="utf-8")


def prepare_all(root: Path) -> dict:
    root = root.resolve()
    result = {split: prepare_split(root, split) for split in SPLITS}
    write_yaml(root, root / "visdrone.yaml")
    (root / "audit.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result


def smoke_yaml(root: Path, seed: int, train_n=128, val_n=32) -> Path:
    import random
    root = root.resolve()
    rng = random.Random(seed)
    lists = {}
    for split, count in (("train", train_n), ("val", val_n)):
        images = sorted((root / "yolo" / "images" / split).glob("*.jpg"))
        if len(images) < count:
            raise RuntimeError(f"Faltan imágenes para smoke/{split}")
        chosen = sorted(rng.sample(images, count))
        listing = root / f"smoke_{split}.txt"
        listing.write_text("\n".join(str(p) for p in chosen) + "\n", encoding="utf-8")
        lists[split] = str(listing)
    import yaml
    path = root / "smoke.yaml"
    path.write_text(yaml.safe_dump({"path": str((root / "yolo").resolve()), "train": lists["train"], "val": lists["val"], "names": dict(enumerate(MISSION_CLASSES))}, sort_keys=False), encoding="utf-8")
    return path
