# Research Agent — 사용 가이드

**이 가이드의 목표**: 시스템 작동 모델 + 사용자가 칠 명령어 9종 + 첫 프로젝트 워크플로.

복잡한 원리·아키텍처는 [MANUAL.md](./MANUAL.md), 설계 철학은 [PRINCIPLES.md](./PRINCIPLES.md).

---

## 1. ⚡ 1분 시작

```bash
cd ~/Documents/research-agent
claude
```

세션 안에서 자연어 명령으로 작업. Claude Code가 인터페이스 + 실행 엔진.

설치가 안 됐으면 [README.md § 설치](./README.md#-설치).

---

## 2. 🧠 핵심 모델 — 두 단계, 두 분석, 두 카드

이 시스템은 **선형 레시피가 아니라 루프**입니다.

### 두 단계 (stage)

| Stage | 폴더 | 역할 |
|-------|------|------|
| **flow** | `projects/{P}/flow/` | 연구 방향·논증 줄거리 (계획) |
| **output** | `projects/{P}/output/` | 실제 결과물 원고 |

각 stage는 **self-contained** — 본문 + 분석 결과 + 평가 결과 + critical을 자기 폴더에 보관 (모든 과거 버전은 별도 `history/` 폴더로 일괄 관리).

### 폴더 구조 한눈

```
projects/{P}/
├── flow/                            계획 단계
│   ├── flow.md
│   ├── claim-extraction-flow.md     레퍼런스 분석 결과
│   ├── evaluations/                 ← 최신만 (axis1~6 + evaluation.md)
│   └── critical/                    ← Critical Mode 활성 시
│
├── output/                          결과물 단계
│   ├── *.md
│   ├── claim-extraction-output.md
│   ├── evaluations/                 ← 최신만
│   ├── critical/
│   └── .registry.json               WRITE 카드 SSOT
│
├── papers/
│   ├── candidates/  collected/  analyzed/
│   ├── .research-raw/ .translations/ .curation/
│   ├── consensus-results.md
│   └── .registry.json               RESEARCH 카드 SSOT
│
├── history/                         ← 모든 history 통합 (stage·type별)
│   ├── flow/
│   │   ├── body/                    flow.md 본문 변경
│   │   ├── evaluations/             평가 스냅샷
│   │   ├── claim-extraction/        레퍼런스 분석 스냅샷
│   │   └── critical/                critical 답변 변경
│   ├── output/
│   │   ├── body/                    output/*.md 본문 변경
│   │   ├── evaluations/
│   │   ├── claim-extraction/
│   │   └── critical/
│   └── work-plan/                   work-plan.md 스냅샷
│
├── work-plan.md                     활성 카드 대시보드
└── activity.log
```

**원칙**: stage 폴더는 "최신 결과만". 과거 버전은 모두 `history/{stage}/{type}/`에 모임.

### 파일 버전 + 싱크 체크

각 산출물 파일 상단에 YAML frontmatter로 버전 정보:

```yaml
---
version: 3
content_hash: a3f8b9c
based_on:
  flow: 3              # flow.md v3을 기준으로 만들어졌음
  claim-extraction: 2
updated_at: 2026-04-24T17:00:00
updated_by: claim-extractor
---
```

**자동 동작**:
- 사용자가 `flow.md` 편집 → 다음 명령 실행 시 시스템이 hash 변경 감지 → `version` 자동 increment
- **이전 버전은 자동 백업** → `history/{stage}/{type}/{NNN}-{date}-v{이전}-pre-bump/`에 사본 보존 (실수로 큰 변경한 경우 복구 가능)
- 시스템이 `claim-extraction-flow.md` 갱신 → `based_on: { flow: 3 }` 자동 기록 + 이전 버전 history에 백업
- 만약 사용자가 다시 flow.md 수정 → `flow.md` v4가 됨 → `claim-extraction-flow.md`는 `based_on.flow=3`이라 **stale 표시**
- 분석 명령(레퍼런스/내용) 실행 시 stale이면 시스템이 **자동 선행 갱신**

`"버전 체크"`로 언제든지 모든 파일의 sync 상태 한눈 확인.

**자동 백업 매핑**:

| 변경 파일 | history 백업 위치 |
|---------|-----------------|
| `flow/flow.md` | `history/flow/body/{NNN}-{date}-v{이전}-pre-bump/flow.md` |
| `flow/claim-extraction-flow.md` | `history/flow/claim-extraction/{NNN}-...` |
| `flow/evaluations/axis*.md`, `evaluation.md` | `history/flow/evaluations/{NNN}-...` |
| `flow/critical/*.md` | `history/flow/critical/{NNN}-...` |
| `output/{파일명}.md` | `history/output/body/{파일명}/{NNN}-...` |
| `output/claim-extraction-output.md` | `history/output/claim-extraction/{NNN}-...` |
| `output/evaluations/*.md` | `history/output/evaluations/{NNN}-...` |
| `output/critical/*.md` | `history/output/critical/{NNN}-...` |

→ 모든 버전 변경이 자동 추적됨. 사용자는 따로 백업 신경 쓸 필요 없음.

### 두 분석 종류

| 분석 | 대상 축 | 산출물 | 발급 카드 |
|------|--------|-------|----------|
| **레퍼런스 분석** | 축 1 (문장↔논문 매칭) | claim-extraction · axis1 평가 | RESEARCH (search/reanalyze) |
| **내용 분석** | 축 2~6 (논리·반박·독창성·정의·비판) | axis2~6 평가 | WRITE (create/modify) |

두 분석은 **독립**. 사용자가 필요한 것만 선택 호출.

### 두 카드 종류

| 카드 | Registry | 실행 명령 |
|------|---------|----------|
| **RESEARCH** | `papers/.registry.json` | `"리서치 진행해줘"` |
| **WRITE** | `output/.registry.json` | `"초안 작성해줘"` / `"output {파일명} 수정해줘: WRITE-NNN"` |

### 전체 루프

```
        ┌── flow.md 작성 (사용자) ──────────────┐
        ↓                                       │
   "flow 레퍼런스 분석해줘"   →  RESEARCH 카드   │
   "flow 내용 분석해줘"       →  WRITE 카드     │
        ↓                                       │
   "리서치 진행해줘"          →  papers/        │
   사용자 PDF 선별 → candidates/                │
   "논문 처리해줘"            →  analyzed/      │
        ↓                                       │
   "초안 작성해줘"            →  output/*.md    │
        ↓                                       │
   "output 레퍼런스 분석해줘"   ←──── 반복 ─────┤
   "output 내용 분석해줘"                       │
        ↓                                       │
   "output {파일명} 수정해줘"                   │
        └───────────────────────────────────────┘
```

### 핵심 파일 4개

| 파일 | 역할 | 언제 보나 |
|------|------|----------|
| `projects/{P}/flow/flow.md` | 연구 방향 (자유 줄글) | 방향 바꿀 때 |
| `projects/{P}/work-plan.md` | **할 일 대시보드** (전체 카드) | **매 세션마다** |
| `projects/{P}/flow/evaluations/latest/evaluation.md` | flow 평가 결과 | 분석 직후 |
| `projects/{P}/output/evaluations/latest/evaluation.md` | output 평가 결과 | 분석 직후 |

---

## 3. 📜 명령어 9종 (전체)

명령어는 **prefix(`flow` 또는 `output`) + 분석 종류 + 동사** 조합. 동사는 **`분석해줘` ≡ `평가해줘`**(혼용).

### 분석 (4종)

| 명령어 | 동작 |
|--------|------|
| `"flow 레퍼런스 분석해줘"` ≡ `"flow 레퍼런스 평가해줘"` | flow 문장 분석 + axis1 + RESEARCH 카드 |
| `"flow 내용 분석해줘"` ≡ `"flow 내용 평가해줘"` | flow axis2~6 + WRITE 카드 |
| `"output 레퍼런스 분석해줘"` ≡ `"output 레퍼런스 평가해줘"` | output 문장 분석 + axis1 + RESEARCH 카드 |
| `"output 내용 분석해줘"` ≡ `"output 내용 평가해줘"` | output axis2~6 + WRITE 카드 |

### 실행 (4종)

| 명령어 | 동작 |
|--------|------|
| `"리서치 진행해줘"` | work-plan의 활성 RESEARCH 카드 일괄 실행 |
| `"논문 처리해줘"` | candidates/*.pdf → triage → Tier 1/2/3 분석 |
| `"초안 작성해줘"` | flow → output/*.md 신규 작성 (WRITE create) |
| `"output {파일명} 수정해줘: WRITE-NNN"` | WRITE modify 카드 처리 |

### 메타 (4종)

| 명령어 | 동작 |
|--------|------|
| `"flow 모드"` / `"output 모드"` | 현재 모드 전환 (prefix 생략 명령에 적용됨) |
| `"현재 모드"` | 현재 모드만 빠르게 출력 |
| `"현재 상태"` | 폴더 상태·진행도·모드·버전/싱크 한눈 출력 |
| `"버전 체크"` | 모든 파일 frontmatter version + based_on sync 검증 |

### 모드 동작

**한 번 모드를 정해두면 prefix 없이 명령어 사용 가능**:

```
"flow 모드"                  ← 한 번 설정
"레퍼런스 분석해줘"             ← flow 적용
"내용 분석해줘"               ← flow 적용
"크리티컬 모드 켜줘"            ← flow/critical/ 활성

"output 모드"                ← 모드 전환
"레퍼런스 분석해줘"             ← 이제 output 적용
```

**prefix 명시는 모드 무시 (override)**:
```
"flow 모드"
"output 레퍼런스 분석해줘"     ← 모드는 flow지만 output 적용 (명시 우선)
```

### Critical 모드 (선택)

| 명령어 | 동작 |
|--------|------|
| `"flow 크리티컬 모드 켜줘"` | `flow/critical/` 폴더 생성 + critical-companion 호출 |
| `"output 크리티컬 모드 켜줘"` | `output/critical/` 폴더 생성 |

### Flow 보강 (사용자 선택)

| 명령어 | 동작 |
|--------|------|
| `"flow 업데이트해줘"` | flow-refiner의 interactive diff 제안 → 사용자 승인 → 즉시 반영 (카드 없음) |

### ❌ 금지

- `"평가해줘"` (prefix 없음) — 단계를 명시해주세요 안내가 뜸
- 폴더명을 다른 이름으로 부르기 — `chapters`, `manuscript` 등 구 명칭 인식 안 됨

---

## 4. 🚀 첫 프로젝트 워크플로 (End-to-End)

### ① 프로젝트 생성

```
"my-essay 프로젝트 만들어줘"
```

→ `projects/my-essay/` 자동 생성.

### ② flow.md 작성 (자유 줄글)

`projects/my-essay/flow/flow.md`를 에디터로 열고 **줄글**로 작성.

**필수 2가지**:
- 연구 질문 한 문장: `"이 글은 X를 묻는다"`
- 핵심 주장 한 문장: `"본 에세이는 Y라고 주장한다"`

**권장 구조**: 문제 → 기존 관점 비판 → 자기 제안 → 예상 반론 → 함의

체크박스·목차 형식 **금지**. 줄글만.

### ③ flow 분석 (두 번 — 레퍼런스 + 내용)

```
"flow 레퍼런스 분석해줘"
```

생성:
- `flow/claim-extraction-flow.md` — 문장 단위 분류 + R 목록
- `flow/evaluations/latest/axis1-reference.md`
- `work-plan.md`에 RESEARCH 카드 추가

```
"flow 내용 분석해줘"
```

생성:
- `flow/evaluations/latest/axis{2-6}-*.md`
- `flow/evaluations/latest/evaluation.md` (roll-up)
- `work-plan.md`에 WRITE 카드 추가 (axis 감점 사유 기반)

### ④ 리서치

```
"리서치 진행해줘"
```

→ work-plan의 활성 RESEARCH 카드를 Consensus에 순차 검색.
→ `papers/consensus-results.md`에 6 카테고리(🎯 최우선 / 🟢 보조 / 🔴 Steelman / 🌏 발달·횡문화 / ⚙️ 방법론 / 🔗 Cross-RESEARCH) 큐레이션.
→ 각 논문에 영어 abstract 한글 전체 번역.

**사용자 작업**: consensus-results.md를 읽고 필요한 PDF를 `papers/candidates/`에 넣기.

```
"논문 처리해줘"
```

→ candidates/ PDF를 triage(haiku) + Tier 1/2/3별 deep-dive 분석.
→ `papers/analyzed/*-analysis.md` 생성.

### ⑤ 초안 작성

```
"초안 작성해줘"
```

→ Phase 1: 구조 설계(사용자 승인 필요) → Phase 2: `output/*.md` 생성.

stage가 자동으로 **output**로 전환됨.

### ⑥ output 분석 → 수정 반복

```
"output 레퍼런스 분석해줘"   ← output 본문 인용 정확성·매칭
"output 내용 분석해줘"       ← output 논리·독창성 등 5축
```

work-plan에 WRITE(modify) 카드가 생기면:

```
"output ch3.md 수정해줘: WRITE-007"
```

→ output-editor가 카드 지시대로 수정 + citation-auditor 자동 체이닝.

**반복**: 수정 → output 재분석 → 새 카드 → 수정.

### ⑦ 최종 통합 + 리뷰

```
"최종 통합해줘"     ← output → final/*.md + .docx
"리뷰 체크해줘"     ← peer-reviewer 시뮬레이션
"리뷰 답변 도와줘: [리뷰 텍스트]"     ← 실제 리뷰 받았을 때
```

---

## 5. 🔁 반복 루프 — 두 번째 세션부터

매 세션 표준 시작:

```
1. "현재 상태"   ← 어디까지 했는지 한눈 확인
2. work-plan.md 열기 → 🧭 브리핑 + 🎯 권장 명령 확인
3. 권장 명령 위에서부터 실행
```

**뭘 할지 모르겠으면**:
```
"작업 추천해줘"
```
→ 정체 구간 탈출용.

### work-plan의 task 타입별 담당 명령

| 카드 타입 | 의미 | 담당 명령 |
|----------|------|----------|
| **RESEARCH-NNN** | 누락된 근거 논문 찾기 | `"리서치 진행해줘"` |
| **RESEARCH-NNN (mode=reanalyze)** | 기존 PDF를 새 각도로 재분석 | `"논문 재분석해줘"` |
| **WRITE-NNN (mode=create)** | 초안 생성 | `"초안 작성해줘"` |
| **WRITE-NNN (mode=modify)** | 챕터 수정 지시 | `"output {파일명} 수정해줘: WRITE-NNN"` |

(flow 수정은 카드로 관리되지 않음 — 사용자가 `"flow 업데이트해줘"` 호출 시 flow-refiner가 interactive diff로 처리)

각 카드에는 `**covers**: R-NN` 필드(mode=search의 경우)가 있어 어떤 claim을 커버하는지 명시합니다. 우선순위는 work-plan 대시보드의 "🎯 다음 권장 명령" 섹션이 자동 정렬해줍니다. 👉 **위에서부터 처리**.

### 재평가는 언제?

- Stage 1(리서치) 끝 → `"레퍼런스 점검해줘"` (경량, 축 1만)
- Stage 2(초안) 끝 → `"flow 레퍼런스 분석해줘" / "flow 내용 분석해줘"` (전체)
- Stage 3(수정) 끝 → `"flow 레퍼런스 분석해줘" / "flow 내용 분석해줘"` (전체)
- Stage 4(최종) 직전 → `"flow 레퍼런스 분석해줘" / "flow 내용 분석해줘"` (전체 + citation 전량 감사)

중간에 재평가 남발은 피하세요 — delta가 움직이지 않는 재계산은 토큰만 소모.

---

## 6. 📖 산출물 읽는 법

시스템이 생성하는 파일 셋을 정확히 읽을 수 있어야 제대로 활용 가능합니다.

### `{stage}/evaluations/latest/evaluation.md` — 평가 진단

```
🩺 종합 판정: 🟠 Major Revision
근거: 🔴 구조적 결함 1축 (axis1)

| 축 | 이름 | 상태 | 이전 → 현재 | 핵심 진단 |
|---|------|------|------|----------|
| 1 | 레퍼런스 충실도 | 🔴 구조적 결함 | (첫 평가) | MATCHED 0편 — RESEARCH 15건 발급 |
| 2 | 논리 전개 | 🟡 적정 | (첫 평가) | thesis 산만 |
...

🚨 Critical Issues (이번 평가에서 가장 시급)
- [축 1] RESEARCH-001~015 즉시 실행
- [축 5] EF·hot/cool·규칙 깊이 정의 + 조작화 부재
```

**보는 법**:
- **메인 시그널**: 카테고리 (🟢🟡🟠🔴⚫) + 핵심 진단 + Critical Issues. 카테고리는 axis-scorer가 직접 판정.
- **카테고리 5단계**: 🟢 충실 / 🟡 적정 / 🟠 보강 필요 / 🔴 구조적 결함 / ⚫ 측정 불가
- **종합 판정 (verdict roll-up)**:
  - 🔴 **Reject**: ≥2축 🔴 OR (axis1+axis5 둘 다 🔴) OR ≥3축 ⚫
  - 🟠 **Major Revision**: ≥1축 🔴 OR ≥3축 🟠
  - 🟡 **Revise & Resubmit**: ≥2축 🟠 OR ≥1축 ⚫
  - 🟢 **Accept**: 모든 축 ≥ 🟡, 🔴/⚫ 0
- **점수는 보조**: `<details>` 안에 trend tracking용으로 보존. **절대 판정·등급 산출에 사용 금지** (LLM 채점 noise ±10점).

### 축별 상세 `axis{N}-*.md`

각 축의 **상태 카테고리 + 핵심 진단 + Critical Issues + sub-criteria 4개 카테고리**가 메인. 점수는 `<details>` 접이식 안에. 진단이 **actionable**(구체 문장·위치)로 적혀있어야 좋은 평가. 예를 들어 축 1 진단에 "S017에 레퍼런스 없음"이 있으면 그 문장이 work-plan의 RESEARCH-XXX로 자동 발급.

**0-State 규칙**: 측정 데이터가 부재 (예: 첫 평가, MATCHED 0편)이면 sub-criteria가 ⚫ 측정 불가로 표기. 잠정 만점·N/A 보류 금지.

### `work-plan.md` — 대시보드

```
> 📅 마지막 갱신: 2026-04-24 15:00 (평가 #003)
> Stage: v1
> intellectual_ambition: critical

## 🧭 현재 당신이 해야 할 일
{시스템이 쓴 한 문단 브리핑}

## 📊 대시보드
{우선순위 상위 3-5개 명령 리스트}

## 🟡 Active / 🔵 In-progress / 🔴 Blocked / 🟢 Recent completed / ⚪ Deferred
{각 섹션에 task 카드들}
```

**보는 법**:
- `**담당 명령**`을 그대로 복사해서 Claude에 붙여넣기.
- `**covers**: R-01, R-04` — 이 RESEARCH 카드가 어느 claim을 커버하는지. registry dedup의 key.
- `**query**: \`...\`` — Consensus 검색 통합 쿼리.
- `**의존성**` — 선행 완료 필요한 카드 ID.
- 대시보드 "축별 현재 상태" — 각 축의 카테고리(🟢🟡🟠🔴⚫)와 active task 수.
- 포맷 엄격 스펙: [WORK-PLAN-FORMAT.md](./skills/WORK-PLAN-FORMAT.md).
- RESEARCH 영속 이력: `.search-registry.json` (work-plan은 활성 view, registry가 SSOT).

### `activity.log` — 시계열 기록

```
[2026-04-24 15:00] 평가 완료 | v1 | - | - | ref:eval-003 | agents:evaluation-orchestrator,axis1-5 | verdict=Major Revision categories=Crit:1,Need:3,Adeq:1
```

- 모든 명령이 자동 기록(Claude Code hooks).
- 라인 복사해서 `"이 시점 X 보여줘"`로 **time-travel archive 조회** (읽기 전용).

### `papers/consensus-results.md` — 리서치 큐레이션

카드별로 6 카테고리 블록 + 각 논문에 **한글 abstract 번역 인용블록** + 📌 액션 아이템.

- 파일 끝 누적 요약(🏆 최중요 / 📥 PDF 우선순위 / 🔗 Cross-RESEARCH 교차표)부터 보세요 — 5분에 전체 파악.

---

## 7. 🗂 명령어 맵 (의사결정 기준)

**언제 쓰는가** 기준으로 재분류. 단순 목록은 `"명령어 보여줘"`로도 확인 가능.

### 🏁 언제든 (상태 관리)

| 명령 | 용도 |
|------|------|
| `"작업 추천해줘"` | **뭘 해야 할지 모를 때** — 로그·work-plan 기반 다음 명령 제안 |
| `"sync 확인해줘"` | 아티팩트 동기화 상태 점검 + 해결 가이드 |
| `"flow 레퍼런스 분석해줘" / "flow 내용 분석해줘"` | 현재 stage에 맞는 평가 자동 분기 |

### 📝 flow 작성/갱신 단계

| 명령 | 시점 |
|------|------|
| `"[이름] 프로젝트 만들어줘"` | 새 프로젝트 |
| `"flow 레퍼런스 분석해줘" / "flow 내용 분석해줘"` | flow 첫 작성 후 |
| `"flow 업데이트해줘"` | 논문 수집 후 flow.md를 다듬고 싶을 때 |
| `"비판 모드 critical로 설정해줘"` | Oxford·ENS 스타일 비판적 시각을 원할 때 (선택) |

### 🔬 리서치 단계

| 명령 | 시점 |
|------|------|
| `"리서치 진행해줘"` | work-plan의 RESEARCH 자동 실행 |
| `"새 논문 처리해줘"` | candidates/에 PDF를 넣은 뒤 |
| `"레퍼런스 점검해줘"` | 리서치 직후 축 1만 경량 재평가 |
| `"논문 재분석해줘"` | flow가 바뀌어 기존 PDF를 새 각도로 스캔 |
| `"논문 제거해줘: {파일명}"` | 철회된 논문 안전 이동 + dangling citation 탐지 |

### ✍️ 초안·수정 단계

| 명령 | 시점 |
|------|------|
| `"초안 작성해줘"` | Phase 1 구조 설계 → 승인 → Phase 2 초안 |
| `"output {파일명} 수정해줘: ..."` | 챕터 부분 수정 + 자동 citation 감사 |
| `"flow 레퍼런스 분석해줘" / "flow 내용 분석해줘"` | 초안/수정 직후 delta 추적 |

### 📦 최종 단계

| 명령 | 시점 |
|------|------|
| `"최종 통합해줘"` | chapters → final/*.md + .docx 재빌드 |
| `"리뷰 체크해줘"` | peer-reviewer 3-4명 심사 시뮬 |
| `"리뷰 답변 도와줘: [리뷰 텍스트]"` | 실제 심사 대응 전략 + 답변 초안 |

### 🔍 심층 평가 (개별 축)

| 명령 | 축 |
|------|----|
| `"독창성 평가해줘"` | 축 4 — "So What?" + Novelty Delta Map |
| `"정의 정밀도 평가해줘"` | 축 5 — 구성개념 정의 감사 |
| `"비판적 시각 평가해줘"` | 축 6 — Critical Mode 전용 |

### 🛠 보조 도구

| 명령 | 용도 |
|------|------|
| `"gap 분석해줘"` | 분야의 빈틈 5종 탐색 (후속 연구 아이디어) |
| `"방법론 추천해줘"` / `"방법론 검증해줘"` | empirical 연구 전용 |

### ⚙️ 고급 플래그

| 플래그 | 의미 |
|-------|------|
| `"평가해줘 --full"` | delta 무시, 전체 6축 강제 재계산 |
| `"평가해줘 axis3,4"` | 명시 축만 실행 |
| `"새 논문 처리해줘 --tier=1"` | 모든 논문 Tier 1 강제 |
| `"새 논문 처리해줘 --priority {파일 목록}"` | 지정 파일만 Tier 1 |
| `"가볍게 처리해줘"` | 전부 Tier 3 강제 |
| `"논문 재분석해줘 --full"` | 모든 논문 Mode B 전량 |
| `"{파일} 논문 재분석해줘 --tier=1"` | 지정 파일 Tier 1 승격 + Critical Reading |

---

## 8. 🆘 막혔을 때

### 점수가 움직이지 않아요

거의 항상 **축 1·3·4**가 원인. 새 논문을 실제로 반영했는지 확인.

```
"레퍼런스 점검해줘"   ← 축 1 먼저
"평가해줘 axis3,4"    ← 반론·독창성만 재계산
```

그래도 그대로면 flow 자체의 **주장**이 약한 것. `"독창성 평가해줘"`(축 4)의 "So What?" 진단을 읽으세요.

### 3일 이상 멈춰있어요

```
"작업 추천해줘"
```

시스템이 activity.log를 분석해 **다음 명령 + 이유**를 제시합니다.

### work-plan이 없어요 / 이상해요

flow.md를 썼는데 평가를 안 했을 가능성. `"flow 레퍼런스 분석해줘" / "flow 내용 분석해줘"`를 먼저.

포맷이 깨진 경우: `"sync 확인해줘"` → 자동 복구 가이드.

### 인용이 의심스러워요 (dangling / over-claim)

수정 명령 시 `citation-auditor`가 자동 실행되지만 명시적으로:
```
"Chapter 2 수정해줘: citation 재검증"
```

또는 최종 단계 `"리뷰 체크해줘"`에서 감사 전량 실행.

### 초안을 처음부터 다시 쓰고 싶어요

```
"초안 작성해줘"
```

재실행. 기존 `output/*.md`는 `history/output/body/{chapter_id}/`에 자동 스냅샷 → 복구 가능.

### 과거 특정 시점 상태를 보고 싶어요

`projects/{P}/activity.log`에서 라인 복사:
```
[2026-04-10 14:30] 평가 완료 | v1 | ... | ref:eval-003 | ...
```

채팅에 붙여넣고:
```
"이 시점 work-plan 보여줘"
```

→ 해당 시점의 archive 내용 출력 (읽기 전용).

### 설치·권한·MCP 오류

| 증상 | 해결 |
|------|------|
| `claude: command not found` | `npm install -g @anthropic-ai/claude-code` |
| 스킬이 인식 안 됨 | `rm ~/.claude/skills/user/research-agent && bash install.sh` |
| Consensus 검색이 3개만 | `claude` → `/mcp` → consensus 선택 → Authenticate |
| 권한 prompt 반복 | `.claude/settings.json`에 패턴 추가 (또는 `/fewer-permission-prompts`) |
| PyPDF2 오류 | `pip3 install pypdf2 --break-system-packages` |

더 많은 경우는 [MANUAL.md § 트러블슈팅](./MANUAL.md#-트러블슈팅).

---

## 9. 🎭 심화 (선택)

### Critical Mode — Oxford·ENS 스타일 비판적 시각

```
"비판 모드 critical로 설정해줘"
```

활성화되면:
- **축 6 critical-lens** 평가 추가 (Paradigm Mapping / Fault-line / Bold Defense / Minority Recovery)
- **critical-companion**이 stage별 **Socratic 질문** 자동 생성 (`{stage}/critical/questions.md`). **답은 사용자가 직접** — 시스템이 암시하지 않습니다.
- 답 작성 후 `"답변 반영해줘"` → `{stage}/critical/commitments.md`에 actionable spec으로 자동 추출 → 이후 writing 에이전트들이 필수 참조.

`intellectual_ambition`: `incremental` (기본) / `critical` / `paradigm-shifting`. flow.md 내용에 따라 자동 제안될 수도 있습니다.

### Gap 분석

```
"gap 분석해줘"
```

분야의 빈틈 5종 탐색 → 후속 연구 아이디어 / 논문 포지셔닝 재설계.

### 방법론 조언 (empirical 전용)

```
"방법론 추천해줘"    ← 3종 비교
"방법론 검증해줘"    ← 내 방법론 감사
```

### Time-travel archive

과거 평가·work-plan 스냅샷 조회. activity.log 라인을 그대로 사용한 §8 참조.

---

## 10. 📚 다음 문서

| 문서 | 내용 |
|------|------|
| [README.md](./README.md) | 설치·시스템 개요·사전 준비 |
| **GUIDE.md** (이 문서) | 사용 가이드 |
| [MANUAL.md](./MANUAL.md) | **전체 레퍼런스** — 19개 에이전트 상세, 병렬 delta 평가 아키텍처, sync, Critical Mode, 활동 로그, 권한, 모델 라우팅, 플래그, troubleshooting |
| [PRINCIPLES.md](./PRINCIPLES.md) | 설계 철학 + 학술 글쓰기 원칙 (5축의 학술적 근거, Kuhn·Popper·Foucault 전통) |
| [skills/WORK-PLAN-FORMAT.md](./skills/WORK-PLAN-FORMAT.md) | work-plan.md 엄격 포맷 스펙 |
| [skills/FLOW-TEMPLATE.md](./skills/FLOW-TEMPLATE.md) | flow.md 줄글 작성 가이드 |

---

## ⚡ 한 줄 요약

```
매 세션: work-plan.md 열기 → 위 카드부터 담당 명령 실행 → stage 끝나면 "flow 레퍼런스 분석해줘" / "flow 내용 분석해줘"
막히면: "작업 추천해줘"
```

평가가 엔진, work-plan이 핸들. 복잡한 건 시스템이 알아서 처리합니다.
