---
type: Trazabilidad
title: Trazabilidad de artefactos
description: Ubicación, dentro de tp4-yolo, de la evidencia citada en la wiki y en el informe.
tags: [trazabilidad, artefactos]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
---

| Artefacto | Ubicación en `tp4-yolo/` |
|---|---|
| Ejecución YOLO11n | `runs/full/20260925T015117Z/` (`run.json`, `train/results.csv`, `latency.json`, `error_sample.json`) |
| Ejecución YOLO26n | `runs/full/20260925T231501Z/` (mismos archivos y `epoch_previews/`) |
| Evaluación por misión | `runs/full/20260925T231501Z/mission_eval/` (`val.json`, `val.md`); código en `tp4/mission.py` |
| Evaluación de resolución | `mission_eval/resolution_val.json`; código en `tp4/inference.py` |
| Evaluación en video | `mission_eval/video_val.json` y caché de predicciones en `mission_eval/video_cache/`; código en `tp4/video.py` |
| VisDrone-VID validación | `data/raw/VisDrone2019-VID-val/`; SHA-256 del ZIP en `data/archives/VisDrone2019-VID-val.json` |
| Análisis comparativo | `analysis/comparacion_yolo11_yolo26.md` y figuras |
| Auditoría de datos | `data/audit.json`, `data/box_review.png` |
| Paquete OBC vigente | `benchmark_artifacts/package_20260926T215439979200Z/` (1280 px) |
| Guía operativa OBC | `BENCHMARK_OBC.md` |
| Código del benchmark | `tp4/benchmark.py`, `bench_common.py`, `bench_worker.py`, `bench_report.py` |
| Wiki y generador del informe | `wiki/`, `tp4/wiki.py`, `tp4/wiki_latex.py`, `tp4/templates/informe_unlam.tex` |
| Informe v1 (histórico) | `informe/informe_tp4_obc.pdf` |

Tabla: Ubicación de la evidencia citada. `runs/`, `data/` y `benchmark_artifacts/` no se suben a git por tamaño, salvo los resultados que lee el notebook (JSON, figuras y el video de la demo), que sí se versionan para que funcione en Colab.

La ejecución `20260925T012307Z` figura como *running* pero solo tiene seis épocas registradas; se excluyó por incompleta. El artefacto `epoch_051` de YOLO26n proviene de una llamada adicional al finalizar el entrenamiento y no corresponde a una época entrenada.
