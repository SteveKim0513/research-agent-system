#!/usr/bin/env python3
"""
HUNT post-condition verifier (v2).

Verifies 4-stage HUNT pipeline invariants for project {P}:

  Stage A (.hunt-raw/HUNT-NNN.json)     — MCP raw cache
  Stage B (.translations/HUNT-NNN.md)   — Korean abstract translations
  Stage C (.curation/HUNT-NNN.md)       — curated 6-category block per HUNT
  Stage D (consensus-results.md)        — assembled from .curation/*.md

Plus work-plan.md HUNT cards must be 1:1 with each stage's files.

Fails fast (exit 1) with clear diagnostic so orchestrator cannot report HUNT
success while any invariant is broken.

Usage:
    python3 scripts/hunt_postcheck.py {PROJECT_NAME}
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 6 category headers required in each .curation/*.md file.
REQUIRED_CATEGORIES = [
    "최우선 인용",        # 🎯
    "보조 증거",          # 🟢
    "반론",               # 🔴 (may be "반론·Steelman" or just "Steelman")
    "발달",               # 🌏 (may be "발달·횡문화" or "Developmental")
    "방법론",             # ⚙️
    "Cross-HUNT",         # 🔗 (may say "Cross-HUNT 재등장")
]

ACTION_ITEMS_MIN = 3


def fail(msg: str) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def hunt_ids_in_work_plan(wp_path: Path) -> set[str]:
    if not wp_path.exists():
        return set()
    text = wp_path.read_text(encoding="utf-8")
    return set(re.findall(r"\[(HUNT-\d+)\]", text))


def hunt_ids_from_files(dir_path: Path, suffix: str) -> set[str]:
    if not dir_path.exists():
        return set()
    ids = set()
    for p in dir_path.iterdir():
        if not p.name.endswith(suffix):
            continue
        m = re.match(r"(HUNT-\d+)", p.name)
        if m:
            ids.add(m.group(1))
    return ids


def check_curation_block(md_text: str, hunt_id: str) -> list[str]:
    """Return list of diagnostic strings for a curation file (empty if clean)."""
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
    """Return error string, or None if OK."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"  {json_path.name}: JSON parse fail — {exc}"
    if not data.get("hunt_id"):
        return f"  {json_path.name}: missing hunt_id field"
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
    # expect at least one `> ` quote line
    if not re.search(r"^\s*>\s+", text, flags=re.MULTILINE):
        return f"  {md_path.name}: no `> ` quote blocks found"
    return None


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: hunt_postcheck.py {PROJECT_NAME}")

    project = sys.argv[1]
    proj = ROOT / "projects" / project
    if not proj.exists():
        fail(f"project dir not found: {proj}")

    papers = proj / "papers"
    raw_dir = papers / ".hunt-raw"
    trans_dir = papers / ".translations"
    curation_dir = papers / ".curation"
    results_md = papers / "consensus-results.md"
    wp_md = proj / "work-plan.md"

    # 1. HUNT ID sets from each stage
    wp_hunts = hunt_ids_in_work_plan(wp_md)
    raw_hunts = hunt_ids_from_files(raw_dir, ".json")
    trans_hunts = hunt_ids_from_files(trans_dir, ".md")
    cur_hunts = hunt_ids_from_files(curation_dir, ".md")

    if not wp_hunts:
        fail("work-plan.md에 HUNT 카드가 없음")

    missing_raw = wp_hunts - raw_hunts
    missing_trans = wp_hunts - trans_hunts
    missing_cur = wp_hunts - cur_hunts

    if missing_raw:
        fail(
            f"Stage A (.hunt-raw) 누락 {len(missing_raw)}건: "
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

    # 2. Stage A raw cache integrity
    raw_errors = []
    for p in sorted(raw_dir.glob("HUNT-*.json")):
        err = check_raw_cache(p)
        if err:
            raw_errors.append(err)
    if raw_errors:
        print(
            f"❌ Stage A raw cache 문제 {len(raw_errors)}건:", file=sys.stderr
        )
        for e in raw_errors[:10]:
            print(e, file=sys.stderr)
        sys.exit(1)

    # 3. Stage B translation integrity
    trans_errors = []
    for p in sorted(trans_dir.glob("HUNT-*.md")):
        err = check_translation(p)
        if err:
            trans_errors.append(err)
    if trans_errors:
        print(
            f"❌ Stage B translation 문제 {len(trans_errors)}건:",
            file=sys.stderr,
        )
        for e in trans_errors[:10]:
            print(e, file=sys.stderr)
        sys.exit(1)

    # 4. Stage C curation integrity (6 categories + action items + no placeholder)
    cur_errors = []
    for p in sorted(curation_dir.glob("HUNT-*.md")):
        hunt_id = re.match(r"(HUNT-\d+)", p.name).group(1)
        diag = check_curation_block(p.read_text(encoding="utf-8"), hunt_id)
        cur_errors.extend(diag)
    if cur_errors:
        print(
            f"❌ Stage C curation 문제 {len(cur_errors)}건:", file=sys.stderr
        )
        for e in cur_errors[:15]:
            print(e, file=sys.stderr)
        sys.exit(1)

    # 5. Stage D assembled consensus-results.md
    if not results_md.exists():
        fail(f"{results_md.name} 없음 (Stage D 미수행)")
    md_text = results_md.read_text(encoding="utf-8")
    if "번역 대기" in md_text:
        fail(f"{results_md.name}에 `번역 대기` 잔존")
    assembled_hunts = set(re.findall(r"^## \[(HUNT-\d+)\]", md_text, re.MULTILINE))
    missing_assembled = cur_hunts - assembled_hunts
    if missing_assembled:
        fail(
            f"Stage D assembly 누락 {len(missing_assembled)}건 "
            "(.curation 있으나 consensus-results.md에 안 들어감): "
            + ", ".join(sorted(missing_assembled)[:10])
        )

    # 6. Cumulative summary existence in consensus-results.md
    if "🏆" not in md_text or "PDF 다운로드 우선순위" not in md_text:
        fail(
            "consensus-results.md 끝에 누적 요약 섹션(🏆 최중요 발견 / 📥 PDF 우선순위) 누락"
        )

    print(
        f"✅ HUNT post-check 통과\n"
        f"   work-plan HUNT: {len(wp_hunts)} · "
        f".hunt-raw: {len(raw_hunts)} · "
        f".translations: {len(trans_hunts)} · "
        f".curation: {len(cur_hunts)} · "
        f"assembled: {len(assembled_hunts)}"
    )


if __name__ == "__main__":
    main()
