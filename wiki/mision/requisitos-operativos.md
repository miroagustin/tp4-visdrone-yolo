---
type: Requisito
title: Requisitos operativos
description: Traducción de las métricas a magnitudes de la misión, como el tamaño aparente de los objetos según la altura y la distancia recorrida entre detecciones según los FPS.
tags: [mision, gsd, fps, requisitos]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: sahi
    resource: /referencias/bibliografia.md
    title: SAHI
---

Las métricas de los experimentos se obtuvieron sobre imágenes fijas y en una GPU de laptop. Para acercarlas al problema real conviene traducirlas a magnitudes de la misión: altura de vuelo, campo visual de la cámara, velocidad y cuadros por segundo.

# Tamaño aparente de los objetos

Para una cámara con campo de visión horizontal $\theta$, a una altura $h$ y con apunte cenital, el ancho cubierto en el terreno y la resolución espacial (GSD, *Ground Sample Distance*) son:

$$
W = 2\,h\,\tan\!\left(\tfrac{\theta}{2}\right), \qquad \mathrm{GSD} = \frac{W}{N}, \qquad n_{\text{px}} = \frac{L}{\mathrm{GSD}}
$$

donde $N$ es el ancho en píxeles de la imagen que procesa la red y $L$ el tamaño real del objeto.

> **Ejemplo ilustrativo (supuestos: h = 50 m, θ = 80°, toma cenital)**
> $W = 2 \cdot 50 \cdot \tan 40^\circ \approx 83{,}9$ m. Con la imagen nativa ($N = 1400$ px), el GSD es de unos 6,0 cm/px; con la entrada de la red ($N = 640$ px), de unos 13,1 cm/px. Una persona vista desde arriba ($L \approx 0{,}5$ m) pasa de ocupar unos **8 px** a unos **4 px**, y un auto ($L \approx 4{,}5$ m) pasa de unos 75 px a unos 34 px. Esto explica por qué *car* alcanza un AP alto mientras *people* y *bicycle* quedan muy por debajo: al reducir la imagen a 640 px, las personas quedan en el límite de lo que la red puede resolver.

La [evaluación por clases de la misión](../experimentos/evaluacion-mision.md) confirma el ejemplo con datos: el recall de personas pasa de 11,8 % entre 4 y 8 px a 61,9 % entre 16 y 32 px. De aquí surgen dos palancas que deben evaluarse *en la placa*, porque ambas aumentan el costo de cómputo: aumentar la resolución de entrada y procesar la imagen por mosaicos, como propone SAHI[^sahi] (ver [mejoras de inferencia](../mejoras/resolucion-y-mosaicos.md)). Además, la altura de vuelo es una palanca de la misión: volar más bajo agranda a las personas en la imagen.

# Frecuencia de procesamiento

Si el dron avanza a velocidad $v$ y la placa procesa $f$ cuadros por segundo, entre dos detecciones consecutivas el dron recorre

$$
\Delta d = \frac{v}{f}
$$

Por ejemplo, a $v = 10$ m/s, procesar 2 FPS implica 5 m entre detecciones, 5 FPS implica 2 m y 15 FPS implica unos 0,7 m. El umbral aceptable depende de la misión. Un conteo de personas en una zona casi estática tolera pocos FPS; el seguimiento de vehículos en movimiento o la evasión requieren muchos más y una latencia baja y estable. Por eso el benchmark informa, además de la media, los percentiles p50 y p95 de latencia: en control, el peor caso importa tanto como el promedio.

Los FPS también determinan cuántas oportunidades tiene el detector de ver a cada objeto durante la pasada, y por lo tanto el [objetivo de detección por pasada](objetivo-deteccion-pasada.md).

[^sahi]: F. C. Akyon *et al.*, Slicing Aided Hyper Inference, ICIP 2022.
