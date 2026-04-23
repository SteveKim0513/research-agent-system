#!/usr/bin/env python3
"""
evaluation_aggregator.py (v2) — axis reports → evaluation.md + work-plan.md live task board.

책임:
1. axis1~6-*.md 점수 파싱 → evaluations/latest/evaluation.md 생성
2. work-plan.md v2 skeleton 보장 (v1 감지 시 work-plan.archive/000-legacy-v1.md로 자동 이동)
3. claim-extraction-*.md의 HUNT-PROPOSAL-X 라벨 → 다음 HUNT-NNN 번호 발급 + back-reference
4. work-plan.md 대시보드 재계산 (WORK-PLAN-FORMAT.md §5 스펙)
5. 기존 task 카드 (Active / In-progress / Blocked / Completed / Deferred)는 그대로 보존

Usage:
    python3 scripts/evaluation_aggregator.py <project_name>
"""
import json
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime


AXIS_FILES = {
    "axis1": ("axis1-reference.md", "레퍼런스 충실도"),
    "axis2": ("axis2-logic.md", "논리 전개 완성도"),
    "axis3": ("axis3-defense.md", "반박·강화 논리"),
    "axis4": ("axis4-originality.md", "독창성·기여도"),
    "axis5": ("axis5-concept.md", "구성개념 정의 정밀도"),
    "axis6": ("axis6-critical.md", "비판적 시각"),
}

TASK_TYPES = ["HUNT", "REANALYZE", "DRAFT", "EDIT", "FIX"]

# 섹션 헤더 → 내부 키 매핑
SECTION_HEADERS = {
    "## 📊 대시보드": "dashboard",
    "## 🟡 Active": "active",
    "## 🔵 In-progress": "in_progress",
    "## 🔴 Blocked": "blocked",
    "## ⚪ Deferred": "deferred",
    "## 📜 Older completed": "completed_older",
}
# Recent completed는 "(최근 N개)" suffix가 붙음 → prefix 매칭
RECENT_COMPLETED_PREFIX = "## 🟢 Recent completed"

SECTION_ORDER = [
    "dashboard",
    "active",
    "in_progress",
    "blocked",
    "completed_recent",
    "deferred",
    "completed_older",
]

CARD_HEADER_RE = re.compile(
    r"^### \[(HUNT|REANALYZE|DRAFT|EDIT|FIX)-(\d+)\](.*?)$",
    re.MULTILINE,
)


# ──────────────────────────────────────────────────────────
# Path helpers
# ──────────────────────────────────────────────────────────

def project_root(project: str) -> Path:
    return Path("projects") / project


def latest_dir(project: str) -> Path:
    return project_root(project) / "evaluations" / "latest"


def flow_md_path(project: str) -> Path:
    return project_root(project) / "flow" / "flow.md"


def work_plan_path(project: str) -> Path:
    return project_root(project) / "work-plan.md"


def claim_extraction_paths(project: str) -> list:
    """존재하는 claim-extraction 파일만 반환."""
    root = project_root(project)
    paths = []
    p1 = root / "flow" / "claim-extraction-flow.md"
    p2 = root / "chapters" / "claim-extraction-draft.md"
    if p1.exists():
        paths.append(p1)
    if p2.exists():
        paths.append(p2)
    return paths


def read_metadata(project: str) -> dict:
    p = project_root(project) / ".paper-metadata.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def detect_stage(project: str) -> str:
    """chapters/에 실제 챕터 파일이 있으면 draft, 없으면 flow."""
    root = project_root(project)
    chap_dir = root / "chapters"
    if not chap_dir.exists():
        return "flow"
    real_chaps = [p for p in chap_dir.glob("*.md")
                  if p.is_file() and p.name != "claim-extraction-draft.md"]
    return "v1-draft" if real_chaps else "flow"


# ──────────────────────────────────────────────────────────
# Axis score parsing
# ──────────────────────────────────────────────────────────

def extract_score(md_path: Path):
    if not md_path.exists():
        return None
    content = md_path.read_text(encoding="utf-8")

    score_m = re.search(r"\*\*점수\*\*\s*:\s*(\d+)\s*/\s*100", content)
    prev_m = re.search(r"\*\*이전\*\*\s*:\s*(\d+)\s*/\s*100", content)
    delta_m = re.search(r"\(([+\-]\s*\d+)\)", content[:500])

    sub_scores = {}
    for sub_m in re.finditer(r"##\s+([\d\-\.]+)\s*([^\(]*)\((\d+)\s*/\s*25\)", content):
        key = sub_m.group(1).strip()
        name = sub_m.group(2).strip()
        val = int(sub_m.group(3))
        sub_scores[key] = {"name": name, "score": val}

    if not score_m:
        return None
    return {
        "score": int(score_m.group(1)),
        "prev": int(prev_m.group(1)) if prev_m else None,
        "delta": delta_m.group(1).replace(" ", "") if delta_m else None,
        "sub": sub_scores,
    }


def parse_axis_scores(project: str):
    lat = latest_dir(project)
    meta = read_metadata(project)
    ambition = meta.get("intellectual_ambition", "baseline")
    critical_mode = ambition in ("critical", "paradigm-shifting")

    axis_data = {}
    missing = []
    for axis, (fname, title) in AXIS_FILES.items():
        if axis == "axis6" and not critical_mode:
            continue
        data = extract_score(lat / fname)
        if data is None:
            missing.append(axis)
            continue
        axis_data[axis] = {"title": title, **data}
    return axis_data, missing, ambition, critical_mode


def grade_of(score: int) -> str:
    if score >= 90: return "A+"
    if score >= 85: return "A"
    if score >= 80: return "B+"
    if score >= 75: return "B"
    if score >= 70: return "C+"
    if score >= 65: return "C"
    if score >= 60: return "C-"
    if score >= 55: return "D+"
    if score >= 50: return "D"
    if score >= 40: return "F+"
    return "F"


def emoji_of(score: int) -> str:
    if score >= 85: return "🟢"
    if score >= 70: return "🟡"
    return "🔴"


# ──────────────────────────────────────────────────────────
# evaluation.md 생성
# ──────────────────────────────────────────────────────────

def write_evaluation_md(project: str, axis_data: dict, missing: list, ambition: str, critical_mode: bool):
    lat = latest_dir(project)
    lat.mkdir(parents=True, exist_ok=True)

    total = sum(d["score"] for d in axis_data.values())
    n_axes = len(axis_data)
    max_total = n_axes * 100
    avg = total / n_axes if n_axes else 0

    prev_total = None
    if axis_data and all(d.get("prev") is not None for d in axis_data.values()):
        prev_total = sum(d["prev"] for d in axis_data.values())

    if avg >= 85:
        judgment = "🟢 **Accept** (minor revisions)"
    elif avg >= 70:
        judgment = "🟡 **Revise & Resubmit**"
    elif avg >= 55:
        judgment = "🟠 **Major Revision**"
    else:
        judgment = "🔴 **Reject** (structural problems)"

    out = [
        f"# {n_axes}축 평가 리포트 — {project}",
        "",
        f"**대상**: `projects/{project}/flow/flow.md`",
        f"**평가일**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**평가자 기준**: Top-tier 저널 + Oxford/Cambridge critical tradition",
        f"**intellectual_ambition**: **{ambition}**" + (" 🎭" if critical_mode else ""),
        "",
        "**파이프라인**: 병렬 축별 워커 (evaluation-orchestrator) → aggregator",
        "",
        "---",
        "",
        "## 📊 종합 점수",
        "",
        f"### {n_axes}축 체계: **{total}/{max_total}** (평균 {avg:.1f}/100)",
        "",
        "| 축 | 이름 | 점수 | 이전 | Δ | 등급 |",
        "|---|------|------|------|---|------|",
    ]
    for axis, d in axis_data.items():
        n = axis[-1]
        prev = f"{d['prev']}" if d.get("prev") is not None else "—"
        delta = d.get("delta") or "—"
        out.append(
            f"| {n} | {d['title']} | **{d['score']}** {emoji_of(d['score'])} | {prev} | {delta} | {grade_of(d['score'])} |"
        )
    out.append("")

    if prev_total is not None:
        out.append(f"**이전 총점**: {prev_total}/{max_total} → **변화 {total - prev_total:+d}**")
        out.append("")

    out.extend([
        f"**심사 판정**: {judgment}",
        "",
        "---",
        "",
        "## 📂 축별 상세 리포트",
        "",
    ])
    for axis, (fname, _) in AXIS_FILES.items():
        if axis not in axis_data:
            continue
        out.append(f"- [{axis_data[axis]['title']}]({fname})")

    out.extend([
        "",
        "---",
        "",
        "## 🎯 잔여 우선순위",
        "",
    ])
    sorted_axes = sorted(axis_data.items(), key=lambda x: x[1]["score"])
    for axis, d in sorted_axes[:3]:
        out.append(f"- **축 {axis[-1]} ({d['title']})** — {d['score']}/100. 상세: `{AXIS_FILES[axis][0]}`")

    if missing:
        out.extend([
            "",
            "---",
            "",
            f"⚠️ **누락된 축**: {', '.join(missing)} — 해당 scorer를 다시 실행하거나 work-plan을 확인하세요.",
        ])

    out.extend([
        "",
        "---",
        "",
        f"*생성: evaluation_aggregator.py at {datetime.now().isoformat()}*",
    ])

    (lat / "evaluation.md").write_text("\n".join(out), encoding="utf-8")
    return total, prev_total


# ──────────────────────────────────────────────────────────
# work-plan.md — skeleton, section parsing, dashboard render
# ──────────────────────────────────────────────────────────

def is_v2_format(text: str) -> bool:
    required = ["## 📊 대시보드", "## 🟡 Active", "## 🔵 In-progress", "## 🟢 Recent completed"]
    return all(h in text for h in required)


def archive_legacy(project: str, legacy_text: str) -> Path:
    """기존 v1 work-plan.md를 work-plan.archive/000-legacy-v1.md로 이동."""
    archive_dir = project_root(project) / "work-plan.archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / f"000-{datetime.now().strftime('%Y-%m-%d')}-legacy-v1.md"
    dest.write_text(legacy_text, encoding="utf-8")
    return dest


SKELETON_TEMPLATE = """# work-plan.md

> 📅 마지막 갱신: {timestamp} ({trigger})
> Stage: {stage}
> intellectual_ambition: {ambition}

---

## 📊 대시보드

{dashboard}

---

## 🟡 Active

_(없음)_

---

## 🔵 In-progress

_(없음)_

---

## 🔴 Blocked

_(없음)_

---

## 🟢 Recent completed (최근 15개)

_(없음)_

---

## ⚪ Deferred

_(없음)_

---

## 📜 Older completed

_(없음)_
"""


def make_skeleton(stage: str, ambition: str, dashboard_block: str, trigger: str = "initial") -> str:
    return SKELETON_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        trigger=trigger,
        stage=stage,
        ambition=ambition,
        dashboard=dashboard_block.strip(),
    )


def split_sections(text: str) -> dict:
    """v2 work-plan을 섹션별로 split. 반환: dict section_name -> body (trimmed)."""
    sections = {name: "" for name in SECTION_ORDER}

    lines = text.split("\n")
    current = None
    buffers = {name: [] for name in SECTION_ORDER}

    for line in lines:
        stripped = line.rstrip()
        matched_key = None
        if stripped in SECTION_HEADERS:
            matched_key = SECTION_HEADERS[stripped]
        elif stripped.startswith(RECENT_COMPLETED_PREFIX):
            matched_key = "completed_recent"

        if matched_key:
            current = matched_key
            continue

        if current and stripped == "---":
            current = None
            continue

        if current:
            buffers[current].append(line)

    for name in SECTION_ORDER:
        sections[name] = "\n".join(buffers[name]).strip()
    return sections


def extract_header_block(text: str) -> str:
    """파일 상단의 제목 + metadata 블록만 추출 (첫 '---' 전까지)."""
    parts = text.split("\n---\n", 1)
    return parts[0]


def find_max_id(text: str, task_type: str) -> int:
    pattern = re.compile(rf"\[{task_type}-(\d+)\]")
    nums = [int(m.group(1)) for m in pattern.finditer(text)]
    return max(nums) if nums else 0


def count_cards(section_text: str) -> int:
    return len(CARD_HEADER_RE.findall(section_text))


def iter_cards(section_text: str):
    """섹션 내 task 카드를 순회. 각 카드는 {type, num, header_line, body}."""
    lines = section_text.split("\n")
    cur = None
    for line in lines:
        m = CARD_HEADER_RE.match(line.rstrip())
        if m:
            if cur is not None:
                yield cur
            cur = {
                "type": m.group(1),
                "num": int(m.group(2)),
                "suffix": m.group(3).strip(),
                "header": line.rstrip(),
                "body_lines": [],
            }
        elif cur is not None:
            cur["body_lines"].append(line)
    if cur is not None:
        yield cur


# ──────────────────────────────────────────────────────────
# HUNT-PROPOSAL processing
# ──────────────────────────────────────────────────────────

PROPOSAL_LABEL_RE = re.compile(r"HUNT-PROPOSAL-([A-Z0-9]+)")


def process_hunt_proposals(project: str, work_plan_text: str):
    """claim-extraction-*.md의 HUNT-PROPOSAL-X → HUNT-NNN 번호 발급.

    Returns: (new_hunt_cards: list[str], updated_ce_texts: dict[Path, str])
    """
    ce_paths = claim_extraction_paths(project)
    if not ce_paths:
        return [], {}

    # 파일별로 발견된 proposal 라벨 수집 (순서 보존, 중복 제거)
    all_proposals_ordered = []
    per_file_proposals = {}
    for p in ce_paths:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        labels = PROPOSAL_LABEL_RE.findall(text)
        dedup = list(dict.fromkeys(labels))
        per_file_proposals[p] = dedup
        for lb in dedup:
            if lb not in all_proposals_ordered:
                all_proposals_ordered.append(lb)

    if not all_proposals_ordered:
        return [], {}

    # ID 발급
    next_id = find_max_id(work_plan_text, "HUNT") + 1
    replacement_map = {}
    new_cards = []
    for proposal_letter in all_proposals_ordered:
        new_id_str = f"HUNT-{next_id:03d}"
        replacement_map[f"HUNT-PROPOSAL-{proposal_letter}"] = new_id_str
        # Proposal 카드 minimal: 자세한 필드는 claim-extraction에 있으므로 referenced
        ce_files_with_this = [p.name for p, labels in per_file_proposals.items() if proposal_letter in labels]
        source = ce_files_with_this[0] if ce_files_with_this else "unknown"
        new_cards.append(build_hunt_card_skeleton(new_id_str, proposal_letter, source))
        next_id += 1

    # claim-extraction 파일에 back-reference 치환
    updated_ce_texts = {}
    for p in ce_paths:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        changed = text
        for old, new in replacement_map.items():
            changed = changed.replace(f"[{old}]", f"[{new}]")
            changed = changed.replace(old, new)
        if changed != text:
            updated_ce_texts[p] = changed

    return new_cards, updated_ce_texts


def build_hunt_card_skeleton(hunt_id: str, proposal_letter: str, source: str) -> str:
    """PROPOSAL → 확정 HUNT 카드. 세부 필드는 claim-extraction 원문 참조."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""### [{hunt_id}] 🟡 active · P2 · axis1 · Stage 1

**무엇**: claim-extraction의 HUNT-PROPOSAL-{proposal_letter}에서 승격 — 세부는 `{source}` 참조

**담당 명령**: `"작업 시작해줘"` → Consensus 자동 검색

**예상 회복**: 축 1-1 +3 (대략)

**검색 키워드**: `{source}`의 HUNT-PROPOSAL-{proposal_letter} 블록 참조
**기대 논문 프로필**: `{source}`의 HUNT-PROPOSAL-{proposal_letter} 블록 참조

**의존성**: 없음
**차단하는 것**: 없음

**진행 로그**:
- {now} · created by evaluation_aggregator (HUNT-PROPOSAL-{proposal_letter} → {hunt_id})
"""


# ──────────────────────────────────────────────────────────
# Dashboard render
# ──────────────────────────────────────────────────────────

STAGE_RE = re.compile(r"Stage\s+(\d+)")
AXIS_TAG_RE = re.compile(r"axis(\d+)")
RECOVERY_RE = re.compile(r"\*\*예상 회복\*\*\s*:\s*축\s*(\d+)(?:-(\d+))?\s*\+(\d+)")


def collect_task_stats(sections: dict) -> dict:
    """섹션별 task 수, stage별 진척도, axis별 잔여 회복 집계."""
    state_counts = {"active": 0, "in_progress": 0, "blocked": 0, "completed": 0, "deferred": 0}
    stage_counts = {1: [0, 0], 2: [0, 0], 3: [0, 0], 4: [0, 0]}  # [done, total]
    axis_recovery = {f"axis{i}": [0, 0] for i in range(1, 7)}  # [+N 합, task 수]

    # 상태 카운트
    state_counts["active"] = count_cards(sections["active"])
    state_counts["in_progress"] = count_cards(sections["in_progress"])
    state_counts["blocked"] = count_cards(sections["blocked"])
    state_counts["deferred"] = count_cards(sections["deferred"])
    state_counts["completed"] = count_cards(sections["completed_recent"]) + count_cards(sections["completed_older"])

    # Stage 진척도 — 모든 카드 스캔
    def process_cards(section_key, is_done: bool):
        for card in iter_cards(sections[section_key]):
            header_line = card["header"] + " " + card["suffix"]
            body = "\n".join(card["body_lines"])

            stage_m = STAGE_RE.search(header_line)
            stage = int(stage_m.group(1)) if stage_m else None
            if stage and stage in stage_counts:
                stage_counts[stage][1] += 1
                if is_done:
                    stage_counts[stage][0] += 1

            # 잔여 회복은 아직 미완료(active/in_progress/blocked) 카드만
            if not is_done:
                axis_m = AXIS_TAG_RE.search(header_line)
                axis_key = f"axis{axis_m.group(1)}" if axis_m else None
                rec_m = RECOVERY_RE.search(body)
                if axis_key and axis_key in axis_recovery and rec_m:
                    axis_recovery[axis_key][0] += int(rec_m.group(3))
                    axis_recovery[axis_key][1] += 1

    for key in ("active", "in_progress", "blocked"):
        process_cards(key, is_done=False)
    for key in ("completed_recent", "completed_older"):
        process_cards(key, is_done=True)

    return {
        "state_counts": state_counts,
        "stage_counts": stage_counts,
        "axis_recovery": axis_recovery,
    }


def bar_10(pct: float) -> str:
    """0~100 → 10칸 bar."""
    filled = max(0, min(10, round(pct / 10)))
    return "█" * filled + "░" * (10 - filled)


def recommend_commands(sections: dict, stats: dict) -> list:
    """다음 권장 명령 최대 3개."""
    recs = []

    def tasks_of_type(section_key, task_type):
        ids = []
        for card in iter_cards(sections[section_key]):
            if card["type"] == task_type:
                ids.append(f"{task_type}-{card['num']:03d}")
        return ids

    hunt_active = tasks_of_type("active", "HUNT")
    if hunt_active:
        preview = ", ".join(hunt_active[:3])
        if len(hunt_active) > 3:
            preview += f" 외 {len(hunt_active) - 3}"
        recs.append(f'`"작업 시작해줘"` — HUNT {len(hunt_active)}건 대기 ({preview})')

    reanalyze_active = tasks_of_type("active", "REANALYZE")
    if reanalyze_active:
        recs.append(f'`"논문 재분석해줘"` — REANALYZE {len(reanalyze_active)}건 대기')

    draft_active = tasks_of_type("active", "DRAFT")
    if draft_active:
        recs.append(f'`"초안 작성해줘"` — DRAFT {len(draft_active)}건 반영 대기')

    edit_active = tasks_of_type("active", "EDIT")
    if edit_active and len(recs) < 3:
        preview = ", ".join(edit_active[:3])
        recs.append(f'`"Chapter X 수정해줘"` — EDIT {len(edit_active)}건 ({preview})')

    fix_active = tasks_of_type("active", "FIX")
    if fix_active and len(recs) < 3:
        recs.append(f'`"flow 업데이트해줘"` — FIX {len(fix_active)}건 승인 대기')

    if not recs:
        if stats["state_counts"]["blocked"] > 0:
            recs.append(f'`"상태 확인해줘"` — 🔴 Blocked {stats["state_counts"]["blocked"]}건 의존성 검토 필요')
        else:
            recs.append('_(권장 명령 없음 — 🟡 Active 비어있음. `"평가해줘"`로 새 task 발급 가능)_')

    return recs[:3]


def render_dashboard(stats: dict, recs: list) -> str:
    state = stats["state_counts"]
    stage = stats["stage_counts"]
    axis = stats["axis_recovery"]

    def stage_line(n: int, name: str) -> str:
        done, total = stage[n]
        pct = (done / total * 100) if total else 0
        return f"- Stage {n} {name}: {bar_10(pct)} {pct:.0f}% ({done}/{total})"

    lines = [
        "### Stage 진척도",
        stage_line(1, "리서치"),
        stage_line(2, "초안  "),
        stage_line(3, "수정  "),
        stage_line(4, "최종  "),
        "",
        "### 상태별 카운트",
        f"🟡 active: {state['active']}  |  🔵 in-progress: {state['in_progress']}  |  🔴 blocked: {state['blocked']}  |  🟢 completed: {state['completed']}  |  ⚪ deferred: {state['deferred']}",
        "",
        "### 축별 잔여 회복 잠재력 (예상)",
    ]
    for i in range(1, 7):
        key = f"axis{i}"
        amount, count = axis[key]
        if count == 0:
            lines.append(f"- 축 {i}: — (관련 task 없음)")
        else:
            lines.append(f"- 축 {i}: +{amount}  ({count} task{'s' if count != 1 else ''})")
    lines.append("")
    lines.append("### 🎯 다음 권장 명령")
    for i, r in enumerate(recs, 1):
        lines.append(f"{i}. {r}")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────
# Work-plan 업데이트
# ──────────────────────────────────────────────────────────

def update_header_block(header_block: str, stage: str, ambition: str, trigger: str) -> str:
    """파일 상단 meta 3줄을 현재 값으로 업데이트."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = header_block.split("\n")
    updated = []
    replaced = {"timestamp": False, "stage": False, "ambition": False}

    for line in lines:
        if line.startswith("> 📅 마지막 갱신:"):
            updated.append(f"> 📅 마지막 갱신: {now} ({trigger})")
            replaced["timestamp"] = True
        elif line.startswith("> Stage:"):
            updated.append(f"> Stage: {stage}")
            replaced["stage"] = True
        elif line.startswith("> intellectual_ambition:"):
            updated.append(f"> intellectual_ambition: {ambition}")
            replaced["ambition"] = True
        else:
            updated.append(line)

    # 누락된 meta 라인 추가 (파일 상단에 `# work-plan.md` 다음)
    if not all(replaced.values()):
        added = []
        for line in updated:
            added.append(line)
            if line.strip() == "# work-plan.md":
                if not replaced["timestamp"]:
                    added.append("")
                    added.append(f"> 📅 마지막 갱신: {now} ({trigger})")
                if not replaced["stage"]:
                    added.append(f"> Stage: {stage}")
                if not replaced["ambition"]:
                    added.append(f"> intellectual_ambition: {ambition}")
        updated = added

    return "\n".join(updated)


def rebuild_work_plan(
    existing: str,
    dashboard: str,
    new_active_cards: list,
    stage: str,
    ambition: str,
    trigger: str,
) -> str:
    """기존 work-plan의 섹션을 보존하며 대시보드 치환 + active에 새 카드 추가."""
    sections = split_sections(existing)
    header_block = extract_header_block(existing)
    header_block = update_header_block(header_block, stage, ambition, trigger)

    # 새 HUNT 카드를 Active 섹션 하단에 추가
    active_body = sections["active"]
    if active_body.strip() == "_(없음)_":
        active_body = ""
    for card in new_active_cards:
        if active_body and not active_body.endswith("\n"):
            active_body += "\n"
        if active_body:
            active_body += "\n"
        active_body += card.rstrip() + "\n"
    active_body = active_body.strip() or "_(없음)_"

    # Recent completed 최신순 유지 + 15개 overflow
    recent_body, older_body = rebalance_completed(sections["completed_recent"], sections["completed_older"])

    # 재조립
    def section_block(header: str, body: str) -> str:
        body = body.strip() or "_(없음)_"
        return f"{header}\n\n{body}"

    recent_header_count = count_cards(recent_body) if recent_body != "_(없음)_" else 0
    recent_header = f"## 🟢 Recent completed (최근 15개, 현재 {recent_header_count})"

    parts = [
        header_block,
        "---",
        "## 📊 대시보드\n\n" + dashboard.strip(),
        "---",
        section_block("## 🟡 Active", active_body),
        "---",
        section_block("## 🔵 In-progress", sections["in_progress"]),
        "---",
        section_block("## 🔴 Blocked", sections["blocked"]),
        "---",
        section_block(recent_header, recent_body),
        "---",
        section_block("## ⚪ Deferred", sections["deferred"]),
        "---",
        section_block("## 📜 Older completed", older_body),
    ]
    return "\n\n".join(parts).rstrip() + "\n"


def rebalance_completed(recent: str, older: str):
    """Recent completed 16번째부터는 Older로 밀어냄. 최신순 유지는 호출자 책임."""
    recent_cards = list(iter_cards(recent))
    if len(recent_cards) <= 15:
        return recent, older

    overflow = recent_cards[15:]
    keep = recent_cards[:15]

    def rebuild(cards):
        if not cards:
            return ""
        blocks = []
        for c in cards:
            block = c["header"] + "\n" + "\n".join(c["body_lines"]).rstrip()
            blocks.append(block.rstrip())
        return "\n\n".join(blocks)

    # older에 overflow 카드 prepend (최신 밀려난 것이 위로)
    overflow_block = rebuild(overflow)
    older_new = (overflow_block + "\n\n" + older).strip() if older and older != "_(없음)_" else overflow_block
    return rebuild(keep) or "_(없음)_", older_new or "_(없음)_"


# ──────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────

def aggregate(project: str) -> int:
    lat = latest_dir(project)
    if not lat.exists():
        print(f"⚠️  {lat} 없음 — axis scorer 결과 없음", file=sys.stderr)
        return 1

    # 1. axis 점수 파싱 + evaluation.md 생성
    axis_data, missing, ambition, critical_mode = parse_axis_scores(project)
    total, prev_total = write_evaluation_md(project, axis_data, missing, ambition, critical_mode)

    n_axes = len(axis_data)
    max_total = n_axes * 100
    print(f"✅ evaluation.md 생성 ({n_axes}축, 총점 {total}/{max_total})")
    if prev_total is not None:
        print(f"   Delta: {total - prev_total:+d}")
    if missing:
        print(f"⚠️  누락 축: {missing}")

    # 2. work-plan.md 준비
    wp_path = work_plan_path(project)
    existing = wp_path.read_text(encoding="utf-8") if wp_path.exists() else ""
    stage = detect_stage(project)

    if existing and not is_v2_format(existing):
        archived = archive_legacy(project, existing)
        print(f"ℹ️  기존 v1 work-plan을 {archived.relative_to(project_root(project))}로 이동")
        existing = ""

    if not existing:
        # 최소 skeleton (대시보드는 placeholder)
        existing = make_skeleton(stage, ambition, "_(대시보드는 아래에서 재계산)_", trigger="initial")

    # 3. HUNT-PROPOSAL 처리 (번호 발급 + claim-extraction back-ref)
    new_cards, updated_ce_texts = process_hunt_proposals(project, existing)
    if new_cards:
        print(f"🆕 HUNT 신규 발급: {len(new_cards)}건")
        for p, text in updated_ce_texts.items():
            p.write_text(text, encoding="utf-8")
            print(f"   {p.relative_to(project_root(project))} 업데이트")

    # 4. 대시보드 재계산 (새 카드 반영 후)
    # rebuild_work_plan은 대시보드를 미리 계산해서 받는 구조이므로, 두 단계로:
    #  (1) new_cards만 먼저 반영한 tmp 버전 생성 → stats 계산
    #  (2) 그 stats로 dashboard 생성 → 최종 rebuild
    tmp = rebuild_work_plan(existing, "_(계산 중)_", new_cards, stage, ambition, "eval")
    sections = split_sections(tmp)
    stats = collect_task_stats(sections)
    recs = recommend_commands(sections, stats)
    dashboard = render_dashboard(stats, recs)

    final = rebuild_work_plan(existing, dashboard, new_cards, stage, ambition, "eval")
    wp_path.write_text(final, encoding="utf-8")
    print(f"✅ work-plan.md 갱신 (active={stats['state_counts']['active']}, "
          f"in_progress={stats['state_counts']['in_progress']}, "
          f"completed={stats['state_counts']['completed']})")

    return 0


def main(argv: list) -> int:
    if len(argv) < 2:
        print("Usage: python3 evaluation_aggregator.py <project_name>")
        return 1
    try:
        return aggregate(argv[1])
    except Exception as e:
        import traceback
        print(f"❌ aggregator 오류: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
