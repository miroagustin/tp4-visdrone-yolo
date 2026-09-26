---
type: Ejecución
title: Ejecución YOLO26n 20260925T231501Z
description: Ajuste completo de YOLO26n, 50 épocas; mAP50–95 de 15,85 % en validación. Su best.pt es el checkpoint del benchmark en placas.
resource: ../../runs/full/20260925T231501Z/run.json
tags: [run, yolo26n, benchmark]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: run
    resource: ../../runs/full/20260925T231501Z/run.json
  - id: mision
    resource: ../../runs/full/20260925T231501Z/mission_eval/val.json
---

- Modelo: [YOLO26n](../modelos/yolo26n.md), con el [protocolo común](protocolo-entrenamiento.md).
- Validación de `best.pt`: Precision 40,41 %, Recall 31,77 %, mAP50 28,45 %, mAP50–95 15,85 %[^run].
- Tiempo total: 4,41 h. Latencia en la RTX 5070: 26,74 ms por imagen.
- Auditoría de 8 imágenes: TP = 251, FP = 151, FN = 620.
- Evaluación por clases de la misión: `mission_eval/val.json` y `val.md`[^mision]. Ver [resultados](evaluacion-mision.md).
- Durante el ajuste se guardó una vista previa por época sobre imágenes de test-dev (`epoch_previews/`). El artefacto `epoch_051` proviene de una llamada adicional al finalizar y no corresponde a una época entrenada.

[^run]: `runs/full/20260925T231501Z/run.json`.
[^mision]: Generado por `python -m tp4.cli mission runs/full/20260925T231501Z`.
