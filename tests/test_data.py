from pathlib import Path
import json
from PIL import Image

from tp4.data import convert_row, prepare_split


def test_conversion_rules():
    row, reason = convert_row("100,50,200,100,1,4,0,0", 1000, 500)
    assert row == "3 0.20000000 0.20000000 0.20000000 0.20000000"
    assert reason == "included"
    assert convert_row("0,0,10,10,0,4", 100, 100)[1] == "ignored_score"
    assert convert_row("0,0,10,10,1,11", 100, 100)[1] == "excluded_category"
    assert convert_row("0,0,-1,10,1,4", 100, 100)[1] == "invalid_box"
    assert convert_row("200,0,10,10,1,4", 100, 100)[1] == "outside_image"
    row, reason = convert_row("-5,0,10,10,1,1", 100, 100)
    assert reason == "clipped" and row.startswith("0 ")


def test_missing_annotation_rejected(tmp_path: Path, monkeypatch):
    raw = tmp_path / "raw" / "VisDrone2019-DET-val"
    (raw / "images").mkdir(parents=True)
    (raw / "annotations").mkdir()
    Image.new("RGB", (10, 10)).save(raw / "images" / "a.jpg")
    (raw / ".archive_sha256").write_text("abc", encoding="ascii")
    monkeypatch.setattr("tp4.data.extract_archive", lambda root, split: raw)
    import pytest
    with pytest.raises(RuntimeError, match="incompletas"):
        prepare_split(tmp_path, "val")


def test_valid_split_is_reused(tmp_path: Path, monkeypatch):
    raw = tmp_path / "raw" / "VisDrone2019-DET-val"
    (raw / "images").mkdir(parents=True)
    (raw / "annotations").mkdir()
    Image.new("RGB", (100, 100)).save(raw / "images" / "a.jpg")
    (raw / "annotations" / "a.txt").write_text("10,10,10,10,1,4\n", encoding="utf-8")
    (raw / ".archive_sha256").write_text("abc", encoding="ascii")
    monkeypatch.setattr("tp4.data.extract_archive", lambda root, split: raw)
    first = prepare_split(tmp_path, "val")
    label = tmp_path / "yolo" / "labels" / "val" / "a.txt"
    timestamp = label.stat().st_mtime_ns
    second = prepare_split(tmp_path, "val")
    assert first == second and label.stat().st_mtime_ns == timestamp
    assert first["class_counts"]["car"] == 1
    label.write_text("corrupted", encoding="utf-8")
    third = prepare_split(tmp_path, "val")
    assert third == first
    assert label.read_text(encoding="utf-8").startswith("3 ")
