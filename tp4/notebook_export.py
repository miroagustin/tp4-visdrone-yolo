"""HTML autónomo del recorrido PRESENTACIÓN; su fuente es el notebook."""
import copy
import html
from pathlib import Path

import mistune
import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager


def export(root: Path, run=None, output=None):
    root = Path(root).resolve()
    source = nbformat.read(root / "notebooks" / "01_visdrone_yolo.ipynb", as_version=4)
    selected = copy.deepcopy(source)
    selected.cells = [c for c in selected.cells if "presentation" in c.metadata.get("tags", [])]
    for cell in selected.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
            if run and "RUN_ID = None" in cell.source:
                cell.source = cell.source.replace("RUN_ID = None", f"RUN_ID = {str(Path(run).resolve())!r}", 1)
    kernels = KernelSpecManager().find_kernel_specs()
    kernel = "tp4-visdrone-yolo" if "tp4-visdrone-yolo" in kernels else "python3"
    NotebookClient(selected, timeout=120, kernel_name=kernel).execute(cwd=str(root))
    markdown = mistune.create_markdown(escape=False, plugins=["table"])
    sections = []
    for cell in selected.cells:
        if cell.cell_type == "markdown":
            sections.append(markdown(cell.source))
        else:
            for item in cell.outputs:
                data = item.get("data", {})
                if "image/png" in data:
                    rendered = f'<img alt="Figura del experimento" src="data:image/png;base64,{data["image/png"]}">'
                elif "text/markdown" in data:
                    rendered = markdown(data["text/markdown"])
                elif "text/html" in data:
                    rendered = data["text/html"]
                elif item.output_type == "stream":
                    rendered = f'<pre>{html.escape(item.text)}</pre>'
                else:
                    rendered = f'<pre>{html.escape(data.get("text/plain", ""))}</pre>'
                sections[-1] += rendered
    total = len(sections)
    slides = "".join(f'<section id="s{i}">{body}<footer>{i} / {total}</footer></section>' for i, body in enumerate(sections, 1))
    page = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TP4 · VisDrone y YOLO11n · Presentación académica</title>
<style>
*{box-sizing:border-box}html{scroll-snap-type:y proximity}body{margin:0;background:#101c2d;color:#edf2f8;font-family:Arial,sans-serif}
section{min-height:100vh;position:relative;padding:3.5vh 6vw 5vh;scroll-snap-align:start;display:flex;flex-direction:column;justify-content:center;gap:.15rem}
h1{font-size:clamp(32px,3.3vw,56px);line-height:1.13}h2{font-size:clamp(25px,2.25vw,39px);color:#87d9ef;line-height:1.15}h3{font-size:1.7vw}
p,li{font-size:clamp(15px,1.35vw,24px);line-height:1.4;margin:.45em 0}table{border-collapse:collapse;width:100%;font-size:clamp(13px,1.18vw,21px);margin:.65em 0}td,th{padding:.43em .6em;text-align:left;border-bottom:1px solid #3b526b}th{color:#87d9ef}img{max-width:100%;max-height:43vh;object-fit:contain;align-self:center}a{color:#9adeef}code{color:#ffc878;font-size:.9em}pre{white-space:pre-wrap}footer{position:absolute;right:2vw;bottom:1vh;color:#a6bbcf;font-size:14px}em{color:#c6d4e4;font-size:.9em}
@media(max-width:800px){section{padding:20px 22px 42px}h3{font-size:20px}table{font-size:13px}img{max-height:40vh}}
@media print{section{break-after:page;min-height:95vh}body{background:white;color:black}h2,th,a{color:#173858}}
</style></head><body>""" + slides + """<script>
const slides=[...document.querySelectorAll('section')];document.addEventListener('keydown',e=>{let d=['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)?1:['ArrowLeft','ArrowUp','PageUp'].includes(e.key)?-1:0;if(!d)return;e.preventDefault();let i=slides.reduce((best,s,j)=>Math.abs(s.getBoundingClientRect().top)<Math.abs(slides[best].getBoundingClientRect().top)?j:best,0);slides[Math.max(0,Math.min(slides.length-1,i+d))].scrollIntoView();});
</script></body></html>"""
    destination = Path(output) if output else root / "presentacion.html"
    destination.write_text(page, encoding="utf-8")
    return destination
