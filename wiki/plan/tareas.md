---
type: Plan
title: Tareas y criterios de aceptación
description: Trabajo pendiente del TP4, con responsable, entregable verificable y reglas para que los resultados sean comparables.
tags: [plan, tareas]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: guia
    resource: ../../BENCHMARK_OBC.md
---

Ya se completaron la evaluación por clases de la misión, la de resolución y mosaicos, y la de detección por pasada en VisDrone-VID. La tabla ordena el trabajo pendiente. Cada tarea tiene un entregable verificable, de modo que cualquier integrante pueda comprobar si está terminada sin depender de quien la ejecutó.

| # | Tarea | Responsable | Criterio de aceptación |
|---|---|---|---|
| 1 | Publicar el código del benchmark y distribuir el ZIP y su `.sha256` | Coordinación | Ambos equipos trabajan sobre el mismo *commit* y el checksum verifica. |
| 2 | Preparar el entorno y generar el diagnóstico | Cada equipo | `doctor.json` con ARM64, Python de 64 bits y versiones; en Jetson, versión de L4T/JetPack. |
| 3 | Exportar el modelo optimizado | Cada equipo | El motor se construye en la propia placa y pasa la prueba de carga e inferencia. |
| 4 | Ejecutar la prueba corta (`--quick`) | Cada equipo | Termina con `status: finished`. |
| 5 | Ejecutar el benchmark oficial | Cada equipo | Seis mediciones completas, 300 paneles por modelo, telemetría presente, fuente y refrigeración registradas. |
| 6 | Comparación conjunta | Coordinación | `informe.html` se abre en otra computadora sin red; diagnósticos e intentos incompletos excluidos. |
| 7 | Agregar 1280 px y mosaicos al benchmark de placas | Coordinación y cada equipo | FPS, latencia p95 y memoria de cada variante en Jetson y Raspberry Pi 5, con el mismo protocolo. |
| 8 | Reentrenar con las dos clases de la misión y entrada de 1280 px | Coordinación | Comparado con la evaluación a 1280 px sin reentrenar, en DET val y en las secuencias limpias de VID. |
| 9 | Ampliar la evaluación en video sin fuga | Coordinación | Secuencias de VID de test-dev cuyo video no esté en el entrenamiento de DET, para tener más objetos limpios. |
| 10 | Evaluar test-dev completo con el modelo fijado | Coordinación | Evaluación única, sin ajustar hiperparámetros después de verla. |
| 11 | Análisis e informe final | Todo el equipo | Discusión frente al objetivo de detección por pasada y al requisito operativo. |

Tabla: Plan de trabajo. Cada ejecución oficial del benchmark requiere al menos 35 minutos, más exportación, calentamientos y evaluación.

# Reglas para que los resultados sean comparables

- No reentrenar ni modificar checkpoints o hiperparámetros a partir de los resultados del benchmark.
- No instalar ruedas de PyTorch para x86/Windows en la Jetson ni actualizar drivers o JetPack automáticamente. Si no existe una combinación compatible con Ultralytics 8.4.162, informar el bloqueo en lugar de cambiar de motor.
- No reemplazar CUDA por CPU de forma silenciosa. Ante un error, corregir el entorno y lanzar una ejecución nueva, sin mezclar repeticiones de intentos distintos.
- Una diferencia de mAP respecto del `.pt` debe investigarse como posible efecto de la exportación o de la precisión numérica, no ocultarse.
- Las pruebas de resolución y de video se comparan siempre con las mismas dos clases de la misión.
