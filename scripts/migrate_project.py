#!/usr/bin/env python3
"""
migrate_project.py — 옛 버전 프로젝트 폴더를 현재(v3.2) 구조로 정리.

다른 사용자에게서 받은 (또는 옛 시점 백업에서 복구한) 프로젝트 폴더를
projects/ 안에 복사한 후 이 스크립트를 한 번 실행해 stale 파일을 정리하고
폴더 구조를 v3.2 표준으로 맞춘다.

멱등 보장 — 이미 정리된 프로젝트에 다시 실행해도 안전 (모든 단계 skip).

처리 항목:
1. .current-mode 잔존 파일 삭제 (v3.2에서 mode 시스템 폐기)
2. evaluations/latest/.eval-cache.json → .eval-cache.json (프로젝트 루트로 이동)
3. evaluations/latest/axis*.md → flow/evaluations/latest/ 로 이동
   (옛 구조엔 stage 분리 없었으므로 flow 단계로 가정)
4. chapters/*.md → output/ 로 이동 (이름 충돌 시 경고만)
5. chapters/claim-extraction-output.md → output/claim-extraction-output.md
6. 빈 chapters/, 빈 evaluations/ 폴더 정리
7. 표준 폴더 구조 보강 (없으면 생성):
   - flow/, output/, history/
   - papers/{collected,candidates,analyzed,.research-raw,.translations,.curation,consensus-results.archive}
   - flow/evaluations/, output/evaluations/
8. .paper-metadata.json의 version 필드 → "1.2"로 갱신 (없으면 추가)

CLI:
    python3 scripts/migrate_project.py <project> [--dry-run]
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "flow",
    "output",
    "history",
    "flow/evaluations/latest",
    "output/evaluations/latest",
    "papers/collected",
    "papers/candidates",
    "papers/analyzed",
    "papers/.research-raw",
    "papers/.translations",
    "papers/.curation",
    "papers/consensus-results.archive",
]

CURRENT_VERSION = "1.2"


class Reporter:
    def __init__(self, dry_run: bool):
        self.dry_run = dry_run
        self.changes: list[str] = []
        self.skipped: list[str] = []

    def did(self, msg: str) -> None:
        prefix = "[dry-run] " if self.dry_run else "✅ "
        print(f"{prefix}{msg}")
        self.changes.append(msg)

    def skip(self, msg: str) -> None:
        print(f"  · skip — {msg}")
        self.skipped.append(msg)

    def warn(self, msg: str) -> None:
        print(f"⚠️  {msg}")


def project_root(project: str) -> Path:
    return ROOT / "projects" / project


# ──────────────────────────── 단계 ────────────────────────────


def step_remove_current_mode(proj: Path, r: Reporter) -> None:
    p = proj / ".current-mode"
    if not p.exists():
        r.skip(".current-mode 없음 (이미 정리됨)")
        return
    if r.dry_run:
        r.did(f"삭제 예정: {p.relative_to(proj)}")
    else:
        p.unlink()
        r.did(f".current-mode 삭제 (mode 시스템 폐기됨)")


def step_move_eval_cache(proj: Path, r: Reporter) -> None:
    old = proj / "evaluations" / "latest" / ".eval-cache.json"
    new = proj / ".eval-cache.json"
    if not old.exists():
        r.skip("옛 eval-cache 없음")
        return
    if new.exists():
        r.warn(f"새 위치에 이미 .eval-cache.json 존재 — 옛 파일은 그대로 두고 검토 필요: {old}")
        return
    if r.dry_run:
        r.did(f"이동 예정: {old.relative_to(proj)} → {new.relative_to(proj)}")
    else:
        shutil.move(str(old), str(new))
        r.did(f"eval-cache.json 위치 갱신 (프로젝트 루트로)")


def step_move_legacy_evaluations(proj: Path, r: Reporter) -> None:
    """옛 evaluations/latest/axis*.md → flow/evaluations/latest/"""
    old_dir = proj / "evaluations" / "latest"
    new_dir = proj / "flow" / "evaluations" / "latest"

    if not old_dir.exists():
        r.skip("옛 evaluations/latest/ 없음")
        return

    files = [p for p in old_dir.iterdir() if p.is_file()]
    if not files:
        r.skip("옛 evaluations/latest/ 비어있음")
        return

    if r.dry_run:
        r.did(f"이동 예정: {old_dir.relative_to(proj)}/* → {new_dir.relative_to(proj)}/  ({len(files)}개)")
        return

    new_dir.mkdir(parents=True, exist_ok=True)
    moved = 0
    for f in files:
        target = new_dir / f.name
        if target.exists():
            r.warn(f"새 위치에 이미 존재 — skip: {target.relative_to(proj)}")
            continue
        shutil.move(str(f), str(target))
        moved += 1
    if moved:
        r.did(f"evaluations 산출물 {moved}개를 flow/evaluations/latest/로 이동")


def step_migrate_chapters(proj: Path, r: Reporter) -> None:
    """chapters/ 잔존 시 → output/ 머지."""
    old_dir = proj / "chapters"
    new_dir = proj / "output"

    if not old_dir.exists():
        r.skip("chapters/ 없음 (이미 정리됨)")
        return

    files = [p for p in old_dir.iterdir() if p.is_file()]
    if not files:
        # 빈 chapters/ 정리
        if r.dry_run:
            r.did(f"빈 chapters/ 삭제 예정")
        else:
            try:
                old_dir.rmdir()
                r.did("빈 chapters/ 삭제")
            except OSError:
                r.warn(f"chapters/ 삭제 실패 (비어있지 않음): {old_dir}")
        return

    if r.dry_run:
        r.did(f"이동 예정: {old_dir.relative_to(proj)}/* → {new_dir.relative_to(proj)}/  ({len(files)}개)")
        return

    new_dir.mkdir(parents=True, exist_ok=True)
    moved = 0
    for f in files:
        target = new_dir / f.name
        if target.exists():
            r.warn(f"이름 충돌 — chapters/{f.name} 보존, output/{f.name} 우선. 사용자가 직접 머지 필요.")
            continue
        shutil.move(str(f), str(target))
        moved += 1
    if moved:
        r.did(f"chapters/* {moved}개 → output/로 이동")

    # 비었으면 폴더 삭제
    remaining = list(old_dir.iterdir())
    if not remaining:
        try:
            old_dir.rmdir()
            r.did("빈 chapters/ 폴더 삭제")
        except OSError:
            pass
    else:
        r.warn(f"chapters/에 {len(remaining)}개 잔존 — 충돌 해결 후 사용자가 정리")


def step_ensure_dirs(proj: Path, r: Reporter) -> None:
    created = []
    for rel in REQUIRED_DIRS:
        d = proj / rel
        if d.exists():
            continue
        if r.dry_run:
            created.append(rel)
        else:
            d.mkdir(parents=True, exist_ok=True)
            created.append(rel)
    if created:
        r.did(f"필수 폴더 {len(created)}개 생성: {', '.join(created)}")
    else:
        r.skip("폴더 구조 이미 완비")


def step_update_metadata(proj: Path, r: Reporter) -> None:
    p = proj / ".paper-metadata.json"
    if not p.exists():
        r.skip(".paper-metadata.json 없음 — 신규 프로젝트면 'sync_state.py init'로 생성")
        return
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        r.warn(f".paper-metadata.json 파싱 실패: {e}")
        return

    current = data.get("version")
    if current == CURRENT_VERSION:
        r.skip(f".paper-metadata.json version 이미 {CURRENT_VERSION}")
        return

    data["version"] = CURRENT_VERSION
    if r.dry_run:
        r.did(f"version {current!r} → {CURRENT_VERSION!r} 갱신 예정")
    else:
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        r.did(f".paper-metadata.json version {current!r} → {CURRENT_VERSION!r}")


def step_cleanup_empty_evaluations(proj: Path, r: Reporter) -> None:
    """루트 evaluations/ 폴더가 비었으면 정리."""
    eval_dir = proj / "evaluations"
    if not eval_dir.exists():
        return
    # 재귀적으로 빈 폴더만 있는지 검사
    has_files = any(f.is_file() for f in eval_dir.rglob("*"))
    if has_files:
        r.warn(f"루트 evaluations/에 파일 잔존 — 수동 정리 필요: {eval_dir}")
        return
    if r.dry_run:
        r.did(f"빈 evaluations/ 트리 삭제 예정")
    else:
        shutil.rmtree(eval_dir)
        r.did("빈 루트 evaluations/ 트리 삭제")


# ──────────────────────────── 엔트리 ────────────────────────────


def migrate(project: str, dry_run: bool = False) -> int:
    proj = project_root(project)
    if not proj.exists():
        print(f"❌ 프로젝트 없음: {proj}", file=sys.stderr)
        return 1

    print(f"\n🔧 마이그레이션 대상: {proj.relative_to(ROOT)}")
    if dry_run:
        print("   (dry-run — 실제 변경 없음)")
    print()

    r = Reporter(dry_run)

    print("━ 1. .current-mode 삭제 (v3.2 mode 폐기)")
    step_remove_current_mode(proj, r)

    print("\n━ 2. eval-cache.json 위치 갱신")
    step_move_eval_cache(proj, r)

    print("\n━ 3. 옛 evaluations/latest/* → flow/evaluations/latest/")
    step_move_legacy_evaluations(proj, r)

    print("\n━ 4. chapters/* → output/")
    step_migrate_chapters(proj, r)

    print("\n━ 5. 표준 폴더 구조 보강")
    step_ensure_dirs(proj, r)

    print("\n━ 6. .paper-metadata.json version 갱신")
    step_update_metadata(proj, r)

    print("\n━ 7. 빈 루트 evaluations/ 정리")
    step_cleanup_empty_evaluations(proj, r)

    print()
    if dry_run:
        print(f"📋 dry-run 요약: 변경 예정 {len(r.changes)}건, skip {len(r.skipped)}건")
        print("   실제 적용하려면 --dry-run 없이 다시 실행")
    elif r.changes:
        print(f"✅ 마이그레이션 완료: {len(r.changes)}건 적용, {len(r.skipped)}건 skip")
        print(f"   다음: 'flow 평가해줘' 또는 '현재 상태'로 검증")
    else:
        print(f"✅ 이미 최신 구조 — 변경 없음 ({len(r.skipped)}건 모두 skip)")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 1
    project = argv[1]
    dry_run = "--dry-run" in argv[2:]
    return migrate(project, dry_run=dry_run)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
