# Research Agent — 사용 가이드

**이 가이드의 목표**: 시스템을 **가장 잘** 쓰는 법.
- 처음 쓰는 사람은 §1 → §3 → §4를 따라가면 첫 평가까지 10분.
- 두 번째 세션부터는 §5(반복 루프)가 본체입니다.
- 명령 레퍼런스는 §7, 막혔을 때는 §8.

복잡한 원리·아키텍처는 [MANUAL.md](./MANUAL.md), 설계 철학은 [PRINCIPLES.md](./PRINCIPLES.md).

---

## 1. ⚡ 1분 시작

```bash
cd ~/Documents/research-agent
claude
```

이 세션 안에서 모든 작업이 자연어 명령으로 진행됩니다. Claude Code는 시스템의 인터페이스이자 실행 엔진이에요.

설치가 안 됐으면 [README.md § 설치](./README.md#-설치)를 먼저.

---

## 2. 🧠 핵심 모델: 평가가 엔진, work-plan.md가 핸들

이 시스템은 **선형 레시피가 아니라 루프**입니다. 한 문장으로 요약하면:

> **"평가해줘" → `work-plan.md`가 갱신됨 → 계획대로 작업 → 다시 "평가해줘"**

```
           ┌─────────────────────────────┐
           │   평가해줘 (5축 점수 산출)      │
           │   ↓                          │
           │   work-plan.md 갱신           │◀──┐
           │   (HUNT/REANALYZE/DRAFT/EDIT)│    │
           └────────────┬────────────────┘    │
                        ↓                      │
              계획대로 명령 실행                  │
              (작업 시작해줘 / 새 논문 /          │
               초안 작성해줘 / Chapter 수정)     │
                        │                      │
                        └──────────────────────┘
                           stage가 끝날 때마다
                           다시 평가해줘
```

### 세 가지 핵심 파일

세션 사이에 기억해야 할 건 **이 세 개뿐**입니다:

| 파일 | 역할 | 언제 보나 |
|------|------|----------|
| `projects/{P}/flow/flow.md` | 연구 방향 (자유 줄글) | 방향 바꿀 때 |
| `projects/{P}/work-plan.md` | **오늘의 할 일 대시보드** | **매 세션마다** |
| `projects/{P}/evaluations/latest/evaluation.md` | 최근 점수·delta | 평가 직후 |

`work-plan.md`를 매일 여는 습관이 곧 이 시스템을 잘 쓰는 법입니다.

---

## 3. 📍 Stage 지도 — "평가해줘"는 stage를 자동 감지합니다

**명령어는 하나(`"평가해줘"`)지만, 시스템이 프로젝트 상태를 보고 stage를 자동 판별**하여 다르게 동작합니다. 이 점을 이해하면 같은 명령을 네 번 쓰면서 네 가지 다른 결과를 얻습니다.

| Stage | 조건 | `평가해줘`가 하는 일 | 권장 재평가 명령 |
|-------|------|---------------------|-----------------|
| **flow** | `flow/flow.md`만 존재 | flow 줄글을 문장 단위로 분석(`claim-extraction-flow.md`) + 6축 점수 + work-plan 생성 | `"평가해줘"` |
| **v1-draft** | `chapters/*.md`가 존재 | chapters 통합 분석(`claim-extraction-draft.md`) + 6축 재평가 + work-plan 갱신 | `"평가해줘"` |
| **revised** | `final/complete-draft.md` + 수정 이력 | 수정 반영 후 재평가 + delta 표시 | `"평가해줘"` |
| **final** | "최종 평가" 명시 또는 final 직전 | 전체 감사 + `citation-auditor` 전량 + reviewer 준비 | `"평가해줘"` 또는 `"리뷰 체크해줘"` |

**경량 보조 명령** (각 stage 중간에):
- Stage 1 리서치 후 → `"레퍼런스 점검해줘"` (축 1만 빠르게)
- flow 갱신 후 → `"논문 재분석해줘"` (기존 PDF를 새 각도로)

**결론**: 워크플로우 어디에 있든 일단 `"평가해줘"`를 쓰면 시스템이 알아서 맞는 평가를 해줍니다.

---

## 4. 🚀 첫 프로젝트 (End-to-End)

새 사용자가 첫 평가까지 가는 최소 경로.

### ① 프로젝트 생성

```
"my-essay 프로젝트 만들어줘"
```

`projects/my-essay/` 폴더 자동 생성. 이 안에서만 작업합니다.

### ② flow.md 작성 (에세이처럼 자유 줄글)

`projects/my-essay/flow/flow.md`를 에디터로 열어 **줄글**로 씁니다.

**필수 2가지**:
- 연구 질문 한 문장: `"이 글은 X를 묻는다"`
- 핵심 주장 한 문장: `"본 에세이는 Y라고 주장한다"`

**권장 구조**: 문제 → 기존 관점 비판 → 자기 제안 → 예상 반론 → 함의 (에세이처럼)

체크박스·목차 형식 **금지**. 시스템이 줄글을 알아서 문장 단위로 분석합니다.

템플릿은 `skills/FLOW-TEMPLATE.md` 참고.

### ③ 첫 평가

```
"평가해줘"
```

**생성되는 것**:
- `evaluations/latest/evaluation.md` — 5축(또는 Critical Mode 시 6축) 점수·판정
- `evaluations/latest/axis1-reference.md` ~ `axis6-critical.md` — 축별 상세 감점 이유
- `flow/claim-extraction-flow.md` — flow 문장 단위 주장 분류 (MATCHED / UNMATCHED-INTERNAL / SUPPORTED)
- `work-plan.md` — **오늘부터 할 일 대시보드** (HUNT·REANALYZE·DRAFT·EDIT 카드)

### ④ 리서치 (work-plan HUNT 자동 실행)

```
"작업 시작해줘"
```

work-plan의 HUNT 카드를 Consensus에서 자동 검색 → `papers/consensus-results.md`에 6 카테고리(🎯 최우선 인용 / 🟢 보조 / 🔴 반론 / 🌏 발달 / ⚙️ 방법론 / 🔗 Cross-HUNT)로 큐레이션.

각 논문에 **영어 abstract 원문 한글 전체 번역**이 인용블록으로 첨부됩니다.

**사용자가 할 일**: 📥 우선순위 리스트대로 PDF 다운로드 → `projects/my-essay/papers/candidates/`에 넣기.

```
"새 논문 처리해줘"
```

→ candidates의 PDF를 triage(haiku) → Tier 분기(Tier 1 opus+Critical / Tier 2·3 sonnet)로 자동 분석.

### ⑤ 초안 작성

```
"초안 작성해줘"
```

→ Phase 1: 구조 설계 제시(사용자 승인 필요) → Phase 2: `chapters/*.md` + `final/complete-draft.md` + `.docx` 생성.

이 시점에서 stage가 **v1-draft**로 전환됩니다.

### ⑥ 재평가 → 수정 반복

```
"평가해줘"            ← 이제 draft 평가로 자동 분기
```

work-plan에 EDIT 카드가 생기면:

```
"Chapter 2 수정해줘: impurity problem 부분을 Löffler 2024 논증으로 강화"
```

→ 자동 일관성 체크 + PDF 대조 인용 감사(citation-auditor).

**여러 챕터 반복 → `"평가해줘"` → 점수 변화 추적**. 목표 점수 도달까지 루프.

### ⑦ 최종 통합 + 리뷰

```
"최종 통합해줘"       ← chapters → final/*.md + .docx 재빌드
"리뷰 체크해줘"       ← 가상 심사자 3-4명 시뮬레이션
```

실제 심사 결과를 받으면:
```
"리뷰 답변 도와줘: [리뷰 텍스트]"
```

---

## 5. 🔁 반복 루프 — 두 번째 세션부터

일단 ④까지 한 번 돌리면 이후 모든 세션은 같은 루프의 변형입니다.

### 매 세션 표준 시작

```
1. projects/{P}/work-plan.md 열기
2. 🧭 "현재 당신이 해야 할 일" 섹션 확인
3. 🟡 Active 또는 🔵 In-progress에서 위부터 카드 하나 집기
4. 해당 카드의 **담당 명령** 필드대로 실행
```

**뭘 할지 모르겠으면**:
```
"작업 추천해줘"
```
→ 로그·work-plan을 분석해 **다음 명령과 이유**를 제시. 정체 구간 탈출용.

### work-plan의 task 타입별 담당 명령

| 카드 타입 | 의미 | 담당 명령 |
|----------|------|----------|
| **HUNT-NNN** | 누락된 근거 논문 찾기 | `"작업 시작해줘"` |
| **REANALYZE-NNN** | 기존 PDF를 새 각도로 재분석 | `"작업 시작해줘"` (HUNT와 함께) |
| **DRAFT-NNN** | 초안 생성 | `"초안 작성해줘"` |
| **EDIT-NNN** | 챕터 수정 지시 | `"Chapter X 수정해줘: {내용}"` |
| **FIX-NNN** | flow 문장 교체 | `"flow 업데이트해줘"` |

각 카드에는 `**covers**: R-NN` 필드(HUNT의 경우)가 있어 어떤 claim을 커버하는지 명시합니다. 우선순위는 work-plan 대시보드의 "🎯 다음 권장 명령" 섹션이 자동 정렬해줍니다. 👉 **위에서부터 처리**.

### 재평가는 언제?

- Stage 1(리서치) 끝 → `"레퍼런스 점검해줘"` (경량, 축 1만)
- Stage 2(초안) 끝 → `"평가해줘"` (전체)
- Stage 3(수정) 끝 → `"평가해줘"` (전체)
- Stage 4(최종) 직전 → `"평가해줘"` (전체 + citation 전량 감사)

중간에 재평가 남발은 피하세요 — delta가 움직이지 않는 재계산은 토큰만 소모.

---

## 6. 📖 산출물 읽는 법

시스템이 생성하는 파일 셋을 정확히 읽을 수 있어야 제대로 활용 가능합니다.

### `evaluations/latest/evaluation.md` — 평가 진단

```
🩺 종합 판정: 🟠 Major Revision
근거: 🔴 구조적 결함 1축 (axis1)

| 축 | 이름 | 상태 | 이전 → 현재 | 핵심 진단 |
|---|------|------|------|----------|
| 1 | 레퍼런스 충실도 | 🔴 구조적 결함 | (첫 평가) | MATCHED 0편 — HUNT 15건 발급 |
| 2 | 논리 전개 | 🟡 적정 | (첫 평가) | thesis 산만 |
...

🚨 Critical Issues (이번 평가에서 가장 시급)
- [축 1] HUNT-001~015 즉시 실행
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

각 축의 **상태 카테고리 + 핵심 진단 + Critical Issues + sub-criteria 4개 카테고리**가 메인. 점수는 `<details>` 접이식 안에. 진단이 **actionable**(구체 문장·위치)로 적혀있어야 좋은 평가. 예를 들어 축 1 진단에 "S017에 레퍼런스 없음"이 있으면 그 문장이 work-plan의 HUNT-XXX로 자동 발급.

**0-State 규칙**: 측정 데이터가 부재 (예: 첫 평가, MATCHED 0편)이면 sub-criteria가 ⚫ 측정 불가로 표기. 잠정 만점·N/A 보류 금지.

### `work-plan.md` — 대시보드

```
> 📅 마지막 갱신: 2026-04-24 15:00 (평가 #003)
> Stage: v1-draft
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
- `**covers**: R-01, R-04` — 이 HUNT가 어느 claim을 커버하는지. registry dedup의 key.
- `**query**: \`...\`` — Consensus 검색 통합 쿼리.
- `**의존성**` — 선행 완료 필요한 카드 ID.
- 대시보드 "축별 현재 상태" — 각 축의 카테고리(🟢🟡🟠🔴⚫)와 active task 수.
- 포맷 엄격 스펙: [WORK-PLAN-FORMAT.md](./skills/WORK-PLAN-FORMAT.md).
- HUNT 영속 이력: `.hunt-registry.json` (work-plan은 활성 view, registry가 SSOT).

### `activity.log` — 시계열 기록

```
[2026-04-24 15:00] 평가 완료 | v1-draft | - | - | ref:eval-003 | agents:evaluation-orchestrator,axis1-5 | verdict=Major Revision categories=Crit:1,Need:3,Adeq:1
```

- 모든 명령이 자동 기록(Claude Code hooks).
- 라인 복사해서 `"이 시점 X 보여줘"`로 **time-travel archive 조회** (읽기 전용).

### `papers/consensus-results.md` — 리서치 큐레이션

HUNT별로 6 카테고리 블록 + 각 논문에 **한글 abstract 번역 인용블록** + 📌 액션 아이템.

- 파일 끝 누적 요약(🏆 최중요 / 📥 PDF 우선순위 / 🔗 Cross-HUNT 교차표)부터 보세요 — 5분에 전체 파악.

---

## 7. 🗂 명령어 맵 (의사결정 기준)

**언제 쓰는가** 기준으로 재분류. 단순 목록은 `"명령어 보여줘"`로도 확인 가능.

### 🏁 언제든 (상태 관리)

| 명령 | 용도 |
|------|------|
| `"작업 추천해줘"` | **뭘 해야 할지 모를 때** — 로그·work-plan 기반 다음 명령 제안 |
| `"sync 확인해줘"` | 아티팩트 동기화 상태 점검 + 해결 가이드 |
| `"평가해줘"` | 현재 stage에 맞는 평가 자동 분기 |

### 📝 flow 작성/갱신 단계

| 명령 | 시점 |
|------|------|
| `"[이름] 프로젝트 만들어줘"` | 새 프로젝트 |
| `"평가해줘"` | flow 첫 작성 후 |
| `"flow 업데이트해줘"` | 논문 수집 후 flow.md를 다듬고 싶을 때 |
| `"비판 모드 critical로 설정해줘"` | Oxford·ENS 스타일 비판적 시각을 원할 때 (선택) |

### 🔬 리서치 단계

| 명령 | 시점 |
|------|------|
| `"작업 시작해줘"` | work-plan의 HUNT·REANALYZE 자동 실행 |
| `"새 논문 처리해줘"` | candidates/에 PDF를 넣은 뒤 |
| `"레퍼런스 점검해줘"` | 리서치 직후 축 1만 경량 재평가 |
| `"논문 재분석해줘"` | flow가 바뀌어 기존 PDF를 새 각도로 스캔 |
| `"논문 제거해줘: {파일명}"` | 철회된 논문 안전 이동 + dangling citation 탐지 |

### ✍️ 초안·수정 단계

| 명령 | 시점 |
|------|------|
| `"초안 작성해줘"` | Phase 1 구조 설계 → 승인 → Phase 2 초안 |
| `"Chapter X 수정해줘: ..."` | 챕터 부분 수정 + 자동 citation 감사 |
| `"평가해줘"` | 초안/수정 직후 delta 추적 |

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

flow.md를 썼는데 평가를 안 했을 가능성. `"평가해줘"`를 먼저.

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

재실행. 기존 `chapters/*.md`는 `chapters/history/{chapter_id}/`에 자동 스냅샷 → 복구 가능.

### 과거 특정 시점 상태를 보고 싶어요

`projects/{P}/activity.log`에서 라인 복사:
```
[2026-04-10 14:30] 평가 완료 | v1-draft | ... | ref:eval-003 | ...
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
- **critical-companion**이 stage별 **Socratic 질문** 자동 생성 (`critical-questions.md`). **답은 사용자가 직접** — 시스템이 암시하지 않습니다.
- 답 작성 후 `"답변 반영해줘"` → `critical-commitments.md`에 actionable spec으로 자동 추출 → 이후 writing 에이전트들이 필수 참조.

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
매 세션: work-plan.md 열기 → 위 카드부터 담당 명령 실행 → stage 끝나면 "평가해줘"
막히면: "작업 추천해줘"
```

평가가 엔진, work-plan이 핸들. 복잡한 건 시스템이 알아서 처리합니다.
