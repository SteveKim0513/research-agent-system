# WORK-PLAN-FORMAT.md — work-plan.md 포맷 규율

> 이 문서는 `projects/{P}/work-plan.md`의 **엄격한 포맷 스펙**입니다. 모든 에이전트(evaluation-orchestrator, claim-extractor, writing-architect, chapter-editor, flow-refiner, paper-processing-orchestrator, evaluation_aggregator)가 work-plan을 읽고 쓸 때 이 파일의 규칙을 준수해야 합니다.
>
> **이 포맷을 지키는 이유**: 에이전트들이 각자 포맷을 해석하면 섹션이 깨지거나 번호가 엇갈립니다. 단일 source of truth + grep/regex로 파싱 가능한 구조가 자동화의 전제.

---

## 1. 파일 전체 구조

```markdown
# work-plan.md

> 📅 마지막 갱신: YYYY-MM-DD HH:MM ({trigger})
> Stage: {flow | v1-draft | revised | final}
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
### [HUNT-002] 🟡 active · P1 · axis1 · Stage 1

**무엇**: S017 — EF 전통적 보편성 가정

**담당 명령**: `"작업 시작해줘"` → Consensus 자동 검색

**예상 회복**: 축 1-1 +3

**검색 키워드**:
- `executive function universal cognitive history`
- `Miyake Friedman definition`
- `Diamond EF review`

**의존성**: 없음
**차단하는 것**: DRAFT-001 (축 1 재평가 후 "So What" 작성 가능)

**진행 로그**:
- 2026-04-23 15:00 · created by aggregator (eval #001, claim-extraction-flow.md:S017)
```

### 2.1 필수 필드

| 필드 | 형식 | 예시 | 필수 |
|------|------|------|------|
| **헤더 라인 (기본)** | `### [TYPE-NNN] {상태이모지} {상태텍스트} · {axis} · Stage {N}` | `### [HUNT-002] 🟡 active · axis1 · Stage 1` | ✅ |
| **헤더 라인 (priority 포함)** | 위 + `P{1\|2\|3}` 태그 (axis 앞) | `### [HUNT-002] 🟡 active · P1 · axis1 · Stage 1` | 선택 (대시보드 권장 명령 정렬에 활용) |
| **무엇** | `**무엇**: {1줄 설명}` | `**무엇**: S017 — EF 전통적 보편성 가정` |
| **담당 명령** | `**담당 명령**: \`"..."\` → {후속 동작}` | `**담당 명령**: "작업 시작해줘" → Consensus 자동 검색` |
| **예상 회복** | `**예상 회복**: {축-하위} +{N}` 또는 `—` | `**예상 회복**: 축 1-1 +3` |
| **진행 로그** | `**진행 로그**:` 아래 bullet list | (예시 참조) |

### 2.2 Task 타입별 추가 필드

- **HUNT** (execution unit — 1 카드 = 1 Consensus 쿼리): `**covers**:` (필수, R-ID 리스트. claim-extractor가 제안한 R 중 이 HUNT가 커버하는 것들. 예: `R-01, R-04`), `**query**:` (필수, 통합 대표 쿼리 단일 문자열), `**검색 키워드**:` (선택, bullet 3-5개 — query 대표성 낮을 때 보조), `**기대 논문 프로필**:` (유형/시대/저널)
- **REANALYZE**: `**대상 PDF**:` (파일명), `**재분석 각도**:` (어느 섹션·주장)
- **DRAFT**: `**위치**:` (Section N·문단), `**내용 요구**:` (구체 구조)
- **EDIT**: `**대상 챕터**:` (파일명), `**수정 내용**:` (구체), `**원인**:` (어느 평가·감사 결과)
- **FIX**: `**대상 위치**:` (flow.md Section N 문단), `**현재 텍스트**:` (인용), `**제안 텍스트**:` (대체)

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

## 3. Task 타입 5종 (담당 명령 1:1)

| Type | 생성자 | 담당 해결 명령 | 담당 에이전트 |
|------|--------|--------------|--------------|
| **HUNT** | claim-extractor (UNMATCHED-EXTERNAL) | `"작업 시작해줘"` | Consensus MCP 직접 검색 |
| **REANALYZE** | claim-extractor (UNMATCHED-INTERNAL), flow-refiner | `"논문 재분석해줘"` (delta 기본) | paper-analyst Mode B |
| **DRAFT** | axis2~5 scorers, flow-refiner | `"초안 작성해줘"` / `"Chapter X 수정해줘"` | writing-architect / chapter-editor |
| **EDIT** | citation-auditor, peer-reviewer, axis3·4·6 scorers | `"Chapter X 수정해줘: EDIT-NNN"` | chapter-editor |
| **FIX** | flow-refiner | `"flow 업데이트해줘"` | flow-refiner (diff 승인) |

**통합 원칙** (복잡도 최소화):
- gap-finder 결과 → HUNT 또는 EDIT로 귀결 (gap 자체를 별 type으로 두지 않음)
- methodology-advisor 결과 → DRAFT 또는 EDIT에 녹여 기재
- peer-reviewer / citation-auditor 결과 → EDIT 생성

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
| (없음) → 🟡 active | aggregator가 신규 task 생성 시 |
| 🟡 active → 🔵 in-progress | 담당 명령 실행 직후, 담당 에이전트가 시작 시 |
| 🔵 → 🟢 completed | 에이전트가 작업 완료 시 |
| 🔵 → 🔴 blocked | 에이전트가 진행 불가 판정 (검색 0건, 의존성 미해결 발견 등) |
| 🔴 blocked → 🟡 active | 의존성 해소 시 자동, 또는 사용자 `"HUNT-005 재개해줘"` |
| 🟡/🔴 → ⚪ deferred | 사용자 `"HUNT-005 연기해줘"` 또는 에이전트 판단 |
| ⚪ → 🟡 | 사용자 `"HUNT-005 재개해줘"` |
| 🟢 → 📜 Older completed | Recent completed 16번째부터 (오래된 것부터 밀림) |

### 4.2 카드 이동 절차 (에이전트가 Edit 시)

**필수 단계** (순서 준수):

1. 대상 카드 전체를 이전 섹션에서 **삭제**
2. 헤더 라인의 이모지·상태 텍스트 변경 (`🟡 active` → `🔵 in-progress` 등)
3. 진행 로그에 새 엔트리 append
4. 새 섹션 **하단**에 append (`## 🟢 Recent completed`는 **최상단**에 append — 최신순 유지)
5. Recent completed가 15개 초과 시 가장 오래된 1개를 `## 📜 Older completed` **상단**에 이동
6. 대시보드 (§5) 숫자 재계산

### 4.3 삭제 금지

Task는 **절대 삭제되지 않음**. 취소도 ⚪ deferred + `note: 취소 사유`로 기록. 이력 영속.

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
- `chapters/*.md` — 초안 (있을 때)
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

### 축별 잔여 회복 잠재력 (예상)
- 축 1: +{N}  ({M} tasks)
- 축 2: +{N}  ({M} tasks)
- 축 3: +{N}  ({M} tasks)
- 축 4: +{N}  ({M} tasks)
- 축 5: +{N}  ({M} tasks)
- 축 6: +{N}  ({M} tasks)

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

### 6.1 발급 주체

`evaluation_aggregator.py`가 **유일한 발급처**. 에이전트가 직접 번호를 생성하지 않음.

예외: 긴급 수동 task (사용자가 직접 추가)는 다음 가용 번호를 사용.

### 6.2 발급 알고리즘

```
1. 기존 work-plan.md에서 해당 TYPE의 모든 번호를 grep:
   grep -oE "\[TYPE-[0-9]+\]" work-plan.md | sort -u
2. 최대값을 찾고 +1을 부여
3. TYPE별로 독립 카운터 (HUNT-001, DRAFT-001이 동시 존재 가능)
```

### 6.3 claim-extraction의 R / HUNT 치환

claim-extractor는 2층으로 제안한다:
- **R-NN** (Research Target, claim-level fine-grained) — UNMATCHED-EXTERNAL 문장/클러스터별
- **HUNT-NN** (execution unit, R들을 같은 쿼리로 커버 가능하게 병합) — JSON 요약의 `hunts[]` 배열

aggregator가 `hunts[]`를 파싱하여 work-plan.md에 신규 HUNT-NNN 카드를 **1:1 발급** (`covers: R-XX, R-YY` 필드 주입). claim-extraction-*.md에는 R ID가 그대로 남고, 각 R 섹션에 `→ HUNT-NNN (work-plan)` back-reference가 추가된다.

---

## 7. 파싱 규칙 (에이전트가 파일 읽을 때)

### 7.1 Active task 목록 추출

```
현재 섹션: "## 🟡 Active"로 시작 → 다음 "---" 또는 "## " 전까지
카드 경계: "### [" 로 시작하는 줄이 새 카드 시작
```

### 7.2 특정 task ID 찾기

```
정규식: /^### \[HUNT-002\] / (m=multiline)
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

### 축별 잔여 회복 잠재력 (예상)
- 축 1: +3  (1 tasks)
- 축 2: +0
- 축 3: +0
- 축 4: +8  (1 task, DRAFT-001)
- 축 5: +0
- 축 6: +0

### 🎯 다음 권장 명령
1. `"작업 시작해줘"` — HUNT-002 (Consensus 검색 1건 대기)
2. `"초안 작성해줘"` — DRAFT-001 (Introduction "So What" 블록)

---

## 🟡 Active

### [HUNT-002] 🟡 active · P1 · axis1 · Stage 1

**무엇**: EF 전통적 보편성 가정의 세미널 원전 확보

**담당 명령**: `"작업 시작해줘"` → Consensus 자동 검색

**예상 회복**: 축 1-1 +3

**covers**: R-07, R-12 (EF universal cognitive history 관련 claim들)

**query**: `executive function universal cognitive history Miyake Friedman Diamond review`

**검색 키워드**:
- `executive function universal cognitive history`
- `Miyake Friedman definition`
- `Diamond EF review`

**기대 논문 프로필**:
- 유형: 세미널 정의 논문 + 최신 리뷰
- 최소 필요 논문: 2-3편

**의존성**: 없음
**차단하는 것**: 없음

**진행 로그**:
- 2026-04-23 14:50 · created by aggregator (eval #001)


### [DRAFT-001] 🟡 active · P2 · axis4 · Stage 2

**무엇**: Introduction에 "So What" 3문장 블록

**담당 명령**: `"초안 작성해줘"` → writing-architect 필수 반영

**예상 회복**: 축 4-1 +8

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

### [HUNT-001] 🟢 completed · P1 · axis1 · Stage 1

**무엇**: S016 — EF 보편/특수 논쟁 최근 동향

**담당 명령**: `"작업 시작해줘"` (실행 완료)

**예상 회복**: 축 1-1 +3 → **실측 +4** (MATCHED 4편 확보)

**검색 키워드**: (생략)

**진행 로그**:
- 2026-04-23 14:50 · created by aggregator
- 2026-04-23 15:10 · in-progress: Consensus 검색
- 2026-04-23 15:25 · ✅ completed: 20 papers (Kroupin 2025, Jukes 2024, Miller 2023 핵심). consensus-results.md 참조

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
| **evaluation_aggregator.py** | 대시보드 재계산용 | ✅ HUNT·REANALYZE·DRAFT·EDIT | — | — | — |
| **claim-extractor** | 기존 HUNT 번호 확인 | (PROPOSAL만) | — | — | — |
| **paper-processing-orchestrator** | 🟡 HUNT 매칭 | — | ✅ | ✅ (MATCHED 발생 시) | — |
| **writing-architect** | 🟡 DRAFT 전체 | — | ✅ | ✅ | — |
| **chapter-editor** | 🟡 EDIT (해당 챕터) | — | ✅ | ✅ | — |
| **flow-refiner** | 🟡 FIX | (승인 반영 시 FIX 추가 생성) | ✅ | ✅ | — |
| **citation-auditor** | — | ✅ EDIT (over-claim 발견 시) | — | — | — |
| **peer-reviewer** | — | ✅ EDIT (reviewer major 이슈) | — | — | — |
| **gap-finder** | — | ✅ HUNT 또는 EDIT | — | — | — |
| **methodology-advisor** | — | ✅ DRAFT 또는 EDIT | — | — | — |
