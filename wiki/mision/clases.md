---
type: Taxonomía
title: Clases de la misión
description: Las 10 clases de VisDrone se agrupan en persona y vehículo, según lo que la misión necesita distinguir.
resource: ../../tp4/data.py
tags: [mision, clases, taxonomia]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-28T02:00:00Z }
sources:
  - id: codigo
    resource: ../../tp4/data.py
    title: MISSION_GROUPS en tp4/data.py
  - id: video
    resource: ../../runs/full/20260925T231501Z/mission_eval/video_val.json
    title: Evaluación en video con ambos agrupamientos
---

La misión no necesita distinguir a un peatón de una persona sentada, ni un auto de una moto: necesita saber dónde hay personas y dónde hay vehículos. El equipo definió dos clases[^codigo], que son las mismas en todo el TP: entrenamiento, evaluación en la laptop y benchmark en las placas.

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

El agrupamiento se aplica **al preparar los datos**: cada etiqueta de VisDrone se convierte a su clase de la misión, y el modelo se entrena directamente con persona y vehículo. El modelo de línea base es anterior a esta decisión: se entrenó con las 10 clases y se evaluó agrupando sus predicciones después de la inferencia (ver la [evaluación por clases de la misión](../experimentos/evaluacion-mision.md)). Los resultados del modelo entrenado con las dos clases están en el [reentrenamiento a 1280 px](../experimentos/reentrenamiento-1280.md).

[^codigo]: `MISSION_GROUPS` en `tp4/data.py`, que usa la conversión de etiquetas.
[^video]: Evaluación en video a 5 FPS y confianza 0,25, secuencias limpias.
