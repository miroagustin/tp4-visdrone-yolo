---
type: Objetivos
title: Objetivos
description: Objetivo general del TP4 y objetivos específicos con su estado.
tags: [objetivos, estado]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
---

**Objetivo general.** Evaluar la viabilidad de un detector YOLO de tamaño *nano* para detectar personas y vehículos a bordo de un dron, con una métrica alineada a la misión.

**Objetivos específicos.** La tabla detalla los objetivos específicos e indica cuáles están cumplidos y cuáles pendientes.

| | Objetivo específico | Estado |
|---|---|---|
| O1 | Preparar y auditar VisDrone2019-DET en formato YOLO, con trazabilidad (SHA-256). | Cumplido |
| O2 | Ajustar YOLO11n y YOLO26n bajo un protocolo idéntico y compararlos en validación. | Cumplido |
| O3 | Construir un paquete de benchmark reproducible y portable para placas OBC. | Cumplido |
| O4 | Medir en Jetson y Raspberry Pi 5 el modelo original y su versión optimizada. | **Pendiente** |
| O5 | Comparar las plataformas y discutir el compromiso precisión/velocidad/memoria. | **Pendiente** |
| O6 | Evaluar test-dev completo con el modelo definitivo. | **Pendiente** |
| O7 | Definir las clases de la misión y evaluar el modelo agrupado sin reentrenar. | Cumplido |
| O8 | Medir la detección por objeto durante la pasada en video (VisDrone-VID). | Cumplido |
| O9 | Evaluar mejoras de inferencia (960 y 1280 px, mosaicos) sin reentrenar. | Cumplido |
| O10 | Medir el costo de las mejoras en las placas y reentrenar a mayor resolución. | **Pendiente** |

Tabla: Objetivos específicos del TP4 y estado al 26 de septiembre de 2026.
