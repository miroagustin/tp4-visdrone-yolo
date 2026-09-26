---
type: Contexto
title: Visión artificial embarcada en drones
description: Por qué la detección de objetos del TP4 debe ejecutarse a bordo del dron y qué restricciones impone la computadora de a bordo.
tags: [drones, obc, swap]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
---

Los vehículos aéreos no tripulados (VANT, o UAV por su sigla en inglés) se emplean en vigilancia, búsqueda y rescate, monitoreo de tránsito, inspección de infraestructura y agricultura. En muchas de estas misiones, la percepción visual debe resolverse *a bordo*. Transmitir el video a una estación terrena para procesarlo añade latencia, depende de la calidad del enlace, consume ancho de banda y deja al sistema sin percepción si el enlace se pierde.

En la arquitectura habitual, un controlador de vuelo se encarga de la estabilización y la navegación. Junto a él, una *computadora de a bordo* (OBC, *On-Board Computer* o *companion computer*) ejecuta las tareas de mayor carga, como la detección de objetos. Esa computadora está sujeta a las restricciones SWaP (*Size, Weight and Power*): cada gramo y cada vatio reducen la autonomía de vuelo, la disipación térmica es limitada y no se dispone de una GPU de escritorio.

En este trabajo se consideran dos familias representativas: placas con GPU integrada (NVIDIA Jetson) y placas solo con CPU (Raspberry Pi 5). Ver [plataformas](../obc/plataformas.md).
