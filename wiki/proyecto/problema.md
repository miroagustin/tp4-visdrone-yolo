---
type: Problema
title: Planteo del problema
description: Detectar personas y vehículos en imágenes aéreas es más difícil que desde el suelo y además debe hacerse en tiempo real en hardware embebido.
tags: [problema, objetos-pequenos, visdrone]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: coco
    resource: /referencias/bibliografia.md
    title: Microsoft COCO
  - id: audit
    resource: ../../data/audit.json
    title: Auditoría de VisDrone2019-DET
---

La detección en imágenes aéreas es sensiblemente más difícil que en los conjuntos de referencia tomados desde el suelo, como COCO[^coco]:

- **Objetos muy pequeños.** Vistos desde decenas de metros, una persona o una bicicleta ocupan pocos píxeles. Al reducir la imagen al tamaño de entrada de la red pueden quedar por debajo del límite que el modelo logra resolver.
- **Alta densidad.** VisDrone promedia unos 53 objetos anotados por imagen en entrenamiento y 71 en validación[^audit]. Las escenas urbanas contienen cientos de instancias parcialmente ocluidas.
- **Clases visualmente próximas.** *Pedestrian* frente a *people*, *tricycle* frente a *awning-tricycle* y *car* frente a *van* se diferencian por detalles que se pierden al reducir la resolución.
- **Variabilidad de punto de vista.** Hay tomas cenitales y oblicuas, con distintas alturas, iluminaciones y escenarios.

A esas dificultades se agrega la restricción de cómputo: el detector debe funcionar en tiempo real en la computadora de a bordo. Por lo tanto, la pregunta del proyecto no se reduce a *qué modelo es más preciso*. Interesa *qué combinación de modelo, motor de inferencia y placa ofrece el mejor compromiso entre precisión, velocidad, memoria y comportamiento térmico dentro de las restricciones de un dron*, medido con una métrica que tenga sentido para la misión: [detectar a cada objeto al menos una vez durante la pasada](../mision/objetivo-deteccion-pasada.md).

[^coco]: T.-Y. Lin *et al.*, Microsoft COCO, ECCV 2014.
[^audit]: Conteos de `data/audit.json`: 343 204 cajas en 6471 imágenes de entrenamiento y 38 759 en 548 de validación.
