"""Genera el notebook académico. No descarga datos ni inicia entrenamiento."""
from pathlib import Path
import hashlib
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
cells = []


def md(text, kind="presentation"):
    cell = nbf.v4.new_markdown_cell(text.strip())
    cell.metadata = {"tags": [kind], "slideshow": {"slide_type": "slide" if kind == "presentation" else "skip"}}
    cells.append(cell)


def code(text, kind="presentation"):
    cell = nbf.v4.new_code_cell(text.strip())
    cell.metadata = {"tags": [kind], "slideshow": {"slide_type": "fragment" if kind == "presentation" else "skip"}}
    cells.append(cell)


md("""<a id="portada"></a>
# Detección de personas y vehículos desde drones
### TP4 · Visión artificial · VisDrone2019-DET + YOLO11n

**Integrantes:** [completar] · **Entrega:** 8 de octubre de 2026

**Propósito:** estudiar el ajuste de un detector pequeño a escenas aéreas densas.

Las conclusiones se calculan a partir de una ejecución **terminada**. Un entrenamiento en curso no se presenta como resultado final.
""")
md("""### Cómo recorrer este notebook
**Público:** estudiantes y docentes de visión artificial. **Prerequisitos:** Python básico, imágenes digitales y nociones de entrenamiento/validación.

Al terminar podrás explicar el problema, justificar las particiones e interpretar métricas y límites.

- **PRESENTACIÓN:** relato y artefactos guardados. Ejecutar la celda de apertura siguiente y luego las celdas marcadas PRESENTACIÓN; no requiere entrenar.
- **APRENDIZAJE:** conceptos, ejercicios y evidencia de respaldo.
- **EJECUCIÓN:** preparación y cómputo, desactivados por defecto.

[1 Portada](#portada) · [2 Problema](#problema) · [3 Objetivos](#objetivos) · [4 Fundamentos](#fundamentos) · [5 Entorno](#entorno) · [6 Datos](#datos) · [7 Exploración](#exploracion) · [8 Protocolo](#protocolo) · [9 Entrenamiento](#entrenamiento) · [10 Evaluación](#evaluacion) · [11 Errores](#errores) · [12 Conclusiones](#conclusiones) · [13 Referencias](#referencias)

**Guion de 9 minutos:** problema y pregunta (1:00), datos y auditoría (1:30), protocolo (1:00), resultados y clases (2:00), errores y latencia (2:00), conclusión (1:00), referencias/cierre (0:30). Curvas y matriz quedan como respaldo para preguntas.
""", "learning")
md("""### Apertura del recorrido · PRESENTACIÓN
Carga JSON y figuras guardadas para presentar desde un kernel limpio. El perfil y el ID identifican el origen de las cifras. `RUN_ID` permite fijar un resultado; vacío selecciona el último full terminado o, en su defecto, smoke.
""", "learning")
code("""import os
import sys
from pathlib import Path
from IPython.display import display, Markdown

ROOT = Path(os.environ.get('TP4_ROOT', Path.cwd())).resolve()
if not (ROOT / 'config.yaml').exists() and (ROOT.parent / 'config.yaml').exists():
    ROOT = ROOT.parent
if not (ROOT / 'config.yaml').exists():
    raise FileNotFoundError('Definí TP4_ROOT al directorio tp4-yolo')
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tp4 import notebook_view as view

RUN_ID = None  # Ejemplo: 'runs/smoke/20260925T011344Z'
ctx = view.context(ROOT, RUN_ID)
view.status(ctx)
""")
md("""<a id="problema"></a>
## 2. La vista aérea dificulta localizar objetos pequeños · PRESENTACIÓN
La tarea recibe una imagen y devuelve **clase, caja y confianza**. Altura, oclusión y densidad reducen la información disponible por objeto.

En robótica, estas detecciones pueden alimentar seguimiento y conteo. Este TP estudia percepción sobre imágenes estáticas: no evalúa navegación, seguimiento temporal ni seguridad de un dron.
""")
md("""<a id="objetivos"></a>
## 3. ¿Qué aprende un detector pequeño al adaptarlo a VisDrone? · PRESENTACIÓN
**Objetivo:** ajustar YOLO11n a diez clases y describir precisión, cobertura y errores.

**Hipótesis de trabajo:** transfer learning puede aportar representaciones útiles, pero objetos diminutos y escenas densas seguirán siendo difíciles. Esta hipótesis requiere entrenamiento suficiente y evaluación; el smoke no la confirma.

**Evidencia necesaria:** protocolo trazable, métricas por clase, ejemplos confrontados con anotaciones y latencia. No se fija un umbral arbitrario de éxito sin una referencia comparable.
""")
md("""<a id="fundamentos"></a>
## 4. Fundamentos · APRENDIZAJE
YOLO predice cajas y clases en una pasada. *Transfer learning* reutiliza pesos de otro entrenamiento y ajusta la red al nuevo conjunto. Elegimos YOLO11n por su tamaño y coste de cómputo, compatibles con la GPU local; eso no demuestra que sea la mejor arquitectura para VisDrone [3].

**IoU = área de intersección / área de unión.** Una detección requiere acertar clase y ubicación.

| Métrica | Qué resume | Cómo leerla |
|---|---|---|
| Precision | TP / (TP + FP) | Proporción de predicciones correctas |
| Recall | TP / (TP + FN) | Proporción de objetos encontrados |
| AP | Área bajo la curva precision–recall de una clase | Usa un criterio de IoU |
| mAP@0.5 | Media de AP entre clases a IoU 0,5 | Tolera errores de ubicación mayores |
| mAP@0.5:0.95 | Media entre clases y diez IoU entre 0,50 y 0,95 | Exige localización más precisa |

Las clases COCO iniciales no equivalen a las diez clases finales. No se usa un COCO sin adaptar como baseline numérico directo.
""", "learning")
md("""<a id="entorno"></a>
## 5. Entorno reproducible · EJECUCIÓN
El diagnóstico opcional consulta versiones y GPU sin entrenar. Permite detectar cambios respecto del entorno guardado. `torch.version.cuda` identifica el runtime de la rueda; el número CUDA de `nvidia-smi` indica soporte del driver.

Local: kernel **TP4 VisDrone YOLO**. Colab: seguir README, definir `TP4_ROOT` y conservar PyTorch preinstalado si funciona. La GPU gratuita no está garantizada y el disco de sesión es temporal: respaldar checkpoints antes de cerrar.
""", "execution")
code("""DIAGNOSTICAR = False
if DIAGNOSTICAR:
    from tp4.experiment import versions
    view.table(['Propiedad', 'Valor actual'], versions().items())
""", "execution")
md("""<a id="datos"></a>
## 6. Los datos mantienen sus particiones oficiales · PRESENTACIÓN
VisDrone2019-DET contiene diez categorías de personas y vehículos [1, 2]. La tabla muestra cantidades **auditadas localmente**. Test-dev tiene etiquetas utilizables y se reserva para evaluación final.
""")
code("view.dataset_table(ctx)")
md("""### Clases y conversión · APRENDIZAJE
| Original → YOLO | Clase | Original → YOLO | Clase |
|---|---|---|---|
| 1 → 0 | pedestrian | 6 → 5 | truck |
| 2 → 1 | people | 7 → 6 | tricycle |
| 3 → 2 | bicycle | 8 → 7 | awning-tricycle |
| 4 → 3 | car | 9 → 8 | bus |
| 5 → 4 | van | 10 → 9 | motor |

`pedestrian` corresponde a personas de pie o caminando; `people`, a otras posturas [2]. Se incluyen filas con score 1 y categoría 1–10. Score 0 marca regiones ignoradas; las categorías restantes se excluyen.

Para imagen W×H, `(x,y,w,h)` se convierte en `((x+w/2)/W, (y+h/2)/H, w/W, h/H)`. Se registran recortes y descartes.

**Ejercicio:** convertí `(100,50,200,100)` en una imagen de 1000×500, categoría car (4). ¿Qué pasa si el alto vale cero?
""", "learning")
code("""# Resolución guiada: modificá valores y compará con el cálculo manual.
from tp4.data import convert_row
row, reason = convert_row('100,50,200,100,1,4,0,0', 1000, 500)
print(row, reason)  # 3 0.2 0.2 0.2 0.2; alto cero se excluye como invalid_box
""", "learning")
md("""### Preparación reutilizable · EJECUCIÓN
Descarga, valida y convierte conservando originales. Activar sólo para preparar el entorno; evitarlo si otro proceso está utilizando esos datos. Las figuras generadas permiten comprobar cajas y distribuciones.
""", "execution")
code("""PREPARAR_DATOS = False
if PREPARAR_DATOS:
    from tp4.data import prepare_all
    from tp4.report import audit_plot, review_boxes
    prepare_all(ROOT / 'data')
    audit_plot(ROOT / 'data')
    review_boxes(ROOT / 'data')
    ctx = view.context(ROOT, RUN_ID)
    view.dataset_table(ctx)
""", "execution")
md("""<a id="exploracion"></a>
## 7. La distribución permite auditar el problema · PRESENTACIÓN
El gráfico de clases permite detectar desbalance. El histograma usa **área de caja / área de imagen**: describe tamaño relativo, no exactitud del detector.
""")
code("view.figure(ctx, 'data/audit.png', 'Figura 1. Distribución en train. El histograma muestra sólo el intervalo graficado; pueden existir cajas mayores.')")
md("""### Control visual de coordenadas · APRENDIZAJE
Las cajas amarillas deben seguir los objetos visibles. La revisión de tres imágenes complementa la validación automática, sin reemplazarla.
""", "learning")
code("view.figure(ctx, 'data/box_review.png', 'Anotaciones convertidas sobre tres imágenes val.')", "learning")
md("""<a id="protocolo"></a>
## 8. El protocolo distingue prueba técnica y experimento · PRESENTACIÓN
**Smoke:** subconjuntos deterministas y dos épocas para comprobar el flujo. **Full:** train completo y selección con val. Test-dev se evalúa cuando las decisiones estén cerradas.

La configuración siguiente corresponde al resultado seleccionado, no a un entrenamiento pendiente.
""")
code("view.protocol(ctx)")
md("""### Controles y límites del protocolo · APRENDIZAJE
- Conservar splits, semilla, resolución, batch, versiones y argumentos completos por run.
- Usar val para seleccionar y diagnosticar; no reajustar el modelo después de observar test-dev y seguir llamándolo evaluación independiente.
- Quitar etiquetas ignoradas no reproduce necesariamente el tratamiento de esas regiones en el evaluador oficial.
- Una sola semilla no estima variabilidad entre entrenamientos. No se realizó un barrido de arquitecturas ni una comparación con baseline adaptado.
- Extensión opcional: comparar 640/960 manteniendo el protocolo y registrando cambios necesarios de batch.
""", "learning")
md("""<a id="entrenamiento"></a>
## 9. Entrenamiento visible y explícito · EJECUCIÓN
El bloque inicia un run y evalúa `best.pt` sobre val. **`ENTRENAR=False` por defecto**, incluso al ejecutar todo el notebook. Si ya hay un entrenamiento en curso, cargar sus artefactos al terminar.

Consultar README para reanudar desde `last.pt`. Ante falta de memoria, reducir batch explícitamente; el entrenamiento en CPU se bloquea. Windows usa workers 0.
""", "execution")
code("""ENTRENAR = False
PERFIL = 'smoke'
if ENTRENAR:
    import time
    import ultralytics.utils as ultralytics_utils
    from ultralytics import YOLO
    from tp4.experiment import resolve, device_or_raise, start_run, finish_run, metrics_dict
    settings = resolve(ROOT, PERFIL)
    device = device_or_raise(settings['device'])
    ultralytics_utils.WEIGHTS_DIR = ROOT / 'weights'
    ultralytics_utils.WEIGHTS_DIR.mkdir(exist_ok=True)
    run = start_run(ROOT, PERFIL, settings)
    began = time.perf_counter()
    try:
        model = YOLO(str(ROOT / settings['model']))
        model.train(
            data=settings['data_yaml'], epochs=settings['epochs'],
            imgsz=settings['imgsz'], batch=settings['batch'],
            workers=settings['workers'], seed=settings['seed'], device=device,
            project=str(run), name='train', exist_ok=True, plots=True,
        )
        best = run / 'train' / 'weights' / 'best.pt'
        validation = YOLO(str(best)).val(
            data=settings['data_yaml'], split='val', imgsz=settings['imgsz'],
            batch=settings['batch'], workers=settings['workers'], device=device,
            project=str(run), name='validation', exist_ok=True, plots=True,
        )
        finish_run(run, elapsed=time.perf_counter()-began, metrics=metrics_dict(validation))
    except Exception as exc:
        finish_run(run, elapsed=time.perf_counter()-began, error=exc)
        raise
    RUN_ID = str(run.relative_to(ROOT))
    ctx = view.context(ROOT, RUN_ID)
""", "execution")
md("""<a id="evaluacion"></a>
## 10. Las métricas necesitan el contexto del experimento · PRESENTACIÓN
Se muestran porcentajes con cuatro decimales para conservar valores pequeños. Un mAP bajo tras dos épocas no acredita calidad final. El perfil y la ejecución identifican la validación utilizada.
""")
code("view.metrics(ctx)")
md("""### El desglose por clase orienta el diagnóstico · PRESENTACIÓN
Las diferencias se leen junto con cantidades y ejemplos. Un valor cero no significa que esa clase esté ausente del dataset.
""")
code("view.metrics(ctx, per_class=True)")
md("""### Curvas y matriz como respaldo · APRENDIZAJE
Las pérdidas ayudan a revisar estabilidad del ajuste; las métricas val muestran evolución. Dos épocas no establecen convergencia. Leer etiquetas de ejes y umbrales al interpretar la matriz de confusión.
""", "learning")
code("view.figure(ctx, 'train/results.png', 'Curvas de la ejecución seleccionada.', run=True)", "learning")
code("view.figure(ctx, 'validation/confusion_matrix.png', 'Matriz del evaluador Ultralytics sobre val.', run=True)", "learning")
md("""<a id="errores"></a>
## 11. Los ejemplos ponen límites a las cifras · PRESENTACIÓN
La muestra usa confianza 0,25 y asociación por clase e IoU 0,5. Sus conteos y el mAP responden preguntas diferentes: AP considera un barrido de confianza.
""")
code("view.errors(ctx)")
code("view.figure(ctx, 'error_gallery.jpg', 'Figura 2. Dos ejemplos de la muestra val: rojo = FN; cian = FP. No mide desempeño por tamaño ni por oclusión.', run=True, first_row=True)")
md("""### Anotaciones frente a predicciones · APRENDIZAJE
Comparar las mismas imágenes permite ubicar omisiones y cajas espurias. Tamaño pequeño y oclusión motivan hipótesis; atribuirles un efecto requiere evaluar grupos definidos en todo el conjunto.
""", "learning")
code("view.figure(ctx, 'validation/val_batch0_labels.jpg', 'Anotaciones del primer lote val.', run=True)", "learning")
code("view.figure(ctx, 'validation/val_batch0_pred.jpg', 'Predicciones del mismo lote.', run=True)", "learning")
md("""### La latencia describe esta máquina y esta condición · PRESENTACIÓN
Se mide `predict` completo con calentamiento y sincronización CUDA. Es un coste local orientativo, no una demostración de rendimiento en hardware embarcado.
""")
code("view.latency(ctx)")
md("""<a id="conclusiones"></a>
## 12. Conclusión sustentada en los artefactos · PRESENTACIÓN
""")
code("view.conclusion(ctx)")
md("""<a id="referencias"></a>
## 13. Referencias y trazabilidad · PRESENTACIÓN
1. Zhu et al. *Detection and Tracking Meet Drones Challenge*. IEEE TPAMI, 44(11), 7380–7399, 2022. [Dataset y cita](https://github.com/VisDrone/VisDrone-Dataset).
2. Ultralytics. [VisDrone: formato, clases y particiones](https://docs.ultralytics.com/datasets/detect/visdrone/).
3. Ultralytics. [YOLO11](https://docs.ultralytics.com/models/yolo11/) y [entrenamiento](https://docs.ultralytics.com/modes/train/).
4. PyTorch. [Instalación](https://pytorch.org/get-started/locally/).

**Reproducción:** README, `config.yaml`, `data/audit.json`, `run.json` y argumentos del entrenamiento. Fuentes consultadas el 24 de septiembre de 2026.
""")
md("""### Reproducción y derechos · APRENDIZAJE
`python -m tp4.cli prepare` prepara datos; `train smoke` verifica el flujo; `train full` inicia el experimento largo. `analyze RUTA_RUN` genera galería y latencia; `test RUTA_RUN` evalúa test-dev. No ejecutar estas operaciones durante la exposición. `python -m tp4.cli present` exporta las celdas PRESENTACIÓN con figuras embebidas, sin entrenar.

El sitio oficial describe [uso académico y derechos](https://aiskyeye.com/data-protection/) para VisDrone2021; su [página de descarga](https://aiskyeye.com/download/) identifica el conjunto de detección como el mismo de 2019. El repositorio 2019 no tiene una licencia específica. La licencia del código Ultralytics (AGPL-3.0) es independiente.

Criterios editoriales: skill `jupyter-notebook` y [MIT Communication Lab](https://mitcommlab.mit.edu/nse/commkit/structuring-a-slide-presentation/): mensaje, evidencia y alcance. Integrantes permanece editable porque no se proporcionaron los nombres.
""", "learning")

for i, cell in enumerate(cells):
    cell.id = hashlib.sha256(f"{i}:{cell.source}".encode()).hexdigest()[:12]
notebook = nbf.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"display_name": "TP4 VisDrone YOLO", "language": "python", "name": "tp4-visdrone-yolo"},
    "language_info": {"name": "python"}})
target = ROOT / "notebooks" / "01_visdrone_yolo.ipynb"
target.parent.mkdir(exist_ok=True)
nbf.write(notebook, target)
print(target)
