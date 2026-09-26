---
type: Métrica
title: Indicadores de rendimiento en placa
description: Qué mide el benchmark en cada computadora de a bordo y cómo se lee cada indicador para el dron.
tags: [metricas, obc, fps, latencia, memoria]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: guia
    resource: ../../BENCHMARK_OBC.md
    title: Guía operativa del benchmark
---

| Indicador | Interpretación para el dron |
|---|---|
| FPS sostenidos (media y dispersión) | Frecuencia real de detección; se contrasta con el requisito Δd = v/f. |
| Latencia p50 / p95 | Retardo típico y en el peor caso habitual entre la captura y la decisión. |
| Factor de aceleración | Ganancia del motor optimizado frente al `.pt` en la misma placa. |
| Δ mAP frente al `.pt` | Costo en precisión de exportar y cambiar la precisión numérica. |
| RSS pico y ahorro de RSS | Memoria disponible para navegación, telemetría y registro. |
| Temperatura y *throttling* | Estabilidad durante el vuelo; necesidad de disipación (peso adicional). |

Tabla: Indicadores del benchmark y su lectura operativa[^guia].

El protocolo actual no mide consumo energético: temperatura, RAM y modo de potencia no equivalen a energía por inferencia. Medirla es una de las [decisiones abiertas](../plan/decisiones.md).

[^guia]: `BENCHMARK_OBC.md`, secciones 5 y 7.
