---
type: Protocolo
title: Protocolo de entrenamiento
description: Parámetros comunes con los que se ajustaron YOLO11n y YOLO26n sobre VisDrone.
resource: ../../config.yaml
tags: [entrenamiento, protocolo, reproducibilidad]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: config
    resource: ../../config.yaml
    title: Configuración del proyecto
  - id: estado
    resource: ../../ESTADO.md
    title: Estado verificado del entorno
---

En ambos modelos se reemplazó la cabeza de 80 clases de COCO por una de 10 clases y se ajustó la red completa (*transfer learning*). COCO aporta solo los pesos iniciales: sus clases no se comparan con las de VisDrone.

| Parámetro | Valor |
|---|---|
| Épocas / resolución / lote | 50 / 640 × 640 / 4 |
| Semilla / *workers* | 42 / 0 |
| Selección de pesos | `best.pt` según validación |
| Hardware | NVIDIA GeForce RTX 5070 Laptop (8 GB), Windows 11 |
| Software | Python 3.14.4, PyTorch 2.13.0+cu130, Ultralytics 8.4.162 |
| Ejecuciones | YOLO11n: `20260925T015117Z`; YOLO26n: `20260925T231501Z` |

Tabla: Protocolo común a ambos modelos, con los mismos particionados y versiones de software[^config].

Además se midieron:

- **Latencia**: `predict` completo en la RTX 5070, 640 px, lote 1, con 5 calentamientos y 20 repeticiones sobre una misma imagen.
- **Auditoría visual de errores**: las 8 primeras imágenes de validación (871 objetos anotados), con confianza 0,25 e IoU 0,5, clasificando cada caja como verdadero positivo (TP), falso positivo (FP) o falso negativo (FN).

[^config]: `config.yaml` y `run.json` de cada ejecución; entorno detallado en `ESTADO.md`.
