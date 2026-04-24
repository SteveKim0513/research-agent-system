#!/usr/bin/env python3
"""
card_registry.py — 2-card 시스템의 SSOT (Single Source of Truth).

카드 타입 2종:
- RESEARCH (papers/.registry.json)  · mode ∈ {search, reanalyze}
- WRITE    (output/.registry.json)  · mode ∈ {create, modify}

카드 = 자동 프로세스(평가·감사·claim-extractor·flow delta 등)가 "결함/필요"를
탐지했을 때 사용자에게 제시되는 권장 후속 작업. registry는 발급·dedup·lifecycle
영속 보존을 담당하고, work-plan.md는 활성 view.

**핵심 원칙**
- 모든 ID 발급은 이 모듈(또는 CLI)을 통해야 한다. self-grep `[TYPE-NNN]` 금지.
- dedup_key는 정규화된 tuple. 첫 원소는 항상 mode.
- 기존 dedup_key와 일치:
    · active(ready/in_progress/blocked/deferred) → 그 ID 재사용 (skip)
    · completed → reactivation (status=ready + history append)

**상태 (lifecycle)**: ready / in_progress / blocked / deferred / completed
**완료 카드 정책**:
- RESEARCH mode=search: completed 시 work-plan에서 카드 제거 (4-stage 산출물이 별도 파일에 남음)
- 그 외: work-plan에 보존 (Recent → Older 자연 이동), registry는 status만 갱신

CLI:
    python3 scripts/card_registry.py stats     <project> <research|write>
    python3 scripts/card_registry.py list      <project> <research|write>
    python3 scripts/card_registry.py bootstrap <project> <research|write>
    python3 scripts/card_registry.py issue     <project> <research|write> <mode> \\
            --dedup-key K1 [K2 ...] [--field k=v ...]
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


REGISTRY_VERSION = "2.0"

DOMAINS = {
    "research": {
        "card_type": "RESEARCH",
        "path_suffix": ("papers", ".registry.json"),
        "modes": ("search", "reanalyze"),
    },
    "write": {
        "card_type": "WRITE",
        "path_suffix": ("output", ".registry.json"),
        "modes": ("create", "modify"),
    },
}

CARD_TYPE_TO_DOMAIN = {v["card_type"]: k for k, v in DOMAINS.items()}


# ──────────────────────────────────────────────────────────
# Path · IO
# ──────────────────────────────────────────────────────────

def _validate_domain(domain: str) -> None:
    if domain not in DOMAINS:
        raise ValueError(f"domain must be one of {list(DOMAINS)}, got {domain!r}")


def _validate_mode(domain: str, mode: str) -> None:
    _validate_domain(domain)
    if mode not in DOMAINS[domain]["modes"]:
        raise ValueError(
            f"mode must be one of {DOMAINS[domain]['modes']} for domain={domain}, got {mode!r}"
        )


def registry_path(project_root: Path, domain: str) -> Path:
    _validate_domain(domain)
    folder, fname = DOMAINS[domain]["path_suffix"]
    return project_root / folder / fname


def empty_registry(domain: str) -> dict:
    _validate_domain(domain)
    return {
        "schema_version": REGISTRY_VERSION,
        "domain": domain,
        "card_type": DOMAINS[domain]["card_type"],
        "next_id": 1,
        "cards": {},
    }


def load(project_root: Path, domain: str) -> dict:
    _validate_domain(domain)
    p = registry_path(project_root, domain)
    if not p.exists():
        return empty_registry(domain)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data.setdefault("schema_version", REGISTRY_VERSION)
        data.setdefault("domain", domain)
        data.setdefault("card_type", DOMAINS[domain]["card_type"])
        data.setdefault("next_id", 1)
        data.setdefault("cards", {})
        return data
    except Exception:
        return empty_registry(domain)


def save(project_root: Path, registry: dict) -> None:
    domain = registry.get("domain")
    _validate_domain(domain)
    p = registry_path(project_root, domain)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )


# ──────────────────────────────────────────────────────────
# Normalization
# ──────────────────────────────────────────────────────────

def _norm_text(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[`\"'“”‘’,.;:!?\[\](){}]", "", s)
    return s


def _norm_filename(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    s = s.split("/")[-1]
    return s


def _norm_location(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r"§|섹션", " section ", s)
    s = re.sub(r"(?<![a-z])sec\.?(?![a-z])", " section ", s)
    s = re.sub(r"¶|문단", " para ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[`\"'“”‘’,.;:!?\[\](){}]", "", s)
    return s


def _norm_r_id(raw: str) -> str:
    """claim-extractor의 R-ID 정규화: 'R-03 (보완)' → 'r-03'."""
    s = raw.strip().rstrip(".,;:")
    m = re.match(r"^(R-\d+)", s, re.IGNORECASE)
    if m:
        return m.group(1).lower()
    return s.lower()


def normalize_dedup_key(domain: str, mode: str, raw_key) -> tuple:
    """(mode, ...normalized_parts)로 정규화된 hashable tuple 반환.

    - research/search   : (mode, *sorted_r_ids) — covers 정규화
    - research/reanalyze: (mode, pdf_filename, angle_norm)
    - write/create      : (mode, target_file, location_norm)
    - write/modify      : (mode, target_file, target_text_norm)
    """
    _validate_mode(domain, mode)
    if isinstance(raw_key, str):
        raw_key = (raw_key,)
    raw_key = tuple(raw_key)

    if domain == "research":
        if mode == "search":
            r_ids = sorted(
                {_norm_r_id(r) for r in raw_key if r and not r.startswith("(")}
            )
            return (mode, *r_ids)
        if mode == "reanalyze":
            if len(raw_key) < 2:
                raise ValueError("research/reanalyze dedup_key: (pdf_filename, angle) 필요")
            return (mode, _norm_filename(raw_key[0]), _norm_text(raw_key[1]))
    if domain == "write":
        if mode == "create":
            if len(raw_key) < 2:
                raise ValueError("write/create dedup_key: (target_file, location) 필요")
            return (mode, _norm_filename(raw_key[0]), _norm_location(raw_key[1]))
        if mode == "modify":
            if len(raw_key) < 2:
                raise ValueError("write/modify dedup_key: (target_file, target_text) 필요")
            return (mode, _norm_filename(raw_key[0]), _norm_text(raw_key[1]))
    raise AssertionError(f"unreachable: {domain}/{mode}")


# ──────────────────────────────────────────────────────────
# Lookup · issuance · lifecycle
# ──────────────────────────────────────────────────────────

def find_by_dedup_key(registry: dict, mode: str, dedup_key) -> str | None:
    """정규화된 dedup_key가 일치하는 card ID 반환. active/completed 모두 탐색."""
    if not dedup_key:
        return None
    target = normalize_dedup_key(registry["domain"], mode, dedup_key)
    if len(target) <= 1:  # mode만 있고 실질 key 없음
        return None
    for cid, meta in registry["cards"].items():
        if meta.get("mode") != mode:
            continue
        existing = tuple(meta.get("dedup_key") or [])
        if existing == target:
            return cid
    return None


def next_id(registry: dict) -> str:
    return f"{registry['card_type']}-{registry['next_id']:03d}"


def add_new(registry: dict, card_id: str, mode: str, dedup_key, metadata: dict | None = None) -> None:
    _validate_mode(registry["domain"], mode)
    if metadata is None:
        metadata = {}
    now = datetime.now().isoformat(timespec="seconds")
    norm_key = normalize_dedup_key(registry["domain"], mode, dedup_key)
    registry["cards"][card_id] = {
        "id": card_id,
        "mode": mode,
        "dedup_key": list(norm_key),
        "metadata": dict(metadata),
        "status": "ready",
        "issued_at": now,
        "completed_at": None,
        "reactivated_count": 0,
        "history": [{"at": now, "event": "issued", "mode": mode}],
    }
    n = int(card_id.split("-")[1])
    if n >= registry["next_id"]:
        registry["next_id"] = n + 1


def reactivate(registry: dict, card_id: str, reason: str = "동일 dedup_key 재제안") -> None:
    if card_id not in registry["cards"]:
        return
    c = registry["cards"][card_id]
    c["status"] = "ready"
    c["completed_at"] = None
    c["reactivated_count"] = c.get("reactivated_count", 0) + 1
    c.setdefault("history", []).append({
        "at": datetime.now().isoformat(timespec="seconds"),
        "event": "reactivated",
        "reason": reason,
    })


def mark_completed(registry: dict, card_id: str, summary: str | None = None) -> None:
    if card_id not in registry["cards"]:
        return
    c = registry["cards"][card_id]
    now = datetime.now().isoformat(timespec="seconds")
    c["status"] = "completed"
    c["completed_at"] = now
    if summary:
        c["result_summary"] = summary
    c.setdefault("history", []).append({
        "at": now, "event": "completed",
        **({"summary": summary} if summary else {}),
    })


def update_status(registry: dict, card_id: str, status: str) -> None:
    if card_id not in registry["cards"]:
        return
    c = registry["cards"][card_id]
    if c["status"] == status:
        return
    c["status"] = status
    c.setdefault("history", []).append({
        "at": datetime.now().isoformat(timespec="seconds"),
        "event": f"status→{status}",
    })


# ──────────────────────────────────────────────────────────
# work-plan ⇄ registry sync
# ──────────────────────────────────────────────────────────

def _id_pattern(card_type: str) -> re.Pattern:
    return re.compile(rf"###\s+\[{card_type}-(\d+)\]")


def sync_from_work_plan(registry: dict, sections: dict) -> list:
    """섹션 위치 기반으로 registry lifecycle 갱신. completed ID 리스트 반환.

    RESEARCH mode=search는 호출자가 work-plan에서 제거할지 별도 판단 (search 정책).
    그 외는 work-plan에 보존.
    """
    section_to_status = {
        "active": "ready",
        "in_progress": "in_progress",
        "blocked": "blocked",
        "deferred": "deferred",
    }
    pat = _id_pattern(registry["card_type"])
    completed_ids = []

    for key, status in section_to_status.items():
        text = sections.get(key, "")
        for m in pat.finditer(text):
            cid = f"{registry['card_type']}-{int(m.group(1)):03d}"
            if cid in registry["cards"]:
                update_status(registry, cid, status)

    for key in ("completed_recent", "completed_older"):
        text = sections.get(key, "")
        for m in pat.finditer(text):
            cid = f"{registry['card_type']}-{int(m.group(1)):03d}"
            if cid in registry["cards"]:
                if registry["cards"][cid]["status"] != "completed":
                    mark_completed(registry, cid)
                completed_ids.append(cid)

    return completed_ids


def remove_cards_from_section_text(section_text: str, card_ids: set, card_type: str) -> str:
    if not section_text or section_text.strip() == "_(없음)_" or not card_ids:
        return section_text

    pat_self = re.compile(rf"^###\s+\[{card_type}-(\d+)\]")
    pat_any = re.compile(r"^###\s+\[")

    lines = section_text.split("\n")
    result = []
    skip = False
    for line in lines:
        m = pat_self.match(line)
        if m:
            cid = f"{card_type}-{int(m.group(1)):03d}"
            skip = cid in card_ids
        elif pat_any.match(line):
            skip = False
        if not skip:
            result.append(line)

    cleaned = "\n".join(result).strip()
    return cleaned or "_(없음)_"


# ──────────────────────────────────────────────────────────
# Bootstrap (work-plan → registry 역복원)
# ──────────────────────────────────────────────────────────

# 카드 블록에서 dedup key 후보 필드 추출용
_BOOTSTRAP_FIELDS = {
    ("research", "search"):      ("covers",),
    ("research", "reanalyze"): ("대상 PDF", "재분석 각도"),
    ("write", "create"):       ("대상 챕터", "위치"),
    ("write", "modify"):       ("대상 챕터", "수정 내용"),
}


def _extract_field(block: str, label: str) -> str:
    m = re.search(rf"\*\*{re.escape(label)}\*\*:\s*([^\n]+)", block)
    return m.group(1).strip() if m else ""


def _infer_mode_from_block(domain: str, block: str) -> str:
    """카드 블록에서 `**mode**: ...` 탐지. 없으면 도메인 기본값."""
    m = re.search(r"\*\*mode\*\*:\s*(\w+)", block)
    if m:
        mode = m.group(1).strip().lower()
        if mode in DOMAINS[domain]["modes"]:
            return mode
    # 기본값: 카드 본문 힌트로 추론
    if domain == "research":
        return "reanalyze" if ("재분석" in block or "analyzed/" in block) else "search"
    # write
    return "create" if "초안" in block or "신규" in block else "modify"


def bootstrap_from_work_plan(registry: dict, work_plan_text: str) -> int:
    if not work_plan_text:
        return 0
    domain = registry["domain"]
    card_type = registry["card_type"]
    pat = _id_pattern(card_type)

    card_starts = [(m.start(), m.group(1)) for m in pat.finditer(work_plan_text)]
    other_starts = [m.start() for m in re.finditer(r"###\s+\[", work_plan_text)]

    added = 0
    for start, num in card_starts:
        cid = f"{card_type}-{int(num):03d}"
        if cid in registry["cards"]:
            continue
        next_b = [s for s in other_starts if s > start]
        end = min(next_b) if next_b else len(work_plan_text)
        block = work_plan_text[start:end]

        status = _infer_status_from_context(work_plan_text, start)
        mode = _infer_mode_from_block(domain, block)
        what = _extract_field(block, "무엇")
        fields = _BOOTSTRAP_FIELDS[(domain, mode)]

        if mode == "search":
            covers_raw = _extract_field(block, "covers")
            raw_key = [r.strip() for r in re.split(r"[,]\s*", covers_raw) if r.strip()]
            if not raw_key:
                raw_key = ["unknown"]
        else:
            raw_values = [_extract_field(block, f) or "unknown" for f in fields]
            raw_key = raw_values

        try:
            norm_key = normalize_dedup_key(domain, mode, raw_key)
        except ValueError:
            norm_key = (mode,) + tuple(_norm_text(x) for x in raw_key)

        metadata = {"무엇": what} if what else {}
        for f in fields:
            v = _extract_field(block, f)
            if v:
                metadata[f] = v

        now = datetime.now().isoformat(timespec="seconds")
        registry["cards"][cid] = {
            "id": cid,
            "mode": mode,
            "dedup_key": list(norm_key),
            "metadata": metadata,
            "status": status,
            "issued_at": now,
            "completed_at": now if status == "completed" else None,
            "reactivated_count": 0,
            "history": [
                {"at": now, "event": "bootstrapped_from_work_plan",
                 "inferred_status": status, "inferred_mode": mode},
            ],
        }
        added += 1
        n = int(num)
        if n >= registry["next_id"]:
            registry["next_id"] = n + 1
    return added


def _infer_status_from_context(work_plan_text: str, card_start: int) -> str:
    preamble = work_plan_text[:card_start]
    section_markers = [
        ("## 🟡 Active", "ready"),
        ("## 🔵 In-progress", "in_progress"),
        ("## 🔴 Blocked", "blocked"),
        ("## ⚪ Deferred", "deferred"),
        ("## 🟢 Recent completed", "completed"),
        ("## 📜 Older completed", "completed"),
    ]
    best_pos = -1
    best_status = "ready"
    for marker, status in section_markers:
        pos = preamble.rfind(marker)
        if pos > best_pos:
            best_pos = pos
            best_status = status
    return best_status


# ──────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────

def _print_usage():
    print("Usage:")
    print("  card_registry.py stats     <project> <research|write>")
    print("  card_registry.py list      <project> <research|write>")
    print("  card_registry.py bootstrap <project> <research|write>")
    print("  card_registry.py issue     <project> <research|write> <mode> \\")
    print("                             --dedup-key K1 [K2 ...] [--field k=v ...]")


def _cli():
    import sys
    if len(sys.argv) < 4:
        _print_usage()
        sys.exit(1)

    cmd = sys.argv[1]
    project = sys.argv[2]
    domain = sys.argv[3].lower()

    try:
        _validate_domain(domain)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    root = Path("projects") / project
    reg = load(root, domain)

    if cmd == "list":
        for cid, c in sorted(reg["cards"].items()):
            topic = c.get("metadata", {}).get("무엇", "")
            print(f"{cid}  {c['mode']:9}  {c['status']:12}  {topic}")
        return

    if cmd == "stats":
        counts = {}
        mode_counts = {}
        for c in reg["cards"].values():
            counts[c["status"]] = counts.get(c["status"], 0) + 1
            mode_counts[c["mode"]] = mode_counts.get(c["mode"], 0) + 1
        print(f"Total {reg['card_type']} cards: {len(reg['cards'])}")
        print(f"Next ID             : {reg['card_type']}-{reg['next_id']:03d}")
        for s, c in sorted(counts.items()):
            print(f"  status · {s:12}: {c}")
        for m, c in sorted(mode_counts.items()):
            print(f"  mode   · {m:9}: {c}")
        return

    if cmd == "bootstrap":
        wp = root / "work-plan.md"
        if not wp.exists():
            print(f"❌ work-plan.md 없음: {wp}")
            sys.exit(1)
        added = bootstrap_from_work_plan(reg, wp.read_text(encoding="utf-8"))
        save(root, reg)
        print(f"✅ {reg['card_type']} bootstrap: {added}건 추가 (next_id={reg['next_id']})")
        return

    if cmd == "issue":
        if len(sys.argv) < 5:
            print("❌ mode 인자 필요 (search|reanalyze|create|modify)")
            _print_usage()
            sys.exit(1)
        mode = sys.argv[4].lower()
        try:
            _validate_mode(domain, mode)
        except ValueError as e:
            print(f"❌ {e}")
            sys.exit(1)

        args = sys.argv[5:]
        dedup_key = []
        metadata = {}
        i = 0
        while i < len(args):
            a = args[i]
            if a == "--dedup-key":
                i += 1
                while i < len(args) and not args[i].startswith("--"):
                    dedup_key.append(args[i])
                    i += 1
            elif a == "--field":
                i += 1
                if i < len(args):
                    kv = args[i]
                    if "=" not in kv:
                        print(f"❌ --field 형식 (k=v): {kv}")
                        sys.exit(1)
                    k, v = kv.split("=", 1)
                    metadata[k.strip()] = v.strip()
                    i += 1
            else:
                print(f"❌ 알 수 없는 인자: {a}")
                sys.exit(1)

        if not dedup_key:
            print("❌ --dedup-key 필수")
            sys.exit(1)

        existing = find_by_dedup_key(reg, mode, dedup_key)
        if existing:
            c = reg["cards"][existing]
            if c["status"] == "completed":
                reactivate(reg, existing, reason="CLI issue 재제안")
                save(root, reg)
                print(existing)
                print(f"   ↻ reactivated (이전 status=completed)", file=sys.stderr)
                return
            print(existing)
            print(f"   ⏭  skip — 동일 dedup_key가 이미 status={c['status']}", file=sys.stderr)
            return

        new_id = next_id(reg)
        add_new(reg, new_id, mode, dedup_key, metadata)
        save(root, reg)
        print(new_id)
        print(f"   ✅ issued (mode={mode}, status=ready)", file=sys.stderr)
        return

    print(f"Unknown command: {cmd}")
    _print_usage()
    sys.exit(1)


if __name__ == "__main__":
    _cli()
