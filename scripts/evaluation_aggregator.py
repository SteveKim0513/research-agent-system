#!/usr/bin/env python3
"""
evaluation_aggregator.py — axis reports → evaluation.md (단일 산출).

책임 (v2 — work-plan.md, card_registry 폐기):
1. axis1~6-*.md 카테고리·진단 파싱 → evaluations/latest/evaluation.md 생성
2. evaluation.md에 다음 섹션 포함 (EVALUATION-FORMAT.md 스펙):
   - 🧭 다음 액션 (사용자가 지금 할 것)
   - 📊 축별 상태 요약
   - 🎯 Verdict
   - ⚠️ Critical Issues
   - 🟠 보강 필요
   - 📚 RESEARCH 항목 (claim-extractor가 식별한 미해결 R-NN)
   - ✏️ WRITE 권고 (axis*.md의 🛠 WRITE 후보)
3. RESEARCH-NNN/WRITE-NNN 카드 발급·등록 코드 제거 — R-NN은 claim-extractor 산출물에 그대로
4. work-plan.md 갱신·읽기·쓰기 코드 모두 제거
5. card_registry import 제거 (papers/.registry.json, output/.registry.json 미사용)

Usage:
    python3 scripts/evaluation_aggregator.py <project> <action> <stage>
      action : reference | content | status   (기본: reference)
      stage  : flow | output | final          (필수 — 사용자 명시 prefix)
"""
import json
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
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

# worst → best 순서. evaluation.md WRITE 권고 정렬용.
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

def _build_next_actions(
    axis_data: dict,
    research_search_items: list,
    research_reanalyze_items: list,
    write_proposals: list,
    stage: str,
) -> list[str]:
    """다음 액션 1–3개 생성 (자연어 명령 + 1줄 사유). EVALUATION-FORMAT.md §3.1 스펙."""
    actions: list[str] = []

    # 1. 미해결 RESEARCH search 항목 — `"리서치 진행해줘"`
    if research_search_items:
        ids_preview = ", ".join(h.get("id", "?") for h in research_search_items[:5])
        more = "" if len(research_search_items) <= 5 else f" 외 {len(research_search_items) - 5}건"
        actions.append(
            f'`"리서치 진행해줘"` — 미해결 RESEARCH {ids_preview}{more} '
            f"({len(research_search_items)}건). axis 1·3 보강에 필요."
        )

    # 2. reanalyze 항목 — `"논문 재분석해줘"`
    if research_reanalyze_items:
        actions.append(
            f'`"논문 재분석해줘"` — 보유 PDF {len(research_reanalyze_items)}건 재스캔 (flow 변경 반영).'
        )

    # 3. WRITE 권고가 있으면 가장 시급한 1건 자연어로 노출
    if write_proposals and len(actions) < 3:
        # 가장 시급한 axis 우선 (critical_gap > needs_work)
        def axis_priority(p):
            ax = p.get("axis", "")
            ax_key = re.match(r"axis\d+", ax).group(0) if re.match(r"axis\d+", ax) else ""
            cat = axis_data.get(ax_key, {}).get("category", "adequate")
            return CATEGORY_PRIORITY.index(cat) if cat in CATEGORY_PRIORITY else 99
        sorted_w = sorted(write_proposals, key=axis_priority)
        first = sorted_w[0]
        target = first.get("target") or "(대상 미명시)"
        what = first.get("what") or "수정 필요"
        actions.append(
            f'`"{Path(target).name} 수정해줘: {what[:30]}{"..." if len(what) > 30 else ""}"` '
            f"— {first.get('cause', '본문 보강 필요')}"
        )

    # fallback: 모든 축 🟢/🟡 — 다음 stage 권고
    if not actions:
        all_ok = axis_data and all(
            d.get("category") in ("strong", "adequate") for d in axis_data.values()
        )
        if all_ok:
            next_cmd = {
                "flow": '"초안 작성해줘"',
                "output": '"최종 통합해줘"',
                "final": '"적대적 리뷰 해줘"',
            }.get(stage, '"평가해줘"')
            actions.append(f"_(권장 명령 없음 — 모든 축 🟢/🟡. 다음 단계 권고: `{next_cmd}`)_")
        else:
            actions.append("_(권장 명령 없음 — axis 보고 확인 필요)_")

    return actions[:3]


def _render_research_section(items: list, kind: str = "search") -> list[str]:
    """미해결 R-NN/H-NN 또는 reanalyze 항목을 evaluation.md 섹션 본문으로 렌더."""
    out: list[str] = []
    if not items:
        return out
    if kind == "search":
        for h in items:
            out.append(f"### {h.get('id', '?')} — {h.get('topic', '(미명시)')}")
            covers = h.get("covers") or []
            if covers:
                out.append(f"- covers: {', '.join(covers)}")
            if h.get("query"):
                out.append(f"- 검색 쿼리: `{h['query']}`")
            if h.get("source_file"):
                out.append(f"- 출처: `{h['source_file']}`")
            out.append("")
    else:  # reanalyze
        for r in items:
            out.append(f"### {r.get('id') or r.get('paper', '?')} — {r.get('topic', '(미명시)')}")
            if r.get("target_pdf"):
                out.append(f"- 대상 PDF: `{r['target_pdf']}`")
            if r.get("angle"):
                out.append(f"- 재분석 각도: {r['angle']}")
            out.append("")
    return out


def _render_write_section(write_proposals: list, axis_data: dict) -> list[str]:
    """WRITE 권고를 axis 시급도 순으로 정렬해 자연어 권고로 렌더 (카드 ID 노출 금지)."""
    out: list[str] = []
    if not write_proposals:
        return out

    def axis_priority(p):
        ax = p.get("axis", "")
        m = re.match(r"axis\d+", ax)
        ax_key = m.group(0) if m else ""
        cat = axis_data.get(ax_key, {}).get("category", "adequate")
        return CATEGORY_PRIORITY.index(cat) if cat in CATEGORY_PRIORITY else 99

    for prop in sorted(write_proposals, key=axis_priority):
        ax = prop.get("axis", "?")
        m = re.match(r"axis(\d+)", ax)
        ax_n = m.group(1) if m else "?"
        cat = axis_data.get(f"axis{ax_n}", {}).get("category")
        cat_emoji = category_emoji(cat) if cat else ""
        target = prop.get("target") or "(대상 미명시)"
        what = prop.get("what") or "(내용 미명시)"
        mode = prop.get("mode", "modify")
        cause = prop.get("cause") or ax

        out.append(f"### {Path(target).name if target else '(대상 미명시)'} (axis {ax_n} {cat_emoji}) — {what}")
        out.append(f"- mode: {mode}")
        if mode == "modify":
            detail = prop.get("detail") or ""
            if detail:
                out.append(f"- 상세: {detail}")
        else:
            loc = prop.get("location") or ""
            if loc:
                out.append(f"- 위치: {loc}")
            req = prop.get("content_req") or ""
            if req:
                out.append(f"- 내용 요구: {req}")
        out.append(f"- 원인: {cause}")
        verb = "수정" if mode == "modify" else "작성"
        out.append(f'- → `"{Path(target).name} {verb}해줘: {what[:40]}"` 또는 직접 편집')
        out.append("")
    return out


def write_evaluation_md(
    project: str,
    stage: str,
    axis_data: dict,
    missing: list,
    ambition: str,
    critical_mode: bool,
    *,
    research_search_items: list | None = None,
    research_reanalyze_items: list | None = None,
    write_proposals: list | None = None,
):
    """evaluation.md 생성 (EVALUATION-FORMAT.md §2 스펙).

    work-plan.md 폐기로 다음 섹션이 evaluation.md로 통합됨:
      - 🧭 다음 액션 (사용자가 지금 할 것) — 1–3개
      - 📚 RESEARCH 항목 (미해결 R-NN/H-NN) — claim-extractor 산출물 그대로
      - ✏️ WRITE 권고 — axis*.md WRITE 후보 자연어로 (카드 ID 노출 금지)
    """
    research_search_items = research_search_items or []
    research_reanalyze_items = research_reanalyze_items or []
    write_proposals = write_proposals or []

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

    # frontmatter (EVALUATION-FORMAT.md §4)
    fm_lines = [
        "---",
        f"generated_at: {datetime.now().isoformat(timespec='seconds')}",
        "generated_by: evaluation_aggregator.py",
        f"stage: {stage}",
        "prev_eval: null",  # archive 추적은 선택 — 호출자가 관리
        f"intellectual_ambition: {ambition}",
        f"critical_mode: {'true' if critical_mode else 'false'}",
        "---",
        "",
    ]

    out = list(fm_lines)
    out.extend([
        f"# Evaluation — {project} ({stage})",
        "",
        f"> 📅 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> 단계: {stage}",
        f"> intellectual_ambition: {ambition}" + (" 🎭" if critical_mode else ""),
        f"> 파이프라인: {pipeline_desc}",
        "",
        "> 신뢰 가능 (메인): 카테고리·진단·Critical Issues·RESEARCH.  보조 (trend only): 점수.",
        "",
        "---",
        "",
        "## 🧭 다음 액션 (사용자가 지금 할 것)",
        "",
    ])
    next_actions = _build_next_actions(
        axis_data, research_search_items, research_reanalyze_items,
        write_proposals, stage,
    )
    for i, act in enumerate(next_actions, 1):
        out.append(f"{i}. {act}")
    out.extend([
        "",
        "---",
        "",
        "## 📊 축별 상태 요약",
        "",
        "| 축 | 이름 | 상태 | 이전 → 현재 | 핵심 진단 |",
        "|---|------|------|------|----------|",
    ])
    for axis, d in axis_data.items():
        n = axis[-1]
        cat = d.get("category")
        emoji = category_emoji(cat) if cat else "❔"
        label = category_label(cat) if cat else "(파싱 실패)"
        if d.get("prev") is not None and d.get("score") is not None:
            arrow = f"점수 {d['prev']}→{d['score']}"
        else:
            arrow = "(첫 평가)"
        diag_short = (d.get("diagnosis") or "—").split("\n")[0][:80]
        out.append(f"| {n} | {d['title']} | {emoji} {label} | {arrow} | {diag_short} |")
    out.extend([
        "",
        "> 상세는 axis{N}-*.md 참조",
        "",
        "---",
        "",
        "## 🎯 Verdict",
        "",
        f"### {verdict_emoji} **{verdict_label}**",
        "",
        f"**근거**: {verdict_reason}",
        "",
    ])

    # Final stage 한정 — holistic banner
    if stage == "final":
        holistic_path = lat / "holistic-review.md"
        if holistic_path.exists():
            holistic_status = f"✅ 함께 생성됨: [`holistic-review.md`]({holistic_path.name}) — 통합 관점 adjudication 결과 참조."
        else:
            holistic_status = "⏳ `holistic-review.md` 미생성 — orchestrator가 `final-holistic-reviewer` 를 dispatch해야 합니다."
        out.extend([
            "> 🛡 **Final stage 통합 평가 의무**",
            "> 위 6축 verdict는 *국소 진단*. 통합본은 사용자가 정합성을 선언한 상태이므로 *척추 보호 adjudication*이 별도 필요.",
            f"> {holistic_status}",
            "",
        ])

    # Sanity 위반 알림 (있으면)
    if issues:
        out.extend(["**⚠️ Sanity check**:"])
        for iss in issues:
            out.append(f"- {iss}")
        out.append("")

    # ⚠️ Critical Issues
    out.extend([
        "---",
        "",
        "## ⚠️ Critical Issues (🔴 구조적 결함)",
        "",
    ])
    crit_lines = []
    for axis, d in axis_data.items():
        if d.get("category") != "critical_gap":
            continue
        for ci in d.get("critical_issues", []):
            crit_lines.append(f"- **[축 {axis[-1]}]** {ci}")
    if crit_lines:
        out.extend(crit_lines)
    else:
        out.append("_(없음)_")

    # 🟠 보강 필요
    out.extend([
        "",
        "---",
        "",
        "## 🟠 보강 필요 (Needs Work)",
        "",
    ])
    needs_lines = []
    for axis, d in axis_data.items():
        if d.get("category") != "needs_work":
            continue
        n = axis[-1]
        diag = (d.get("diagnosis") or "").split("\n")[0]
        needs_lines.append(f"### 축 {n} — {d['title']} (🟠)")
        if diag:
            needs_lines.append(f"- 진단: {diag}")
        for ci in d.get("critical_issues", []):
            needs_lines.append(f"- {ci}")
        needs_lines.append("")
    if needs_lines:
        out.extend(needs_lines)
    else:
        out.append("_(없음)_")
        out.append("")

    # 📚 RESEARCH 항목
    out.extend([
        "---",
        "",
        "## 📚 RESEARCH 항목 (미해결)",
        "",
    ])
    if research_search_items:
        out.append('다음 R-NN/H-NN은 `"리서치 진행해줘"` 한 번으로 일괄 검색됩니다.')
        out.append("")
        out.extend(_render_research_section(research_search_items, kind="search"))
    if research_reanalyze_items:
        out.append("### 재분석 항목 (보유 PDF)")
        out.append("")
        out.extend(_render_research_section(research_reanalyze_items, kind="reanalyze"))
    if not research_search_items and not research_reanalyze_items:
        out.append("_(미해결 RESEARCH 없음)_")
        out.append("")

    # ✏️ WRITE 권고
    out.extend([
        "---",
        "",
        "## ✏️ WRITE 권고 (수정·작성 필요)",
        "",
    ])
    if write_proposals:
        out.extend(_render_write_section(write_proposals, axis_data))
    else:
        out.append("_(WRITE 후보 없음)_")
        out.append("")

    # 📂 축별 상세 리포트
    out.extend([
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
            f"⚠️ **누락된 축**: {', '.join(missing)} — 해당 scorer를 다시 실행하세요.",
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
# claim-extraction 파싱 (R-NN, search[] / reanalyze[])
# ──────────────────────────────────────────────────────────

# claim-extraction의 ```json ... ``` 요약 블록 추출 (nested [] 안전)
JSON_BLOCK_RE = re.compile(r"```json\s*\n(\{.*?\n\})\s*\n```", re.DOTALL)


# claim-extraction-{stage}.md 안의 R-NN 섹션 헤더 추출용
R_HEADER_RE = re.compile(r"^###\s+(R-\d+)\s*[—\-]?\s*(.*?)$", re.MULTILINE)


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


# ──────────────────────────────────────────────────────────
# WRITE 후보 파싱 — axis*.md의 "🛠 WRITE 후보" 섹션
# (카드 발급 폐기 — evaluation.md WRITE 권고 섹션 채우기에만 사용)
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


def _delta_reanalyze_items(affected: list) -> list:
    """paper_reanalysis_delta 결과를 reanalyze 항목 리스트로 정규화.

    affected: [{"paper": "Zelazo_2012", "primary_section": "hot/cool EF", "changed_section": "..."}]
    Returns: list of {paper, target_pdf, angle, topic}
    카드 발급은 폐기 (work-plan / card_registry 모두 사라짐). evaluation.md WRITE/RESEARCH
    권고 섹션에서 자연어로 노출됨.
    """
    items = []
    for entry in affected:
        paper = entry["paper"]
        items.append({
            "paper": paper,
            "target_pdf": f"papers/collected/{paper}.pdf",
            "angle": f"flow 변경 섹션 '{entry.get('changed_section', '')}' 반영 — "
                     f"{entry.get('primary_section', '')} 재스캔",
            "topic": f"{paper} delta 재분석 ({entry.get('primary_section', '')})",
        })
    if items:
        print(f"   🆕 delta reanalyze 항목 {len(items)}건 — evaluation.md '다음 액션'에서 노출")
    return items


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

    # flow가 bump됐고 action=reference면 paper_reanalysis_delta 자동 호출 → 영향 논문 list 산출
    delta_reanalyze_items = []
    if flow_was_bumped and action == "reference":
        affected = paper_reanalysis_delta.get_affected_papers(project)
        if affected:
            print(f"   📊 flow 변경 delta — 영향 논문 {len(affected)}건")
            delta_reanalyze_items = _delta_reanalyze_items(affected)

    lat = latest_dir(project, stage)
    if not lat.exists():
        print(f"⚠️  {lat} 없음 — axis scorer 결과 없음", file=sys.stderr)
        return 1

    # 0.7 파생 파일 frontmatter 자동 부여 (sync 보장)
    _apply_frontmatter_to_derivatives(project, stage)

    # 1. axis 파싱
    axis_data, missing, ambition, critical_mode = parse_axis_scores(project, stage)

    # 2. claim-extraction에서 미해결 RESEARCH 항목 (search[] + reanalyze[]) 추출
    ce_paths = claim_extraction_paths(project)
    research_search_items = extract_search_proposals_from_claim_extraction(ce_paths)
    research_reanalyze_items = extract_reanalyze_proposals_from_claim_extraction(ce_paths)
    # delta 기반 reanalyze 항목 합류
    research_reanalyze_items = research_reanalyze_items + delta_reanalyze_items

    # 3. axis*.md에서 WRITE 권고 추출 (action=content 또는 항상 — 사용자에게 노출)
    write_proposals = extract_write_proposals_from_axes(project, stage)

    # 4. evaluation.md 생성 (다음 액션 + RESEARCH + WRITE 권고 섹션 포함)
    total, prev_total = write_evaluation_md(
        project, stage, axis_data, missing, ambition, critical_mode,
        research_search_items=research_search_items,
        research_reanalyze_items=research_reanalyze_items,
        write_proposals=write_proposals,
    )

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
    if research_search_items:
        print(f"   📚 미해결 RESEARCH search 항목: {len(research_search_items)}건 → evaluation.md")
    if research_reanalyze_items:
        print(f"   🔄 reanalyze 항목: {len(research_reanalyze_items)}건 → evaluation.md")
    if write_proposals:
        print(f"   ✏️ WRITE 권고: {len(write_proposals)}건 → evaluation.md")

    # 5. Sanity check
    issues = validate_axis_consistency(project, axis_data)
    if issues:
        print("⚠️  Sanity check 위반:")
        for iss in issues:
            print(f"   {iss}")

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

    # 3. papers / RESEARCH 항목 (claim-extractor 산출물에서 추출)
    papers_root_dir = root / "papers"

    # candidates/ 는 stage별 분리 폴더 + legacy single 폴더 양쪽 지원
    cands_total = 0
    cands_by_stage: dict[str, int] = {}
    cdir_root = papers_root_dir / "candidates"
    if cdir_root.exists():
        # subfolder per stage (research-gap, flow)
        for sub in cdir_root.iterdir():
            if sub.is_dir():
                cnt = len(list(sub.glob("*.pdf")))
                if cnt:
                    cands_by_stage[sub.name] = cnt
                    cands_total += cnt
        # legacy: candidates/ 에 직접 PDF
        direct = list(cdir_root.glob("*.pdf"))
        if direct:
            cands_by_stage["(legacy)"] = len(direct)
            cands_total += len(direct)

    coll = list((papers_root_dir / "collected").glob("*.pdf")) if (papers_root_dir / "collected").exists() else []

    # search-results/{stage}.md (신규) 또는 consensus-results.md (legacy)
    sr_dir = papers_root_dir / "search-results"
    search_results_files = []
    if sr_dir.exists():
        search_results_files = sorted(sr_dir.glob("*.md"))
    legacy_consensus = papers_root_dir / "consensus-results.md"
    if legacy_consensus.exists():
        search_results_files.append(legacy_consensus)

    # claim-extraction-{stage}.md 에서 미해결 R-NN/H-NN 카운트
    research_search_total = 0
    research_reanalyze_total = 0
    for st in STAGES:
        ce = root / st / f"claim-extraction-{st}.md"
        if not ce.exists():
            continue
        try:
            search_items = extract_search_proposals_from_claim_extraction([ce])
            ra_items = extract_reanalyze_proposals_from_claim_extraction([ce])
            research_search_total += len(search_items)
            research_reanalyze_total += len(ra_items)
        except Exception:
            continue

    print(f"📚 Research")
    if research_search_total:
        print(f"   미해결 RESEARCH search 항목: {research_search_total}건 (claim-extraction)")
    if research_reanalyze_total:
        print(f"   미해결 reanalyze 항목: {research_reanalyze_total}건")
    for srf in search_results_files:
        try:
            text = srf.read_text(encoding="utf-8")
            n_papers = len(re.findall(r"^\#{2,3}\s+#\d+", text, re.MULTILINE))
            print(f"   {srf.relative_to(papers_root_dir)}: {n_papers}편 후보")
        except Exception:
            pass
    if cands_total:
        parts = ", ".join(f"{k}={v}" for k, v in cands_by_stage.items())
        print(f"   candidates/: {cands_total}편 대기 ({parts})")
    print(f"   collected/: {len(coll)}편 처리 완료")
    print()

    # 4. WRITE 권고 (axis*.md 🛠 WRITE 후보)
    write_total = 0
    for st in STAGES:
        try:
            wp = extract_write_proposals_from_axes(project, st)
            write_total += len(wp)
        except Exception:
            continue
    if write_total:
        print(f"✏️  Write")
        print(f"   WRITE 권고: {write_total}건 (axis*.md WRITE 후보 → evaluation.md 자연어로 노출)")
        print()

    # 5. 다음 권장 명령
    print(f"💡 권장 다음 명령:")
    recs = []
    if research_search_total > 0:
        recs.append(f'   • `"리서치 진행해줘"` — 미해결 search 항목 {research_search_total}건')
    if research_reanalyze_total > 0:
        recs.append(f'   • `"논문 재분석해줘"` — reanalyze 항목 {research_reanalyze_total}건')
    if cands_total > 0:
        recs.append(f'   • `"논문 처리해줘"` — candidates/ {cands_total}편 분석')
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
