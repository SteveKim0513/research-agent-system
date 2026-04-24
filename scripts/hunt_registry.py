#!/usr/bin/env python3
"""
hunt_registry.py — HUNT 발급 관리 single source of truth.

Registry 파일: projects/{P}/.hunt-registry.json

역할:
- 모든 HUNT의 ID·metadata·상태를 영구 보존 (work-plan은 활성 view일 뿐)
- 중복 발급 방지: 동일 covers의 HUNT 재제안 시 (a) active면 skip, (b) completed면 reactivation
- 다음 HUNT 번호 발급의 유일한 source

상태 (lifecycle):
- ready  : 막 발급되었거나 reactivation된 상태 (work-plan Active 섹션에 카드 존재)
- active : ready와 동일 의미. 호환성 위해 ready 사용 권장. (deprecated alias)
- in_progress : 에이전트가 작업 중 (work-plan In-progress 섹션)
- blocked    : 의존성 대기 중 (work-plan Blocked 섹션)
- deferred   : 사용자 보류 (work-plan Deferred 섹션)
- completed  : 완료 (work-plan에서 삭제, registry에만 보존)

동일 문제 판정:
- 정규화된 covers set이 완전 일치 → 같은 HUNT
- normalize: "R-03 (보완)" → "R-03", "R-03-supplement" → "R-03", "S040" 같은 비 R-ID는 원형 보존

Usage:
    from hunt_registry import load, save, next_id, find_by_covers, ...
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


REGISTRY_VERSION = "1.0"


def registry_path(project_root: Path) -> Path:
    return project_root / ".hunt-registry.json"


def empty_registry() -> dict:
    return {
        "schema_version": REGISTRY_VERSION,
        "next_id": 1,
        "hunts": {},  # "HUNT-001": {...}
    }


def load(project_root: Path) -> dict:
    p = registry_path(project_root)
    if not p.exists():
        return empty_registry()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        # Legacy migration: ensure required keys exist
        if "schema_version" not in data:
            data["schema_version"] = REGISTRY_VERSION
        if "next_id" not in data:
            data["next_id"] = 1
        if "hunts" not in data:
            data["hunts"] = {}
        return data
    except Exception:
        return empty_registry()


def save(project_root: Path, registry: dict) -> None:
    p = registry_path(project_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )


def normalize_cover(raw: str) -> str:
    """'R-03 (보완)', 'R-03-supplement', 'R-03.' → 'R-03'. 비 R-ID는 원형."""
    s = raw.strip().rstrip(".,;:")
    m = re.match(r"^(R-\d+)", s)
    if m:
        return m.group(1)
    return s


def normalize_covers_set(covers: list) -> tuple:
    """covers list → 정규화 정렬된 튜플 (hashable key)."""
    normalized = {normalize_cover(c) for c in covers if c and not c.startswith("(")}
    return tuple(sorted(normalized))


def find_by_covers(registry: dict, covers: list) -> str | None:
    """정규화된 covers set이 일치하는 HUNT ID 반환. 없으면 None.

    동일 covers + active/ready/in_progress 이면 그 HUNT 사용.
    동일 covers + completed 이면 reactivation 대상으로 반환.
    """
    if not covers:
        return None
    target = normalize_covers_set(covers)
    if not target:
        return None
    for hid, meta in registry["hunts"].items():
        existing = normalize_covers_set(meta.get("covers") or [])
        if existing == target:
            return hid
    return None


def next_id(registry: dict) -> str:
    """다음 발급 ID 반환 (registry의 next_id 값 기반). 호출자가 add_new 후 increment 해야 함."""
    return f"HUNT-{registry['next_id']:03d}"


def add_new(registry: dict, hunt_id: str, metadata: dict) -> None:
    """신규 HUNT를 registry에 추가. metadata: covers, query, topic, source_file."""
    now = datetime.now().isoformat(timespec="seconds")
    registry["hunts"][hunt_id] = {
        "id": hunt_id,
        "covers": metadata.get("covers", []),
        "query": metadata.get("query", ""),
        "topic": metadata.get("topic", ""),
        "source_file": metadata.get("source_file", ""),
        "status": "ready",
        "issued_at": now,
        "completed_at": None,
        "reactivated_count": 0,
        "history": [
            {"at": now, "event": "issued"},
        ],
    }
    # registry의 next_id는 항상 max(id)+1 유지
    n = int(hunt_id.split("-")[1])
    if n >= registry["next_id"]:
        registry["next_id"] = n + 1


def reactivate(registry: dict, hunt_id: str, reason: str = "동일 covers 재제안") -> None:
    """완료된 HUNT를 ready 상태로 되돌림. 이력에 기록."""
    if hunt_id not in registry["hunts"]:
        return
    h = registry["hunts"][hunt_id]
    h["status"] = "ready"
    h["completed_at"] = None
    h["reactivated_count"] = h.get("reactivated_count", 0) + 1
    h.setdefault("history", []).append({
        "at": datetime.now().isoformat(timespec="seconds"),
        "event": "reactivated",
        "reason": reason,
    })


def mark_completed(registry: dict, hunt_id: str, summary: str | None = None) -> None:
    """HUNT를 완료 상태로. work-plan에서 card는 삭제됨."""
    if hunt_id not in registry["hunts"]:
        return
    h = registry["hunts"][hunt_id]
    now = datetime.now().isoformat(timespec="seconds")
    h["status"] = "completed"
    h["completed_at"] = now
    if summary:
        h["result_summary"] = summary
    h.setdefault("history", []).append({
        "at": now, "event": "completed",
        **({"summary": summary} if summary else {}),
    })


def update_status(registry: dict, hunt_id: str, status: str) -> None:
    """lifecycle status 갱신 (ready → in_progress → completed 등). completed는 mark_completed 사용."""
    if hunt_id not in registry["hunts"]:
        return
    h = registry["hunts"][hunt_id]
    if h["status"] == status:
        return
    h["status"] = status
    h.setdefault("history", []).append({
        "at": datetime.now().isoformat(timespec="seconds"),
        "event": f"status→{status}",
    })


def sync_from_work_plan(registry: dict, sections: dict) -> list:
    """work-plan 섹션들에서 HUNT 상태를 읽어 registry에 반영.

    Returns: completed HUNT ID 리스트 (work-plan에서 제거 대상).

    - 각 section (active/in_progress/blocked/deferred/completed_*)에서 HUNT ID 수집
    - registry의 각 HUNT status를 해당 섹션에 맞게 갱신
    - completed 섹션의 HUNT는 mark_completed + 리스트에 포함 (호출자가 work-plan에서 제거)
    """
    section_to_status = {
        "active": "ready",
        "in_progress": "in_progress",
        "blocked": "blocked",
        "deferred": "deferred",
    }

    completed_ids = []

    # Active / In-progress / Blocked / Deferred 반영
    for key, status in section_to_status.items():
        text = sections.get(key, "")
        for m in re.finditer(r"###\s+\[HUNT-(\d+)\]", text):
            hid = f"HUNT-{int(m.group(1)):03d}"
            if hid in registry["hunts"]:
                update_status(registry, hid, status)

    # Completed 섹션 (recent + older) → mark_completed + removal 리스트
    for key in ("completed_recent", "completed_older"):
        text = sections.get(key, "")
        for m in re.finditer(r"###\s+\[HUNT-(\d+)\]", text):
            hid = f"HUNT-{int(m.group(1)):03d}"
            if hid in registry["hunts"]:
                if registry["hunts"][hid]["status"] != "completed":
                    mark_completed(registry, hid)
                completed_ids.append(hid)

    return completed_ids


def remove_cards_from_section_text(section_text: str, hunt_ids: set) -> str:
    """주어진 section body에서 특정 HUNT ID 카드 블록을 제거."""
    if not section_text or section_text.strip() == "_(없음)_" or not hunt_ids:
        return section_text

    lines = section_text.split("\n")
    result = []
    skip = False
    for line in lines:
        m = re.match(r"^###\s+\[HUNT-(\d+)\]", line)
        if m:
            hid = f"HUNT-{int(m.group(1)):03d}"
            skip = hid in hunt_ids
        elif re.match(r"^###\s+\[", line):
            # 다른 task 카드 시작 → skip 해제
            skip = False
        if not skip:
            result.append(line)

    cleaned = "\n".join(result).strip()
    return cleaned or "_(없음)_"


def bootstrap_from_work_plan(registry: dict, work_plan_text: str) -> int:
    """기존 work-plan의 HUNT 카드에서 registry를 역복원 (migration).

    Registry가 비어있거나 일부 HUNT가 누락된 경우 사용.
    Returns: 신규 추가된 HUNT 수.
    """
    if not work_plan_text:
        return 0

    added = 0
    # 각 HUNT 카드 블록 추출: "### [HUNT-NNN]" 다음부터 다음 "### [" 또는 EOF까지
    card_starts = [(m.start(), m.group(1)) for m in re.finditer(r"###\s+\[HUNT-(\d+)\]", work_plan_text)]
    other_starts = [m.start() for m in re.finditer(r"###\s+\[", work_plan_text)]

    for i, (start, num) in enumerate(card_starts):
        hid = f"HUNT-{int(num):03d}"
        if hid in registry["hunts"]:
            continue
        # 블록 끝 = 다음 "### [" 위치
        next_boundaries = [s for s in other_starts if s > start]
        end = min(next_boundaries) if next_boundaries else len(work_plan_text)
        block = work_plan_text[start:end]

        # Section 추론 (active/in_progress/blocked/completed): 헤더 위로 가장 최근 "## 🟡 Active" 류 찾기
        status = _infer_status_from_context(work_plan_text, start)

        covers_m = re.search(r"\*\*covers\*\*:\s*([^\n]+)", block)
        query_m = re.search(r"\*\*query\*\*:\s*`([^`]+)`", block)
        topic_m = re.search(r"\*\*무엇\*\*:\s*([^\n]+)", block)

        covers = []
        if covers_m:
            for raw in re.split(r"[,]\s*", covers_m.group(1).strip()):
                raw = raw.strip()
                if raw and not raw.startswith("("):
                    covers.append(normalize_cover(raw))

        now = datetime.now().isoformat(timespec="seconds")
        registry["hunts"][hid] = {
            "id": hid,
            "covers": covers,
            "query": query_m.group(1) if query_m else "",
            "topic": topic_m.group(1).strip() if topic_m else "",
            "source_file": "bootstrap",
            "status": status,
            "issued_at": now,
            "completed_at": now if status == "completed" else None,
            "reactivated_count": 0,
            "history": [
                {"at": now, "event": "bootstrapped_from_work_plan", "inferred_status": status},
            ],
        }
        added += 1
        n = int(num)
        if n >= registry["next_id"]:
            registry["next_id"] = n + 1
    return added


def _infer_status_from_context(work_plan_text: str, card_start: int) -> str:
    """카드 위치 앞에 가장 가까운 섹션 헤더를 찾아 status 추론."""
    preamble = work_plan_text[:card_start]
    section_markers = [
        ("## 🟡 Active", "ready"),
        ("## 🔵 In-progress", "in_progress"),
        ("## 🔴 Blocked", "blocked"),
        ("## ⚪ Deferred", "deferred"),
        ("## 🟢 Recent completed", "completed"),
        ("## 📜 Older completed", "completed"),
    ]
    best_pos = -1
    best_status = "ready"
    for marker, status in section_markers:
        pos = preamble.rfind(marker)
        if pos > best_pos:
            best_pos = pos
            best_status = status
    return best_status


# ──────────────────────────────────────────────────────────
# CLI (운영용 단순 조회·migration)
# ──────────────────────────────────────────────────────────

def _cli():
    import sys
    if len(sys.argv) < 3:
        print("Usage: hunt_registry.py <command> <project_name>")
        print("  commands: list | stats | bootstrap")
        sys.exit(1)

    cmd = sys.argv[1]
    project = sys.argv[2]
    root = Path("projects") / project
    reg = load(root)

    if cmd == "list":
        for hid, h in sorted(reg["hunts"].items()):
            print(f"{hid}  {h['status']:12}  {h['topic']}")
    elif cmd == "stats":
        counts = {}
        for h in reg["hunts"].values():
            counts[h["status"]] = counts.get(h["status"], 0) + 1
        print(f"Total HUNTs: {len(reg['hunts'])}")
        print(f"Next ID    : HUNT-{reg['next_id']:03d}")
        for s, c in sorted(counts.items()):
            print(f"  {s:12}: {c}")
    elif cmd == "bootstrap":
        wp = root / "work-plan.md"
        if not wp.exists():
            print(f"❌ work-plan.md 없음: {wp}")
            sys.exit(1)
        added = bootstrap_from_work_plan(reg, wp.read_text(encoding="utf-8"))
        save(root, reg)
        print(f"✅ bootstrap: {added}개 HUNT 추가 (next_id={reg['next_id']})")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    _cli()
