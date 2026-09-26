---
type: Modelo
title: YOLO11n
description: Detector de una etapa de Ultralytics, variante nano, preentrenado en COCO y ajustado a VisDrone.
resource: https://github.com/ultralytics/ultralytics
tags: [yolo, modelo, nano]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: yolo
    resource: /referencias/bibliografia.md
    title: YOLO (Redmon et al., 2016)
  - id: yolo11
    resource: https://github.com/ultralytics/ultralytics
    title: Ultralytics YOLO11
---

Generación consolidada de Ultralytics[^yolo11] dentro de la familia de detectores de una etapa YOLO[^yolo]. Su posprocesamiento requiere supresión de no máximos (NMS). Se usó la variante más pequeña (*nano*), preentrenada en COCO. En la comparación resultó descriptivamente más favorable en mAP50–95 y en costo de entrenamiento, con una diferencia que no alcanza significancia (ver [comparación](../experimentos/comparacion-yolo11-yolo26.md)).

[^yolo]: J. Redmon *et al.*, You Only Look Once, CVPR 2016.
[^yolo11]: G. Jocher y J. Qiu, Ultralytics YOLO11, 2024.
