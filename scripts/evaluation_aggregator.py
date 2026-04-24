#!/usr/bin/env python3
"""
evaluation_aggregator.py (v2) — axis reports → evaluation.md + work-plan.md live task board.

책임:
1. axis1~6-*.md 점수 파싱 → evaluations/latest/evaluation.md 생성
2. work-plan.md v2 skeleton 보장 (v1 감지 시 work-plan.archive/000-legacy-v1.md로 자동 이동)
3. claim-extraction-*.md의 JSON 요약 `hunts[]` 배열 → work-plan.md HUNT-NNN 카드 1:1 발급 (covers 필드 포함) + claim-extraction back-reference
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

sys.path.insert(0, str(Path(__file__).parent))
import hunt_registry


AXIS_FILES = {
    "axis1": ("axis1-reference.md", "레퍼런스 충실도"),
    "axis2": ("axis2-logic.md", "논리 전개 완성도"),
    "axis3": ("axis3-defense.md", "반박·강화 논리"),
    "axis4": ("axis4-originality.md", "독창성·기여도"),
    "axis5": ("axis5-concept.md", "구성개념 정의 정밀도"),
    "axis6": ("axis6-critical.md", "비판적 시각"),
}

TASK_TYPES = ["HUNT", "REANALYZE", "DRAFT", "EDIT", "FIX"]

BRIEFING_HEADER = "## 🧭 현재 당신이 해야 할 일"

# 섹션 헤더 → 내부 키 매핑
SECTION_HEADERS = {
    BRIEFING_HEADER: "briefing",
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
    "briefing",
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
# Category system (메인 시그널) — 점수 기반 grade/emoji 폐기
# ──────────────────────────────────────────────────────────

# 카테고리 emoji → 정규화 라벨. 누락 시 None.
CATEGORY_BY_EMOJI = {
    "🟢": ("strong", "충실"),
    "🟡": ("adequate", "적정"),
    "🟠": ("needs_work", "보강 필요"),
    "🔴": ("critical_gap", "구조적 결함"),
    "⚫": ("cannot_assess", "측정 불가"),
}
EMOJI_BY_KEY = {v[0]: k for k, v in CATEGORY_BY_EMOJI.items()}
LABEL_BY_KEY = {v[0]: v[1] for v in CATEGORY_BY_EMOJI.values()}

# worst → best 순서. render_briefing 에서 worst-axis 정렬용.
CATEGORY_PRIORITY = ["critical_gap", "cannot_assess", "needs_work", "adequate", "strong"]


def category_emoji(key: str) -> str:
    return EMOJI_BY_KEY.get(key, "❔")


def category_label(key: str) -> str:
    return LABEL_BY_KEY.get(key, key)


def parse_category_from_line(line: str):
    """`**상태**: 🔴 구조적 결함` 같은 라인에서 카테고리 키 추출."""
    for emoji, (key, _) in CATEGORY_BY_EMOJI.items():
        if emoji in line:
            return key
    return None


# ──────────────────────────────────────────────────────────
# Axis report parsing (카테고리 + 진단 + Critical Issues + 보조 점수)
# ──────────────────────────────────────────────────────────

def extract_axis(md_path: Path):
    """axis 파일에서 카테고리(메인) + 진단 + critical issues + 보조 점수 파싱."""
    if not md_path.exists():
        return None
    content = md_path.read_text(encoding="utf-8")

    # 1. 축 전체 상태 (상단 헤더 — `**상태**:` 라인 첫 번째)
    status_m = re.search(r"\*\*상태\*\*\s*:\s*([^\n]+)", content)
    overall_status = parse_category_from_line(status_m.group(1)) if status_m else None

    # 2. 핵심 진단 (`**핵심 진단**:` 다음 한 단락)
    diag_m = re.search(r"\*\*핵심 진단\*\*\s*:\s*([^\n]+(?:\n(?!\*\*|##|---)[^\n]+)*)", content)
    diagnosis = diag_m.group(1).strip() if diag_m else ""

    # 3. Critical Issues (numbered list)
    crit_m = re.search(r"\*\*Critical Issues\*\*\s*:\s*\n((?:\d+\.\s+[^\n]+\n?)+)", content)
    critical_issues = []
    if crit_m:
        for line in crit_m.group(1).strip().split("\n"):
            m = re.match(r"\d+\.\s+(.+)", line.strip())
            if m:
                critical_issues.append(m.group(1).strip())

    # 4. Sub-criteria 카테고리 (각 `## N-N <name>` 블록 내 `**상태**:` 첫 번째)
    sub_status = {}
    for sub_m in re.finditer(
        r"##\s+([A-Z]?[\d\-\.]+)\s+([^\n]+?)\n+\*\*상태\*\*\s*:\s*([^\n]+)",
        content,
    ):
        key = sub_m.group(1).strip()
        name = sub_m.group(2).strip()
        cat = parse_category_from_line(sub_m.group(3))
        sub_status[key] = {"name": name, "category": cat}

    # 5. 보조 점수 (있으면 — <details> 안에 있을 수 있음)
    score_m = re.search(r"\*\*점수\*\*\s*:\s*(\d+)\s*/\s*100", content)
    prev_m = re.search(r"\*\*이전\*\*\s*:\s*(\d+)\s*/\s*100", content)
    delta_m = re.search(r"\(\s*([+\-]\d+)\s*\)", content[:1500])

    sub_scores = {}
    for sub_m in re.finditer(r"\|\s*([A-Z]?[\d\-\.]+)\s+[^\|]*\|\s*(\d+)\s*/\s*25", content):
        key = sub_m.group(1).strip()
        sub_scores[key] = int(sub_m.group(2))

    return {
        "category": overall_status,
        "diagnosis": diagnosis,
        "critical_issues": critical_issues,
        "sub_status": sub_status,
        # 보조 (trend tracking — 메인 판정에 사용 금지)
        "score": int(score_m.group(1)) if score_m else None,
        "prev": int(prev_m.group(1)) if prev_m else None,
        "delta": delta_m.group(1) if delta_m else None,
        "sub_scores": sub_scores,
    }


def parse_axis_scores(project: str):
    """이름은 legacy지만 카테고리·진단·점수 모두 반환."""
    lat = latest_dir(project)
    meta = read_metadata(project)
    ambition = meta.get("intellectual_ambition", "incremental")
    critical_mode = ambition in ("critical", "paradigm-shifting")

    axis_data = {}
    missing = []
    for axis, (fname, title) in AXIS_FILES.items():
        if axis == "axis6" and not critical_mode:
            continue
        data = extract_axis(lat / fname)
        if data is None:
            missing.append(axis)
            continue
        axis_data[axis] = {"title": title, **data}
    return axis_data, missing, ambition, critical_mode


# ──────────────────────────────────────────────────────────
# Verdict roll-up (점수 평균 폐기 — 카테고리 카운트 기반)
# ──────────────────────────────────────────────────────────

STRUCTURAL_AXES = ("axis1", "axis5")  # 레퍼런스 + 개념 정의 (구조적 인프라)


def verdict_from_categories(axis_data: dict) -> tuple:
    """카테고리 카운트로 verdict 산출. (verdict_emoji, verdict_label, reason) 반환."""
    cats = [d.get("category") for d in axis_data.values()]
    counts = {k: cats.count(k) for k, _ in [(v[0], None) for v in CATEGORY_BY_EMOJI.values()]}

    crit_axes = [a for a, d in axis_data.items() if d.get("category") == "critical_gap"]
    needs_axes = [a for a, d in axis_data.items() if d.get("category") == "needs_work"]
    na_axes = [a for a, d in axis_data.items() if d.get("category") == "cannot_assess"]

    structural_both_crit = all(
        axis_data.get(a, {}).get("category") == "critical_gap" for a in STRUCTURAL_AXES
        if a in axis_data
    ) and all(a in axis_data for a in STRUCTURAL_AXES)

    # Reject 조건
    if len(crit_axes) >= 2:
        return ("🔴", "Reject", f"🔴 구조적 결함 {len(crit_axes)}축")
    if structural_both_crit:
        return ("🔴", "Reject", "axis1+axis5 (구조적 축) 둘 다 🔴")
    if len(na_axes) >= 3:
        return ("🔴", "Reject", f"⚫ 측정 불가 {len(na_axes)}축 (측정 불완전)")

    # Major Revision 조건
    if len(crit_axes) >= 1:
        return ("🟠", "Major Revision", f"🔴 구조적 결함 1축 ({crit_axes[0]})")
    if len(needs_axes) >= 3:
        return ("🟠", "Major Revision", f"🟠 보강 필요 {len(needs_axes)}축")

    # R&R 조건
    if len(needs_axes) >= 2:
        return ("🟡", "Revise & Resubmit", f"🟠 보강 필요 {len(needs_axes)}축")
    if len(na_axes) >= 1:
        return ("🟡", "Revise & Resubmit", f"⚫ 측정 불가 {len(na_axes)}축")

    # 카테고리 부재 (None) 축이 있으면 Accept 불가 → 보수적 처리
    none_axes = [a for a, d in axis_data.items() if d.get("category") is None]
    if none_axes:
        return ("🟡", "Revise & Resubmit",
                f"카테고리 미부여 {len(none_axes)}축 — 재채점 필요 (구 포맷 또는 파싱 실패)")

    # Accept 조건 (모든 축 ≥ 🟡, 🔴/⚫ 0)
    if cats and all(c in ("strong", "adequate") for c in cats):
        return ("🟢", "Accept", "all axes ≥ 🟡 Adequate")

    return ("🟡", "Revise & Resubmit", "예상 외 카테고리 조합 — 재검토 필요")


# ──────────────────────────────────────────────────────────
# Sanity check (입력-출력 일관성 검증)
# ──────────────────────────────────────────────────────────

def validate_axis_consistency(project: str, axis_data: dict) -> list:
    """axis 보고와 실제 입력 데이터의 일관성 검증. 위반 list 반환."""
    issues = []

    # 1. axis1 vs claim-extraction MATCHED 수
    ce_paths = claim_extraction_paths(project)
    matched_count = None
    for p in ce_paths:
        text = p.read_text(encoding="utf-8")
        # JSON 요약의 "matched": N 또는 표 합계 행
        m = re.search(r'"matched"\s*:\s*(\d+)', text)
        if m:
            matched_count = int(m.group(1))
            break
        m = re.search(r"\|\s*\*\*합계\*\*\s*\|\s*\d+\s*\|\s*\*\*(\d+)\*\*", text)
        if m:
            matched_count = int(m.group(1))
            break

    if matched_count == 0 and "axis1" in axis_data:
        cat = axis_data["axis1"].get("category")
        if cat in ("strong", "adequate"):
            issues.append(
                f"❌ axis1 일관성 위반: MATCHED=0인데 axis1 상태가 {category_emoji(cat)} {category_label(cat)}. "
                f"0-state 규칙 위반 (잠정 만점 금지). axis1 재채점 필요."
            )

    # 2. 카테고리 vs 보조 점수 일관성
    for axis, d in axis_data.items():
        cat = d.get("category")
        score = d.get("score")
        if cat is None:
            issues.append(f"⚠️ {axis}: **상태** 카테고리 파싱 실패 (출력 템플릿 확인)")
            continue
        if score is None:
            continue  # 점수 demote — 부재 허용
        if cat == "critical_gap" and score > 70:
            issues.append(f"⚠️ {axis}: 카테고리 🔴인데 보조 점수 {score} (>70) — 재채점 권장")
        if cat == "strong" and score < 60:
            issues.append(f"⚠️ {axis}: 카테고리 🟢인데 보조 점수 {score} (<60) — 재채점 권장")

    # 3. 측정 불완전 플래그
    na_count = sum(1 for d in axis_data.values() if d.get("category") == "cannot_assess")
    if na_count >= 3:
        issues.append(
            f"ℹ️ ⚫ 측정 불가 축이 {na_count}개 — 측정 불완전. HUNT 실행 후 재평가 권장."
        )

    return issues


# ──────────────────────────────────────────────────────────
# evaluation.md 생성
# ──────────────────────────────────────────────────────────

def write_evaluation_md(project: str, axis_data: dict, missing: list, ambition: str, critical_mode: bool):
    lat = latest_dir(project)
    lat.mkdir(parents=True, exist_ok=True)

    n_axes = len(axis_data)

    # 점수 (보조 — trend tracking용)
    scores = [d["score"] for d in axis_data.values() if d.get("score") is not None]
    total = sum(scores) if scores else None
    max_total = n_axes * 100
    prev_total = None
    if axis_data and all(d.get("prev") is not None for d in axis_data.values()):
        prev_total = sum(d["prev"] for d in axis_data.values())

    # Verdict (카테고리 roll-up)
    verdict_emoji, verdict_label, verdict_reason = verdict_from_categories(axis_data)

    # Sanity check
    issues = validate_axis_consistency(project, axis_data)

    out = [
        f"# 평가 진단 — {project}",
        "",
        f"**대상**: `projects/{project}/flow/flow.md`",
        f"**평가일**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**intellectual_ambition**: **{ambition}**" + (" 🎭" if critical_mode else ""),
        f"**파이프라인**: 병렬 축별 워커 (evaluation-orchestrator) → aggregator",
        "",
        "> 신뢰 가능 (메인): 카테고리·진단·Critical Issues·HUNT.  보조 (trend only): 점수.",
        "",
        "---",
        "",
        "## 🩺 종합 판정",
        "",
        f"### {verdict_emoji} **{verdict_label}**",
        "",
        f"**근거**: {verdict_reason}",
        "",
    ]

    # Sanity 위반 알림 (있으면)
    if issues:
        out.append("**⚠️ Sanity check**:")
        for iss in issues:
            out.append(f"- {iss}")
        out.append("")

    out.extend([
        "---",
        "",
        "## 📋 축별 상태",
        "",
        "| 축 | 이름 | 상태 | 이전 → 현재 | 핵심 진단 |",
        "|---|------|------|------|----------|",
    ])
    for axis, d in axis_data.items():
        n = axis[-1]
        cat = d.get("category")
        emoji = category_emoji(cat) if cat else "❔"
        label = category_label(cat) if cat else "(파싱 실패)"
        # 카테고리 변화 (이전 카테고리 vs 현재) — 현 구조에서 이전 카테고리는 archive 파싱 필요. 단순화: 점수 기반 hint.
        if d.get("prev") is not None and d.get("score") is not None:
            arrow = f"점수 {d['prev']}→{d['score']}"
        else:
            arrow = "(첫 평가)"
        diag_short = (d.get("diagnosis") or "—").split("\n")[0][:80]
        out.append(f"| {n} | {d['title']} | {emoji} {label} | {arrow} | {diag_short} |")

    out.append("")
    out.append("---")
    out.append("")
    out.append("## 🚨 Critical Issues (이번 평가에서 가장 시급)")
    out.append("")
    crit_lines = []
    for axis, d in axis_data.items():
        for ci in d.get("critical_issues", []):
            crit_lines.append(f"- **[축 {axis[-1]}]** {ci}")
    if crit_lines:
        out.extend(crit_lines)
    else:
        out.append("- _(축별 보고에서 Critical Issues 미추출)_")

    out.extend([
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

    if missing:
        out.extend([
            "",
            "---",
            "",
            f"⚠️ **누락된 축**: {', '.join(missing)} — 해당 scorer를 다시 실행하거나 work-plan을 확인하세요.",
        ])

    # 점수 추세 (보조 — <details>로 demote)
    out.extend([
        "",
        "---",
        "",
        "<details>",
        "<summary>📊 점수 추세 (보조 — 절대 판정에 사용 금지)</summary>",
        "",
    ])
    if total is not None:
        out.append(f"**총점**: {total}/{max_total} (평균 {total/n_axes:.1f}/100)")
        if prev_total is not None:
            out.append(f"**이전 총점**: {prev_total}/{max_total} (변화 {total - prev_total:+d})")
        out.append("")
    out.extend([
        "| 축 | 이름 | 점수 | 이전 | Δ |",
        "|---|------|------|------|---|",
    ])
    for axis, d in axis_data.items():
        n = axis[-1]
        sc = d.get("score")
        sc_str = f"{sc}/100" if sc is not None else "—"
        prev = f"{d['prev']}/100" if d.get("prev") is not None else "—"
        delta = d.get("delta") or "—"
        out.append(f"| {n} | {d['title']} | {sc_str} | {prev} | {delta} |")
    out.extend([
        "",
        "> ⚠️ 점수는 추세 모니터링용 보조 신호. 절대 판정·등급 산출에 사용 금지.",
        "> 메인 시그널은 위 카테고리 (🟢🟡🟠🔴⚫) + Critical Issues.",
        "",
        "</details>",
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

## 🧭 현재 당신이 해야 할 일

{briefing}

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


def make_skeleton(stage: str, ambition: str, dashboard_block: str, briefing_block: str = "_(평가 후 자동 갱신)_", trigger: str = "initial") -> str:
    return SKELETON_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        trigger=trigger,
        stage=stage,
        ambition=ambition,
        briefing=briefing_block.strip(),
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
# HUNT processing (from claim-extraction hunts[] → work-plan cards)
# ──────────────────────────────────────────────────────────

# claim-extraction의 ```json ... ``` 요약 블록 추출 (nested [] 안전)
JSON_BLOCK_RE = re.compile(r"```json\s*\n(\{.*?\n\})\s*\n```", re.DOTALL)


def extract_hunts_from_claim_extraction(ce_paths: list) -> list:
    """claim-extraction-*.md의 ```json 요약 블록에서 hunts[] 배열 파싱.

    Returns: list of {"id": "HUNT-001", "covers": [R-IDs], "query": "...", "topic": "..."} dicts.
    순서 보존 (claim-extractor 출력 순서대로).
    """
    collected = []
    seen_ids = set()
    for p in ce_paths:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in JSON_BLOCK_RE.finditer(text):
            try:
                data = json.loads(m.group(1))
            except Exception:
                continue
            hunts = data.get("hunts")
            if not hunts:
                continue
            for h in hunts:
                hid = h.get("id")
                if not hid or hid in seen_ids:
                    continue
                seen_ids.add(hid)
                collected.append({
                    "id": hid,
                    "covers": h.get("covers") or [],
                    "query": h.get("query") or "",
                    "topic": h.get("topic") or "",
                    "source_file": p.name,
                })
            break  # 첫 매치만 사용
    return collected


def process_hunts(project: str, work_plan_text: str):
    """claim-extraction의 hunts[] → work-plan.md HUNT-NNN 카드로 1:1 발급.

    Single source of truth: `.hunt-registry.json` (hunt_registry 모듈).
    중복 발급 방지 2-layer:
    1. **Primary (registry covers match)**: 정규화된 covers가 registry의 기존 HUNT와 일치 시:
       - 기존이 active/ready/in_progress/blocked → skip (이미 활성)
       - 기존이 completed → **reactivation** (status=ready로 복귀 + work-plan에 재등록)
       - 기존이 deferred → skip
    2. **Secondary (registry 부재 시 bootstrap)**: 첫 실행이거나 legacy work-plan이면
       work-plan에서 registry 역복원 후 위 로직 수행.

    Returns: (new_hunt_cards: list[str], updated_ce_texts: dict[Path, str], reactivated_ids: list[str])
    """
    ce_paths = claim_extraction_paths(project)
    if not ce_paths:
        return [], {}, []

    proposed = extract_hunts_from_claim_extraction(ce_paths)
    if not proposed:
        return [], {}, []

    root = project_root(project)
    registry = hunt_registry.load(root)

    # Bootstrap — registry가 비어있는데 work-plan에 HUNT가 있으면 역복원
    if not registry["hunts"] and work_plan_text:
        added = hunt_registry.bootstrap_from_work_plan(registry, work_plan_text)
        if added:
            print(f"   🔧 registry bootstrap: {added}건 HUNT 역복원 (.hunt-registry.json 생성)")

    replacement_map = {}      # ce 내부 ID → 발급된 work-plan ID
    new_cards = []            # 신규 work-plan 카드
    reactivated_cards = []    # reactivation으로 work-plan 재삽입될 카드
    reactivated_ids = []      # reactivation된 HUNT ID
    skipped_active = []       # 이미 활성 상태라 skip

    for h in proposed:
        existing_hid = hunt_registry.find_by_covers(registry, h.get("covers") or [])
        if existing_hid:
            status = registry["hunts"][existing_hid]["status"]
            replacement_map[h["id"]] = existing_hid
            if status == "completed":
                # Reactivation: completed → ready + work-plan에 재삽입
                hunt_registry.reactivate(registry, existing_hid, reason=f"동일 covers 재제안 (from {h['id']})")
                # registry의 metadata 우선 (topic/query는 기존 보존, source_file 업데이트)
                meta = registry["hunts"][existing_hid]
                meta["source_file"] = h.get("source_file") or meta.get("source_file", "")
                card_meta = {
                    "covers": meta["covers"],
                    "query": meta.get("query") or h.get("query", ""),
                    "topic": meta.get("topic") or h.get("topic", ""),
                    "source_file": meta.get("source_file", ""),
                }
                reactivated_cards.append(build_hunt_card(existing_hid, card_meta, note="reactivated"))
                reactivated_ids.append(existing_hid)
            else:
                # 이미 active/ready/in_progress/blocked/deferred → skip
                skipped_active.append((h["id"], existing_hid, status))
            continue

        # 신규 발급 — registry next_id 기반
        new_id_str = hunt_registry.next_id(registry)
        replacement_map[h["id"]] = new_id_str
        new_cards.append(build_hunt_card(new_id_str, h))
        hunt_registry.add_new(registry, new_id_str, {
            "covers": h.get("covers", []),
            "query": h.get("query", ""),
            "topic": h.get("topic", ""),
            "source_file": h.get("source_file", ""),
        })

    hunt_registry.save(root, registry)

    if skipped_active:
        preview = ", ".join(f"{orig}→{hid}({st})" for orig, hid, st in skipped_active[:3])
        more = f" 외 {len(skipped_active)-3}" if len(skipped_active) > 3 else ""
        print(f"   ↪︎ 이미 활성 HUNT 스킵 ({len(skipped_active)}건): {preview}{more}")
    if reactivated_ids:
        print(f"   🔄 reactivation: {len(reactivated_ids)}건 ({', '.join(reactivated_ids[:5])}{'...' if len(reactivated_ids) > 5 else ''})")
    if new_cards:
        print(f"   🆕 신규 HUNT 발급: {len(new_cards)}건")

    # claim-extraction 파일의 HUNT ID 라벨을 발급된 ID로 치환 (back-reference)
    updated_ce_texts = {}
    for p in ce_paths:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        changed = text
        for old, new in replacement_map.items():
            if old == new:
                continue
            changed = re.sub(rf"\[{old}\]", f"[{new}]", changed)
            changed = changed.replace(f'"{old}"', f'"{new}"')
        if changed != text:
            updated_ce_texts[p] = changed

    return new_cards + reactivated_cards, updated_ce_texts, reactivated_ids


def build_hunt_card(hunt_id: str, h: dict, note: str | None = None) -> str:
    """hunts[] 항목 → work-plan HUNT 카드. covers·query·topic 필드 포함.

    note="reactivated"인 경우 진행 로그에 reactivation 표시.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    covers_str = ", ".join(h["covers"]) if h["covers"] else "(없음)"
    topic = h.get("topic") or "claim-extraction 참조"
    query = h.get("query") or ""
    source = h.get("source_file", "claim-extraction-flow.md")

    if note == "reactivated":
        log_line = f"- {now} · 🔄 **reactivated** by evaluation_aggregator (동일 covers 재제안 감지, completed → ready)"
    else:
        log_line = f"- {now} · created by evaluation_aggregator (from hunts[] in {source})"

    return f"""### [{hunt_id}] 🟡 active · P2 · axis1 · Stage 1

**무엇**: {topic}

**담당 명령**: `"작업 시작해줘"` → Consensus 자동 검색

**covers**: {covers_str}

**query**: `{query}`

**검색 키워드 / 기대 논문 프로필**: `{source}`의 각 R 섹션 참조 / registry: `.hunt-registry.json`

**의존성**: 없음
**차단하는 것**: 없음

**진행 로그**:
{log_line}
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


def render_briefing(project: str, sections: dict, stats: dict, recs: list,
                     ambition: str, critical_mode: bool,
                     axis_data: dict, prev_total) -> str:
    """대시보드 위에 표시되는 '사용자 브리핑' — 지금 할 일을 한눈에."""
    root = project_root(project)

    # 1. 지금 열어볼 파일
    read_files = ["1. **`evaluations/latest/evaluation.md`** — 최근 평가 진단 (카테고리·Critical Issues·축별 상태)"]
    # 가장 시급한 축 지목 (카테고리 우선순위 기반 — worst 먼저)
    if axis_data:
        def axis_priority(item):
            cat = item[1].get("category")
            return CATEGORY_PRIORITY.index(cat) if cat in CATEGORY_PRIORITY else len(CATEGORY_PRIORITY)
        worst_axis, worst_d = min(axis_data.items(), key=axis_priority)
        worst_n = worst_axis[-1]
        worst_cat = worst_d.get("category")
        cat_str = f"{category_emoji(worst_cat)} {category_label(worst_cat)}" if worst_cat else "(카테고리 부재)"
        read_files.append(
            f"2. **`evaluations/latest/axis{worst_n}-*.md`** — 가장 시급한 축({worst_d['title']} {cat_str}) 상세"
        )
    read_files.append("3. **이 파일 (`work-plan.md`)** — 아래 🎯 다음 명령부터 따라가세요")

    # 2. 확인·수정 가능한 작업 파일
    work_files = []
    flow_md = root / "flow" / "flow.md"
    if flow_md.exists():
        work_files.append("- `flow/flow.md` — 줄글 플랜 (수정하고 `\"평가해줘\"` 재실행 가능)")
    chap_dir = root / "chapters"
    if chap_dir.exists():
        real_chaps = [p for p in chap_dir.glob("*.md") if p.name != "claim-extraction-draft.md"]
        if real_chaps:
            work_files.append(f"- `chapters/*.md` — 생성된 초안 {len(real_chaps)}개. `\"Chapter X 수정해줘: EDIT-NNN\"`")
    crit_q = root / "critical-questions.md"
    if crit_q.exists():
        crit_c = root / "critical-commitments.md"
        if not crit_c.exists() or crit_q.stat().st_mtime > crit_c.stat().st_mtime:
            work_files.append("- `critical-questions.md` — 🎭 **답변 작성 필요** → `\"답변 반영해줘\"`")
        else:
            work_files.append("- `critical-questions.md` (답변 완료) · `critical-commitments.md` (commitment 추출됨)")
    if not work_files:
        work_files.append("- `flow/flow.md` — 먼저 줄글 플랜을 작성하세요 (참고: `flow/FLOW-TEMPLATE.md`)")

    # 3. 지금 실행할 명령 (aggregator가 이미 계산한 recs 재활용)
    commands_block = []
    for i, r in enumerate(recs, 1):
        commands_block.append(f"{i}. {r}")
    if not commands_block:
        commands_block.append('1. `"평가해줘"` — 아직 평가 없음. 먼저 flow를 평가하세요')

    # 4. 중요 알림
    alerts = []
    if stats["state_counts"]["blocked"] > 0:
        alerts.append(f"🔴 **Blocked {stats['state_counts']['blocked']}건** — 의존성 해소 필요 (아래 🔴 Blocked 섹션 확인)")
    if critical_mode:
        if (root / "critical-questions.md").exists():
            crit_c = root / "critical-commitments.md"
            crit_q_path = root / "critical-questions.md"
            if not crit_c.exists():
                alerts.append("🎭 **Critical Mode 활성** — `critical-questions.md`에 답변 필요 → `\"답변 반영해줘\"`")
            elif crit_q_path.stat().st_mtime > crit_c.stat().st_mtime:
                alerts.append("🎭 **critical-questions.md 변경 감지** — `\"답변 반영해줘\"`로 commitment 재추출 필요")
        else:
            alerts.append("🎭 **Critical Mode 활성** — 첫 평가 후 `critical-questions.md` 자동 생성됨")
    if prev_total is not None and axis_data:
        scores = [d["score"] for d in axis_data.values() if d.get("score") is not None]
        if scores:
            total = sum(scores)
            delta = total - prev_total
            if delta > 0:
                alerts.append(f"📈 점수 추세: 지난 평가 대비 **+{delta}** (보조 신호)")
            elif delta < 0:
                alerts.append(f"📉 점수 추세: 지난 평가 대비 **{delta}** (보조 신호) — 카테고리 변화 우선 확인")
    if stats["state_counts"]["active"] == 0 and stats["state_counts"]["in_progress"] == 0:
        alerts.append("✨ 🟡 Active 비어있음 — `\"평가해줘\"`로 새 task 발급 또는 프로젝트 단계 이동")
    if not alerts:
        alerts.append("_(특이사항 없음)_")

    # 5. Stage 체크리스트
    sc = stats["stage_counts"]
    def stage_check(n, name):
        done, total = sc[n]
        if total == 0:
            return f"- [ ] **Stage {n} {name}** — 아직 task 없음"
        if done == total:
            return f"- [x] **Stage {n} {name}** — 완료 ({done}/{total})"
        return f"- [ ] **Stage {n} {name}** — 진행 중 ({done}/{total})"

    lines = [
        "### 📖 지금 열어볼 파일",
        *read_files,
        "",
        "### ✍️ 확인·수정 가능한 작업 파일",
        *work_files,
        "",
        "### 🎯 지금 실행할 명령 (우선순위 순)",
        *commands_block,
        "",
        "### ⚠️ 중요 알림",
        *[f"- {a}" for a in alerts],
        "",
        "### 📚 Stage 진행 체크리스트",
        stage_check(1, "리서치"),
        stage_check(2, "초안"),
        stage_check(3, "수정"),
        stage_check(4, "최종"),
    ]
    return "\n".join(lines)


def render_dashboard(stats: dict, recs: list, axis_data: dict = None) -> str:
    state = stats["state_counts"]
    stage = stats["stage_counts"]
    axis_rec = stats["axis_recovery"]
    axis_data = axis_data or {}

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
        "### 축별 현재 상태",
    ]
    axis_titles = {f"axis{i}": AXIS_FILES[f"axis{i}"][1] for i in range(1, 7)}
    for i in range(1, 7):
        key = f"axis{i}"
        title = axis_titles[key]
        d = axis_data.get(key)
        _amount, count = axis_rec.get(key, (0, 0))
        if d and d.get("category"):
            cat = d["category"]
            emoji = category_emoji(cat)
            label = category_label(cat)
            lines.append(f"- 축 {i} ({title}): {emoji} {label}  ({count} active task{'s' if count != 1 else ''})")
        elif key == "axis6":
            lines.append(f"- 축 {i} ({title}): — (Critical Mode 비활성)")
        else:
            lines.append(f"- 축 {i} ({title}): _(평가 미실행)_  ({count} active task{'s' if count != 1 else ''})")
    lines.append("")
    lines.append("> 축 상태 emoji: 🟢 충실 / 🟡 적정 / 🟠 보강 필요 / 🔴 구조적 결함 / ⚫ 측정 불가")
    lines.append("> task state emoji와 column 헤더로 구분됨 (위 상태별 카운트 vs 위 축별 현재 상태).")
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
    briefing: str,
    new_active_cards: list,
    stage: str,
    ambition: str,
    trigger: str,
    remove_hunt_ids: set = None,
) -> str:
    """기존 work-plan의 섹션을 보존하며 대시보드 치환 + active에 새 카드 추가.

    remove_hunt_ids: 주어진 HUNT ID 카드를 모든 섹션에서 제거 (completed sync / reactivation 대체).
    """
    sections = split_sections(existing)
    header_block = extract_header_block(existing)
    header_block = update_header_block(header_block, stage, ambition, trigger)

    # completed/reactivated HUNT 카드 제거
    if remove_hunt_ids:
        for key in ("active", "in_progress", "blocked", "deferred",
                    "completed_recent", "completed_older"):
            sections[key] = hunt_registry.remove_cards_from_section_text(
                sections[key], remove_hunt_ids
            )

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
        f"{BRIEFING_HEADER}\n\n" + briefing.strip(),
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

    # 1. axis 파싱 + evaluation.md 생성
    axis_data, missing, ambition, critical_mode = parse_axis_scores(project)
    total, prev_total = write_evaluation_md(project, axis_data, missing, ambition, critical_mode)

    n_axes = len(axis_data)
    verdict_emoji, verdict_label, _ = verdict_from_categories(axis_data)
    cat_counts = {k: 0 for k in CATEGORY_PRIORITY}
    for d in axis_data.values():
        c = d.get("category")
        if c in cat_counts:
            cat_counts[c] += 1
    cat_summary = " ".join(
        f"{category_emoji(k)}:{cat_counts[k]}" for k in CATEGORY_PRIORITY if cat_counts[k] > 0
    ) or "(카테고리 없음)"
    print(f"✅ evaluation.md 생성 ({n_axes}축) — {verdict_emoji} {verdict_label}  [{cat_summary}]")
    if total is not None and prev_total is not None:
        print(f"   점수 추세 (보조): {total}/{n_axes*100} (Δ {total - prev_total:+d})")
    if missing:
        print(f"⚠️  누락 축: {missing}")

    # 1.5 Sanity check
    issues = validate_axis_consistency(project, axis_data)
    if issues:
        print("⚠️  Sanity check 위반:")
        for iss in issues:
            print(f"   {iss}")

    # 2. work-plan.md 준비
    wp_path = work_plan_path(project)
    existing = wp_path.read_text(encoding="utf-8") if wp_path.exists() else ""
    stage = detect_stage(project)

    if existing and not is_v2_format(existing):
        archived = archive_legacy(project, existing)
        print(f"ℹ️  기존 v1 work-plan을 {archived.relative_to(project_root(project))}로 이동")
        existing = ""

    if not existing:
        existing = make_skeleton(stage, ambition,
                                  "_(대시보드는 아래에서 재계산)_",
                                  "_(브리핑은 아래에서 재계산)_",
                                  trigger="initial")

    # 3. HUNT 발급 (claim-extraction의 hunts[] → work-plan HUNT 카드 1:1)
    # registry가 single source of truth — 중복 ID/covers 방지 + reactivation 처리.
    new_cards, updated_ce_texts, reactivated_ids = process_hunts(project, existing)
    for p, text in updated_ce_texts.items():
        p.write_text(text, encoding="utf-8")
        print(f"   {p.relative_to(project_root(project))} 업데이트")

    # 3.5 Registry sync: work-plan의 completed 섹션의 HUNT를 registry에 mark_completed 한 뒤
    # work-plan에서 제거 (user 요청: "완료되면 work-plan에서 삭제").
    root = project_root(project)
    registry = hunt_registry.load(root)
    tmp_sections = split_sections(existing) if existing else None
    completed_hunt_ids = []
    if tmp_sections:
        completed_hunt_ids = hunt_registry.sync_from_work_plan(registry, tmp_sections)
        hunt_registry.save(root, registry)
    if completed_hunt_ids:
        print(f"   ✅ completed HUNT registry 기록: {len(completed_hunt_ids)}건 — work-plan에서 제거")

    # reactivation된 HUNT는 만약 work-plan에 남은 잔여 카드가 있다면 제거 (새 카드로 대체될 예정)
    reactivate_set = set(reactivated_ids)

    # 4. 대시보드·브리핑 재계산 (새 카드 반영 후)
    tmp = rebuild_work_plan(existing, "_(계산 중)_", "_(계산 중)_",
                             new_cards, stage, ambition, "eval",
                             remove_hunt_ids=set(completed_hunt_ids) | reactivate_set)
    sections = split_sections(tmp)
    stats = collect_task_stats(sections)
    recs = recommend_commands(sections, stats)
    dashboard = render_dashboard(stats, recs, axis_data)
    briefing = render_briefing(project, sections, stats, recs,
                                ambition, critical_mode, axis_data, prev_total)

    final = rebuild_work_plan(existing, dashboard, briefing,
                               new_cards, stage, ambition, "eval",
                               remove_hunt_ids=set(completed_hunt_ids) | reactivate_set)

    # 변경이 있는 경우에만 쓰기 (unnecessary snapshot 방지)
    # 단, mtime·timestamp 라인은 매번 바뀌므로 그 라인을 빼고 비교
    def normalize_for_compare(text: str) -> str:
        return re.sub(r"> 📅 마지막 갱신:.*\n", "", text)

    if wp_path.exists() and normalize_for_compare(existing) == normalize_for_compare(final):
        # 실질 변경 없음 → 파일 쓰기 skip (mtime 보존)
        print("ℹ️  work-plan.md 실질 변경 없음 — 파일 갱신 skip")
    else:
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
