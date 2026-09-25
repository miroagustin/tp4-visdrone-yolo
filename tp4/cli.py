"""Comandos reproducibles para datos, entrenamiento y presentación."""
import argparse
import json
from pathlib import Path

from .experiment import project_root


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    train = sub.add_parser("train")
    train.add_argument("profile", choices=("smoke", "full"))
    train.add_argument("--batch", type=int)
    train.add_argument("--imgsz", type=int)
    train.add_argument("--resume", type=Path)
    train.add_argument("--yolo26", action=argparse.BooleanOptionalAction, default=None,
                       help="Usar YOLO26n; --no-yolo26 selecciona YOLO11n. Sin flag: config.yaml.")
    test = sub.add_parser("test")
    test.add_argument("run", type=Path)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("run", type=Path)
    pres = sub.add_parser("present")
    pres.add_argument("--run", type=Path)
    args = parser.parse_args()
    root = project_root()
    if args.command == "prepare":
        from .data import prepare_all
        from .report import audit_plot, review_boxes
        result = prepare_all(root / "data")
        audit_plot(root / "data")
        review_boxes(root / "data")
        print(json.dumps({k: {"images": v["images"], "rows": v["rows"]} for k, v in result.items()}, indent=2))
    elif args.command == "train":
        from .experiment import train as run_train
        print(run_train(root, args.profile, batch=args.batch, imgsz=args.imgsz, use_yolo26=args.yolo26, resume=args.resume))
    elif args.command == "test":
        from .experiment import evaluate_test
        print(json.dumps(evaluate_test(args.run.resolve(), root / "data" / "visdrone.yaml"), indent=2))
    elif args.command == "analyze":
        from .report import error_gallery, measure_latency
        run = args.run.resolve()
        print(json.dumps({"errors": error_gallery(root, run), "latency": measure_latency(root, run)}, indent=2))
    elif args.command == "present":
        from .report import presentation
        print(presentation(root, args.run))


if __name__ == "__main__":
    main()
