#!/usr/bin/env python3
"""
activity_log.py — Research Agent 사용자 활동 로그 시스템.

Claude Code hooks를 통해 자동 기록되며, 기록이 누락되어도 SKILL.md
의 MD 지시(Layer 4)가 fallback으로 작동.

주요 기능:
- append: 수동 또는 MD fallback용 로그 한 줄 쓰기
- on-prompt-submit: UserPromptSubmit hook 진입점 (명령 감지)
- on-turn-end: Stop hook 진입점 (turn 결과 정리)
- on-bash-event: PostToolUse(Bash) hook 진입점 (핵심 스크립트 추적)
- parse: 한 줄 파싱 → 구조화된 딕셔너리 (time-travel 용)
- recent: 최근 N일치 엔트리 반환
- recommend: 로그 기반 작업 추천 엔진

로그 파일: projects/{project}/activity.log (가시 파일)
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


# 로그 엔트리 포맷: 파이프 + key=value 하이브리드
# [YYYY-MM-DD HH:MM:SS] ACTION | STAGE | TARGET | RESULT | ref:ID | agents:A,B | key=value
# Stop hook 자동 추가 필드: duration=Ns tokens_in=N tokens_out=N cache_read=N cache_creation=N key=value

LOG_FORMAT = "[{timestamp}] {action} | {stage} | {target} | {result} | {ref} | {agents} | {meta}"

# Claude Code 기반 명령 패턴 (Korean + English)
COMMAND_PATTERNS = [
    # (pattern, action_label, stage_hint)
    (r"(평가해줘|5축\s*평가|점수\s*매겨줘|원고\s*평가해줘|flow\s*평가해줘)", "평가 요청", None),
    (r"(레퍼런스\s*점검해줘|축\s*1\s*재평가|reference\s*check)", "레퍼런스 점검 요청", "post-research"),
    (r"(flow\s*업데이트해줘|flow\s*보강|새\s*논문\s*반영해서\s*flow)", "flow 업데이트 요청", "post-research"),
    (r"(작업\s*시작해줘|논문\s*검색해줘|HUNT\s*실행|필요한\s*논문\s*찾아줘)", "리서치 실행 요청", "stage1"),
    (r"(새\s*논문\s*처리해줘|논문\s*처리해줘|candidates\s*처리해줘|논문\s*분석해줘)", "논문 처리 요청", "stage1"),
    (r"논문\s*재분석해줘", "논문 재분석 요청", None),
    (r"논문\s*제거해줘", "논문 제거 요청", None),
    (r"(초안\s*작성해줘|draft\s*생성|글\s*써줘)", "초안 작성 요청", "v1-draft"),
    (r"Chapter\s*\d+\s*수정해줘|\d+장\s*수정", "챕터 수정 요청", "revised"),
    (r"(최종\s*통합해줘|final\s*재빌드|docx\s*재생성|chapter\s*합쳐줘)", "최종 통합 요청", "final"),
    (r"(리뷰\s*체크해줘|심사\s*시뮬|제출\s*전\s*체크)", "리뷰 시뮬 요청", "final"),
    (r"(리뷰\s*답변\s*도와줘|리뷰\s*분석)", "리뷰 대응 요청", "final"),
    (r"(질문\s*업데이트해줘|비판적\s*질문\s*생성해줘|critical\s*questions)", "질문 업데이트 요청", None),
    (r"(답변\s*반영해줘|commitments?\s*추출해줘)", "답변 반영 요청", None),
    (r"(비판\s*모드\s*설정해줘|intellectual_ambition\s*설정해줘|비판\s*모드\s*(critical|incremental|paradigm))", "비판 모드 설정 요청", None),
    (r"(sync\s*확인해줘|sync\s*점검|상태\s*확인해줘|stale\s*체크)", "sync 점검 요청", None),
    (r"(gap\s*분석해줘|연구\s*gap\s*찾아줘|뭐가\s*안\s*다뤄졌어)", "gap 분석 요청", None),
    (r"(방법론\s*추천해줘|방법론\s*검증해줘|어떻게\s*접근해야)", "방법론 요청", None),
    (r"(독창성\s*평가해줘|contribution\s*평가|novelty\s*확인해줘)", "축 4 심층 요청", None),
    (r"(정의\s*정밀도\s*평가해줘|개념\s*평가|construct\s*clarity)", "축 5 심층 요청", None),
    (r"(비판적\s*시각\s*평가해줘|critical\s*lens|paradigm\s*평가)", "축 6 심층 요청", None),
    (r"비판적으로\s*분석해줘", "논문 Mode C 요청", None),
    (r"(작업\s*추천해줘|뭘\s*해야\s*해|next\s*step|추천해줘)", "작업 추천 요청", None),
    (r"프로젝트\s*만들어줘", "프로젝트 생성 요청", "init"),
]

REF_PATTERN = re.compile(r"ref:([a-z\-]+)-(\d{3})")


# ─────────────────────────── Core I/O ───────────────────────────


def get_repo_root() -> Path:
    """research-agent 루트 디렉토리 반환."""
    # 이 스크립트는 {repo}/scripts/activity_log.py
    return Path(__file__).resolve().parent.parent


def detect_project(cwd: Path | None = None, hint_text: str = "") -> str | None:
    """활성 프로젝트 감지.

    우선순위:
    1. hint_text에 "projects/X" 언급이 있으면 X
    2. hint_text에 프로젝트 이름 직접 언급 (예: "CDEA")
    3. projects/ 내 가장 최근 수정된 폴더
    4. 없으면 None
    """
    repo = get_repo_root()
    projects_dir = repo / "projects"
    if not projects_dir.exists():
        return None

    # 1. hint_text에서 projects/X 패턴 추출
    m = re.search(r"projects/([A-Za-z0-9_\-]+)", hint_text)
    if m and (projects_dir / m.group(1)).exists():
        return m.group(1)

    # 2. hint_text에서 알려진 프로젝트 이름 매칭
    for p in projects_dir.iterdir():
        if p.is_dir() and p.name in hint_text:
            return p.name

    # 3. 가장 최근 수정된 프로젝트 폴더
    candidates = [p for p in projects_dir.iterdir() if p.is_dir() and not p.name.startswith("_")]
    if not candidates:
        return None
    most_recent = max(candidates, key=lambda p: p.stat().st_mtime)
    return most_recent.name


def log_path(project: str) -> Path:
    return get_repo_root() / "projects" / project / "activity.log"


def format_entry(
    timestamp: str,
    action: str,
    stage: str = "",
    target: str = "",
    result: str = "",
    ref: str = "",
    agents: str = "",
    meta: dict | None = None,
) -> str:
    """로그 엔트리 포맷. 빈 필드는 '-'로 채우지 않고 생략하되 파이프는 유지."""
    meta_str = " ".join(f"{k}={v}" for k, v in (meta or {}).items())
    # 각 필드가 None/공백이면 빈 문자열
    fields = [
        f"[{timestamp}]",
        action.strip(),
    ]
    tail = [stage or "-", target or "-", result or "-", ref or "-", agents or "-", meta_str or "-"]
    return f"{fields[0]} {fields[1]} | " + " | ".join(tail)


def append_line(project: str, line: str) -> None:
    """append-only 쓰기. 실패해도 예외 전파 안 함 (로그 실패가 작업을 막지 않도록)."""
    try:
        path = log_path(project)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            header = (
                "# Research Agent Activity Log\n"
                f"# Project: {project}\n"
                f"# Created: {now_iso()}\n"
                "# Format: [TIMESTAMP] ACTION | STAGE | TARGET | RESULT | ref:ID | agents:... | key=value\n"
                "# Stop hook 자동 필드: duration=Ns tokens_in=N tokens_out=N cache_read=N cache_creation=N\n"
                "\n"
            )
            path.write_text(header, encoding="utf-8")
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"⚠️  activity_log 쓰기 실패 ({e}) — 계속 진행", file=sys.stderr)


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def detect_command(prompt: str) -> tuple[str, str | None] | None:
    """prompt에서 명령 패턴 매칭. (action_label, stage_hint) 반환."""
    for pattern, label, stage in COMMAND_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return (label, stage)
    return None


# ─────────────────────────── Hook 진입점 ───────────────────────────


def cmd_on_prompt_submit() -> int:
    """UserPromptSubmit hook 진입점.
    stdin에서 JSON 받아 prompt 추출 → 명령 감지 → pending 라인 기록.
    """
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    prompt = data.get("prompt", "") or data.get("user_message", "") or ""
    if not prompt:
        return 0

    # time-travel 패턴 (ref:XXX-NNN) 감지
    ref_matches = REF_PATTERN.findall(prompt)
    if ref_matches:
        project = detect_project(hint_text=prompt)
        if project:
            ref_str = ",".join(f"ref:{kind}-{num}" for kind, num in ref_matches)
            line = format_entry(
                timestamp=now_iso(),
                action="⏪ time-travel 조회 요청",
                stage="-",
                target="archive",
                result="pending",
                ref=ref_str,
                meta={"source": "hook"},
            )
            append_line(project, line)
        return 0

    # 명령 감지
    detected = detect_command(prompt)
    if not detected:
        return 0  # 평범한 채팅은 로깅 안 함

    action_label, stage_hint = detected
    project = detect_project(hint_text=prompt)
    if not project:
        # 프로젝트 판별 불가 — 로깅 스킵 (프로젝트 생성 중이면 단계 resolve에서 처리)
        return 0

    # pending 라인 기록
    line = format_entry(
        timestamp=now_iso(),
        action=f"▶️ {action_label}",
        stage=stage_hint or "-",
        target="-",
        result="pending",
        meta={"source": "hook"},
    )
    append_line(project, line)
    return 0


def cmd_on_turn_end() -> int:
    """Stop hook 진입점.
    가장 최근 pending 엔트리를 찾고, 실제로 어떤 아티팩트가 변경됐는지 판단해서
    완료 라인 append. (append-only이므로 pending 수정 안 함.)
    duration·tokens 메트릭을 함께 기록.
    """
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    # transcript_path에서 최근 tool 호출·생성 파일 추출 시도
    transcript_path = data.get("transcript_path", "")

    # 가장 최근 수정된 프로젝트를 찾음
    project = detect_project()
    if not project:
        return 0

    # 최근 pending 엔트리가 있는지 확인
    path = log_path(project)
    if not path.exists():
        return 0

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return 0

    # 아직 닫히지 않은(이후 turn_end=true 라인 없는) 가장 최근 pending 탐색
    pending_line = find_unclosed_pending(lines)

    if not pending_line:
        return 0  # pending 없음 또는 이미 닫힘 → 기록할 의미 없는 turn

    # pending 타임스탬프 추출 → duration 계산
    pending_ts = extract_ts(pending_line)
    now_dt = datetime.now()
    duration_sec = int((now_dt - pending_ts).total_seconds()) if pending_ts else None

    # transcript에서 이번 turn 토큰 사용량 집계 (pending 이후 assistant 이벤트)
    tokens = scan_transcript_tokens(transcript_path, pending_ts)

    # transcript를 읽어 이번 turn에 변경된 아티팩트 추론
    artifacts_touched = scan_transcript_artifacts(transcript_path, project)

    # 완료 라인 생성
    action = "✅ turn 완료"
    target = ", ".join(artifacts_touched[:3]) if artifacts_touched else "-"
    if len(artifacts_touched) > 3:
        target += f" (+{len(artifacts_touched) - 3} more)"

    meta = {"source": "hook", "turn_end": "true"}
    if duration_sec is not None:
        meta["duration"] = f"{duration_sec}s"
    if tokens:
        meta["tokens_in"] = str(tokens["input_tokens"])
        meta["tokens_out"] = str(tokens["output_tokens"])
        meta["cache_read"] = str(tokens["cache_read_tokens"])
        meta["cache_creation"] = str(tokens["cache_creation_tokens"])

    line = format_entry(
        timestamp=now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        action=action,
        stage="-",
        target=target,
        result="ok",
        meta=meta,
    )
    append_line(project, line)
    return 0


def extract_ts(log_line: str) -> datetime | None:
    """로그 라인에서 '[YYYY-MM-DD HH:MM:SS]' 파싱 → datetime 반환."""
    m = re.match(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", log_line)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def find_unclosed_pending(lines: list[str]) -> str | None:
    """파일을 거꾸로 읽어 아직 turn_end=true로 닫히지 않은 가장 최근 pending 라인을 찾는다.

    counting 방식: 뒤에서 앞으로 스캔하며 turn_end=true를 만날 때마다 closer +1,
    pending을 만나면 closer가 있으면 하나 소진 후 계속. closer 없이 pending을
    만나면 그것이 '열린' pending.
    """
    closers = 0
    for line in reversed(lines):
        if "turn_end=true" in line:
            closers += 1
            continue
        if "result=pending" in line or "| pending |" in line:
            if closers > 0:
                closers -= 1
                continue
            return line
    return None


def scan_transcript_tokens(transcript_path: str, since_ts: datetime | None) -> dict | None:
    """transcript JSONL → since_ts 이후 assistant 이벤트 토큰 집계.

    동일한 requestId로 여러 assistant 이벤트(thinking/tool_use 등 분할)가 기록되는
    경우가 있으므로 requestId 기준 dedupe. since_ts가 None이면 None 반환.
    """
    if not since_ts or not transcript_path or not Path(transcript_path).exists():
        return None

    # 로그 타임스탬프는 local naive → UTC로 변환
    since_utc = since_ts.astimezone(timezone.utc) if since_ts.tzinfo else since_ts.replace(
        tzinfo=datetime.now().astimezone().tzinfo
    ).astimezone(timezone.utc)

    seen_requests: dict[str, dict] = {}
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for raw in f:
                try:
                    evt = json.loads(raw)
                except Exception:
                    continue
                if evt.get("type") != "assistant":
                    continue
                ts_str = evt.get("timestamp", "")
                if not ts_str:
                    continue
                try:
                    evt_ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except Exception:
                    continue
                if evt_ts < since_utc:
                    continue
                req_id = evt.get("requestId") or ""
                msg = evt.get("message") or {}
                usage = msg.get("usage") or {}
                if not usage:
                    continue
                if req_id and req_id in seen_requests:
                    continue
                seen_requests[req_id or f"_anon_{id(evt)}"] = usage
    except Exception:
        return None

    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
    }
    for usage in seen_requests.values():
        totals["input_tokens"] += usage.get("input_tokens", 0) or 0
        totals["output_tokens"] += usage.get("output_tokens", 0) or 0
        totals["cache_read_tokens"] += usage.get("cache_read_input_tokens", 0) or 0
        totals["cache_creation_tokens"] += usage.get("cache_creation_input_tokens", 0) or 0
    return totals


def scan_transcript_artifacts(transcript_path: str, project: str) -> list[str]:
    """transcript JSONL을 읽어 이번 turn에 touched된 프로젝트 내 파일 추출."""
    touched = set()
    if not transcript_path or not Path(transcript_path).exists():
        return []
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    evt = json.loads(line)
                except Exception:
                    continue
                # tool_use 이벤트에서 파일 경로 추출
                if evt.get("type") == "tool_use":
                    inp = evt.get("input", {})
                    for key in ("file_path", "path", "target"):
                        val = inp.get(key, "")
                        if isinstance(val, str) and f"projects/{project}" in val:
                            rel = val.split(f"projects/{project}/", 1)[-1]
                            touched.add(rel)
    except Exception:
        return []
    return sorted(touched)[:10]


def cmd_on_bash_event() -> int:
    """PostToolUse(Bash) hook 진입점.
    핵심 스크립트(sync_state.py 등) 호출을 별도 이벤트로 기록.
    """
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        return 0

    # 핵심 스크립트 호출만 필터
    key_scripts = [
        ("sync_state.py snapshot-chapters", "📸 챕터 스냅샷"),
        ("sync_state.py snapshot-critical-questions", "📸 질문 스냅샷"),
        ("sync_state.py snapshot-critical-commitments", "📸 commitments 스냅샷"),
        ("sync_state.py update-evaluation", "📊 평가 상태 갱신"),
        ("sync_state.py update-chapter", "✏️  챕터 상태 갱신"),
        ("sync_state.py update-paper", "📄 논문 상태 갱신"),
        ("sync_state.py update-flow", "📝 flow 상태 갱신"),
        ("sync_state.py update-final", "📦 final 상태 갱신"),
        ("sync_state.py remove-paper", "🗑  논문 제거"),
        ("extract_metadata.py", "🔍 PDF 메타데이터 추출"),
    ]

    for key, label in key_scripts:
        if key in command:
            project = detect_project(hint_text=command)
            if project:
                line = format_entry(
                    timestamp=now_iso(),
                    action=label,
                    stage="-",
                    target="-",
                    result="ok",
                    meta={"source": "hook", "cmd": key.split()[-1] if " " in key else key},
                )
                append_line(project, line)
            break
    return 0


# ─────────────────────────── 수동 append (MD fallback) ───────────────────────────


def cmd_append(project: str, action: str, **fields) -> int:
    """MD Layer 4 fallback용. Claude가 명령 완료 시 직접 호출."""
    line = format_entry(
        timestamp=now_iso(),
        action=action,
        stage=fields.get("stage", ""),
        target=fields.get("target", ""),
        result=fields.get("result", ""),
        ref=fields.get("ref", ""),
        agents=fields.get("agents", ""),
        meta={k: v for k, v in fields.items() if k not in ("stage", "target", "result", "ref", "agents")},
    )
    append_line(project, line)
    print(f"✅ 로그 기록: {line}")
    return 0


# ─────────────────────────── 파싱 / 조회 ───────────────────────────


LINE_RE = re.compile(
    r"^\[(?P<ts>[\d\-:\s]+)\]\s+(?P<action>[^|]+?)\s*\|\s*(?P<stage>[^|]+?)\s*\|\s*"
    r"(?P<target>[^|]+?)\s*\|\s*(?P<result>[^|]+?)\s*\|\s*(?P<ref>[^|]+?)\s*\|\s*"
    r"(?P<agents>[^|]+?)\s*\|\s*(?P<meta>.+?)\s*$"
)


def parse_line(line: str) -> dict | None:
    """로그 한 줄 → 구조화된 딕셔너리."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    m = LINE_RE.match(line)
    if not m:
        return None
    d = m.groupdict()
    meta = {}
    for kv in d["meta"].split():
        if "=" in kv:
            k, v = kv.split("=", 1)
            meta[k] = v
    d["meta_dict"] = meta
    return d


def cmd_parse(line: str) -> int:
    """디버그용: 한 줄 파싱 결과 출력."""
    parsed = parse_line(line)
    if parsed:
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    else:
        print("⚠️  파싱 실패 (포맷 불일치)")
    return 0


def cmd_recent(project: str, days: int = 14) -> int:
    """최근 N일치 엔트리를 JSON list로 반환."""
    path = log_path(project)
    if not path.exists():
        print("[]")
        return 0

    cutoff = datetime.now() - timedelta(days=days)
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_line(line)
        if not parsed:
            continue
        try:
            ts = datetime.strptime(parsed["ts"].strip(), "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if ts >= cutoff:
            parsed["ts_obj"] = ts.isoformat()
            del parsed["ts_obj"]  # JSON 직렬화 위해 문자열만 유지
            entries.append(parsed)
    print(json.dumps(entries, indent=2, ensure_ascii=False))
    return 0


# ─────────────────────────── 추천 엔진 ───────────────────────────


def cmd_recommend(project: str, days: int = 14) -> int:
    """최근 로그 분석 + sync 상태 종합 → 작업 추천."""
    path = log_path(project)
    if not path.exists():
        print(json.dumps({
            "status": "no_log",
            "message": "활동 로그가 없습니다. 프로젝트를 사용하시면 로그가 누적됩니다.",
        }, ensure_ascii=False, indent=2))
        return 0

    cutoff = datetime.now() - timedelta(days=days)
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_line(line)
        if not parsed:
            continue
        try:
            ts = datetime.strptime(parsed["ts"].strip(), "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if ts >= cutoff:
            parsed["_ts"] = ts
            entries.append(parsed)

    # 현재 상태 스냅샷 구성
    last_action = entries[-1] if entries else None
    days_since_last = (datetime.now() - last_action["_ts"]).days if last_action else 999

    # 최근 평가 결과 추출
    last_eval = None
    for e in reversed(entries):
        if "평가" in e["action"] and "pending" not in e["result"]:
            last_eval = e
            break

    # 최근 수행된 stage
    last_stage = None
    for e in reversed(entries):
        if e["stage"] != "-":
            last_stage = e["stage"]
            break

    # 미완 commitment·HUNT 탐지 (간단한 휴리스틱)
    commitment_hints = [e for e in entries if "commitment" in e["action"].lower() or "답변 반영" in e["action"]]

    recs = []

    # P1: 장기 미활동
    if days_since_last >= 3:
        if last_stage in ("v1-draft", "revised"):
            recs.append({
                "priority": "P1",
                "command": '"평가해줘"',
                "reason": f"{days_since_last}일 미활동. 마지막 stage는 {last_stage}. 재평가로 현재 상태 확인 권장.",
                "ref_log": last_action["ts"] if last_action else "",
            })
        elif last_stage == "stage1":
            recs.append({
                "priority": "P1",
                "command": '"레퍼런스 점검해줘"',
                "reason": f"{days_since_last}일 미활동. 마지막은 Stage 1 리서치. 축 1 경량 점검으로 재진입 권장.",
                "ref_log": last_action["ts"] if last_action else "",
            })

    # P2: stage 자연 다음 단계
    if last_stage == "flow":
        recs.append({
            "priority": "P2",
            "command": '"작업 시작해줘"',
            "reason": "flow 평가 완료 후 자연 다음 단계. HUNT·REANALYZE 과제 자동 실행.",
            "ref_log": last_eval["ts"] if last_eval else "",
        })
    elif last_stage == "stage1":
        recs.append({
            "priority": "P2",
            "command": '"초안 작성해줘"',
            "reason": "리서치 완료 후 Stage 2 초안 작성 권장.",
            "ref_log": last_action["ts"] if last_action else "",
        })
    elif last_stage == "v1-draft":
        recs.append({
            "priority": "P2",
            "command": '"Chapter X 수정해줘: ..."',
            "reason": "초안 완료. 평가 결과를 바탕으로 약한 챕터부터 순차 수정 권장.",
            "ref_log": last_eval["ts"] if last_eval else "",
        })
    elif last_stage == "revised":
        recs.append({
            "priority": "P2",
            "command": '"최종 통합해줘"',
            "reason": "수정 완료. final/ 재빌드 후 리뷰 체크로 최종 품질 게이트.",
            "ref_log": last_action["ts"] if last_action else "",
        })

    # P3: 미완 감지
    if commitment_hints:
        recs.append({
            "priority": "P3",
            "command": '"답변 반영해줘"',
            "reason": "critical-questions 답변 반영 기록 있음. commitment 상태 재확인 권장.",
            "ref_log": commitment_hints[-1]["ts"],
        })

    # P4: 기본 안전망
    if not recs:
        recs.append({
            "priority": "P4",
            "command": '"sync 확인해줘"',
            "reason": "특별한 다음 단계가 없음. 현재 프로젝트 상태 점검으로 시작 권장.",
            "ref_log": last_action["ts"] if last_action else "",
        })

    result = {
        "status": "ok",
        "current_state": {
            "last_activity": last_action["ts"] if last_action else None,
            "days_since_last": days_since_last,
            "last_stage": last_stage,
            "last_evaluation": (
                {"ts": last_eval["ts"], "result": last_eval["result"]}
                if last_eval else None
            ),
            "entries_analyzed": len(entries),
            "window_days": days,
        },
        "recommendations": recs,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


# ─────────────────────────── Time-travel archive 조회 ───────────────────────────


def cmd_resolve_ref(project: str, ref_id: str) -> int:
    """ref:kind-NNN을 archive 경로로 해석해 파일 목록 반환."""
    m = REF_PATTERN.match(ref_id)
    if not m:
        print(json.dumps({"status": "error", "msg": f"잘못된 ref 형식: {ref_id}"}))
        return 1
    kind, num = m.groups()

    repo = get_repo_root()
    proj_root = repo / "projects" / project

    archive_map = {
        "eval": proj_root / "evaluations" / "archive",
        "ch": proj_root / "chapters" / "archive",
        "q": proj_root / "critical-questions.archive",
        "commits": proj_root / "critical-commitments.archive",
    }

    archive_dir = archive_map.get(kind)
    if not archive_dir or not archive_dir.exists():
        print(json.dumps({"status": "error", "msg": f"archive 폴더 없음: {kind}"}))
        return 1

    # {NNN}-* 폴더 또는 {NNN}-*.md 파일 탐색
    candidates = []
    for item in archive_dir.iterdir():
        if item.name.startswith(f"{num}-"):
            candidates.append(str(item.relative_to(repo)))

    if not candidates:
        print(json.dumps({"status": "not_found", "msg": f"ref:{kind}-{num} 해당 archive 없음"}))
        return 1

    print(json.dumps({
        "status": "ok",
        "ref": f"ref:{kind}-{num}",
        "paths": candidates,
    }, indent=2, ensure_ascii=False))
    return 0


# ─────────────────────────── CLI ───────────────────────────


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1

    cmd = argv[1]
    args = argv[2:]

    try:
        if cmd == "on-prompt-submit":
            return cmd_on_prompt_submit()
        if cmd == "on-turn-end":
            return cmd_on_turn_end()
        if cmd == "on-bash-event":
            return cmd_on_bash_event()
        if cmd == "append" and len(args) >= 2:
            project = args[0]
            action = args[1]
            fields = {}
            for a in args[2:]:
                if "=" in a:
                    k, v = a.split("=", 1)
                    fields[k] = v
            return cmd_append(project, action, **fields)
        if cmd == "parse" and len(args) >= 1:
            return cmd_parse(" ".join(args))
        if cmd == "recent" and len(args) >= 1:
            days = int(args[1]) if len(args) >= 2 else 14
            return cmd_recent(args[0], days)
        if cmd == "recommend" and len(args) >= 1:
            days = int(args[1]) if len(args) >= 2 else 14
            return cmd_recommend(args[0], days)
        if cmd == "resolve-ref" and len(args) == 2:
            return cmd_resolve_ref(args[0], args[1])
    except Exception as e:
        print(f"⚠️  activity_log 오류: {e}", file=sys.stderr)
        return 0  # 절대 user 작업을 막지 않음

    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
