---
type: Sección de informe
title: Síntesis para el equipo
description: Qué se hizo, qué se concluye, qué sigue y qué hay que decidir.
tags: [informe, sintesis]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T21:30:00Z }
---

| | |
|---|---|
| **Qué se hizo** | Datos preparados y auditados; YOLO11n y YOLO26n entrenados y comparados; clases de la misión definidas; evaluación a 640, 960 y 1280 px y con mosaicos; detección por pasada medida en VisDrone-VID; paquete de benchmark OBC verificado; wiki del proyecto como fuente del informe. |
| **Qué se concluye** | Sin reentrenar, 1280 px detecta al menos una vez el 84 % de las personas por pasada a 5 FPS (85 % a 10 FPS), y los mosaicos el 87 %; 640 px se queda en 74 %. Los vehículos pequeños en 4K no llegan (61–70 %). El costo es de 5 a 9 falsas personas por cuadro con confianza 0,25. |
| **Qué sigue** | Medir 640 px, 1280 px y mosaicos en Jetson (TensorRT) y Raspberry Pi 5 (NCNN); reentrenar con las clases de la misión a 1280 px; ampliar el video con secuencias sin fuga; evaluar test-dev con el modelo fijado. |
| **Qué decidir** | Modelo exacto de Jetson y responsables; escenario de la misión (altura, velocidad, FPS mínimo); umbral de confianza y uso de un tracker para confirmar objetos; YOLO11n como control; medición de energía. |
