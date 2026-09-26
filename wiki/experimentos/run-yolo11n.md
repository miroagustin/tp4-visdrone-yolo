---
type: Ejecución
title: Ejecución YOLO11n 20260925T015117Z
description: Ajuste completo de YOLO11n, 50 épocas; mAP50–95 de 16,03 % en validación.
resource: ../../runs/full/20260925T015117Z/run.json
tags: [run, yolo11n]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: run
    resource: ../../runs/full/20260925T015117Z/run.json
  - id: analisis
    resource: ../../analysis/comparacion_yolo11_yolo26.md
---

- Modelo: [YOLO11n](../modelos/yolo11n.md), con el [protocolo común](protocolo-entrenamiento.md).
- Validación de `best.pt`: Precision 41,88 %, Recall 31,38 %, mAP50 28,41 %, mAP50–95 16,03 %[^run].
- Tiempo total: 3,27 h. Latencia en la RTX 5070: 26,59 ms por imagen.
- Auditoría de 8 imágenes: TP = 263, FP = 192, FN = 608[^analisis].
- Artefactos: `train/results.csv`, `train/args.yaml`, `latency.json`, `error_sample.json`, `error_gallery.jpg`.

La ejecución `20260925T012307Z` figura como *running* pero solo tiene seis épocas registradas; se excluyó por incompleta.

[^run]: `runs/full/20260925T015117Z/run.json`.
[^analisis]: `analysis/comparacion_yolo11_yolo26.md`.
