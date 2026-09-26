from pathlib import Path

from tp4.wiki import check_bundle, load_concept, report_concepts
from tp4.wiki_latex import PARSE, Renderer, build_tex, escape

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "wiki"


def test_real_bundle_is_okf_conformant():
    assert check_bundle(BUNDLE) == []


def test_report_outline_covers_existing_concepts():
    report = load_concept(BUNDLE, BUNDLE / "informe" / "informe-avance.md").meta
    paths = report_concepts(report)
    assert paths and all((BUNDLE / p.lstrip("/")).exists() for p in paths)


def write(folder: Path, name: str, text: str) -> Path:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_check_detects_okf_violations(tmp_path):
    write(tmp_path, "index.md", "# Sin versión\n\ntexto suelto\n")
    write(tmp_path, "a.md", "sin frontmatter\n")
    write(tmp_path, "b.md", "---\ntitle: sin type\ngenerated: { by: x, at: 2026-09-26T10:00:00 }\n---\n[roto](nada.md) y nota[^n]\n")
    errors = "\n".join(check_bundle(tmp_path))
    for expected in ("okf_version", "línea no válida", "a.md: sin frontmatter", "b.md: falta type",
                     "zona horaria", "enlace roto nada.md", "[^n] sin definición"):
        assert expected in errors


def render(folder: Path, body: str, bib=("visdrone",)):
    concept_file = write(folder, "c.md", body)
    r = Renderer(folder, bib)
    r.source = concept_file
    tokens = PARSE(body)
    r.notes = {t["attrs"]["key"].lower(): t["children"] for f in tokens if f["type"] == "footnotes" for t in f["children"]}
    return r.blocks(tokens, 2), r


def test_escape_and_units():
    assert escape("50 % de a_b & c#") == r"50\,\% de a\_b \& c\#"
    assert escape("Δ ≈ θ") == r"$\Delta$ $\approx$ $\theta$"


def test_table_with_caption_and_alignment(tmp_path):
    tex, _ = render(tmp_path, "| Clase | AP |\n|---|---:|\n| car | 47 % |\n\nTabla: AP por clase.\n")
    assert r"\begin{tabular}{@{}lr@{}}" in tex and r"\caption{AP por clase.}" in tex and "Tabla:" not in tex


def test_figure_box_math_and_citations(tmp_path):
    body = ("Dato[^visdrone] y nota[^local].\n\n![Título](x.png \"ancho=0.8\")\n\n"
            "> **Recuadro**\n> texto\n\n$$\nW = 2h\n$$\n\n[^visdrone]: VisDrone.\n[^local]: Aclaración.\n")
    tex, r = render(tmp_path, body)
    assert r"~\cite{visdrone}" in tex and r"\footnote{Aclaración.}" in tex and r.cites == ["visdrone"]
    assert r"\includegraphics[width=0.8\textwidth]{figuras/x.png}" in tex
    assert r"\begin{recuadro}{Recuadro}" in tex and "\\begin{equation}\nW = 2h\n\\end{equation}" in tex


def test_build_tex_contains_every_section():
    tex = build_tex(BUNDLE)
    report = load_concept(BUNDLE, BUNDLE / "informe" / "informe-avance.md").meta
    for group in report["secciones"]:
        assert escape(group["titulo"]) in tex
    assert r"\bibitem{visdrone}" in tex and "((" not in tex
