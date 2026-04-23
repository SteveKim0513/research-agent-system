#!/usr/bin/env python3
"""
paper_reanalysis_delta.py — flow.md 변경 기반 영향 논문 필터.

`논문 재분석해줘` 호출 시 paper-processing-orchestrator가 이 스크립트를 실행해
flow.md의 어떤 섹션이 바뀌었고, 그 섹션을 primary_section으로 가진 논문만
재분석 대상으로 반환한다.

알고리즘:
1. 현재 flow/flow.md 섹션 헤더 + 본문 해시 스냅샷
2. 가장 최근 flow/history/*/flow.md (pre-claim-extract 또는 pre-refine)의 섹션 해시 비교
3. 내용이 달라진 섹션 목록 추출
4. 각 papers/analyzed/{파일명}-analysis.md의 frontmatter 또는 메타에서 primary_section 읽음
5. primary_section이 변경 목록에 포함된 논문만 재분석 대상으로 출력

사용법:
    python scripts/paper_reanalysis_delta.py <project_name>
        영향 논문 JSON 반환 (orchestrator가 소비)
    python scripts/paper_reanalysis_delta.py <project_name> --full
        모든 analyzed 논문 반환 (delta 무시)
"""
import hashlib
import json
import re
import sys
from pathlib import Path


def project_root(project: str) -> Path:
    p = Path("projects") / project
    if not p.exists():
        raise SystemExit(f"프로젝트 없음: {p}")
    return p


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def parse_sections(text: str) -> dict:
    """md에서 ## 헤더별로 섹션 분절. 각 섹션의 (제목 → 본문 해시)."""
    sections = {}
    current_title = None
    current_body = []

    for line in text.split("\n"):
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            if current_title is not None:
                sections[current_title] = sha_text("\n".join(current_body))
            current_title = m.group(1).strip()
            current_body = []
        else:
            if current_title is not None:
                current_body.append(line)

    if current_title is not None:
        sections[current_title] = sha_text("\n".join(current_body))
    return sections


def load_primary_section(analysis_file: Path) -> str:
    """analyzed/{파일명}-analysis.md에서 primary_section 추출.

    다양한 위치를 시도:
    - frontmatter `primary_section: "..."`
    - 메타 섹션 `- **primary_section**: ...`
    - 연동: triage.json 쪽에 있으면 그쪽 우선
    """
    # 우선 동명의 triage.json 확인
    triage_file = analysis_file.parent / analysis_file.name.replace("-analysis.md", "-triage.json")
    if triage_file.exists():
        try:
            data = json.loads(triage_file.read_text(encoding="utf-8"))
            ps = data.get("primary_section")
            if ps:
                return ps
        except Exception:
            pass

    if not analysis_file.exists():
        return ""
    try:
        text = analysis_file.read_text(encoding="utf-8")
    except Exception:
        return ""

    # frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        m = re.search(r"primary_section\s*:\s*['\"]?([^'\"\n]+)", fm)
        if m:
            return m.group(1).strip()

    # 메타 섹션
    m = re.search(r"[*\-]\s*\*\*primary_section\*\*\s*:\s*(.+)", text)
    if m:
        return m.group(1).strip().strip("\"'")

    return ""


def find_latest_history_flow(root: Path) -> Path:
    """flow/history/{NNN}-*/flow.md 중 가장 최근 것."""
    history_dir = root / "flow" / "history"
    if not history_dir.exists():
        return None
    dirs = sorted(
        [d for d in history_dir.iterdir() if d.is_dir() and d.name[:3].isdigit()],
        key=lambda d: int(d.name[:3]),
    )
    for d in reversed(dirs):
        flow_snapshot = d / "flow.md"
        if flow_snapshot.exists():
            return flow_snapshot
    return None


def cmd_delta(project: str, full: bool = False) -> int:
    root = project_root(project)
    analyzed_dir = root / "papers" / "analyzed"
    all_analysis = sorted(analyzed_dir.glob("*-analysis.md")) if analyzed_dir.exists() else []

    if full:
        result = {
            "project": project,
            "mode": "full",
            "affected_papers": [f.name.replace("-analysis.md", "") for f in all_analysis],
            "changed_sections": [],
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    cur_flow = root / "flow" / "flow.md"
    prev_flow = find_latest_history_flow(root)

    if not cur_flow.exists():
        print(json.dumps({
            "project": project,
            "mode": "delta",
            "error": "flow/flow.md 없음",
            "affected_papers": [],
        }, indent=2, ensure_ascii=False))
        return 1

    if not prev_flow:
        # history 없음 = 전량 재분석 필요 (첫 분석이면 delta 의미 없음)
        result = {
            "project": project,
            "mode": "delta",
            "note": "flow/history/ 비어 있음 — delta 기준 없어 전량 반환",
            "affected_papers": [f.name.replace("-analysis.md", "") for f in all_analysis],
            "changed_sections": [],
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    cur_sections = parse_sections(cur_flow.read_text(encoding="utf-8"))
    prev_sections = parse_sections(prev_flow.read_text(encoding="utf-8"))

    changed = []
    for title, h in cur_sections.items():
        if prev_sections.get(title) != h:
            changed.append(title)
    # 삭제된 섹션도 변경으로 취급
    for title in prev_sections:
        if title not in cur_sections:
            changed.append(f"(deleted) {title}")

    # 각 analysis의 primary_section 확인
    affected = []
    for f in all_analysis:
        primary = load_primary_section(f)
        if not primary:
            # primary_section 모르면 보수적으로 포함
            affected.append((f.name.replace("-analysis.md", ""), "unknown"))
            continue
        # 섹션명이 changed 목록에 부분 일치하면 포함
        for ch in changed:
            if primary.lower() in ch.lower() or ch.lower() in primary.lower():
                affected.append((f.name.replace("-analysis.md", ""), primary))
                break

    result = {
        "project": project,
        "mode": "delta",
        "prev_flow_snapshot": str(prev_flow.relative_to(root)),
        "changed_sections": changed,
        "affected_papers": [name for name, _ in affected],
        "affected_detail": [{"paper": n, "primary_section": ps} for n, ps in affected],
        "total_analyzed": len(all_analysis),
        "skipped": len(all_analysis) - len(affected),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def main(argv: list) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    args = argv[1:]
    full = "--full" in args
    plain = [a for a in args if not a.startswith("--")]
    if len(plain) != 1:
        print(__doc__)
        return 1
    try:
        return cmd_delta(plain[0], full=full)
    except Exception as e:
        print(f"⚠️ 오류: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
