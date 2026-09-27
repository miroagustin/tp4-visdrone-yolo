"""Lectura y presentación de artefactos: no importa torch ni ejecuta inferencia."""
import json
from pathlib import Path

from IPython.display import HTML, Image, Markdown, display


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None  # Un proceso de entrenamiento puede estar escribiendo el manifiesto.


def context(root, selected=None, final_only=False):
    root = Path(root).resolve()
    if selected:
        run = (root / selected).resolve()
        info = read_json(run / "run.json")
        if not info or info.get("status") != "finished":
            raise ValueError(f"El run seleccionado no está completo: {run}")
        if final_only and info["settings"]["profile"] != "full":
            raise ValueError("El informe final requiere una ejecución full.")
    else:
        run = None
        info = None
        for profile in (("full",) if final_only else ("full", "smoke")):
            for path in sorted((root / "runs" / profile).glob("*/run.json"), reverse=True):
                candidate = read_json(path)
                if candidate and candidate.get("status") == "finished":
                    run, info = path.parent, candidate
                    break
            if run:
                break
    unfinished = [p.parent.name for p in (root / "runs" / "full").glob("*/run.json")
                  if (read_json(p) or {}).get("status") == "running"]
    protocol_info = info
    if protocol_info is None:
        for path in sorted((root / "runs" / "full").glob("*/run.json"), reverse=True):
            candidate = read_json(path)
            if candidate and candidate.get("settings"):
                protocol_info = candidate
                break
    return {"root": root, "run": run, "info": info, "protocol_info": protocol_info, "unfinished": unfinished,
            "audit": read_json(root / "data" / "audit.json")}


def space(height=160):
    display(HTML(f'<div class="result-space" style="min-height:{height}px"></div>'))


def table(headers, rows):
    def escape(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(map(escape, headers)) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(map(escape, row)) + " |" for row in rows]
    display(Markdown("\n".join(lines)))


def status(ctx):
    info = ctx["info"]
    if not info:
        display(Markdown("**SIN RESULTADOS GUARDADOS.** El diseño experimental está disponible; aún no hay métricas que presentar."))
        return
    profile = info["settings"]["profile"]
    message = "Prueba técnica de funcionamiento; experimento académico pendiente." if profile == "smoke" else "Entrenamiento académico completado; consultar abajo el estado de test-dev."
    display(Markdown(f"**Estado: {profile.upper()} · ejecución `{ctx['run'].name}`**  \n{message}"))
    if ctx["unfinished"]:
        display(Markdown("Las ejecuciones full sin cierre quedan fuera de estas cifras; se muestran sólo resultados terminados."))


def dataset_table(ctx):
    audit = ctx["audit"]
    if not audit:
        space()
        return
    settings = (ctx.get("protocol_info") or {}).get("settings", {})
    test_use = ("Evaluación y seguimiento cualitativo" if settings.get("epoch_preview", {}).get("enabled")
                else "Evaluación final reservada")
    table(["Partición", "Imágenes auditadas", "Cajas válidas", "Score 0 excluido", "Uso"],
          [(name, audit[name]["images"], sum(audit[name]["class_counts"].values()), audit[name]["rows"].get("ignored_score", 0), use)
           for name, use in (("train", "Ajustar pesos"), ("val", "Seleccionar / diagnosticar"), ("test-dev", test_use))])
    invalid = sum(v["rows"].get("invalid_box", 0) for v in audit.values())
    display(Markdown(f"**Control de calidad:** se excluyeron {invalid} cajas con tamaño inválido. Se conservaron las imágenes y anotaciones originales."))


def protocol(ctx):
    info = ctx["protocol_info"]
    if not info:
        space()
        return
    s = info["settings"]
    table(["Variable", "Configuración experimental"], [("Modelo / inicialización", f"{s['model']} · pesos preentrenados COCO"),
          ("Épocas configuradas", s['epochs']),
          ("Train / val", f"{s.get('train_images') or 'split completo'} / {s.get('val_images') or 'split completo'} imágenes"),
          ("Resolución / batch / semilla", f"{s['imgsz']} px / {s['batch']} / {s['seed']}"),
          ("GPU", info["versions"].get("gpu") or "No registrada"),
          ("PyTorch / Ultralytics", f"{info['versions']['torch']} / {info['versions']['ultralytics']}")])


def runs_table(ctx):
    """Ejecuciones full registradas; de las que no terminaron solo se informa el avance."""
    import yaml
    rows = []
    for path in sorted((ctx["root"] / "runs" / "full").glob("*/run.json")):
        info = read_json(path)
        if not info:
            continue
        s, m = info["settings"], info.get("metrics") or {}
        try:
            classes = len(m["per_class"]) if m else len(yaml.safe_load(Path(s["data_yaml"]).read_text(encoding="utf-8"))["names"])
        except (OSError, KeyError, TypeError):
            classes = "—"
        if info.get("status") == "finished":
            state = "terminada"
        elif info.get("status") == "running":
            csv = path.parent / "train" / "results.csv"
            done = len(csv.read_text(encoding="utf-8").splitlines()) - 1 if csv.exists() else 0
            state = f"en curso · época {done} de {s['epochs']}"
        else:
            state = "fallida"
        rows.append((path.parent.name, s["model"].removesuffix(".pt"), f"{s['imgsz']} px", classes, state, pct(m.get("map50"))))
    if not rows:
        space()
        return
    table(["Ejecución", "Modelo", "Entrada", "Clases", "Estado", "mAP@0.5 (val)"], rows)
    display(Markdown("El mAP con 10 clases y con 2 clases no se compara entre sí. De las ejecuciones en curso no se informan métricas parciales."))


def metrics(ctx, per_class=False):
    info = ctx["info"]
    if not info or not info.get("metrics"):
        space(220 if per_class else 140)
        return
    m = info["metrics"]
    keys = ("precision", "recall", "map50", "map50_95")
    def percent(value):
        value *= 100
        return "<0.0001" if 0 < value < 0.0001 else f"{value:.4f}"
    headers = ["Clase" if per_class else "Evaluación", "Precision (%)", "Recall (%)", "mAP@0.5 (%)", "mAP@0.5:0.95 (%)"]
    rows = [(name, *[percent(values[k]) for k in keys]) for name, values in m.get("per_class", {}).items()] if per_class else [("Validación", *[percent(m[k]) for k in keys])]
    table(headers, rows)
    display(Markdown("Porcentajes sobre la validación de esta ejecución. P/R agregadas por el evaluador; no corresponden necesariamente al umbral 0,25 de la galería. Métricas estándar de Ultralytics, no del evaluador oficial VisDrone."))


def figure(ctx, relative, caption, *, run=False, width=900, first_row=False):
    base = ctx["run"] if run else ctx["root"]
    if base is None or not (base / relative).exists():
        space(200)
        return
    if first_row:
        from PIL import Image as PILImage
        from io import BytesIO
        with PILImage.open(base / relative) as original:
            crop = original.crop((0, 0, original.width, min(500, original.height)))
            buffer = BytesIO()
            crop.save(buffer, format="PNG")
        display(Image(data=buffer.getvalue(), width=width))
    else:
        display(Image(filename=str(base / relative), width=width))
    display(Markdown(f"*{caption}*"))


def errors(ctx):
    run = ctx["run"]
    result = read_json(run / "error_sample.json") if run else None
    if not result:
        space()
        return
    table(["Imágenes", "Confianza", "IoU de asociación", "TP", "FP", "FN"], [[result[k] for k in ("images", "confidence", "iou", "tp", "fp", "fn")]])
    if result["tp"] == result["fp"] == 0:
        display(Markdown("En esta muestra no hubo detecciones por encima del umbral elegido. Todos los objetos anotados quedaron como falsos negativos."))
    else:
        display(Markdown("Asociación uno a uno, misma clase e IoU ≥ umbral. Son conteos de una muestra, no métricas de todo el conjunto."))


def latency(ctx):
    result = read_json(ctx["run"] / "latency.json") if ctx["run"] else None
    if not result:
        space()
        return
    table(["Tiempo por imagen", "GPU", "Resolución / batch", "Calentamiento / repeticiones"],
          [[f"{result['ms_per_image']:.2f} ms", result.get("gpu") or result["device"], f"{result['imgsz']} / {result['batch']}", f"{result['warmup']} / {result['repeats']}"]])
    display(Markdown(f"Condición: {result['scope']}. Una imagen repetida no representa la variabilidad de escenas ni el rendimiento en un dron."))


def conclusion(ctx):
    info = ctx["info"]
    if not info or not info.get("metrics"):
        space(240)
        return
    s, m = info["settings"], info["metrics"]
    if s["profile"] == "smoke":
        display(Markdown(f"**El flujo completo funciona; la capacidad de detección aún no está demostrada.**\n\n"
            f"Con {s['epochs']} épocas y {s['train_images']} imágenes train, mAP@0.5 fue **{m['map50']*100:.4f}%** sobre {s['val_images']} imágenes val. "
            "Este resultado es insuficiente para concluir utilidad en percepción robótica."))
    else:
        display(Markdown(f"**Resultado de validación ({s['model'].removesuffix('.pt')}, {s['imgsz']} px, {len(m['per_class'])} clases):** mAP@0.5 **{m['map50']*100:.4f}%** y mAP@0.5:0.95 **{m['map50_95']*100:.4f}%**. "
                         "Estos valores caracterizan la detección en el conjunto de validación. La diferencia entre ambos criterios refleja el efecto de exigir una localización más precisa."))
    test = read_json(ctx["run"] / "test_dev.json")
    if test:
        display(Markdown(f"**Evaluación independiente en test-dev:** mAP@0.5 {test['map50']*100:.4f}%; mAP@0.5:0.95 {test['map50_95']*100:.4f}%."))


# ---------------------------------------------------------------- misión embarcada
VARIANT_NAMES = {"full640": "Imagen completa 640 px", "full960": "Imagen completa 960 px", "full1280": "Imagen completa 1280 px",
                 "mosaicos": "Mosaicos nativos", "mosaicos1280": "Mosaicos nativos + 1280 px",
                 "mosaicos1920": "Mosaicos sobre imagen de 1920 px", "mosaicos2560": "Mosaicos sobre imagen de 2560 px"}


def pct(value):
    return "—" if value is None else f"{value * 100:.1f} %".replace(".", ",")


def mission_eval(ctx, name):
    return read_json(ctx["run"] / "mission_eval" / name) if ctx["run"] else None


def mission_classes(ctx):
    result = mission_eval(ctx, "val.json")
    if not result:
        space()
        return
    fused = result["variants"]["mision_fusion"]
    point = next(p for p in fused["operating_points"] if p["conf"] == 0.25)
    table(["Clase de la misión", "Clases VisDrone", "Objetos (val)", "AP50", "Precisión / recall por cuadro"],
          [(name, ", ".join(result["groups"][name]), fused["per_class"][name]["objects"], pct(fused["per_class"][name].get("ap50")),
            f"{pct(point['per_class'][name]['precision'])} / {pct(point['per_class'][name]['recall'])}") for name in fused["classes"]])
    display(Markdown("Mismo modelo de 10 clases, reagrupado después de la inferencia (640 px, confianza 0,25, IoU 0,5). "
                     "El conductor de una moto o bicicleta está anotado como persona; el vehículo que conduce, como vehículo."))


def resolution(ctx):
    result = mission_eval(ctx, "resolution_val.json")
    if not result:
        space()
        return
    rows = []
    for key, r in result["variants"].items():
        point = next(p for p in r["mision"]["operating_points"] if p["conf"] == 0.25)
        rows.append((VARIANT_NAMES.get(key, key), f"{r['inferences_per_image']:.1f}".replace(".", ","), f"{r['ms_per_image']:.0f}",
                     pct(r["mision"]["map50"]), pct(point["per_class"]["persona"]["recall"]), pct(point["per_class"]["vehiculo"]["recall"])))
    table(["Variante", "Inferencias por imagen", "ms por imagen (laptop)", "mAP50 misión", "Recall persona", "Recall vehículo"], rows)
    display(Markdown(f"Mismo `best.pt`, sin reentrenar, en las {result['images']} imágenes de validación de DET. Recall por cuadro con confianza 0,25. "
                     "El tiempo es de la GPU de la laptop: en una placa el costo crece cerca de la cantidad de píxeles."))


def pass_detection(ctx, variants=("full640", "full1280", "mosaicos1920", "mosaicos1280")):
    result = mission_eval(ctx, "video_val.json")
    if not result:
        space()
        return
    def get(variant, stride):
        return next(e for e in result["variants"][variant]["evaluations"] if e["stride"] == stride and e["conf"] == 0.25)["limpias"]
    from .inference import inferences_per_image
    clean = {s: v for s, v in result["sequences"].items() if not v["seen_in_det_train"]}
    frames = sum(v["frames"] for v in clean.values())
    rows = []
    for key in (v for v in variants if v in result["variants"]):
        calls = sum(inferences_per_image(*v["size"], key) * v["frames"] for v in clean.values()) / frames
        rows.append((VARIANT_NAMES.get(key, key), f"{calls:.1f}".replace(".", ","), *(pct(get(key, k)["persona"]["detected_once"]) for k in (3, 6, 15)),
                     pct(get(key, 6)["vehiculo"]["detected_once"])))
    table(["Variante", "Inferencias por cuadro", "Personas a 10 FPS", "Personas a 5 FPS", "Personas a 2 FPS", "Vehículos a 5 FPS"], rows)
    persons = get("full1280", 6)["persona"]
    display(Markdown(f"Objetos detectados al menos una vez durante la pasada, en las {len(clean)} secuencias de VisDrone-VID que no comparten video "
                     f"con el entrenamiento ({persons['objects']} personas). Confianza 0,25 y 30 FPS nominales. "
                     f"**Objetivo: 85 % de las personas a 5 FPS o más.** Con 1280 px: {pct(persons['detected_once'])} a 5 FPS y "
                     f"{pct(get('full1280', 3)['persona']['detected_once'])} a 10 FPS."))


def video_demo(ctx):
    import base64
    demos = sorted((ctx["run"] / "mission_eval").glob("demo_*.json")) if ctx["run"] else []
    info = read_json(demos[0]) if demos else None
    video = demos[0].parent / info["video"] if info else None
    if not info or not video.exists():
        space(300)
        return
    kind = "video/mp4" if video.suffix == ".mp4" else "video/webm"
    data = base64.b64encode(video.read_bytes()).decode("ascii")
    display(HTML(f'<video controls autoplay muted loop playsinline style="width:100%;max-height:62vh;background:#000">'
                 f'<source src="data:{kind};base64,{data}" type="{kind}"></video>'))
    found = info["detected_once"]
    display(Markdown(f"*Secuencia `{info['sequence']}` (no vista en entrenamiento), {VARIANT_NAMES.get(info['variant'], info['variant']).lower()}, "
                     f"{info['fps']:.0f} FPS simulados. Al final de la pasada: {found['persona']['found']} de {found['persona']['seen']} personas y "
                     f"{found['vehiculo']['found']} de {found['vehiculo']['seen']} vehículos detectados al menos una vez. "
                     "Naranja: persona; celeste: vehículo; rojo: persona que todavía no se detectó en ningún cuadro.*"))
