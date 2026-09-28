---
type: Modelo
title: YOLO26n
description: Generación más reciente de Ultralytics, end-to-end sin NMS y orientada a dispositivos de borde; modelo de referencia para las placas.
resource: https://docs.ultralytics.com/models/yolo26/
tags: [yolo, modelo, nano, edge]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-28T02:30:00Z }
sources:
  - id: yolo26
    resource: https://docs.ultralytics.com/models/yolo26/
    title: Documentación oficial de YOLO26
---

Generación más reciente de Ultralytics, también en variante *nano* y preentrenada en COCO. Según la documentación del fabricante[^yolo26], produce una salida *end-to-end* sin NMS, elimina el módulo DFL y está orientada explícitamente a dispositivos de borde. También declara mejoras en la función de pérdida pensadas para objetos pequeños; en este experimento esas mejoras no se tradujeron en una ganancia clara en las clases pequeñas.

Es el modelo de referencia del [benchmark en placas](../obc/benchmark.md): su checkpoint `best.pt` proviene de la ejecución `20260928T003017Z`, [reentrenada](../experimentos/reentrenamiento-1280.md) con persona y vehículo a 1280 px.

[^yolo26]: Ultralytics, YOLO26, documentación oficial. Afirmaciones del fabricante, a verificar en placa.
