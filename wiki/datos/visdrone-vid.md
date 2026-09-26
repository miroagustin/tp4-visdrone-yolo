---
type: Dataset
title: VisDrone2019-VID
description: Videos de VisDrone con identificador por objeto; la validación (7 secuencias, 758 objetos) permite medir si cada objeto se detecta al menos una vez durante la pasada. Cuatro secuencias comparten video de origen con el entrenamiento de DET.
resource: https://github.com/VisDrone/VisDrone-Dataset
tags: [visdrone, video, tracking]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T21:00:00Z }
sources:
  - id: visdrone
    resource: https://github.com/VisDrone/VisDrone-Dataset
    title: VisDrone Dataset (descargas VID y MOT)
  - id: mot-toolkit
    resource: https://github.com/VisDrone/VisDrone2018-MOT-toolkit
    title: VisDrone MOT toolkit
  - id: archivo
    resource: ../../data/archives/VisDrone2019-VID-val.json
    title: Tamaño y SHA-256 del ZIP descargado
---

Las tareas de video de VisDrone (VID y MOT) anotan cada cuadro con el formato `frame_index, target_id, bbox_left, bbox_top, bbox_width, bbox_height, score, object_category, truncation, occlusion`[^mot-toolkit]. El campo `target_id` identifica a cada objeto a lo largo del video: con él se calcula la [detección por objeto](../metricas/recall-por-objeto.md) sin necesidad de un tracker. Las categorías son las mismas diez de DET, más regiones ignoradas (categoría 0, *score* 0) y *others* (11), así que el agrupamiento en [clases de la misión](../mision/clases.md) se aplica sin cambios. El desafío oficial de MOT evalúa solo cinco clases; eso no limita el uso que hacemos acá.

# Validación descargada

Se usó la validación de VID (1,6 GB, descarga manual desde la página oficial[^visdrone]), extraída en `data/raw/VisDrone2019-VID-val/` con su SHA-256 registrado[^archivo].

| Secuencia | Cuadros | Resolución | Personas | Vehículos | Dos ruedas | Video de origen en DET |
|---|---:|---:|---:|---:|---:|---|
| uav0000086_00000_v | 464 | 1344 × 756 | 79 | 0 | 3 | validación |
| uav0000117_02622_v | 349 | 2720 × 1530 | 105 | 32 | 8 | validación |
| uav0000137_00458_v | 233 | 2688 × 1512 | 81 | 44 | 55 | **entrenamiento** |
| uav0000182_00000_v | 363 | 1344 × 756 | 24 | 75 | 56 | **entrenamiento** |
| uav0000268_05773_v | 978 | 3840 × 2160 | 6 | 46 | 0 | ninguno |
| uav0000305_00000_v | 184 | 1904 × 1071 | 6 | 50 | 13 | **entrenamiento** |
| uav0000339_00001_v | 275 | 1904 × 1071 | 34 | 29 | 12 | **entrenamiento** |
| **Total** | **2846** | | **335** | **276** | **147** | |

Tabla: Secuencias de validación de VisDrone-VID, objetos únicos por clase de la misión y relación con DET.

# Verificaciones

- **Identificadores consistentes.** Solo uno de los 758 objetos cambia de clase de la misión a lo largo del video; se le asigna la más frecuente.
- **Fuga con DET confirmada.** Las imágenes de DET se extrajeron de los mismos videos: el prefijo `0000182_00000_d` de DET corresponde a `uav0000182_00000_v`. Una comparación por huella perceptual (dHash) encontró cuadros idénticos. Cuatro secuencias tienen su video de origen en el **entrenamiento** de DET (entre 6 y 18 imágenes cada una), así que el modelo ya vio esas escenas. Por eso los resultados en video se informan aparte para las tres secuencias **limpias** (086, 117 y 268). Las secuencias 086 y 117 comparten origen con la validación de DET, que no se usó para entrenar.
- **Sin cuadros por segundo en los archivos.** Se asume el nominal de 30 FPS. Los objetos se desplazan unos pocos píxeles entre cuadros consecutivos, lo que es coherente con video continuo, pero el valor no está verificado. Por eso los submuestreos se informan también como "1 de cada k cuadros".
- **Resoluciones altas.** Tres secuencias superan los 2600 px de ancho, y una es 4K. A 640 px, un objeto de 4K se reduce 6 veces.

[^mot-toolkit]: VisDrone2018-MOT-toolkit, formato de anotaciones.
[^visdrone]: VisDrone-Dataset, sección de descargas de la tarea 2 (VID).
[^archivo]: `data/archives/VisDrone2019-VID-val.json`.
