#!/usr/bin/env python3
"""
version_manager.py — 문서 버전 + 싱크 체크.

각 시스템 산출물 파일 상단에 YAML frontmatter:

    ---
    version: 3
    content_hash: a3f8b9c
    based_on:
      flow: 3
      claim-extraction: 2
    updated_at: 2026-04-24T17:00:00
    updated_by: claim-extractor
    ---

    # 본문 시작...

핵심 원칙:
- content_hash는 frontmatter 제외 본문만의 SHA-256 short(8) hex.
- version은 content_hash가 바뀔 때만 increment. 단순 frontmatter 갱신은 영향 없음.
- 사용자 본문 파일 (flow.md, output/*.md)은 시스템이 매 명령 진입 시 hash 비교 → 다르면 자동 increment.
- 파생 파일은 작성자(claim-extractor·axis scorer 등)가 출력 시 update_version() 호출.
- check_sync(): 모든 파생 파일의 based_on.{X} == {X}.version 검증.

CLI:
    python3 scripts/version_manager.py check {project}        # 싱크 체크
    python3 scripts/version_manager.py bump {filepath}        # 사용자 편집 감지 → version++
    python3 scripts/version_manager.py info {filepath}        # frontmatter 조회
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FRONTMATTER_OPEN = "---\n"
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


# ──────────────────────────────────────────────────────────
# Project root detection + history path mapping
# ──────────────────────────────────────────────────────────

def find_project_root(filepath: Path) -> Path | None:
    """파일 경로에서 projects/{P}/ 형태의 프로젝트 root 추론."""
    fp = filepath.resolve()
    for p in fp.parents:
        if p.parent.name == "projects":
            return p
    return None


def categorize_for_history(filepath: Path, project_root: Path) -> tuple[str, str, str | None] | None:
    """파일 경로 → (stage, type, sub_id) for history/{stage}/{type}[/sub_id]/.

    Returns None if file is not subject to history snapshotting.
    """
    try:
        rel = filepath.resolve().relative_to(project_root.resolve())
    except ValueError:
        return None
    parts = rel.parts
    if not parts:
        return None

    if parts[0] == "flow":
        if rel.name == "flow.md":
            return ("flow", "body", None)
        if rel.name.startswith("claim-extraction"):
            return ("flow", "claim-extraction", None)
        if len(parts) >= 2 and parts[1] == "evaluations":
            return ("flow", "evaluations", None)
        if len(parts) >= 2 and parts[1] == "critical":
            return ("flow", "critical", None)
    if parts[0] == "output":
        if rel.name.startswith("claim-extraction"):
            return ("output", "claim-extraction", None)
        if len(parts) >= 2 and parts[1] == "evaluations":
            return ("output", "evaluations", None)
        if len(parts) >= 2 and parts[1] == "critical":
            return ("output", "critical", None)
        # output 본문 — 파일별 sub-folder
        if rel.name.endswith(".md"):
            return ("output", "body", rel.stem)
    return None


def _snapshot_before_bump(
    filepath: Path, prev_version: int, prev_text: str
) -> Path | None:
    """version++ 직전 이전 버전을 history에 백업.

    이전 파일 내용 그대로(frontmatter + body) 저장. NNN-{date}-v{prev_version}-pre-bump 폴더.
    output/body는 파일별 sub-folder (history/output/body/{file_id}/...).

    Returns: 백업 경로 또는 None (대상 아닐 때).
    """
    proj = find_project_root(filepath)
    if proj is None:
        return None
    cat = categorize_for_history(filepath, proj)
    if cat is None:
        return None
    stage, type_, sub_id = cat

    base = proj / "history" / stage / type_
    if sub_id:
        base = base / sub_id
    base.mkdir(parents=True, exist_ok=True)

    # 다음 NNN 결정
    existing = sorted(
        [p for p in base.iterdir() if p.is_dir() and p.name[:3].isdigit()],
        key=lambda p: int(p.name[:3]),
    )
    seq = (int(existing[-1].name[:3]) + 1) if existing else 1

    date_tag = datetime.now().strftime("%Y-%m-%d")
    folder_name = f"{seq:03d}-{date_tag}-v{prev_version}-pre-bump"
    dest_dir = base / folder_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filepath.name
    dest.write_text(prev_text, encoding="utf-8")
    return dest


# ──────────────────────────────────────────────────────────
# Frontmatter parse / render (단순 YAML — version_manager 자체 스펙)
# ──────────────────────────────────────────────────────────

def split_frontmatter(text: str) -> tuple[dict, str]:
    """text → (frontmatter dict, body). frontmatter 없으면 ({}, text).

    body는 leading \\n 제거 정규화 — hash·diff 일관성 보장.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text.lstrip("\n")
    fm_text = m.group(1)
    body = text[m.end():].lstrip("\n")
    return parse_frontmatter(fm_text), body


def parse_frontmatter(fm_text: str) -> dict:
    """단순 YAML 파서. key: value 또는 key:\\n  sub: val 지원."""
    data: dict = {}
    current_key = None
    for line in fm_text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("  ") and current_key:
            sub_m = re.match(r"^\s+([\w\-]+)\s*:\s*(.*)$", line)
            if sub_m:
                k, v = sub_m.group(1), sub_m.group(2).strip()
                if not isinstance(data.get(current_key), dict):
                    data[current_key] = {}
                data[current_key][k] = _parse_value(v)
            continue
        m = re.match(r"^([\w\-]+)\s*:\s*(.*)$", line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if v == "":
                # 다음 줄에 sub-keys
                data[k] = {}
                current_key = k
            else:
                data[k] = _parse_value(v)
                current_key = k
    return data


def _parse_value(v: str):
    if v == "":
        return None
    # 정수
    if re.match(r"^-?\d+$", v):
        return int(v)
    # 따옴표 문자열
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


def render_frontmatter(data: dict) -> str:
    """dict → YAML frontmatter 텍스트 (--- 포함). 키 순서: version, content_hash, based_on, updated_at, updated_by, 그 외."""
    out = ["---"]
    order = ["version", "content_hash", "based_on", "updated_at", "updated_by"]
    seen = set()
    for k in order:
        if k in data:
            _emit(out, k, data[k])
            seen.add(k)
    for k, v in data.items():
        if k not in seen:
            _emit(out, k, v)
    out.append("---")
    return "\n".join(out) + "\n"


def _emit(out: list, k: str, v):
    if isinstance(v, dict):
        out.append(f"{k}:")
        for sk, sv in v.items():
            out.append(f"  {sk}: {sv}")
    elif v is None:
        out.append(f"{k}:")
    else:
        out.append(f"{k}: {v}")


# ──────────────────────────────────────────────────────────
# Hash · version
# ──────────────────────────────────────────────────────────

def compute_content_hash(body: str) -> str:
    """frontmatter 제외 본문의 SHA-256 첫 8자 hex."""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]


def get_version_info(filepath: Path) -> dict:
    """파일의 frontmatter 정보 반환. 없으면 {}."""
    if not filepath.exists():
        return {}
    text = filepath.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    return {
        "filepath": str(filepath),
        "version": fm.get("version", 0),
        "content_hash": fm.get("content_hash", ""),
        "based_on": fm.get("based_on", {}) or {},
        "updated_at": fm.get("updated_at", ""),
        "updated_by": fm.get("updated_by", ""),
        "body_hash_now": compute_content_hash(body),
    }


def update_version(
    filepath: Path,
    based_on: dict | None = None,
    updated_by: str = "system",
    force: bool = False,
) -> dict:
    """파일 frontmatter 갱신. 본문 hash 변경 시 version++.

    - filepath 없으면 무시 ({} 반환).
    - based_on이 None이면 기존 frontmatter의 based_on 유지.
    - force=True면 hash 동일해도 version++ + frontmatter 갱신.

    Returns: 갱신 후 frontmatter 정보.
    """
    if not filepath.exists():
        return {}
    text = filepath.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)

    body_hash = compute_content_hash(body)
    prev_hash = fm.get("content_hash", "")
    prev_version = int(fm.get("version", 0) or 0)

    will_increment = force or body_hash != prev_hash

    # version++ 직전 이전 버전 자동 백업 (이전 v >= 1인 경우만 — 첫 v1 부여는 백업할 게 없음)
    snapshot_path = None
    if will_increment and prev_version > 0:
        snapshot_path = _snapshot_before_bump(filepath, prev_version, text)

    if will_increment:
        version = prev_version + 1
    else:
        version = prev_version if prev_version > 0 else 1

    new_fm = {
        "version": version,
        "content_hash": body_hash,
    }
    # based_on 처리: 명시 우선, 없으면 기존 유지
    bo = based_on if based_on is not None else fm.get("based_on", {}) or {}
    if bo:
        new_fm["based_on"] = bo
    new_fm["updated_at"] = datetime.now().isoformat(timespec="seconds")
    new_fm["updated_by"] = updated_by

    # 일관 포맷: frontmatter + 빈 줄 1개 + 본문 (body는 이미 lstrip된 상태)
    rendered = render_frontmatter(new_fm) + "\n" + body
    filepath.write_text(rendered, encoding="utf-8")

    return {
        "filepath": str(filepath),
        "version": version,
        "content_hash": body_hash,
        "based_on": bo,
        "updated_at": new_fm["updated_at"],
        "updated_by": updated_by,
        "incremented": will_increment,
        "snapshot_path": str(snapshot_path) if snapshot_path else None,
    }


def bump_if_changed(filepath: Path, updated_by: str = "user") -> dict:
    """사용자 본문 파일 (flow.md, output/*.md) 자동 increment.

    body hash 변경 시에만 version++. frontmatter 없으면 v1 신규 생성.
    """
    return update_version(filepath, based_on=None, updated_by=updated_by, force=False)


# ──────────────────────────────────────────────────────────
# Sync check
# ──────────────────────────────────────────────────────────

def project_files(project_root: Path) -> list[dict]:
    """프로젝트의 sync 검증 대상 파일 목록.

    각 항목: {filepath, role, expects (의존하는 다른 파일의 키)}
    """
    files = []
    flow_md = project_root / "flow" / "flow.md"
    flow_ce = project_root / "flow" / "claim-extraction-flow.md"
    output_dir = project_root / "output"
    output_ce = output_dir / "claim-extraction-output.md"

    flow_eval = project_root / "flow" / "evaluations"
    output_eval = output_dir / "evaluations"

    if flow_md.exists():
        files.append({"filepath": flow_md, "role": "flow:body", "expects": []})
    if flow_ce.exists():
        files.append({"filepath": flow_ce, "role": "flow:claim-extraction",
                      "expects": [("flow", flow_md)]})
    if flow_eval.exists():
        for p in sorted(flow_eval.glob("*.md")):
            files.append({"filepath": p, "role": f"flow:eval:{p.stem}",
                          "expects": [("flow", flow_md), ("claim-extraction", flow_ce)]})
    flow_critical = project_root / "flow" / "critical"
    if flow_critical.exists():
        for p in sorted(flow_critical.glob("*.md")):
            files.append({"filepath": p, "role": f"flow:critical:{p.stem}",
                          "expects": [("flow", flow_md)]})

    if output_dir.exists():
        for p in sorted(output_dir.glob("*.md")):
            if p.name.startswith("claim-extraction"):
                continue
            files.append({"filepath": p, "role": f"output:body:{p.stem}", "expects": []})
        if output_ce.exists():
            files.append({"filepath": output_ce, "role": "output:claim-extraction",
                          "expects": [("output", None)]})  # output 본문은 다중 — 별도 처리
        if output_eval.exists():
            for p in sorted(output_eval.glob("*.md")):
                files.append({"filepath": p, "role": f"output:eval:{p.stem}",
                              "expects": [("output", None), ("claim-extraction", output_ce)]})
        output_critical = output_dir / "critical"
        if output_critical.exists():
            for p in sorted(output_critical.glob("*.md")):
                files.append({"filepath": p, "role": f"output:critical:{p.stem}",
                              "expects": [("output", None)]})
    return files


def check_sync(project_root: Path) -> list[dict]:
    """모든 파일 sync 상태 검증. 각 항목: {role, version, based_on, expected, status, message}."""
    file_specs = project_files(project_root)
    # 1차 패스: 모든 파일 version 정보 수집
    info_by_role: dict[str, dict] = {}
    for spec in file_specs:
        info = get_version_info(spec["filepath"])
        info["role"] = spec["role"]
        info["expects"] = spec["expects"]
        info_by_role[spec["role"]] = info

    # 2차 패스: based_on vs expected 비교
    results = []
    for spec in file_specs:
        info = info_by_role[spec["role"]]
        based_on = info.get("based_on", {}) or {}
        version = info.get("version", 0)

        # frontmatter 자체가 없는 파일
        if version == 0:
            status = "not_versioned"
            msgs = []
        else:
            status = "synced"
            msgs = []

            for dep_key, dep_path in spec["expects"]:
                # output multi-body: output 본문 중 가장 큰 version과 비교
                if dep_key == "output" and dep_path is None:
                    output_versions = [
                        v["version"] for r, v in info_by_role.items()
                        if r.startswith("output:body:") and v["version"] > 0
                    ]
                    expected = max(output_versions) if output_versions else 0
                elif dep_path and dep_path.exists():
                    expected = info_by_role.get(_role_for_path(dep_path, info_by_role), {}).get("version", 0)
                else:
                    expected = 0

                actual = based_on.get(dep_key, 0) if isinstance(based_on, dict) else 0
                if expected > 0 and actual != expected:
                    status = "stale"
                    msgs.append(f"based_on.{dep_key}={actual} but {dep_key} v{expected}")

            # 본문 hash 변경 감지
            if info.get("content_hash", "") and info.get("body_hash_now", "") != info.get("content_hash", ""):
                status = "edited"
                msgs.append("본문 변경 감지 — version bump 필요")

        # 상대 경로 안전 변환
        try:
            rel_path = spec["filepath"].resolve().relative_to(project_root.resolve())
        except ValueError:
            rel_path = spec["filepath"]

        results.append({
            "role": spec["role"],
            "filepath": rel_path,
            "version": version,
            "based_on": based_on,
            "status": status,
            "messages": msgs,
        })
    return results


def _role_for_path(path: Path, info_by_role: dict) -> str:
    for role, info in info_by_role.items():
        if str(path) == info.get("filepath", "") or str(path) == info.get("filepath"):
            return role
    return ""


def render_sync_report(project_root: Path) -> str:
    """싱크 체크 결과를 사람이 읽기 좋은 표로 렌더."""
    results = check_sync(project_root)
    if not results:
        return "(검증 대상 파일 없음)\n"

    by_status = {"synced": [], "edited": [], "stale": [], "not_versioned": []}
    for r in results:
        by_status[r["status"]].append(r)

    lines = []
    if by_status["synced"]:
        lines.append("✅ Synced")
        for r in by_status["synced"]:
            bo = ", ".join(f"{k} v{v}" for k, v in (r["based_on"] or {}).items()) or "—"
            lines.append(f"   {str(r['filepath']):60} v{r['version']}  (based on {bo})")
        lines.append("")
    if by_status["edited"]:
        lines.append("📝 Edited — 본문 변경 감지 (다음 분석 명령 실행 시 자동 v++ → 파생 파일 모두 stale 처리됨)")
        for r in by_status["edited"]:
            lines.append(f"   {str(r['filepath']):60} v{r['version']}  ⚠️ {r['messages'][0]}")
        lines.append("")
    if by_status["stale"]:
        lines.append("⚠️ Stale (재실행 권장)")
        for r in by_status["stale"]:
            for m in r["messages"]:
                lines.append(f"   {str(r['filepath']):60} v{r['version']}  ⚠️ {m}")
        lines.append("")
    if by_status["not_versioned"]:
        lines.append("⏳ Not versioned (frontmatter 없음 — 첫 분석 명령 시 v1 부여 예정)")
        for r in by_status["not_versioned"]:
            lines.append(f"   {str(r['filepath']):60}")
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────

def _cli():
    if len(sys.argv) < 2:
        print("Usage: version_manager.py <check|bump|info> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "check":
        if len(sys.argv) < 3:
            print("Usage: version_manager.py check <project>")
            sys.exit(1)
        proj = ROOT / "projects" / sys.argv[2]
        if not proj.exists():
            print(f"❌ 프로젝트 없음: {proj}")
            sys.exit(1)
        print(render_sync_report(proj))
        return

    if cmd == "bump":
        if len(sys.argv) < 3:
            print("Usage: version_manager.py bump <filepath>")
            sys.exit(1)
        fp = Path(sys.argv[2])
        result = bump_if_changed(fp, updated_by="cli")
        if not result:
            print(f"⚠️  파일 없음: {fp}")
            sys.exit(1)
        if result.get("incremented"):
            msg = f"✅ {fp.name}: v{result['version']} (content_hash={result['content_hash']})"
            if result.get("snapshot_path"):
                snap = Path(result["snapshot_path"])
                proj = find_project_root(fp) or Path()
                try:
                    rel_snap = snap.resolve().relative_to(proj.resolve()) if proj.exists() else snap
                except ValueError:
                    rel_snap = snap
                msg += f"\n   💾 이전 버전 백업: {rel_snap}"
            print(msg)
        else:
            print(f"ℹ️  {fp.name}: v{result['version']} (변경 없음)")
        return

    if cmd == "info":
        if len(sys.argv) < 3:
            print("Usage: version_manager.py info <filepath>")
            sys.exit(1)
        fp = Path(sys.argv[2])
        info = get_version_info(fp)
        if not info:
            print(f"⚠️  파일 없음: {fp}")
            sys.exit(1)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    print(f"Unknown command: {cmd}")
    sys.exit(1)


if __name__ == "__main__":
    _cli()
