---
type: Sección de informe
title: Síntesis para el equipo
description: Qué se hizo, qué se concluye, qué sigue y qué hay que decidir.
tags: [informe, sintesis]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-28T02:30:00Z }
---

| | |
|---|---|
| **Qué se hizo** | Datos preparados y auditados; YOLO11n y YOLO26n entrenados y comparados; clases de la misión definidas; evaluación a 640, 960 y 1280 px y con mosaicos; detección por pasada medida en VisDrone-VID; ambos modelos reentrenados con persona y vehículo a 1280 px; paquete de benchmark OBC regenerado con YOLO26n reentrenado; wiki del proyecto como fuente del informe. |
| **Qué se concluye** | Reentrenado con persona y vehículo a 1280 px, YOLO26n detecta al menos una vez el 89 % de las personas por pasada a 5 FPS (86 % a 2 FPS) con una inferencia por cuadro, frente a 84 % de la línea base a 1280 px y 74 % a 640 px. El costo sigue siendo de unas 7 falsas personas por cuadro con confianza 0,25. Los vehículos pequeños en 4K no llegan (65 %). |
| **Qué sigue** | Medir YOLO26n reentrenado a 1280 px en Jetson (TensorRT) y Raspberry Pi 5 (NCNN); ampliar el video con secuencias sin fuga; evaluar test-dev con el modelo fijado. |
| **Qué decidir** | Modelo exacto de Jetson y responsables; escenario de la misión (altura, velocidad, FPS mínimo); umbral de confianza y uso de un tracker para confirmar objetos; YOLO11n como control; medición de energía. |
