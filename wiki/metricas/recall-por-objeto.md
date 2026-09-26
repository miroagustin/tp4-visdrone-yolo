---
type: Métrica
title: Detección por objeto durante la pasada
description: Fracción de objetos únicos de un video detectados con la clase correcta en al menos un cuadro evaluado.
tags: [metricas, video, recall-por-objeto]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
---

**Definición.** Para cada clase de la misión, es la fracción de objetos únicos (identificados por su `target_id` en [VisDrone-VID](../datos/visdrone-vid.md)) que en al menos uno de los cuadros evaluados tiene una detección de la clase correcta con IoU de al menos 0,5.

**Cálculo.** En cada cuadro se emparejan detecciones y anotaciones igual que en la evaluación por cuadro. El `target_id` de cada anotación emparejada marca a ese objeto como detectado. No hace falta un tracker para medir; el tracker hace falta recién en vuelo, para confirmar y contar objetos.

**Indicadores que la acompañan**, según el [objetivo de detección por pasada](../mision/objetivo-deteccion-pasada.md):

| Indicador | Para qué |
|---|---|
| Detección por objeto (al menos 1 cuadro) | Métrica principal frente al 85 % |
| Detección por objeto (al menos 3 cuadros) | Lo que necesita un tracker para confirmar un objeto |
| Falsas alarmas por cuadro y por minuto | Evita que un umbral bajo infle el resultado |
| Recall y precisión por cuadro | Comparación directa con la evaluación en imágenes fijas |
| Tiempo hasta la primera detección | Cuánto tarda el sistema en reportar un objeto nuevo |
| Desglose por tamaño máximo | Qué objetos quedan fuera del alcance de la resolución |

Tabla: Indicadores de la evaluación en video.

Cada indicador se calcula submuestreando el video a los FPS simulados de cada placa (por ejemplo, 30, 10, 5 y 2 FPS), usando los resultados del [benchmark en placas](../obc/benchmark.md).

Estado: **implementada** en `tp4/video.py` (`python -m tp4.cli video runs/full/ID`), con el emparejamiento y el agrupamiento de `tp4/mission.py`. Las detecciones que caen dentro de regiones ignoradas no cuentan como falsas alarmas. Resultados en la [evaluación en video](../experimentos/evaluacion-video.md).
