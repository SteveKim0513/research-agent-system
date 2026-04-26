#!/usr/bin/env python3
"""
bibliography.py — 단순화 마이그레이션 Phase A.4.

analyzed/*.md frontmatter 스캔 → APA / MLA / Chicago / BibTeX 렌더.

이전 render_bibliography.py 단순화 (manifest 의존 제거).

CLI:
    python3 scripts/bibliography.py <project> [--format=apa|mla|chicago|bibtex]
                                              [--include-anchor-unused]
                                              [--include-non-cited]    # default: 인용된 것만
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import yaml


def papers_root(project_root: Path) -> Path:
    return project_root / "papers"


def analyzed_dir(project_root: Path) -> Path:
    return papers_root(project_root) / "analyzed"


def output_dir(project_root: Path) -> Path:
    return project_root / "output"


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        fm = {}
    return fm, m.group(2)


def _parse_canonical(canonical: str) -> dict:
    parts = canonical.split("_")
    if len(parts) >= 2:
        author = parts[0]
        year = parts[1] if parts[1].isdigit() else "n.d."
        title_kws = parts[2:]
    else:
        author, year, title_kws = "Unknown", "n.d.", []
    title = " ".join(w.capitalize() for w in title_kws) if title_kws else canonical
    return {"author": author, "year": year, "title": title}


def collect_entries(project_root: Path, include_non_cited: bool = False) -> list[dict]:
    adir = analyzed_dir(project_root)
    if not adir.exists():
        return []
    entries = []
    for p in sorted(adir.glob("*.md")):
        try:
            fm, _ = split_frontmatter(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        cs = fm.get("citation_state", {}) or {}
        use_count = cs.get("use_count_in_output", 0) or 0
        if not include_non_cited and use_count == 0:
            continue
        meta = _parse_canonical(p.stem)
        meta["canonical"] = p.stem
        meta["use_count"] = use_count
        meta["anchor"] = fm.get("anchor", False)
        meta["axis_tags"] = fm.get("axis_tags") or []
        entries.append(meta)
    return entries


# ──────────────────────────────────────────────────────────────────────
# 포맷
# ──────────────────────────────────────────────────────────────────────

def render_apa(entries: list[dict]) -> str:
    lines = ["# Bibliography (APA 7th)\n"]
    for e in sorted(entries, key=lambda x: (x["author"].lower(), x["year"])):
        lines.append(f"- {e['author']}, A. ({e['year']}). *{e['title']}*. _[저널·권·페이지 보완 필요]_")
    return "\n".join(lines) + "\n"


def render_mla(entries: list[dict]) -> str:
    lines = ["# Bibliography (MLA)\n"]
    for e in sorted(entries, key=lambda x: (x["author"].lower(), x["year"])):
        lines.append(f"- {e['author']}. \"{e['title']}.\" _[저널]_, {e['year']}.")
    return "\n".join(lines) + "\n"


def render_chicago(entries: list[dict]) -> str:
    lines = ["# Bibliography (Chicago)\n"]
    for e in sorted(entries, key=lambda x: (x["author"].lower(), x["year"])):
        lines.append(f"- {e['author']}. {e['year']}. \"{e['title']}.\" _[저널]_.")
    return "\n".join(lines) + "\n"


def render_bibtex(entries: list[dict]) -> str:
    out = []
    for e in sorted(entries, key=lambda x: (x["author"].lower(), x["year"])):
        key = f"{e['author'].lower()}{e['year']}"
        out.append("@article{" + key + ",")
        out.append(f"  author = {{{e['author']}}},")
        out.append(f"  year = {{{e['year']}}},")
        out.append(f"  title = {{{e['title']}}},")
        out.append(f"  journal = {{<수동 보완>}},")
        out.append("}\n")
    return "\n".join(out) + "\n"


_FMT = {
    "apa": (render_apa, "bibliography.md"),
    "mla": (render_mla, "bibliography.md"),
    "chicago": (render_chicago, "bibliography.md"),
    "bibtex": (render_bibtex, "bibliography.bib"),
}


def render(project_root: Path, format_: str = "apa",
           include_non_cited: bool = False,
           include_anchor_unused: bool = False) -> Path:
    if format_ not in _FMT:
        raise ValueError(f"unknown format: {format_}")

    cited = collect_entries(project_root, include_non_cited=include_non_cited)
    fn, filename = _FMT[format_]
    body = fn(cited)

    if include_anchor_unused:
        all_papers = collect_entries(project_root, include_non_cited=True)
        anchor_unused = [e for e in all_papers if e["anchor"] and e["use_count"] == 0]
        if anchor_unused:
            body += "\n---\n\n## ⚠️ Anchor 미사용 (검토 필요)\n\n"
            for e in anchor_unused:
                body += f"- {e['canonical']} (anchor 선언됐으나 인용 0회)\n"

    odir = output_dir(project_root)
    odir.mkdir(parents=True, exist_ok=True)
    out = odir / filename
    out.write_text(body, encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--format", default="apa", choices=list(_FMT.keys()))
    parser.add_argument("--include-non-cited", action="store_true")
    parser.add_argument("--include-anchor-unused", action="store_true")
    args = parser.parse_args(argv)

    repo = SCRIPTS_DIR.parent
    project_root = repo / "projects" / args.project
    if not project_root.exists():
        print(f"❌ 프로젝트 없음: {project_root}")
        return 1

    out = render(project_root, args.format,
                 include_non_cited=args.include_non_cited,
                 include_anchor_unused=args.include_anchor_unused)
    print(f"✅ 생성: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
