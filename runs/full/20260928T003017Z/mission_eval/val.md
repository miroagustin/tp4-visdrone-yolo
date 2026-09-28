# Evaluación agrupada por misión · 20260928T003017Z · val

548 imágenes, entrada 1280 px. Modelo entrenado con las clases de la misión. Métricas estilo Ultralytics; no es el evaluador oficial de VisDrone.

| Variante | mAP50 | mAP50-95 |
|---|---:|---:|
| Misión, agrupado directo | 70.4 % | 40.0 % |
| Misión, agrupado + fusión IoU 0.7 | 70.4 % | 40.0 % |

Control: el validador de Ultralytics en esta misma pasada dio mAP50 70.4 % y mAP50-95 40.0 %. run.json registra 70.4 % y 40.0 %.

## Clases de la misión (agrupado + fusión), confianza 0.25, IoU 0,5

| Clase | Objetos | AP50 | AP50-95 | Precisión | Recall |
|---|---:|---:|---:|---:|---:|
| persona | 13969 | 60.0 % | 27.1 % | 64.1 % | 57.6 % |
| vehiculo | 24789 | 80.8 % | 52.9 % | 77.9 % | 75.6 % |
| todos | 38758 | | | 73.2 % | 69.1 % |

## Precisión y recall según el umbral de confianza

| Confianza | persona P / R | vehiculo P / R | todos P / R |
|---:|---:|---:|---:|
| 0.05 | 27.9 % / 73.3 % | 38.8 % / 86.9 % | 34.5 % / 82.0 % |
| 0.1 | 37.1 % / 70.0 % | 51.5 % / 83.9 % | 45.8 % / 78.9 % |
| 0.15 | 46.6 % / 65.9 % | 62.3 % / 81.2 % | 56.3 % / 75.7 % |
| 0.25 | 64.1 % / 57.6 % | 77.9 % / 75.6 % | 73.2 % / 69.1 % |
| 0.4 | 85.3 % / 44.9 % | 91.1 % / 67.0 % | 89.4 % / 59.0 % |
| 0.5 | 92.0 % / 34.0 % | 94.9 % / 60.1 % | 94.2 % / 50.7 % |

## Recall por tamaño en la entrada de la red (confianza 0.25)

| Clase | <4 px | 4-8 px | 8-16 px | 16-32 px | >=32 px |
|---|---:|---:|---:|---:|---:|
| persona | 0.0 % (36) | 16.0 % (1126) | 45.3 % (5308) | 70.1 % (5978) | 83.3 % (1521) |
| vehiculo | 0.0 % (38) | 22.8 % (1036) | 54.3 % (4454) | 75.6 % (9125) | 90.7 % (10136) |

Entre paréntesis, cantidad de objetos anotados en cada tamaño.
