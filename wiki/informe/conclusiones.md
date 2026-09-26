---
type: Sección de informe
title: Conclusiones
description: Conclusiones del TP4 al 26 de septiembre de 2026.
tags: [informe, conclusiones]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T21:30:00Z }
---

1. El pipeline de datos, entrenamiento y evaluación del TP4 está completo y es trazable: datos auditados con hash, ejecuciones con configuración registrada, evaluaciones reproducibles por línea de comandos y una wiki que concentra el conocimiento del proyecto.
2. YOLO11n y YOLO26n alcanzan una precisión equivalente sobre VisDrone (mAP50–95 cercano al 16 %). El límite no es la arquitectura, sino el tamaño aparente de los objetos al procesar la imagen a 640 px.
3. Agrupar las clases según la misión elimina la confusión entre vehículos. Aumentar la resolución efectiva recupera personas pequeñas sin reentrenar: con 1280 px, el mAP50 de la misión pasa de 48,4 % a 61,4 %, y el recall de personas por cuadro, de 27 % a 43 %.
4. Medido por pasada en video y con secuencias limpias, el objetivo del 85 % es alcanzable para personas: 84 % con 1280 px a 5 FPS (85 % a 10 FPS) y 87 % con mosaicos, frente a 74 % con 640 px. Para vehículos muy pequeños en video 4K no alcanza sin reentrenar ni volar más bajo.
5. El precio de esa detección son las falsas alarmas: entre 5 y 9 falsas personas por cuadro con confianza 0,25. Un tracker que confirme por persistencia es la forma natural de reducirlas y todavía no está medido.
6. La decisión de despliegue depende ahora del hardware: 1280 px cuesta alrededor de 4 veces más píxeles que 640 px, y los mosaicos, varias inferencias por cuadro. El benchmark en Jetson (con GPU) y Raspberry Pi 5 (sin GPU) ya está preparado y debe incorporar estas variantes.
