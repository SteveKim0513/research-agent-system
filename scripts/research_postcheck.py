#!/usr/bin/env python3
"""
RESEARCH post-condition verifier (v3).

Verifies 4-stage pipeline invariants for RESEARCH mode=search cards in project {P}:

  Stage A (.research-raw/RESEARCH-NNN.json)     — MCP raw cache
  Stage B (.translations/RESEARCH-NNN.md)       — Korean abstract translations
  Stage C (.curation/RESEARCH-NNN.md)           — curated 6-category block per card
  Stage D (consensus-results.md)                — assembled from .curation/*.md

Plus work-plan.md RESEARCH cards (mode=search) must be 1:1 with each stage's files.

Fails fast (exit 1) with clear diagnostic so orchestrator cannot report success
while any invariant is broken.

Usage:
    python3 scripts/research_postcheck.py {PROJECT_NAME}
"""
from __future__ import annotations

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


def fail(msg: str) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def card_ids_in_work_plan(wp_path: Path) -> set[str]:
    """Collect RESEARCH card IDs whose body carries `**mode**: search`."""
    if not wp_path.exists():
        return set()
    text = wp_path.read_text(encoding="utf-8")
    ids = set()
    for m in re.finditer(r"###\s+\[(RESEARCH-\d+)\](.*?)(?=\n### \[|\Z)", text, re.DOTALL):
        cid, body = m.group(1), m.group(2)
        mode_m = re.search(r"\*\*mode\*\*:\s*(\w+)", body)
        mode = mode_m.group(1).strip() if mode_m else "search"
        if mode == "search":
            ids.add(cid)
    return ids


def card_ids_from_files(dir_path: Path, suffix: str) -> set[str]:
    if not dir_path.exists():
        return set()
    ids = set()
    for p in dir_path.iterdir():
        if not p.name.endswith(suffix):
            continue
        m = re.match(r"(RESEARCH-\d+)", p.name)
        if m:
            ids.add(m.group(1))
    return ids


def check_curation_block(md_text: str, card_id: str) -> list[str]:
    diag = []
    for cat in REQUIRED_CATEGORIES:
        if cat not in md_text:
            diag.append(f"  {card_id}: missing category header '{cat}'")
    action_lines = re.findall(r"^\s*-\s*\[[ x]\]\s+", md_text, flags=re.MULTILINE)
    if len(action_lines) < ACTION_ITEMS_MIN:
        diag.append(
            f"  {card_id}: action items {len(action_lines)} < {ACTION_ITEMS_MIN} required"
        )
    if "번역 대기" in md_text:
        diag.append(f"  {card_id}: contains `번역 대기` placeholder")
    return diag


def check_raw_cache(json_path: Path) -> str | None:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"  {json_path.name}: JSON parse fail — {exc}"
    if not data.get("card_id"):
        return f"  {json_path.name}: missing card_id field"
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
    if len(sys.argv) != 2:
        fail("usage: research_postcheck.py {PROJECT_NAME}")

    project = sys.argv[1]
    proj = ROOT / "projects" / project
    if not proj.exists():
        fail(f"project dir not found: {proj}")

    papers = proj / "papers"
    raw_dir = papers / ".research-raw"
    trans_dir = papers / ".translations"
    curation_dir = papers / ".curation"
    results_md = papers / "consensus-results.md"
    wp_md = proj / "work-plan.md"

    wp_cards = card_ids_in_work_plan(wp_md)
    raw_cards = card_ids_from_files(raw_dir, ".json")
    trans_cards = card_ids_from_files(trans_dir, ".md")
    cur_cards = card_ids_from_files(curation_dir, ".md")

    if not wp_cards:
        fail("work-plan.md에 RESEARCH mode=search 카드가 없음")

    missing_raw = wp_cards - raw_cards
    missing_trans = wp_cards - trans_cards
    missing_cur = wp_cards - cur_cards

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
    for p in sorted(raw_dir.glob("RESEARCH-*.json")):
        err = check_raw_cache(p)
        if err:
            raw_errors.append(err)
    if raw_errors:
        print(f"❌ Stage A raw cache 문제 {len(raw_errors)}건:", file=sys.stderr)
        for e in raw_errors[:10]:
            print(e, file=sys.stderr)
        sys.exit(1)

    trans_errors = []
    for p in sorted(trans_dir.glob("RESEARCH-*.md")):
        err = check_translation(p)
        if err:
            trans_errors.append(err)
    if trans_errors:
        print(f"❌ Stage B translation 문제 {len(trans_errors)}건:", file=sys.stderr)
        for e in trans_errors[:10]:
            print(e, file=sys.stderr)
        sys.exit(1)

    cur_errors = []
    for p in sorted(curation_dir.glob("RESEARCH-*.md")):
        card_id = re.match(r"(RESEARCH-\d+)", p.name).group(1)
        diag = check_curation_block(p.read_text(encoding="utf-8"), card_id)
        cur_errors.extend(diag)
    if cur_errors:
        print(f"❌ Stage C curation 문제 {len(cur_errors)}건:", file=sys.stderr)
        for e in cur_errors[:15]:
            print(e, file=sys.stderr)
        sys.exit(1)

    if not results_md.exists():
        fail(f"{results_md.name} 없음 (Stage D 미수행)")
    md_text = results_md.read_text(encoding="utf-8")
    if "번역 대기" in md_text:
        fail(f"{results_md.name}에 `번역 대기` 잔존")
    assembled = set(re.findall(r"^## \[(RESEARCH-\d+)\]", md_text, re.MULTILINE))
    missing_assembled = cur_cards - assembled
    if missing_assembled:
        fail(
            f"Stage D assembly 누락 {len(missing_assembled)}건 "
            "(.curation 있으나 consensus-results.md에 안 들어감): "
            + ", ".join(sorted(missing_assembled)[:10])
        )

    if "🏆" not in md_text or "PDF 다운로드 우선순위" not in md_text:
        fail(
            "consensus-results.md 끝에 누적 요약 섹션(🏆 최중요 발견 / 📥 PDF 우선순위) 누락"
        )

    print(
        f"✅ RESEARCH post-check 통과\n"
        f"   work-plan RESEARCH(search): {len(wp_cards)} · "
        f".research-raw: {len(raw_cards)} · "
        f".translations: {len(trans_cards)} · "
        f".curation: {len(cur_cards)} · "
        f"assembled: {len(assembled)}"
    )


if __name__ == "__main__":
    main()
