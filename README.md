# TP4 · YOLO en VisDrone2019-DET

Bonus de despliegue: [guía de benchmark OBC para Jetson y Raspberry Pi 5](BENCHMARK_OBC.md). Incluye paquete común, TensorRT/NCNN, medición de memoria/FPS y reporte comparativo autónomo. La [Raspberry Pi 5 ya tiene resultados oficiales](wiki/obc/benchmark.md); Jetson sigue pendiente.

Proyecto académico para detectar personas y vehículos en imágenes aéreas. Todo el TP (entrenamiento, evaluación local y placas) usa las mismas dos clases: **persona** y **vehiculo**. El [notebook](notebooks/01_visdrone_yolo.ipynb) explica el proceso completo. `presentacion.html` es un recorrido autónomo de 8–10 minutos con artefactos guardados. **Un resultado smoke sólo verifica el pipeline; no demuestra calidad final.**

## Instalación local (Windows 11, GPU NVIDIA)

Desde `tp4-yolo`:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/cu130
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m ipykernel install --user --name tp4-visdrone-yolo --display-name "TP4 VisDrone YOLO"
.venv/Scripts/python.exe -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

PyTorch 2.13.0+cu130 y torchvision 0.28.0+cu130 tienen ruedas para Python 3.14/Windows. El driver NVIDIA 610.74 anuncia soporte CUDA 13.3; eso **no** indica un toolkit CUDA 13.3 instalado. Se usa el runtime incluido en las ruedas PyTorch. No se modifica el driver. Consulta la [guía oficial de PyTorch](https://pytorch.org/get-started/locally/) y sus [versiones](https://pytorch.org/get-started/previous-versions/). En Linux, reemplazá `.venv/Scripts/python.exe` por `.venv/bin/python` y comprobá qué índice CUDA corresponde a tu driver. Si faltan ruedas para tu Python, usá un entorno aislado con Python 3.12.

## Datos y ejecución

```powershell
.venv/Scripts/python.exe -m tp4.cli prepare
.venv/Scripts/python.exe -m tp4.cli train smoke
.venv/Scripts/python.exe -m tp4.cli analyze runs/smoke/ID
.venv/Scripts/python.exe -m tp4.cli present
```

La descarga usa los ZIP de [Ultralytics](https://docs.ultralytics.com/datasets/detect/visdrone/) que reflejan los splits de [VisDrone](https://github.com/VisDrone/VisDrone-Dataset): train 6471, val 548 y test-dev 1610 imágenes. Conserva ZIP, imágenes y anotaciones originales en `data/`. El manifiesto incluye SHA-256. `data/audit.json` contiene conteos reales y descartes; `data/box_review.png` permite revisar cajas. Los originales y el formato YOLO quedan excluidos de Git por tamaño. La [página oficial de privacidad y derechos](https://aiskyeye.com/data-protection/) indica uso académico y describe CC BY-NC-SA 3.0 para VisDrone2021; la [página oficial de descarga](https://aiskyeye.com/download/) indica que el conjunto de detección es el mismo que VisDrone2019. Como el repositorio 2019 no contiene una licencia específica, no asumimos derechos de redistribución: consultar a los autores si se quieren publicar imágenes o pesos para otros usos. La licencia del código Ultralytics ([AGPL-3.0](https://github.com/ultralytics/ultralytics/blob/main/LICENSE)) es independiente.

Para el entrenamiento académico completo, después de revisar smoke:

```powershell
.venv/Scripts/python.exe -m tp4.cli train full
```

El perfil full usa 50 épocas, resolución 1280, batch 4, seed 42 y 8 workers (a 1280 px, 8 workers casi duplican la velocidad; smoke sigue con 0). En la RTX 5070 Laptop cada época tarda unos 4,5 min, unas 4 h por modelo, y la GPU reserva hasta ~7,7 GB: cerrá juegos y otras apps que usen la GPU antes de entrenar. Para entrenar YOLO11n y después YOLO26n en una sola tanda (el `;` lanza el segundo aunque falle el primero):

```powershell
.venv/Scripts/python.exe -m tp4.cli train full --no-yolo26; .venv/Scripts/python.exe -m tp4.cli train full --yolo26
```

El run `20260925T231501Z` (YOLO26n, 640 px, 10 clases VisDrone reagrupadas después de la inferencia) queda como línea base. Ajustá parámetros en `config.yaml` o usá `--batch 2`/`--imgsz 960` para una variante explícita; cada ejecución guarda su configuración resuelta en `run.json`. Si CUDA informa memoria insuficiente, bajá batch, iniciá un nuevo run y registrá el cambio. El entrenamiento se bloquea si PyTorch no detecta GPU. Para reanudar, usá `train full --resume runs/full/ID/train/weights/last.pt`; el código comprueba el archivo. `best.pt` se evalúa en val automáticamente. Reservá test-dev para el final:

```powershell
.venv/Scripts/python.exe -m tp4.cli test runs/full/ID
```

### Selección del modelo

`use_yolo26: true` en `config.yaml` selecciona **YOLO26n preentrenado en COCO** para nuevos entrenamientos. Con `false` se usa YOLO11n, también preentrenado en COCO. Se puede sobrescribir esa elección para un run sin editar el archivo:

```powershell
.venv/Scripts/python.exe -m tp4.cli train full --yolo26
.venv/Scripts/python.exe -m tp4.cli train full --no-yolo26
```

Sin flag se utiliza el valor de `config.yaml`. El flag resuelto y el nombre del modelo quedan registrados en `run.json`. Cambiar la configuración no altera un proceso que ya cargó el modelo. Al reanudar con `--resume`, se conserva el checkpoint y la configuración original del run, incluso si era YOLO11 y el nuevo predeterminado es YOLO26. Por eso `--resume` no se combina con flags de modelo, batch o resolución. El informe identifica el modelo de la ejecución evaluada, independientemente del predeterminado actual.

Las métricas de Ultralytics son Precision, Recall, mAP@0.5 y mAP@0.5:0.95, con desglose por clase. **No son métricas del evaluador oficial VisDrone.** Las regiones con score 0 se excluyen de las etiquetas, pero el evaluador oficial puede tratarlas de otro modo. `pedestrian` significa persona de pie o caminando; `people` incluye otras posturas. Al preparar los datos, las categorías originales 1–10 se agrupan en persona (0: *pedestrian*, *people*) y vehiculo (1: el resto) según `MISSION_GROUPS` en `tp4/data.py`; las demás se excluyen. No se comparan las etiquetas COCO preentrenadas como si fueran las mismas clases.

## Notebook y presentación

### Imágenes por época

`epoch_preview: {enabled: true, confidence: 0.25}` activa una predicción al finalizar cada época en los nuevos entrenamientos. Se elige una imagen aleatoria reproducible de **test-dev**, exclusivamente, mediante semilla y número de época. Usa una copia de los pesos EMA en CPU para evitar una segunda inferencia en GPU; agrega tiempo a cada época. Guarda imagen y metadatos en `runs/PROFILE/ID/epoch_previews/`. No lee etiquetas de test ni modifica el modelo entrenado. Los errores de visualización se registran sin interrumpir el entrenamiento.

Si el entrenamiento se llama desde Python en una celda, el callback agrega cada imagen al output automáticamente. Si se ejecuta desde terminal o con `!python`, abrí la sección «Predicciones a lo largo del entrenamiento», asigná `RUN_EVOLUTION = 'runs/full/ID'` y `WATCH_EPOCHS = True`, y ejecutá esa celda para observar las imágenes conforme se guardan. La celda espera hasta que el run termina; puede interrumpirse sin detener el proceso externo. Con `False` carga el historial disponible y termina. Guardá el notebook para conservar sus salidas; volvé a dejar `False` para la entrega. Con `RUN_EVOLUTION = None` se toma el último full que tiene vistas guardadas. La secuencia completa queda en el notebook, fuera del HTML breve.

Un proceso ya iniciado no incorpora callbacks nuevos. Tampoco se pueden reconstruir épocas pasadas sin los pesos correspondientes. Los runs antiguos reanudados conservan su configuración original y no habilitan esta opción si no la tenían registrada. No se ha reiniciado el entrenamiento actual.

Al observar test-dev durante el entrenamiento deja de ser un conjunto completamente reservado. No elijas hiperparámetros ni checkpoints según estas imágenes; la selección sigue usando val. La secuencia cambia de imagen y sirve como ilustración cualitativa, no como comparación controlada entre épocas. El notebook explicita esta limitación.

`notebooks/01_visdrone_yolo.ipynb` es la única fuente del informe académico: introducción, objetivos, datos, método, resultados, discusión y referencias. Se edita directamente en Jupyter, VS Code o Colab y se guarda en Git. Se ejecuta de arriba abajo para leer artefactos. La celda de «Ajuste y selección del modelo» trae `ENTRENAR = False`; con `True` reentrena con el perfil full (elegí el modelo con `USAR_YOLO26`), muestra la predicción de cada época en su salida y las secciones siguientes pasan a esa ejecución. No la actives mientras otro entrenamiento usa la GPU.

El informe selecciona sólo ejecuciones **full terminadas**, sin recurrir a métricas smoke. Si falta una métrica, figura o conclusión, conserva un espacio vacío. `RUN_ID` fija un full terminado; con `None` selecciona el último. La configuración de un full registrado puede describir el método mientras se entrena, pero sus métricas parciales no se incorporan al informe. Las antiguas variables `TP4_TRAIN`, `TP4_PREPARE` y `TP4_LATENCY` no activan cómputo en el notebook.

Después de finalizar full, ejecutar `python -m tp4.cli analyze RUTA_RUN` para producir galería y latencia, y luego todas las celdas del notebook con el kernel **TP4 VisDrone YOLO** para guardar la versión de entrega. La evaluación de test-dev se realiza por separado con `python -m tp4.cli test RUTA_RUN`.

`python -m tp4.cli present` lee el notebook guardado, ejecuta sólo las celdas con metadatos `presentation` en un kernel limpio y exporta sus salidas con figuras embebidas; `present --run RUTA_RUN` fija la ejecución. El HTML abre sin datos ni conexión. El exportador no modifica el notebook. Para generar el HTML se necesitan los módulos del proyecto y los artefactos que se quieran mostrar.

El flujo de edición es **notebook → presentación HTML**. No hay un script que regenere o sobrescriba las celdas. Editá textos, código y orden directamente en el `.ipynb`; guardalo antes de exportar. `tp4/notebook_view.py` reúne las funciones que muestran tablas y figuras, y `tp4/notebook_export.py` transforma el recorrido breve en HTML. No dupliques el contenido académico en esos módulos ni edites el HTML generado.

Conservá los metadatos de las celdas: `tags: ["presentation"]` incluye una celda en el HTML; `tags: ["detail"]` la reserva al notebook. Al agregar una celda en Colab, copiá una del mismo tipo y conservá sus metadatos, o asigná la etiqueta desde un editor que permita editar tags. Las celdas sin `presentation` no se exportan. Las celdas de instalación o entrenamiento no deben llevar esa etiqueta, porque el exportador ejecuta las celdas seleccionadas.

Guion orientativo de nueve minutos: problema y objetivos (1:00), datos (1:30), metodología (1:00), resultados (2:00), errores y latencia (2:00), conclusiones (1:00), referencias y cierre (0:30). Las curvas, matriz y lotes completos sirven como respaldo para preguntas.

## Google Colab

El TP4 vive en su propio repositorio, [miroagustin/tp4-visdrone-yolo](https://github.com/miroagustin/tp4-visdrone-yolo). Para presentarlo, abrir el notebook en Colab: [TP4 en Google Colab](https://colab.research.google.com/github/miroagustin/tp4-visdrone-yolo/blob/main/notebooks/01_visdrone_yolo.ipynb). Colab carga solo el `.ipynb`; al ejecutar la primera celda, el notebook clona el repositorio en `/content/tp4-visdrone-yolo` e importa `tp4`. El repositorio versiona los resultados que leen las celdas de presentación (JSON de métricas, figuras y el video de la demo en `runs/full/20260925T231501Z/`), así que el recorrido completo funciona sin dataset, sin GPU y sin entrenar. Para guardar cambios en GitHub, usar **Archivo → Guardar una copia en GitHub**, elegir repositorio, rama y ruta `notebooks/01_visdrone_yolo.ipynb`. Si no tienen permiso de escritura, guarden en su fork y creen un pull request. Coordinen secciones para reducir conflictos.

El notebook abierto y el clon de `/content` son copias distintas: guardar la copia en GitHub no actualiza ese clon. Para generar `presentacion.html` con las últimas ediciones, integren primero el commit en la rama del proyecto y actualicen el clon local; luego ejecuten `python -m tp4.cli present`. También pueden descargar desde Colab el `.ipynb` y reemplazar el del clon. La edición del texto no requiere ejecutar el notebook. Para ejecutar celdas de resultados se necesitan el código auxiliar y los artefactos de la ejecución; la VM y archivos de Colab no quedan guardados en GitHub.

Activá GPU si está disponible (no se garantiza cuota gratuita). Para entrenar en Colab, en celdas:

```python
%cd /content
!git clone https://github.com/miroagustin/tp4-visdrone-yolo.git
%cd /content/tp4-visdrone-yolo
import torch, os
print(torch.__version__, torch.cuda.is_available())
!python -m pip install -r requirements.txt
os.environ['TP4_ROOT'] = '/content/tp4-visdrone-yolo'
!python -m tp4.cli prepare
!python -m tp4.cli train smoke
# Después de revisar smoke y confirmar GPU:
!python -m tp4.cli train full
```

Si el PyTorch preinstalado funciona, no lo reinstales. Si `torch.cuda.is_available()` es falso, la exploración y la presentación funcionan en CPU, pero el comando train se bloquea. Trabajá en el disco local de la sesión. Para conservar checkpoints, montá Drive opcionalmente y copiá `runs/` allí al terminar; `/content` se pierde al cerrar la sesión. Si la cuota de GPU termina, reanudá desde una copia de `last.pt` junto con el directorio del run. En Colab abrí el notebook con `TP4_ROOT` definido como arriba.

## Archivos y reproducibilidad

`config.yaml` fija parámetros y `visdrone.template.yaml` documenta el dataset. `tp4/data.py` prepara y audita; `tp4/experiment.py` guarda runs y métricas; `tp4/report.py` crea figuras; `tp4/notebook_view.py` muestra los artefactos y `tp4/notebook_export.py` genera HTML desde el notebook. `tests/` cubre conversión, errores y reutilización. `data/visdrone.yaml` se genera con rutas absolutas al preparar los datos. Los resultados viven en `runs/{smoke,full}/ID`, separados por fecha UTC. Consultá `ESTADO.md` para ver qué se ejecutó realmente en esta máquina.

## Wiki y informe

`wiki/` documenta el TP4 como un bundle [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format): planteo de la plataforma de dron, datos, experimentos, clases de la misión, benchmark en placas, mejoras de inferencia, plan y decisiones. Es la única fuente del informe; las convenciones de edición están en [wiki/guia-edicion.md](wiki/guia-edicion.md).

```powershell
.venv/Scripts/python.exe -m tp4.cli wiki check      # conformidad OKF y enlaces
.venv/Scripts/python.exe -m tp4.cli informe         # genera informe/informe_tp4.pdf (requiere pdflatex)
.venv/Scripts/python.exe -m tp4.cli informe --solo-tex
```

`informe/informe_tp4_obc.pdf` es la versión 1, escrita a mano, y se conserva como referencia histórica.

Evaluaciones con las clases de la misión (persona y vehículo). Sirven para los modelos de 2 clases y para la línea base de 10 clases, que se reagrupa después de la inferencia:

```powershell
.venv/Scripts/python.exe -m tp4.cli mission runs/full/ID      # clases agrupadas en DET val
.venv/Scripts/python.exe -m tp4.cli resolution runs/full/ID   # 640/960/1280 px y mosaicos en DET val
.venv/Scripts/python.exe -m tp4.cli video runs/full/ID        # detección por pasada en VisDrone-VID val
```

`video` necesita `VisDrone2019-VID-val.zip` (descarga manual desde la página de VisDrone) extraído en `data/raw/`. Guarda un caché de predicciones en `mission_eval/video_cache/`, así que volver a evaluar no repite la inferencia.
