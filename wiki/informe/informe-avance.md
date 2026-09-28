---
type: Informe
title: Detección de personas y vehículos en imágenes aéreas para plataformas de drones
description: Estructura y carátula del informe de avance del TP4 que genera `python -m tp4.cli informe`.
tags: [informe, unlam]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-28T02:30:00Z }
version: 3
subtitulo: "Comparación YOLO11n / YOLO26n sobre VisDrone, reentrenamiento con las clases de la misión y plan de benchmark en computadoras de a bordo (OBC) con y sin GPU"
universidad: Universidad Nacional de La Matanza
departamento: Departamento de Ingeniería e Investigaciones Tecnológicas
materia: Visión Artificial
trabajo: Trabajo Práctico N.º 4
tipo_informe: Informe de avance
integrantes:
  - { nombre: "[Apellido, Nombre]", dni: "[00.000.000]" }
  - { nombre: "[Apellido, Nombre]", dni: "[00.000.000]" }
  - { nombre: "[Apellido, Nombre]", dni: "[00.000.000]" }
  - { nombre: "[Apellido, Nombre]", dni: "[00.000.000]" }
docentes: "[completar]"
destinatarios: "equipo del proyecto (coordinación, equipo Jetson, equipo Raspberry Pi 5)"
ciclo: "Ciclo lectivo 2026 · 2.º cuatrimestre"
lugar: San Justo, Buenos Aires
fecha: 28 de septiembre de 2026
palabras_clave: [detección de objetos, vehículos aéreos no tripulados, YOLO, VisDrone, computación embarcada, TensorRT, NCNN]
resumen: /informe/resumen.md
sintesis: /informe/sintesis.md
bibliografia: /referencias/bibliografia.md
secciones:
  - titulo: Introducción
    conceptos: [/proyecto/contexto-drones.md, /proyecto/problema.md, /proyecto/objetivos.md]
  - titulo: Datos
    conceptos: [/datos/visdrone-det.md, /datos/visdrone-vid.md]
  - titulo: Metodología de la comparación inicial
    conceptos: [/modelos/yolo11n.md, /modelos/yolo26n.md, /experimentos/protocolo-entrenamiento.md, /metricas/map.md]
  - titulo: Resultados de la comparación inicial
    conceptos: [/experimentos/comparacion-yolo11-yolo26.md]
  - titulo: Clases de la misión y evaluación agrupada
    conceptos: [/mision/clases.md, /experimentos/evaluacion-mision.md]
  - titulo: "Del laboratorio al dron: requisitos y objetivo"
    conceptos: [/mision/requisitos-operativos.md, /mision/objetivo-deteccion-pasada.md, /metricas/recall-por-objeto.md]
  - titulo: Mejoras de la inferencia
    conceptos: [/mejoras/resolucion-y-mosaicos.md, /experimentos/evaluacion-resolucion.md]
  - titulo: Detección por pasada en video
    conceptos: [/experimentos/evaluacion-video.md]
  - titulo: Reentrenamiento con las clases de la misión
    conceptos: [/experimentos/reentrenamiento-1280.md]
  - titulo: Benchmark en computadoras de a bordo
    conceptos: [/obc/plataformas.md, /obc/benchmark.md, /metricas/rendimiento-obc.md]
  - titulo: Plan de trabajo
    conceptos: [/plan/tareas.md, /plan/decisiones.md]
  - titulo: Limitaciones y riesgos
    conceptos: [/plan/riesgos.md]
  - titulo: Conclusiones
    conceptos: [/informe/conclusiones.md]
anexos:
  - titulo: "Anexo: trazabilidad de artefactos"
    conceptos: [/experimentos/trazabilidad.md]
---

Este concepto define el informe de avance: los campos del frontmatter arman la carátula y `secciones` fija el orden. Una sección con varios conceptos usa el título de cada uno como subsección; con uno solo, los títulos internos del concepto pasan a ser las subsecciones.

Para completar la carátula, editar `integrantes` y `docentes`; los valores entre corchetes se imprimen en gris como pendientes. Para regenerar el PDF, ver la [guía de edición](../guia-edicion.md).

La versión 1 del informe se escribió a mano y se conserva en `informe/informe_tp4_obc.pdf`.
