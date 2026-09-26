---
type: Resultado
title: Evaluación por clases de la misión
description: El best.pt de YOLO26n, reagrupado en persona, vehículo y dos ruedas sin reentrenar, alcanza 45,3 % de mAP50; el límite lo imponen los objetos de menos de 8 px.
resource: ../../runs/full/20260925T231501Z/mission_eval/val.json
tags: [resultados, mision, recall, tamano]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: mision
    resource: ../../runs/full/20260925T231501Z/mission_eval/val.json
    title: Evaluación agrupada en validación
  - id: codigo
    resource: ../../tp4/mission.py
    title: Implementación de la evaluación agrupada
  - id: confusion
    resource: ../../runs/full/20260925T231501Z/validation/confusion_matrix_normalized.png
    title: Matriz de confusión normalizada de YOLO26n
---

# Método

El detector conserva sus 10 clases. Se capturan las predicciones del propio validador de Ultralytics (entrada rectangular de 640 px, confianza 0,001, máximo 300 detecciones) y luego se reagrupan predicciones y etiquetas en las [clases de la misión](../mision/clases.md)[^codigo]. La variante de 10 clases, calculada con el mismo código, reproduce exactamente el mAP50 de 28,45 % y el mAP50–95 de 15,85 % registrados en `run.json`, lo que valida el procedimiento. La variante *con fusión* aplica además una supresión por grupo (IoU 0,7), para no contar dos veces un objeto que el modelo marcó a la vez como *car* y como *van*.

Se evaluó solo validación: test-dev queda reservado para la evaluación final.

# Resultados

| Variante | mAP50 | mAP50–95 |
|---|---:|---:|
| 10 clases VisDrone (control) | 28,5 % | 15,9 % |
| Misión, agrupado directo | 44,4 % | 22,9 % |
| Misión, agrupado con fusión | **45,3 %** | **23,1 %** |

Tabla: mAP en validación (548 imágenes) antes y después de agrupar las clases[^mision].

El salto parece grande, pero una tarea con menos clases es más fácil: estas cifras no se comparan con las de 10 clases, sino con futuros modelos evaluados con las mismas tres clases. Lo informativo es el detalle por clase en un punto de operación concreto.

| Clase | Objetos | AP50 | AP50–95 | Precisión | Recall |
|---|---:|---:|---:|---:|---:|
| persona | 13 969 | 34,6 % | 13,0 % | 65,3 % | **27,7 %** |
| vehículo | 18 617 | 71,0 % | 44,8 % | 79,2 % | **63,8 %** |
| dos ruedas | 6173 | 30,2 % | 11,4 % | 60,5 % | **23,5 %** |
| todos | 38 759 | | | 73,8 % | 44,4 % |

Tabla: Clases de la misión (agrupado con fusión). Precisión y recall con confianza 0,25 e IoU 0,5.

Agrupar corrige casi toda la confusión entre clases, que se concentraba en los vehículos: en la matriz de confusión de 10 clases, el 41 % de las *van* se predecía como *car* y el 17 % de los *truck* también[^confusion]. En cambio, la confusión entre *pedestrian* y *people* era pequeña (2–6 %), porque la mayoría de esas personas directamente no se detecta.

# Umbral de confianza

| Confianza | persona P / R | vehículo P / R | dos ruedas P / R | todos P / R |
|---:|---:|---:|---:|---:|
| 0,05 | 25,4 % / 50,1 % | 41,8 % / 77,1 % | 21,7 % / 52,1 % | 32,0 % / 63,4 % |
| 0,10 | 35,4 % / 45,0 % | 54,0 % / 73,8 % | 32,8 % / 43,2 % | 44,2 % / 58,5 % |
| 0,15 | 45,8 % / 38,9 % | 63,8 % / 70,4 % | 43,2 % / 35,4 % | 55,3 % / 53,5 % |
| 0,25 | 65,3 % / 27,7 % | 79,2 % / 63,8 % | 60,5 % / 23,5 % | 73,8 % / 44,4 % |
| 0,40 | 86,5 % / 14,8 % | 93,6 % / 52,4 % | 78,4 % / 8,4 % | 91,6 % / 31,8 % |
| 0,50 | 93,7 % / 8,9 % | 97,5 % / 44,7 % | 85,6 % / 2,9 % | 96,8 % / 25,1 % |

Tabla: Precisión (P) y recall (R) por cuadro según el umbral de confianza, IoU 0,5.

Una precisión del 85 % se consigue subiendo la confianza a 0,4–0,5, a costa de que el recall de personas caiga al 15 % o menos. Un recall por cuadro del 85 % no se alcanza en ninguna clase con ningún umbral: el máximo es 77 % en vehículos y 50 % en personas, con confianza 0,05 y mucho ruido.

# Recall según el tamaño del objeto

| Clase | < 4 px | 4–8 px | 8–16 px | 16–32 px | ≥ 32 px |
|---|---:|---:|---:|---:|---:|
| persona | 0,5 % (1164) | 11,8 % (5312) | 38,2 % (5971) | 61,9 % (1413) | 78,9 % (109) |
| vehículo | 3,0 % (770) | 31,9 % (2620) | 59,3 % (6171) | 77,1 % (6290) | 90,9 % (2766) |
| dos ruedas | 0,7 % (303) | 10,3 % (1829) | 24,4 % (2956) | 50,1 % (1029) | 41,1 % (56) |

Tabla: Recall con confianza 0,25 según el lado equivalente del objeto, raíz de ancho por alto, medido en la entrada de 640 px de la red. Entre paréntesis, la cantidad de objetos anotados.

El **46 % de las personas anotadas mide menos de 8 px** en la entrada de la red, y ahí el modelo prácticamente no detecta nada. El error dominante es no ver el objeto, no confundir la clase: por eso la siguiente palanca es la [resolución de entrada](../mejoras/resolucion-y-mosaicos.md), y no un reentrenamiento solo para agrupar.

# Observación sobre el pipeline de inferencia

Un primer intento que evaluaba con `predict` en lugar del validador dio unos 3 puntos menos de mAP50 (25,6 % frente a 28,5 %) con los mismos pesos. La causa no está aislada. No afecta al benchmark, porque cada placa se compara contra el `.pt` medido con su mismo pipeline, pero implica que las cifras de las placas no se comparan directamente con las de validación.

[^codigo]: `tp4/mission.py`; comando `python -m tp4.cli mission runs/full/20260925T231501Z`.
[^mision]: `mission_eval/val.json` de la ejecución YOLO26n.
[^confusion]: `runs/full/20260925T231501Z/validation/confusion_matrix_normalized.png`, con el umbral por defecto.
