#!/usr/bin/env python3
"""
evaluation_delta.py — 축별 변경 감지 엔진 (v3, stage 명시 강제).

각 축은 평가 대상 stage에 따라 다른 입력에 의존한다:
  flow 단계:
    axis1: flow/flow.md + flow/claim-extraction-flow.md + analyzed/*.md
    axis2: flow/flow.md
    axis3: flow/flow.md + analyzed:steelman
    axis4: flow/flow.md + analyzed:delta
    axis5: flow/flow.md
    axis6: flow/flow.md + critical-questions.md + critical-commitments.md + analyzed:minority

  output 단계 (output/*.md 챕터들):
    axis1: output/*.md + output/claim-extraction-output.md + analyzed/*.md
    axis2: output/*.md
    axis3: output/*.md + analyzed:steelman
    axis4: output/*.md + analyzed:delta
    axis5: output/*.md
    axis6: output/*.md + critical-questions.md + critical-commitments.md + analyzed:minority

  final 단계 (final/*.md 통합본):
    axis1: final/*.md + final/claim-extraction-final.md + analyzed/*.md
    axis2~5: final/*.md (+ steelman/delta tag)
    axis6: final/*.md + critical-questions.md + critical-commitments.md + analyzed:minority

이 스크립트는 입력 해시를 이전 평가 시점의 캐시와 비교해 재계산 필요한 축을 반환한다.

stage는 사용자가 명시 prefix로 지정 (자동 감지 폐기).

하위 명령:
  compute-inputs {project} --stage=flow|output|final
  check {project}           --stage=...
  mark-done {project} <axes_csv>  --stage=...
  reset {project}
"""
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime


AXES = ["axis1", "axis2", "axis3", "axis4", "axis5", "axis6"]

STAGES = ("flow", "output", "final")

# Stage별 축 의존성
AXIS_DEPENDENCIES = {
    "flow": {
        "axis1": ["flow/flow.md", "flow/claim-extraction-flow.md", "analyzed:*"],
        "axis2": ["flow/flow.md"],
        "axis3": ["flow/flow.md", "analyzed:steelman"],
        "axis4": ["flow/flow.md", "analyzed:delta"],
        "axis5": ["flow/flow.md"],
        "axis6": ["flow/flow.md", "critical-questions.md", "critical-commitments.md", "analyzed:minority"],
    },
    "output": {
        "axis1": ["output/*.md", "output/claim-extraction-output.md", "analyzed:*"],
        "axis2": ["output/*.md"],
        "axis3": ["output/*.md", "analyzed:steelman"],
        "axis4": ["output/*.md", "analyzed:delta"],
        "axis5": ["output/*.md"],
        "axis6": ["output/*.md", "critical-questions.md", "critical-commitments.md", "analyzed:minority"],
    },
    "final": {
        "axis1": ["final/*.md", "final/claim-extraction-final.md", "analyzed:*"],
        "axis2": ["final/*.md"],
        "axis3": ["final/*.md", "analyzed:steelman"],
        "axis4": ["final/*.md", "analyzed:delta"],
        "axis5": ["final/*.md"],
        "axis6": ["final/*.md", "critical-questions.md", "critical-commitments.md", "analyzed:minority"],
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


def stage_files(proj: Path, stage: str) -> list:
    """stage 폴더의 본문 *.md (claim-extraction-* 제외)."""
    st_dir = proj / stage
    if not st_dir.exists():
        return []
    return sorted([
        p for p in st_dir.glob("*.md")
        if p.is_file() and not p.name.startswith("claim-extraction")
    ])


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
    deps = AXIS_DEPENDENCIES[stage][axis]
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
        elif dep.endswith("/*.md"):
            # stage 본문 (output/*.md or final/*.md)
            st = dep.split("/", 1)[0]
            files = stage_files(proj, st)
            for f in files:
                parts.append(f"{st}:{f.name}:{sha256_file(f)}")
            parts.append(f"{st}:count={len(files)}")
        elif "/claim-extraction-" in dep:
            # flow/claim-extraction-flow.md, output/claim-extraction-output.md, final/claim-extraction-final.md
            f = proj / dep
            parts.append(f"{dep}:{sha256_file(f)}")
        elif dep == "flow/flow.md":
            f = proj / "flow" / "flow.md"
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
    """캐시 파일 위치 — 프로젝트 루트에 단일 파일.

    Stage가 다른 (flow/output/final) 평가들 모두 같은 캐시에 저장하되
    엔트리 안에 stage 필드를 함께 보관.
    """
    return project_root(project) / ".eval-cache.json"


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
    """stage 명시 강제. 자동 감지 폐기."""
    if not stage_arg or stage_arg == "auto":
        raise ValueError(
            f"stage 필수 (--stage=flow|output|final). "
            f"v3에서 자동 감지 폐기 — 사용자 명시 prefix만 인식."
        )
    if stage_arg not in STAGES:
        raise ValueError(f"stage는 {STAGES} 중 하나여야 함, got {stage_arg!r}")
    return stage_arg


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
    """--stage=X 플래그를 추출 후 (plain_args, stage) 반환. stage 미지정 시 None."""
    plain = []
    stage = None
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
