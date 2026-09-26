---
type: Sección de informe
title: Resumen
description: Resumen del informe de avance del TP4.
tags: [informe, resumen]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T21:30:00Z }
---

El objetivo del TP4 es detectar personas y vehículos en imágenes captadas por drones, con un detector lo bastante liviano para ejecutarse a bordo de la aeronave. Sobre VisDrone2019-DET se ajustaron dos detectores de tamaño *nano* preentrenados en COCO, YOLO11n y YOLO26n, con un protocolo idéntico (50 épocas, entrada de 640 px, lote 4 y semilla 42). En validación ambos resultaron prácticamente equivalentes: mAP50–95 de 16,03 % y 15,85 %.

Para acercar el trabajo a la misión, las diez clases se agruparon en persona y vehículo, y se fijó un objetivo operativo: detectar al menos una vez durante la pasada el 85 % de las personas, con el modelo a 5 FPS o más en la placa. Con la entrada de 640 px, el límite es el tamaño aparente: el 46 % de las personas mide menos de 8 px y el modelo encuentra solo el 27 % de ellas en cada cuadro. Sin reentrenar, procesar la imagen a 1280 px sube ese recall al 43 % y el mAP50 de la misión de 48,4 % a 61,4 %.

En videos de VisDrone-VID, usando solo secuencias que no comparten origen con el entrenamiento, a 5 FPS simulados y con confianza 0,25, las personas detectadas al menos una vez pasan de 74 % (640 px) a 84 % (1280 px) y 87 % (mosaicos a resolución nativa). Los vehículos pequeños de un video 4K siguen lejos del objetivo. El siguiente paso es medir estas variantes en una NVIDIA Jetson (GPU integrada, TensorRT) y en una Raspberry Pi 5 (solo CPU, NCNN), con el paquete de benchmark ya preparado, y reentrenar con las clases de la misión a mayor resolución. Este informe se genera a partir de la wiki del proyecto.
