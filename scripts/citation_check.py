#!/usr/bin/env python3
"""
citation_check.py — 단순화 마이그레이션 Phase A.3.

output.md (또는 output/*.md) 인용 ↔ analyzed/*.md 정합성 검증.

검사:
1. (Author year) 추출
2. analyzed/{Author_Year_*}.md 매칭
3. 페이지 번호가 analyzed의 "인용 가능" 섹션에 있는지
4. anchor=true인데 인용 0회 → 경고
5. analyzed에 없는 paper 인용 → 경고

산출: output/.citation-check-report.md (또는 stdout)

CLI:
    python3 scripts/citation_check.py <project>
    python3 scripts/citation_check.py <project> --json
"""
from __future__ import annotations

import argparse
import json
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


# ──────────────────────────────────────────────────────────────────────
# 인용 추출
# ──────────────────────────────────────────────────────────────────────

_INLINE = re.compile(
    r"\(([A-ZÀ-Ý][A-Za-zà-ÿ\-]+(?:\s+(?:et\s+al\.?|and|&)\s+[A-ZÀ-Ý][A-Za-zà-ÿ\-]+)?)"
    r",?\s*(\d{4})(?:,?\s*p?p?\.?\s*(\d+(?:[-–]\d+)?))?\)",
)
_NARRATIVE = re.compile(
    r"([A-ZÀ-Ý][A-Za-zà-ÿ\-]+)(?:\s+et\s+al\.?)?\s+\((\d{4})(?:,\s*p?\.\s*(\d+(?:[-–]\d+)?))?\)",
)


def extract_citations(odir: Path) -> list[dict]:
    citations: list[dict] = []
    if not odir.exists():
        # output/*.md 없으면 단일 output.md 또는 ch*.md 검사
        return citations
    targets = list(odir.glob("**/*.md"))
    # output 폴더가 아니어도 output.md 단일 파일 케이스
    if not targets:
        return citations
    for md in sorted(targets):
        if md.name.startswith(".") or md.name in ("bibliography.md", ".citation-check-report.md"):
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(text.split("\n"), start=1):
            for m in _INLINE.finditer(line):
                citations.append({
                    "file": md.name,
                    "line": i,
                    "author": m.group(1).strip(),
                    "year": m.group(2),
                    "page": m.group(3) or None,
                    "raw": m.group(0),
                    "type": "inline",
                })
            for m in _NARRATIVE.finditer(line):
                if any(c["raw"] == m.group(0) for c in citations
                       if c["file"] == md.name and c["line"] == i):
                    continue
                citations.append({
                    "file": md.name,
                    "line": i,
                    "author": m.group(1).strip(),
                    "year": m.group(2),
                    "page": m.group(3) or None,
                    "raw": m.group(0),
                    "type": "narrative",
                })
    return citations


def extract_single_file_citations(file_path: Path) -> list[dict]:
    """output.md 단일 파일 모드."""
    if not file_path.exists():
        return []
    citations = []
    text = file_path.read_text(encoding="utf-8")
    for i, line in enumerate(text.split("\n"), start=1):
        for m in _INLINE.finditer(line):
            citations.append({
                "file": file_path.name, "line": i,
                "author": m.group(1).strip(), "year": m.group(2),
                "page": m.group(3) or None, "raw": m.group(0), "type": "inline",
            })
        for m in _NARRATIVE.finditer(line):
            if any(c["raw"] == m.group(0) for c in citations
                   if c["file"] == file_path.name and c["line"] == i):
                continue
            citations.append({
                "file": file_path.name, "line": i,
                "author": m.group(1).strip(), "year": m.group(2),
                "page": m.group(3) or None, "raw": m.group(0), "type": "narrative",
            })
    return citations


# ──────────────────────────────────────────────────────────────────────
# Analyzed 매칭
# ──────────────────────────────────────────────────────────────────────

def list_analyzed(project_root: Path) -> list[tuple[str, dict, str]]:
    """analyzed/*.md → [(canonical, frontmatter, body), ...]."""
    adir = analyzed_dir(project_root)
    if not adir.exists():
        return []
    out = []
    for p in sorted(adir.glob("*.md")):
        try:
            text = p.read_text(encoding="utf-8")
            fm, body = split_frontmatter(text)
        except Exception:
            continue
        out.append((p.stem, fm, body))
    return out


def _author_year_from_canonical(canonical: str) -> tuple[str, str]:
    parts = canonical.split("_")
    if len(parts) < 2:
        return "", ""
    return parts[0].lower(), parts[1]


def match_citation(citation: dict, analyzed: list[tuple[str, dict, str]]) -> tuple[str, dict, str] | None:
    a = citation["author"].lower()
    a = re.sub(r"\bet\s+al\.?", "", a, flags=re.IGNORECASE).strip()
    a = re.sub(r"\s+(?:and|&)\s+.*", "", a, flags=re.IGNORECASE).strip()
    y = citation["year"]
    for canonical, fm, body in analyzed:
        c_author, c_year = _author_year_from_canonical(canonical)
        if c_author == a and c_year == y:
            return (canonical, fm, body)
        if a and a in c_author and c_year == y:
            return (canonical, fm, body)
    return None


# ──────────────────────────────────────────────────────────────────────
# Lint
# ──────────────────────────────────────────────────────────────────────

_PAGE_IN_QUOTE_RE = re.compile(r"\(p\.?\s*(\d+)|\bp\.?\s*(\d+)\)|page:\s*(\d+)")


def extract_pages_from_body(body: str) -> set[str]:
    """analyzed/{}.md '인용 가능' 섹션에서 페이지 번호 추출."""
    pages = set()
    for m in _PAGE_IN_QUOTE_RE.finditer(body):
        for g in m.groups():
            if g:
                pages.add(g)
    return pages


def check(project_root: Path) -> dict:
    odir = output_dir(project_root)
    citations = extract_citations(odir)
    # output.md 단일 파일도 보조
    single = project_root / "output.md"
    if single.exists():
        citations.extend(extract_single_file_citations(single))

    analyzed = list_analyzed(project_root)
    anchors = [(c, fm, body) for c, fm, body in analyzed if fm.get("anchor")]

    issues: list[dict] = []
    matched_canonicals: set[str] = set()

    for c in citations:
        m = match_citation(c, analyzed)
        if not m:
            issues.append({
                "level": "warning",
                "code": "no_analyzed_match",
                "file": c["file"], "line": c["line"],
                "msg": f"({c['author']} {c['year']})이 analyzed/에 없음. "
                       f"외부 인용이거나 paper 누락.",
            })
            continue
        canonical, fm, body = m
        matched_canonicals.add(canonical)

        if c["page"]:
            pages = extract_pages_from_body(body)
            cited_page = c["page"].split("-")[0]
            if pages and cited_page not in pages:
                issues.append({
                    "level": "info",
                    "code": "page_not_in_quote_pool",
                    "file": c["file"], "line": c["line"],
                    "msg": f"({c['author']} {c['year']}, p.{c['page']}) — "
                           f"analyzed 인용 가능 페이지({sorted(pages)})에 없음. 검증 필요.",
                })

    # Anchor 미사용
    for canonical, fm, body in anchors:
        if canonical not in matched_canonicals:
            issues.append({
                "level": "info",
                "code": "anchor_uncited",
                "msg": f"Anchor `{canonical}` output에 인용 0회 — 자격 재검토 또는 인용 추가.",
            })

    return {
        "total_citations": len(citations),
        "matched_papers": len(matched_canonicals),
        "anchor_total": len(anchors),
        "anchor_cited": sum(1 for c, _, _ in anchors if c in matched_canonicals),
        "issues": issues,
    }


def render_report(project_root: Path) -> Path:
    report = check(project_root)
    lines = ["# Citation Check Report\n"]
    lines.append(f"> 인용 {report['total_citations']}건 · 매칭 {report['matched_papers']}편")
    lines.append(f"> Anchor: {report['anchor_cited']}/{report['anchor_total']} 인용됨\n")

    if not report["issues"]:
        lines.append("✅ 검출 문제 없음")
    else:
        by_level: dict[str, list] = {"error": [], "warning": [], "info": []}
        for i in report["issues"]:
            by_level.setdefault(i["level"], []).append(i)
        for lvl in ("error", "warning", "info"):
            if not by_level.get(lvl):
                continue
            sym = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[lvl]
            lines.append(f"\n## {sym} {lvl.upper()} ({len(by_level[lvl])}건)\n")
            for i in by_level[lvl]:
                loc = f" [{i.get('file', '')}:{i.get('line', '')}]" if i.get("file") else ""
                lines.append(f"- **[{i['code']}]**{loc}: {i['msg']}")

    odir = output_dir(project_root)
    odir.mkdir(parents=True, exist_ok=True)
    out = odir / ".citation-check-report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repo = SCRIPTS_DIR.parent
    project_root = repo / "projects" / args.project
    if not project_root.exists():
        print(f"❌ 프로젝트 없음: {project_root}")
        return 1

    if args.json:
        print(json.dumps(check(project_root), ensure_ascii=False, indent=2))
    else:
        out = render_report(project_root)
        report = check(project_root)
        n = len(report["issues"])
        print(f"✅ 생성: {out}")
        if n == 0:
            print("✅ 검출 문제 없음")
        else:
            print(f"⚠️  {n}건 이슈 — {out} 참조")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
