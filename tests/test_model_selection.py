import json

import pytest

from tp4.experiment import resolve, training_settings


@pytest.mark.parametrize("configured,override,expected", [
    (True, None, "yolo26n.pt"),
    (False, None, "yolo11n.pt"),
    (True, False, "yolo11n.pt"),
    (False, True, "yolo26n.pt"),
])
def test_flag_resolution(tmp_path, monkeypatch, configured, override, expected):
    monkeypatch.setattr("tp4.experiment.load_config", lambda root: {
        "use_yolo26": configured, "data_dir": "data", "runs_dir": "runs",
        "profiles": {"full": {"epochs": 50, "batch": 4, "imgsz": 640}},
    })
    settings = resolve(tmp_path, "full", use_yolo26=override)
    assert settings["model"] == expected
    assert settings["use_yolo26"] == (expected == "yolo26n.pt")


def test_resume_preserves_original_model_and_configuration(tmp_path, monkeypatch):
    run = tmp_path / "runs" / "full" / "original"
    checkpoint = run / "train" / "weights" / "last.pt"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"placeholder; this test does not load torch")
    original = {"profile": "full", "model": "yolo11n.pt", "epochs": 50, "batch": 4, "imgsz": 640}
    (run / "run.json").write_text(json.dumps({"settings": original}), encoding="utf-8")
    def reject_config_read(root):
        pytest.fail("Resume must not consult the new model default")
    monkeypatch.setattr("tp4.experiment.load_config", reject_config_read)
    settings, resumed = training_settings(tmp_path, "full", resume=checkpoint)
    assert settings == original
    assert resumed == run


@pytest.mark.parametrize("override", [{"use_yolo26": True}, {"use_yolo26": False}, {"batch": 2}, {"imgsz": 960}])
def test_resume_rejects_protocol_overrides(tmp_path, override):
    with pytest.raises(ValueError, match="conserva"):
        training_settings(tmp_path, "full", resume=tmp_path / "last.pt", **override)
