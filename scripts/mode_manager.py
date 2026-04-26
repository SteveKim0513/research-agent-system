#!/usr/bin/env python3
"""
mode_manager.py — 작업 단계 (flow → output) **단방향 진행** 관리.

이전 v2: flow/output 자유 전환. 사용자 요청으로 v3에서 단방향:
- 시작 = flow
- flow 마무리 후 output으로 전진 (`set_mode(p, "output")`)
- **output → flow 되돌리기 금지** — flow는 thesis 계획, 일단 output 작성
  단계로 넘어가면 더 이상 flow를 *직접 수정*하지 않음.
- flow.md 자체는 그대로 두되, 분석/카드 발급/수정의 *대상*이 output 으로만.

저장: projects/{P}/.current-mode

CLI:
    python3 scripts/mode_manager.py get {project}
    python3 scripts/mode_manager.py advance {project}        # flow → output (단방향)
    python3 scripts/mode_manager.py set {project} flow       # 강제 reset (예외 — 사용자 명시 시만)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VALID_MODES = ("flow", "output")
DEFAULT_MODE = "flow"


def mode_file(project_root: Path) -> Path:
    return project_root / ".current-mode"


def get_mode(project_root: Path) -> str:
    p = mode_file(project_root)
    if not p.exists():
        return DEFAULT_MODE
    text = p.read_text(encoding="utf-8").strip()
    return text if text in VALID_MODES else DEFAULT_MODE


def advance_to_output(project_root: Path) -> str:
    """flow → output 단방향 전진. 이미 output이면 noop."""
    current = get_mode(project_root)
    if current == "output":
        return "already_output"
    project_root.mkdir(parents=True, exist_ok=True)
    mode_file(project_root).write_text("output\n", encoding="utf-8")
    return "advanced"


def set_mode(project_root: Path, mode: str, *, force: bool = False) -> None:
    """단방향 enforcement.

    - flow → output: OK
    - output → output: noop
    - output → flow: **금지** (force=True 일 때만 — 사용자 명시 reset)
    - flow → flow: noop
    """
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be {VALID_MODES}, got {mode!r}")

    current = get_mode(project_root)
    if current == "output" and mode == "flow" and not force:
        raise RuntimeError(
            "이미 output 단계 진행 중. flow로 되돌리는 것은 권장되지 않습니다. "
            "정말 필요하면 `set_mode(..., force=True)` 사용 (사용자 명시)."
        )
    project_root.mkdir(parents=True, exist_ok=True)
    mode_file(project_root).write_text(mode + "\n", encoding="utf-8")


def resolve_stage(project_root: Path, explicit_prefix: str | None = None) -> str:
    """명시 prefix 우선, 없으면 현재 모드.

    참고: prefix는 단발 override 였으나 v3에서는 mode 변경 자체가 단방향.
    flow에서 'output 분석해줘' prefix → 즉시 advance_to_output.
    output에서 'flow 분석해줘' prefix → 경고 + 무시 (또는 force).
    """
    if explicit_prefix in VALID_MODES:
        return explicit_prefix
    return get_mode(project_root)


# ──────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────

def _cli():
    if len(sys.argv) < 3:
        print("Usage: mode_manager.py <get|advance|set> <project> [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    project = sys.argv[2]
    proj = ROOT / "projects" / project
    if not proj.exists():
        print(f"❌ 프로젝트 없음: {proj}", file=sys.stderr)
        sys.exit(1)

    if cmd == "get":
        print(get_mode(proj))
        return

    if cmd == "advance":
        result = advance_to_output(proj)
        if result == "already_output":
            print(f"ℹ️  이미 output 단계")
        else:
            print(f"✅ flow → output 단계 진행")
        return

    if cmd == "set":
        if len(sys.argv) < 4:
            print(f"Usage: mode_manager.py set {project} <flow|output> [--force]")
            sys.exit(1)
        mode = sys.argv[3].lower()
        force = "--force" in sys.argv
        if mode not in VALID_MODES:
            print(f"❌ mode는 {VALID_MODES}", file=sys.stderr)
            sys.exit(1)
        try:
            prev = get_mode(proj)
            set_mode(proj, mode, force=force)
            if prev == mode:
                print(f"ℹ️  이미 {mode} 단계")
            else:
                print(f"✅ {prev} → {mode}")
        except RuntimeError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
        return

    print(f"Unknown command: {cmd}")
    sys.exit(1)


if __name__ == "__main__":
    _cli()
