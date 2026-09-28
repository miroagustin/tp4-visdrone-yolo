---
type: Resultado
title: Evaluación de detección por pasada en video
description: En las secuencias limpias de VisDrone-VID, a 5 FPS y con confianza 0,25, las personas detectadas al menos una vez pasan de 74 % (640 px) a 84 % (1280 px) y a 88–89 % combinando mosaicos con más resolución; los vehículos de la secuencia 4K siguen lejos del 85 %.
resource: ../../runs/full/20260925T231501Z/mission_eval/video_val.json
tags: [resultados, video, recall-por-objeto, mision]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-28T02:30:00Z }
sources:
  - id: video
    resource: ../../runs/full/20260925T231501Z/mission_eval/video_val.json
    title: Resultados por variante, FPS simulado y umbral
  - id: codigo
    resource: ../../tp4/video.py
    title: Evaluador de detección por objeto
---

Esta evaluación corresponde al modelo de **línea base**: YOLO26n entrenado a 640 px con las diez clases de VisDrone. Los resultados del modelo reentrenado con persona y vehículo a 1280 px están en el [reentrenamiento](reentrenamiento-1280.md).

# Método

Se procesaron los 2846 cuadros de las siete secuencias de validación de [VisDrone-VID](../datos/visdrone-vid.md) con el mismo `best.pt` de YOLO26n, sin reentrenar, en tres variantes de la [evaluación de resolución](evaluacion-resolucion.md): imagen completa a 640 px, a 1280 px y mosaicos nativos[^codigo]. Sobre esas predicciones se calculó la [detección por objeto](../metricas/recall-por-objeto.md) con las reglas del [objetivo por pasada](../mision/objetivo-deteccion-pasada.md):

- un objeto cuenta como detectado si en algún cuadro evaluado tiene una detección de su clase de la misión con IoU de al menos 0,5;
- para simular los FPS de una placa, se evalúa uno de cada k cuadros (30 FPS nominales: k = 1, 3, 6 y 15 equivalen a 30, 10, 5 y 2 FPS);
- las falsas alarmas excluyen las detecciones que caen dentro de regiones ignoradas.

Por la fuga con el entrenamiento de DET, las cifras principales usan solo las **tres secuencias limpias** (086, 117 y 268). Allí hay 187 personas y 89 vehículos (incluidas 10 bicicletas y motos).

# Detección al menos una vez

| Variante | FPS simulados | persona | vehículo |
|---|---:|---:|---:|
| 640 px | 30 | 80,0 % | 56,2 % |
| 640 px | 10 | 75,9 % | 55,1 % |
| 640 px | 5 | 74,3 % | 52,8 % |
| 640 px | 2 | 65,2 % | 52,8 % |
| 1280 px | 30 | 86,3 % | 64,0 % |
| 1280 px | 10 | 85,0 % | 64,0 % |
| 1280 px | 5 | 84,0 % | 64,0 % |
| 1280 px | 2 | 80,4 % | 62,9 % |
| Mosaicos | 30 | 89,5 % | 75,3 % |
| Mosaicos | 10 | 87,7 % | 73,0 % |
| Mosaicos | 5 | 87,2 % | 71,9 % |
| Mosaicos | 2 | 77,7 % | 65,2 % |

Tabla: Objetos detectados al menos una vez en las secuencias limpias, con confianza 0,25[^video].

| Variante | persona limpias / todas | vehículo limpias / todas |
|---|---:|---:|
| 640 px | 74,3 % / 79,2 % | 52,8 % / 81,2 % |
| 1280 px | 84,0 % / 87,5 % | 64,0 % / 86,5 % |
| Mosaicos | 87,2 % / 90,5 % | 71,9 % / 89,8 % |

Tabla: Efecto de la fuga a 5 FPS y confianza 0,25. "Todas" incluye las cuatro secuencias cuyo video aporta imágenes al entrenamiento de DET.

# Personas: umbral, confirmación y falsas alarmas

| Variante | Confianza | Detectada ≥ 1 | Detectada ≥ 3 | Recall por cuadro | Precisión por cuadro | Falsas alarmas por cuadro |
|---|---:|---:|---:|---:|---:|---:|
| 640 px | 0,1 | 83,4 % | 74,3 % | 61,7 % | 35,4 % | 21,4 |
| 640 px | 0,25 | 74,3 % | 59,9 % | 47,9 % | 64,4 % | 5,0 |
| 640 px | 0,4 | 56,7 % | 42,2 % | 34,2 % | 81,7 % | 1,5 |
| 1280 px | 0,1 | 90,9 % | 81,8 % | 67,8 % | 36,6 % | 22,3 |
| 1280 px | 0,25 | 84,0 % | 72,2 % | 55,9 % | 60,3 % | 7,0 |
| 1280 px | 0,4 | 73,3 % | 63,1 % | 45,9 % | 74,8 % | 2,9 |
| Mosaicos | 0,1 | 92,5 % | 84,5 % | 68,1 % | 30,4 % | 29,7 |
| Mosaicos | 0,25 | 87,2 % | 72,7 % | 57,3 % | 55,1 % | 8,9 |
| Mosaicos | 0,4 | 76,5 % | 62,0 % | 45,8 % | 70,5 % | 3,6 |

Tabla: Personas en las secuencias limpias a 5 FPS simulados.

| Variante | < 4 px | 4–8 px | 8–16 px | 16–32 px | ≥ 32 px |
|---|---:|---:|---:|---:|---:|
| 640 px | 0,0 % | 10,0 % | 74,3 % | 90,4 % | 100,0 % |
| 1280 px | 0,0 % | 35,0 % | 86,5 % | 95,9 % | 100,0 % |
| Mosaicos | 75,0 % | 65,0 % | 86,5 % | 91,8 % | 100,0 % |

Tabla: Personas detectadas al menos una vez según su tamaño máximo en la pasada, referido a 640 px (4, 20, 74, 73 y 16 personas por columna), a 5 FPS y confianza 0,25.

# Combinaciones de mosaicos y resolución

Se probaron dos combinaciones: **mosaicos + 1280 px** (mosaicos nativos con la pasada completa a 1280 px) y **mosaicos reducidos** (pasada completa a 640 px y mosaicos sobre la imagen reducida a 1920 o 2560 px de lado mayor, solo si es más grande). Reducir antes de cortar baja el costo en los videos grandes: en 4K, 9 o 16 inferencias por cuadro en lugar de 33.

| Variante | Inferencias por cuadro | ms por cuadro | Persona a 30 FPS | Persona / vehículo a 5 FPS | Persona / vehículo a 2 FPS | Falsas personas por cuadro |
|---|---:|---:|---:|---:|---:|---:|
| 640 px | 1,0 | 18 | 80,0 % | 74,3 % / 52,8 % | 65,2 % / 52,8 % | 5,0 |
| 1280 px | 1,0 | 19 | 86,3 % | 84,0 % / 64,0 % | 80,4 % / 62,9 % | 7,0 |
| Mosaicos reducidos a 1920 px | 8,5 | 71 | **92,6 %** | 88,2 % / 65,2 % | 81,5 % / 65,2 % | 9,1 |
| Mosaicos reducidos a 2560 px | 13,7 | 112 | 91,6 % | 87,7 % / 66,3 % | 78,8 % / 65,2 % | 9,6 |
| Mosaicos nativos (640 px) | 23,5 | 131 | 89,5 % | 87,2 % / **71,9 %** | 77,7 % / 65,2 % | 8,9 |
| Mosaicos nativos + 1280 px | 23,5 | 148 | 91,6 % | **89,3 %** / **71,9 %** | **84,2 % / 66,3 %** | 8,9 |

Tabla: Objetos detectados al menos una vez en las secuencias limpias según la variante, con confianza 0,25. Inferencias y tiempos promediados por cuadro en esas secuencias (RTX 5070); falsas alarmas a 5 FPS.

- **Mosaicos reducidos a 1920 px es el mejor compromiso para personas:** 88 % a 5 FPS con 8,5 inferencias por cuadro, casi lo mismo que la combinación más cara (89 %) con un tercio del costo. Supera el 85 % a 5 FPS, que 1280 px sola no alcanza (84 %).
- **Mosaicos nativos + 1280 px es la más completa:** es la única que se sostiene a 2 FPS (84 % de personas) y, junto con los mosaicos nativos, la mejor en vehículos (72 %), pero con unas 24 inferencias por cuadro, y 33 en 4K.
- **Reducir la imagen antes de cortar sacrifica los vehículos chicos del 4K** (de 72 % a 65–66 %), que solo se recuperan cortando a resolución nativa.
- **Las falsas alarmas suben con cualquier combinación**, a unas 9 personas falsas por cuadro, frente a 7 con 1280 px.

# Lectura

- **El objetivo por pasada es alcanzable para personas.** A 5 FPS y confianza 0,25, las personas detectadas al menos una vez suben de 74 % (640 px) a 84 % (1280 px) y 87 % (mosaicos). A 10 FPS, 1280 px llega a 85 %. Con 640 px el objetivo no se alcanza en ningún escenario limpio.
- **La pasada multiplica las oportunidades.** El recall por cuadro de personas es 56–57 %, pero cada persona aparece en decenas de cuadros. La mediana del tiempo hasta la primera detección es 0 s: casi siempre se detectan en su primer cuadro evaluado. Bajar de 5 a 2 FPS cuesta entre 4 y 10 puntos.
- **Los vehículos pequeños en 4K no se alcanzan.** En la secuencia 4K (268), 29 de 46 vehículos no se detectan nunca a 1280 px, aunque son visibles durante 38 a 263 cuadros: miden entre 7 y 15 px referidos a 640. Los mosaicos nativos recuperan parte, y aun así vehículo queda en 72 %. Ese escenario pide volar más bajo o reentrenar con más resolución.
- **El costo son las falsas alarmas.** Con confianza 0,25 hay entre 5 y 9 falsas personas por cuadro en escenas densas, y la precisión por cuadro ronda el 55–64 %, similar a DET. Exigir 3 detecciones antes de confirmar un objeto baja la detección de personas a 72–73 % con 1280 px o mosaicos. Un tracker que confirme por persistencia debería filtrar la mayoría de esas falsas alarmas, que no se sostienen entre cuadros, pero eso no está medido.
- **La fuga infla los resultados**, sobre todo en vehículos: a 5 FPS con 640 px pasan de 53 % en limpias a 81 % con todas las secuencias. Las conclusiones se apoyan en las secuencias limpias.
- **Costo en la laptop:** unos 15–19 ms por cuadro a 640 px, 16–23 ms a 1280 px y 52–166 ms con mosaicos (hasta 33 inferencias por cuadro en 4K). El costo en la placa se mide en el [benchmark](../obc/benchmark.md).

[^codigo]: `tp4/video.py`; comando `python -m tp4.cli video runs/full/20260925T231501Z`.
[^video]: `mission_eval/video_val.json` de la ejecución YOLO26n.
