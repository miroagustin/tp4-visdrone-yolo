---
type: Taxonomía
title: Clases de la misión
description: Las 10 clases de VisDrone se agrupan en persona y vehículo, según lo que la misión necesita distinguir.
resource: ../../tp4/mission.py
tags: [mision, clases, taxonomia]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T23:00:00Z }
sources:
  - id: codigo
    resource: ../../tp4/mission.py
    title: MISSION_GROUPS en tp4/mission.py
  - id: video
    resource: ../../runs/full/20260925T231501Z/mission_eval/video_val.json
    title: Evaluación en video con ambos agrupamientos
---

La misión no necesita distinguir a un peatón de una persona sentada, ni un auto de una moto: necesita saber dónde hay personas y dónde hay vehículos. El equipo definió dos clases[^codigo]:

| Clase de la misión | Clases VisDrone que agrupa |
|---|---|
| persona | *pedestrian*, *people* |
| vehículo | *car*, *van*, *truck*, *bus*, *tricycle*, *awning-tricycle*, *bicycle*, *motor* |

Tabla: Agrupamiento de clases definido para la misión.

Criterios de la decisión:

- **Dos clases, no tres.** Se probó primero separar *dos ruedas* (bicicleta y moto). VisDrone anota a quien conduce una bicicleta o una moto como *people*, así que esa persona ya cuenta como persona. Además, en las secuencias de video limpias hay solo 10 bicicletas y motos. Sumarlas a vehículo no cambia los resultados de persona y sube la detección por pasada de vehículos a 1280 px de 61 % a 64 %[^video].
- **Agrupar, no borrar.** Si se quitaran las etiquetas de *van* o *truck* pero esos objetos siguieran en las imágenes, el modelo aprendería a tratarlos como fondo, y eso choca con aprender "vehículo".
- **No usar las clases de COCO.** COCO solo aporta los pesos iniciales. Usar directamente las clases de COCO sin reentrenar daría peor resultado, porque son fotos tomadas desde el suelo.
- **Sin efecto en velocidad.** Pasar de 10 a 2 clases solo cambia la última capa de clasificación; los FPS en la placa serían prácticamente iguales. La ganancia es de precisión y de claridad para la misión.
- **El objetivo se fija sobre personas.** Vehículo se informa, pero no se exige (ver el [objetivo por pasada](objetivo-deteccion-pasada.md)).

El agrupamiento se aplica hoy **después de la inferencia**, sobre el modelo de 10 clases. Ver la [evaluación por clases de la misión](../experimentos/evaluacion-mision.md).

[^codigo]: `MISSION_GROUPS` en `tp4/mission.py`.
[^video]: Evaluación en video a 5 FPS y confianza 0,25, secuencias limpias.
