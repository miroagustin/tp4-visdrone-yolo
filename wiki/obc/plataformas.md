---
type: Plataforma
title: Plataformas y variantes
description: Las dos computadoras de a bordo del benchmark, con GPU (NVIDIA Jetson) y sin GPU (Raspberry Pi 5), y las variantes de YOLO26n que se miden en cada una.
tags: [obc, jetson, raspberry-pi, tensorrt, ncnn]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: ul-tensorrt
    resource: https://docs.ultralytics.com/integrations/tensorrt/
  - id: ncnn
    resource: https://github.com/Tencent/ncnn
  - id: ul-ncnn
    resource: https://docs.ultralytics.com/integrations/ncnn/
  - id: ul-jetson
    resource: https://docs.ultralytics.com/guides/nvidia-jetson/
  - id: ul-rpi
    resource: https://docs.ultralytics.com/guides/raspberry-pi/
---

| | NVIDIA Jetson (con GPU) | Raspberry Pi 5 (sin GPU de cómputo) |
|---|---|---|
| Procesador | SoC ARM64 con GPU integrada CUDA; modelo exacto a registrar por el equipo | SoC ARM64, CPU de 4 núcleos Cortex-A76 |
| Memoria | Compartida entre CPU y GPU | RAM del sistema |
| Referencia | PyTorch FP32 sobre CUDA | PyTorch FP32 sobre CPU |
| Optimizado | TensorRT FP16[^ul-tensorrt], motor construido en la propia placa | NCNN[^ncnn][^ul-ncnn], 4 hilos, Vulkan desactivado |
| Telemetría | `tegrastats`, temperaturas, frecuencias | `vcgencmd get_throttled`, temperaturas, frecuencias |
| Guía de referencia | Ultralytics para Jetson[^ul-jetson] | Ultralytics para Raspberry Pi[^ul-rpi] |

Tabla: Configuraciones que se medirán. La comparación principal es original frente a optimizado dentro de cada placa; entre placas se comparan soluciones completas, con hardware, motor y precisión numérica diferentes.

[^ul-tensorrt]: Ultralytics, exportación TensorRT.
[^ncnn]: Tencent, ncnn.
[^ul-ncnn]: Ultralytics, exportación NCNN.
[^ul-jetson]: Ultralytics, guía para NVIDIA Jetson.
[^ul-rpi]: Ultralytics, guía para Raspberry Pi.
