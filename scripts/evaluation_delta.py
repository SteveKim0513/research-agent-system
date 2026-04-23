#!/usr/bin/env python3
"""
evaluation_delta.py — 축별 변경 감지 엔진 (v2 stage-aware).

각 축은 평가 대상 stage에 따라 다른 입력에 의존한다:
  flow 단계 (아직 chapters/ 없음):
    axis1: flow/flow.md + flow/claim-extraction-flow.md + analyzed/*.md
    axis2: flow/flow.md
    axis3: flow/flow.md + analyzed:steelman
    axis4: flow/flow.md + analyzed:delta
    axis5: flow/flow.md
    axis6: flow/flow.md + critical-questions.md + critical-commitments.md + analyzed:minority

  draft 단계 (chapters/ 존재):
    axis1: chapters/*.md + chapters/claim-extraction-draft.md + analyzed/*.md
    axis2: chapters/*.md
    axis3: chapters/*.md + analyzed:steelman
    axis4: chapters/*.md + analyzed:delta
    axis5: chapters/*.md
    axis6: chapters/*.md + critical-questions.md + critical-commitments.md + analyzed:minority

이 스크립트는 입력 해시를 이전 평가 시점의 캐시와 비교해 재계산 필요한 축을 반환한다.

하위 명령:
  compute-inputs {project} [--stage=auto|flow|v1-draft|revised|final]
  check {project}           [--stage=...]
  mark-done {project} <axes_csv>  [--stage=...]
  reset {project}
"""
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime


AXES = ["axis1", "axis2", "axis3", "axis4", "axis5", "axis6"]

STAGE_FLOW = "flow"
STAGE_DRAFT_STAGES = {"v1-draft", "revised", "final"}

# Stage별 축 의존성
AXIS_DEPENDENCIES = {
    STAGE_FLOW: {
        "axis1": ["flow/flow.md", "flow/claim-extraction-flow.md", "analyzed:*"],
        "axis2": ["flow/flow.md"],
        "axis3": ["flow/flow.md", "analyzed:steelman"],
        "axis4": ["flow/flow.md", "analyzed:delta"],
        "axis5": ["flow/flow.md"],
        "axis6": ["flow/flow.md", "critical-questions.md", "critical-commitments.md", "analyzed:minority"],
    },
    # draft 단계는 v1-draft/revised/final 모두 동일 구조
    "draft": {
        "axis1": ["chapters/*.md", "chapters/claim-extraction-draft.md", "analyzed:*"],
        "axis2": ["chapters/*.md"],
        "axis3": ["chapters/*.md", "analyzed:steelman"],
        "axis4": ["chapters/*.md", "analyzed:delta"],
        "axis5": ["chapters/*.md"],
        "axis6": ["chapters/*.md", "critical-questions.md", "critical-commitments.md", "analyzed:minority"],
    },
}


# ─────────────────────── 경로/유틸 ───────────────────────

def project_root(project: str) -> Path:
    return Path("projects") / project


def sha256_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def chapter_files(proj: Path) -> list:
    """chapters/의 실제 챕터 (claim-extraction-draft.md 제외)."""
    chap_dir = proj / "chapters"
    if not chap_dir.exists():
        return []
    return sorted([
        p for p in chap_dir.glob("*.md")
        if p.is_file() and p.name != "claim-extraction-draft.md"
    ])


def detect_stage(proj: Path) -> str:
    """프로젝트 현재 stage 자동 감지.

    chapters/에 실제 챕터 파일이 있으면 draft, 없으면 flow.
    세부 구분(v1-draft/revised/final)은 현재 단순화 위해 draft로 통합.
    """
    return "v1-draft" if chapter_files(proj) else STAGE_FLOW


def stage_key(stage: str) -> str:
    """stage 이름을 AXIS_DEPENDENCIES의 키로 매핑."""
    return STAGE_FLOW if stage == STAGE_FLOW else "draft"


# ─────────────────────── 태그 추출 ───────────────────────

def extract_axis_tags(analyzed_file: Path) -> set:
    if not analyzed_file.exists():
        return set()
    try:
        content = analyzed_file.read_text(encoding="utf-8")
    except Exception:
        return set()

    import re
    m = re.search(r"axis_tags\s*:\s*\[([^\]]+)\]", content)
    if not m:
        return set()
    raw = m.group(1)
    tags = set()
    for t in re.findall(r"['\"]([a-z_]+)['\"]", raw):
        tags.add(t)
    return tags


def collect_analyzed_by_tag(proj: Path) -> dict:
    analyzed_dir = proj / "papers" / "analyzed"
    result = {"*": []}
    if not analyzed_dir.exists():
        return result
    for md in sorted(analyzed_dir.glob("*.md")):
        result["*"].append(md)
        for tag in extract_axis_tags(md):
            result.setdefault(tag, []).append(md)
    return result


# ─────────────────────── 입력 해시 계산 ───────────────────────

def compute_axis_input_hash(project: str, axis: str, stage: str) -> str:
    proj = project_root(project)
    deps = AXIS_DEPENDENCIES[stage_key(stage)][axis]
    parts = []
    analyzed_map = None

    for dep in deps:
        if dep.startswith("analyzed:"):
            tag = dep.split(":", 1)[1]
            if analyzed_map is None:
                analyzed_map = collect_analyzed_by_tag(proj)
            files = analyzed_map.get(tag, [])
            for f in sorted(files):
                parts.append(f"{f.name}:{sha256_file(f)}")
            parts.append(f"analyzed:{tag}:count={len(files)}")
        elif dep == "chapters/*.md":
            chaps = chapter_files(proj)
            for f in chaps:
                parts.append(f"chapter:{f.name}:{sha256_file(f)}")
            parts.append(f"chapters:count={len(chaps)}")
        elif dep == "chapters/claim-extraction-draft.md":
            f = proj / "chapters" / "claim-extraction-draft.md"
            parts.append(f"{dep}:{sha256_file(f)}")
        elif dep == "flow/flow.md":
            f = proj / "flow" / "flow.md"
            parts.append(f"{dep}:{sha256_file(f)}")
        elif dep == "flow/claim-extraction-flow.md":
            f = proj / "flow" / "claim-extraction-flow.md"
            parts.append(f"{dep}:{sha256_file(f)}")
        elif dep in ("critical-questions.md", "critical-commitments.md"):
            f = proj / dep
            parts.append(f"{dep}:{sha256_file(f)}")
        else:
            parts.append(f"{dep}:unknown")

    combined = "||".join(parts)
    return sha256_str(combined)


# ─────────────────────── 캐시 ───────────────────────

def cache_path(project: str) -> Path:
    return project_root(project) / "evaluations" / "latest" / ".eval-cache.json"


def load_cache(project: str) -> dict:
    p = cache_path(project)
    if not p.exists():
        return {"axes": {}, "last_updated": None}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"axes": {}, "last_updated": None}


def save_cache(project: str, cache: dict) -> None:
    p = cache_path(project)
    p.parent.mkdir(parents=True, exist_ok=True)
    cache["last_updated"] = datetime.now().isoformat()
    p.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


# ─────────────────────── 커맨드 ───────────────────────

def resolve_stage(project: str, stage_arg: str) -> str:
    if stage_arg and stage_arg != "auto":
        return stage_arg
    return detect_stage(project_root(project))


def cmd_compute_inputs(project: str, stage: str) -> int:
    stage = resolve_stage(project, stage)
    result = {
        "project": project,
        "stage": stage,
        "hashes": {axis: compute_axis_input_hash(project, axis, stage) for axis in AXES},
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_check(project: str, stage: str) -> int:
    stage = resolve_stage(project, stage)
    cache = load_cache(project)
    stale = []
    fresh = []
    reasons = {}
    for axis in AXES:
        current = compute_axis_input_hash(project, axis, stage)
        cached_entry = cache.get("axes", {}).get(axis, {})
        cached_hash = cached_entry.get("input_hash")
        cached_stage = cached_entry.get("stage")

        if cached_stage and cached_stage != stage:
            stale.append(axis)
            reasons[axis] = f"stage changed ({cached_stage} → {stage})"
        elif cached_hash != current:
            stale.append(axis)
            reasons[axis] = (
                f"input hash changed (cached={cached_hash}, current={current})"
                if cached_hash else "no cached score"
            )
        else:
            fresh.append(axis)

    result = {
        "project": project,
        "stage": stage,
        "stale_axes": stale,
        "fresh_axes": fresh,
        "reason": reasons,
        "checked_at": datetime.now().isoformat(),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_mark_done(project: str, axes_csv: str, stage: str) -> int:
    stage = resolve_stage(project, stage)
    cache = load_cache(project)
    cache.setdefault("axes", {})
    for axis in axes_csv.split(","):
        axis = axis.strip()
        if axis not in AXES:
            print(f"⚠️ 알 수 없는 축: {axis}", file=sys.stderr)
            continue
        cache["axes"][axis] = {
            "input_hash": compute_axis_input_hash(project, axis, stage),
            "stage": stage,
            "scored_at": datetime.now().isoformat(),
        }
    save_cache(project, cache)
    print(f"✅ mark-done ({stage}): {axes_csv}")
    return 0


def cmd_reset(project: str) -> int:
    cache = {"axes": {}, "last_updated": datetime.now().isoformat()}
    save_cache(project, cache)
    print("✅ cache reset (전체 재계산 예정)")
    return 0


# ─────────────────────── 엔트리 ───────────────────────

def parse_stage_arg(args: list) -> tuple:
    """--stage=X 플래그를 추출 후 (plain_args, stage) 반환."""
    plain = []
    stage = "auto"
    for a in args:
        if a.startswith("--stage="):
            stage = a.split("=", 1)[1]
        else:
            plain.append(a)
    return plain, stage


def main(argv: list) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    args, stage = parse_stage_arg(argv[2:])
    try:
        if cmd == "compute-inputs" and len(args) == 1:
            return cmd_compute_inputs(args[0], stage)
        if cmd == "check" and len(args) == 1:
            return cmd_check(args[0], stage)
        if cmd == "mark-done" and len(args) == 2:
            return cmd_mark_done(args[0], args[1], stage)
        if cmd == "reset" and len(args) == 1:
            return cmd_reset(args[0])
    except Exception as e:
        print(f"⚠️ evaluation_delta 오류: {e}", file=sys.stderr)
        return 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
