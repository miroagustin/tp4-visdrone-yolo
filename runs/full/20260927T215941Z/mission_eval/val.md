# Evaluación agrupada por misión · 20260927T215941Z · val

548 imágenes, entrada 1280 px. Modelo entrenado con las clases de la misión. Métricas estilo Ultralytics; no es el evaluador oficial de VisDrone.

| Variante | mAP50 | mAP50-95 |
|---|---:|---:|
| Misión, agrupado directo | 69.7 % | 39.7 % |
| Misión, agrupado + fusión IoU 0.7 | 69.7 % | 39.7 % |

Control: el validador de Ultralytics en esta misma pasada dio mAP50 69.7 % y mAP50-95 39.7 %. run.json registra 69.7 % y 39.7 %.

## Clases de la misión (agrupado + fusión), confianza 0.25, IoU 0,5

| Clase | Objetos | AP50 | AP50-95 | Precisión | Recall |
|---|---:|---:|---:|---:|---:|
| persona | 13969 | 59.2 % | 26.6 % | 62.8 % | 57.4 % |
| vehiculo | 24789 | 80.3 % | 52.9 % | 77.2 % | 75.5 % |
| todos | 38758 | | | 72.3 % | 69.0 % |

## Precisión y recall según el umbral de confianza

| Confianza | persona P / R | vehiculo P / R | todos P / R |
|---:|---:|---:|---:|
| 0.05 | 26.9 % / 73.4 % | 37.9 % / 86.8 % | 33.5 % / 82.0 % |
| 0.1 | 35.5 % / 70.0 % | 50.7 % / 83.9 % | 44.6 % / 78.9 % |
| 0.15 | 45.2 % / 66.0 % | 61.4 % / 81.1 % | 55.2 % / 75.6 % |
| 0.25 | 62.8 % / 57.4 % | 77.2 % / 75.5 % | 72.3 % / 69.0 % |
| 0.4 | 83.5 % / 43.8 % | 90.3 % / 66.9 % | 88.4 % / 58.6 % |
| 0.5 | 91.2 % / 33.9 % | 94.7 % / 60.6 % | 93.9 % / 51.0 % |

## Recall por tamaño en la entrada de la red (confianza 0.25)

| Clase | <4 px | 4-8 px | 8-16 px | 16-32 px | >=32 px |
|---|---:|---:|---:|---:|---:|
| persona | 0.0 % (36) | 11.7 % (1126) | 45.0 % (5308) | 71.1 % (5978) | 82.0 % (1521) |
| vehiculo | 0.0 % (38) | 20.9 % (1036) | 54.2 % (4454) | 75.6 % (9125) | 90.5 % (10136) |

Entre paréntesis, cantidad de objetos anotados en cada tamaño.
