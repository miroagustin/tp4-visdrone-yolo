import numpy as np

from tp4.data import CLASSES
from tp4.mission import MISSION_CLASSES, MISSION_GROUPS, TO_MISSION, evaluate_samples, match_pairs, box_iou, size_bins


def test_every_visdrone_class_has_one_group():
    members = [name for group in MISSION_GROUPS.values() for name in group]
    assert sorted(members) == sorted(CLASSES)
    for i, name in enumerate(CLASSES):
        assert name in MISSION_GROUPS[MISSION_CLASSES[TO_MISSION[i]]]


def test_matching_is_one_to_one_by_class():
    gt = np.array([[0, 0, 10, 10], [20, 20, 30, 30]], dtype=float)
    pred = np.array([[0, 0, 10, 10], [1, 1, 10, 10], [20, 20, 30, 30]], dtype=float)
    pairs = match_pairs(box_iou(gt, pred), np.array([3, 3, 4]), np.array([3, 3]), 0.5)
    assert sorted(map(tuple, pairs)) == [(0, 0)]


def sample(pred_cls, gt_cls, conf=(0.9,)):
    box = np.array([[0, 0, 20, 20]], dtype=float)
    return box, np.array(conf, dtype=float), np.array(pred_cls), box, np.array(gt_cls), np.array([20.0])


def test_van_predicted_as_car_counts_only_for_mission():
    result = evaluate_samples([sample([3], [4])])
    ten = next(p for p in result["visdrone10"]["operating_points"] if p["conf"] == 0.25)
    grouped = next(p for p in result["mision"]["operating_points"] if p["conf"] == 0.25)
    assert ten["all_objects"]["recall"] == 0.0
    assert grouped["per_class"]["vehiculo"]["recall"] == 1.0
    assert result["mision"]["per_class"]["vehiculo"]["ap50"] > 0.99


def test_two_class_model_is_not_regrouped():
    # Clase 1 es vehículo en un modelo de 2 clases; como índice VisDrone sería people (persona).
    result = evaluate_samples([sample([1], [1])], pred_nc=2, gt_nc=2)
    assert "visdrone10" not in result
    point = next(p for p in result["mision"]["operating_points"] if p["conf"] == 0.25)
    assert point["per_class"]["vehiculo"]["recall"] == 1.0
    assert point["per_class"]["persona"]["fp"] == 0
    # Línea base de 10 clases contra etiquetas ya agrupadas: car (3) contra vehículo (1).
    mixed = evaluate_samples([sample([3], [1])], pred_nc=10, gt_nc=2)
    assert next(p for p in mixed["mision"]["operating_points"] if p["conf"] == 0.25)["per_class"]["vehiculo"]["recall"] == 1.0


def test_fusion_removes_duplicate_after_grouping():
    boxes = np.array([[0, 0, 20, 20], [0, 0, 20, 19]], dtype=float)
    gt = np.array([[0, 0, 20, 20]], dtype=float)
    data = [(boxes, np.array([0.8, 0.6]), np.array([3, 4]), gt, np.array([3]), np.array([20.0]))]
    result = evaluate_samples(data)
    direct = next(p for p in result["mision"]["operating_points"] if p["conf"] == 0.25)["per_class"]["vehiculo"]
    fused = next(p for p in result["mision_fusion"]["operating_points"] if p["conf"] == 0.25)["per_class"]["vehiculo"]
    assert (direct["tp"], direct["fp"]) == (1, 1)
    assert (fused["tp"], fused["fp"]) == (1, 0)


def test_low_confidence_and_size_bins():
    result = evaluate_samples([sample([0], [1], conf=(0.1,))])
    point = next(p for p in result["mision"]["operating_points"] if p["conf"] == 0.25)
    assert point["per_class"]["persona"]["recall"] == 0.0
    assert point["recall_by_size"]["persona"]["16-32"]["objects"] == 1
    assert list(size_bins(np.array([3.9, 4, 12, 40]))) == [0, 1, 2, 4]
