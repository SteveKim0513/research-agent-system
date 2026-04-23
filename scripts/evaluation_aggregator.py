#!/usr/bin/env python3
"""
evaluation_aggregator.py — 축별 워커 결과를 합쳐 evaluation.md 생성.

입력: evaluations/latest/axis{1..6}-*.md
출력: evaluations/latest/evaluation.md (요약 + delta 표 + 종합 판정)

아카이브 사용:
- evaluations/archive/{최신}/axis{N}-*.md → 이전 점수 (delta 계산)
"""
import json
import re
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


def project_root(project: str) -> Path:
    return Path("projects") / project


def latest_dir(project: str) -> Path:
    return project_root(project) / "evaluations" / "latest"


def extract_score(md_path: Path) -> dict | None:
    """axis{N}-*.md에서 점수 블록 파싱. 없으면 None."""
    if not md_path.exists():
        return None
    content = md_path.read_text(encoding="utf-8")

    # Look for: **점수**: NN/100 or **점수**: NN
    score_m = re.search(r"\*\*점수\*\*\s*:\s*(\d+)\s*/\s*100", content)
    prev_m = re.search(r"\*\*이전\*\*\s*:\s*(\d+)\s*/\s*100", content)
    delta_m = re.search(r"\(([+-]\s*\d+)\)", content[:500])  # 이전 옆 delta

    # 하위 기준 점수
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


def read_metadata(project: str) -> dict:
    p = project_root(project) / ".paper-metadata.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def aggregate(project: str) -> int:
    lat = latest_dir(project)
    if not lat.exists():
        print(f"⚠️  {lat} 없음", file=sys.stderr)
        return 1

    meta = read_metadata(project)
    ambition = meta.get("intellectual_ambition", "baseline")
    critical_mode = ambition in ("critical", "paradigm-shifting")

    # 축별 점수 수집
    axis_data = {}
    missing = []
    for axis, (fname, title) in AXIS_FILES.items():
        if axis == "axis6" and not critical_mode:
            continue  # 축 6은 Critical Mode일 때만
        data = extract_score(lat / fname)
        if data is None:
            missing.append(axis)
            continue
        axis_data[axis] = {"title": title, **data}

    if missing:
        print(f"⚠️  누락된 축: {missing} — evaluation.md 생성 계속하나 표시")

    # 총점
    total = sum(d["score"] for d in axis_data.values())
    n_axes = len(axis_data)
    max_total = n_axes * 100
    avg = total / n_axes if n_axes else 0

    # 이전 총점 (delta)
    prev_total = None
    if all(d.get("prev") is not None for d in axis_data.values()):
        prev_total = sum(d["prev"] for d in axis_data.values())

    # 심사 판정
    if avg >= 85:
        judgment = "🟢 **Accept** (minor revisions)"
    elif avg >= 70:
        judgment = "🟡 **Revise & Resubmit**"
    elif avg >= 55:
        judgment = "🟠 **Major Revision**"
    else:
        judgment = "🔴 **Reject** (structural problems)"

    # evaluation.md 생성
    out = [
        f"# {n_axes}축 평가 리포트 — {project}",
        "",
        f"**대상**: `projects/{project}/flow.md`",
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
    for axis, (fname, title) in AXIS_FILES.items():
        if axis not in axis_data:
            continue
        out.append(f"- [{title}]({fname})")
    out.extend([
        "",
        "---",
        "",
        "## 🎯 잔여 우선순위 (축별 상세는 각 파일 참조)",
        "",
    ])

    # 감점이 큰 축 순으로 정렬
    sorted_axes = sorted(axis_data.items(), key=lambda x: x[1]["score"])
    for axis, d in sorted_axes[:3]:
        out.append(f"- **축 {axis[-1]} ({d['title']})** — {d['score']}/100. 상세: `{AXIS_FILES[axis][0]}`")
    out.append("")

    # 생성 메타
    out.extend([
        "---",
        "",
        f"*생성: evaluation_aggregator.py at {datetime.now().isoformat()}*",
    ])

    eval_md = lat / "evaluation.md"
    eval_md.write_text("\n".join(out), encoding="utf-8")

    print(f"✅ evaluation.md 생성 완료 ({n_axes}축, 총점 {total}/{max_total})")
    if prev_total is not None:
        print(f"   Delta: {total - prev_total:+d}")
    if missing:
        print(f"⚠️  누락 축: {missing} — 재실행 권장")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python3 evaluation_aggregator.py <project_name>")
        return 1
    return aggregate(argv[1])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
