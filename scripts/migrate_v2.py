#!/usr/bin/env python3
"""
migrate_v2.py — v1 → v2 폴더 구조 마이그레이션.

v1 구조:
    projects/{NAME}/flow.md
    projects/{NAME}/FLOW-TEMPLATE.md
    projects/{NAME}/evaluations/latest/claim-extraction.md
    projects/{NAME}/evaluations/latest/work-plan.md
    projects/{NAME}/evaluations/latest/{originality,concept-clarity,critical-lens}-report.md

v2 구조:
    projects/{NAME}/flow/flow.md
    projects/{NAME}/flow/FLOW-TEMPLATE.md
    projects/{NAME}/flow/claim-extraction-flow.md       ← 이동
    projects/{NAME}/work-plan.md                         ← 이동 (루트)
    projects/{NAME}/evaluations/latest/{axis1~6-*.md,evaluation.md}
        (폐기 파일 삭제: {originality,concept-clarity,critical-lens}-report.md)

사용법:
    python scripts/migrate_v2.py <project_name>              # 단일 프로젝트
    python scripts/migrate_v2.py --all                        # projects/ 전체
    python scripts/migrate_v2.py <project_name> --dry-run    # 실제 이동 없이 계획만

멱등성: 이미 v2인 프로젝트는 스킵. 재실행해도 안전.
"""

import shutil
import sys
from pathlib import Path


OBSOLETE_EVAL_FILES = [
    "originality-report.md",
    "concept-clarity-report.md",
    "critical-lens-report.md",
]


def log(msg: str, dry: bool = False) -> None:
    prefix = "[DRY] " if dry else ""
    print(f"{prefix}{msg}")


def is_v2(proj: Path) -> bool:
    """이미 v2 구조면 True."""
    return (proj / "flow" / "flow.md").exists()


def migrate_project(proj: Path, dry: bool = False) -> int:
    if not proj.exists():
        print(f"⚠️  프로젝트 없음: {proj}", file=sys.stderr)
        return 1

    if is_v2(proj):
        log(f"⏭️  이미 v2: {proj.name}", dry)
        return 0

    print(f"▶ migrating: {proj.name}")

    # 1. flow/ 폴더 생성
    flow_dir = proj / "flow"
    if not dry:
        flow_dir.mkdir(parents=True, exist_ok=True)

    # 1a. flow.md 이동
    src_flow = proj / "flow.md"
    dest_flow = flow_dir / "flow.md"
    if src_flow.exists():
        log(f"  mv {src_flow.name} → flow/flow.md", dry)
        if not dry:
            shutil.move(str(src_flow), str(dest_flow))
    else:
        log(f"  ℹ️  flow.md 없음 (스킵)", dry)

    # 1b. FLOW-TEMPLATE.md 이동
    src_tpl = proj / "FLOW-TEMPLATE.md"
    dest_tpl = flow_dir / "FLOW-TEMPLATE.md"
    if src_tpl.exists():
        log(f"  mv FLOW-TEMPLATE.md → flow/FLOW-TEMPLATE.md", dry)
        if not dry:
            shutil.move(str(src_tpl), str(dest_tpl))
    else:
        log(f"  ℹ️  FLOW-TEMPLATE.md 없음 (스킵)", dry)

    # 1c. evaluations/latest/claim-extraction.md → flow/claim-extraction-flow.md
    src_ce = proj / "evaluations" / "latest" / "claim-extraction.md"
    dest_ce = flow_dir / "claim-extraction-flow.md"
    if src_ce.exists():
        log(f"  mv evaluations/latest/claim-extraction.md → flow/claim-extraction-flow.md", dry)
        if not dry:
            shutil.move(str(src_ce), str(dest_ce))
    else:
        log(f"  ℹ️  claim-extraction.md 없음 (스킵)", dry)

    # 2. work-plan.md 루트로 이동
    src_wp = proj / "evaluations" / "latest" / "work-plan.md"
    dest_wp = proj / "work-plan.md"
    if src_wp.exists():
        if dest_wp.exists():
            log(f"  ⚠️  work-plan.md 이미 루트에 존재 — evaluations 쪽 덮어쓰기 안 함", dry)
        else:
            log(f"  mv evaluations/latest/work-plan.md → work-plan.md", dry)
            if not dry:
                shutil.move(str(src_wp), str(dest_wp))
    else:
        log(f"  ℹ️  work-plan.md 없음 (스킵)", dry)

    # 3. 폐기 eval report 삭제
    latest_dir = proj / "evaluations" / "latest"
    if latest_dir.exists():
        for obs in OBSOLETE_EVAL_FILES:
            f = latest_dir / obs
            if f.exists():
                log(f"  rm evaluations/latest/{obs} (폐기 파일)", dry)
                if not dry:
                    f.unlink()

    # 4. chapters/ history 구조 확인/생성 (새로 만들 필요 없음 — 빈 폴더라 남겨둠)
    chap_dir = proj / "chapters"
    if chap_dir.exists() and not (chap_dir / "history").exists():
        log(f"  mkdir chapters/history/", dry)
        if not dry:
            (chap_dir / "history").mkdir(exist_ok=True)

    # 5. work-plan.archive/ 준비
    wpa = proj / "work-plan.archive"
    if not wpa.exists():
        log(f"  mkdir work-plan.archive/", dry)
        if not dry:
            wpa.mkdir(exist_ok=True)

    print(f"✅ v2 변환 완료: {proj.name}")
    return 0


def migrate_all(dry: bool = False) -> int:
    root = Path("projects")
    if not root.exists():
        print(f"⚠️  projects/ 없음: {root}", file=sys.stderr)
        return 1
    total = 0
    for proj in sorted(root.iterdir()):
        if proj.is_dir() and not proj.name.startswith("."):
            total += migrate_project(proj, dry=dry)
    return 0 if total == 0 else 1


def main(argv: list) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1

    dry = "--dry-run" in argv
    targets = [a for a in argv[1:] if not a.startswith("--")]

    if "--all" in argv:
        return migrate_all(dry=dry)

    if len(targets) != 1:
        print(__doc__)
        return 1

    return migrate_project(Path("projects") / targets[0], dry=dry)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
