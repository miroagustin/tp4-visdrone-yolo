---
type: Protocolo
title: Protocolo de entrenamiento
description: Parámetros con los que se ajustaron YOLO11n y YOLO26n sobre VisDrone, en la línea base (10 clases, 640 px) y en el reentrenamiento (persona y vehículo, 1280 px).
resource: ../../config.yaml
tags: [entrenamiento, protocolo, reproducibilidad]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-28T02:00:00Z }
sources:
  - id: config
    resource: ../../config.yaml
    title: Configuración del proyecto
  - id: estado
    resource: ../../ESTADO.md
    title: Estado verificado del entorno
---

En ambos modelos se reemplazó la cabeza de 80 clases de COCO por una propia y se ajustó la red completa (*transfer learning*). COCO aporta solo los pesos iniciales: sus clases no se comparan con las de VisDrone. Hubo dos etapas: la **línea base**, con las 10 clases de VisDrone a 640 px, y el **reentrenamiento**, con las [clases de la misión](../mision/clases.md) a 1280 px.

| Parámetro | Línea base | Reentrenamiento |
|---|---|---|
| Clases | 10 de VisDrone | persona y vehículo |
| Épocas / resolución / lote | 50 / 640 × 640 / 4 | 50 / 1280 × 1280 / 4 |
| Semilla / *workers* | 42 / 0 | 42 / 8 |
| Selección de pesos | `best.pt` según validación | `best.pt` según validación |
| Ejecución YOLO11n | `20260925T015117Z` (3,27 h) | `20260927T215941Z` (2,51 h) |
| Ejecución YOLO26n | `20260925T231501Z` (4,41 h) | `20260928T003017Z` (2,93 h) |

Tabla: Protocolo de cada etapa, con los mismos particionados, hardware (NVIDIA GeForce RTX 5070 Laptop de 8 GB, Windows 11) y software (Python 3.14.4, PyTorch 2.13.0+cu130, Ultralytics 8.4.162)[^config].

El reentrenamiento tardó menos pese a procesar cuatro veces más píxeles. La causa probable es la carga de imágenes en CPU: en una prueba corta a 1280 px, pasar de 0 a 8 *workers* casi duplicó la velocidad (de 3,6 a 6,5 iteraciones por segundo).

Además se midieron:

- **Latencia**: `predict` completo en la RTX 5070, a la resolución de cada etapa, lote 1, con 5 calentamientos y 20 repeticiones sobre una misma imagen.
- **Auditoría visual de errores**: las 8 primeras imágenes de validación (871 objetos anotados), con confianza 0,25 e IoU 0,5, clasificando cada caja como verdadero positivo (TP), falso positivo (FP) o falso negativo (FN).

[^config]: `config.yaml` y `run.json` de cada ejecución; entorno detallado en `ESTADO.md`.
