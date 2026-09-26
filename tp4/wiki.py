"""Bundle Open Knowledge Format (v0.2) de la wiki del TP4: carga y controles de conformidad."""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

RESERVED = {"index.md", "log.md"}
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(.*)\Z", re.S)
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FOOTNOTE_REF = re.compile(r"\[\^([^\]]+)\](?!:)")
FOOTNOTE_DEF = re.compile(r"^\[\^([^\]]+)\]:", re.M)
INDEX_LINE = re.compile(r"^(#+ .+|\* \[[^\]]+\]\([^)]+\)( - .+)?)$")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)
TIME_KEYS ={"at", "last_modified", "stale_after", "from", "to"}


@dataclass
class Concept:
    path: Path
    rel: str  # ruta relativa al bundle, con "/" inicial
    meta: dict
    body: str


def wiki_root(root: Path) -> Path:
    return root / "wiki"


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    match = FRONTMATTER.match(text)
    if not match:
        return None, text
    return yaml.safe_load(match.group(1)) or {}, match.group(2)


def load_concept(bundle: Path, path: Path) -> Concept:
    meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    return Concept(path, "/" + path.relative_to(bundle).as_posix(), meta or {}, body)


def load_bundle(bundle: Path) -> dict[str, Concept]:
    return {c.rel: c for c in (load_concept(bundle, p) for p in sorted(bundle.rglob("*.md")) if p.name not in RESERVED)}


def resolve(bundle: Path, source: Path, target: str) -> Path | None:
    """Ruta local de un enlace; None si es externo o un ancla."""
    target = target.split("#", 1)[0]
    if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target):
        return None
    return (bundle / target[1:]) if target.startswith("/") else (source.parent / target)


def _times(value, path=""):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in TIME_KEYS:
                yield f"{path}{key}", item
            yield from _times(item, f"{path}{key}.")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from _times(item, f"{path}{i}.")


def check_bundle(bundle: Path) -> list[str]:
    """Conformidad OKF §11 más controles propios (enlaces, notas, estructura del informe)."""
    errors = []
    root_index = bundle / "index.md"
    if not root_index.exists():
        errors.append("falta index.md en la raíz")
    else:
        meta, _ = split_frontmatter(root_index.read_text(encoding="utf-8"))
        if not meta or str(meta.get("okf_version")) != "0.2":
            errors.append("index.md raíz: falta okf_version: \"0.2\"")
    for path in sorted(bundle.rglob("*.md")):
        rel = path.relative_to(bundle).as_posix()
        text = path.read_text(encoding="utf-8")
        try:
            meta, body = split_frontmatter(text)
        except yaml.YAMLError as exc:
            errors.append(f"{rel}: frontmatter ilegible ({exc})")
            continue
        if path.name == "index.md":
            for line in body.splitlines():
                if line.strip() and not INDEX_LINE.match(line.strip()):
                    errors.append(f"{rel}: línea no válida en índice: {line.strip()[:60]}")
        elif path.name != "log.md":
            if meta is None:
                errors.append(f"{rel}: sin frontmatter YAML")
                continue
            if not isinstance(meta.get("type"), str) or not meta["type"].strip():
                errors.append(f"{rel}: falta type")
        for key, value in _times(meta or {}):
            if isinstance(value, str):
                try:
                    value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"{rel}: {key} no es ISO 8601")
                    continue
            if not isinstance(value, dt.datetime) or value.tzinfo is None:
                errors.append(f"{rel}: {key} necesita fecha, hora y zona horaria explícita")
        body = CODE.sub("", body)
        for target in LINK.findall(body):
            local = resolve(bundle, path, target)
            if local is not None and not local.exists():
                errors.append(f"{rel}: enlace roto {target}")
        defined = {k.lower() for k in FOOTNOTE_DEF.findall(body)}
        for key in FOOTNOTE_REF.findall(body):
            if key.lower() not in defined:
                errors.append(f"{rel}: nota [^{key}] sin definición")
    if not any("frontmatter" in e for e in errors):
        errors += _check_report(bundle)
    return errors


def bibliography(bundle: Path, report: dict) -> list[dict]:
    return load_concept(bundle, bundle / report["bibliografia"].lstrip("/")).meta.get("referencias", [])


def report_concepts(report: dict) -> list[str]:
    paths = [report[k] for k in ("resumen", "sintesis", "bibliografia")]
    for group in report.get("secciones", []) + report.get("anexos", []):
        paths += group["conceptos"]
    return paths


def _check_report(bundle: Path) -> list[str]:
    report_path = bundle / "informe" / "informe-avance.md"
    if not report_path.exists():
        return ["falta informe/informe-avance.md"]
    report = load_concept(bundle, report_path).meta
    missing = [p for p in report_concepts(report) if not (bundle / p.lstrip("/")).exists()]
    errors = [f"informe: concepto inexistente {p}" for p in missing]
    if missing:
        return errors
    ids = {entry["id"].lower() for entry in bibliography(bundle, report)}
    for rel in report_concepts(report):
        concept = load_concept(bundle, bundle / rel.lstrip("/"))
        for source in concept.meta.get("sources", []) or []:
            if "resource" not in source:
                errors.append(f"{rel}: una entrada de sources no tiene resource")
        cited = {k.lower() for k in FOOTNOTE_REF.findall(CODE.sub("", concept.body))}
        own = {str(s.get("id", "")).lower() for s in concept.meta.get("sources", []) or []}
        for key in cited - ids - own:
            errors.append(f"{rel}: [^{key}] no está en la bibliografía ni en sources")
    return errors
