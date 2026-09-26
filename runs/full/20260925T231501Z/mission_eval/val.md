# Evaluación agrupada por misión · 20260925T231501Z · val

548 imágenes, entrada 640 px. Evaluación agrupada post hoc del modelo de 10 clases; no reemplaza un reentrenamiento. Métricas estilo Ultralytics; no es el evaluador oficial de VisDrone.

| Variante | mAP50 | mAP50-95 |
|---|---:|---:|
| 10 clases VisDrone (control) | 28.5 % | 15.9 % |
| Misión, agrupado directo | 47.9 % | 25.1 % |
| Misión, agrupado + fusión IoU 0.7 | 48.8 % | 25.3 % |

Control: el validador de Ultralytics en esta misma pasada dio mAP50 28.5 % y mAP50-95 15.9 %. run.json registra 28.5 % y 15.9 %.

## Clases de la misión (agrupado + fusión), confianza 0.25, IoU 0,5

| Clase | Objetos | AP50 | AP50-95 | Precisión | Recall |
|---|---:|---:|---:|---:|---:|
| persona | 13969 | 34.6 % | 13.0 % | 65.3 % | 27.7 % |
| vehiculo | 24790 | 63.0 % | 37.5 % | 77.3 % | 54.2 % |
| todos | 38759 | | | 74.3 % | 44.6 % |

## Precisión y recall según el umbral de confianza

| Confianza | persona P / R | vehiculo P / R | todos P / R |
|---:|---:|---:|---:|
| 0.05 | 25.4 % / 50.1 % | 37.1 % / 71.6 % | 32.8 % / 63.9 % |
| 0.1 | 35.4 % / 45.0 % | 49.9 % / 66.8 % | 44.9 % / 59.0 % |
| 0.15 | 45.8 % / 38.9 % | 60.7 % / 62.3 % | 56.0 % / 53.8 % |
| 0.25 | 65.3 % / 27.7 % | 77.3 % / 54.2 % | 74.3 % / 44.6 % |
| 0.4 | 86.5 % / 14.8 % | 93.0 % / 41.5 % | 91.9 % / 31.9 % |
| 0.5 | 93.7 % / 8.9 % | 97.4 % / 34.3 % | 96.9 % / 25.2 % |

## Recall por tamaño en la entrada de la red (confianza 0.25)

| Clase | <4 px | 4-8 px | 8-16 px | 16-32 px | >=32 px |
|---|---:|---:|---:|---:|---:|
| persona | 0.5 % (1164) | 11.8 % (5312) | 38.2 % (5971) | 61.9 % (1413) | 78.9 % (109) |
| vehiculo | 2.3 % (1073) | 23.3 % (4449) | 48.4 % (9127) | 73.9 % (7319) | 90.0 % (2822) |

Entre paréntesis, cantidad de objetos anotados en cada tamaño.
