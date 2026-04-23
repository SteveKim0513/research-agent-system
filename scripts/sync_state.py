#!/usr/bin/env python3
"""
sync_state.py — Research-Agent 프로젝트의 아티팩트 sync 상태 관리 유틸리티.

.sync-state.json을 읽고/쓰고/갱신하여 다음 아티팩트들의 의존 관계를 추적한다:
- flow.md
- papers/collected/*.pdf
- papers/analyzed/*.md
- chapters/*.md
- final/*.md
- evaluations/latest/*

사용법:
    python scripts/sync_state.py init <project_name>
    python scripts/sync_state.py check <project_name>
    python scripts/sync_state.py update-flow <project_name>
    python scripts/sync_state.py update-paper <project_name> <paper_filename>
    python scripts/sync_state.py update-chapter <project_name> <chapter_filename>
    python scripts/sync_state.py update-evaluation <project_name>
    python scripts/sync_state.py update-final <project_name>
    python scripts/sync_state.py remove-paper <project_name> <paper_filename>
    python scripts/sync_state.py snapshot-chapters <project_name> <trigger> [chapter_filename]
        trigger: "pre-redraft", "chX-edit" 등의 태그 (폴더명에 포함)
        chapter_filename 지정 시 해당 챕터만 스냅샷, 미지정 시 chapters/ 전체
    python scripts/sync_state.py snapshot-critical-questions <project_name> <trigger>
        trigger: "post-research", "post-draft", "manual-update" 등
        critical-questions.md를 critical-questions.archive/{NNN}-{date}-{trigger}.md로 보존
    python scripts/sync_state.py snapshot-critical-commitments <project_name> <trigger>
        critical-commitments.md를 critical-commitments.archive/{NNN}-{date}-{trigger}.md로 보존
"""

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path


SCHEMA_VERSION = "1.0"


def project_root(project_name: str) -> Path:
    cwd = Path.cwd()
    candidate = cwd / "projects" / project_name
    if not candidate.exists():
        raise SystemExit(f"프로젝트 폴더 없음: {candidate}")
    return candidate


def state_path(project_name: str) -> Path:
    return project_root(project_name) / ".sync-state.json"


def file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]  # short form is enough for drift detection


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def empty_state(project_name: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_name": project_name,
        "updated_at": now_iso(),
        "flow_md": {"hash": "", "mtime": ""},
        "papers": {},     # filename.pdf -> {pdf_hash, analyzed_version, analyzed_flow_hash_at, analyzed_updated_at}
        "chapters": {},   # 01-introduction.md -> {hash, flow_hash_at_write, papers_used: {filename: version}}
        "evaluations": {
            "flow_hash_at_run": "",
            "chapter_hashes_at_run": {},
            "ran_at": "",
        },
        "final": {
            "chapter_hashes_at_build": {},
            "built_at": "",
        },
    }


def load_state(project_name: str) -> dict:
    p = state_path(project_name)
    if not p.exists():
        return empty_state(project_name)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(project_name: str, state: dict) -> None:
    state["updated_at"] = now_iso()
    p = state_path(project_name)
    with p.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ───────────────────────── Commands ─────────────────────────

def cmd_init(project_name: str) -> int:
    root = project_root(project_name)
    state = empty_state(project_name)

    # flow.md 초기 해시
    flow = root / "flow.md"
    if flow.exists():
        state["flow_md"]["hash"] = file_hash(flow)
        state["flow_md"]["mtime"] = now_iso()

    save_state(project_name, state)
    print(f"✅ .sync-state.json 생성 완료: {state_path(project_name)}")
    return 0


def cmd_update_flow(project_name: str) -> int:
    state = load_state(project_name)
    flow = project_root(project_name) / "flow.md"
    state["flow_md"]["hash"] = file_hash(flow)
    state["flow_md"]["mtime"] = now_iso()
    save_state(project_name, state)
    print(f"✅ flow.md 해시 갱신: {state['flow_md']['hash']}")
    return 0


def cmd_update_paper(project_name: str, paper_filename: str) -> int:
    state = load_state(project_name)
    root = project_root(project_name)
    pdf = root / "papers" / "collected" / paper_filename
    if not pdf.exists():
        print(f"⚠️  PDF 없음: {pdf}", file=sys.stderr)
        return 1

    entry = state["papers"].get(paper_filename, {
        "pdf_hash": "",
        "analyzed_version": "v1",
        "analyzed_flow_hash_at": state["flow_md"]["hash"],
        "analyzed_updated_at": now_iso(),
    })
    # re-analysis → version bump
    if entry.get("pdf_hash") and entry["analyzed_flow_hash_at"] != state["flow_md"]["hash"]:
        prev = entry.get("analyzed_version", "v1")
        try:
            n = int(prev.lstrip("v")) + 1
        except ValueError:
            n = 2
        entry["analyzed_version"] = f"v{n}"

    entry["pdf_hash"] = file_hash(pdf)
    entry["analyzed_flow_hash_at"] = state["flow_md"]["hash"]
    entry["analyzed_updated_at"] = now_iso()
    state["papers"][paper_filename] = entry
    save_state(project_name, state)
    print(f"✅ 논문 상태 갱신: {paper_filename} → {entry['analyzed_version']}")
    return 0


def cmd_snapshot_chapters(project_name: str, trigger: str, chapter_filename: str = None) -> int:
    """chapters/의 현재 상태를 chapters/archive/{NNN}-{date}-{trigger}/에 스냅샷.

    chapter_filename 지정 시 단일 파일만, 미지정 시 chapters/ 전체.
    Before-overwrite 보존용.
    """
    root = project_root(project_name)
    chap_dir = root / "chapters"
    if not chap_dir.exists():
        print(f"⚠️  chapters/ 폴더 없음: {chap_dir}", file=sys.stderr)
        return 1

    archive_dir = chap_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 다음 순번 계산
    existing = sorted([p for p in archive_dir.iterdir() if p.is_dir() and p.name[:3].isdigit()])
    next_n = len(existing) + 1
    next_tag = f"{next_n:03d}"
    date = datetime.now().strftime("%Y-%m-%d")
    folder_name = f"{next_tag}-{date}-{trigger}"
    dest_dir = archive_dir / folder_name

    if chapter_filename:
        src = chap_dir / chapter_filename
        if not src.exists():
            print(f"⚠️  챕터 없음: {src}", file=sys.stderr)
            return 1
        dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / chapter_filename).write_bytes(src.read_bytes())
        print(f"✅ 챕터 스냅샷: {dest_dir}/{chapter_filename}")
    else:
        chapter_files = [p for p in chap_dir.glob("*.md") if p.is_file()]
        if not chapter_files:
            print("⚠️  스냅샷할 챕터 없음 (chapters/ 비어있음)", file=sys.stderr)
            return 0
        dest_dir.mkdir(parents=True, exist_ok=True)
        for src in chapter_files:
            (dest_dir / src.name).write_bytes(src.read_bytes())
        print(f"✅ 전체 챕터 스냅샷: {dest_dir} ({len(chapter_files)}개 파일)")
    return 0


def cmd_snapshot_evaluation(project_name: str, trigger: str) -> int:
    """evaluations/latest/ 전체를 evaluations/archive/{NNN}-{date}-{trigger}/로 스냅샷.

    병렬 평가 아키텍처에서 orchestrator가 단계 3에서 호출.
    """
    import shutil
    root = project_root(project_name)
    latest_dir = root / "evaluations" / "latest"
    if not latest_dir.exists():
        print(f"ℹ️  evaluations/latest/ 없음 — 스냅샷 스킵 (첫 평가)")
        return 0

    archive_dir = root / "evaluations" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted([p for p in archive_dir.iterdir() if p.is_dir() and p.name[:3].isdigit()])
    next_n = len(existing) + 1
    next_tag = f"{next_n:03d}"
    date = datetime.now().strftime("%Y-%m-%d")
    folder_name = f"{next_tag}-{date}-{trigger}"
    dest_dir = archive_dir / folder_name

    # 재귀 복사
    shutil.copytree(latest_dir, dest_dir)
    n_files = sum(1 for _ in dest_dir.rglob("*") if _.is_file())
    print(f"✅ 평가 스냅샷: {dest_dir} ({n_files}개 파일)")
    return 0


def cmd_snapshot_critical_commitments(project_name: str, trigger: str) -> int:
    """critical-commitments.md를 critical-commitments.archive/{NNN}-{date}-{trigger}.md로 보존."""
    root = project_root(project_name)
    src = root / "critical-commitments.md"
    if not src.exists():
        print(f"ℹ️  critical-commitments.md 없음 — 스냅샷 스킵")
        return 0

    archive_dir = root / "critical-commitments.archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted([p for p in archive_dir.iterdir() if p.is_file() and p.name[:3].isdigit()])
    next_n = len(existing) + 1
    next_tag = f"{next_n:03d}"
    date = datetime.now().strftime("%Y-%m-%d")
    dest = archive_dir / f"{next_tag}-{date}-{trigger}.md"
    dest.write_bytes(src.read_bytes())
    print(f"✅ critical-commitments 스냅샷: {dest}")
    return 0


def cmd_snapshot_critical_questions(project_name: str, trigger: str) -> int:
    """critical-questions.md를 critical-questions.archive/{NNN}-{date}-{trigger}.md로 보존.

    critical-companion이 새 버전 생성 직전 호출.
    """
    root = project_root(project_name)
    src = root / "critical-questions.md"
    if not src.exists():
        print(f"ℹ️  critical-questions.md 없음 (초기 버전) — 스냅샷 스킵")
        return 0

    archive_dir = root / "critical-questions.archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted([p for p in archive_dir.iterdir() if p.is_file() and p.name[:3].isdigit()])
    next_n = len(existing) + 1
    next_tag = f"{next_n:03d}"
    date = datetime.now().strftime("%Y-%m-%d")
    dest = archive_dir / f"{next_tag}-{date}-{trigger}.md"
    dest.write_bytes(src.read_bytes())
    print(f"✅ critical-questions 스냅샷: {dest}")
    return 0


def cmd_remove_paper(project_name: str, paper_filename: str) -> int:
    state = load_state(project_name)
    if paper_filename in state["papers"]:
        del state["papers"][paper_filename]
        save_state(project_name, state)
        print(f"✅ 논문 상태 제거: {paper_filename}")
    else:
        print(f"⚠️  상태에 없음: {paper_filename}", file=sys.stderr)
    return 0


def cmd_update_chapter(project_name: str, chapter_filename: str) -> int:
    state = load_state(project_name)
    root = project_root(project_name)
    chap = root / "chapters" / chapter_filename
    if not chap.exists():
        print(f"⚠️  챕터 없음: {chap}", file=sys.stderr)
        return 1

    papers_used = {
        fname: info.get("analyzed_version", "v1")
        for fname, info in state["papers"].items()
    }
    state["chapters"][chapter_filename] = {
        "hash": file_hash(chap),
        "flow_hash_at_write": state["flow_md"]["hash"],
        "papers_used": papers_used,
        "written_at": now_iso(),
    }
    save_state(project_name, state)
    print(f"✅ 챕터 상태 갱신: {chapter_filename}")
    return 0


def cmd_update_evaluation(project_name: str) -> int:
    state = load_state(project_name)
    root = project_root(project_name)
    state["evaluations"]["flow_hash_at_run"] = state["flow_md"]["hash"]
    state["evaluations"]["ran_at"] = now_iso()

    chapter_hashes = {}
    chap_dir = root / "chapters"
    if chap_dir.exists():
        for chap in sorted(chap_dir.glob("*.md")):
            chapter_hashes[chap.name] = file_hash(chap)
    state["evaluations"]["chapter_hashes_at_run"] = chapter_hashes
    save_state(project_name, state)
    print(f"✅ 평가 상태 갱신")
    return 0


def cmd_update_final(project_name: str) -> int:
    state = load_state(project_name)
    root = project_root(project_name)
    chapter_hashes = {}
    chap_dir = root / "chapters"
    if chap_dir.exists():
        for chap in sorted(chap_dir.glob("*.md")):
            chapter_hashes[chap.name] = file_hash(chap)
    state["final"]["chapter_hashes_at_build"] = chapter_hashes
    state["final"]["built_at"] = now_iso()
    save_state(project_name, state)
    print(f"✅ final 상태 갱신")
    return 0


def stale_priority(stale: dict) -> int:
    """각 stale 항목의 긴급도 점수. 높을수록 downstream 영향 큼."""
    kind = stale.get("kind", "")
    if kind == "flow_changed":
        return 30  # 가장 많은 downstream 무효화
    if kind == "paper_removed":
        dangling = stale.get("dangling_in_chapters", {}) or {}
        return 20 + len(dangling) * 10  # dangling 많을수록 급함
    if kind == "paper_added_untracked":
        impacted = stale.get("impacted", []) or []
        return 8 + len(impacted) * 4
    if kind == "chapter_paper_version_drift":
        details = stale.get("details", []) or []
        return 10 * len(details)
    if kind == "chapter_flow_drift":
        impacted = stale.get("impacted", []) or []
        return 15 * len(impacted)
    if kind == "final_stale":
        return 5
    if kind == "evaluation_stale":
        return 10
    if kind == "commitment_unfulfilled":
        details = stale.get("details", []) or []
        return 20 + len(details) * 3  # UNFULFILLED·CONFLICTING per entry
    return 0


def stale_tier(score: int) -> str:
    if score >= 30:
        return "P1-Critical"
    if score >= 15:
        return "P2-High"
    return "P3-Medium"


def dependency_order(stale: dict) -> int:
    """의존성 해소 순서. 낮을수록 먼저 해결해야 함."""
    order_map = {
        "paper_added_untracked": 1,       # 새 논문 처리 우선
        "paper_removed": 2,               # dangling 빨리 해소
        "flow_changed": 3,                # cascade 시작점
        "chapter_paper_version_drift": 4, # papers 정리 후
        "chapter_flow_drift": 5,          # papers 정리 후
        "commitment_unfulfilled": 5,      # chapter 정리와 함께 해소 (chapters 수정으로)
        "final_stale": 6,                 # chapters 정리 후
        "evaluation_stale": 7,            # 모든 것 정리 후 마지막
    }
    return order_map.get(stale.get("kind", ""), 99)


def cmd_check(project_name: str) -> int:
    """현재 아티팩트들의 해시를 계산하여 state와 비교, stale 항목을 보고한다."""
    state = load_state(project_name)
    root = project_root(project_name)
    stales = []

    # 1. flow.md 변경 감지
    flow = root / "flow.md"
    current_flow_hash = file_hash(flow)
    flow_changed = current_flow_hash and current_flow_hash != state["flow_md"]["hash"]
    if flow_changed:
        stales.append({
            "kind": "flow_changed",
            "msg": "flow.md가 변경됨 — 다음 자식 아티팩트 재생성 필요",
            "impacted": [
                "analyzed/*.md (논문 재분석 권장)",
                "evaluations/latest/ (재평가 권장)",
                "chapters/*.md (sync 경고 — 내용 반영 필요할 수 있음)",
            ],
            "resolve": '"논문 재분석해줘" 후 "평가해줘"',
        })

    # 2. 논문 추가/삭제 감지
    collected = root / "papers" / "collected"
    actual_pdfs = set()
    if collected.exists():
        actual_pdfs = {p.name for p in collected.glob("*.pdf")}
    tracked_pdfs = set(state["papers"].keys())
    added = actual_pdfs - tracked_pdfs
    removed = tracked_pdfs - actual_pdfs
    if added:
        stales.append({
            "kind": "paper_added_untracked",
            "msg": f"collected/에 미추적 논문 {len(added)}개",
            "impacted": list(added),
            "resolve": '"새 논문 처리해줘"',
        })
    if removed:
        # dangling citation 탐지
        dangling = detect_dangling_citations(root, removed)
        stales.append({
            "kind": "paper_removed",
            "msg": f"추적 중이던 논문 {len(removed)}개가 collected/에서 제거됨",
            "impacted": list(removed),
            "dangling_in_chapters": dangling,
            "resolve": '"논문 제거해줘: {파일명}" 또는 "sync 복구해줘"',
        })

    # 3. 챕터 vs 논문 버전 sync 감지
    chap_sync_issues = []
    for chap_name, chap_info in state["chapters"].items():
        for pname, used_version in chap_info.get("papers_used", {}).items():
            cur = state["papers"].get(pname, {}).get("analyzed_version", "")
            if cur and cur != used_version:
                chap_sync_issues.append({
                    "chapter": chap_name,
                    "paper": pname,
                    "used": used_version,
                    "current": cur,
                })
    if chap_sync_issues:
        stales.append({
            "kind": "chapter_paper_version_drift",
            "msg": f"챕터 {len(chap_sync_issues)}건이 구버전 논문 분석 기반",
            "details": chap_sync_issues,
            "resolve": '"Chapter X 수정해줘: 새 분석 반영"',
        })

    # 4. 챕터 vs flow sync
    flow_drift_chapters = []
    for chap_name, chap_info in state["chapters"].items():
        if chap_info.get("flow_hash_at_write") != state["flow_md"]["hash"]:
            flow_drift_chapters.append(chap_name)
    if flow_drift_chapters:
        stales.append({
            "kind": "chapter_flow_drift",
            "msg": f"챕터 {len(flow_drift_chapters)}개가 구 flow.md 기반",
            "impacted": flow_drift_chapters,
            "resolve": '"Chapter X 수정해줘"',
        })

    # 5. final vs chapters sync
    current_chap_hashes = {}
    chap_dir = root / "chapters"
    if chap_dir.exists():
        for chap in sorted(chap_dir.glob("*.md")):
            current_chap_hashes[chap.name] = file_hash(chap)
    built_hashes = state["final"].get("chapter_hashes_at_build", {})
    final_stale = False
    if built_hashes:  # final이 한 번이라도 만들어졌을 때만
        for name, h in current_chap_hashes.items():
            if built_hashes.get(name) != h:
                final_stale = True
                break
    if final_stale:
        stales.append({
            "kind": "final_stale",
            "msg": "final/complete-draft.* 가 chapters의 현재 상태와 불일치",
            "resolve": '"최종 통합해줘"',
        })

    # 6a. commitment 반영 상태 (critical-commitments.md의 UNFULFILLED/CONFLICTING 파싱)
    commitments_file = root / "critical-commitments.md"
    if commitments_file.exists():
        try:
            text = commitments_file.read_text(encoding="utf-8")
            unfulfilled_count = text.count("🔴 UNFULFILLED")
            conflicting_count = text.count("⚠️ CONFLICTING")
            partial_count = text.count("🟡 PARTIAL")
            problematic = unfulfilled_count + conflicting_count
            if problematic > 0:
                stales.append({
                    "kind": "commitment_unfulfilled",
                    "msg": f"Critical commitments 미이행 {problematic}건 (UNFULFILLED {unfulfilled_count} + CONFLICTING {conflicting_count})",
                    "details": ["critical-commitments.md 참조"] * problematic,
                    "partial_count": partial_count,
                    "resolve": '"Chapter X 수정해줘"로 commitment 해소, 또는 "질문 업데이트해줘"로 답변 철회',
                })
        except Exception:
            pass

    # 6. evaluation vs flow/chapters sync
    eval_flow_stale = (
        state["evaluations"].get("flow_hash_at_run")
        and state["evaluations"]["flow_hash_at_run"] != state["flow_md"]["hash"]
    )
    eval_chap_hashes = state["evaluations"].get("chapter_hashes_at_run", {})
    eval_chap_stale = eval_chap_hashes and eval_chap_hashes != current_chap_hashes
    if eval_flow_stale or eval_chap_stale:
        stales.append({
            "kind": "evaluation_stale",
            "msg": "evaluations/latest/ 가 현재 flow/chapters와 불일치",
            "resolve": '"평가해줘"',
        })

    # priority 점수 + 등급 부여
    for s in stales:
        s["score"] = stale_priority(s)
        s["priority"] = stale_tier(s["score"])
        s["dependency_order"] = dependency_order(s)

    # 긴급도 순 (displayed)
    stales_by_urgency = sorted(stales, key=lambda s: -s["score"])

    # 의존성 해소 순서 (execution)
    stales_by_dependency = sorted(stales, key=lambda s: (s["dependency_order"], -s["score"]))
    ordered_plan = [
        {
            "step": i + 1,
            "priority": s["priority"],
            "kind": s["kind"],
            "score": s["score"],
            "resolve": s.get("resolve", ""),
        }
        for i, s in enumerate(stales_by_dependency)
    ]

    # 등급별 집계
    tier_counts = {"P1-Critical": 0, "P2-High": 0, "P3-Medium": 0}
    for s in stales:
        tier_counts[s["priority"]] = tier_counts.get(s["priority"], 0) + 1

    result = {
        "project": project_name,
        "checked_at": now_iso(),
        "stale_count": len(stales),
        "tier_counts": tier_counts,
        "stales": stales_by_urgency,
        "ordered_resolution_plan": ordered_plan,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not stales else 1


def detect_dangling_citations(root: Path, removed_papers: set) -> dict:
    """삭제된 논문을 인용하는 챕터 파일들을 탐지.

    간단한 방식: 파일 이름의 저자 부분을 챕터 본문에서 문자열 검색.
    """
    dangling = {}
    chap_dir = root / "chapters"
    if not chap_dir.exists():
        return dangling
    for chap in chap_dir.glob("*.md"):
        try:
            text = chap.read_text(encoding="utf-8")
        except Exception:
            continue
        hits = []
        for pname in removed_papers:
            # e.g. "Kroupin_2025.pdf" → candidate strings
            stem = pname.rsplit(".", 1)[0]
            # Heuristic: first token as author surname, last 4 digits as year
            parts = stem.split("_")
            author = parts[0] if parts else stem
            year = ""
            for p in parts:
                if p.isdigit() and len(p) == 4:
                    year = p
                    break
            for needle in [f"{author} ({year})", f"{author} et al. ({year})", f"({author}, {year})", f"({author} et al., {year})"]:
                if needle and needle in text:
                    hits.append(needle)
        if hits:
            dangling[chap.name] = hits
    return dangling


# ───────────────────────── CLI ─────────────────────────

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    args = argv[2:]

    try:
        if cmd == "init" and len(args) == 1:
            return cmd_init(args[0])
        if cmd == "check" and len(args) == 1:
            return cmd_check(args[0])
        if cmd == "update-flow" and len(args) == 1:
            return cmd_update_flow(args[0])
        if cmd == "update-paper" and len(args) == 2:
            return cmd_update_paper(args[0], args[1])
        if cmd == "update-chapter" and len(args) == 2:
            return cmd_update_chapter(args[0], args[1])
        if cmd == "update-evaluation" and len(args) == 1:
            return cmd_update_evaluation(args[0])
        if cmd == "update-final" and len(args) == 1:
            return cmd_update_final(args[0])
        if cmd == "remove-paper" and len(args) == 2:
            return cmd_remove_paper(args[0], args[1])
        if cmd == "snapshot-evaluation" and len(args) == 2:
            return cmd_snapshot_evaluation(args[0], args[1])
        if cmd == "snapshot-chapters" and 2 <= len(args) <= 3:
            chapter_fn = args[2] if len(args) == 3 else None
            return cmd_snapshot_chapters(args[0], args[1], chapter_fn)
        if cmd == "snapshot-critical-questions" and len(args) == 2:
            return cmd_snapshot_critical_questions(args[0], args[1])
        if cmd == "snapshot-critical-commitments" and len(args) == 2:
            return cmd_snapshot_critical_commitments(args[0], args[1])
    except SystemExit:
        raise
    except Exception as e:
        print(f"❌ 오류: {e}", file=sys.stderr)
        return 2

    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
