# TP4 · YOLO en VisDrone2019-DET

Proyecto académico para detectar diez tipos de personas y vehículos en imágenes aéreas. El [notebook](notebooks/01_visdrone_yolo.ipynb) explica el proceso completo. `presentacion.html` es un recorrido autónomo de 8–10 minutos con artefactos guardados. **Un resultado smoke sólo verifica el pipeline; no demuestra calidad final.**

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

El perfil full usa 50 épocas, resolución 640, batch 4, seed 42 y workers 0. Ajustá parámetros en `config.yaml` o usá `--batch 2`/`--imgsz 960` para una variante explícita; cada ejecución guarda su configuración resuelta en `run.json`. Si CUDA informa memoria insuficiente, bajá batch, iniciá un nuevo run y registrá el cambio. El entrenamiento se bloquea si PyTorch no detecta GPU. Para reanudar, usá `train full --resume runs/full/ID/train/weights/last.pt`; el código comprueba el archivo. `best.pt` se evalúa en val automáticamente. Reservá test-dev para el final:

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

Las métricas de Ultralytics son Precision, Recall, mAP@0.5 y mAP@0.5:0.95, con desglose por clase. **No son métricas del evaluador oficial VisDrone.** Las regiones con score 0 se excluyen de las etiquetas, pero el evaluador oficial puede tratarlas de otro modo. `pedestrian` significa persona de pie o caminando; `people` incluye otras posturas. Las categorías originales 1–10 se convierten a índices YOLO 0–9; las demás se excluyen. No se comparan las etiquetas COCO preentrenadas como si fueran las mismas clases.

## Notebook y presentación

`notebooks/01_visdrone_yolo.ipynb` es la única fuente del informe académico: introducción, objetivos, datos, método, resultados, discusión y referencias. Se edita directamente en Jupyter, VS Code o Colab y se guarda en Git. Se ejecuta de arriba abajo para leer artefactos. La función que ilustra entrenamiento y evaluación no se invoca al ejecutarlo.

El informe selecciona sólo ejecuciones **full terminadas**, sin recurrir a métricas smoke. Si falta una métrica, figura o conclusión, conserva un espacio vacío. `RUN_ID` fija un full terminado; con `None` selecciona el último. La configuración de un full registrado puede describir el método mientras se entrena, pero sus métricas parciales no se incorporan al informe. Las antiguas variables `TP4_TRAIN`, `TP4_PREPARE` y `TP4_LATENCY` no activan cómputo en el notebook.

Después de finalizar full, ejecutar `python -m tp4.cli analyze RUTA_RUN` para producir galería y latencia, y luego todas las celdas del notebook con el kernel **TP4 VisDrone YOLO** para guardar la versión de entrega. La evaluación de test-dev se realiza por separado con `python -m tp4.cli test RUTA_RUN`.

`python -m tp4.cli present` lee el notebook guardado, ejecuta sólo las celdas con metadatos `presentation` en un kernel limpio y exporta sus salidas con figuras embebidas; `present --run RUTA_RUN` fija la ejecución. El HTML abre sin datos ni conexión. El exportador no modifica el notebook. Para generar el HTML se necesitan los módulos del proyecto y los artefactos que se quieran mostrar.

El flujo de edición es **notebook → presentación HTML**. No hay un script que regenere o sobrescriba las celdas. Editá textos, código y orden directamente en el `.ipynb`; guardalo antes de exportar. `tp4/notebook_view.py` reúne las funciones que muestran tablas y figuras, y `tp4/notebook_export.py` transforma el recorrido breve en HTML. No dupliques el contenido académico en esos módulos ni edites el HTML generado.

Conservá los metadatos de las celdas: `tags: ["presentation"]` incluye una celda en el HTML; `tags: ["detail"]` la reserva al notebook. Al agregar una celda en Colab, copiá una del mismo tipo y conservá sus metadatos, o asigná la etiqueta desde un editor que permita editar tags. Las celdas sin `presentation` no se exportan. Las celdas de instalación o entrenamiento no deben llevar esa etiqueta, porque el exportador ejecuta las celdas seleccionadas.

Guion orientativo de nueve minutos: problema y objetivos (1:00), datos (1:30), metodología (1:00), resultados (2:00), errores y latencia (2:00), conclusiones (1:00), referencias y cierre (0:30). Las curvas, matriz y lotes completos sirven como respaldo para preguntas.

## Google Colab

Para colaborar en el informe, abrí `notebooks/01_visdrone_yolo.ipynb` desde GitHub en Colab, editá las celdas y guardá la copia en GitHub en la misma ruta, preferentemente en una rama propia. Coordiná cambios por secciones para reducir conflictos. El notebook ya contiene salidas guardadas que pueden leerse sin ejecutar ni descargar el dataset. Las instrucciones de instalación y operación permanecen en este README.

El documento abierto en Colab y el archivo de un clon en `/content` son copias independientes. Para exportar los cambios, guardá primero el notebook en GitHub y actualizá el clon de esa rama, o descargá el `.ipynb` y reemplazá `notebooks/01_visdrone_yolo.ipynb` en el clon. Luego ejecutá `python -m tp4.cli present` desde `tp4-yolo`. También podés generar el HTML localmente después de recibir los commits de tus compañeros. La edición en Colab no requiere entrenamiento; para volver a ejecutar las celdas que leen resultados, deben estar disponibles los módulos y artefactos correspondientes.

Activá GPU si está disponible (no se garantiza cuota gratuita). Una vez que estos archivos estén publicados en el repositorio, en celdas de Colab:

```python
%cd /content
!git clone https://github.com/miroagustin/VISION-ARTIFICIAL.git
%cd /content/VISION-ARTIFICIAL/tp4-yolo
import torch, os
print(torch.__version__, torch.cuda.is_available())
!python -m pip install -r requirements.txt
os.environ['TP4_ROOT'] = '/content/VISION-ARTIFICIAL/tp4-yolo'
!python -m tp4.cli prepare
!python -m tp4.cli train smoke
# Después de revisar smoke y confirmar GPU:
!python -m tp4.cli train full
```

Si el PyTorch preinstalado funciona, no lo reinstales. Si `torch.cuda.is_available()` es falso, la exploración y la presentación funcionan en CPU, pero el comando train se bloquea. Trabajá en el disco local de la sesión. Para conservar checkpoints, montá Drive opcionalmente y copiá `runs/` allí al terminar; `/content` se pierde al cerrar la sesión. Si la cuota de GPU termina, reanudá desde una copia de `last.pt` junto con el directorio del run. En Colab abrí el notebook con `TP4_ROOT` definido como arriba.

## Archivos y reproducibilidad

`config.yaml` fija parámetros y `visdrone.template.yaml` documenta el dataset. `tp4/data.py` prepara y audita; `tp4/experiment.py` guarda runs y métricas; `tp4/report.py` crea figuras; `tp4/notebook_view.py` muestra los artefactos y `tp4/notebook_export.py` genera HTML desde el notebook. `tests/` cubre conversión, errores y reutilización. `data/visdrone.yaml` se genera con rutas absolutas al preparar los datos. Los resultados viven en `runs/{smoke,full}/ID`, separados por fecha UTC. Consultá `ESTADO.md` para ver qué se ejecutó realmente en esta máquina.
