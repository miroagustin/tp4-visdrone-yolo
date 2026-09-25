"""Lectura y presentación de artefactos: no importa torch ni ejecuta inferencia."""
import json
from pathlib import Path

from IPython.display import Image, Markdown, display


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None  # Un proceso de entrenamiento puede estar escribiendo el manifiesto.


def context(root, selected=None):
    root = Path(root).resolve()
    if selected:
        run = (root / selected).resolve()
        info = read_json(run / "run.json")
        if not info or info.get("status") != "finished":
            raise ValueError(f"El run seleccionado no está completo: {run}")
    else:
        run = None
        info = None
        for profile in ("full", "smoke"):
            for path in sorted((root / "runs" / profile).glob("*/run.json"), reverse=True):
                candidate = read_json(path)
                if candidate and candidate.get("status") == "finished":
                    run, info = path.parent, candidate
                    break
            if run:
                break
    unfinished = [p.parent.name for p in (root / "runs" / "full").glob("*/run.json")
                  if (read_json(p) or {}).get("status") == "running"]
    return {"root": root, "run": run, "info": info, "unfinished": unfinished,
            "audit": read_json(root / "data" / "audit.json")}


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
        display(Markdown("Hay manifiestos full sin cierre; no se incorporan sus métricas parciales. El estado `running` guardado no prueba que el proceso siga activo."))


def dataset_table(ctx):
    audit = ctx["audit"]
    if not audit:
        display(Markdown("Auditoría local pendiente. Cantidades de referencia: 6471 train, 548 val y 1610 test-dev [1, 2]."))
        return
    table(["Partición", "Imágenes auditadas", "Cajas válidas", "Score 0 excluido", "Uso"],
          [(name, audit[name]["images"], sum(audit[name]["class_counts"].values()), audit[name]["rows"].get("ignored_score", 0), use)
           for name, use in (("train", "Ajustar pesos"), ("val", "Seleccionar / diagnosticar"), ("test-dev", "Evaluación final reservada"))])
    invalid = sum(v["rows"].get("invalid_box", 0) for v in audit.values())
    display(Markdown(f"**Control de calidad:** {invalid} caja(s) con tamaño inválido excluida(s). Imágenes y anotaciones originales conservadas; detalles en `data/audit.json`."))


def protocol(ctx):
    info = ctx["info"]
    if not info:
        display(Markdown("Sin ejecución seleccionada. La configuración prevista se encuentra en `config.yaml`."))
        return
    s = info["settings"]
    table(["Variable", "Ejecución presentada"], [("Modelo / inicialización", f"{s['model']} · pesos preentrenados COCO"),
          ("Perfil / épocas", f"{s['profile']} / {s['epochs']}"),
          ("Train / val", f"{s.get('train_images') or 'split completo'} / {s.get('val_images') or 'split completo'} imágenes"),
          ("Resolución / batch / semilla", f"{s['imgsz']} px / {s['batch']} / {s['seed']}"),
          ("GPU", info["versions"].get("gpu") or "No registrada"),
          ("PyTorch / Ultralytics", f"{info['versions']['torch']} / {info['versions']['ultralytics']}")])


def metrics(ctx, per_class=False):
    info = ctx["info"]
    if not info or not info.get("metrics"):
        display(Markdown("**Métricas pendientes.** No se sustituyen valores faltantes por cero."))
        return
    m = info["metrics"]
    status(ctx)
    keys = ("precision", "recall", "map50", "map50_95")
    headers = ["Clase" if per_class else "Evaluación", "Precision (%)", "Recall (%)", "mAP@0.5 (%)", "mAP@0.5:0.95 (%)"]
    rows = [(name, *[f"{values[k] * 100:.4f}" for k in keys]) for name, values in m.get("per_class", {}).items()] if per_class else [("Validación", *[f"{m[k] * 100:.4f}" for k in keys])]
    table(headers, rows)
    display(Markdown("Porcentajes sobre la validación de esta ejecución. P/R agregadas por el evaluador; no corresponden necesariamente al umbral 0,25 de la galería. Métricas estándar de Ultralytics, no del evaluador oficial VisDrone."))


def figure(ctx, relative, caption, *, run=False, width=900, first_row=False):
    base = ctx["run"] if run else ctx["root"]
    if base is None or not (base / relative).exists():
        display(Markdown(f"**Figura pendiente:** {caption}"))
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
        display(Markdown("Análisis de errores pendiente: `python -m tp4.cli analyze RUTA_RUN`."))
        return
    table(["Imágenes", "Confianza", "IoU de asociación", "TP", "FP", "FN"], [[result[k] for k in ("images", "confidence", "iou", "tp", "fp", "fn")]])
    if result["tp"] == result["fp"] == 0:
        display(Markdown("**En esta muestra no hubo detecciones por encima del umbral elegido.** Todos los objetos anotados quedaron como falsos negativos. No demuestra qué clase funcionará mejor después de entrenar full."))
    else:
        display(Markdown("Asociación uno a uno, misma clase e IoU ≥ umbral. Son conteos de una muestra, no métricas de todo el conjunto."))


def latency(ctx):
    result = read_json(ctx["run"] / "latency.json") if ctx["run"] else None
    if not result:
        display(Markdown("Latencia pendiente de medición; no se estima a partir del tiempo de entrenamiento."))
        return
    table(["Tiempo por imagen", "GPU", "Resolución / batch", "Calentamiento / repeticiones"],
          [[f"{result['ms_per_image']:.2f} ms", result.get("gpu") or result["device"], f"{result['imgsz']} / {result['batch']}", f"{result['warmup']} / {result['repeats']}"]])
    display(Markdown(f"Condición: {result['scope']}. Una imagen repetida no representa la variabilidad de escenas ni el rendimiento en un dron."))


def conclusion(ctx):
    info = ctx["info"]
    if not info or not info.get("metrics"):
        display(Markdown("**Conclusión actual:** todavía no hay evidencia experimental guardada. El próximo paso es ejecutar y evaluar el protocolo."))
        return
    s, m = info["settings"], info["metrics"]
    if s["profile"] == "smoke":
        display(Markdown(f"**El flujo completo funciona; la capacidad de detección aún no está demostrada.**\n\n"
            f"Con {s['epochs']} épocas y {s['train_images']} imágenes train, mAP@0.5 fue **{m['map50']*100:.4f}%** sobre {s['val_images']} imágenes val. "
            "Este resultado es insuficiente para concluir utilidad en percepción robótica.\n\n"
            "**Próximo paso:** entrenar full, estudiar errores por clase y evaluar una vez en test-dev después de fijar el modelo. La comparación 640/960 queda como extensión controlada."))
    else:
        display(Markdown(f"**Resultado de validación:** mAP@0.5 **{m['map50']*100:.4f}%** y mAP@0.5:0.95 **{m['map50_95']*100:.4f}%**. "
                         "Interpretar estos valores junto con clases, ejemplos y costes de inferencia; no implican por sí solos aptitud para despliegue."))
    test = read_json(ctx["run"] / "test_dev.json")
    display(Markdown("**Test-dev: pendiente; sin métrica final independiente.**" if test is None else f"**Test-dev guardado:** mAP@0.5 {test['map50']*100:.4f}%; mAP@0.5:0.95 {test['map50_95']*100:.4f}%."))
