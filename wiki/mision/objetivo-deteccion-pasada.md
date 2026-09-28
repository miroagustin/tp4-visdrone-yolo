---
type: Requisito
title: Objetivo de detección por pasada
description: Detectar al menos una vez el 85 % de las personas durante la pasada, con el modelo optimizado a 5 FPS o más en la placa; entrada de 1280 px por defecto.
tags: [mision, objetivo, recall-por-objeto]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-28T02:30:00Z }
---

**Objetivo del TP4:** detectar **al menos una vez durante la pasada el 85 % de las personas**, con el modelo optimizado corriendo **a 5 FPS o más en la placa** y con entrada de **1280 px**.

- **Calidad:** 85 % de personas detectadas al menos una vez, con confianza 0,25, en las secuencias limpias de VisDrone-VID.
- **Velocidad:** 5 FPS sostenidos en la placa. A 10 m/s, el dron avanza 2 m entre detecciones (ver [requisitos operativos](requisitos-operativos.md)).
- **Configuración por defecto:** imagen completa a 1280 px, una inferencia por cuadro. Es la que mejor equilibra calidad y costo; los mosaicos quedan como resultado de laboratorio.
- **Alcance:** el objetivo se fija sobre personas. Vehículo se informa, pero no se exige: los vehículos pequeños en 4K no alcanzan el 85 % con ninguna variante, ni siquiera reentrenando (65 % a 1280 px, 72 % con mosaicos nativos).

La calidad se mide en el laboratorio y la velocidad en la placa. El [benchmark](../obc/benchmark.md) da los FPS que sostiene cada placa, y la [evaluación en video](../experimentos/evaluacion-video.md) da la detección por pasada a esos FPS.

Exigir el 85 % en cada cuadro no es realista con objetos de pocos píxeles: con el modelo de línea base, el recall por cuadro de personas era 27,7 % con confianza 0,25 a 640 px, y con el reentrenado a 1280 px es 57,4 % (ver [evaluación por clases de la misión](../experimentos/evaluacion-mision.md)). En cambio, durante una pasada cada persona aparece en muchos cuadros y basta con verla una vez para registrarla. Este objetivo se mide con la [detección por objeto](../metricas/recall-por-objeto.md) sobre videos con identificador ([VisDrone-VID](../datos/visdrone-vid.md)).

"Al menos una vez" es un criterio generoso. Para que el número sea honesto se fijan estas reglas:

1. **Evaluar a los FPS reales de la placa.** Si el video tiene 30 cuadros por segundo y la Raspberry procesa 3, se evalúa uno de cada 10 cuadros. Así el [benchmark en placas](../obc/benchmark.md) alimenta directamente esta métrica.
2. **Acompañarlo con falsas alarmas por minuto.** Si no, bajar la confianza a 0,05 infla el resultado gratis.
3. **Reportar también "detectado en al menos 3 cuadros"**, que es lo que necesita un tracker para confirmar un objeto, y el **tiempo hasta la primera detección**.
4. **Desglosar por tamaño máximo del objeto** durante la pasada, igual que en la evaluación por cuadro.

**Estado de la calidad: cumplido en el laboratorio.** Con YOLO26n [reentrenado](../experimentos/reentrenamiento-1280.md) a 1280 px, las personas llegan a 88,8 % a 5 FPS, 90,9 % a 10 FPS y 86,4 % a 2 FPS, con una inferencia por cuadro. El modelo de línea base, inferido a 1280 px, se quedaba en 84,0 % a 5 FPS.

**Estado de la velocidad: pendiente** de la medición en placa. El requisito de 5 FPS se mantiene por la distancia entre detecciones; la calidad ya no depende de él, porque a 2 FPS se detecta el 86,4 % de las personas.
