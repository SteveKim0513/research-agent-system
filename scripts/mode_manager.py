#!/usr/bin/env python3
"""
mode_manager.py — 사용자 모드(flow/output) 저장 및 전환.

저장 위치: projects/{P}/.current-mode (한 줄 텍스트, "flow" | "output")

기본값: flow (파일 부재 시).

용도:
- prefix 생략 명령(`"레퍼런스 분석해줘"` 등)에서 어느 stage를 대상으로 할지 결정
- prefix 명시(`"output 레퍼런스 분석해줘"`)는 mode를 무시(override)
- `"현재 상태"` / `"버전 체크"`에서 모드 표시

CLI:
    python3 scripts/mode_manager.py get {project}                  # 현재 모드 출력
    python3 scripts/mode_manager.py set {project} {flow|output}    # 모드 전환
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


def set_mode(project_root: Path, mode: str) -> None:
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be {VALID_MODES}, got {mode!r}")
    project_root.mkdir(parents=True, exist_ok=True)
    mode_file(project_root).write_text(mode + "\n", encoding="utf-8")


def resolve_stage(project_root: Path, explicit_prefix: str | None = None) -> str:
    """명시 prefix 우선, 없으면 현재 모드. 둘 다 없으면 DEFAULT_MODE."""
    if explicit_prefix in VALID_MODES:
        return explicit_prefix
    return get_mode(project_root)


# ──────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────

def _cli():
    if len(sys.argv) < 3:
        print("Usage: mode_manager.py <get|set> <project> [<mode>]")
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

    if cmd == "set":
        if len(sys.argv) < 4:
            print(f"Usage: mode_manager.py set {project} <flow|output>")
            sys.exit(1)
        mode = sys.argv[3].lower()
        if mode not in VALID_MODES:
            print(f"❌ mode는 {VALID_MODES}", file=sys.stderr)
            sys.exit(1)
        prev = get_mode(proj)
        set_mode(proj, mode)
        if prev == mode:
            print(f"ℹ️  이미 {mode} 모드")
        else:
            print(f"✅ 모드 전환: {prev} → {mode}")
        return

    print(f"Unknown command: {cmd}")
    sys.exit(1)


if __name__ == "__main__":
    _cli()
