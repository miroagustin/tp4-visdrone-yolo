import numpy as np

from tp4.inference import tile_grid
from tp4.video import evaluate_sequence, summarize


def box(x, y, s=10):
    return [x, y, x + s, y + s]


def gt_frame(boxes, ids, groups):
    b = np.array(boxes, dtype=float)
    return b, np.array(ids), np.array(groups), np.sqrt((b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1]))


def test_object_detected_once_and_first_delay():
    # Una persona (id 7, grupo 0) visible en los cuadros 1-4; se detecta solo en el 3.
    gt = {f: gt_frame([box(10, 10)], [7], [0]) for f in (1, 2, 3, 4)}
    preds = {3: (np.array([box(10, 10)], dtype=float), np.array([0.9]), np.array([1]))}  # clase VisDrone "people"
    part = evaluate_sequence([1, 2, 3, 4], gt, {}, preds, conf=0.25, nc=10)
    result = summarize([part], seconds=4 / 30, fps=30)["persona"]
    assert result["objects"] == 1 and result["detected_once"] == 1.0 and result["detected_3"] == 0.0
    assert abs(result["first_detection_s_median"] - 2 / 30) < 1e-9 and result["frame_recall"] == 0.25
    # Con submuestreo 1 de cada 2 (cuadros 1 y 3) sigue detectada; con los cuadros 2 y 4, no.
    assert summarize([evaluate_sequence([1, 3], gt, {}, preds, 0.25, 10)], 1, 30)["persona"]["detected_once"] == 1.0
    assert summarize([evaluate_sequence([2, 4], gt, {}, preds, 0.25, 10)], 1, 30)["persona"]["detected_once"] == 0.0


def test_false_alarms_skip_ignored_regions_and_low_confidence():
    preds = {1: (np.array([box(0, 0), box(100, 100), box(200, 200)], dtype=float), np.array([0.9, 0.9, 0.1]), np.array([3, 3, 3]))}
    ign = {1: np.array([[95, 95, 120, 120]], dtype=float)}
    part = evaluate_sequence([1], {}, ign, preds, conf=0.25, nc=10)
    assert part["fp"].tolist() == [0, 1]  # solo la primera caja de vehículo es falsa alarma


def test_tiles_cover_image_with_overlap():
    grid = tile_grid(1400, 788)
    assert len(grid) == 6 and grid[-1][2:] == (1400, 788)
    assert tile_grid(600, 400) == [(0, 0, 600, 400)]


def test_scaled_tiling_reduces_inferences_on_4k():
    from tp4.inference import inferences_per_image
    assert inferences_per_image(3840, 2160, "mosaicos") == 33
    assert inferences_per_image(3840, 2160, "mosaicos1920") == 9
    assert inferences_per_image(1400, 788, "mosaicos1920") == inferences_per_image(1400, 788, "mosaicos")
    assert inferences_per_image(1400, 788, "full1280") == 1
