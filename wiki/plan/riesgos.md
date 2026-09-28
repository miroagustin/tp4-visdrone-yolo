---
type: Riesgo
title: Limitaciones y riesgos
description: Qué limita las conclusiones actuales y qué puede demorar el trabajo pendiente.
tags: [plan, riesgos, limitaciones]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-28T02:00:00Z }
---

- **Una sola semilla por modelo.** Las diferencias entre YOLO11n y YOLO26n carecen de significancia estadística.
- **Evaluador no oficial.** Las métricas son las de Ultralytics, no las del evaluador oficial de VisDrone, que trata las regiones ignoradas de otra forma.
- **Test-dev parcialmente observado.** Las vistas previas por época de los entrenamientos usaron imágenes de test-dev, y el benchmark usa 300 imágenes de ese mismo conjunto. Ninguna decisión de modelo debe basarse en esas observaciones.
- **Muestra de 300 imágenes.** La comparación *relativa* dentro de una misma placa es más robusta que los valores absolutos.
- **FPS desde disco.** Las mediciones no equivalen a los FPS con una cámara real ni incluyen el resto del software de a bordo.
- **Sin medición de energía** en el protocolo base.
- **Compatibilidad de software en Jetson.** La combinación de JetPack, PyTorch, TensorRT y Ultralytics 8.4.162 puede bloquear la exportación. Es el principal riesgo de calendario.
- **Discrepancias sin aislar.** Las validaciones internas por época no coinciden exactamente con la evaluación independiente de `best.pt`, y evaluar con `predict` dio unos 3 puntos menos de mAP50 que con el validador.
- **Fuga entre DET y VID.** Cuatro de las siete secuencias de validación de VID vienen de videos que aportan imágenes al entrenamiento de DET. Sus resultados son optimistas; las conclusiones se apoyan en las tres secuencias limpias, que son pocas (187 personas y 89 vehículos).
- **FPS de los videos asumidos.** Los archivos no traen cuadros por segundo; se asumen 30 FPS nominales para convertir cuadros en segundos y simular los FPS de cada placa.
- **Costo de 1280 px en las placas sin medir.** El modelo reentrenado procesa cuatro veces más píxeles que a 640 px. En la laptop eso casi no se nota, porque la GPU está subutilizada con lote 1; en una placa el costo crece cerca de la cantidad de píxeles.
