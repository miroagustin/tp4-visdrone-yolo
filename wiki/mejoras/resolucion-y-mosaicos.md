---
type: Hipótesis
title: Resolución de entrada y mosaicos
description: Aumentar la resolución efectiva recupera personas pequeñas; medido sin reentrenar, 1280 px es el mejor compromiso y los mosaicos dan el mayor recall. Falta medir el costo en las placas.
tags: [mejoras, resolucion, sahi, objetos-pequenos]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T21:00:00Z }
sources:
  - id: sahi
    resource: /referencias/bibliografia.md
    title: SAHI
  - id: mision
    resource: ../../runs/full/20260925T231501Z/mission_eval/val.json
  - id: resolucion
    resource: ../../runs/full/20260925T231501Z/mission_eval/resolution_val.json
---

# Hipótesis

La inferencia inicial procesa la imagen completa reducida a 640 px de lado. Las imágenes de DET miden entre 1360 y 1920 px de ancho, y los videos de VID llegan a 3840 px, así que se reducen entre 2 y 6 veces. En DET, el 46 % de las personas queda por debajo de 8 px[^mision]. Si el recall depende sobre todo del tamaño aparente, aumentar la resolución efectiva debería recuperar gran parte de esas personas.

# Alternativas

| Alternativa | Qué hace | Costo por imagen |
|---|---|---|
| Entrada de 960 o 1280 px | Reduce menos la imagen: los objetos quedan 1,5 o 2 veces más grandes | Unas 2,25 o 4 veces más píxeles para la red |
| Mosaicos (SAHI) | Corta la imagen nativa en mosaicos solapados de 640 px y une las detecciones[^sahi] | Una inferencia por mosaico: unas 6 en DET y hasta 33 en video 4K |
| Mosaicos reducidos | Reduce la imagen a 1920 px de lado mayor antes de cortarla | Hasta 9 inferencias por cuadro, también en 4K |
| Mosaicos + 1280 px | Mosaicos nativos con la pasada completa a 1280 px | Como los mosaicos nativos |
| Volar más bajo | Agranda los objetos sin cambiar el software | Cubre menos terreno por pasada |

Tabla: Palancas para recuperar objetos pequeños.

# Resultado sin reentrenar

La [evaluación de resolución](../experimentos/evaluacion-resolucion.md) confirma la hipótesis en DET[^resolucion]:

- Con **1280 px**, el recall de personas por cuadro pasa de 27 % a 43 % y el mAP50 de la misión, de 44,6 % a 56,9 %, con una sola inferencia.
- Con **mosaicos**, el recall de personas llega a 45 % y el de todos los objetos a 61 %, pero con menos precisión y varias inferencias por imagen.
- La estimación previa de alrededor de 50 % de recall de personas por cuadro fue optimista.
- Combinando mosaicos con más resolución, en DET el recall de personas por cuadro llega a 48 % (mosaicos nativos + 1280 px).

En video, frente al objetivo del 85 % por pasada a 5 FPS, las personas llegan a 84 % con 1280 px, 88 % con mosaicos sobre la imagen reducida a 1920 px (8,5 inferencias por cuadro) y 89 % con mosaicos nativos + 1280 px (unas 24 inferencias por cuadro). Ver la [evaluación en video](../experimentos/evaluacion-video.md).

# Próximos pasos

1. **Medir el costo en las placas.** Agregar 1280 px y mosaicos reducidos a 1920 px (y mosaicos nativos + 1280 px en la Jetson) al [benchmark](../obc/benchmark.md): en una placa el costo crece cerca de la cantidad de píxeles, no como en la GPU de la laptop.
2. **Reentrenar una sola vez** con las tres clases de la misión y entrada de 1280 px, y comparar contra estas evaluaciones con las mismas clases. Debería recuperar las personas grandes que se pierden al inferir a más resolución que la de entrenamiento.
3. **Considerar un modelo híbrido** si la placa no alcanza: 1280 px solo en zonas de interés o mosaicos a menor frecuencia que la pasada completa.

[^mision]: `mission_eval/val.json`, recall por tamaño.
[^resolucion]: `mission_eval/resolution_val.json` de la ejecución YOLO26n.
[^sahi]: F. C. Akyon *et al.*, Slicing Aided Hyper Inference, ICIP 2022.
