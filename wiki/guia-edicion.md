---
type: Guía
title: Cómo editar la wiki y regenerar el informe
description: Convenciones del bundle OKF del TP4 y del conversor que genera el informe PDF.
tags: [wiki, informe, okf]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T18:30:00Z }
sources:
  - id: okf
    resource: https://github.com/GoogleCloudPlatform/open-knowledge-format
    title: Open Knowledge Format v0.2
---

# Qué es esta carpeta

La wiki sigue el formato Open Knowledge Format v0.2[^okf]. Cada archivo `.md` es un **concepto**: un bloque YAML inicial (frontmatter) y un cuerpo en markdown. `index.md` y `log.md` son nombres reservados: los índices listan conceptos y el historial registra los cambios, del más reciente al más antiguo.

La wiki es la **única fuente** del informe: no se edita el `.tex` generado.

# Frontmatter

- `type` es obligatorio. Los demás campos usados son `title`, `description`, `tags`, `status` (`draft`, `stable` o `deprecated`), `generated` y `sources`.
- Las fechas y horas llevan zona horaria: `2026-09-26T18:30:00Z`.
- `verified` se agrega **solo** cuando alguien del equipo revisa el concepto: `verified: { by: human:<usuario>, at: <fecha> }`.
- Las afirmaciones con fuente usan notas al pie cuya clave coincide con un `sources[].id`, por ejemplo `[^visdrone]`. Si la clave está en la [bibliografía](referencias/bibliografia.md), el informe la convierte en una cita numerada.

# Markdown que entiende el conversor

- **Tablas:** un párrafo inmediatamente después de la tabla que empieza con `Tabla:` es su título. Las columnas alineadas a la derecha (`---:`) quedan alineadas a la derecha.
- **Figuras:** una imagen sola en un párrafo, `![Título](../figuras/x.png "ancho=0.8")`. Si existe `figuras/x.tex` (diagrama TikZ), el informe usa su versión vectorial.
- **Recuadros:** un bloque de cita cuya primera línea está en negrita, `> **Título**`. Dentro de un recuadro va texto, listas o fórmulas, no tablas.
- **Fórmulas:** `$...$` en línea y `$$...$$` en bloque.
- **Referencias cruzadas:** se enlazan otros conceptos con rutas relativas; en el PDF queda solo el texto. No usar números de sección o tabla en la prosa: cambian al reordenar.

# Regenerar el informe

Desde `tp4-yolo/`:

```
.venv/Scripts/python.exe -m tp4.cli wiki check
.venv/Scripts/python.exe -m tp4.cli informe
```

`informe` controla la wiki, compila los diagramas y genera `informe/informe_tp4.pdf` con pdflatex (MiKTeX o TeX Live). `--solo-tex` deja solo `informe/build/informe_tp4.tex` para quien no tenga LaTeX; `--figuras` además regenera los PNG de los diagramas que se ven en GitHub. La estructura del informe (orden de secciones y carátula) está en [informe-avance](informe/informe-avance.md).

[^okf]: Open Knowledge Format, especificación v0.2.
