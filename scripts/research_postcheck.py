#!/usr/bin/env python3
"""
RESEARCH post-condition verifier (v4 — R-NN/H-NN 기반).

Verifies 4-stage pipeline invariants for the search pipeline in project {P}:

  Stage A (.research-raw/{HUNT-XXX or H-NN}.json)   — MCP raw cache
  Stage B (.translations/{HUNT-XXX or H-NN}.md)     — Korean abstract translations
  Stage C (.curation/{HUNT-XXX or H-NN}.md)         — curated 6-category block per hunt
  Stage D (papers/search-results/{stage}.md)        — assembled from .curation/*.md

work-plan.md는 폐기됨. 대신 검증 기준은:
  1. claim-extraction-{stage}.md / search-results/{stage}.md 에서 H-NN (또는 legacy HUNT-NNN) 추출
  2. 각 H-NN이 raw / translations / curation 에 모두 있어야 함
  3. search-results/{stage}.md 에 모두 assemble 되어 있어야 함

Fails fast (exit 1) with clear diagnostic.

Usage:
    python3 scripts/research_postcheck.py {PROJECT_NAME} [--stage flow|research-gap]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_CATEGORIES = [
    "최우선",             # 🎯
    "보조",               # 🟢
    "Steelman",           # 🔴
    "발달",               # 🌏
    "방법론",             # ⚙️
    "Cross-RESEARCH",     # 🔗
]

ACTION_ITEMS_MIN = 3

# 카드 ID 패턴: 신규 H-NN, R-NN + legacy HUNT-NNN, RESEARCH-NNN 모두 허용
HUNT_ID_PAT = re.compile(r"\b(H-\d+|HUNT-\d+|R-\d+|RESEARCH-\d+)\b")


def fail(msg: str) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def hunt_ids_in_search_results(path: Path) -> set[str]:
    """search-results/{stage}.md 또는 legacy consensus-results.md에서 H-NN/HUNT-NNN/R-NN/RESEARCH-NNN 추출."""
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    return set(HUNT_ID_PAT.findall(text))


def hunt_ids_in_claim_extraction(path: Path) -> set[str]:
    """claim-extraction-{stage}.md에서 H-NN/R-NN 추출 (search 큐 + R 항목)."""
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    return set(HUNT_ID_PAT.findall(text))


def hunt_ids_from_files(dir_path: Path, suffix: str) -> set[str]:
    """파일명 prefix로 H-NN/HUNT-NNN 추출 (예: H-01.json, HUNT-001.md)."""
    if not dir_path.exists():
        return set()
    ids = set()
    for p in dir_path.iterdir():
        if not p.name.endswith(suffix):
            continue
        m = HUNT_ID_PAT.match(p.name)
        if m:
            ids.add(m.group(1))
    return ids


def check_curation_block(md_text: str, hunt_id: str) -> list[str]:
    diag = []
    for cat in REQUIRED_CATEGORIES:
        if cat not in md_text:
            diag.append(f"  {hunt_id}: missing category header '{cat}'")
    action_lines = re.findall(r"^\s*-\s*\[[ x]\]\s+", md_text, flags=re.MULTILINE)
    if len(action_lines) < ACTION_ITEMS_MIN:
        diag.append(
            f"  {hunt_id}: action items {len(action_lines)} < {ACTION_ITEMS_MIN} required"
        )
    if "번역 대기" in md_text:
        diag.append(f"  {hunt_id}: contains `번역 대기` placeholder")
    return diag


def check_raw_cache(json_path: Path) -> str | None:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"  {json_path.name}: JSON parse fail — {exc}"
    if not (data.get("hunt_id") or data.get("card_id")):
        return f"  {json_path.name}: missing hunt_id/card_id field"
    papers = data.get("papers") or []
    if not papers:
        return f"  {json_path.name}: empty papers[]"
    missing_abs = sum(1 for p in papers if not p.get("abstract"))
    if missing_abs and missing_abs == len(papers):
        return f"  {json_path.name}: all {len(papers)} papers missing abstract"
    return None


def check_translation(md_path: Path) -> str | None:
    text = md_path.read_text(encoding="utf-8")
    if "번역 대기" in text:
        return f"  {md_path.name}: contains `번역 대기`"
    if not re.search(r"^\s*>\s+", text, flags=re.MULTILINE):
        return f"  {md_path.name}: no `> ` quote blocks found"
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--stage", default="flow",
                        help="단계명 (flow | research-gap). 기본 flow.")
    args = parser.parse_args()

    project = args.project
    stage = args.stage
    proj = ROOT / "projects" / project
    if not proj.exists():
        fail(f"project dir not found: {proj}")

    papers = proj / "papers"
    raw_dir = papers / ".research-raw"
    trans_dir = papers / ".translations"
    curation_dir = papers / ".curation"

    # search-results/{stage}.md (신규) → 없으면 legacy consensus-results.md fallback
    results_md = papers / "search-results" / f"{stage}.md"
    if not results_md.exists():
        legacy = papers / "consensus-results.md"
        if legacy.exists():
            results_md = legacy

    # claim-extraction-{stage}.md 에서 expected H-NN 추출 (work-plan 대체 SSOT)
    ce_path = proj / stage / f"claim-extraction-{stage}.md"
    expected_ids = hunt_ids_in_claim_extraction(ce_path)
    # search-results/{stage}.md 에 assemble된 ID와 union하여 SSOT 구성
    if results_md.exists():
        expected_ids = expected_ids | hunt_ids_in_search_results(results_md)

    raw_ids = hunt_ids_from_files(raw_dir, ".json")
    trans_ids = hunt_ids_from_files(trans_dir, ".md")
    cur_ids = hunt_ids_from_files(curation_dir, ".md")

    if not expected_ids and not raw_ids:
        fail(f"H-NN/HUNT-NNN/R-NN 카드를 찾을 수 없음 "
             f"(claim-extraction-{stage}.md / search-results/{stage}.md / .research-raw/ 모두 비어 있음)")

    # expected가 비어있으면 raw_ids를 SSOT로 사용 (early-stage)
    ssot = expected_ids if expected_ids else raw_ids

    missing_raw = ssot - raw_ids
    missing_trans = ssot - trans_ids
    missing_cur = ssot - cur_ids

    if missing_raw:
        fail(
            f"Stage A (.research-raw) 누락 {len(missing_raw)}건: "
            + ", ".join(sorted(missing_raw)[:10])
        )
    if missing_trans:
        fail(
            f"Stage B (.translations) 누락 {len(missing_trans)}건: "
            + ", ".join(sorted(missing_trans)[:10])
        )
    if missing_cur:
        fail(
            f"Stage C (.curation) 누락 {len(missing_cur)}건: "
            + ", ".join(sorted(missing_cur)[:10])
        )

    raw_errors = []
    for p in sorted(raw_dir.glob("*.json")):
        if not HUNT_ID_PAT.match(p.name):
            continue
        err = check_raw_cache(p)
        if err:
            raw_errors.append(err)
    if raw_errors:
        print(f"❌ Stage A raw cache 문제 {len(raw_errors)}건:", file=sys.stderr)
        for e in raw_errors[:10]:
            print(e, file=sys.stderr)
        sys.exit(1)

    trans_errors = []
    for p in sorted(trans_dir.glob("*.md")):
        if not HUNT_ID_PAT.match(p.name):
            continue
        err = check_translation(p)
        if err:
            trans_errors.append(err)
    if trans_errors:
        print(f"❌ Stage B translation 문제 {len(trans_errors)}건:", file=sys.stderr)
        for e in trans_errors[:10]:
            print(e, file=sys.stderr)
        sys.exit(1)

    cur_errors = []
    for p in sorted(curation_dir.glob("*.md")):
        m = HUNT_ID_PAT.match(p.name)
        if not m:
            continue
        diag = check_curation_block(p.read_text(encoding="utf-8"), m.group(1))
        cur_errors.extend(diag)
    if cur_errors:
        print(f"❌ Stage C curation 문제 {len(cur_errors)}건:", file=sys.stderr)
        for e in cur_errors[:15]:
            print(e, file=sys.stderr)
        sys.exit(1)

    if not results_md.exists():
        fail(f"search-results/{stage}.md (또는 legacy consensus-results.md) 없음 (Stage D 미수행)")
    md_text = results_md.read_text(encoding="utf-8")
    if "번역 대기" in md_text:
        fail(f"{results_md.name}에 `번역 대기` 잔존")
    assembled = hunt_ids_in_search_results(results_md)
    missing_assembled = cur_ids - assembled
    if missing_assembled:
        fail(
            f"Stage D assembly 누락 {len(missing_assembled)}건 "
            f"(.curation 있으나 {results_md.name}에 안 들어감): "
            + ", ".join(sorted(missing_assembled)[:10])
        )

    if "🏆" not in md_text or "PDF 다운로드 우선순위" not in md_text:
        fail(
            f"{results_md.name} 끝에 누적 요약 섹션(🏆 최중요 발견 / 📥 PDF 우선순위) 누락"
        )

    print(
        f"✅ RESEARCH post-check 통과 (stage={stage})\n"
        f"   expected: {len(ssot)} · "
        f".research-raw: {len(raw_ids)} · "
        f".translations: {len(trans_ids)} · "
        f".curation: {len(cur_ids)} · "
        f"assembled: {len(assembled)}"
    )


if __name__ == "__main__":
    main()
