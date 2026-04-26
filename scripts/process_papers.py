#!/usr/bin/env python3
"""
process_papers.py — v3.1: PDF 단일 패스 + consensus 매핑 + 분류 + 파일명 prefix.

이전 v3.0은 추출만 수행하고 anchor_picker.py가 별도 단계로 분류했음.
v3.1에서는 1단계에서 consensus lookup + 분류 + frontmatter 채움까지 통합.

산출물:
- collected/{Author_Year_kw}.pdf       (prefix 없음 — 외부 도구 호환)
- markdown/{Author_Year_kw}.md         (PDF 본문 캐시, prefix 없음)
- analyzed/[X].{Author_Year_kw}.md     (분석 skeleton + frontmatter)
   X ∈ {A, N, ?}:
     [A] = anchor (consensus 🎯 최우선 OR 🔴 Steelman)
     [N] = non-anchor (그 외 카테고리)
     [?] = consensus 매칭 없음 (사용자 직접 추가 — MANUAL curation 대기)
- .quarantine/empty/, .quarantine/corrupt/

→ paper-analyst는 파일명 prefix [A]/[N]/[?]를 읽고 즉시 분석 깊이 분기.
   [?] paper는 먼저 MANUAL curation (LLM이 (a)(b)(c) 주석 + 카테고리 생성)
   → consensus-results.md 재조립 → 그 후 prefix 갱신 + 분석.

CLI:
    python3 scripts/process_papers.py <project> [--workers=N] [--dry-run] [--limit=N]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import traceback
from datetime import datetime
from hashlib import sha256
from multiprocessing import Pool
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import normalize_filename as nf  # noqa


try:
    import pdfplumber
except ImportError:
    print("process_papers.py: pdfplumber 필요. `pip install pdfplumber`", file=sys.stderr)
    sys.exit(2)


# ──────────────────────────────────────────────────────────────────────
# 상수
# ──────────────────────────────────────────────────────────────────────

DEFAULT_WORKERS = 8


# ──────────────────────────────────────────────────────────────────────
# Path helpers
# ──────────────────────────────────────────────────────────────────────

def papers_root(project_root: Path) -> Path:
    return project_root / "papers"


def candidates_dir(project_root: Path) -> Path:
    return papers_root(project_root) / "candidates"


def collected_dir(project_root: Path) -> Path:
    return papers_root(project_root) / "collected"


def markdown_dir(project_root: Path) -> Path:
    return papers_root(project_root) / "markdown"


def analyzed_dir(project_root: Path) -> Path:
    return papers_root(project_root) / "analyzed"


def quarantine_dir(project_root: Path, kind: str) -> Path:
    return papers_root(project_root) / ".quarantine" / kind


def consensus_path(project_root: Path) -> Path:
    return papers_root(project_root) / "consensus-results.md"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ──────────────────────────────────────────────────────────────────────
# Consensus 매핑 (v3.1)
# ──────────────────────────────────────────────────────────────────────

_CONSENSUS_RESEARCH_RE = re.compile(r"^##\s+\[(?:RESEARCH|MANUAL)-(\d+)\]")
_CONSENSUS_CATEGORY_RE = re.compile(
    r"^##\s+(🎯 최우선|🟢 보조|🔴 Steelman|🌏 발달·횡문화|⚙️ 방법론 비판|🔗 Cross-RESEARCH)"
)
_CONSENSUS_PAPER_RE = re.compile(
    r"^#(\d+)\s+\*\*([^*]+)\s+\((\d{4})\)\*\*\s+—\s+\[([^\]]+)\]\(([^)]+)\)"
    r"(?:\s*·\s*([^,]+),\s*(\d+(?:[,.]\d+)*)회\s*인용\.?)?",
)

_ANCHOR_CATEGORIES = ("🎯 최우선", "🔴 Steelman")


def _norm_author_for_consensus(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\bet\s+al\.?", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"\s*&\s*|\s+and\s+", " ", s, flags=re.IGNORECASE)
    parts = s.split()
    return parts[0].lower() if parts else ""


def parse_consensus(consensus_md: Path) -> dict:
    """consensus-results.md → {(author_lower, year): consensus_entry}.

    한 paper가 여러 카드에 등장하면 cross_research_count++, 더 강한 카테고리 유지.
    """
    if not consensus_md.exists():
        return {}
    text = consensus_md.read_text(encoding="utf-8")
    entries: dict[tuple[str, str], dict] = {}
    cur_card = None
    cur_cat = None

    cat_priority = {
        "🎯 최우선": 30, "🔴 Steelman": 30, "🟢 보조": 15,
        "🌏 발달·횡문화": 5, "⚙️ 방법론 비판": 5, "🔗 Cross-RESEARCH": 0,
    }

    for raw in text.split("\n"):
        line = raw.strip()
        m = _CONSENSUS_RESEARCH_RE.match(line)
        if m:
            cur_card = f"CARD-{int(m.group(1)):03d}"
            cur_cat = None
            continue
        m = _CONSENSUS_CATEGORY_RE.match(line)
        if m:
            cur_cat = m.group(1)
            continue
        m = _CONSENSUS_PAPER_RE.match(line)
        if m:
            _, authors, year, _, _, journal, citations_str = m.groups()
            citations = 0
            if citations_str:
                try:
                    citations = int(citations_str.replace(",", "").replace(".", ""))
                except ValueError:
                    citations = 0
            key = (_norm_author_for_consensus(authors), year)
            existing = entries.get(key)
            if existing:
                existing["cross_research_count"] += 1
                if cur_card:
                    existing["research_cards"].add(cur_card)
                if cat_priority.get(cur_cat or "", 0) > cat_priority.get(existing["category"] or "", 0):
                    existing["category"] = cur_cat
            else:
                entries[key] = {
                    "year": year,
                    "journal": (journal or "").strip(),
                    "citations": citations,
                    "category": cur_cat,
                    "research_cards": {cur_card} if cur_card else set(),
                    "cross_research_count": 1,
                }
    return entries


def _author_year_from_canonical(canonical: str) -> tuple[str, str]:
    parts = canonical.split("_")
    if len(parts) < 2:
        return "", ""
    return parts[0].lower(), parts[1]


def classify_paper(canonical: str, consensus_entries: dict) -> tuple[str, dict | None]:
    """canonical → ('A' | 'N' | '?', consensus_entry | None).

    A = anchor (🎯/🔴), N = non-anchor (그 외 매칭), ? = consensus 매칭 없음
    """
    author, year = _author_year_from_canonical(canonical)
    if not author or not year:
        return "?", None
    entry = consensus_entries.get((author, year))
    if entry is None:
        return "?", None
    if entry.get("category") in _ANCHOR_CATEGORIES:
        return "A", entry
    return "N", entry


def build_analyzed_skeleton(
    canonical: str,
    tier_letter: str,
    consensus_entry: dict | None,
) -> str:
    """analyzed/[X].{name}.md 초기 본문 생성 (frontmatter + placeholder)."""
    anchor = (tier_letter == "A")
    needs_curation = (tier_letter == "?")

    fm_lines = ["---"]
    fm_lines.append("status: collected")
    fm_lines.append(f"anchor: {str(anchor).lower()}")
    fm_lines.append("critique_target: false")
    fm_lines.append("axis_tags: []")
    if consensus_entry:
        cat = consensus_entry.get("category") or ""
        fm_lines.append(f'consensus_category: "{cat}"')
        fm_lines.append(f"cross_research_count: {consensus_entry.get('cross_research_count', 0)}")
        fm_lines.append(f"citations: {consensus_entry.get('citations', 0)}")
        journal = consensus_entry.get("journal") or ""
        if journal:
            fm_lines.append(f'journal: "{journal}"')
    else:
        fm_lines.append("consensus_category: null")
        fm_lines.append("cross_research_count: 0")
        fm_lines.append("citations: 0")
    if needs_curation:
        fm_lines.append("needs_consensus_curation: true   # MANUAL curation 대기")
    fm_lines.append("last_analyzed: null")
    fm_lines.append("based_on:")
    fm_lines.append("  flow_md_hash: null")
    fm_lines.append("  markdown_hash: null")
    fm_lines.append("artifacts:")
    fm_lines.append(f"  pdf: papers/collected/{canonical}.pdf")
    fm_lines.append(f"  markdown: papers/markdown/{canonical}.md")
    fm_lines.append("citation_state:")
    fm_lines.append("  use_count_in_output: 0")
    fm_lines.append("  direct_quotes_used: []")
    fm_lines.append("  paraphrase_count: 0")
    fm_lines.append("user_overrides: null")
    fm_lines.append("rejection_reason: null")
    fm_lines.append("---")

    author, year = _author_year_from_canonical(canonical)
    body = f"\n# {author.capitalize()} ({year})\n\n_(분석 대기 — paper-analyst 호출 필요)_\n"
    return "\n".join(fm_lines) + body


def file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def text_hash(text: str) -> str:
    return f"sha256:{sha256(text.encode('utf-8')).hexdigest()}"


# ──────────────────────────────────────────────────────────────────────
# PDF 추출
# ──────────────────────────────────────────────────────────────────────

YEAR_RE = re.compile(r"\b(19[6-9]\d|20[0-3]\d)\b")

_HEADER_TRASH = (
    "doi.org", "doi:", "©", "copyright", "all rights reserved",
    "received", "accepted", "published", "issn", "available online",
    "contents lists available", "sciencedirect", "elsevier", "springer",
    "wiley", "journal homepage", "www.", "http://", "https://",
    "abstract", "keywords",
    "full length article", "review article", "research article",
    "original research", "original article", "short communication",
    "special issue", "letters", "perspective", "commentary",
    "open access", "creative commons",
)

_JOURNAL_HEADER_RE = re.compile(
    r"^[A-Za-z]+\d+\(\d{4}\)\d+[–\-]\d+$|"
    r"^[A-Za-z]+\d+\(\d{4}\)\d+$|"
    r"^vol(?:ume)?\.?\s*\d+",
    re.IGNORECASE,
)

_ARTICLE_START_RE = re.compile(r"^(a|an|the)\s+", re.IGNORECASE)
_FUNCTION_WORDS = {
    "of", "the", "and", "or", "in", "on", "at", "to", "for", "by", "with",
    "is", "are", "was", "were", "be", "been", "being", "from", "that",
    "this", "these", "those", "an", "as", "it", "its", "their",
}


def _is_header_trash(line: str) -> bool:
    low = line.lower()
    if any(s in low for s in _HEADER_TRASH):
        return True
    if " " not in line and len(line) > 30 and any(c.isalpha() for c in line):
        return True
    if _JOURNAL_HEADER_RE.match(line):
        return True
    return False


def _is_alphabetic_line(line: str, min_alpha_ratio: float = 0.5) -> bool:
    if not line:
        return False
    alpha = sum(1 for c in line if c.isalpha())
    return alpha >= max(10, len(line) * min_alpha_ratio)


def _has_min_words(line: str, n: int = 3) -> bool:
    return len([w for w in line.split() if w]) >= n


def _is_author_like(line: str) -> bool:
    if not line or len(line) > 250:
        return False
    if _is_header_trash(line):
        return False
    if _ARTICLE_START_RE.match(line):
        return False
    if not re.match(r"^\s*[A-ZÀ-Ý]", line):
        return False

    words = [w.strip(".,;:") for w in line.split() if w.strip()]
    if not words:
        return False

    name_words = [
        w for w in words
        if len(w) >= 2 and w[0].isupper() and any(c.islower() for c in w)
    ]
    func_words = [w.lower() for w in words if w.lower() in _FUNCTION_WORDS]

    if len(func_words) >= max(2, len(words) * 0.25):
        return False
    if len(name_words) >= 2:
        return True
    return False


def _find_author_line_idx(lines: list[str]) -> int:
    for i, raw in enumerate(lines[:40]):
        if i < 3:
            continue
        line = raw.strip()
        if not line or _is_header_trash(line):
            continue
        if _is_author_like(line):
            return i
    return -1


def _extract_title(first_page: str) -> str:
    if not first_page:
        return ""
    lines = first_page.split("\n")
    author_idx = _find_author_line_idx(lines)
    if author_idx < 0:
        # author 못 찾으면 forward scan
        return _extract_title_forward(first_page)

    title_lines: list[str] = []
    for j in range(author_idx - 1, -1, -1):
        line = lines[j].strip()
        if not line:
            if title_lines:
                break
            continue
        if _is_header_trash(line):
            if title_lines:
                break
            continue
        if len(line) < 5 or re.match(r"^[\d\W]+$", line):
            if title_lines:
                break
            continue
        if not _has_min_words(line, 2):
            if title_lines and _has_min_words(line, 1) and _is_alphabetic_line(line, 0.7):
                title_lines.insert(0, line)
                continue
            if title_lines:
                break
            continue
        if not _is_alphabetic_line(line, 0.6):
            if title_lines:
                break
            continue
        title_lines.insert(0, line)
        if sum(len(l) for l in title_lines) > 250:
            break
    return " ".join(title_lines).strip().rstrip(",").strip()


def _extract_title_forward(first_page: str) -> str:
    lines = first_page.split("\n")
    title_lines: list[str] = []
    in_title = False
    for raw in lines[:50]:
        line = raw.strip()
        if not line:
            if in_title:
                break
            continue
        if _is_header_trash(line):
            if in_title:
                break
            continue
        if len(line) < 15 or re.match(r"^[\d\W]+$", line):
            if in_title:
                break
            continue
        if not _has_min_words(line, 3):
            if in_title:
                break
            continue
        if not _is_alphabetic_line(line, 0.6):
            if in_title:
                break
            continue
        title_lines.append(line)
        in_title = True
        if sum(len(l) for l in title_lines) > 250:
            break
    return " ".join(title_lines).strip().rstrip(",").strip()


def _extract_author(first_page: str, title: str) -> str:
    if not first_page:
        return ""
    lines = first_page.split("\n")
    idx = _find_author_line_idx(lines)
    if idx < 0:
        return ""
    line = lines[idx].strip()
    cleaned = re.sub(r"[\*†‡§¶]+", "", line)
    return cleaned.strip()


def _clean_author_first(author_line: str) -> str:
    s = author_line.strip()
    s = re.sub(r"\bet\s+al\.?", "", s, flags=re.IGNORECASE).strip()
    parts = re.split(r"\s*[,;]\s*|\s+(?:and|&)\s+", s, flags=re.IGNORECASE)
    first = parts[0].strip()
    first = re.sub(r"[\*†‡§¶]+", "", first)
    first = re.sub(r"\s+[a-z]$", "", first)
    return first.strip()


def _extract_year(first_page: str, filename: str) -> str:
    for source in (first_page[:2000], filename):
        for m in YEAR_RE.finditer(source):
            return m.group(0)
    return ""


def extract_pdf_text(pdf_path: Path) -> tuple[list[str], dict] | None:
    try:
        pages: list[str] = []
        meta: dict = {}
        with pdfplumber.open(pdf_path) as pdf:
            meta["pages_count"] = len(pdf.pages)
            try:
                pmeta = pdf.metadata or {}
                meta["pdf_title"] = (pmeta.get("Title") or "").strip()
                meta["pdf_author"] = (pmeta.get("Author") or "").strip()
            except Exception:
                meta["pdf_title"] = ""
                meta["pdf_author"] = ""
            for page in pdf.pages:
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""
                pages.append(text)
        return pages, meta
    except Exception:
        return None


def extract_metadata_from_body(pages: list[str], filename: str) -> dict:
    head = "\n".join(pages[:2]) if pages else ""
    title = _extract_title(head)
    author_raw = _extract_author(head, title)
    author = _clean_author_first(author_raw) if author_raw else ""
    year = _extract_year(head, filename)
    return {
        "title": title,
        "author": author,
        "author_raw": author_raw,
        "year": year,
    }


def render_markdown_cache(pages: list[str], meta: dict, source_pdf_relpath: str, content_hash: str) -> str:
    fm_lines = [
        "---",
        f"source_pdf: {source_pdf_relpath}",
        f"pages: {meta.get('pages_count', len(pages))}",
        f"extracted_at: {now_iso()}",
        f"extraction_lib: pdfplumber",
        f"content_hash: {content_hash}",
    ]
    if meta.get("pdf_title"):
        fm_lines.append(f"pdf_title: {json.dumps(meta['pdf_title'], ensure_ascii=False)}")
    if meta.get("pdf_author"):
        fm_lines.append(f"pdf_author: {json.dumps(meta['pdf_author'], ensure_ascii=False)}")
    fm_lines.append("---")
    fm = "\n".join(fm_lines) + "\n\n"

    body = []
    for i, text in enumerate(pages, start=1):
        body.append(f"<!-- page: {i} -->")
        body.append((text or "").strip())
        body.append("")
    return fm + "\n".join(body).strip() + "\n"


# ──────────────────────────────────────────────────────────────────────
# 단일 PDF 처리 (worker 함수 — multiprocessing-safe, 순수 데이터)
# ──────────────────────────────────────────────────────────────────────

def _process_pdf_worker(args: dict) -> dict:
    """multiprocessing worker. PDF 1편 → 처리 결과 dict.

    Worker는 파일을 *직접 옮기지 않음* — main 프로세스가 race 방지하며 처리.
    Worker는 추출 + 정규화 + markdown 본문 생성까지만.
    """
    pdf_path = Path(args["pdf_path"])
    project_root = Path(args["project_root"])

    result = {
        "pdf_name": pdf_path.name,
        "action": "unknown",
        "canonical": None,
        "source": None,
        "markdown_body": None,  # main이 markdown/{canonical}.md에 쓸 본문
        "pdf_size": 0,
        "reason": None,
    }

    try:
        size = pdf_path.stat().st_size
    except Exception:
        result["action"] = "missing"
        return result
    result["pdf_size"] = size

    if size < 100:
        result["action"] = "quarantine_empty"
        result["reason"] = f"size={size}"
        return result

    extracted = extract_pdf_text(pdf_path)
    if extracted is None:
        result["action"] = "quarantine_corrupt"
        result["reason"] = "pdfplumber 파싱 실패"
        return result

    pages, meta = extracted
    if not pages or not any(p.strip() for p in pages):
        result["action"] = "quarantine_empty"
        result["reason"] = "텍스트 0"
        return result

    body_meta = extract_metadata_from_body(pages, pdf_path.name)
    if not body_meta["title"] and meta.get("pdf_title"):
        body_meta["title"] = meta["pdf_title"]
    if not body_meta["author"] and meta.get("pdf_author"):
        body_meta["author"] = meta["pdf_author"]

    norm = nf.normalize_filename(
        pdf_path.name,
        title=body_meta["title"],
        author=body_meta["author"],
        year=body_meta["year"],
    )
    canonical = norm["canonical"]
    result["canonical"] = canonical
    result["source"] = norm["source"]

    # Worker는 PDF 이동 안 함 (main이 함). markdown 본문만 만들어둠 (PDF는 main에서 옮긴 뒤 collected/ 경로)
    pdf_relpath = f"papers/collected/{canonical}.pdf"
    pdf_hash = file_hash(pdf_path)
    md_body = render_markdown_cache(pages, meta, pdf_relpath, pdf_hash)

    result["action"] = "ready"
    result["markdown_body"] = md_body
    result["pdf_hash"] = pdf_hash
    return result


# ──────────────────────────────────────────────────────────────────────
# Main 프로세스 — 결과 집계 + 파일 시스템 변경
# ──────────────────────────────────────────────────────────────────────

def _move_to_quarantine(pdf_path: Path, project_root: Path, kind: str, reason: str = "") -> None:
    target_dir = quarantine_dir(project_root, kind)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / pdf_path.name
    if target.exists():
        target = target_dir / f"{pdf_path.stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    shutil.move(str(pdf_path), str(target))
    if reason:
        target.with_suffix(".reason.txt").write_text(reason, encoding="utf-8")


def collect(
    project_root: Path,
    *,
    workers: int = DEFAULT_WORKERS,
    dry_run: bool = False,
    limit: int | None = None,
) -> dict:
    cdir = candidates_dir(project_root)
    if not cdir.exists():
        return {"error": f"candidates/ 없음: {cdir}"}

    pdfs = sorted(cdir.glob("*.pdf"))
    if limit:
        pdfs = pdfs[:limit]
    total = len(pdfs)
    print(f"📂 candidates/: {total}편")
    if dry_run:
        print("🧪 DRY-RUN 모드 (파일 이동·작성 안 함)")

    if total == 0:
        return {"total": 0, "counters": {}}

    # 폴더 미리 생성
    if not dry_run:
        collected_dir(project_root).mkdir(parents=True, exist_ok=True)
        markdown_dir(project_root).mkdir(parents=True, exist_ok=True)
        analyzed_dir(project_root).mkdir(parents=True, exist_ok=True)

    # 1단계: 병렬 추출 (worker는 파일 이동 안 함)
    print(f"🔧 Worker {workers}개 병렬 추출 시작...")
    args_list = [{"pdf_path": str(p), "project_root": str(project_root)} for p in pdfs]
    if workers > 1:
        with Pool(processes=workers) as pool:
            results = pool.map(_process_pdf_worker, args_list)
    else:
        results = [_process_pdf_worker(a) for a in args_list]

    # 2단계: main 프로세스에서 consensus 로드 후 파일 시스템 변경
    print(f"📚 consensus-results.md 로드...")
    consensus_entries = parse_consensus(consensus_path(project_root))
    print(f"   {len(consensus_entries)}개 paper entry 매핑됨")

    counters = {
        "registered_anchor": 0,
        "registered_non_anchor": 0,
        "registered_needs_curation": 0,
        "dedup_removed": 0,
        "quarantine_empty": 0,
        "quarantine_corrupt": 0,
        "missing": 0,
    }
    by_source: dict[str, int] = {}
    classification_dist = {"A": 0, "N": 0, "?": 0}
    needs_curation_list: list[str] = []
    failures: list[str] = []

    for pdf, r in zip(pdfs, results):
        action = r["action"]
        try:
            if action == "missing":
                counters["missing"] += 1
                continue

            if action == "quarantine_empty":
                if not dry_run:
                    _move_to_quarantine(pdf, project_root, "empty", r.get("reason") or "")
                counters["quarantine_empty"] += 1
                continue

            if action == "quarantine_corrupt":
                if not dry_run:
                    _move_to_quarantine(pdf, project_root, "corrupt", r.get("reason") or "")
                counters["quarantine_corrupt"] += 1
                continue

            if action == "ready":
                canonical = r["canonical"]
                # dedup 검사: collected/{canonical}.pdf 이미 있으면 candidates 원본 삭제
                target_pdf = collected_dir(project_root) / f"{canonical}.pdf"
                if target_pdf.exists():
                    if not dry_run:
                        pdf.unlink()
                    counters["dedup_removed"] += 1
                    continue

                # consensus 분류 + tier prefix 결정
                tier_letter, entry = classify_paper(canonical, consensus_entries)
                classification_dist[tier_letter] += 1
                if tier_letter == "?":
                    needs_curation_list.append(canonical)

                # 파일 이동·작성
                if not dry_run:
                    # PDF: collected/{canonical}.pdf (prefix 없음)
                    shutil.move(str(pdf), str(target_pdf))
                    # markdown: markdown/{canonical}.md (prefix 없음)
                    md_path = markdown_dir(project_root) / f"{canonical}.md"
                    md_path.write_text(r["markdown_body"], encoding="utf-8")
                    # analyzed: analyzed/[X].{canonical}.md (tier prefix)
                    analyzed_filename = f"[{tier_letter}].{canonical}.md"
                    analyzed_path = analyzed_dir(project_root) / analyzed_filename
                    if not analyzed_path.exists():
                        skeleton = build_analyzed_skeleton(canonical, tier_letter, entry)
                        analyzed_path.write_text(skeleton, encoding="utf-8")

                if tier_letter == "A":
                    counters["registered_anchor"] += 1
                elif tier_letter == "N":
                    counters["registered_non_anchor"] += 1
                else:
                    counters["registered_needs_curation"] += 1

                src = r.get("source") or "?"
                by_source[src] = by_source.get(src, 0) + 1
                continue

        except Exception as e:
            failures.append(f"{pdf.name}: {e}")
            traceback.print_exc(file=sys.stderr)

    return {
        "total": total,
        "counters": counters,
        "classification": classification_dist,
        "needs_curation": needs_curation_list,
        "by_source": by_source,
        "failures": failures,
    }


# ──────────────────────────────────────────────────────────────────────
# 보고서
# ──────────────────────────────────────────────────────────────────────

def print_summary(summary: dict) -> None:
    if "error" in summary:
        print(f"❌ {summary['error']}")
        return
    if summary["total"] == 0:
        print("📂 candidates/ 비어 있음")
        return

    c = summary["counters"]
    cls = summary.get("classification", {})
    print()
    print("=" * 60)
    print(f"📊 process_papers 결과 (총 {summary['total']}편)")
    print("=" * 60)
    print(f"  ⭐ Anchor [A]            : {c.get('registered_anchor', 0)}")
    print(f"  📚 Non-anchor [N]        : {c.get('registered_non_anchor', 0)}")
    print(f"  ❓ Curation 대기 [?]     : {c.get('registered_needs_curation', 0)}  (consensus 매칭 없음)")
    print(f"  🔁 dedup 제거            : {c.get('dedup_removed', 0)}")
    print(f"  📦 빈 파일 격리          : {c.get('quarantine_empty', 0)}")
    print(f"  💥 손상 격리             : {c.get('quarantine_corrupt', 0)}")
    if c.get("missing"):
        print(f"  ❌ 누락                  : {c['missing']}")
    if summary.get("by_source"):
        print()
        print("📍 파일명 메타 출처별:")
        for src, n in summary["by_source"].items():
            print(f"     {src:20}: {n}")
    if summary.get("needs_curation"):
        print()
        print(f"⚠ Curation 필요 ({len(summary['needs_curation'])}편) — paper-analyst가 후속 처리:")
        for c_name in summary["needs_curation"][:5]:
            print(f"     - {c_name}")
        if len(summary["needs_curation"]) > 5:
            print(f"     ... +{len(summary['needs_curation']) - 5}편")
    if summary.get("failures"):
        print()
        print(f"❌ 실패 {len(summary['failures'])}편:")
        for f in summary["failures"][:5]:
            print(f"     {f}")
        if len(summary["failures"]) > 5:
            print(f"     ... +{len(summary['failures']) - 5}")
    print()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"병렬 worker 수 (기본 {DEFAULT_WORKERS})")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    repo = SCRIPTS_DIR.parent
    project_root = repo / "projects" / args.project
    if not project_root.exists():
        print(f"❌ 프로젝트 없음: {project_root}")
        return 1

    summary = collect(project_root, workers=args.workers,
                      dry_run=args.dry_run, limit=args.limit)
    print_summary(summary)
    return 0 if not summary.get("failures") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
