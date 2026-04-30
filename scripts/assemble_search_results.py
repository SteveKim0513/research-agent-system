#!/usr/bin/env python3
"""Assemble papers/search-results/{stage}.md from per-card curation files.

이전 이름: assemble_consensus_results.py
이전 출력 경로: papers/consensus-results.md (단일 파일)
신규 출력 경로: papers/search-results/{stage}.md (stage별 분리)

Concat `.curation/{HUNT-NNN|H-NN|RESEARCH-NNN|R-NN}.md` in order, cross-card URL dedup
(first full entry kept, subsequent occurrences replaced with one-line dup marker),
prepend master header. Writes header + card blocks only — the cumulative summary
sections (🏆 최중요 / 📥 PDF 우선순위 / 🔗 Cross-RESEARCH 교차표 / 👉 다음 단계)
are appended by a thin LLM summarizer in a later step.

Usage:
    python3 scripts/assemble_search_results.py {PROJECT} [--stage flow|research-gap]

stage 생략 시: flow 기본값.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--stage", default="flow",
                        choices=["flow", "research-gap"],
                        help="단계명 (기본: flow). search-results/{stage}.md로 출력.")
    args = parser.parse_args()
    project = args.project
    stage = args.stage

    base = pathlib.Path("projects") / project / "papers"
    cur_dir = base / ".curation"

    # 신규 출력 경로: papers/search-results/{stage}.md
    out_dir = base / "search-results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{stage}.md"

    # H-NN / HUNT-NNN / R-NN / RESEARCH-NNN / MANUAL-NNN 모두 지원
    # stage 분리는 .curation 파일명 prefix로 한다고 가정 안 함 — 모두 concat (파일별 카드 ID로 식별)
    # research-gap stage는 'gap-' prefix를 쓸 수도 있으나 호환을 위해 prefix 무관 처리
    research_files = sorted(cur_dir.glob("RESEARCH-*.md"))
    hunt_files = sorted(cur_dir.glob("HUNT-*.md"))
    h_files = sorted(cur_dir.glob("H-*.md"))
    r_files = sorted(cur_dir.glob("R-*.md"))
    manual_files = sorted(cur_dir.glob("MANUAL-*.md"))
    files = research_files + hunt_files + h_files + r_files + manual_files
    if not files:
        print(f"no curation files in {cur_dir}", file=sys.stderr)
        sys.exit(1)

    # Regex to match one full paper entry
    entry_re = re.compile(
        r"^(#\d+) (\*\*[^\n]+\*\*) — \[([^\]]+)\]\(([^)]+)\)([^\n]*)\n"
        r"((?:  \([a-c]\)[^\n]*\n?)+)",
        re.MULTILINE,
    )

    def norm(u: str) -> str:
        return u.split("?", 1)[0].rstrip("/")

    first_seen: dict[str, tuple[str, str]] = {}
    dedup_count_per_card: dict[str, int] = {}

    # Pass 1
    for f in files:
        card_id = f.stem
        text = f.read_text()
        for m in entry_re.finditer(text):
            num = m.group(1)
            url = norm(m.group(4))
            if url not in first_seen:
                first_seen[url] = (card_id, num)

    # Pass 2
    blocks: list[str] = []
    for f in files:
        card_id = f.stem
        text = f.read_text()
        dup_count = 0

        def repl(m: re.Match) -> str:
            nonlocal dup_count
            num = m.group(1)
            url = norm(m.group(4))
            origin = first_seen.get(url)
            if origin and origin[0] != card_id:
                dup_count += 1
                orig_card, orig_num = origin
                return f"{num} ⚠️ 중복 — {orig_card} {orig_num} 참조.\n"
            return m.group(0)

        rewritten = entry_re.sub(repl, text)
        dedup_count_per_card[card_id] = dup_count

        # H-NN / HUNT-NNN / R-NN / RESEARCH-NNN / MANUAL-NNN 모두 지원
        lines = rewritten.splitlines(keepends=True)
        head_re = re.compile(
            r"^# ((?:HUNT|RESEARCH|MANUAL)-\d+|H-\d+|R-\d+)\s+(?:Curation|Manual addition)\s+—\s+(.+?)\s*$"
        )
        if lines:
            m = head_re.match(lines[0].rstrip("\n"))
            if m:
                lines[0] = f"## [{m.group(1)}] {m.group(2)}\n"
            elif lines[0].startswith("# "):
                lines[0] = "## [" + lines[0][2:].replace(" ", "] ", 1)
        blocks.append("".join(lines))

    ts = datetime.datetime.now().isoformat(timespec="seconds")
    n_research = len(research_files)
    n_hunt = len(hunt_files) + len(h_files) + len(r_files)
    n_manual = len(manual_files)
    n_unique_urls = len(first_seen)
    total_dups = sum(dedup_count_per_card.values())

    header = f"""# {project} — Search Results ({stage})

> 📅 생성: {ts}  ·  stage: {stage}  ·  RESEARCH/HUNT cards: {n_research + n_hunt}  ·  MANUAL additions: {n_manual}  ·  유니크 논문 URL: {n_unique_urls}  ·  cross-card 중복 치환: {total_dups}
> 파이프라인: Stage A (MCP serial) + MANUAL → Stage B+C (research-processor / paper-analyst) → Stage D (mechanical concat + URL dedup)
> 생성 도구: scripts/assemble_search_results.py

이 파일은 `.curation/*.md` 를 concat하고, 동일 URL이 복수 카드에 등장할 때 첫 등장 외에는 one-liner로 치환한 결과입니다.

---

"""

    content = header + "\n\n---\n\n".join(blocks) + "\n"

    tmp = out_path.with_suffix(f".md.tmp.{os.getpid()}")
    tmp.write_text(content)
    tmp.replace(out_path)

    print(json.dumps({
        "project": project,
        "stage": stage,
        "n_research": n_research,
        "n_hunt": n_hunt,
        "n_manual": n_manual,
        "n_cards": len(files),
        "n_unique_urls": n_unique_urls,
        "cross_card_dedup_total": total_dups,
        "dedup_per_card": dedup_count_per_card,
        "bytes": out_path.stat().st_size,
        "out": str(out_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
