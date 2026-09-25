# TP4 · YOLO11n en VisDrone2019-DET

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

Las métricas de Ultralytics son Precision, Recall, mAP@0.5 y mAP@0.5:0.95, con desglose por clase. **No son métricas del evaluador oficial VisDrone.** Las regiones con score 0 se excluyen de las etiquetas, pero el evaluador oficial puede tratarlas de otro modo. `pedestrian` significa persona de pie o caminando; `people` incluye otras posturas. Las categorías originales 1–10 se convierten a índices YOLO 0–9; las demás se excluyen. No se comparan las etiquetas COCO preentrenadas como si fueran las mismas clases.

## Notebook y presentación

Abrí `notebooks/01_visdrone_yolo.ipynb` con el kernel **TP4 VisDrone YOLO**. Por defecto corre de arriba abajo en perfil presentación y muestra artefactos existentes sin descargar ni entrenar. Variables opcionales antes de abrir Jupyter: `TP4_PREPARE=1` descarga/prepara; `TP4_PROFILE=smoke` y `TP4_TRAIN=1` entrenan el smoke; `TP4_PROFILE=full` y `TP4_TRAIN=1` ejecutan el entrenamiento largo. `TP4_LATENCY=1` mide latencia (5 warm-up y 20 inferencias, batch 1). Ejecutá `python -m tp4.cli present` después de cada run para actualizar el HTML; abre `presentacion.html` en cualquier navegador incluso sin datos ni conexión.

## Google Colab

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

`config.yaml` fija parámetros y `visdrone.template.yaml` documenta el dataset. `tp4/data.py` prepara y audita; `tp4/experiment.py` guarda runs y métricas; `tp4/report.py` crea figuras y HTML. `scripts/build_notebook.py` regenera el notebook. `tests/` cubre conversión, errores y reutilización. `data/visdrone.yaml` se genera con rutas absolutas al preparar los datos. Los resultados viven en `runs/{smoke,full}/ID`, separados por fecha UTC. Consultá `ESTADO.md` para ver qué se ejecutó realmente en esta máquina.
