#!/usr/bin/env python3
"""
paper_triage.py — Pass 1 triage 결과 집계·tier 분류 유틸리티.

paper-analyst(Mode A-triage)가 각 논문마다 `papers/analyzed/{파일명}-triage.json`을
생성한 뒤, 이 스크립트가 tier 분포를 집계하고 tier별 파일 리스트를 반환한다.

paper-processing-orchestrator가 Pass 2 dispatch 전에 이 스크립트를 호출해
tier별 파일 목록을 얻는다.

사용법:
    python scripts/paper_triage.py summarize <project_name>
        tier 분포 + 파일 리스트 JSON 반환
    python scripts/paper_triage.py list <project_name> --tier=1|2|3
        특정 tier 파일 목록 한 줄씩 출력
    python scripts/paper_triage.py promote <project_name> <filename> --to=1|2
        특정 파일의 tier를 수동 승격 (triage.json 수정)
"""
import json
import sys
from pathlib import Path


def project_root(project: str) -> Path:
    cwd = Path.cwd()
    p = cwd / "projects" / project
    if not p.exists():
        raise SystemExit(f"프로젝트 없음: {p}")
    return p


def load_triages(project: str) -> list:
    root = project_root(project)
    analyzed = root / "papers" / "analyzed"
    if not analyzed.exists():
        return []
    results = []
    for f in sorted(analyzed.glob("*-triage.json")):
        try:
            results.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"⚠️ {f.name} 파싱 실패: {e}", file=sys.stderr)
    return results


def parse_stage_arg(args: list, flag: str, default=None):
    for a in args:
        if a.startswith(f"--{flag}="):
            return a.split("=", 1)[1]
    return default


def cmd_summarize(project: str) -> int:
    triages = load_triages(project)
    tier_counts = {1: 0, 2: 0, 3: 0}
    tier_files = {1: [], 2: [], 3: []}
    tag_counts = {"steelman": 0, "delta": 0, "minority": 0, "definition": 0}

    for t in triages:
        tier = t.get("tier", 3)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        tier_files[tier].append(t.get("filename", "?"))
        for tag in t.get("axis_tags", []) or []:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    summary = {
        "project": project,
        "total_triaged": len(triages),
        "tier_counts": tier_counts,
        "tier_files": tier_files,
        "axis_tag_counts": tag_counts,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def cmd_list(project: str, tier: str) -> int:
    try:
        tier_int = int(tier)
    except ValueError:
        print(f"⚠️ tier는 1/2/3 중 하나여야 함: {tier}", file=sys.stderr)
        return 1
    triages = load_triages(project)
    for t in triages:
        if t.get("tier") == tier_int:
            print(t.get("filename", ""))
    return 0


def cmd_promote(project: str, filename: str, new_tier: str) -> int:
    try:
        new_tier_int = int(new_tier)
    except ValueError:
        print(f"⚠️ --to 는 1/2/3", file=sys.stderr)
        return 1
    if new_tier_int not in (1, 2, 3):
        print(f"⚠️ tier 범위 밖: {new_tier_int}", file=sys.stderr)
        return 1

    root = project_root(project)
    triage_file = root / "papers" / "analyzed" / f"{filename}-triage.json"
    if not triage_file.exists():
        # filename에 확장자 포함했을 수도
        stem = filename.rsplit(".", 1)[0]
        triage_file = root / "papers" / "analyzed" / f"{stem}-triage.json"
        if not triage_file.exists():
            print(f"⚠️ triage 파일 없음: {triage_file}", file=sys.stderr)
            return 1

    data = json.loads(triage_file.read_text(encoding="utf-8"))
    old = data.get("tier", "?")
    data["tier"] = new_tier_int
    data["manual_override"] = True
    triage_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ tier {old} → {new_tier_int}: {triage_file.name}")
    return 0


def main(argv: list) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 1
    cmd = argv[1]
    args = argv[2:]
    plain = [a for a in args if not a.startswith("--")]

    try:
        if cmd == "summarize" and len(plain) == 1:
            return cmd_summarize(plain[0])
        if cmd == "list" and len(plain) == 1:
            tier = parse_stage_arg(args, "tier")
            if not tier:
                print("⚠️ --tier=1|2|3 필요", file=sys.stderr)
                return 1
            return cmd_list(plain[0], tier)
        if cmd == "promote" and len(plain) == 2:
            to = parse_stage_arg(args, "to")
            if not to:
                print("⚠️ --to=1|2|3 필요", file=sys.stderr)
                return 1
            return cmd_promote(plain[0], plain[1], to)
    except Exception as e:
        print(f"⚠️ 오류: {e}", file=sys.stderr)
        return 2

    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
