#!/usr/bin/env python3
"""
finalize_draft.py — '최종 완성했어' 명령 처리.

output/*.md (claim-extraction 제외)을 파일명 정렬 순서로 단일
final/complete-draft.md 로 머지한다. 챕터 사이 구분 헤더 자동 삽입.

final/ 폴더는 이 명령 실행 시점에만 생성된다.
- 통합본 외 다른 파일 (claim-extraction-final.md, evaluations/) 은
  이후 사용자가 'final 평가해줘' 명령을 실행할 때 별도 파이프라인으로 생성.

CLI:
    python3 scripts/finalize_draft.py <project>
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def project_root(project: str) -> Path:
    return ROOT / "projects" / project


def chapter_files(out_dir: Path) -> list[Path]:
    if not out_dir.exists():
        return []
    return sorted(
        p for p in out_dir.glob("*.md")
        if p.is_file() and not p.name.startswith("claim-extraction")
        and p.name != "feedback.md"
    )


def merge(project: str) -> int:
    proj = project_root(project)
    if not proj.exists():
        print(f"❌ 프로젝트 없음: {proj}", file=sys.stderr)
        return 1

    out_dir = proj / "output"
    chapters = chapter_files(out_dir)
    if not chapters:
        print(
            f"❌ output/ 에 챕터 파일이 없습니다 ({out_dir}). "
            f"'초안 작성해줘'로 챕터를 먼저 만들어야 합니다.",
            file=sys.stderr,
        )
        return 1

    final_dir = proj / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    target = final_dir / "complete-draft.md"

    parts = [
        "---",
        f"project: {project}",
        f"merged_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"source_chapters: {[p.name for p in chapters]}",
        "kind: final-merged-draft",
        "note: output/*.md 자동 머지 — 직접 편집 금지. 다음 머지 시 덮어씌워짐.",
        "---",
        "",
        f"# {project} — 최종 통합본",
        "",
    ]

    for ch in chapters:
        text = ch.read_text(encoding="utf-8")
        # 챕터 frontmatter 제거 (있으면)
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                text = text[end + 4:].lstrip("\n")
        parts.append(f"<!-- ===== {ch.name} ===== -->")
        parts.append("")
        parts.append(text.rstrip())
        parts.append("")
        parts.append("")

    merged = "\n".join(parts)
    target.write_text(merged, encoding="utf-8")

    print(f"✅ {target.relative_to(proj)} 생성 — {len(chapters)}개 챕터 머지")
    print(f"   다음: 'final 레퍼런스 분석해줘' / 'final 내용 분석해줘'로 평가")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python3 finalize_draft.py <project>")
        return 1
    return merge(argv[1])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
