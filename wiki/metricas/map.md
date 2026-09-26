---
type: Métrica
title: Métricas de detección
description: Precision, Recall, mAP50 y mAP50–95 tal como los calcula el evaluador de Ultralytics; no es el evaluador oficial de VisDrone.
tags: [metricas, map, ultralytics]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
---

Se informan *Precision*, *Recall*, mAP50 (precisión media por clase con umbral de IoU de 0,5, promediada entre clases) y mAP50–95 (promedio sobre umbrales de IoU de 0,50 a 0,95 en pasos de 0,05). El mAP50–95 exige mayor exactitud de localización y fue el criterio principal para comparar modelos.

Todas las métricas provienen del evaluador de Ultralytics, **no** del evaluador oficial de VisDrone, que trata las regiones ignoradas de otra forma.

Para la misión interesan además métricas en un **punto de operación** (un umbral de confianza fijo): la precisión es la fracción de detecciones correctas y el recall, la fracción de objetos encontrados con la clase correcta e IoU de al menos 0,5. Y, sobre todo, la [detección por objeto durante la pasada](recall-por-objeto.md).
