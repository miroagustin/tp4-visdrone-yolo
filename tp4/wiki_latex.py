"""Genera el informe PDF (estilo UNLaM) a partir de la wiki OKF.

Convenciones de markdown que entiende el conversor (ver wiki/guia-edicion.md):
- una tabla seguida de un párrafo "Tabla: ..." toma ese párrafo como título;
- una imagen sola en un párrafo es una figura; su título "ancho=0.8" o "escala=1" fija el tamaño;
- un blockquote que empieza con **Título** es un recuadro;
- una nota [^id] cuyo id está en la bibliografía se vuelve cita numerada.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import mistune

from .wiki import load_concept, bibliography, check_bundle

PARSE = mistune.create_markdown(renderer=None, plugins=["table", "footnotes", "math", "strikethrough"])
LEVELS = ("section", "subsection", "subsubsection", "paragraph", "subparagraph")
SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
UNICODE = {"≈": r"$\approx$", "→": r"$\rightarrow$", "←": r"$\leftarrow$", "Δ": r"$\Delta$", "≥": r"$\geq$",
           "≤": r"$\leq$", "θ": r"$\theta$", "−": r"$-$", "±": r"$\pm$"}
ESCAPE = re.compile("|".join(re.escape(k) for k in [*SPECIAL, *UNICODE]))


def escape(text: str) -> str:
    text = ESCAPE.sub(lambda m: SPECIAL.get(m.group(), UNICODE.get(m.group())), text)
    return re.sub(r"(\d) \\%", r"\1\\,\\%", text)


def plain(tokens) -> str:
    return "".join(t.get("raw", "") if "children" not in t else plain(t["children"]) for t in tokens)


class Renderer:
    def __init__(self, bundle: Path, bib_ids, figures: Path | None = None):
        self.bundle = bundle
        self.bib_ids = {i.lower(): i for i in bib_ids}
        self.figures = figures
        self.cites: list[str] = []
        self.notes: dict[str, list] = {}
        self.source: Path = bundle
        self.in_caption = False

    # ------------------------------------------------------------------ bloques
    def concept(self, concept, level: int, boxed=False) -> str:
        self.source = concept.path
        tokens = PARSE(concept.body)
        self.notes = {t["attrs"]["key"].lower(): t["children"] for f in tokens if f["type"] == "footnotes" for t in f["children"]}
        return self.blocks(tokens, level, boxed)

    def blocks(self, tokens, level: int, boxed=False) -> str:
        out, i = [], 0
        tokens = [t for t in tokens if t["type"] not in ("blank_line", "footnotes")]
        while i < len(tokens):
            tok = tokens[i]
            if tok["type"] == "table":
                caption = None
                nxt = tokens[i + 1] if i + 1 < len(tokens) else None
                if nxt and nxt["type"] == "paragraph" and plain(nxt["children"]).startswith("Tabla:"):
                    caption = self.caption(nxt["children"]).split(":", 1)[1].strip()
                    i += 1
                out.append(self.table(tok, caption, boxed))
            else:
                out.append(self.block(tok, level, boxed))
            i += 1
        return "\n".join(x for x in out if x)

    def block(self, tok, level: int, boxed=False) -> str:
        kind = tok["type"]
        if kind == "heading":
            cmd = LEVELS[min(level + tok["attrs"]["level"] - 1, len(LEVELS) - 1)]
            return f"\\{cmd}{{{self.inline(tok['children'])}}}\n"
        if kind == "paragraph":
            children = [c for c in tok["children"] if not (c["type"] == "text" and not c["raw"].strip())]
            if len(children) == 1 and children[0]["type"] == "image":
                return self.figure(children[0])
            return self.inline(tok["children"]) + "\n"
        if kind == "block_text":
            return self.inline(tok["children"])
        if kind == "list":
            env = "enumerate" if tok["attrs"].get("ordered") else "itemize"
            items = "\n".join(f"  \\item {self.blocks(item['children'], level, boxed).strip()}" for item in tok["children"])
            return f"\\begin{{{env}}}\n{items}\n\\end{{{env}}}\n"
        if kind == "block_quote":
            return self.box(tok, level)
        if kind == "block_math":
            return f"\\begin{{equation}}\n{tok['raw'].strip()}\n\\end{{equation}}\n"
        if kind == "block_code":
            return f"\\begin{{verbatim}}\n{tok['raw'].rstrip()}\n\\end{{verbatim}}\n"
        return ""

    def box(self, tok, level: int) -> str:
        children = [c for c in tok["children"] if c["type"] != "blank_line"]
        first = children[0] if children else None
        if first and first["type"] == "paragraph" and first["children"][0]["type"] == "strong":
            title = self.inline(first["children"][0]["children"])
            rest = first["children"][1:]
            while rest and rest[0]["type"] in ("softbreak", "linebreak") or (rest and rest[0]["type"] == "text" and not rest[0]["raw"].strip()):
                rest = rest[1:]
            body = (self.inline(rest) + "\n" if rest else "") + self.blocks(children[1:], level, boxed=True)
            return f"\\begin{{recuadro}}{{{title}}}\n\\small\n{body}\\end{{recuadro}}\n"
        return f"\\begin{{quote}}\n{self.blocks(children, level, boxed=True)}\\end{{quote}}\n"

    def table(self, tok, caption, boxed) -> str:
        head = tok["children"][0]["children"]
        rows = [r["children"] for r in tok["children"][1]["children"]] if len(tok["children"]) > 1 else []
        specs, wide = [], False
        for j, cell in enumerate(head):
            align = cell["attrs"].get("align")
            longest = max(len(plain(r[j].get("children", []))) for r in [head] + rows) if rows else 0
            if align == "right":
                specs.append("r")
            elif align == "center":
                specs.append("c")
            elif longest > 34:
                specs.append("L")
                wide = True
            else:
                specs.append("l")
        spec = "@{}" + "".join(specs) + "@{}"
        header = [self.inline(c.get("children", [])) for c in head]
        lines = [] if boxed and not any(header) else [" & ".join(f"\\textbf{{{h}}}" for h in header) + r" \\", r"\midrule"]
        lines += [" & ".join(self.inline(c.get("children", [])) for c in r) + r" \\" for r in rows]
        env = ("tabularx", "{\\linewidth}") if wide else ("tabular", "")
        tabular = f"\\begin{{{env[0]}}}{env[1]}{{{spec}}}\n\\toprule\n" + "\n".join(lines) + f"\n\\bottomrule\n\\end{{{env[0]}}}"
        if boxed:
            return tabular.replace("\\toprule\n", "").replace("\n\\bottomrule", "").replace("\\midrule", "\\addlinespace[2pt]") + "\n"
        if not wide:  # sin columnas flexibles: si no entra, se reduce al ancho de línea
            tabular = f"\\begin{{adjustbox}}{{max width=\\linewidth}}\n{tabular}\n\\end{{adjustbox}}"
        cap = f"\n\\caption{{{caption}}}" if caption else ""
        return f"\\begin{{table}}[H]\n\\centering\\small\n{tabular}{cap}\n\\end{{table}}\n"

    def figure(self, tok) -> str:
        url, title = tok["attrs"]["url"], tok["attrs"].get("title") or ""
        options = dict(part.split("=", 1) for part in title.split() if "=" in part)
        source = (self.source.parent / url).resolve()
        name = source.name
        if self.figures is not None:
            vector = self.figures / f"{source.stem}.pdf"
            name = vector.name if (source.with_suffix(".tex").exists() and vector.exists()) else name
        size = f"scale={options['escala']}" if "escala" in options else f"width={options.get('ancho', '1')}\\textwidth"
        pos = options.get("pos", "H")
        return (f"\\begin{{figure}}[{pos}]\n\\centering\n\\includegraphics[{size}]{{figuras/{name}}}\n"
                f"\\caption{{{self.caption(tok['children'])}}}\n\\end{{figure}}\n")

    # ------------------------------------------------------------------ en línea
    def caption(self, tokens) -> str:
        """En títulos de tablas y figuras, las notas que no son citas van entre paréntesis."""
        self.in_caption = True
        try:
            return self.inline(tokens)
        finally:
            self.in_caption = False

    def inline(self, tokens) -> str:
        return "".join(self.span(t) for t in tokens)

    def span(self, tok) -> str:
        kind = tok["type"]
        if kind == "text":
            return escape(tok["raw"])
        if kind == "strong":
            return f"\\textbf{{{self.inline(tok['children'])}}}"
        if kind == "emphasis":
            return f"\\emph{{{self.inline(tok['children'])}}}"
        if kind == "codespan":
            return f"\\texttt{{{escape(tok['raw']).replace('--', '-{}-')}}}"
        if kind == "inline_math":
            return f"${tok['raw']}$"
        if kind in ("softbreak",):
            return " "
        if kind == "linebreak":
            return "\\\\\n"
        if kind == "link":
            text = self.inline(tok["children"])
            url = tok["attrs"]["url"]
            return f"\\href{{{url}}}{{{text}}}" if re.match(r"^https?://", url) else text
        if kind == "footnote_ref":
            key = tok["raw"].lower()
            if key in self.bib_ids:
                if key not in self.cites:
                    self.cites.append(key)
                return f"~\\cite{{{key}}}"
            note = self.notes.get(key, [])
            if self.in_caption:
                return f" ({self.blocks(note, 4, boxed=True).strip().rstrip('.')})"
            return f"\\footnote{{{self.blocks(note, 4, boxed=True).strip()}}}"
        if kind == "strikethrough":
            return self.inline(tok["children"])
        return self.inline(tok.get("children", [])) if "children" in tok else escape(tok.get("raw", ""))


# ---------------------------------------------------------------------- ensamblado
def _cover_value(text) -> str:
    text = str(text)
    return f"\\pendiente{{{escape(text)}}}" if text.startswith("[") else escape(text)


def _concept(bundle: Path, rel: str):
    return load_concept(bundle, bundle / rel.lstrip("/"))


def build_tex(bundle: Path, figures: Path | None = None) -> str:
    """Devuelve el .tex completo del informe descrito en informe/informe-avance.md."""
    from jinja2 import Environment, FileSystemLoader
    report = _concept(bundle, "/informe/informe-avance.md").meta
    refs = bibliography(bundle, report)
    r = Renderer(bundle, [e["id"] for e in refs], figures)

    def section_block(group, numbered=True):
        concepts = [_concept(bundle, p) for p in group["conceptos"]]
        star = "" if numbered else "*"
        parts = [f"\\needspace{{10\\baselineskip}}\n\\section{star}{{{escape(group['titulo'])}}}\n"]
        if len(concepts) == 1 and not group.get("subtitulos", False):
            parts.append(r.concept(concepts[0], 1))
        else:
            for c in concepts:
                parts.append(f"\\subsection{{{escape(c.meta.get('title', c.rel))}}}\n" + r.concept(c, 2))
        return "\n".join(parts)

    resumen = r.concept(_concept(bundle, report["resumen"]), 2)
    synthesis = _concept(bundle, report["sintesis"])
    sintesis = (f"\\begin{{recuadro}}{{{escape(synthesis.meta.get('title', ''))}}}\n\\small\n"
                + r.concept(synthesis, 2, boxed=True) + "\\end{recuadro}\n")
    body = "\n".join(section_block(g) for g in report["secciones"])
    anexos = "\n".join(section_block(g) for g in report.get("anexos", []))
    by_id = {e["id"].lower(): e for e in refs}
    bib = []
    for key in r.cites:
        entry = by_id[key]
        text = r.inline(PARSE(entry["texto"])[0]["children"])
        if entry.get("url"):
            text += f" [En línea]. Disponible: \\url{{{entry['url']}}}"
        bib.append(f"\\bibitem{{{key}}} {text}")
    env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"), block_start_string="((*", block_end_string="*))",
                      variable_start_string="(((", variable_end_string=")))", comment_start_string="((=", comment_end_string="=))",
                      keep_trailing_newline=True)
    cover = {k: _cover_value(v) for k, v in report.items() if isinstance(v, (str, int))}
    cover["integrantes"] = [{k: _cover_value(v) for k, v in m.items()} for m in report.get("integrantes", [])]
    cover["palabras_clave"] = escape(", ".join(report.get("palabras_clave", [])))
    return env.get_template("informe_unlam.tex").render(p=cover, resumen=resumen, sintesis=sintesis, cuerpo=body,
                                                         bibliografia="\n".join(bib), anexos=anexos)


def _pdflatex(tex: Path, runs: int = 1) -> None:
    for _ in range(runs):
        done = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name], cwd=tex.parent,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        if done.returncode:
            log = tex.with_suffix(".log")
            tail = log.read_text(encoding="utf-8", errors="replace")[-3000:] if log.exists() else done.stdout[-3000:]
            raise RuntimeError(f"pdflatex falló con {tex.name}:\n{tail}")


def build_report(root: Path, *, compile_pdf=True, refresh_pngs=False) -> Path:
    """Compila diagramas TikZ y el informe. Devuelve el PDF (o el .tex con compile_pdf=False)."""
    bundle = root / "wiki"
    build = root / "informe" / "build"
    figures = build / "figuras"
    figures.mkdir(parents=True, exist_ok=True)
    for diagram in sorted((bundle / "figuras").glob("*.tex")) if compile_pdf else []:
        shutil.copy2(diagram, figures / diagram.name)
        _pdflatex(figures / diagram.name)
        if refresh_pngs:
            subprocess.run(["pdftoppm", "-r", "220", "-png", "-singlefile", str(figures / f"{diagram.stem}.pdf"),
                            str(bundle / "figuras" / diagram.stem)], check=True, capture_output=True)
    errors = check_bundle(bundle)
    if errors:
        raise ValueError("La wiki no pasa los controles:\n" + "\n".join(errors))
    for asset in (bundle / "figuras").iterdir():
        if asset.suffix.lower() in (".png", ".jpg", ".jpeg"):
            shutil.copy2(asset, figures / asset.name)
    tex = build / "informe_tp4.tex"
    tex.write_text(build_tex(bundle, figures if compile_pdf else None), encoding="utf-8")
    if not compile_pdf:
        return tex
    _pdflatex(tex, runs=3)
    pdf = root / "informe" / "informe_tp4.pdf"
    shutil.copy2(tex.with_suffix(".pdf"), pdf)
    return pdf
