#!/usr/bin/env python3
"""
sync_state.py — Research-Agent 프로젝트의 아티팩트 sync 상태 관리 유틸리티.

v2 폴더 구조를 기준으로 동작한다:
    projects/{NAME}/flow/flow.md + flow/claim-extraction-flow.md + flow/history/
    projects/{NAME}/chapters/*.md + chapters/claim-extraction-draft.md + chapters/history/{chapter_id}/
    projects/{NAME}/work-plan.md + work-plan.archive/
    projects/{NAME}/evaluations/latest/ + evaluations/archive/{NNN}/manifest.json

사용법:
    python scripts/sync_state.py init <project_name>
    python scripts/sync_state.py check <project_name>
    python scripts/sync_state.py update-flow <project_name>
    python scripts/sync_state.py update-paper <project_name> <paper_filename>
    python scripts/sync_state.py update-chapter <project_name> <chapter_filename>
    python scripts/sync_state.py update-evaluation <project_name>
    python scripts/sync_state.py update-final <project_name>
    python scripts/sync_state.py remove-paper <project_name> <paper_filename>

Snapshot commands (before-overwrite 보존):
    python scripts/sync_state.py snapshot-flow <project_name> <trigger>
        flow/flow.md + flow/claim-extraction-flow.md를 flow/history/{NNN}-{date}-{trigger}/로
    python scripts/sync_state.py snapshot-chapter <project_name> <trigger> <chapter_filename>
        단일 챕터 + claim-extraction-draft.md를 chapters/history/{chapter_id}/{NNN}-{date}-{trigger}/로
    python scripts/sync_state.py snapshot-chapters <project_name> <trigger>
        전체 챕터 일괄 (각 챕터에 개별 NNN 생성) + draft 분석 쌍
    python scripts/sync_state.py snapshot-work-plan <project_name> <trigger>
        work-plan.md를 work-plan.archive/{NNN}-{date}-{trigger}.md로
    python scripts/sync_state.py snapshot-evaluation <project_name> <trigger>
        evaluations/latest/를 evaluations/archive/{NNN}-{date}-{trigger}/로 (증분 — manifest.json 포함)
    python scripts/sync_state.py snapshot-critical-questions <project_name> <trigger>
    python scripts/sync_state.py snapshot-critical-commitments <project_name> <trigger>
"""

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path


SCHEMA_VERSION = "2.0"


# ───────────────────────── Path helpers ─────────────────────────

def project_root(project_name: str) -> Path:
    cwd = Path.cwd()
    candidate = cwd / "projects" / project_name
    if not candidate.exists():
        raise SystemExit(f"프로젝트 폴더 없음: {candidate}")
    return candidate


def state_path(project_name: str) -> Path:
    return project_root(project_name) / ".sync-state.json"


def flow_md_path(root: Path) -> Path:
    """flow.md 경로 (v2: flow/flow.md, v1 fallback: 루트 flow.md)."""
    v2 = root / "flow" / "flow.md"
    if v2.exists():
        return v2
    legacy = root / "flow.md"
    return legacy if legacy.exists() else v2  # 존재하지 않으면 v2 경로 반환


def claim_extraction_flow_path(root: Path) -> Path:
    return root / "flow" / "claim-extraction-flow.md"


def claim_extraction_draft_path(root: Path) -> Path:
    return root / "chapters" / "claim-extraction-draft.md"


def work_plan_path(root: Path) -> Path:
    """work-plan.md 경로 (v2: 루트 work-plan.md, v1 fallback: evaluations/latest/work-plan.md)."""
    v2 = root / "work-plan.md"
    if v2.exists():
        return v2
    legacy = root / "evaluations" / "latest" / "work-plan.md"
    return legacy if legacy.exists() else v2


def chapter_files(root: Path) -> list:
    """chapters/의 실제 챕터 파일 목록 (claim-extraction-draft.md 제외)."""
    chap_dir = root / "chapters"
    if not chap_dir.exists():
        return []
    return sorted([
        p for p in chap_dir.glob("*.md")
        if p.is_file() and p.name != "claim-extraction-draft.md"
    ])


# ───────────────────────── Hash / time ─────────────────────────

def file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def today_tag() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def next_sequence(parent: Path, *, dirs_only: bool = True) -> int:
    """parent 안의 {NNN}-* 엔트리 중 가장 큰 NNN + 1 반환."""
    if not parent.exists():
        return 1
    entries = []
    for p in parent.iterdir():
        if dirs_only and not p.is_dir():
            continue
        if not dirs_only and not p.is_file():
            continue
        if len(p.name) >= 3 and p.name[:3].isdigit():
            try:
                entries.append(int(p.name[:3]))
            except ValueError:
                continue
    return (max(entries) + 1) if entries else 1


# ───────────────────────── State ─────────────────────────

def empty_state(project_name: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_name": project_name,
        "updated_at": now_iso(),
        "flow_md": {"hash": "", "mtime": ""},
        "papers": {},
        "chapters": {},
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


# ───────────────────────── Commands: state updates ─────────────────────────

def cmd_init(project_name: str) -> int:
    root = project_root(project_name)
    state = empty_state(project_name)

    flow = flow_md_path(root)
    if flow.exists():
        state["flow_md"]["hash"] = file_hash(flow)
        state["flow_md"]["mtime"] = now_iso()

    save_state(project_name, state)
    print(f"✅ .sync-state.json 생성 완료: {state_path(project_name)}")
    return 0


def cmd_update_flow(project_name: str) -> int:
    state = load_state(project_name)
    flow = flow_md_path(project_root(project_name))
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

    chapter_hashes = {chap.name: file_hash(chap) for chap in chapter_files(root)}
    state["evaluations"]["chapter_hashes_at_run"] = chapter_hashes
    save_state(project_name, state)
    print(f"✅ 평가 상태 갱신")
    return 0


def cmd_update_final(project_name: str) -> int:
    state = load_state(project_name)
    root = project_root(project_name)
    chapter_hashes = {chap.name: file_hash(chap) for chap in chapter_files(root)}
    state["final"]["chapter_hashes_at_build"] = chapter_hashes
    state["final"]["built_at"] = now_iso()
    save_state(project_name, state)
    print(f"✅ final 상태 갱신")
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


# ───────────────────────── Commands: snapshots ─────────────────────────

def cmd_snapshot_flow(project_name: str, trigger: str) -> int:
    """flow/flow.md + flow/claim-extraction-flow.md를 flow/history/{NNN}-{date}-{trigger}/로."""
    root = project_root(project_name)
    flow_dir = root / "flow"
    src_flow = flow_dir / "flow.md"
    src_claims = flow_dir / "claim-extraction-flow.md"
    if not src_flow.exists():
        print(f"ℹ️  flow/flow.md 없음 — 스냅샷 스킵")
        return 0

    history_dir = flow_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    seq = next_sequence(history_dir, dirs_only=True)
    folder_name = f"{seq:03d}-{today_tag()}-{trigger}"
    dest_dir = history_dir / folder_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    (dest_dir / "flow.md").write_bytes(src_flow.read_bytes())
    if src_claims.exists():
        (dest_dir / "claim-extraction-flow.md").write_bytes(src_claims.read_bytes())
    print(f"✅ flow 스냅샷: {dest_dir}")
    return 0


def cmd_snapshot_chapter(project_name: str, trigger: str, chapter_filename: str) -> int:
    """단일 챕터 + 현재 claim-extraction-draft.md를 chapters/history/{chapter_id}/{NNN}-*/에."""
    root = project_root(project_name)
    chap_dir = root / "chapters"
    src_chap = chap_dir / chapter_filename
    if not src_chap.exists():
        print(f"⚠️  챕터 없음: {src_chap}", file=sys.stderr)
        return 1

    chapter_id = chapter_filename.rsplit(".", 1)[0]
    history_dir = chap_dir / "history" / chapter_id
    history_dir.mkdir(parents=True, exist_ok=True)
    seq = next_sequence(history_dir, dirs_only=True)
    folder_name = f"{seq:03d}-{today_tag()}-{trigger}"
    dest_dir = history_dir / folder_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    (dest_dir / chapter_filename).write_bytes(src_chap.read_bytes())
    src_draft = claim_extraction_draft_path(root)
    if src_draft.exists():
        (dest_dir / "claim-extraction-draft.md").write_bytes(src_draft.read_bytes())
    print(f"✅ 챕터 스냅샷: {dest_dir}")
    return 0


def cmd_snapshot_chapters(project_name: str, trigger: str, chapter_filename: str = None) -> int:
    """전체 챕터 일괄 스냅샷 (pre-redraft 시). 각 챕터마다 개별 NNN으로 snapshot-chapter."""
    if chapter_filename:
        return cmd_snapshot_chapter(project_name, trigger, chapter_filename)

    root = project_root(project_name)
    chaps = chapter_files(root)
    if not chaps:
        print("⚠️  스냅샷할 챕터 없음 (chapters/ 비어있음)", file=sys.stderr)
        return 0

    for chap in chaps:
        cmd_snapshot_chapter(project_name, trigger, chap.name)
    return 0


def cmd_snapshot_work_plan(project_name: str, trigger: str) -> int:
    """work-plan.md를 work-plan.archive/{NNN}-{date}-{trigger}.md로."""
    root = project_root(project_name)
    src = root / "work-plan.md"
    if not src.exists():
        print(f"ℹ️  work-plan.md 없음 — 스냅샷 스킵")
        return 0

    archive_dir = root / "work-plan.archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    seq = next_sequence(archive_dir, dirs_only=False)
    dest = archive_dir / f"{seq:03d}-{today_tag()}-{trigger}.md"
    dest.write_bytes(src.read_bytes())
    print(f"✅ work-plan 스냅샷: {dest}")
    return 0


def cmd_snapshot_evaluation(project_name: str, trigger: str) -> int:
    """evaluations/latest/의 증분 스냅샷.

    - 각 파일의 해시를 이전 manifest의 해시와 비교
    - 해시가 동일하면: manifest에 이전 경로 참조만 기록 (파일 복사 X)
    - 해시가 다르면: 실제 복사 + manifest에 현재 스냅샷 경로 기록
    - evaluation.md는 항상 복사 (집계 결과이므로 매번 재생성됨)
    """
    root = project_root(project_name)
    latest_dir = root / "evaluations" / "latest"
    if not latest_dir.exists():
        print(f"ℹ️  evaluations/latest/ 없음 — 스냅샷 스킵 (첫 평가)")
        return 0

    archive_dir = root / "evaluations" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    seq = next_sequence(archive_dir, dirs_only=True)
    folder_name = f"{seq:03d}-{today_tag()}-{trigger}"
    dest_dir = archive_dir / folder_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 이전 매니페스트 로드 (있으면)
    prev_archives = sorted(
        [p for p in archive_dir.iterdir()
         if p.is_dir() and p.name[:3].isdigit() and p.name != folder_name],
        key=lambda p: int(p.name[:3]),
    )
    prev_manifest = {"files": {}}
    if prev_archives:
        prev_mf_file = prev_archives[-1] / "manifest.json"
        if prev_mf_file.exists():
            try:
                prev_manifest = json.loads(prev_mf_file.read_text(encoding="utf-8"))
            except Exception:
                prev_manifest = {"files": {}}

    manifest = {
        "version": "v2",
        "snapshot_tag": folder_name,
        "created_at": now_iso(),
        "trigger": trigger,
        "files": {},
    }

    n_copy = 0
    n_ref = 0

    for src in latest_dir.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(latest_dir).as_posix()
        h = file_hash(src)
        prev_meta = prev_manifest.get("files", {}).get(rel, {})
        prev_hash = prev_meta.get("hash", "")
        prev_ref = prev_meta.get("stored_at", "")
        always_copy = rel == "evaluation.md"

        if not always_copy and prev_hash == h and prev_ref:
            manifest["files"][rel] = {
                "hash": h,
                "stored_at": prev_ref,  # 이전 실제 경로 상속
                "copy_mode": "reference",
            }
            n_ref += 1
        else:
            dest_file = dest_dir / rel
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_bytes(src.read_bytes())
            manifest["files"][rel] = {
                "hash": h,
                "stored_at": f"{folder_name}/{rel}",
                "copy_mode": "copy",
            }
            n_copy += 1

    (dest_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"✅ 평가 스냅샷 (증분): {dest_dir} — 복사 {n_copy}개 / 참조 {n_ref}개")
    return 0


def cmd_snapshot_critical_commitments(project_name: str, trigger: str) -> int:
    root = project_root(project_name)
    src = root / "critical-commitments.md"
    if not src.exists():
        print(f"ℹ️  critical-commitments.md 없음 — 스냅샷 스킵")
        return 0

    archive_dir = root / "critical-commitments.archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    seq = next_sequence(archive_dir, dirs_only=False)
    dest = archive_dir / f"{seq:03d}-{today_tag()}-{trigger}.md"
    dest.write_bytes(src.read_bytes())
    print(f"✅ critical-commitments 스냅샷: {dest}")
    return 0


def cmd_snapshot_critical_questions(project_name: str, trigger: str) -> int:
    root = project_root(project_name)
    src = root / "critical-questions.md"
    if not src.exists():
        print(f"ℹ️  critical-questions.md 없음 (초기 버전) — 스냅샷 스킵")
        return 0

    archive_dir = root / "critical-questions.archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    seq = next_sequence(archive_dir, dirs_only=False)
    dest = archive_dir / f"{seq:03d}-{today_tag()}-{trigger}.md"
    dest.write_bytes(src.read_bytes())
    print(f"✅ critical-questions 스냅샷: {dest}")
    return 0


# ───────────────────────── Commands: check ─────────────────────────

def stale_priority(stale: dict) -> int:
    kind = stale.get("kind", "")
    if kind == "flow_changed":
        return 30
    if kind == "paper_removed":
        dangling = stale.get("dangling_in_chapters", {}) or {}
        return 20 + len(dangling) * 10
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
        return 20 + len(details) * 3
    if kind == "claim_extraction_stale":
        impacted = stale.get("impacted", []) or []
        return 12 + len(impacted) * 3
    return 0


def stale_tier(score: int) -> str:
    if score >= 30:
        return "P1-Critical"
    if score >= 15:
        return "P2-High"
    return "P3-Medium"


def dependency_order(stale: dict) -> int:
    order_map = {
        "paper_added_untracked": 1,
        "paper_removed": 2,
        "flow_changed": 3,
        "claim_extraction_stale": 4,
        "chapter_paper_version_drift": 5,
        "chapter_flow_drift": 6,
        "commitment_unfulfilled": 6,
        "final_stale": 7,
        "evaluation_stale": 8,
    }
    return order_map.get(stale.get("kind", ""), 99)


def cmd_check(project_name: str) -> int:
    state = load_state(project_name)
    root = project_root(project_name)
    stales = []

    # 1. flow 변경 감지
    flow = flow_md_path(root)
    current_flow_hash = file_hash(flow)
    flow_changed = current_flow_hash and current_flow_hash != state["flow_md"]["hash"]
    if flow_changed:
        stales.append({
            "kind": "flow_changed",
            "msg": "flow/flow.md가 변경됨 — 다음 자식 아티팩트 재생성 필요",
            "impacted": [
                "flow/claim-extraction-flow.md (재분석 필요)",
                "analyzed/*.md (논문 재분석 권장)",
                "evaluations/latest/ (재평가 권장)",
                "chapters/*.md (sync 경고 — 내용 반영 필요할 수 있음)",
            ],
            "resolve": '"평가해줘" (claim-extractor 자동 호출됨)',
        })

    # 1b. claim-extraction stale 감지
    ce_flow = claim_extraction_flow_path(root)
    ce_stale_sources = []
    if flow.exists() and ce_flow.exists():
        try:
            if flow.stat().st_mtime > ce_flow.stat().st_mtime:
                ce_stale_sources.append("flow.md > claim-extraction-flow.md (flow 수정 후 재분석 필요)")
        except Exception:
            pass

    ce_draft = claim_extraction_draft_path(root)
    if ce_draft.exists():
        for chap in chapter_files(root):
            try:
                if chap.stat().st_mtime > ce_draft.stat().st_mtime:
                    ce_stale_sources.append(
                        f"chapters/{chap.name} > claim-extraction-draft.md (챕터 수정 후 재분석 필요)"
                    )
            except Exception:
                continue
    elif chapter_files(root):
        ce_stale_sources.append("claim-extraction-draft.md 미생성 (챕터 있음에도)")

    if ce_stale_sources:
        stales.append({
            "kind": "claim_extraction_stale",
            "msg": f"claim-extraction 재분석 필요 ({len(ce_stale_sources)}건)",
            "impacted": ce_stale_sources,
            "resolve": '"평가해줘" 실행 시 자동 갱신',
        })

    # 2. 논문 추가/삭제
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
        dangling = detect_dangling_citations(root, removed)
        stales.append({
            "kind": "paper_removed",
            "msg": f"추적 중이던 논문 {len(removed)}개가 collected/에서 제거됨",
            "impacted": list(removed),
            "dangling_in_chapters": dangling,
            "resolve": '"논문 제거해줘: {파일명}" 또는 "sync 복구해줘"',
        })

    # 3. 챕터 vs 논문 버전 sync
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
            "msg": f"챕터 {len(flow_drift_chapters)}개가 구 flow 기반",
            "impacted": flow_drift_chapters,
            "resolve": '"Chapter X 수정해줘"',
        })

    # 5. final vs chapters sync
    current_chap_hashes = {chap.name: file_hash(chap) for chap in chapter_files(root)}
    built_hashes = state["final"].get("chapter_hashes_at_build", {})
    final_stale = False
    if built_hashes:
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

    # 6. commitment 상태
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

    # 7. evaluation vs flow/chapters sync
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

    for s in stales:
        s["score"] = stale_priority(s)
        s["priority"] = stale_tier(s["score"])
        s["dependency_order"] = dependency_order(s)

    stales_by_urgency = sorted(stales, key=lambda s: -s["score"])
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
    """삭제된 논문을 인용하는 챕터 파일들 탐지."""
    dangling = {}
    for chap in chapter_files(root):
        try:
            text = chap.read_text(encoding="utf-8")
        except Exception:
            continue
        hits = []
        for pname in removed_papers:
            stem = pname.rsplit(".", 1)[0]
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

def main(argv: list) -> int:
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
        if cmd == "snapshot-flow" and len(args) == 2:
            return cmd_snapshot_flow(args[0], args[1])
        if cmd == "snapshot-chapter" and len(args) == 3:
            return cmd_snapshot_chapter(args[0], args[1], args[2])
        if cmd == "snapshot-chapters" and 2 <= len(args) <= 3:
            chapter_fn = args[2] if len(args) == 3 else None
            return cmd_snapshot_chapters(args[0], args[1], chapter_fn)
        if cmd == "snapshot-work-plan" and len(args) == 2:
            return cmd_snapshot_work_plan(args[0], args[1])
        if cmd == "snapshot-evaluation" and len(args) == 2:
            return cmd_snapshot_evaluation(args[0], args[1])
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
