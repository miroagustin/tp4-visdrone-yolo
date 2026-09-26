---
type: Log
title: Historial del TP4
---

# Historial

## 2026-09-26

- **Evaluación** de resolución sin reentrenar en DET val (`python -m tp4.cli resolution`): 1280 px es el mejor compromiso y los mosaicos dan el mayor recall. Ver [resultados](experimentos/evaluacion-resolucion.md).
- **Evaluación** de detección por pasada en VisDrone-VID val (`python -m tp4.cli video`): con secuencias limpias, 84 % de personas detectadas a 5 FPS con 1280 px y 87 % con mosaicos. Ver [resultados](experimentos/evaluacion-video.md).
- **Hallazgo**: cuatro de las siete secuencias de VID comparten video de origen con el entrenamiento de DET. Los resultados en video se informan con las tres secuencias limpias. Ver [VisDrone-VID](datos/visdrone-vid.md).
- **Descarga** de VisDrone-VID val completada y extraída en `data/raw/`; se asumen 30 FPS nominales.

- **Creación** de la wiki como bundle Open Knowledge Format v0.2, generada por `claude-code/claude-opus-5-5` a partir del informe v1, `BENCHMARK_OBC.md`, `analysis/`, `ESTADO.md` y la evaluación por misión. Pasa a ser la única fuente del informe: `python -m tp4.cli informe` genera `informe/informe_tp4.pdf` (versión 2). Ningún concepto tiene `verified` todavía: falta la revisión del equipo.
- **Decisión**: la misión usa tres clases (persona, vehículo, dos ruedas) y el objetivo es detectar al menos una vez durante la pasada el 85 % de los objetos. Ver [decisiones](plan/decisiones.md).
- **Evaluación** agrupada por misión del `best.pt` de YOLO26n sin reentrenar (`python -m tp4.cli mission`). Ver [resultados](experimentos/evaluacion-mision.md).
- **Informe v1** en PDF (`informe/informe_tp4_obc.pdf`), escrito a mano en LaTeX. Se conserva como versión histórica; su fuente `.tex` se reemplazó por esta wiki.
- **Paquete de benchmark OBC** `package_20260926T172031125947Z` generado y verificado en la laptop. Ver [benchmark](obc/benchmark.md).

## 2026-09-25

- **Entrenamiento** completo de YOLO11n (`20260925T015117Z`) y YOLO26n (`20260925T231501Z`), 50 épocas cada uno. Ver [comparación](experimentos/comparacion-yolo11-yolo26.md).

## 2026-09-24

- **Preparación** y auditoría de VisDrone2019-DET; ejecuciones smoke del pipeline. Ver [VisDrone-DET](datos/visdrone-det.md).
