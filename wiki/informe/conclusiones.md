---
type: Sección de informe
title: Conclusiones
description: Conclusiones del TP4 al 26 de septiembre de 2026.
tags: [informe, conclusiones]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-28T02:30:00Z }
---

1. El pipeline de datos, entrenamiento y evaluación del TP4 está completo y es trazable: datos auditados con hash, ejecuciones con configuración registrada, evaluaciones reproducibles por línea de comandos y una wiki que concentra el conocimiento del proyecto.
2. YOLO11n y YOLO26n alcanzan una precisión equivalente sobre VisDrone (mAP50–95 cercano al 16 %). El límite no es la arquitectura, sino el tamaño aparente de los objetos al procesar la imagen a 640 px.
3. Agrupar las clases según la misión elimina la confusión entre vehículos, y reentrenar con persona y vehículo a 1280 px ataca el límite real, el tamaño aparente: frente a la línea base inferida a 1280 px, el mAP50 de la misión pasa de 61,4 % a 69,9 %, y el recall de personas por cuadro, de 43 % a 57 %. El modelo recupera tanto personas pequeñas como las grandes que la línea base perdía al cambiar de escala.
4. Medido por pasada en video y con secuencias limpias, el objetivo del 85 % se cumple para personas con una sola inferencia por cuadro: 89 % a 5 FPS y 86 % a 2 FPS, frente a 84 % y 80 % de la línea base a 1280 px. Para vehículos muy pequeños en video 4K no alcanza (65 %): requiere volar más bajo o mosaicos a resolución nativa.
5. El precio de esa detección son las falsas alarmas: unas 7 falsas personas por cuadro con confianza 0,25, igual que la línea base; con 0,4 bajan a 3,4 y la detección por pasada queda en 84 %. Un tracker que confirme por persistencia es la forma natural de reducirlas y todavía no está medido.
6. YOLO11n y YOLO26n vuelven a ser equivalentes al reentrenarlos; YOLO26n sigue como modelo de las placas por su salida sin NMS y sus menores falsas alarmas. En la Raspberry Pi 5, a 1280 px y solo CPU, NCNN mejora de 0,91 a 3,11 FPS frente a PyTorch, pero no llega al requisito de 5 FPS. La prueba en Jetson con GPU y TensorRT sigue pendiente; aún no hay una configuración de placa que cumpla el requisito operativo medido.
