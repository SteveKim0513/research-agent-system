#!/usr/bin/env python3
"""
evaluation_delta.py — 축별 변경 감지 엔진.

**핵심 아이디어**: 각 축(axis)은 특정 입력에 의존한다.
- Axis 1: flow.md + analyzed/*.md + claim-extraction.md
- Axis 2: flow.md only
- Axis 3: flow.md + analyzed/*.md#steelman tag
- Axis 4: flow.md + analyzed/*.md#delta tag
- Axis 5: flow.md only
- Axis 6: flow.md + critical-questions.md + critical-commitments.md + analyzed/*.md#minority

이 스크립트는 입력 해시를 이전 평가 시점(.eval-cache.json)과 비교해
**재계산 필요한 축 목록**을 반환한다.

하위 명령:
- compute-inputs {project} → 각 축의 현재 입력 해시 계산 → stdout (JSON)
- check {project} → 변경된 축 목록 반환 → stdout (JSON)
- mark-done {project} {axis1,axis2,...} → 해당 축 캐시 해시 갱신
- reset {project} → 캐시 초기화 (전체 재계산 강제)
"""
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime


# ─────────────────────── 경로/유틸 ───────────────────────

AXES = ["axis1", "axis2", "axis3", "axis4", "axis5", "axis6"]

# 각 축이 의존하는 입력 유형
AXIS_DEPENDENCIES = {
    "axis1": ["flow.md", "analyzed:*", "claim-extraction.md"],
    "axis2": ["flow.md"],
    "axis3": ["flow.md", "analyzed:steelman"],
    "axis4": ["flow.md", "analyzed:delta"],
    "axis5": ["flow.md"],
    "axis6": ["flow.md", "critical-questions.md", "critical-commitments.md", "analyzed:minority"],
}


def project_root(project: str) -> Path:
    # 현재 working directory가 research-agent/ 라고 가정
    return Path("projects") / project


def repo_root() -> Path:
    # research-agent/ 루트
    return Path.cwd()


def sha256_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


# ─────────────────────── 태그 추출 ───────────────────────

def extract_axis_tags(analyzed_file: Path) -> set[str]:
    """analyzed/*.md의 frontmatter 또는 '## 메타' 섹션에서 axis_tags 읽기.

    지원 형식:
    1. frontmatter: axis_tags: ["steelman", "delta"]
    2. md 섹션:    - **axis_tags**: ["steelman", "delta"]
    """
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


def collect_analyzed_by_tag(proj: Path) -> dict[str, list[Path]]:
    """analyzed/*.md를 태그별로 그룹핑. '*' 키는 전체."""
    analyzed_dir = proj / "papers" / "analyzed"
    result: dict[str, list[Path]] = {"*": []}
    if not analyzed_dir.exists():
        return result
    for md in sorted(analyzed_dir.glob("*.md")):
        result["*"].append(md)
        for tag in extract_axis_tags(md):
            result.setdefault(tag, []).append(md)
    return result


# ─────────────────────── 입력 해시 계산 ───────────────────────

def compute_axis_input_hash(project: str, axis: str) -> str:
    """축별 입력 파일 집합의 combined hash."""
    proj = project_root(project)
    deps = AXIS_DEPENDENCIES[axis]
    parts = []

    analyzed_map = None  # lazy
    for dep in deps:
        if dep.startswith("analyzed:"):
            tag = dep.split(":", 1)[1]
            if analyzed_map is None:
                analyzed_map = collect_analyzed_by_tag(proj)
            files = analyzed_map.get(tag, [])
            # 파일 해시를 정렬 후 연결
            for f in sorted(files):
                parts.append(f"{f.name}:{sha256_file(f)}")
            # 파일 수도 해시에 포함 (삭제 감지)
            parts.append(f"analyzed:{tag}:count={len(files)}")
        elif dep == "claim-extraction.md":
            f = proj / "evaluations" / "latest" / "claim-extraction.md"
            parts.append(f"{dep}:{sha256_file(f)}")
        elif dep in ("critical-questions.md", "critical-commitments.md"):
            f = proj / dep
            parts.append(f"{dep}:{sha256_file(f)}")
        elif dep == "flow.md":
            f = proj / "flow.md"
            parts.append(f"{dep}:{sha256_file(f)}")
        else:
            parts.append(f"{dep}:unknown")

    combined = "||".join(parts)
    return sha256_str(combined)


# ─────────────────────── 캐시 관리 ───────────────────────

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

def cmd_compute_inputs(project: str) -> int:
    result = {axis: compute_axis_input_hash(project, axis) for axis in AXES}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_check(project: str) -> int:
    """
    변경된 축 목록을 JSON으로 반환.
    출력:
    {
      "stale_axes": ["axis2", "axis3"],
      "fresh_axes": ["axis1", "axis5"],
      "reason": {
        "axis2": "flow.md hash changed",
        ...
      }
    }
    """
    cache = load_cache(project)
    stale = []
    fresh = []
    reasons = {}
    for axis in AXES:
        current = compute_axis_input_hash(project, axis)
        cached_entry = cache.get("axes", {}).get(axis, {})
        cached_hash = cached_entry.get("input_hash")
        if cached_hash != current:
            stale.append(axis)
            reasons[axis] = (
                f"input hash changed (cached={cached_hash}, current={current})"
                if cached_hash else "no cached score"
            )
        else:
            fresh.append(axis)
    result = {
        "stale_axes": stale,
        "fresh_axes": fresh,
        "reason": reasons,
        "project": project,
        "checked_at": datetime.now().isoformat(),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_mark_done(project: str, axes_csv: str) -> int:
    """해당 축의 cache entry를 현재 해시로 갱신 (평가 완료 후 호출)."""
    cache = load_cache(project)
    cache.setdefault("axes", {})
    for axis in axes_csv.split(","):
        axis = axis.strip()
        if axis not in AXES:
            print(f"⚠️ 알 수 없는 축: {axis}", file=sys.stderr)
            continue
        cache["axes"][axis] = {
            "input_hash": compute_axis_input_hash(project, axis),
            "scored_at": datetime.now().isoformat(),
        }
    save_cache(project, cache)
    print(f"✅ mark-done: {axes_csv}")
    return 0


def cmd_reset(project: str) -> int:
    """캐시 초기화. 다음 평가는 전체 재계산."""
    cache = {"axes": {}, "last_updated": datetime.now().isoformat()}
    save_cache(project, cache)
    print("✅ cache reset (전체 재계산 예정)")
    return 0


# ─────────────────────── 엔트리 ───────────────────────

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    args = argv[2:]
    try:
        if cmd == "compute-inputs" and len(args) == 1:
            return cmd_compute_inputs(args[0])
        if cmd == "check" and len(args) == 1:
            return cmd_check(args[0])
        if cmd == "mark-done" and len(args) == 2:
            return cmd_mark_done(args[0], args[1])
        if cmd == "reset" and len(args) == 1:
            return cmd_reset(args[0])
    except Exception as e:
        print(f"⚠️ evaluation_delta 오류: {e}", file=sys.stderr)
        return 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
