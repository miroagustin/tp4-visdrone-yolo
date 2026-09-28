---
type: Resultado
title: Evaluación de resolución y mosaicos
description: Sin reentrenar, procesar la imagen completa a 1280 px sube el recall de personas de 27 % a 43 % y el mAP50 de la misión de 48,4 % a 61,4 %; los mosaicos dan el mayor recall con menos precisión y unas 6 inferencias por imagen.
resource: ../../runs/full/20260925T231501Z/mission_eval/resolution_val.json
tags: [resultados, resolucion, sahi, mosaicos, objetos-pequenos]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-28T02:30:00Z }
sources:
  - id: resolucion
    resource: ../../runs/full/20260925T231501Z/mission_eval/resolution_val.json
    title: Resultados por variante en DET val
  - id: codigo
    resource: ../../tp4/inference.py
    title: Inferencia por resolución y mosaicos
  - id: sahi
    resource: /referencias/bibliografia.md
---

Esta evaluación corresponde al modelo de **línea base**: YOLO26n entrenado a 640 px con las diez clases de VisDrone. Los resultados del modelo reentrenado con persona y vehículo a 1280 px están en el [reentrenamiento](reentrenamiento-1280.md).

# Método

Se evaluó el mismo `best.pt` de YOLO26n, **sin reentrenar**, sobre las 548 imágenes de validación de DET, con las [clases de la misión](../mision/clases.md) y cuatro formas de procesar cada imagen[^codigo]:

- **640, 960 y 1280 px:** la imagen completa reducida a ese lado mayor.
- **Mosaicos:** además de la pasada completa a 640 px, la imagen nativa se corta en mosaicos de 640 px con 20 % de solapamiento, al estilo de SAHI[^sahi]. Se descartan las cajas cortadas por un borde interno del mosaico y se unen las detecciones con supresión por clase (IoU 0,5).
- **Mosaicos + 1280 px:** los mismos mosaicos nativos, pero con la pasada completa a 1280 px en lugar de 640 px.

La variante de mosaicos sobre una imagen reducida (1920 o 2560 px de lado mayor) coincide en DET con los mosaicos nativos, porque sus imágenes no superan los 1920 px; se evalúa en [video](evaluacion-video.md).

Todas las variantes usan el pipeline `predict` con confianza mínima 0,01, que subestima levemente el mAP frente al validador; la variante de 640 px sirve de referencia con el mismo pipeline. El tamaño de cada objeto se refiere siempre a la entrada de 640 px, para comparar las mismas personas entre variantes.

# Resultados

| Variante | Inferencias por imagen | ms por imagen (RTX 5070) | mAP50 | mAP50–95 | Recall persona | Recall todos |
|---|---:|---:|---:|---:|---:|---:|
| 640 px | 1 | 16,2 | 48,4 % | 25,1 % | 27,2 % | 44,5 % |
| 960 px | 1 | 17,0 | 57,0 % | 30,9 % | 37,4 % | 53,8 % |
| 1280 px | 1 | 18,5 | **61,4 %** | **33,6 %** | 42,9 % | 57,6 % |
| Mosaicos | 6,2 | 53,9 | 55,8 % | 31,7 % | 45,2 % | 61,3 % |
| Mosaicos + 1280 px | 6,2 | 60,8 | 61,0 % | **33,6 %** | **48,0 %** | **63,1 %** |

Tabla: Variantes de resolución con las clases de la misión en DET val. Recall por cuadro con confianza 0,25 e IoU 0,5[^resolucion].

| Variante | persona P / R | vehículo P / R |
|---|---:|---:|
| 640 px | 66,3 % / 27,2 % | 76,6 % / 54,3 % |
| 960 px | 63,9 % / 37,4 % | 76,5 % / 63,0 % |
| 1280 px | 64,8 % / 42,9 % | 77,8 % / 65,9 % |
| Mosaicos | 64,2 % / 45,2 % | 71,3 % / 70,4 % |
| Mosaicos + 1280 px | 64,5 % / 48,0 % | 73,7 % / 71,6 % |

Tabla: Precisión (P) y recall (R) por clase con confianza 0,25.

| Variante | < 4 px | 4–8 px | 8–16 px | 16–32 px | ≥ 32 px |
|---|---:|---:|---:|---:|---:|
| 640 px | 0,4 % | 11,3 % | 37,5 % | 61,5 % | 76,1 % |
| 960 px | 3,5 % | 23,1 % | 49,2 % | 66,7 % | 66,1 % |
| 1280 px | 9,8 % | 29,6 % | 55,2 % | 66,3 % | 65,1 % |
| Mosaicos | 11,5 % | 33,3 % | 56,4 % | 67,5 % | 78,0 % |
| Mosaicos + 1280 px | 14,0 % | 36,8 % | 59,4 % | 68,2 % | 67,9 % |

Tabla: Recall de personas según su tamaño en la entrada de 640 px, confianza 0,25.

# Lectura

- **La hipótesis se confirma:** duplicar la resolución efectiva recupera personas pequeñas. Entre 4 y 8 px, el recall pasa de 11 % a 30–33 %. La estimación previa de alrededor de 50 % de recall de personas fue optimista: se llega a 43–45 %.
- **1280 px es el mejor compromiso en precisión global:** mayor mAP con una sola inferencia. Sus personas grandes (≥ 32 px) bajan de 76 % a 65 %, porque quedan más grandes que lo que el modelo vio al entrenar a 640 px.
- **Mosaicos + 1280 px da el mayor recall por cuadro** (48 % de personas, 63 % de todos los objetos) con casi el mAP de 1280 px, con un costo similar al de los mosaicos con pasada a 640 px. Como 1280 px, pierde algo en personas grandes.
- **Los mosaicos con pasada a 640 px maximizan el recall de personas grandes**, pero pierden precisión en vehículos, por falsas detecciones en las uniones, y cuestan unas 6 inferencias por imagen de VisDrone, y muchas más en video 4K.
- **El tiempo de la laptop no predice el de la placa.** En la RTX 5070, 1280 px cuesta apenas un 15 % más que 640 px porque la GPU está subutilizada con lote 1. En una placa el costo crece más cerca de la cantidad de píxeles: alrededor de 4 veces para 1280 px. Por eso estas variantes deben pasar por el [benchmark en placas](../obc/benchmark.md).
- **Reentrenar a mayor resolución** podría recuperar las personas grandes y sumar recall, ahora con una base medida contra la cual comparar.

[^codigo]: `tp4/inference.py`; comando `python -m tp4.cli resolution runs/full/20260925T231501Z`.
[^resolucion]: `mission_eval/resolution_val.json` de la ejecución YOLO26n.
[^sahi]: F. C. Akyon *et al.*, Slicing Aided Hyper Inference, ICIP 2022.
