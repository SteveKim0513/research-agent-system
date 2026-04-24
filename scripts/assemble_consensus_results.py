#!/usr/bin/env python3
"""Assemble projects/{P}/papers/consensus-results.md from per-RESEARCH curation files.

Concat `.curation/RESEARCH-NNN.md` in order, cross-RESEARCH URL dedup (first full
entry kept, subsequent occurrences replaced with one-line dup marker),
prepend master header. Writes header + RESEARCH blocks only — the cumulative
summary sections (🏆 최중요 / 📥 PDF 우선순위 / 🔗 Cross-RESEARCH 교차표 /
👉 다음 단계) are appended by a thin LLM summarizer in a later step.

Usage: python3 scripts/assemble_consensus_results.py {PROJECT}
"""
import sys, re, json, os, pathlib, datetime


def main():
    if len(sys.argv) < 2:
        print("usage: assemble_consensus_results.py {PROJECT}", file=sys.stderr)
        sys.exit(2)
    project = sys.argv[1]
    base = pathlib.Path("projects") / project / "papers"
    cur_dir = base / ".curation"
    out_path = base / "consensus-results.md"

    files = sorted(cur_dir.glob("RESEARCH-*.md"))
    if not files:
        print(f"no curation files in {cur_dir}", file=sys.stderr)
        sys.exit(1)

    # Regex to match one full paper entry:
    #   `#N **Authors** — [Title](URL) · journal, X회 인용.`
    #   `  (a) ...`
    #   `  (b) ...`
    #   `  (c) ...`
    entry_re = re.compile(
        r"^(#\d+) (\*\*[^\n]+\*\*) — \[([^\]]+)\]\(([^)]+)\)([^\n]*)\n"
        r"((?:  \([a-c]\)[^\n]*\n?)+)",
        re.MULTILINE,
    )

    # URL normalizer: strip tracking params after '?'
    def norm(u: str) -> str:
        return u.split("?", 1)[0].rstrip("/")

    # First-pass: walk each RESEARCH in order, record first-seen URLs.
    # Second-pass: rewrite each RESEARCH's body, replacing entries whose URL
    # was already seen in an earlier RESEARCH.
    first_seen: dict[str, tuple[str, str]] = {}  # url -> (CARD_ID, #N)
    dedup_count_per_card: dict[str, int] = {}

    # Pass 1 — record first-seen URLs by scanning in RESEARCH order.
    for f in files:
        card_id = f.stem  # "RESEARCH-001"
        text = f.read_text()
        for m in entry_re.finditer(text):
            num = m.group(1)
            url = norm(m.group(4))
            if url not in first_seen:
                first_seen[url] = (card_id, num)

    # Pass 2 — build per-RESEARCH body with dedup replacement.
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
            # Only dedup if origin is an *earlier* RESEARCH (not self).
            if origin and origin[0] != card_id:
                dup_count += 1
                orig_card, orig_num = origin
                return f"{num} ⚠️ 중복 — {orig_card} {orig_num} 참조.\n"
            return m.group(0)

        rewritten = entry_re.sub(repl, text)
        dedup_count_per_card[card_id] = dup_count

        # Demote file's top heading `# RESEARCH-NNN Curation — topic` to
        # `## [RESEARCH-NNN] topic` so that (a) the master file's `#` stays
        # at the top level and (b) postcheck's `## [RESEARCH-NNN]` regex
        # matches.
        lines = rewritten.splitlines(keepends=True)
        head_re = re.compile(r"^# (RESEARCH-\d+)\s+Curation\s+—\s+(.+?)\s*$")
        if lines:
            m = head_re.match(lines[0].rstrip("\n"))
            if m:
                lines[0] = f"## [{m.group(1)}] {m.group(2)}\n"
            elif lines[0].startswith("# "):
                # Fallback: any `# RESEARCH-NNN ...` form.
                lines[0] = "## [" + lines[0][2:].replace(" ", "] ", 1)
        blocks.append("".join(lines))

    # Master header.
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    n_cards = len(files)
    n_unique_urls = len(first_seen)
    total_dups = sum(dedup_count_per_card.values())

    header = f"""# {project} — Consensus 검색 통합 결과

> 📅 생성: {ts}  ·  RESEARCH cards: {n_cards}  ·  유니크 논문 URL: {n_unique_urls}  ·  cross-RESEARCH 중복 치환: {total_dups}
> 파이프라인: Stage A (MCP serial) → pipelined Stage B+C (research-processor background) → Stage D (mechanical concat + URL dedup + thin summary)
> 생성 도구: scripts/assemble_consensus_results.py

이 파일은 `.curation/RESEARCH-*.md` 15개를 순서대로 concat하고, 동일 URL이 복수 카드에 등장할 때 첫 등장 외에는 one-liner로 치환한 결과입니다. 뒤쪽 누적 요약 섹션은 별도 단계에서 append됩니다.

---

"""

    content = header + "\n\n---\n\n".join(blocks) + "\n"

    # Atomic write.
    tmp = out_path.with_suffix(f".md.tmp.{os.getpid()}")
    tmp.write_text(content)
    tmp.replace(out_path)

    # Report.
    print(json.dumps({
        "project": project,
        "n_cards": n_cards,
        "n_unique_urls": n_unique_urls,
        "cross_card_dedup_total": total_dups,
        "dedup_per_card": dedup_count_per_card,
        "bytes": out_path.stat().st_size,
        "out": str(out_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
