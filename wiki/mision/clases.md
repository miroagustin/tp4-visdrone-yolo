---
type: Taxonomía
title: Clases de la misión
description: Las 10 clases de VisDrone se agrupan en persona, vehículo y dos ruedas, según lo que la misión necesita distinguir.
resource: ../../tp4/mission.py
tags: [mision, clases, taxonomia]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: codigo
    resource: ../../tp4/mission.py
    title: MISSION_GROUPS en tp4/mission.py
---

La misión no necesita distinguir a un peatón de una persona sentada, ni un auto de una camioneta: necesita saber dónde hay personas, vehículos y vehículos de dos ruedas. El equipo definió tres clases[^codigo]:

| Clase de la misión | Clases VisDrone que agrupa |
|---|---|
| persona | *pedestrian*, *people* |
| vehículo | *car*, *van*, *truck*, *bus*, *tricycle*, *awning-tricycle* |
| dos ruedas | *bicycle*, *motor* |

Tabla: Agrupamiento de clases definido para la misión.

Criterios de la decisión:

- **Agrupar, no borrar.** Si se quitaran las etiquetas de *van* o *truck* pero esos objetos siguieran en las imágenes, el modelo aprendería a tratarlos como fondo, y eso choca con aprender "vehículo".
- **No usar las clases de COCO.** COCO solo aporta los pesos iniciales. Usar directamente las clases de COCO sin reentrenar daría peor resultado, porque son fotos tomadas desde el suelo.
- **Sin efecto en velocidad.** Pasar de 10 a 3 clases solo cambia la última capa de clasificación; los FPS en la placa serían prácticamente iguales. La ganancia es de precisión y de claridad para la misión.

El agrupamiento se aplica hoy **después de la inferencia**, sobre el modelo de 10 clases. Ver la [evaluación por clases de la misión](../experimentos/evaluacion-mision.md).

[^codigo]: `MISSION_GROUPS` en `tp4/mission.py`.
