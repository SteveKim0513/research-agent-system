#!/usr/bin/env python3
"""
build_index.py — analyzed/INDEX.md 자동 생성.

paper-analyst가 분석 완료 후 [X][D].{name}.md frontmatter에 채운 index_fields
블록을 모든 analyzed 파일에서 수집해 INDEX.md (A: §섹션 매핑 / B: 분석 완료 paper /
C: audit 통계) 단일 파일로 렌더한다.

INDEX.md는 view일 뿐 SSOT 아님. 사용자 직접 편집 금지 (다음 빌드에서 덮어씀).
모든 paper 데이터는 각 [X][D].md frontmatter.index_fields가 SSOT.

CLI:
    python3 scripts/build_index.py <project>

자동 호출:
- process_papers.py 끝
- paper-analyst Mode A/B/C 완료 후
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

try:
    import yaml
except ImportError:
    print("build_index.py: pyyaml 필요. `pip install pyyaml`", file=sys.stderr)
    sys.exit(2)


# ──────────────────────────────────────────────────────────────────────
# Path helpers
# ──────────────────────────────────────────────────────────────────────

def project_root(repo: Path, project: str) -> Path:
    return repo / "projects" / project


def analyzed_dir(proj: Path) -> Path:
    return proj / "papers" / "analyzed"


def flow_md_path(proj: Path) -> Path:
    return proj / "flow" / "flow.md"


def output_dir(proj: Path) -> Path:
    return proj / "output"


def index_path(proj: Path) -> Path:
    return analyzed_dir(proj) / "INDEX.md"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ──────────────────────────────────────────────────────────────────────
# Frontmatter parsing
# ──────────────────────────────────────────────────────────────────────

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(md_text: str) -> dict | None:
    m = _FM_RE.match(md_text)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None


# ──────────────────────────────────────────────────────────────────────
# 파일 분류 (filename prefix 기반)
# ──────────────────────────────────────────────────────────────────────

def classify_filename(name: str) -> tuple[str, str]:
    """파일명 → (status, tier).

    status ∈ {pending, done, curation, unknown}
    tier ∈ {A, N, ?}
    """
    if name.startswith("[A][D]."):
        return "done", "A"
    if name.startswith("[N][D]."):
        return "done", "N"
    if name.startswith("[A]."):
        return "pending", "A"
    if name.startswith("[N]."):
        return "pending", "N"
    if name.startswith("[?]."):
        return "curation", "?"
    return "unknown", "?"


def canonical_from_filename(name: str) -> str:
    """[X][D].{canonical}.md 또는 [X].{canonical}.md → canonical."""
    base = name[:-3] if name.endswith(".md") else name
    # prefix 제거
    for prefix in ("[A][D].", "[N][D].", "[A].", "[N].", "[?]."):
        if base.startswith(prefix):
            return base[len(prefix):]
    return base


# ──────────────────────────────────────────────────────────────────────
# flow.md 섹션 파싱
# ──────────────────────────────────────────────────────────────────────

def parse_flow_sections(flow_md: Path) -> list[dict]:
    """flow.md → [{level, title, line_no}]."""
    if not flow_md.exists():
        return []
    sections = []
    for i, line in enumerate(flow_md.read_text(encoding="utf-8").splitlines(), start=1):
        m = re.match(r"^(#+)\s+(.+?)\s*$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            sections.append({"level": level, "title": title, "line_no": i})
    return sections


def normalize_section_title(t: str) -> str:
    """비교용 정규화 — '§EF' / '§"EF의 ..."' / 'EF의 ...' 모두 같은 키로."""
    s = t.strip()
    s = s.lstrip("§").strip().strip('"').strip("'").strip()
    # 마침표·쉼표 제거
    s = re.sub(r"[.,;:!?]+$", "", s)
    return s.lower()


def section_titles_match(a: str, b: str, min_overlap: int = 5) -> bool:
    """두 섹션 title이 사실상 같은지 — substring match 허용.

    'EF의 보편성과 특수성' ↔ 'EF의 보편성과 특수성에 대하여' 매칭 케이스.
    """
    na, nb = normalize_section_title(a), normalize_section_title(b)
    if na == nb:
        return True
    if len(na) < min_overlap or len(nb) < min_overlap:
        return False
    # 한쪽이 다른 쪽의 prefix이거나 substring (긴 쪽 기준 70% 이상 겹침)
    if na in nb or nb in na:
        shorter = min(len(na), len(nb))
        longer = max(len(na), len(nb))
        return shorter / longer >= 0.5
    return False


def find_matching_section(target: str, candidates: list[str]) -> str | None:
    """candidates 중 target과 매칭되는 첫 title 반환. 없으면 None."""
    for c in candidates:
        if section_titles_match(target, c):
            return c
    return None


# ──────────────────────────────────────────────────────────────────────
# Output 스캔 — 인용 패턴 추출 + paper 매칭
# ──────────────────────────────────────────────────────────────────────

# 학술 인용 패턴:
# 1. (Author, 2020) / (Author & Smith, 2020) / (Author et al., 2020)
# 2. Author (2020) / Author and Smith (2020) / Author et al. (2020)
# 3. (Author 2020) — 쉼표 없는 변형
_CITATION_PARENS_RE = re.compile(
    r"(?:\(|;)\s*([A-ZÀ-Ý][a-zA-ZÀ-ÿ\-']+(?:\s*(?:&|\sand\s)\s*[A-ZÀ-Ý][a-zA-ZÀ-ÿ\-']+)*"
    r"(?:\s+et\s+al\.?)?)[,\s]+(\d{4})[a-z]?",
    re.IGNORECASE,
)
_CITATION_NARRATIVE_RE = re.compile(
    r"(?<![a-zA-Z])([A-ZÀ-Ý][a-zA-ZÀ-ÿ\-']+(?:\s+(?:&|and)\s+[A-ZÀ-Ý][a-zA-ZÀ-ÿ\-']+)?"
    r"(?:\s+et\s+al\.?)?)\s+\((\d{4})[a-z]?\)",
)


def _normalize_author_for_match(s: str) -> str:
    """인용 surface → 매칭 키. 'Adrover-Roig' → 'adroverroig', 'Doebel et al' → 'doebel'."""
    s = re.sub(r"\bet\s+al\.?", "", s, flags=re.IGNORECASE).strip()
    # 첫 author까지만
    parts = re.split(r"\s*(?:&|,|\band\b)\s*", s, flags=re.IGNORECASE)
    first = parts[0].strip() if parts else s
    return re.sub(r"[^A-Za-z]", "", first).lower()


def build_paper_keys(papers: list[dict]) -> dict[tuple[str, str], dict]:
    """paper별 인용 매칭 키 생성. {(author_norm, year): paper}.

    우선순위:
    1. index_fields.author (paper-analyst가 직접 명시한 정확 author) — 가장 신뢰
    2. canonical 첫 토큰 (process_papers.py가 PDF에서 추출, 잡음 가능)
    3. canonical 내부 substring (doebelrethinking 같은 슬러그에서 추출 시도)
    4. 변형: trailing digit/`a` 제거
    """
    keys: dict[tuple[str, str], dict] = {}
    for p in papers:
        parts = p["canonical"].split("_")
        year = ""
        for part in parts[:3]:  # 첫 3토큰 안에 year 있으면 사용
            if re.fullmatch(r"\d{4}", part):
                year = part
                break
        if not year:
            continue

        idx = p.get("index_fields") or {}

        # 1순위: index_fields.author (single string or list)
        idx_author = idx.get("author")
        if idx_author:
            authors = idx_author if isinstance(idx_author, list) else [idx_author]
            for a in authors:
                a_norm = re.sub(r"[^A-Za-z]", "", str(a)).lower()
                if a_norm and len(a_norm) >= 3:
                    keys[(a_norm, year)] = p

        # 2순위: canonical 첫 토큰
        first = re.sub(r"[^A-Za-z]", "", parts[0]).lower()
        if first and len(first) >= 3:
            keys.setdefault((first, year), p)
            clean = re.sub(r"\d+$", "", first)
            if clean and clean != first and len(clean) >= 4:
                keys.setdefault((clean, year), p)
            if first.endswith("a") and len(first) >= 5:
                keys.setdefault((first[:-1], year), p)

        # 3순위: canonical 내부 substring 스캔 — 슬러그에 author 이름이 묻힌 경우
        # (e.g. 'Rethinking_2020_..._doebelrethinking' → 'doebel' 추출)
        # 알려진 저자 surname 패턴: 4자 이상 lowercase 토큰 with 인접한 다른 단어와 합쳐진 경우
        joined = re.sub(r"[^a-z]", "", p["canonical"].lower())
        # known surname 후보를 vs 필드에서 가져옴 (다른 paper가 자기를 'Doebel_2020'로 참조하면 그게 author)
        for other in papers:
            if other is p:
                continue
            vs = (other.get("index_fields") or {}).get("vs") or {}
            for ref_key in vs.keys():
                m = re.match(r"^([A-Za-z]+)_(\d{4})$", str(ref_key))
                if not m:
                    continue
                ref_author, ref_year = m.group(1).lower(), m.group(2)
                if ref_year != year:
                    continue
                if len(ref_author) >= 4 and ref_author in joined:
                    keys.setdefault((ref_author, year), p)
    return keys


def match_citation(author_raw: str, year: str, paper_keys: dict) -> dict | None:
    """(author_surface, year) → paper or None.

    매칭 우선순위:
    1. 정확 (author_norm, year)
    2. surface가 canonical_author의 prefix (또는 역)
    3. 최소 4자 이상 공통
    """
    author = _normalize_author_for_match(author_raw)
    if not author or not year:
        return None

    if (author, year) in paper_keys:
        return paper_keys[(author, year)]

    for (a, y), p in paper_keys.items():
        if y != year:
            continue
        if len(a) < 4 or len(author) < 4:
            continue
        # prefix 또는 동일 (kroupin vs kroupina)
        if author.startswith(a) or a.startswith(author):
            return p
    return None


def parse_output(odir: Path, papers: list[dict]) -> dict:
    """output/*.md 스캔 → 섹션 + 인용 매칭 결과.

    반환:
        files_scanned: int
        sections: [{file, level, title, line_no}]
        citations: [{file, section, paper_canonical, line_no, raw}]
        paper_citation_counts: {canonical: N}
        paper_cited_sections: {canonical: [section_title, ...]}
        unmatched_citations: [{file, section, raw, line_no}]  # paper 매칭 실패한 인용
        section_to_papers: {section_title: [paper_canonical, ...]}  # 섹션별 paper 리스트
    """
    result = {
        "files_scanned": 0,
        "sections": [],
        "citations": [],
        "paper_citation_counts": defaultdict(int),
        "paper_cited_sections": defaultdict(set),
        "unmatched_citations": [],
        "section_to_papers": defaultdict(list),
    }
    if not odir.exists():
        return result

    paper_keys = build_paper_keys(papers)

    for f in sorted(odir.glob("*.md")):
        if f.name.startswith("."):
            continue
        result["files_scanned"] += 1
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue

        # frontmatter 제거
        text = re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL)

        current_section = f.stem  # 헤더 만나기 전 default
        for line_no, line in enumerate(text.splitlines(), start=1):
            # 섹션 헤더
            hm = re.match(r"^(#+)\s+(.+?)\s*$", line)
            if hm:
                level = len(hm.group(1))
                title = hm.group(2).strip()
                current_section = title
                result["sections"].append({
                    "file": f.name, "level": level,
                    "title": title, "line_no": line_no,
                })
                continue

            # 인용 추출 (한 줄에 여러 인용 가능)
            seen_in_line: set[tuple[str, str]] = set()
            for m in _CITATION_PARENS_RE.finditer(line):
                author_raw, year = m.group(1), m.group(2)
                key = (author_raw.lower(), year)
                if key in seen_in_line:
                    continue
                seen_in_line.add(key)
                p = match_citation(author_raw, year, paper_keys)
                _record_citation(result, f.name, current_section,
                                 line_no, author_raw, year, p)
            for m in _CITATION_NARRATIVE_RE.finditer(line):
                author_raw, year = m.group(1), m.group(2)
                key = (author_raw.lower(), year)
                if key in seen_in_line:
                    continue
                seen_in_line.add(key)
                p = match_citation(author_raw, year, paper_keys)
                _record_citation(result, f.name, current_section,
                                 line_no, author_raw, year, p)

    # set → list 변환
    result["paper_cited_sections"] = {
        k: sorted(v) for k, v in result["paper_cited_sections"].items()
    }
    result["paper_citation_counts"] = dict(result["paper_citation_counts"])
    result["section_to_papers"] = {
        k: sorted(set(v)) for k, v in result["section_to_papers"].items()
    }
    return result


def _record_citation(result: dict, fname: str, section: str, line_no: int,
                     author_raw: str, year: str, p: dict | None) -> None:
    raw = f"{author_raw} ({year})"
    if p is None:
        result["unmatched_citations"].append({
            "file": fname, "section": section,
            "line_no": line_no, "raw": raw,
        })
        return
    result["citations"].append({
        "file": fname, "section": section, "line_no": line_no,
        "paper_canonical": p["canonical"], "raw": raw,
    })
    result["paper_citation_counts"][p["canonical"]] += 1
    result["paper_cited_sections"][p["canonical"]].add(section)
    result["section_to_papers"][section].append(p["canonical"])


# ──────────────────────────────────────────────────────────────────────
# Citation state writeback — 각 paper frontmatter에 use_count 갱신
# ──────────────────────────────────────────────────────────────────────

def writeback_citation_state(adir: Path, papers: list[dict],
                              output_data: dict) -> int:
    """각 paper의 frontmatter.citation_state.use_count_in_output·cited_in_sections 갱신.

    반환: 갱신된 paper 수.
    """
    counts = output_data.get("paper_citation_counts", {})
    sections_map = output_data.get("paper_cited_sections", {})
    updated = 0

    for p in papers:
        canonical = p["canonical"]
        new_count = counts.get(canonical, 0)
        new_sections = sections_map.get(canonical, [])
        cs = p["frontmatter"].get("citation_state") or {}
        old_count = cs.get("use_count_in_output", 0)
        old_sections = cs.get("cited_in_sections") or []

        if new_count == old_count and sorted(new_sections) == sorted(old_sections):
            continue  # 변경 없음

        # frontmatter rewrite
        fpath = adir / p["filename"]
        try:
            text = fpath.read_text(encoding="utf-8")
        except Exception:
            continue
        m = _FM_RE.match(text)
        if not m:
            continue
        body = text[m.end():]
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            continue
        cs = fm.setdefault("citation_state", {})
        cs["use_count_in_output"] = new_count
        cs["cited_in_sections"] = new_sections
        new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=10000)
        fpath.write_text(f"---\n{new_fm}---\n{body}", encoding="utf-8")
        updated += 1

    return updated


# ──────────────────────────────────────────────────────────────────────
# 데이터 수집
# ──────────────────────────────────────────────────────────────────────

def collect_papers(adir: Path) -> list[dict]:
    """analyzed/ → paper별 dict 리스트."""
    if not adir.exists():
        return []
    papers = []
    for f in sorted(adir.iterdir()):
        if not f.is_file() or not f.name.endswith(".md"):
            continue
        if f.name == "INDEX.md":
            continue
        status, tier = classify_filename(f.name)
        if status == "unknown":
            continue
        canonical = canonical_from_filename(f.name)
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        fm = parse_frontmatter(text) or {}
        papers.append({
            "filename": f.name,
            "canonical": canonical,
            "status": status,
            "tier": tier,
            "frontmatter": fm,
            "index_fields": fm.get("index_fields") or {},
        })
    return papers


# ──────────────────────────────────────────────────────────────────────
# 렌더 — Section A: §섹션 매핑
# ──────────────────────────────────────────────────────────────────────

_AGE_GROUP_ABBR = {
    "early childhood": "EC",
    "middle childhood": "MC",
    "Adolescence": "AD",
    "해당없음": "—",
}


def _format_age_group_short(age_group: str) -> str:
    """age_group을 짧게 — 'early childhood + middle childhood' → 'EC+MC'."""
    if not age_group:
        return ""
    parts = [p.strip() for p in age_group.split("+")]
    return "+".join(_AGE_GROUP_ABBR.get(p, p) for p in parts)


def _format_paper_label(p: dict) -> str:
    """B 섹션 등에서 사용하는 짧은 라벨: 'Doebel 2020 [steelman,delta]'."""
    canonical = p["canonical"]
    parts = canonical.split("_")
    author = parts[0] if parts else canonical
    year = parts[1] if len(parts) > 1 and parts[1].isdigit() else ""
    label = f"{author} {year}".strip()
    age = _format_age_group_short(p["frontmatter"].get("age_group") or "")
    if age:
        label += f" ({age})"
    axis = p["frontmatter"].get("axis_tags") or []
    if axis:
        label += f" [{','.join(axis)}]"
    return label


def render_section_a(papers: list[dict], flow_sections: list[dict],
                      output_data: dict) -> str:
    """A. §Section 매핑 — A1 plan / A2 actual / A3 discrepancy."""
    lines = ["## A. §Section 매핑 — drafting 시작점", ""]
    if not flow_sections:
        lines.append("⚠ flow.md 없음 또는 섹션 헤더 0개.")
        lines.append("")
        return "\n".join(lines)

    # flow 섹션 title 리스트 (level >= 2)
    flow_titles = [s["title"] for s in flow_sections if s["level"] >= 2]

    # ── A1: 계획 (intended, from index_fields.sections_used) ──
    # 각 paper의 sections_used를 flow title로 정규화 매핑 (fuzzy)
    plan_section_to_papers: dict[str, dict[str, list[dict]]] = defaultdict(
        lambda: {"anchor_done": [], "non_anchor_done": [],
                 "anchor_skeleton": [], "non_anchor_skeleton": []}
    )
    canonical_to_planned_titles: dict[str, set[str]] = defaultdict(set)  # flow title 기준
    canonical_to_planned_raw: dict[str, set[str]] = defaultdict(set)  # 원본 (flow에 없으면)
    unassigned_done: list[dict] = []

    for p in papers:
        sections_used = p["index_fields"].get("sections_used") or []
        if not sections_used and p["status"] == "done":
            unassigned_done.append(p)
            continue
        for s in sections_used:
            # flow title과 fuzzy 매칭 시도
            matched = find_matching_section(s, flow_titles)
            canonical_title = matched if matched else s
            if matched:
                canonical_to_planned_titles[p["canonical"]].add(matched)
            else:
                canonical_to_planned_raw[p["canonical"]].add(s)
            key = normalize_section_title(canonical_title)
            if p["status"] == "done":
                if p["tier"] == "A":
                    plan_section_to_papers[key]["anchor_done"].append(p)
                else:
                    plan_section_to_papers[key]["non_anchor_done"].append(p)
            elif p["status"] == "pending":
                if p["tier"] == "A":
                    plan_section_to_papers[key]["anchor_skeleton"].append(p)
                else:
                    plan_section_to_papers[key]["non_anchor_skeleton"].append(p)

    # ── A2: 실제 (actual, from output scan) ──
    # output 섹션 → flow 섹션으로 정규화 매핑
    output_section_to_papers: dict[str, list[tuple[str, int]]] = defaultdict(list)
    output_unmapped_sections: list[str] = []  # flow에 없는 output-only 섹션
    flow_keys = {normalize_section_title(s["title"]) for s in flow_sections if s["level"] >= 2}

    counts = output_data.get("paper_citation_counts", {})
    cited_sections_map = output_data.get("paper_cited_sections", {})
    section_to_papers = output_data.get("section_to_papers", {})
    files_scanned = output_data.get("files_scanned", 0)

    # output에 인용된 paper의 cited section을 flow title로 fuzzy 매핑
    canonical_to_cited_titles: dict[str, set[str]] = defaultdict(set)  # flow title 기준
    canonical_to_cited_raw: dict[str, set[str]] = defaultdict(set)  # 원본 (flow에 없으면)
    for canonical, secs in cited_sections_map.items():
        for s in secs:
            matched = find_matching_section(s, flow_titles)
            if matched:
                canonical_to_cited_titles[canonical].add(matched)
            else:
                canonical_to_cited_raw[canonical].add(s)

    output_section_to_papers_by_flow: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for output_sec, paper_canonicals in section_to_papers.items():
        matched = find_matching_section(output_sec, flow_titles)
        if matched:
            key = normalize_section_title(matched)
            output_section_to_papers_by_flow[key] = [(c, counts.get(c, 0)) for c in set(paper_canonicals)]
        else:
            # flow에 없는 output-only 섹션
            output_section_to_papers[normalize_section_title(output_sec)] = [
                (c, counts.get(c, 0)) for c in set(paper_canonicals)
            ]
            output_unmapped_sections.append(output_sec)
    # 통합
    for k, v in output_section_to_papers_by_flow.items():
        output_section_to_papers[k] = v

    # ── 렌더 ──
    lines.append(f"### A1 — flow.md 계획 (intended)")
    lines.append("")
    for sec in flow_sections:
        if sec["level"] < 2:
            continue
        title = sec["title"]
        line_no = sec["line_no"]
        key = normalize_section_title(title)
        bucket = plan_section_to_papers.get(key)
        lines.append(f"#### §{title} (line {line_no})")
        if bucket and bucket["anchor_done"]:
            labels = [_format_paper_label(p) for p in bucket["anchor_done"]]
            lines.append(f"  anchor [done]: {', '.join(labels)}")
        if bucket and bucket["non_anchor_done"]:
            labels = [_format_paper_label(p) for p in bucket["non_anchor_done"]]
            lines.append(f"  non-anchor [done]: {', '.join(labels)}")
        if bucket and bucket["anchor_skeleton"]:
            labels = [_format_paper_label(p) for p in bucket["anchor_skeleton"]]
            lines.append(f"  anchor [skeleton, 분석 권고]: {', '.join(labels)}")
        if bucket and bucket["non_anchor_skeleton"]:
            labels = [_format_paper_label(p) for p in bucket["non_anchor_skeleton"]]
            lines.append(f"  non-anchor [skeleton]: {', '.join(labels)}")
        if not bucket or not any(bucket.values()):
            lines.append("  (매핑된 paper 없음 — gap)")
        lines.append("")

    if unassigned_done:
        lines.append("#### [unassigned — 분석 완료지만 §매핑 없음]")
        for p in unassigned_done:
            label = _format_paper_label(p)
            claim = p["index_fields"].get("claim_oneline") or ""
            lines.append(f"  - {label}: {claim[:80]}{'...' if len(claim) > 80 else ''}")
        lines.append("")

    # ── A2 ──
    lines.append(f"### A2 — output 실제 인용 (actual, scanned from output/*.md)")
    lines.append("")
    if files_scanned == 0:
        lines.append("(output 디렉토리 비어 있음 — 작성 시작 전)")
        lines.append("")
    else:
        lines.append(f"output/*.md 파일 {files_scanned}개 스캔됨, 매칭된 인용 {len(output_data.get('citations', []))}건")
        lines.append("")
        # canonical → label 매핑
        canonical_to_paper = {p["canonical"]: p for p in papers}
        # flow 섹션 순서대로 + flow에 없는 output 섹션은 끝에
        for sec in flow_sections:
            if sec["level"] < 2:
                continue
            title = sec["title"]
            key = normalize_section_title(title)
            cited = output_section_to_papers.get(key, [])
            if not cited:
                continue
            cited_labels = []
            for canonical, count in sorted(cited, key=lambda x: -x[1]):
                p = canonical_to_paper.get(canonical)
                label = _format_paper_label(p) if p else canonical
                cited_labels.append(f"{label} [{count}회]")
            lines.append(f"#### §{title}")
            lines.append(f"  cited: {', '.join(cited_labels)}")
            lines.append("")
        if output_unmapped_sections:
            lines.append("#### [output에만 있는 섹션 — flow에 없음]")
            for output_sec in sorted(set(output_unmapped_sections)):
                norm = normalize_section_title(output_sec)
                cited = output_section_to_papers.get(norm, [])
                cited_labels = []
                for canonical, count in cited:
                    p = canonical_to_paper.get(canonical)
                    label = _format_paper_label(p) if p else canonical
                    cited_labels.append(f"{label} [{count}회]")
                lines.append(f"  §{output_sec}: {', '.join(cited_labels)}")
            lines.append("")

        unmatched = output_data.get("unmatched_citations", [])
        if unmatched:
            lines.append(f"#### ⚠ 매칭 실패 인용 ({len(unmatched)}건 — paper 미수집 또는 author/year 잡음)")
            for u in unmatched[:10]:
                lines.append(f"  - {u['file']}:{u['line_no']} §{u['section']} — `{u['raw']}`")
            if len(unmatched) > 10:
                lines.append(f"  …외 {len(unmatched) - 10}건")
            lines.append("")

    # ── A3: Discrepancy (flow title 기준 비교, fuzzy match 적용) ──
    lines.append(f"### A3 — Discrepancy (계획 ↔ 실제)")
    lines.append("")
    if files_scanned == 0:
        lines.append("(output 비어 있음 — discrepancy 계산 보류)")
        lines.append("")
    else:
        # planned but not cited (flow title 기준 비교)
        planned_only: list[tuple[dict, list[str]]] = []
        for canonical, planned_titles in canonical_to_planned_titles.items():
            cited_titles = canonical_to_cited_titles.get(canonical, set())
            missing = planned_titles - cited_titles
            if missing:
                p = next((pp for pp in papers if pp["canonical"] == canonical), None)
                if p and p["status"] == "done":
                    planned_only.append((p, sorted(missing)))
        # raw planned (flow에 매칭 안 됐지만 paper-analyst가 명시한 섹션)
        for canonical, raw_titles in canonical_to_planned_raw.items():
            if not raw_titles:
                continue
            p = next((pp for pp in papers if pp["canonical"] == canonical), None)
            if p and p["status"] == "done":
                planned_only.append((p, [f"{t} (flow에 매칭 안 됨)" for t in sorted(raw_titles)]))

        if planned_only:
            lines.append("#### Planned but not cited yet (분석 완료 paper 중 의도된 §에 미인용)")
            for p, secs in planned_only:
                label = _format_paper_label(p)
                lines.append(f"  - {label} — 의도 §: {', '.join(secs)}")
            lines.append("")

        # cited but not planned
        cited_only: list[tuple[dict, list[str]]] = []
        for canonical, cited_titles in canonical_to_cited_titles.items():
            planned_titles = canonical_to_planned_titles.get(canonical, set())
            extra = cited_titles - planned_titles
            if extra:
                p = next((pp for pp in papers if pp["canonical"] == canonical), None)
                if p:
                    cited_only.append((p, sorted(extra)))
        # raw cited (flow에 매칭 안 됐지만 output에 등장)
        for canonical, raw_titles in canonical_to_cited_raw.items():
            if not raw_titles:
                continue
            p = next((pp for pp in papers if pp["canonical"] == canonical), None)
            if p:
                cited_only.append((p, [f"{t} (flow에 매칭 안 됨)" for t in sorted(raw_titles)]))

        if cited_only:
            lines.append("#### Cited but not planned (계획 외 인용 — 새 발굴 가능성)")
            for p, secs in cited_only:
                label = _format_paper_label(p)
                lines.append(f"  - {label} — 인용된 §: {', '.join(secs)}")
            lines.append("")

        if not planned_only and not cited_only:
            lines.append("(불일치 없음 — 계획대로 인용됨)")
            lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
# 렌더 — Section B: 분석 완료 papers
# ──────────────────────────────────────────────────────────────────────

def render_paper_entry(p: dict) -> str:
    """B 섹션 — paper별 7-10줄 entry."""
    fm = p["frontmatter"]
    idx = p["index_fields"]
    parts = p["canonical"].split("_")
    author = parts[0] if parts else p["canonical"]
    year = parts[1] if len(parts) > 1 and parts[1].isdigit() else ""

    title = idx.get("title") or fm.get("title") or ""
    tier_label = "[A] anchor" if p["tier"] == "A" else "[N] non-anchor"
    consensus = fm.get("consensus_category") or ""
    citations = fm.get("citations") or 0
    cross_count = fm.get("cross_research_count") or 0
    model = fm.get("model_used") or "?"
    fallback_step = fm.get("policy_fallback_step")

    lines = []
    head = f"### {author} {year}"
    if title:
        head += f" — {title}"
    lines.append(head)
    lines.append(f"- canonical: {p['canonical']}")
    meta_parts = [tier_label]
    if consensus:
        meta_parts.append(consensus)
    meta_parts.append(f"{citations} citations")
    meta_parts.append(f"cross_research: {cross_count}")
    meta_parts.append(f"model: {model}")
    if fallback_step:
        meta_parts.append(f"policy_fallback_step: {fallback_step}")
    lines.append("- " + " · ".join(meta_parts))

    age_group = fm.get("age_group") or ""
    if age_group:
        lines.append(f"- 연령대: {age_group}")

    sections_used = idx.get("sections_used") or []
    if sections_used:
        lines.append(f"- 사용 §: {', '.join(sections_used)}")

    axis = fm.get("axis_tags") or []
    if axis:
        lines.append(f"- axis: {', '.join(axis)}")

    claim = idx.get("claim_oneline") or ""
    if claim:
        lines.append(f"- 핵심: {claim}")

    keywords = idx.get("keywords") or []
    if keywords:
        lines.append(f"- 키워드: {', '.join(keywords)}")

    self_limit = idx.get("self_limit") or ""
    if self_limit:
        lines.append(f"- self-limit: {self_limit}")

    foil = idx.get("foil") or []
    if foil:
        lines.append(f"- foil/반대: {', '.join(foil)}")

    vs = idx.get("vs") or {}
    if vs:
        lines.append("- vs:")
        for other, info in vs.items():
            stance = info.get("stance", "?") if isinstance(info, dict) else str(info)
            note = info.get("note", "") if isinstance(info, dict) else ""
            entry = f"    {other} — {stance}"
            if note:
                entry += f" ({note})"
            lines.append(entry)

    quote_count = idx.get("quote_count")
    quote_cats = idx.get("quote_categories") or {}
    if quote_count:
        cat_parts = [f"{k} {v}" for k, v in quote_cats.items()]
        cat_str = f" ({' / '.join(cat_parts)})" if cat_parts else ""
        lines.append(f"- 인용: {quote_count}편{cat_str}")

    last_analyzed = fm.get("last_analyzed") or ""
    cs = fm.get("citation_state") or {}
    use_count = cs.get("use_count_in_output", 0)
    lines.append(f"- last_analyzed: {last_analyzed} · use_count: {use_count}")

    return "\n".join(lines)


def render_section_b(papers: list[dict]) -> str:
    """B. 분석 완료 papers."""
    done = [p for p in papers if p["status"] == "done"]
    # tier A 먼저, 그 다음 use_count desc, alphabetical
    done.sort(key=lambda p: (
        0 if p["tier"] == "A" else 1,
        -((p["frontmatter"].get("citation_state") or {}).get("use_count_in_output", 0)),
        p["canonical"],
    ))

    lines = [f"## B. 분석 완료 papers ([X][D]) — {len(done)}편", ""]
    if not done:
        lines.append("(아직 분석 완료된 paper 없음)")
        lines.append("")
        return "\n".join(lines)

    for p in done:
        lines.append(render_paper_entry(p))
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
# 렌더 — Section C: Audit
# ──────────────────────────────────────────────────────────────────────

def render_section_c(papers: list[dict]) -> str:
    """C. Audit — pending / blocked / 통계."""
    done = [p for p in papers if p["status"] == "done"]
    pending = [p for p in papers if p["status"] == "pending"]
    curation = [p for p in papers if p["status"] == "curation"]
    blocked = [p for p in papers if p["frontmatter"].get("policy_blocked")]

    lines = ["## C. Audit — pending / blocked / 통계", ""]

    # pending breakdown
    pending_a = [p for p in pending if p["tier"] == "A"]
    pending_n = [p for p in pending if p["tier"] == "N"]
    lines.append(f"### Pending ({len(pending)}편)")
    lines.append(f"- [A] anchor pending: {len(pending_a)}편")
    if pending_a:
        labels = [p["canonical"] for p in pending_a[:20]]
        lines.append(f"  {', '.join(labels)}{'  …' if len(pending_a) > 20 else ''}")
    lines.append(f"- [N] non-anchor pending: {len(pending_n)}편")
    if pending_n:
        labels = [p["canonical"] for p in pending_n[:10]]
        lines.append(f"  {', '.join(labels)}{'  …' if len(pending_n) > 10 else ''}")
    lines.append("")

    # curation 대기
    if curation:
        lines.append(f"### Curation 대기 ([?]) — {len(curation)}편")
        labels = [p["canonical"] for p in curation[:20]]
        lines.append(f"  {', '.join(labels)}{'  …' if len(curation) > 20 else ''}")
        lines.append("")

    # policy blocked
    lines.append(f"### Policy blocked — {len(blocked)}편")
    if blocked:
        for p in blocked:
            step = p["frontmatter"].get("policy_fallback_step", "?")
            lines.append(f"  - {p['canonical']} (step {step})")
    else:
        lines.append("  없음")
    lines.append("")

    # 미사용 분석 paper
    unused = [
        p for p in done
        if (p["frontmatter"].get("citation_state") or {}).get("use_count_in_output", 0) == 0
    ]
    lines.append(f"### 미사용 분석 paper (use_count=0) — {len(unused)}편")
    if unused:
        for p in unused:
            lines.append(f"  - {_format_paper_label(p)}")
    lines.append("")

    # axis 분포
    axis_count: dict[str, int] = defaultdict(int)
    for p in done:
        for a in (p["frontmatter"].get("axis_tags") or []):
            axis_count[a] += 1
    if done:
        lines.append("### Axis 분포 (분석 완료 paper)")
        for axis, n in sorted(axis_count.items(), key=lambda x: -x[1]):
            lines.append(f"  - {axis}: {n}")
        lines.append("")

    # 연령대 분포 (anchor [A] 한정 — 이 정보가 표기된 대상)
    anchor_done = [p for p in done if p["tier"] == "A"]
    age_total = sum(1 for p in anchor_done if p["frontmatter"].get("age_group"))
    if age_total > 0:
        age_combo_count: dict[str, int] = defaultdict(int)  # 조합 그대로
        age_atomic_count: dict[str, int] = defaultdict(int)  # 분해된 단일 연령
        age_papers: dict[str, list[dict]] = defaultdict(list)
        for p in anchor_done:
            ag = p["frontmatter"].get("age_group") or ""
            if not ag:
                continue
            age_combo_count[ag] += 1
            age_papers[ag].append(p)
            for atom in [a.strip() for a in ag.split("+")]:
                age_atomic_count[atom] += 1

        lines.append(f"### 연령대 분포 (anchor [A] 분석 완료 — {age_total}편)")
        # atomic 분포 (각 연령대가 몇 편에 등장하는지, 중복 포함)
        order = ["early childhood", "middle childhood", "Adolescence", "해당없음"]
        atomic_lines = []
        for k in order:
            if k in age_atomic_count:
                atomic_lines.append(f"{k} {age_atomic_count[k]}")
        # 알려지지 않은 라벨은 끝에
        for k, n in sorted(age_atomic_count.items(), key=lambda x: -x[1]):
            if k not in order:
                atomic_lines.append(f"{k} {n}")
        if atomic_lines:
            lines.append("  - atomic 빈도 (조합 분해, 중복 포함): " + " · ".join(atomic_lines))
        # 조합별 paper 리스트
        for combo, n in sorted(age_combo_count.items(), key=lambda x: -x[1]):
            labels = [_format_paper_label(p) for p in age_papers[combo]]
            lines.append(f"  - {combo} ({n}편): {', '.join(labels)}")
        lines.append("")

    # 인접 논쟁 그래프
    vs_graph = []
    for p in done:
        vs_dict = p["index_fields"].get("vs") or {}
        for other, info in vs_dict.items():
            stance = info.get("stance", "?") if isinstance(info, dict) else str(info)
            # other의 분석 상태 판정 (canonical 정확 매칭이 어려울 수 있어 fuzzy)
            other_status = _find_paper_status(other, papers)
            mark = "[done]" if other_status == "done" else \
                   "[skeleton ★먼저 분석]" if other_status == "pending" else \
                   "[curation]" if other_status == "curation" else "[미수집]"
            vs_graph.append((p, other, stance, mark))
    if vs_graph:
        lines.append("### 인접 논쟁 그래프 (anchor done의 vs 관계)")
        # group by source paper
        by_source: dict[str, list[tuple]] = defaultdict(list)
        for p, other, stance, mark in vs_graph:
            by_source[_format_paper_label(p)].append((other, stance, mark))
        for src, edges in by_source.items():
            lines.append(f"  {src}")
            for other, stance, mark in edges:
                lines.append(f"    ── {stance} ── {other} {mark}")
        lines.append("")

    return "\n".join(lines)


def _find_paper_status(other_label: str, papers: list[dict]) -> str | None:
    """'Miyake_2000' 또는 'Miyake 2000' → papers 중에서 해당 status."""
    norm = re.sub(r"[\s_]+", "_", other_label).lower()
    for p in papers:
        canonical_lower = p["canonical"].lower()
        # author_year prefix 매칭
        if canonical_lower.startswith(norm):
            return p["status"]
        # 또는 canonical 내부에 author_year 패턴이 있는 경우
        m = re.match(r"^([a-z]+)_(\d{4})", norm)
        if m:
            author, year = m.groups()
            if author in canonical_lower and year in canonical_lower:
                return p["status"]
    return None


# ──────────────────────────────────────────────────────────────────────
# 헤더 + main
# ──────────────────────────────────────────────────────────────────────

def render_header(papers: list[dict], project: str, output_data: dict) -> str:
    n_total = len(papers)
    n_done = sum(1 for p in papers if p["status"] == "done")
    n_pending = sum(1 for p in papers if p["status"] == "pending")
    n_curation = sum(1 for p in papers if p["status"] == "curation")
    n_blocked = sum(1 for p in papers if p["frontmatter"].get("policy_blocked"))
    n_output_files = output_data.get("files_scanned", 0)
    n_citations = len(output_data.get("citations", []))
    n_unmatched = len(output_data.get("unmatched_citations", []))

    lines = [
        f"# Papers Index — {project}",
        "",
        "> **자동 생성됨** by `scripts/build_index.py` — 사용자 직접 편집 금지.",
        "> 모든 paper 데이터의 SSOT는 각 `[X][D].{canonical}.md` frontmatter의 `index_fields`.",
        "> INDEX.md는 그것의 view일 뿐이며 다음 빌드에서 덮어써짐.",
        "",
        f"last_synced: {now_iso()}",
        f"papers: {n_total}편 (analyzed: {n_done} / pending: {n_pending} / curation: {n_curation} / blocked: {n_blocked})",
        f"output: {n_output_files}개 파일 스캔 · 매칭 인용 {n_citations}건 · 미매칭 {n_unmatched}건",
        "",
        "**3 view 구조**:",
        "- A — §Section 매핑 (A1 계획 / A2 실제 / A3 불일치)",
        "- B — 분석 완료 paper별 entry (discovery·counter-arg)",
        "- C — Audit (pending·blocked·통계·인접 논쟁)",
        "",
        "연령대 약자 (anchor [A] paper에 표기): EC=early childhood / MC=middle childhood / AD=Adolescence / —=해당없음",
        "",
    ]
    return "\n".join(lines)


def build_index(project: str, repo: Path | None = None,
                 writeback: bool = True) -> Path:
    if repo is None:
        repo = SCRIPTS_DIR.parent
    proj = project_root(repo, project)
    if not proj.exists():
        raise SystemExit(f"❌ 프로젝트 없음: {proj}")

    papers = collect_papers(analyzed_dir(proj))
    flow_sections = parse_flow_sections(flow_md_path(proj))
    output_data = parse_output(output_dir(proj), papers)

    # citation_state 자동 갱신 (use_count·cited_in_sections)
    if writeback and output_data["files_scanned"] > 0:
        n_updated = writeback_citation_state(analyzed_dir(proj), papers, output_data)
        if n_updated > 0:
            # frontmatter 갱신 후 다시 collect (use_count 반영용)
            papers = collect_papers(analyzed_dir(proj))

    parts = [
        render_header(papers, project, output_data),
        render_section_a(papers, flow_sections, output_data),
        render_section_b(papers),
        render_section_c(papers),
    ]
    output_text = "\n".join(parts).rstrip() + "\n"

    out_path = index_path(proj)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output_text, encoding="utf-8")
    return out_path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", help="프로젝트명 (projects/{project}/)")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--no-writeback", action="store_true",
                        help="paper frontmatter citation_state 자동 갱신 비활성")
    args = parser.parse_args(argv)

    out = build_index(args.project, writeback=not args.no_writeback)
    if not args.quiet:
        print(f"✅ INDEX.md 생성: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
