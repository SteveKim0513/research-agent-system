#!/usr/bin/env python3
"""
evaluation_aggregator.py — axis reports → evaluation.md + work-plan.md live task board.

책임:
1. axis1~6-*.md 점수 파싱 → evaluations/latest/evaluation.md 생성
2. work-plan.md v2 skeleton 보장 (v1 감지 시 history/work-plan/000-legacy-v1.md로 자동 이동)
3. claim-extraction-*.md의 JSON 요약 `search[]` 배열 → work-plan.md RESEARCH-NNN (mode=search) 카드 1:1 발급 (covers dedup) + claim-extraction back-reference
4. research/write registry (papers/.registry.json, output/.registry.json) sync
5. work-plan.md 대시보드 재계산 (WORK-PLAN-FORMAT.md §5 스펙)
6. 기존 카드 (Active / In-progress / Blocked / Completed / Deferred)는 그대로 보존

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
import card_registry
import version_manager
import paper_reanalysis_delta


AXIS_FILES = {
    "axis1": ("axis1-reference.md", "레퍼런스 충실도"),
    "axis2": ("axis2-logic.md", "논리 전개 완성도"),
    "axis3": ("axis3-defense.md", "반박·강화 논리"),
    "axis4": ("axis4-originality.md", "독창성·기여도"),
    "axis5": ("axis5-concept.md", "구성개념 정의 정밀도"),
    "axis6": ("axis6-critical.md", "비판적 시각"),
}

TASK_TYPES = ["RESEARCH", "WRITE"]

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
    r"^### \[(RESEARCH|WRITE)-(\d+)\](.*?)$",
    re.MULTILINE,
)


# ──────────────────────────────────────────────────────────
# Path helpers
# ──────────────────────────────────────────────────────────

def project_root(project: str) -> Path:
    return Path("projects") / project


STAGES = ("flow", "output", "final")
VALID_STAGES = STAGES  # 명시 prefix 강제 — 자동 감지 폐기


def latest_dir(project: str, stage: str = "flow") -> Path:
    """평가 결과는 stage 폴더 하위에 배치. flow/evaluations/, output/evaluations/ (최신만)."""
    return project_root(project) / stage / "evaluations"


def archive_dir(project: str, stage: str = "flow") -> Path:
    """평가 history 경로 — history/{stage}/evaluations/."""
    return project_root(project) / "history" / stage / "evaluations"


def flow_md_path(project: str) -> Path:
    return project_root(project) / "flow" / "flow.md"


def work_plan_path(project: str) -> Path:
    return project_root(project) / "work-plan.md"


def output_dir(project: str) -> Path:
    return project_root(project) / "output"


def claim_extraction_path(project: str, stage: str) -> Path:
    """stage별 claim-extraction 파일 경로. flow/claim-extraction-flow.md, output/claim-extraction-output.md."""
    return project_root(project) / stage / f"claim-extraction-{stage}.md"


def claim_extraction_paths(project: str) -> list:
    """존재하는 claim-extraction 파일 모두 반환 (flow + output + final)."""
    paths = []
    for stage in STAGES:
        p = claim_extraction_path(project, stage)
        if p.exists():
            paths.append(p)
    return paths


def read_metadata(project: str) -> dict:
    p = project_root(project) / ".paper-metadata.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


# (detect_stage 제거 — stage는 사용자가 명시 prefix로만 결정)


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


def parse_axis_scores(project: str, stage: str):
    """이름은 legacy지만 카테고리·진단·점수 모두 반환."""
    lat = latest_dir(project, stage)
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
            f"ℹ️ ⚫ 측정 불가 축이 {na_count}개 — 측정 불완전. RESEARCH 실행 후 재평가 권장."
        )

    return issues


# ──────────────────────────────────────────────────────────
# evaluation.md 생성
# ──────────────────────────────────────────────────────────

def write_evaluation_md(project: str, stage: str, axis_data: dict, missing: list, ambition: str, critical_mode: bool):
    lat = latest_dir(project, stage)
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

    pipeline_desc = "병렬 축별 워커 (evaluation-orchestrator) → aggregator"
    if stage == "final":
        pipeline_desc += " → final-holistic-reviewer (adjudication)"

    out = [
        f"# 평가 진단 — {project}",
        "",
        f"**대상**: `projects/{project}/flow/flow.md`",
        f"**평가일**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**intellectual_ambition**: **{ambition}**" + (" 🎭" if critical_mode else ""),
        f"**파이프라인**: {pipeline_desc}",
        "",
        "> 신뢰 가능 (메인): 카테고리·진단·Critical Issues·RESEARCH.  보조 (trend only): 점수.",
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

    # Final stage 한정 — holistic banner
    if stage == "final":
        holistic_path = lat / "holistic-review.md"
        if holistic_path.exists():
            holistic_status = f"✅ 함께 생성됨: [`holistic-review.md`]({holistic_path.name}) — 통합 관점 adjudication 결과 참조."
        else:
            holistic_status = "⏳ `holistic-review.md` 미생성 — orchestrator가 `final-holistic-reviewer` 를 dispatch해야 work-plan 카드가 actionable."
        out.extend([
            "> 🛡 **Final stage 통합 평가 의무**",
            "> 위 6축 verdict는 *국소 진단*. 통합본은 사용자가 정합성을 선언한 상태이므로 *척추 보호 adjudication*이 별도 필요.",
            f"> {holistic_status}",
            "> work-plan WRITE 카드 적용 전 카드의 `holistic_verdict` 필드를 반드시 점검 (REJECT/DEFER/REROUTE는 skip).",
            "",
        ])

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

    eval_path = lat / "evaluation.md"
    eval_path.write_text("\n".join(out), encoding="utf-8")

    # frontmatter 부여 — based_on은 axis 파일들의 version 합집합
    stage = lat.parent.name  # flow|output
    flow_md = project_root(project) / "flow" / "flow.md"
    flow_v = version_manager.get_version_info(flow_md).get("version", 0)
    ce_path = (project_root(project) / stage / f"claim-extraction-{stage}.md")
    ce_v = version_manager.get_version_info(ce_path).get("version", 0)
    based_on = {}
    if flow_v:
        based_on["flow"] = flow_v
    if ce_v:
        based_on["claim-extraction"] = ce_v
    version_manager.update_version(eval_path, based_on=based_on, updated_by="aggregator")

    return total, prev_total


# ──────────────────────────────────────────────────────────
# work-plan.md — skeleton, section parsing, dashboard render
# ──────────────────────────────────────────────────────────

def is_v2_format(text: str) -> bool:
    required = ["## 📊 대시보드", "## 🟡 Active", "## 🔵 In-progress", "## 🟢 Recent completed"]
    return all(h in text for h in required)


def archive_legacy(project: str, legacy_text: str) -> Path:
    """기존 v1 work-plan.md를 history/work-plan/000-legacy-v1.md로 이동."""
    archive_dir = project_root(project) / "history" / "work-plan"
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
# RESEARCH mode=search processing (from claim-extraction search[] → work-plan cards)
# ──────────────────────────────────────────────────────────

# claim-extraction의 ```json ... ``` 요약 블록 추출 (nested [] 안전)
JSON_BLOCK_RE = re.compile(r"```json\s*\n(\{.*?\n\})\s*\n```", re.DOTALL)


def extract_search_proposals_from_claim_extraction(ce_paths: list) -> list:
    """claim-extraction-*.md의 ```json 요약 블록에서 search[] 배열 파싱.

    Returns: list of {"id": "RESEARCH-001", "covers": [R-IDs], "query": "...", "topic": "..."} dicts.
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
            items = data.get("search")
            if not items:
                continue
            for h in items:
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


def extract_reanalyze_proposals_from_claim_extraction(ce_paths: list) -> list:
    """claim-extraction-*.md의 ```json 요약 블록에서 reanalyze[] 배열 파싱.

    Returns: list of {"id": "RESEARCH-XXX", "target_pdf": "...", "angle": "...", "topic": "..."} dicts.
    순서 보존.
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
            items = data.get("reanalyze")
            if not items:
                continue
            for r in items:
                rid = r.get("id")
                if not rid or rid in seen_ids:
                    continue
                seen_ids.add(rid)
                collected.append({
                    "id": rid,
                    "target_pdf": r.get("target_pdf") or "",
                    "angle": r.get("angle") or "",
                    "topic": r.get("topic") or "",
                    "current_version": r.get("current_version") or "",
                    "source_file": p.name,
                })
            break
    return collected


def process_reanalyze_proposals(project: str, work_plan_text: str):
    """claim-extraction의 reanalyze[] → RESEARCH mode=reanalyze 카드 1:1 발급.

    dedup_key = (mode=reanalyze, pdf_filename, angle).
    동일 dedup_key가 이미 활성이면 skip, completed면 reactivation.

    Returns: (new_cards, replacement_map, reactivated_ids)
    """
    ce_paths = claim_extraction_paths(project)
    if not ce_paths:
        return [], {}, []

    proposed = extract_reanalyze_proposals_from_claim_extraction(ce_paths)
    if not proposed:
        return [], {}, []

    root = project_root(project)
    registry = card_registry.load(root, "research")
    # bootstrap은 process_research_proposals에서 이미 처리됨

    replacement_map = {}
    new_cards = []
    reactivated_cards = []
    reactivated_ids = []
    skipped_active = []

    for r in proposed:
        dedup_raw = [r["target_pdf"], r["angle"]]
        existing_cid = card_registry.find_by_dedup_key(registry, "reanalyze", dedup_raw)
        if existing_cid:
            status = registry["cards"][existing_cid]["status"]
            replacement_map[r["id"]] = existing_cid
            if status == "completed":
                card_registry.reactivate(registry, existing_cid,
                                          reason=f"동일 (pdf, angle) 재제안 (from {r['id']})")
                meta = registry["cards"][existing_cid]
                card_meta = {
                    "topic": meta.get("metadata", {}).get("무엇") or r["topic"],
                    "대상 PDF": r["target_pdf"],
                    "재분석 각도": r["angle"],
                    "source_file": r["source_file"],
                }
                reactivated_cards.append(build_research_card(existing_cid, "reanalyze", card_meta, note="reactivated"))
                reactivated_ids.append(existing_cid)
            else:
                skipped_active.append((r["id"], existing_cid, status))
            continue

        new_id = card_registry.next_id(registry)
        replacement_map[r["id"]] = new_id
        new_cards.append(build_research_card(new_id, "reanalyze", {
            "topic": r["topic"],
            "대상 PDF": r["target_pdf"],
            "재분석 각도": r["angle"],
            "source_file": r["source_file"],
        }))
        card_registry.add_new(registry, new_id, "reanalyze", dedup_raw, {
            "무엇": r["topic"],
            "대상 PDF": r["target_pdf"],
            "재분석 각도": r["angle"],
            "source_file": r["source_file"],
        })

    card_registry.save(root, registry)

    if skipped_active:
        print(f"   ↪︎ 이미 활성 RESEARCH(reanalyze) 스킵 ({len(skipped_active)}건)")
    if reactivated_ids:
        print(f"   🔄 reanalyze reactivation: {len(reactivated_ids)}건")
    if new_cards:
        n_new = len(new_cards) - len(reactivated_ids)
        if n_new > 0:
            print(f"   🆕 신규 RESEARCH(reanalyze) 발급: {n_new}건")

    return new_cards + reactivated_cards, replacement_map, reactivated_ids


def process_research_proposals(project: str, work_plan_text: str):
    """claim-extraction의 search[] → work-plan.md RESEARCH-NNN (mode=search) 카드 1:1 발급.

    Single source of truth: `papers/.registry.json` (card_registry, domain=research).
    중복 발급 방지 2-layer:
    1. Primary (dedup_key match): 정규화된 covers가 기존 RESEARCH mode=search와 일치 시:
       - active 상태 → skip (이미 활성)
       - completed → reactivation (ready + work-plan 재삽입)
    2. Secondary: registry가 비어있고 work-plan에 RESEARCH 카드가 있으면 bootstrap.

    Returns: (new_cards: list[str], updated_ce_texts: dict[Path, str], reactivated_ids: list[str])
    """
    ce_paths = claim_extraction_paths(project)
    if not ce_paths:
        return [], {}, []

    proposed = extract_search_proposals_from_claim_extraction(ce_paths)
    if not proposed:
        return [], {}, []

    root = project_root(project)
    registry = card_registry.load(root, "research")

    if not registry["cards"] and work_plan_text:
        added = card_registry.bootstrap_from_work_plan(registry, work_plan_text)
        if added:
            print(f"   🔧 research registry bootstrap: {added}건 역복원 (papers/.registry.json)")

    replacement_map = {}
    new_cards = []
    reactivated_cards = []
    reactivated_ids = []
    skipped_active = []

    for h in proposed:
        covers = h.get("covers") or []
        existing_cid = card_registry.find_by_dedup_key(registry, "search", covers)
        if existing_cid:
            status = registry["cards"][existing_cid]["status"]
            replacement_map[h["id"]] = existing_cid
            if status == "completed":
                card_registry.reactivate(
                    registry, existing_cid,
                    reason=f"동일 covers 재제안 (from {h['id']})"
                )
                meta = registry["cards"][existing_cid]
                card_meta = {
                    "covers": covers,
                    "query": meta.get("metadata", {}).get("query") or h.get("query", ""),
                    "topic": meta.get("metadata", {}).get("무엇") or h.get("topic", ""),
                    "source_file": h.get("source_file") or meta.get("metadata", {}).get("source_file", ""),
                }
                reactivated_cards.append(build_research_card(existing_cid, "search", card_meta, note="reactivated"))
                reactivated_ids.append(existing_cid)
            else:
                skipped_active.append((h["id"], existing_cid, status))
            continue

        new_id = card_registry.next_id(registry)
        replacement_map[h["id"]] = new_id
        new_cards.append(build_research_card(new_id, "search", h))
        card_registry.add_new(
            registry, new_id, "search", covers,
            {
                "무엇": h.get("topic", ""),
                "query": h.get("query", ""),
                "source_file": h.get("source_file", ""),
            },
        )

    card_registry.save(root, registry)

    if skipped_active:
        preview = ", ".join(f"{orig}→{cid}({st})" for orig, cid, st in skipped_active[:3])
        more = f" 외 {len(skipped_active)-3}" if len(skipped_active) > 3 else ""
        print(f"   ↪︎ 이미 활성 RESEARCH 스킵 ({len(skipped_active)}건): {preview}{more}")
    if reactivated_ids:
        print(f"   🔄 reactivation: {len(reactivated_ids)}건 ({', '.join(reactivated_ids[:5])}{'...' if len(reactivated_ids) > 5 else ''})")
    if new_cards:
        print(f"   🆕 신규 RESEARCH 발급: {len(new_cards)}건")

    # claim-extraction 파일의 임시 ID 라벨을 발급된 RESEARCH ID로 치환
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


def build_research_card(card_id: str, mode: str, h: dict, note: str | None = None) -> str:
    """RESEARCH 카드 렌더. mode=search (외부 Consensus 검색) 또는 reanalyze (보유 PDF 재스캔)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    topic = h.get("topic") or h.get("무엇") or "claim-extraction 참조"
    source = h.get("source_file", "claim-extraction-flow.md")

    if note == "reactivated":
        log_line = f"- {now} · 🔄 **reactivated** by evaluation_aggregator (동일 dedup_key 재제안 감지, completed → ready)"
    else:
        log_line = f"- {now} · created by evaluation_aggregator (from {source})"

    if mode == "search":
        covers = h.get("covers") or []
        covers_str = ", ".join(covers) if covers else "(없음)"
        query = h.get("query", "")
        body = f"""**mode**: search

**담당 명령**: `"리서치 진행해줘"` → Consensus 자동 검색 (4-stage 파이프라인)

**covers**: {covers_str}

**query**: `{query}`

**검색 키워드 / 기대 논문 프로필**: `{source}`의 각 R 섹션 참조 / registry: `papers/.registry.json`"""
    else:  # reanalyze
        target_pdf = h.get("대상 PDF", "")
        angle = h.get("재분석 각도", "")
        body = f"""**mode**: reanalyze

**담당 명령**: `"논문 재분석해줘"` → paper-analyst Mode B

**대상 PDF**: {target_pdf}

**재분석 각도**: {angle}

**registry**: `papers/.registry.json`"""

    return f"""### [{card_id}] 🟡 active · P2 · axis1 · Stage 1

**무엇**: {topic}

{body}

**의존성**: 없음
**차단하는 것**: 없음

**진행 로그**:
{log_line}
"""


# ──────────────────────────────────────────────────────────
# WRITE 카드 발급 — axis*.md의 "🛠 WRITE 후보" 섹션 파싱 → card_registry
# ──────────────────────────────────────────────────────────

WRITE_SECTION_RE = re.compile(
    r"##\s+🛠\s+WRITE\s+후보(?!\s*출력\s*명세)(.*?)(?=\n##\s+|\Z)",
    re.DOTALL,
)
WRITE_ITEM_RE = re.compile(
    r"###\s+(W-\d+)\s*\[mode=(modify|create)\](.*?)(?=\n###\s+W-\d+|\Z)",
    re.DOTALL,
)


def _extract_field(block: str, label: str) -> str:
    m = re.search(rf"\*\*{re.escape(label)}\*\*\s*:\s*([^\n]+(?:\n(?!\*\*|##|###)[^\n]+)*)", block)
    return m.group(1).strip() if m else ""


def extract_write_proposals_from_axes(project: str, stage: str) -> list:
    """{stage}/evaluations/axis*.md를 모두 스캔해 WRITE 후보 추출.

    Returns: list of {axis, temp_id, mode, target, what, location/detail/etc, cause}
    """
    proposals = []
    eval_dir = latest_dir(project, stage)
    if not eval_dir.exists():
        return proposals

    for axis_path in sorted(eval_dir.glob("axis*.md")):
        text = axis_path.read_text(encoding="utf-8")
        axis_id = axis_path.stem  # 예: axis2-logic
        sec_m = WRITE_SECTION_RE.search(text)
        if not sec_m:
            continue
        section = sec_m.group(1)
        for item_m in WRITE_ITEM_RE.finditer(section):
            temp_id, mode, body = item_m.group(1), item_m.group(2), item_m.group(3)
            target = _extract_field(body, "대상")
            what = _extract_field(body, "무엇")
            cause = _extract_field(body, "원인") or axis_id
            entry = {
                "axis": axis_id,
                "temp_id": temp_id,
                "mode": mode,
                "target": target,
                "what": what,
                "cause": cause,
            }
            if mode == "modify":
                entry["detail"] = _extract_field(body, "상세")
            else:  # create
                entry["location"] = _extract_field(body, "위치")
                entry["content_req"] = _extract_field(body, "내용 요구")
            if target and what:
                proposals.append(entry)
    return proposals


def process_write_proposals(project: str, work_plan_text: str, stage: str) -> tuple:
    """axis*.md WRITE 후보 → work-plan WRITE 카드 발급.

    Returns: (new_cards, reactivated_ids)
    """
    proposed = extract_write_proposals_from_axes(project, stage)
    if not proposed:
        return [], []

    root = project_root(project)
    write_reg = card_registry.load(root, "write")

    # bootstrap: work-plan에 WRITE 카드 있으나 registry에 없으면 역복원
    if not write_reg["cards"] and work_plan_text:
        added = card_registry.bootstrap_from_work_plan(write_reg, work_plan_text)
        if added:
            print(f"   🔧 write registry bootstrap: {added}건 역복원 (output/.registry.json)")

    new_cards = []
    reactivated_ids = []
    skipped_active = 0
    by_axis: dict[str, list[str]] = {}

    for prop in proposed:
        if prop["mode"] == "modify":
            dedup_raw = [prop["target"], prop["what"]]
        else:
            dedup_raw = [prop["target"], prop.get("location") or prop["what"]]

        existing = card_registry.find_by_dedup_key(write_reg, prop["mode"], dedup_raw)
        if existing:
            status = write_reg["cards"][existing]["status"]
            if status == "completed":
                card_registry.reactivate(write_reg, existing,
                                          reason=f"동일 dedup_key 재제안 (from {prop['axis']}/{prop['temp_id']})")
                meta = write_reg["cards"][existing]["metadata"]
                new_cards.append(build_write_card(existing, prop["mode"], {
                    **meta,
                    "무엇": prop["what"],
                    "원인": prop["cause"],
                }, prop, note="reactivated"))
                reactivated_ids.append(existing)
            else:
                skipped_active += 1
            continue

        new_id = card_registry.next_id(write_reg)
        metadata = {
            "무엇": prop["what"],
            "대상 챕터": prop["target"],
            "원인": prop["cause"],
        }
        if prop["mode"] == "modify" and prop.get("detail"):
            metadata["수정 내용"] = prop["detail"]
        if prop["mode"] == "create":
            if prop.get("location"):
                metadata["위치"] = prop["location"]
            if prop.get("content_req"):
                metadata["내용 요구"] = prop["content_req"]

        card_registry.add_new(write_reg, new_id, prop["mode"], dedup_raw, metadata)
        new_cards.append(build_write_card(new_id, prop["mode"], metadata, prop))
        by_axis.setdefault(prop["axis"], []).append(new_id)

    card_registry.save(root, write_reg)

    if skipped_active:
        print(f"   ↪︎ 이미 활성 WRITE 스킵 ({skipped_active}건)")
    if reactivated_ids:
        print(f"   🔄 WRITE reactivation: {len(reactivated_ids)}건")
    if new_cards:
        summary = ", ".join(f"{ax}:{len(ids)}" for ax, ids in by_axis.items())
        n_new = len(new_cards) - len(reactivated_ids)
        print(f"   🆕 신규 WRITE 발급: {n_new}건 ({summary})")

    return new_cards, reactivated_ids


def build_write_card(card_id: str, mode: str, metadata: dict, prop: dict, note: str | None = None) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    target = metadata.get("대상 챕터", prop.get("target", ""))
    what = metadata.get("무엇", prop.get("what", ""))
    cause = metadata.get("원인", prop.get("cause", ""))

    # axis number → 영향 축 표기
    axis_id = prop.get("axis", "")
    axis_n_m = re.match(r"axis(\d+)", axis_id)
    axis_tag = f"axis{axis_n_m.group(1)}" if axis_n_m else "axis?"

    if note == "reactivated":
        log_line = f"- {now} · 🔄 **reactivated** by evaluation_aggregator (동일 dedup_key 재제안)"
    else:
        log_line = f"- {now} · created by aggregator (from {axis_id}/{prop.get('temp_id', '?')})"

    if mode == "modify":
        body = f"""**mode**: modify

**담당 명령**: `"output {Path(target).name} 수정해줘: {card_id}"` → output-editor

**대상 챕터**: {target}

**수정 내용**: {metadata.get('수정 내용', prop.get('detail', ''))}

**원인**: {cause}"""
    else:  # create
        body = f"""**mode**: create

**담당 명령**: `"초안 작성해줘"` → writing-architect (Phase 1 구조 설계 → Phase 2 작성)

**대상 챕터**: {target}

**위치**: {metadata.get('위치', prop.get('location', ''))}

**내용 요구**: {metadata.get('내용 요구', prop.get('content_req', ''))}

**원인**: {cause}"""

    return f"""### [{card_id}] 🟡 active · P2 · {axis_tag} · Stage 2

**무엇**: {what}

{body}

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

    # RESEARCH 카드는 mode로 search/reanalyze 구분 — 카드 본문에서 `**mode**:` 필드로 분류
    research_active = []
    for card in iter_cards(sections["active"]):
        if card["type"] == "RESEARCH":
            body = "\n".join(card["body_lines"])
            mode_m = re.search(r"\*\*mode\*\*:\s*(\w+)", body)
            mode = mode_m.group(1).strip() if mode_m else "search"
            research_active.append((f"RESEARCH-{card['num']:03d}", mode))

    search_active = [cid for cid, m in research_active if m == "search"]
    reanalyze_active = [cid for cid, m in research_active if m == "reanalyze"]

    if search_active:
        preview = ", ".join(search_active[:3])
        if len(search_active) > 3:
            preview += f" 외 {len(search_active) - 3}"
        recs.append(f'`"리서치 진행해줘"` — RESEARCH search {len(search_active)}건 대기 ({preview})')

    if reanalyze_active:
        recs.append(f'`"논문 재분석해줘"` — RESEARCH reanalyze {len(reanalyze_active)}건 대기')

    # WRITE 카드도 mode로 create/modify 구분
    write_active = []
    for card in iter_cards(sections["active"]):
        if card["type"] == "WRITE":
            body = "\n".join(card["body_lines"])
            mode_m = re.search(r"\*\*mode\*\*:\s*(\w+)", body)
            mode = mode_m.group(1).strip() if mode_m else "modify"
            write_active.append((f"WRITE-{card['num']:03d}", mode))

    create_active = [cid for cid, m in write_active if m == "create"]
    modify_active = [cid for cid, m in write_active if m == "modify"]

    if create_active and len(recs) < 3:
        recs.append(f'`"초안 작성해줘"` — WRITE create {len(create_active)}건 대기')

    if modify_active and len(recs) < 3:
        preview = ", ".join(modify_active[:3])
        recs.append(f'`"Chapter X 수정해줘"` — WRITE modify {len(modify_active)}건 ({preview})')

    if not recs:
        if stats["state_counts"]["blocked"] > 0:
            recs.append(f'`"상태 확인해줘"` — 🔴 Blocked {stats["state_counts"]["blocked"]}건 의존성 검토 필요')
        else:
            recs.append('_(권장 명령 없음 — 🟡 Active 비어있음. `"flow 레퍼런스 분석해줘"` / `"flow 내용 분석해줘"`로 새 카드 발급)_')

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
    out_dir = root / "output"
    if out_dir.exists():
        real_files = [p for p in out_dir.glob("*.md") if not p.name.startswith("claim-extraction")]
        if real_files:
            work_files.append(f"- `output/*.md` — 생성된 결과물 {len(real_files)}개. `\"output {{파일명}} 수정해줘: WRITE-NNN\"`")
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
        commands_block.append('1. `"flow 레퍼런스 분석해줘"` + `"flow 내용 분석해줘"` — 아직 분석 없음')

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
    """파일 상단 meta 4줄을 현재 값으로 업데이트 (timestamp, Mode, Stage, ambition)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = header_block.split("\n")
    updated = []
    replaced = {"timestamp": False, "mode": False, "stage": False, "ambition": False}

    for line in lines:
        if line.startswith("> 📅 마지막 갱신:"):
            updated.append(f"> 📅 마지막 갱신: {now} ({trigger})")
            replaced["timestamp"] = True
        elif line.startswith("> Mode:"):
            updated.append(f"> Mode: {stage}")
            replaced["mode"] = True
        elif line.startswith("> Stage:"):
            # 호환: stage는 mode와 동기화 (구 v2 호환)
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
                if not replaced["mode"]:
                    added.append(f"> Mode: {stage}")
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
    remove_research_ids: set = None,
) -> str:
    """기존 work-plan의 섹션을 보존하며 대시보드 치환 + active에 새 카드 추가.

    remove_research_ids: 주어진 RESEARCH ID 카드를 모든 섹션에서 제거
    (completed mode=search 정리 / reactivation 대체).
    """
    sections = split_sections(existing)
    header_block = extract_header_block(existing)
    header_block = update_header_block(header_block, stage, ambition, trigger)

    # completed/reactivated RESEARCH 카드 제거
    if remove_research_ids:
        for key in ("active", "in_progress", "blocked", "deferred",
                    "completed_recent", "completed_older"):
            sections[key] = card_registry.remove_cards_from_section_text(
                sections[key], remove_research_ids, "RESEARCH"
            )

    # 새 RESEARCH 카드를 Active 섹션 하단에 추가
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

VALID_ACTIONS = ("reference", "content", "status")


def _check_action_dependencies(project: str, stage: str, action: str) -> list[str]:
    """action 진입 전 의존성 stale 체크 → LLM dispatch instruction 메시지 리스트 반환.

    - reference action: claim-extraction-{stage}.md mtime > 본문 mtime 또는 부재 → claim-extractor 선행
    - content action: axis2~6 mtime < 본문 mtime → 해당 stale axis만 재실행 권장
    - stale axis 외에는 기존 결과 활용 (delta 모드)
    """
    root = project_root(project)
    msgs = []

    if stage == "flow":
        body_md = root / "flow" / "flow.md"
        body_files = [body_md] if body_md.exists() else []
    else:
        body_files = [p for p in (root / "output").glob("*.md")
                      if not p.name.startswith("claim-extraction")]
    if not body_files:
        return msgs
    body_mtime_max = max(p.stat().st_mtime for p in body_files)

    if action == "reference":
        # claim-extraction-{stage}.md 검사
        ce = root / stage / f"claim-extraction-{stage}.md"
        if not ce.exists():
            msgs.append(f"📝 `{stage}/claim-extraction-{stage}.md` 부재 → "
                        f"`claim-extractor` Agent를 먼저 dispatch (stage={stage})")
        elif ce.stat().st_mtime < body_mtime_max:
            ce_v = version_manager.get_version_info(ce).get("version", 0)
            body_v = version_manager.get_version_info(body_files[0]).get("version", 0)
            msgs.append(f"📝 `{stage}/claim-extraction-{stage}.md` stale "
                        f"(v{ce_v}, 본문 v{body_v}) → `claim-extractor` Agent 재호출 (stage={stage})")

    if action == "content":
        # axis2~6 stale 검사 (delta 식별)
        eval_dir = latest_dir(project, stage)
        stale_axes = []
        if eval_dir.exists():
            for n in (2, 3, 4, 5, 6):
                pattern = list(eval_dir.glob(f"axis{n}-*.md"))
                if not pattern:
                    stale_axes.append(f"axis{n}")  # 부재 → 새로 실행
                    continue
                ax = pattern[0]
                if ax.stat().st_mtime < body_mtime_max:
                    stale_axes.append(f"axis{n}")
        else:
            stale_axes = [f"axis{n}" for n in (2, 3, 4, 5, 6)]
        if stale_axes:
            msgs.append(f"📊 stale 축 {len(stale_axes)}개: {', '.join(stale_axes)} → "
                        f"각 axis*-scorer Agent dispatch 권장 (stale 축만)")
            msgs.append(f"   fresh 축은 기존 {stage}/evaluations/axis*.md 결과 그대로 활용 (delta 모드)")

    return msgs


def _issue_reanalyze_from_delta(project: str, affected: list) -> tuple:
    """paper_reanalysis_delta 결과 → RESEARCH(reanalyze) 카드 발급.

    affected: [{"paper": "Zelazo_2012", "primary_section": "hot/cool EF", "changed_section": "..."}]
    Returns: (new_cards: list[str], reactivated_ids: list[str])
    """
    root = project_root(project)
    registry = card_registry.load(root, "research")

    new_cards = []
    reactivated_ids = []
    skipped = 0

    for entry in affected:
        paper = entry["paper"]
        # 추정: papers/collected/{paper}.pdf
        target_pdf = f"papers/collected/{paper}.pdf"
        angle = f"flow 변경 섹션 '{entry['changed_section']}' 반영 — {entry['primary_section']} 재스캔"
        topic = f"{paper} delta 재분석 ({entry['primary_section']})"

        dedup_raw = [target_pdf, angle]
        existing_cid = card_registry.find_by_dedup_key(registry, "reanalyze", dedup_raw)
        if existing_cid:
            status = registry["cards"][existing_cid]["status"]
            if status == "completed":
                card_registry.reactivate(registry, existing_cid,
                                          reason=f"flow delta 재제안 (paper={paper})")
                meta = registry["cards"][existing_cid]
                card_meta = {
                    "topic": meta.get("metadata", {}).get("무엇") or topic,
                    "대상 PDF": target_pdf,
                    "재분석 각도": angle,
                    "source_file": "paper_reanalysis_delta",
                }
                new_cards.append(build_research_card(existing_cid, "reanalyze", card_meta, note="reactivated"))
                reactivated_ids.append(existing_cid)
            else:
                skipped += 1
            continue

        new_id = card_registry.next_id(registry)
        new_cards.append(build_research_card(new_id, "reanalyze", {
            "topic": topic,
            "대상 PDF": target_pdf,
            "재분석 각도": angle,
            "source_file": "paper_reanalysis_delta",
        }))
        card_registry.add_new(registry, new_id, "reanalyze", dedup_raw, {
            "무엇": topic,
            "대상 PDF": target_pdf,
            "재분석 각도": angle,
            "source_file": "paper_reanalysis_delta",
        })

    card_registry.save(root, registry)

    if skipped:
        print(f"   ↪︎ delta 재제안 중 이미 활성 {skipped}건 skip")
    n_new = len(new_cards) - len(reactivated_ids)
    if n_new > 0:
        print(f"   🆕 delta RESEARCH(reanalyze) 발급: {n_new}건")
    if reactivated_ids:
        print(f"   🔄 delta reanalyze reactivation: {len(reactivated_ids)}건")

    return new_cards, reactivated_ids


def _apply_frontmatter_to_derivatives(project: str, stage: str) -> None:
    """파생 파일들에 frontmatter 자동 부여.

    aggregator가 호출되는 시점은 곧 분석 흐름이 막 끝난 직후. 작성자(LLM)가
    frontmatter 부여를 빠뜨려도 여기서 보장. content_hash 기반이라 변경 없으면
    no-op (idempotent).

    대상:
    - {stage}/claim-extraction-{stage}.md (based_on=flow 또는 output)
    - {stage}/evaluations/axis*.md (based_on=stage 본문 + claim-extraction)
    - {stage}/critical/{questions,commitments}.md (based_on=stage 본문)
    """
    root = project_root(project)
    flow_md = root / "flow" / "flow.md"
    flow_v = version_manager.get_version_info(flow_md).get("version", 0)

    # output multi-body — 가장 큰 version
    output_v = 0
    out_dir = root / "output"
    if out_dir.exists():
        for p in out_dir.glob("*.md"):
            if p.name.startswith("claim-extraction"):
                continue
            v = version_manager.get_version_info(p).get("version", 0)
            if v > output_v:
                output_v = v

    body_v = output_v if stage == "output" else flow_v

    # 1. claim-extraction-{stage}.md
    ce_path = root / stage / f"claim-extraction-{stage}.md"
    if ce_path.exists():
        based_on = {stage: body_v} if body_v else {}
        version_manager.update_version(ce_path, based_on=based_on, updated_by="claim-extractor")

    ce_v = version_manager.get_version_info(ce_path).get("version", 0) if ce_path.exists() else 0

    # 2. axis*.md
    eval_dir = latest_dir(project, stage)
    if eval_dir.exists():
        for axis_path in eval_dir.glob("axis*.md"):
            based_on = {stage: body_v} if body_v else {}
            # axis1만 claim-extraction 의존 (레퍼런스 매칭이라)
            if axis_path.name.startswith("axis1") and ce_v:
                based_on["claim-extraction"] = ce_v
            version_manager.update_version(axis_path, based_on=based_on, updated_by=axis_path.stem)

    # 3. critical/{questions,commitments}.md
    crit_dir = root / stage / "critical"
    if crit_dir.exists():
        for crit_path in crit_dir.glob("*.md"):
            based_on = {stage: body_v} if body_v else {}
            version_manager.update_version(crit_path, based_on=based_on, updated_by="critical-companion")


def aggregate(project: str, action: str = "reference", stage: str | None = None) -> int:
    """
    aggregator entry point.

    action:
      - "reference"  : 레퍼런스 분석 — axis1 통합 + RESEARCH 카드 발급
      - "content"    : 내용 분석 — axis2~6 통합 + WRITE 카드 발급
      - "status"     : 분석 없이 현재 상태만 출력 (status renderer)

    stage: "flow" | "output" | "final" — 사용자가 명시 prefix로 지정 (필수)
    """
    if action not in VALID_ACTIONS:
        print(f"❌ action은 {VALID_ACTIONS} 중 하나여야 함, got {action!r}", file=sys.stderr)
        return 1
    if stage is None or stage not in STAGES:
        print(
            f"❌ stage 필수: {STAGES} 중 하나 명시 (got {stage!r}). "
            f"사용자가 'flow / output / final' prefix를 붙여야 함.",
            file=sys.stderr,
        )
        return 1

    if action == "status":
        return render_status(project, stage)

    # action별 stale 의존성 검사 — LLM에 명시적 "선행 dispatch" instruction 출력
    stale_msgs = _check_action_dependencies(project, stage, action)
    if stale_msgs:
        print("\n⚠️  의존성 stale 감지 — 분석 전 다음을 먼저 실행해야 정합성 유지됩니다:")
        for msg in stale_msgs:
            print(f"   {msg}")
        print()

    # 사용자 본문 파일 자동 version bump (사용자가 편집한 것 자동 감지)
    root = project_root(project)
    user_files = [root / "flow" / "flow.md"]
    out_dir = root / "output"
    if out_dir.exists():
        user_files += [p for p in out_dir.glob("*.md") if not p.name.startswith("claim-extraction")]
    bumped = []
    flow_was_bumped = False
    for fp in user_files:
        if fp.exists():
            res = version_manager.bump_if_changed(fp, updated_by="user")
            if res.get("incremented"):
                snap = res.get("snapshot_path")
                bumped.append((fp.relative_to(root), res["version"], snap))
                if fp.name == "flow.md":
                    flow_was_bumped = True
    if bumped:
        for f, v, snap in bumped:
            line = f"🔄 사용자 편집 감지: {f} → v{v}"
            if snap:
                try:
                    rel_snap = Path(snap).resolve().relative_to(root.resolve())
                    line += f"  (이전 버전 백업: {rel_snap})"
                except ValueError:
                    pass
            print(line)

    # flow가 bump됐고 action=reference면 paper_reanalysis_delta 자동 호출 → reanalyze 카드 발급
    delta_reanalyze_cards = []
    delta_reanalyze_reactivated = []
    if flow_was_bumped and action == "reference":
        affected = paper_reanalysis_delta.get_affected_papers(project)
        if affected:
            print(f"   📊 flow 변경 delta — 영향 논문 {len(affected)}건 → RESEARCH(reanalyze) 발급 검토")
            delta_reanalyze_cards, delta_reanalyze_reactivated = _issue_reanalyze_from_delta(project, affected)

    lat = latest_dir(project, stage)
    if not lat.exists():
        print(f"⚠️  {lat} 없음 — axis scorer 결과 없음", file=sys.stderr)
        return 1

    # 0.7 파생 파일 frontmatter 자동 부여 (sync 보장)
    # claim-extraction-{stage}.md, axis*.md 변경 감지되면 version_manager로 갱신.
    _apply_frontmatter_to_derivatives(project, stage)

    # 1. axis 파싱 + evaluation.md 생성
    axis_data, missing, ambition, critical_mode = parse_axis_scores(project, stage)
    total, prev_total = write_evaluation_md(project, stage, axis_data, missing, ambition, critical_mode)

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

    if existing and not is_v2_format(existing):
        archived = archive_legacy(project, existing)
        print(f"ℹ️  기존 v1 work-plan을 {archived.relative_to(project_root(project))}로 이동")
        existing = ""

    if not existing:
        existing = make_skeleton(stage, ambition,
                                  "_(대시보드는 아래에서 재계산)_",
                                  "_(브리핑은 아래에서 재계산)_",
                                  trigger="initial")

    # 3. action별 카드 발급
    # - reference: claim-extraction의 search[] → RESEARCH 카드만
    # - content  : axis*.md의 🛠 WRITE 후보 → WRITE 카드만
    new_cards = []
    updated_ce_texts = {}
    reactivated_ids = []

    if action == "reference":
        # mode=search 발급
        new_cards, updated_ce_texts, reactivated_ids = process_research_proposals(project, existing)
        # mode=reanalyze 발급 (claim-extraction의 reanalyze[] 기반)
        ra_cards, ra_replacement, ra_reactivated = process_reanalyze_proposals(project, existing)
        new_cards = new_cards + ra_cards
        reactivated_ids = reactivated_ids + ra_reactivated
        # delta 기반 reanalyze 카드 (위에서 flow_was_bumped 시 산출됨)
        new_cards = new_cards + delta_reanalyze_cards
        reactivated_ids = reactivated_ids + delta_reanalyze_reactivated
        # claim-extraction 파일에 reanalyze 임시 ID도 치환 (XXX/YYY → RESEARCH-NNN)
        if ra_replacement:
            for p in claim_extraction_paths(project):
                try:
                    text = updated_ce_texts.get(p) or p.read_text(encoding="utf-8")
                except Exception:
                    continue
                changed = text
                for old, new in ra_replacement.items():
                    if old == new:
                        continue
                    changed = re.sub(rf"\[{old}\]", f"[{new}]", changed)
                    changed = changed.replace(f'"{old}"', f'"{new}"')
                if changed != text:
                    updated_ce_texts[p] = changed
        for p, text in updated_ce_texts.items():
            p.write_text(text, encoding="utf-8")
            print(f"   {p.relative_to(project_root(project))} 업데이트")

    if action == "content":
        new_write_cards, reactivated_write_ids = process_write_proposals(project, existing, stage)
        new_cards = new_cards + new_write_cards
        reactivated_ids = reactivated_ids + reactivated_write_ids

    # 3.5 research registry sync: work-plan completed 섹션의 RESEARCH를 mark_completed.
    # mode=search 카드는 완료 시 work-plan에서 제거 (4-stage 산출물이 별도 파일에 남음).
    # mode=reanalyze 카드는 work-plan에 보존 (analyzed/*.md에 v2 append로 이력 남음).
    root = project_root(project)
    research_reg = card_registry.load(root, "research")
    tmp_sections = split_sections(existing) if existing else None
    completed_research_ids = []
    search_completed_ids = []  # work-plan에서 제거할 대상 (mode=search만)
    if tmp_sections:
        completed_research_ids = card_registry.sync_from_work_plan(research_reg, tmp_sections)
        card_registry.save(root, research_reg)
        # mode=search만 work-plan에서 제거
        for cid in completed_research_ids:
            c = research_reg["cards"].get(cid)
            if c and c.get("mode") == "search":
                search_completed_ids.append(cid)
    if search_completed_ids:
        print(f"   ✅ completed RESEARCH(search) 기록: {len(search_completed_ids)}건 — work-plan에서 제거")

    # 3.6 write registry sync (lifecycle 추적 + bootstrap). work-plan에 완료 카드 보존.
    write_reg = card_registry.load(root, "write")
    if tmp_sections:
        added = card_registry.bootstrap_from_work_plan(write_reg, existing)
        done = card_registry.sync_from_work_plan(write_reg, tmp_sections)
        card_registry.save(root, write_reg)
        if added:
            print(f"   🔧 write registry bootstrap: {added}건 역복원")
        if done:
            print(f"   ✅ completed WRITE 기록: {len(done)}건 (work-plan에는 보존)")

    # reactivation된 RESEARCH가 work-plan에 잔여로 남아있다면 제거 (새 카드로 대체)
    reactivate_set = set(reactivated_ids)

    # 4. 대시보드·브리핑 재계산 (새 카드 반영 후)
    tmp = rebuild_work_plan(existing, "_(계산 중)_", "_(계산 중)_",
                             new_cards, stage, ambition, "eval",
                             remove_research_ids=set(search_completed_ids) | reactivate_set)
    sections = split_sections(tmp)
    stats = collect_task_stats(sections)
    recs = recommend_commands(sections, stats)
    dashboard = render_dashboard(stats, recs, axis_data)
    briefing = render_briefing(project, sections, stats, recs,
                                ambition, critical_mode, axis_data, prev_total)

    final = rebuild_work_plan(existing, dashboard, briefing,
                               new_cards, stage, ambition, "eval",
                               remove_research_ids=set(search_completed_ids) | reactivate_set)

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

    # Final stage 한정 — holistic dispatch 의무 안내
    if stage == "final":
        holistic_path = lat / "holistic-review.md"
        eval_path = lat / "evaluation.md"
        needs_holistic = (
            not holistic_path.exists()
            or (eval_path.exists() and holistic_path.stat().st_mtime < eval_path.stat().st_mtime)
        )
        if needs_holistic:
            print()
            print("🛡 stage=final — holistic adjudication 필수")
            print("   evaluation-orchestrator는 final-holistic-reviewer를 dispatch해야 합니다.")
            print("   (통합본 척추를 prior로, axis 카드 verdict를 adjudicate)")
            print(f"   출력 예정: {holistic_path.relative_to(project_root(project))}")
            print("   미실행 시 work-plan WRITE 카드는 actionable로 간주하지 않음.")
        else:
            print()
            print("🛡 holistic-review.md 최신 — adjudication 완료 상태")

    return 0


def render_status(project: str, stage: str) -> int:
    """현재 상태 명령어 — 폴더 상태·진행도·다음 권장 명령 한눈에 출력."""
    root = project_root(project)
    if not root.exists():
        print(f"❌ 프로젝트 없음: {root}", file=sys.stderr)
        return 1

    # 1. 폴더 상태
    print(f"\n📍 Project: {project}")
    flow_status = "있음" if (root/'flow').exists() else "없음"
    out_status = "있음" if (root/'output').exists() else "없음"
    final_status = "있음" if (root/'final').exists() else "없음"
    print(f"   Folders: flow/ {flow_status} · output/ {out_status} · final/ {final_status}")
    print(f"   💡 stage 명령: \"flow 평가해줘\" / \"output 평가해줘\" / \"final 평가해줘\"\n")

    # 2. flow / output 본문 상태
    for st in STAGES:
        st_dir = root / st
        if not st_dir.exists():
            continue
        body_files = []
        if st == "flow":
            body = st_dir / "flow.md"
            if body.exists():
                body_files.append(("flow.md", body))
        else:
            body_files = [(p.name, p) for p in st_dir.glob("*.md")
                          if not p.name.startswith("claim-extraction")]
        if body_files:
            for name, p in body_files[:3]:
                lines = len(p.read_text(encoding="utf-8").splitlines())
                print(f"   {st}/{name}: {lines}줄")
            if len(body_files) > 3:
                print(f"   ... 외 {len(body_files)-3}개")

        # claim-extraction
        ce = claim_extraction_path(project, st)
        if ce.exists():
            from datetime import datetime
            mtime = datetime.fromtimestamp(ce.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"   {st}/claim-extraction-{st}.md : {mtime} (레퍼런스 분석 완료)")

        # evaluations/latest
        eval_dir = latest_dir(project, st)
        if eval_dir.exists():
            ax_files = sorted(eval_dir.glob("axis*.md"))
            if ax_files:
                from datetime import datetime
                mtime = datetime.fromtimestamp(ax_files[0].stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"   {st}/evaluations/latest : {mtime} ({len(ax_files)}축 결과)")

        # critical mode
        critical_dir = st_dir / "critical"
        if critical_dir.exists():
            print(f"   {st}/critical : 활성 ({len(list(critical_dir.glob('*.md')))} 파일)")
        print()

    # 3. papers / RESEARCH 카드
    research_reg = card_registry.load(root, "research")
    cands = list((root / "papers" / "candidates").glob("*.pdf")) if (root / "papers" / "candidates").exists() else []
    coll = list((root / "papers" / "collected").glob("*.pdf")) if (root / "papers" / "collected").exists() else []
    consensus = root / "papers" / "consensus-results.md"

    print(f"📚 Research")
    n_total = len(research_reg["cards"])
    n_done = sum(1 for c in research_reg["cards"].values() if c["status"] == "completed")
    n_active = sum(1 for c in research_reg["cards"].values() if c["status"] in ("ready", "in_progress"))
    print(f"   RESEARCH 카드: {n_total} (완료 {n_done} · 활성 {n_active})")
    if consensus.exists():
        text = consensus.read_text(encoding="utf-8")
        n_papers = len(re.findall(r"^\#{2,3}\s+#\d+", text, re.MULTILINE))
        print(f"   consensus-results.md: {n_papers}편 후보 확보")
    print(f"   candidates/: {len(cands)}편 대기 (사용자 선별)")
    print(f"   collected/: {len(coll)}편 처리 완료")
    print()

    # 4. WRITE 카드 + 활성 카드 dispatch 가이드
    write_reg = card_registry.load(root, "write")
    n_w_total = len(write_reg["cards"])
    n_w_active = sum(1 for c in write_reg["cards"].values() if c["status"] in ("ready", "in_progress"))
    if n_w_total:
        print(f"✏️  Write")
        print(f"   WRITE 카드: {n_w_total} (활성 {n_w_active})\n")

    # 5. 활성 카드 dispatch 가이드 (각 카드별 다음 명령)
    active_cards = []
    for cid, c in research_reg["cards"].items():
        if c["status"] in ("ready", "in_progress"):
            cmd = '"리서치 진행해줘"' if c["mode"] == "search" else '"논문 재분석해줘"'
            active_cards.append((cid, c["mode"], cmd, c["metadata"].get("무엇", "")))
    for cid, c in write_reg["cards"].items():
        if c["status"] in ("ready", "in_progress"):
            target = c["metadata"].get("대상 챕터", "")
            fname = Path(target).name if target else "{파일명}"
            cmd = '"초안 작성해줘"' if c["mode"] == "create" else f'"output {fname} 수정해줘: {cid}"'
            active_cards.append((cid, c["mode"], cmd, c["metadata"].get("무엇", "")))

    if active_cards:
        print(f"🎯 처리 가능한 활성 카드 ({len(active_cards)}개)")
        for cid, mode, cmd, what in active_cards[:8]:
            preview = (what[:40] + "…") if len(what) > 40 else what
            print(f"   {cid} ({mode:9}) → {cmd}")
            if preview:
                print(f"     └ {preview}")
        if len(active_cards) > 8:
            print(f"   ... 외 {len(active_cards)-8}개")
        print()

    # 6. 다음 권장 명령
    print(f"💡 권장 다음 명령:")
    recs = []
    if n_active > 0:
        recs.append(f'   • `"리서치 진행해줘"` — 활성 RESEARCH {n_active}건 실행')
    if n_done > 0 and len(cands) == 0 and len(coll) == 0:
        recs.append(f'   • consensus-results.md 검토 후 필요 PDF를 papers/candidates/에 투입')
    if len(cands) > 0:
        recs.append(f'   • `"논문 처리해줘"` — candidates/ {len(cands)}편 분석')
    flow_eval = latest_dir(project, "flow")
    if (root / "flow" / "flow.md").exists() and not (flow_eval / "axis1-reference.md").exists():
        recs.append(f'   • `"flow 레퍼런스 분석해줘"` — 아직 안 돌림')
    if (root / "flow" / "flow.md").exists() and not (flow_eval / "axis2-logic.md").exists():
        recs.append(f'   • `"flow 내용 분석해줘"` — 아직 안 돌림')
    if stage == "flow" and len(coll) > 0:
        recs.append(f'   • `"초안 작성해줘"` — output/ 단계 진입 (논문 분석 완료)')
    if not recs:
        recs.append(f'   • 현재 진행 중인 작업이 없습니다. 새 명령을 시작하세요.')
    for r in recs[:5]:
        print(r)
    print()

    # 6. 버전 / 싱크 상태
    print(f"🔢 버전 / 싱크 상태")
    sync_report = version_manager.render_sync_report(root)
    if sync_report.strip():
        for line in sync_report.split("\n"):
            print(f"   {line}" if line else "")
    else:
        print(f"   (검증 대상 파일 없음)")
    print()
    return 0


def main(argv: list) -> int:
    if len(argv) < 2:
        print("Usage: python3 evaluation_aggregator.py <project> <action> <stage>")
        print("  action : reference | content | status   (기본: reference)")
        print("  stage  : flow | output | final          (필수 — 사용자 명시 prefix)")
        return 1
    project = argv[1]
    action = argv[2] if len(argv) >= 3 else "reference"
    stage = argv[3] if len(argv) >= 4 else None
    try:
        return aggregate(project, action=action, stage=stage)
    except Exception as e:
        import traceback
        print(f"❌ aggregator 오류: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
