---
type: Resultado
title: Reentrenamiento con las clases de la misión a 1280 px
description: Entrenados con persona y vehículo a 1280 px, YOLO26n y YOLO11n detectan al menos una vez el 89–90 % de las personas por pasada a 5 FPS; el objetivo del 85 % se cumple con una sola inferencia por cuadro.
tags: [resultados, reentrenamiento, yolo26n, yolo11n, mision]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-28T02:30:00Z }
sources:
  - id: run26
    resource: ../../runs/full/20260928T003017Z/run.json
    title: Ejecución YOLO26n reentrenado
  - id: run11
    resource: ../../runs/full/20260927T215941Z/run.json
    title: Ejecución YOLO11n reentrenado
  - id: resolucion
    resource: ../../runs/full/20260928T003017Z/mission_eval/resolution_val.json
    title: Evaluación por resolución de YOLO26n reentrenado
  - id: video
    resource: ../../runs/full/20260928T003017Z/mission_eval/video_val.json
    title: Evaluación en video de YOLO26n reentrenado
  - id: base
    resource: ../../runs/full/20260925T231501Z/mission_eval/resolution_val.json
    title: Línea base inferida a 1280 px sin reentrenar
  - id: paquete
    resource: ../../BENCHMARK_OBC.md
    title: Paquete del benchmark en placas
---

# Qué se cambió

Las evaluaciones de la línea base mostraron que el límite era el tamaño aparente de las personas, y que inferir a 1280 px con un modelo entrenado a 640 px recuperaba las pequeñas pero perdía las grandes (ver [resolución y mosaicos](../mejoras/resolucion-y-mosaicos.md)). Por eso YOLO11n y YOLO26n se entrenaron de nuevo con dos cambios respecto del [protocolo](protocolo-entrenamiento.md) de la línea base:

- **Clases de la misión desde las etiquetas.** Cada etiqueta de VisDrone se convierte a persona o vehículo al preparar los datos (ver [clases de la misión](../mision/clases.md)). El modelo, la evaluación y las placas usan las mismas dos clases.
- **Entrada de 1280 px**, la configuración por defecto de la misión.

Las épocas, el lote, la semilla y los datos son los mismos. YOLO11n tardó 2,51 h y YOLO26n, 2,93 h[^run26].

# Validación

| Modelo | Precision | Recall | mAP50 | mAP50–95 | AP50 persona | AP50 vehículo |
|---|---:|---:|---:|---:|---:|---:|
| YOLO11n | 77,6 % | 62,1 % | 69,7 % | 39,7 % | 59,2 % | 80,3 % |
| YOLO26n | **79,4 %** | **62,3 %** | **70,4 %** | **40,0 %** | **60,0 %** | **80,8 %** |

Tabla: Evaluación de `best.pt` con el validador de Ultralytics sobre las 548 imágenes de validación, a 1280 px[^run11]. Estas cifras de dos clases no se comparan con el mAP de diez clases de la línea base.

# Comparación con la línea base

La comparación usa la misma variante (imagen completa a 1280 px) y el mismo procedimiento de predicción para los tres modelos. La línea base es YOLO26n entrenado a 640 px con diez clases, inferido a 1280 px y reagrupado[^base].

| Modelo | mAP50 misión | Recall persona | Recall vehículo | Precisión persona |
|---|---:|---:|---:|---:|
| Línea base (YOLO26n, 640 px, 10 clases) | 61,4 % | 42,9 % | 65,9 % | 64,8 % |
| YOLO11n reentrenado | 69,3 % | 57,3 % | 75,7 % | 63,1 % |
| YOLO26n reentrenado | **69,9 %** | **57,4 %** | **75,8 %** | 64,5 % |

Tabla: DET val con imagen completa a 1280 px. Recall y precisión por cuadro con confianza 0,25 e IoU 0,5[^resolucion].

| Tamaño de la persona | < 4 px | 4–8 px | 8–16 px | 16–32 px | ≥ 32 px |
|---|---:|---:|---:|---:|---:|
| Línea base | 9,8 % | 29,6 % | 55,2 % | 66,3 % | 65,1 % |
| YOLO26n reentrenado | 15,3 % | 45,4 % | 69,7 % | 82,2 % | 86,2 % |

Tabla: Recall de personas por cuadro según su tamaño, referido a la entrada de 640 px, con imagen completa a 1280 px y confianza 0,25.

La mejora aparece en todos los tamaños. En las personas grandes, la línea base caía de 76 % (a 640 px) a 65 % al inferir a 1280 px, porque quedaban más grandes que las vistas en entrenamiento; el modelo reentrenado llega a 86 %.

| Modelo | Personas a 10 FPS | Personas a 5 FPS | Personas a 2 FPS | Vehículos a 5 FPS | Falsas personas por cuadro |
|---|---:|---:|---:|---:|---:|
| Línea base | 85,0 % | 84,0 % | 80,4 % | 64,0 % | 7,0 |
| YOLO11n reentrenado | 90,4 % | **89,8 %** | 85,9 % | 65,2 % | 8,0 |
| YOLO26n reentrenado | **90,9 %** | 88,8 % | **86,4 %** | 65,2 % | **6,9** |

Tabla: Objetos detectados al menos una vez durante la pasada en las tres secuencias limpias de VisDrone-VID (187 personas y 89 vehículos), imagen completa a 1280 px, confianza 0,25[^video].

En la demostración en video del notebook, sobre la secuencia `uav0000117_02622_v`, a 10 FPS simulados, YOLO26n reentrenado detecta al menos una vez 93 de 105 personas, frente a 84 de la línea base.

# Resolución de entrada con el modelo reentrenado

| Variante | Inferencias por imagen | mAP50 misión | Recall persona | Recall vehículo | Personas por pasada a 5 FPS |
|---|---:|---:|---:|---:|---:|
| Imagen completa 640 px | 1 | 49,9 % | 33,4 % | 58,9 % | 78,6 % |
| Imagen completa 960 px | 1 | 63,2 % | 49,5 % | 70,7 % | — |
| Imagen completa 1280 px | 1 | 69,9 % | 57,4 % | 75,8 % | 88,8 % |
| Mosaicos nativos | 6,2 | 64,7 % | 59,5 % | 77,8 % | 93,0 % |
| Mosaicos nativos + 1280 px | 6,2 | **70,0 %** | **62,3 %** | **79,6 %** | **95,2 %** |

Tabla: YOLO26n reentrenado. mAP y recall en DET val con confianza 0,25; detección por pasada en las secuencias limpias de VID. En video, por la secuencia 4K, los mosaicos nativos cuestan unas 23,5 inferencias por cuadro; sobre la imagen reducida a 1920 px, 8,5, con el mismo 93,0 % de personas.

- **El modelo necesita la entrada de 1280 px.** Inferido a 640 px pierde casi toda la mejora (49,9 % de mAP50, frente a 48,4 % de la línea base a 640 px). Si una placa no sostiene 1280 px, no alcanza con bajar la resolución de este modelo.
- **Los mosaicos agregan recall a un costo alto.** Sobre la imagen completa a 1280 px suman unos 5 puntos de recall de personas y casi no cambian el mAP, con seis o más inferencias por imagen. Siguen siendo un resultado de laboratorio.
- En DET val, los mosaicos sobre la imagen reducida a 1920 o 2560 px coinciden con los nativos: ninguna imagen de validación supera los 1920 px.

# Umbral de confianza

| Confianza | Línea base: personas / falsas por cuadro | YOLO26n reentrenado: personas / falsas por cuadro |
|---:|---:|---:|
| 0,10 | 90,9 % / 22,3 | 94,1 % / 19,2 |
| 0,25 | 84,0 % / 7,0 | 88,8 % / 6,9 |
| 0,40 | 73,3 % / 2,9 | 84,0 % / 3,4 |

Tabla: Personas detectadas al menos una vez por pasada a 5 FPS y falsas personas por cuadro, imagen completa a 1280 px, secuencias limpias.

Con el modelo reentrenado, subir la confianza a 0,4 baja las falsas alarmas a la mitad y deja la detección por pasada en 84 %, casi en el objetivo. Es un insumo para la [decisión abierta](../plan/decisiones.md) sobre el umbral operativo.

# Referencia en test-dev

El [paquete del benchmark](../obc/benchmark.md) lleva YOLO26n reentrenado y su evaluación de referencia en la laptop sobre las 300 imágenes de test-dev, a 1280 px: mAP50 57,5 % y mAP50–95 32,0 %, con AP50 de 35,0 % en persona y 80,0 % en vehículo[^paquete]. Las personas de test-dev resultan mucho más difíciles que las de validación (AP50 de 60,0 %). No es la evaluación final de test-dev: las vistas previas por época observaron imágenes de ese conjunto.

# Conclusiones

- **El objetivo se cumple en el laboratorio con una sola inferencia por cuadro.** YOLO26n reentrenado a 1280 px detecta al menos una vez el 88,8 % de las personas a 5 FPS y el 86,4 % a 2 FPS, sin más falsas alarmas que la línea base.
- **Reentrenar corrige el desajuste de escala.** Mejora el recall de personas pequeñas y recupera las grandes que la línea base perdía al inferir a 1280 px.
- **YOLO11n y YOLO26n vuelven a ser equivalentes en detección.** YOLO26n comete menos falsas alarmas y no requiere NMS, por lo que sigue siendo el modelo de las placas.
- **Los vehículos pequeños del video 4K siguen sin alcanzarse** (65 % por pasada). Requieren volar más bajo o mosaicos a resolución nativa.
- **La pregunta pasa a ser el hardware:** qué FPS sostiene cada placa con YOLO26n a 1280 px.

[^run26]: `runs/full/20260928T003017Z/run.json`.
[^run11]: `run.json` de `20260927T215941Z` (YOLO11n) y `20260928T003017Z` (YOLO26n).
[^resolucion]: `mission_eval/resolution_val.json` de cada ejecución; comando `python -m tp4.cli resolution`.
[^video]: `mission_eval/video_val.json` de cada ejecución; comando `python -m tp4.cli video`.
[^base]: `runs/full/20260925T231501Z/mission_eval/resolution_val.json` y `video_val.json`.
[^paquete]: `BENCHMARK_OBC.md`; paquete `package_20260928T020732595419Z`.
