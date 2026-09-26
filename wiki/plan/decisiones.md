---
type: Decisión
title: Decisiones
description: Decisiones ya tomadas por el equipo y decisiones abiertas para acercar el trabajo al problema operativo del dron.
tags: [plan, decisiones]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
---

# Decisiones tomadas

| Decisión | Motivo |
|---|---|
| YOLO26n como modelo de referencia en placa | Precisión equivalente a YOLO11n; salida sin NMS y orientación a dispositivos de borde. |
| Dos clases de la misión: persona y vehículo | Es lo que la misión necesita distinguir; agrupar elimina la confusión *car*/*van*. Dos ruedas se suma a vehículo: el conductor ya está anotado como persona y hay muy pocos casos limpios. |
| Objetivo: 85 % de las personas detectadas al menos una vez por pasada, a 5 FPS o más en la placa | El 85 % por cuadro no es alcanzable con objetos de pocos píxeles; la pasada da varias oportunidades. 5 FPS equivale a 2 m entre detecciones a 10 m/s. El objetivo se fija sobre personas porque los vehículos pequeños en 4K no alcanzan sin reentrenar. |
| No reentrenar solo para agrupar | La evaluación agrupada ya elimina la confusión; el límite es el tamaño aparente. |
| Probar la resolución antes de reentrenar | El 46 % de las personas mide menos de 8 px en la entrada de 640 px; la prueba sin reentrenar confirmó la mejora. |
| Entrada de 1280 px por defecto | Mejor mAP (61,4 %) y personas detectadas por pasada en 84–85 % a 5–10 FPS, con una sola inferencia por cuadro. |
| Mosaicos solo como resultado de laboratorio | Reducidos a 1920 px llegan a 88 % de personas a 5 FPS, y nativos + 1280 px a 89 %, pero con 9 a 24 inferencias por cuadro; no se llevan a la placa. |
| Demo: `.pt` frente a optimizado en una placa por SSH | El benchmark ya compara ambas variantes; sus FPS se cruzan con la evaluación en video para ver si se cumple el objetivo. |
| Informar el video solo con secuencias limpias | Cuatro de las siete secuencias de VID comparten video de origen con el entrenamiento de DET. |

Tabla: Decisiones tomadas al 26 de septiembre de 2026.

# Decisiones abiertas

1. **Asignar hardware y responsables.** Registrar el modelo exacto de Jetson (su generación cambia mucho los resultados), la fuente de alimentación y la refrigeración que se usarían en vuelo.
2. **Fijar el escenario de referencia** de la misión: altura, velocidad, cámara y tipo de misión. De él se derivan el FPS mínimo, la latencia p95 máxima y el tamaño mínimo de objeto exigible (ver [requisitos operativos](../mision/requisitos-operativos.md)).
3. **Incorporar YOLO11n como control en placa** (extensión opcional). La elección de YOLO26n se apoya en que no necesita NMS; medir YOLO11n con el mismo protocolo confirmaría si esa ventaja aparece en la placa.
4. **Medir el consumo energético** (extensión). En un dron la batería es el recurso crítico. En Jetson pueden aprovecharse los sensores de potencia que informa `tegrastats`; en la Raspberry Pi 5, un medidor USB-C. El indicador sería la energía por inferencia (J/cuadro).
5. **Fijar el umbral de confianza operativo.** Con 0,25 se detecta el 84–87 % de las personas por pasada con 5–9 falsas alarmas por cuadro; con 0,1 se supera el 90 % con más de 20. La elección depende de si un tracker confirma los objetos por persistencia.
6. **Trabajos futuros hacia el sistema completo:** cuantización INT8 con calibración en TensorRT, captura desde cámara real (CSI/USB) en lugar de disco, seguimiento multiobjeto para confirmar detecciones e integración con el controlador de vuelo.
