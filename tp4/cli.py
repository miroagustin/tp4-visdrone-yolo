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
    mission = sub.add_parser("mission", help="Evalúa best.pt con las clases de la misión (persona y vehículo) sin reentrenar.")
    mission.add_argument("run", type=Path)
    mission.add_argument("--split", choices=("val", "test"), default="val",
                         help="test-dev queda reservado para la evaluación final.")
    resolution = sub.add_parser("resolution", help="Evalúa best.pt en DET val con 640/960/1280 px y mosaicos, clases de la misión.")
    resolution.add_argument("run", type=Path)
    resolution.add_argument("--variants", nargs="+", help="Variantes de tp4.inference.VARIANTS; agrega al JSON existente.")
    video = sub.add_parser("video", help="Detección por objeto en VisDrone-VID val (requiere data/raw/VisDrone2019-VID-val).")
    video.add_argument("run", type=Path)
    video.add_argument("--variants", nargs="+", default=["full640", "full1280", "mosaicos"],
                       help="Variantes de tp4.inference.VARIANTS; las ya calculadas se leen del caché.")
    demo = sub.add_parser("demo", help="Video de demostración sobre una secuencia limpia de VisDrone-VID (usa el caché de video).")
    demo.add_argument("run", type=Path)
    demo.add_argument("--sequence", default="uav0000117_02622_v")
    demo.add_argument("--variant", default="full1280")
    wiki = sub.add_parser("wiki", help="Controla la wiki OKF (wiki/).")
    wiki.add_argument("action", choices=("check",))
    informe = sub.add_parser("informe", help="Genera informe/informe_tp4.pdf desde la wiki.")
    informe.add_argument("--solo-tex", action="store_true", help="Solo escribe el .tex, sin compilar con pdflatex.")
    informe.add_argument("--figuras", action="store_true", help="Regenera también los PNG de los diagramas TikZ de la wiki.")
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
    elif args.command == "mission":
        from .mission import evaluate_run
        result = evaluate_run(root, args.run.resolve(), split=args.split)
        print(json.dumps({k: {"map50": v["map50"], "map50_95": v["map50_95"]} for k, v in result["variants"].items()}, indent=2))
        print(f"Informe: {args.run / 'mission_eval' / (args.split + '.md')}")
    elif args.command == "resolution":
        from .inference import evaluate_resolution
        from .inference import VARIANTS
        evaluate_resolution(root, args.run.resolve(), variants=tuple(args.variants or VARIANTS))
        print(f"Resultados: {args.run / 'mission_eval' / 'resolution_val.json'}")
    elif args.command == "video":
        from .video import evaluate_video
        evaluate_video(root, args.run.resolve(), variants=tuple(args.variants))
        print(f"Resultados: {args.run / 'mission_eval' / 'video_val.json'}")
    elif args.command == "demo":
        from .demo_video import render_demo
        print(json.dumps(render_demo(root, args.run.resolve(), sequence=args.sequence, variant=args.variant), indent=2, ensure_ascii=False))
    elif args.command == "wiki":
        from .wiki import check_bundle
        errors = check_bundle(root / "wiki")
        print("\n".join(errors) if errors else "Wiki conforme a OKF v0.2 y a las convenciones del informe.")
        raise SystemExit(1 if errors else 0)
    elif args.command == "informe":
        from .wiki_latex import build_report
        print(build_report(root, compile_pdf=not args.solo_tex, refresh_pngs=args.figuras))
    elif args.command == "present":
        from .report import presentation
        print(presentation(root, args.run))


if __name__ == "__main__":
    main()
