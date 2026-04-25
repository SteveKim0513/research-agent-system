# WORK-PLAN-FORMAT.md — work-plan.md 포맷 규율

> 이 문서는 `projects/{P}/work-plan.md`의 **엄격한 포맷 스펙**입니다. 모든 에이전트(evaluation-orchestrator, claim-extractor, writing-architect, chapter-editor, flow-refiner, paper-processing-orchestrator, evaluation_aggregator)가 work-plan을 읽고 쓸 때 이 파일의 규칙을 준수해야 합니다.
>
> **이 포맷을 지키는 이유**: 에이전트들이 각자 포맷을 해석하면 섹션이 깨지거나 번호가 엇갈립니다. 단일 source of truth + grep/regex로 파싱 가능한 구조가 자동화의 전제.

---

## 1. 파일 전체 구조

```markdown
# work-plan.md

> 📅 마지막 갱신: YYYY-MM-DD HH:MM ({trigger})
> Stage: {flow | v1 | revised | final}
> intellectual_ambition: {incremental | critical | paradigm-shifting}

---

## 🧭 현재 당신이 해야 할 일

{사용자 브리핑 — 아래 §4.5}

---

## 📊 대시보드

{고정 포맷 — 아래 §5}

---

## 🟡 Active

{task 카드 0개 이상}

---

## 🔵 In-progress

{task 카드 0개 이상}

---

## 🔴 Blocked

{task 카드 0개 이상}

---

## 🟢 Recent completed (최근 15개)

{task 카드 0-15개, 최신순}

---

## ⚪ Deferred

{task 카드 0개 이상 — 사용자가 의식적으로 미룬 것}

---

## 📜 Older completed

{Recent completed에서 밀려난 것. 카드 전체 유지. 파일이 길어지면 snapshot-work-plan이 archive로 스냅샷}
```

**섹션 순서 고정**. 각 섹션 사이에 `---` 구분자. 섹션 헤더(`## 🟡 Active` 등) 텍스트 정확히 일치해야 파싱 가능.

빈 섹션은 `_(없음)_` 한 줄만 넣고 유지 (섹션 자체를 삭제하지 않음).

---

## 2. Task 카드 엄격 스키마

각 task는 `### [TYPE-NNN]` 헤더로 시작하는 **단일 카드 블록**. 카드 간 `---` 또는 빈 줄 2개로 구분.

```markdown
### [RESEARCH-002] 🟡 active · P1 · axis1 · Stage 1

**무엇**: S017 — EF 전통적 보편성 가정

**mode**: search

**담당 명령**: `"리서치 진행해줘"` → Consensus 자동 검색 (4-stage 파이프라인)

**covers**: R-02

**query**: `executive function universal cognitive history`

**검색 키워드 / 기대 논문 프로필**: `claim-extraction-flow.md`의 R-02 섹션 참조 / registry: `papers/.registry.json`

**의존성**: 없음
**차단하는 것**: WRITE-001 (축 1 재평가 후 "So What" 작성 가능)

**진행 로그**:
- 2026-04-23 15:00 · created by aggregator (eval #001, claim-extraction-flow.md:S017)
```

### 2.1 필수 필드

| 필드 | 형식 | 예시 | 필수 |
|------|------|------|------|
| **헤더 라인 (기본)** | `### [TYPE-NNN] {상태이모지} {상태텍스트} · {axis} · Stage {N}` | `### [RESEARCH-002] 🟡 active · axis1 · Stage 1` | ✅ |
| **헤더 라인 (priority 포함)** | 위 + `P{1\|2\|3}` 태그 (axis 앞) | `### [RESEARCH-002] 🟡 active · P1 · axis1 · Stage 1` | 선택 (대시보드 권장 명령 정렬에 활용) |
| **무엇** | `**무엇**: {1줄 설명}` | `**무엇**: S017 — EF 전통적 보편성 가정` | ✅ |
| **mode** | `**mode**: {search\|reanalyze\|create\|modify}` | `**mode**: search` | ✅ (2-type+mode 체계) |
| **담당 명령** | `**담당 명령**: \`"..."\` → {후속 동작}` | `**담당 명령**: "리서치 진행해줘" → Consensus 자동 검색` | ✅ |
| **covers** (RESEARCH mode=search) | `**covers**: R-NN, R-MM` | `**covers**: R-02` | search는 ✅ (registry dedup_key) |
| **query** (RESEARCH mode=search) | `**query**: \`<consensus 통합 쿼리>\`` | (예시 참조) | search는 ✅ |
| **진행 로그** | `**진행 로그**:` 아래 bullet list | (예시 참조) | ✅ |

> 📌 **점수 회복 필드 폐기**: 기존 `**예상 회복**: 축 N +M` 필드는 카테고리 기반 평가 시스템 도입 시 폐기됨. 점수는 보조 신호이므로 card-level 회복량 예측은 더 이상 추적하지 않음.

### 2.2 Card mode별 추가 필드

- **RESEARCH mode=search** (execution unit — 1 카드 = 1 Consensus 쿼리): `**covers**:` (필수, R-ID 리스트. claim-extractor가 제안한 R 중 이 카드가 커버하는 것들. 예: `R-01, R-04`. 정규화 covers = dedup_key), `**query**:` (필수, 통합 대표 쿼리 단일 문자열), `**검색 키워드**:` (선택, bullet 3-5개), `**기대 논문 프로필**:` (유형/시대/저널)
- **RESEARCH mode=reanalyze**: `**대상 PDF**:` (파일명), `**재분석 각도**:` (어느 섹션·주장). dedup_key = (pdf_filename, angle)
- **WRITE mode=create**: `**대상 챕터**:` (파일명), `**위치**:` (Section N·문단), `**내용 요구**:` (구체 구조). dedup_key = (대상 챕터, 위치)
- **WRITE mode=modify**: `**대상 챕터**:` (파일명), `**수정 내용**:` (구체), `**원인**:` (어느 평가·감사 결과). dedup_key = (대상 챕터, 수정 내용 요지)

### 2.3 공통 선택 필드

- `**의존성**: {TASK-ID 목록}` 또는 `없음`
- `**차단하는 것**: {TASK-ID 목록}` 또는 `없음`
- `**메모**: {자유 텍스트 — 에이전트가 남긴 주의사항}`

### 2.4 진행 로그 포맷

```
**진행 로그**:
- YYYY-MM-DD HH:MM · {event} {by 주체} {(context)}
```

이벤트 종류:
- `created by {agent}` — 최초 생성
- `in-progress: {agent}` — 🔵로 전환
- `✅ completed: {요약}` — 🟢로 전환 + 결과 요약
- `🔴 blocked: {이유}` — 🔴로 전환
- `⚪ deferred: {이유}` — ⚪로 전환
- `🟡 resumed` — 🔴·⚪에서 🟡로 복귀
- `note: {자유}` — 상태 전환 없이 메모만

로그는 **append-only**. 과거 로그 수정·삭제 금지.

---

## 3. Card 타입 2종 × mode (담당 명령 1:1)

| Card · mode | 발급 시점 (자동) | 실행 명령 | 담당 에이전트 |
|-------------|----------------|----------|--------------|
| **RESEARCH · search** | `"{stage} 레퍼런스 분석해줘"` (UNMATCHED-EXTERNAL → claim-extraction의 `search[]`) | `"리서치 진행해줘"` | Consensus MCP (4-stage 파이프라인) |
| **RESEARCH · reanalyze** | `"{stage} 레퍼런스 분석해줘"` (UNMATCHED-INTERNAL), `paper_reanalysis_delta.py` (flow 변경) | `"리서치 진행해줘"` | paper-analyst Mode B |
| **WRITE · create** | `"{stage} 내용 분석해줘"` (axis2~6의 `## 🛠 WRITE 후보` 섹션) + writing-architect | `"초안 작성해줘"` | writing-architect |
| **WRITE · modify** | `"{stage} 내용 분석해줘"` (axis2~6의 `## 🛠 WRITE 후보` 섹션) + citation-auditor/peer-reviewer (사후 체이닝) | `"output {파일명} 수정해줘: WRITE-NNN"` | output-editor |

**WRITE 카드 자동 발급 흐름**:
1. `"{stage} 내용 분석해줘"` 명령 → axis2~6 scorer 병렬 실행
2. 각 axis scorer는 출력 끝에 `## 🛠 WRITE 후보` 섹션을 명시 (mode=create|modify, 대상, 무엇, 원인 등)
3. aggregator가 해당 섹션을 파싱 → `card_registry`(domain=write)로 dedup 후 WRITE-NNN 발급
4. dedup_key:
   - mode=modify: `(modify, 대상_filename, 무엇_norm)`
   - mode=create: `(create, 대상_filename, 위치_norm)`
5. 신규 → work-plan 🟡 Active append. 기존 활성 → skip. completed → reactivation.

`{stage}` ∈ {`flow`, `output`}. 자세한 명령어 체계는 `skills/SKILL.md` §명령어 참조.

**카드가 아닌 것 — flow.md 수정**: 사용자가 `"flow 업데이트해줘"` 명령 시 flow-refiner가 interactive diff 제안. 사용자가 항목별 수락/거부 → 승인된 것만 즉시 반영. work-plan에 카드 발급 없음 (사용자의 판단 활동은 시스템이 큐잉할 대상이 아님).

**통합 원칙** (복잡도 최소화):
- gap-finder 결과 → RESEARCH(search) 또는 WRITE(modify)로 귀결 (gap 자체를 별 type으로 두지 않음)
- methodology-advisor 결과 → WRITE(create|modify)에 녹여 기재
- peer-reviewer / citation-auditor 결과 → WRITE(modify) 생성

---

## 4. 상태 전이 규칙

```
             ┌─────────────────────────────┐
             │                              ↓
[created] → 🟡 active ─→ 🔵 in-progress ─→ 🟢 completed
                ↓              ↓
           🔴 blocked     ⚪ deferred
                ↑ (의존성 미해결)
```

### 4.1 전이 트리거

| 전이 | 트리거 |
|------|--------|
| (없음) → 🟡 active | aggregator가 신규 카드 생성 시 (registry에도 status=ready 기록) |
| 🟡 active → 🔵 in-progress | 담당 명령 실행 직후, 담당 에이전트가 시작 시 |
| 🔵 → 🟢 completed | 에이전트가 작업 완료 시 (🟢 Recent completed 섹션 이동) |
| 🟢 completed → **삭제** | aggregator 다음 실행 시 RESEARCH mode=search만 work-plan에서 제거 + registry에 completed 보존. 그 외는 work-plan에 보존. |
| 🔵 → 🔴 blocked | 에이전트가 진행 불가 판정 (검색 0건, 의존성 미해결 발견 등) |
| 🔴 blocked → 🟡 active | 의존성 해소 시 자동, 또는 사용자 `"RESEARCH-005 재개해줘"` |
| 🟡/🔴 → ⚪ deferred | 사용자 `"RESEARCH-005 연기해줘"` 또는 에이전트 판단 |
| ⚪ → 🟡 | 사용자 `"RESEARCH-005 재개해줘"` |
| registry completed → 🟡 active | **Reactivation** — claim-extraction이 동일 dedup_key 재제안 시 aggregator가 자동 부활 (registry: completed→ready + work-plan 재삽입) |

### 4.2 Card registry (Single Source of Truth — 2-domain)

2개 도메인이 **각자 registry 파일을 lifecycle SSOT**로 보유. work-plan.md는 활성 view. registry가 ID 발급·dedup·이력 영속을 담당해 에이전트 race / 중복 / 손실을 차단한다.

| Card · mode | Registry 파일 | dedup_key (정규화 후) |
|-------------|--------------|---------------------|
| RESEARCH · search | `papers/.registry.json` | `(mode, *sorted_r_ids)` — covers 정규화 |
| RESEARCH · reanalyze | `papers/.registry.json` | `(mode, pdf_filename, angle)` |
| WRITE · create | `output/.registry.json` | `(mode, target_file, location)` |
| WRITE · modify | `output/.registry.json` | `(mode, target_file, target_passage)` |

모든 도메인은 단일 모듈 `scripts/card_registry.py`가 처리. domain 파라미터로 `research` / `write` 분기.

**Registry 스키마** (공통, `papers/.registry.json` 또는 `output/.registry.json`):
```json
{
  "schema_version": "2.0",
  "domain": "research",
  "card_type": "RESEARCH",
  "next_id": 16,
  "cards": {
    "RESEARCH-007": {
      "id": "RESEARCH-007",
      "mode": "search",
      "dedup_key": ["search", "r-01", "r-04"],
      "metadata": {
        "무엇": "EF 측정 혼입 요인 + impurity problem",
        "query": "executive function task impurity motivation confound",
        "source_file": "flow/claim-extraction-flow.md",
        "covers": "R-01, R-04"
      },
      "status": "ready | in_progress | blocked | deferred | completed",
      "issued_at": "2026-04-24T14:00:00",
      "completed_at": null,
      "reactivated_count": 0,
      "history": [{"at": "...", "event": "issued", "mode": "search"}, ...]
    }
  }
}
```

**중복 발급 방지**:
- 새 제안의 dedup_key가 registry의 기존 카드와 일치 (같은 mode, 같은 key) 시:
  - ready/in_progress/blocked/deferred → **skip** (CLI가 기존 ID 반환, work-plan append 금지)
  - completed → **reactivation** (status=ready + work-plan에 카드 재삽입 + 진행 로그 "reactivated")
- dedup_key 첫 원소가 `mode`이므로 다른 mode 카드끼리는 절대 충돌하지 않음 (예: search 카드와 reanalyze 카드가 같은 식별자를 써도 별개 카드).

**정규화 규칙**:
- R-ID: `R-03 (보완)` / `R-03-supplement` → `r-03`. dedup_key에서 정렬된 튜플.
- 파일명: basename + lowercase (`output/CH3.md` → `ch3.md`)
- 텍스트: 공백·구두점 collapse + lowercase
- 위치: `§`·`섹션`·`Sec.` → `section`. `¶`·`문단` → `para`

**완료 카드 보존 정책 차이**:
- RESEARCH mode=search: completed → work-plan에서 카드 **삭제**, registry에만 영속 (4-stage curation 산출물이 `papers/.curation/*.md` + `consensus-results.md`에 남음)
- 그 외 (RESEARCH reanalyze / WRITE create·modify): completed → work-plan 🟢 Recent completed에 보존, 시간 흐르면 📜 Older completed로 이동. registry status만 갱신, 카드 자체는 손대지 않음.

**CLI** (운영 조회·발급):
```bash
# 조회
python3 scripts/card_registry.py stats     CDEA research   # RESEARCH 카드 상태·mode별 카운트
python3 scripts/card_registry.py list      CDEA write      # WRITE 카드 전체 리스트
python3 scripts/card_registry.py bootstrap CDEA research   # work-plan → registry 역복원

# 에이전트 발급 (citation-auditor / peer-reviewer 등 평가 외 시점)
python3 scripts/card_registry.py issue CDEA write modify \
  --dedup-key "output/ch3.md" "EF universal claim" \
  --field "무엇=ch3 EF 보편성 over-claim" \
  --field "대상 챕터=output/ch3.md" \
  --field "원인=citation-auditor #003"
# stdout = 발급된 ID 한 줄. stderr = ✅ issued / ⏭ skip / ↻ reactivated 안내.
```

평가 완료 시의 batch 발급(claim-extractor search[] → RESEARCH, axis scorer 감점 → WRITE 등)은 `evaluation_aggregator.py`가 모듈 직접 import로 처리. CLI는 주로 평가 외 시점 단발 발급용.

### 4.3 카드 이동 절차 (에이전트가 Edit 시)

**필수 단계** (순서 준수):

1. 대상 카드 전체를 이전 섹션에서 **삭제**
2. 헤더 라인의 이모지·상태 텍스트 변경 (`🟡 active` → `🔵 in-progress` 등)
3. 진행 로그에 새 엔트리 append
4. 새 섹션 **하단**에 append (`## 🟢 Recent completed`는 **최상단**에 append — 최신순 유지)
5. 카드가 🟢 Recent completed 섹션으로 이동하면, **다음 aggregator 실행 시 자동으로**:
   - 모든 mode: registry에 `mark_completed` + `completed_at` 기록 + history 엔트리 추가
   - RESEARCH mode=search만: work-plan에서 카드 **완전 삭제** (💾 registry가 영속 이력 + 4-stage 산출물이 `consensus-results.md`·`.curation/*.md`에 남음)
   - 그 외 (RESEARCH reanalyze / WRITE create·modify): work-plan 카드 보존 (Recent → Older 자연 이동, registry는 status만 갱신)
6. 대시보드 (§5) 숫자 재계산

### 4.4 삭제 정책

- **RESEARCH mode=search**: Recent completed 이동 후 aggregator가 work-plan에서 삭제. registry가 completed 상태로 이력 영속. 실제 산출물은 `papers/consensus-results.md`·`papers/.curation/*.md`·`papers/analyzed/*.md`에 남으므로 카드를 work-plan에서 치워도 자료는 보존됨.
- **그 외 (RESEARCH reanalyze / WRITE create·modify)**: work-plan에서 삭제 없음. Recent → Older completed 자연 이동. registry가 lifecycle 영속 보존 — work-plan 파일 손상 시 `card_registry.py bootstrap`으로 역복원 가능.
- **취소**: ⚪ deferred + `note: 취소 사유`로 기록. registry도 status=deferred.

---

## 4.5 사용자 브리핑 섹션 포맷 (엄격)

**위치**: work-plan.md 최상단, `---` 구분자 직후 **대시보드보다 위**. 사용자가 파일을 열자마자 제일 먼저 봄.

**목적**: 한 곳에서 "지금 어떤 파일을 열고 / 뭘 확인하고 / 어떤 명령을 실행할지"를 즉시 알 수 있게.

### 5개 하위 섹션 (순서 고정)

```markdown
## 🧭 현재 당신이 해야 할 일

### 📖 지금 열어볼 파일
1. **`evaluations/latest/evaluation.md`** — 최근 평가 요약 (점수·심사 판정·잔여 우선순위)
2. **`evaluations/latest/axis{N}-*.md`** — 가장 낮은 축 상세 (동적)
3. **이 파일** — 🎯 다음 명령부터

### ✍️ 확인·수정 가능한 작업 파일
- `flow/flow.md` — 줄글 플랜 (수정 가능)
- `output/*.md` — 초안 (있을 때)
- `critical-questions.md` — 🎭 답변 필요 (Critical Mode일 때, 조건부)

### 🎯 지금 실행할 명령 (우선순위 순)
1. `"{command}"` — {reason, task IDs, expected recovery}
2. `"{command}"` — {...}
3. `"{command}"` — {...}

### ⚠️ 중요 알림
- 🔴 **Blocked N건** — (있을 때)
- 🎭 **Critical Mode ...** — (활성 시)
- 📈 **+N점 개선** / 📉 **-N점 하락** — (delta 있을 때)
- ✨ 🟡 Active 비어있음 — (idle 시)
- _(특이사항 없음)_

### 📚 Stage 진행 체크리스트
- [ ] **Stage 1 리서치** — {done}/{total}
- [ ] **Stage 2 초안**
- [ ] **Stage 3 수정**
- [ ] **Stage 4 최종**
```

### 렌더링 주체

`evaluation_aggregator.py`의 `render_briefing()` 함수가 유일한 생성자. 에이전트가 수동으로 이 섹션을 건드리지 말 것 — 다음 평가 시 aggregator가 덮어씀.

### 왜 이 구조인가

사용자는 work-plan.md를 열면 **3초 안에** 다음을 알 수 있어야 함:
1. 어떤 파일을 열어봐야 현재 상황을 이해하는가 (📖)
2. 어떤 파일을 내가 수정할 수 있는가 (✍️)
3. 지금 Claude에게 뭐라고 말해야 하는가 (🎯)
4. 놓치면 안 되는 것이 있는가 (⚠️)
5. 전체 여정 중 어디쯤 와 있는가 (📚)

대시보드(§5)는 **숫자·트렌드** 전용. 브리핑은 **액션**. 둘은 상호보완.

## 5. 대시보드 포맷 (엄격)

```markdown
## 📊 대시보드

### Stage 진척도
- Stage 1 리서치: {bar} {pct}% ({done}/{total})
- Stage 2 초안:   {bar} {pct}% ({done}/{total})
- Stage 3 수정:   {bar} {pct}% ({done}/{total})
- Stage 4 최종:   {bar} {pct}% ({done}/{total})

### 상태별 카운트
🟡 active: {N}  |  🔵 in-progress: {N}  |  🔴 blocked: {N}  |  🟢 completed: {N}  |  ⚪ deferred: {N}

### 축별 현재 상태
- 축 1 (레퍼런스 충실도): {emoji} {라벨}  ({active}/{total} tasks)
- 축 2 (논리 전개 완성도): {emoji} {라벨}  ({active}/{total} tasks)
- 축 3 (반박·강화 논리): {emoji} {라벨}  ({active}/{total} tasks)
- 축 4 (독창성·기여도): {emoji} {라벨}  ({active}/{total} tasks)
- 축 5 (구성개념 정의): {emoji} {라벨}  ({active}/{total} tasks)
- 축 6 (비판적 시각): {emoji} {라벨}  ({active}/{total} tasks) — Critical Mode 시에만

축 상태 emoji (axis-scorer가 직접 부여, task state emoji와 별도 column으로 의미 구분):
- 🟢 충실 / 🟡 적정 / 🟠 보강 필요 / 🔴 구조적 결함 / ⚫ 측정 불가

### 🎯 다음 권장 명령
1. `"{command}"` — {reason, task IDs}
2. `"{command}"` — {reason}
3. `"{command}"` — {reason}
```

**bar 렌더링**: 10칸 기준. 예 — `████████░░` (80%), `░░░░░░░░░░` (0%), `██████████` (100%).

**재계산 주기**:
- 모든 task 상태 전이 후 (즉시)
- `evaluation_aggregator.py` 실행 시 (평가 완료)
- `"작업 추천해줘"` 명령 시

---

## 6. ID 번호 발급 규칙

### 6.1 발급 주체 (registry 단일화)

ID 발급은 **모두 registry 모듈을 거친다**. 에이전트가 work-plan.md를 grep해서 max+1 하는 self-grep 방식 **금지** — race condition + dedup 우회 위험.

| 발급 시점 | 발급자 | 경유 |
|----------|-------|------|
| 평가 완료 시 batch 발급 (RESEARCH / WRITE) | `evaluation_aggregator.py` | 모듈 직접 import (`card_registry`) |
| 평가 외 시점 단발 발급 (citation-auditor / peer-reviewer 등) | 해당 에이전트 | `python3 scripts/card_registry.py issue` CLI |
| **사용자 자율 추가** | 사람 ↔ AI | 사용자는 자연어 채팅 또는 work-plan.md 직접 편집. AI가 받아 CLI로 정식 카드 변환 (사용자는 CLI 직접 호출 안 함) |

**사용자 자율 추가 흐름** — 사용자 인터페이스는 두 가지뿐:

1. **Claude Code 채팅 자연어 요청**:
   ```
   "ch3 Section 4 EF 보편성 강화 카드 추가해줘"
   ```
   → AI가 의도 해석 → 내부적으로 `card_registry.py issue` 호출 → work-plan에 카드 블록 추가.

2. **work-plan.md 에디터 직접 편집**:
   - 자유 메모 (`### [TODO] ...`) — AI가 다음 호출 시 정식 카드로 변환
   - 정식 카드 스키마 직접 작성 — 다음 분석 시 `bootstrap_from_work_plan`이 registry 등록

**사용자가 CLI를 직접 칠 일 없음** — `card_registry.py issue`는 AI/에이전트의 내부 도구.

### 6.2 발급 알고리즘

```python
# 의사코드 — 모든 발급 경로가 따르는 흐름
def issue(domain, mode, dedup_key, metadata):
    reg = card_registry.load(project, domain)          # research | write
    existing = card_registry.find_by_dedup_key(reg, mode, dedup_key)
    if existing:
        if reg.cards[existing].status == "completed":
            card_registry.reactivate(reg, existing)
            return existing  # work-plan에 카드 재삽입
        return existing      # 활성 상태면 skip (work-plan append 금지)
    new_id = card_registry.next_id(reg)                # f"{CARD_TYPE}-{reg.next_id:03d}"
    card_registry.add_new(reg, new_id, mode, dedup_key, metadata)
    card_registry.save(project, reg)
    return new_id            # work-plan 🟡 Active에 카드 신규 append
```

Card type별 독립 카운터 (`RESEARCH-001`, `WRITE-001`이 동시 존재 가능). mode는 dedup_key 첫 원소라 mode 간 충돌 원천 차단. dedup_key 정의는 §4.2 참조.

### 6.3 claim-extraction의 R / RESEARCH 치환

claim-extractor는 2층으로 제안한다:
- **R-NN** (Research Target, claim-level fine-grained) — UNMATCHED-EXTERNAL 문장/클러스터별
- **execution unit** (R들을 같은 쿼리로 커버 가능하게 병합) — JSON 요약의 `search[]` 배열 (mode=search 후보)

aggregator가 `search[]`를 파싱하여 `card_registry`(domain=research)로 신규 RESEARCH-NNN을 **1:1 발급** (mode=search, `covers: R-XX, R-YY` dedup_key). claim-extraction-*.md에는 R ID가 그대로 남고, 각 R 섹션에 `→ RESEARCH-NNN (work-plan)` back-reference가 추가된다. UNMATCHED-INTERNAL 섹션에서는 동일 흐름으로 mode=reanalyze 카드 발급.

---

## 7. 파싱 규칙 (에이전트가 파일 읽을 때)

### 7.1 Active task 목록 추출

```
현재 섹션: "## 🟡 Active"로 시작 → 다음 "---" 또는 "## " 전까지
카드 경계: "### [" 로 시작하는 줄이 새 카드 시작
```

### 7.2 특정 카드 ID 찾기

```
정규식: /^### \[RESEARCH-002\] / (m=multiline)   # 또는 [WRITE-NNN]
이 매치부터 다음 "### [" 전까지가 해당 카드 블록
```

### 7.3 담당 명령 추출

```
각 카드 내 "**담당 명령**:" 라인의 백틱 안 내용
```

---

## 8. 에이전트 의무 (명령 실행 사이클)

각 에이전트는 자신이 담당하는 명령에서 다음을 **반드시** 수행:

### 8.1 명령 시작 시

1. `work-plan.md` 읽기
2. 🟡 Active 섹션에서 자신이 담당하는 task 탐색 (담당 명령 필드 매칭)
3. 대상 task를 🔵 In-progress로 전환 + 진행 로그 append (`in-progress: {agent}`)

### 8.2 명령 종료 시 (성공)

1. 🔵 In-progress의 해당 task를 🟢 Recent completed로 이동
2. 진행 로그에 `✅ completed: {요약}` append
3. Recent completed overflow 처리 (15개 초과 시)
4. 대시보드 재계산

### 8.3 명령 종료 시 (실패·부분 완료)

1. 🔵 In-progress에서 🔴 Blocked (근본 문제) 또는 🟡 Active (일시 실패, 재시도 가능)로 이동
2. 진행 로그에 상세 사유 append

### 8.4 신규 task 발견 시 (평가·감사·분석 과정)

1. 해당 타입의 다음 가용 번호 발급 (§6)
2. 🟡 Active 섹션 하단에 신규 카드 append
3. 대시보드 카운트 갱신

---

## 9. 금지 사항

- ❌ Task 카드 필드 순서 바꾸기
- ❌ 진행 로그 과거 엔트리 수정·삭제
- ❌ 번호 건너뛰기 또는 중복 발급
- ❌ Task 삭제 (대신 ⚪ deferred로 이동)
- ❌ 섹션 헤더 텍스트 변경 (`## 🟡 Active` 고정)
- ❌ 이모지 변경 (상태 이모지 5종 외 사용 금지)
- ❌ 대시보드 없는 상태로 파일 저장

---

## 10. 예시 — 완전한 work-plan.md 미니 샘플

```markdown
# work-plan.md

> 📅 마지막 갱신: 2026-04-23 15:42 (eval #002 후)
> Stage: flow
> intellectual_ambition: incremental

---

## 📊 대시보드

### Stage 진척도
- Stage 1 리서치: ████████░░ 80% (4/5)
- Stage 2 초안:   ░░░░░░░░░░ 0% (0/3)
- Stage 3 수정:   ░░░░░░░░░░ 0% (0/0)
- Stage 4 최종:   ░░░░░░░░░░ 0% (0/0)

### 상태별 카운트
🟡 active: 2  |  🔵 in-progress: 0  |  🔴 blocked: 0  |  🟢 completed: 4  |  ⚪ deferred: 0

### 축별 현재 상태
- 축 1 (레퍼런스 충실도): 🟠 보강 필요  (1/1 tasks)
- 축 2 (논리 전개 완성도): 🟡 적정  (0/0 tasks)
- 축 3 (반박·강화 논리): 🟡 적정  (0/0 tasks)
- 축 4 (독창성·기여도): 🟠 보강 필요  (1/1 tasks, WRITE-001)
- 축 5 (구성개념 정의): 🟡 적정  (0/0 tasks)
- 축 6 (비판적 시각): — (Critical Mode 비활성)

### 🎯 다음 권장 명령
1. `"리서치 진행해줘"` — RESEARCH-002 (Consensus 검색 1건 대기, mode=search)
2. `"초안 작성해줘"` — WRITE-001 (Introduction "So What" 블록, mode=create)

---

## 🟡 Active

### [RESEARCH-002] 🟡 active · P1 · axis1 · Stage 1

**무엇**: EF 전통적 보편성 가정의 세미널 원전 확보

**mode**: search

**담당 명령**: `"리서치 진행해줘"` → Consensus 자동 검색 (4-stage 파이프라인)

**covers**: R-07, R-12 (EF universal cognitive history 관련 claim들)

**query**: `executive function universal cognitive history Miyake Friedman Diamond review`

**검색 키워드 / 기대 논문 프로필**: `claim-extraction-flow.md`의 R-07, R-12 섹션 참조 / registry: `papers/.registry.json`

**의존성**: 없음
**차단하는 것**: 없음

**진행 로그**:
- 2026-04-23 14:50 · created by aggregator (eval #001)


### [WRITE-001] 🟡 active · P2 · axis4 · Stage 2

**무엇**: Introduction에 "So What" 3문장 블록

**mode**: create

**담당 명령**: `"초안 작성해줘"` → writing-architect 필수 반영

**대상 챕터**: output/ch1-introduction.md
**위치**: Section 1 Introduction 문단 3
**내용 요구**:
- (a) 분야가 잃는 것 (해결 안 되면)
- (b) 이 논문이 채우는 지점
- (c) 파급 경로

**의존성**: 없음
**차단하는 것**: 없음

**진행 로그**:
- 2026-04-23 14:50 · created by axis4-originality-scorer (eval #001)


---

## 🔵 In-progress

_(없음)_

---

## 🔴 Blocked

_(없음)_

---

## 🟢 Recent completed (최근 15개)

### [RESEARCH-001] 🟢 completed · P1 · axis1 · Stage 1

**무엇**: S016 — EF 보편/특수 논쟁 최근 동향

**mode**: search

**담당 명령**: `"리서치 진행해줘"` (실행 완료)

**covers**: R-01

**query**: (생략)

**진행 로그**:
- 2026-04-23 14:50 · created by aggregator
- 2026-04-23 15:10 · in-progress: Consensus 검색
- 2026-04-23 15:25 · ✅ completed: 20 papers (Kroupin 2025, Jukes 2024, Miller 2023 핵심). consensus-results.md 참조

> ⚠️ 이 카드(mode=search)는 다음 aggregator 실행 시 work-plan에서 자동 삭제됨 (registry에 status=completed로 영속 보존). mode=reanalyze / WRITE create·modify는 work-plan에 보존됨.

---

## ⚪ Deferred

_(없음)_

---

## 📜 Older completed

_(없음 — 총 completed 15개 이하)_
```

---

## 11. 에이전트별 work-plan 의무 요약 (cross-ref)

| 에이전트 | 읽기 | 생성 | 🔵 전환 | 🟢 전환 | 🔴 전환 |
|----------|------|------|----------|---------|---------|
| **evaluation-orchestrator** | — | (aggregator 경유) | — | — | — |
| **evaluation_aggregator.py** | 대시보드 재계산용 | ✅ RESEARCH · WRITE | — | — | — |
| **claim-extractor** | 기존 RESEARCH 번호 확인 | (PROPOSAL만) | — | — | — |
| **paper-processing-orchestrator** | 🟡 RESEARCH(search) 매칭 | — | ✅ | ✅ (MATCHED 발생 시) | — |
| **writing-architect** | 🟡 WRITE(create) 전체 | — | ✅ | ✅ | — |
| **chapter-editor** | 🟡 WRITE(modify) 해당 챕터 | — | ✅ | ✅ | — |
| **flow-refiner** | — (in-session helper, 카드 없음) | — | — | — | — |
| **citation-auditor** | — | ✅ WRITE(modify) — over-claim 시 `card_registry issue` | — | — | — |
| **peer-reviewer** | — | ✅ WRITE(modify) — reviewer Major 이슈 | — | — | — |
| **gap-finder** | — | ✅ RESEARCH(search) 또는 WRITE(modify) | — | — | — |
| **methodology-advisor** | — | ✅ WRITE(create 또는 modify)에 녹임 | — | — | — |

**flow-refiner 예외**: `flow.md` 수정은 사용자 판단 활동이라 카드로 큐잉하지 않음. 사용자 명령 시 interactive diff 제안 → 승인 → 즉시 반영 → claim-extractor 자동 재실행 (후속 RESEARCH 카드는 aggregator가 발급). 정책은 §3의 "카드가 아닌 것" 섹션 참조.
