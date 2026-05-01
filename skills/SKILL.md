---
name: research-agent
description: "Academic research project management with AI agents. Creates projects, manages papers with Consensus, generates drafts with Flow-based structure."
---

# Research Agent System

이 스킬은 research-agent 폴더 안의 projects/ 디렉토리에서 작동합니다.

## 전체 작업 흐름 (4-stage 표준)

모든 프로젝트는 **표준 4단계**를 따른다. 사용자 상황에 따라 *앞선 단계 1-2개를 의식적으로 생략*할 수 있다 (생략 = 해당 단계 폴더를 비워둠).

```
[프로젝트 생성 — 4 stage 폴더·템플릿 모두 자동 생성]
   ↓
┌─────────────────────────────────────────────────────────────────┐
│   ① research-gap         ② flow              ③ output       ④ final  │
│   분야 anchor 탐색         논증 구조·thesis      chapter 작성    통합본    │
│   갭 발견                  outline                                       │
│   ↓                       ↓                   ↓               ↓         │
│   gap-report.md            evaluation.md       evaluation.md   evaluation.md │
└─────────────────────────────────────────────────────────────────┘
   ↑ 각 단계 완료 후 "{stage} 평가해줘"로 재진단
```

**표준 진입점 = research-gap**. 새 프로젝트는 일반적으로 이 단계부터 시작 (분야 anchor 탐색 + 갭 발견 → thesis 형성 → flow 작성).

### 생략 가능 패턴 (사용자 상황에 따라)

| 상황 | 시작 stage | 생략하는 것 |
|---|---|---|
| 분야 anchor 탐색 필요 (가장 일반) | **research-gap** | — |
| thesis 이미 명확 (사용자 의식적 결정) | **flow** | research-gap 생략 |
| 이미 chapter 일부 작성 (드뭄 — 외부에서 가져옴) | **output** | research-gap·flow 생략 |
| 이미 통합본 보유 (가장 드뭄 — coursework 채점만 필요) | **final** | research-gap·flow·output 생략 |

생략 = **해당 폴더(research-gap/, flow/, output/)를 비워두기만 하면 됨**. 별도 flag·설정 불필요. 폴더가 비어있으면 main agent가 그 단계 자동 skip.

### 생략 후 다시 진입

생략한 단계로 *나중에* 진입 가능:
- output 작성 중 "다시 thesis 다듬고 싶다" → flow로 회귀 (단, 단방향 원칙상 명시적 사용자 결정 필요. SKILL의 "단방향 진행 원칙" 참조)
- thesis 정해졌는데 anchor 부족 발견 → research-gap.md 작성하면 그 단계 활성화

### 핵심 원칙

1. **research-gap = 표준 시작점**. 생략은 사용자가 의식적으로 결정 (시스템이 강제 X)
2. **폴더가 SSOT** — stage flag 추적 X. 폴더 비어있음 = 그 단계 미진행 OR 의식적 생략
3. flow.md / output / final 완성 → `"{stage} 평가해줘"` → `evaluation.md`가 다음 액션 안내 (work-plan.md 폐기, evaluation.md 단일 진입)
4. main agent는 매 응답 시 폴더 스캔 → 자동 추론 + 모호 시 conversational confirmation

## 🧱 Sub-agent 운영 규율

Sub-agent는 **하나의 좁은 작업**만 담당하며 다음 규칙을 지킨다:

1. **작업 단위 ≤5분 wall clock** — 더 길면 쪼갠다. `1 RESEARCH = 1 worker` 식의 미세 분할이 원칙. `3 RESEARCH end-to-end 담당` 같은 거대 worker 금지.
2. **디스크 출력 의무** — 결과를 return값에만 담지 말 것. 반드시 `.research-raw/`, `.translations/`, `.curation/` 등 **약속된 경로에 파일로 저장** 후 "OK: {한 줄}" 복귀. context가 휘발돼도 디스크가 SSOT.
3. **프롬프트 ≤ 800 토큰** — 스펙 경로를 읽게 하되 내용을 copy-paste 하지 않는다. 공용 스펙(`skills/agents/*.md`, `.context-pack.md`)은 1회 작성 후 worker들이 각자 Read.
4. **병렬 상한 명시** — MCP 호출 있는 작업은 main이 직접 adaptive serial. MCP 없는 순수 추론 작업(번역·curation)은 ≤10 parallel 허용.
5. **간결한 복귀** — 거대한 결과 markdown을 리턴 메시지에 담지 말 것 (context 낭비 + main이 파싱하는 실수 유발). 디스크 경로 + 상태 한 줄만.
6. **idempotent** — 같은 worker를 재호출해도 같은 결과. 출력 파일이 이미 있으면 skip 또는 덮어쓰기 명시적 결정.
7. **사용자 승인 폭주 방지** — main이 parallel Agent 호출을 한꺼번에 대량 투입하지 않는다. 3개 이상 parallel은 한 배치씩 나눠서. 각 배치 완료 확인 후 다음 배치.
8. **파일 쓰기 원자성** — `.curation/{R-id}.md`, `.translations/{R-id}.md`, `.research-raw/{R-id}.json` 등 최종 출력 파일은 **`.tmp.{pid}` 임시 경로에 먼저 쓴 뒤 `mv`로 원자 교체**. sub-agent 중단 시 반쪽 파일이 남지 않도록. Bash 예시:
   ```bash
   python3 -c "open('.curation/R-01.md.tmp.$$', 'w').write(content)" && \
     mv .curation/R-01.md.tmp.$$ .curation/R-01.md
   ```
   Write 도구로 `.tmp.{pid}` 경로에 쓴 뒤 Bash `mv`로 교체. 또는 Python `tempfile.NamedTemporaryFile(dir=target_dir) + os.replace`. post-check(`research_postcheck.py`)가 부분 파일 탐지하면 재실행 유도.

## 💬 사용자 인터페이스 패러다임 — GPT 대화창처럼

사용자는 이 시스템을 **GPT 대화창 쓰듯** 사용합니다 — 자연어로 의도 표현, 응답에서 다음 단계 힌트 자연스럽게 받음, 명령어 외우지 않음. main agent는 이를 다음 운영 원칙으로 지원합니다.

### 1. 자연어 의도 매칭 (rigid pattern X, intent extraction O)

사용자 발화 → 의도 파싱 → 작업 분기. 정확한 명령어가 아니어도 의도가 명확하면 진행.

| 사용자 발화 (예시) | 의도 추출 → 작업 |
|---|---|
| "이거 어떻게 보강해야 할까?" | 현재 단계 evaluation.md 안 봤으면 → 평가 / 봤으면 → 추천 |
| "근거 좀 더 찾아줘" | "리서치 진행해줘" 동등 |
| "이 부분 좀 다듬어줘 X" | output-editor (대상 자동 추론) |
| "비판 받고 싶어" | 비판 시뮬 3종 선택지 (§비판 시뮬 활용 가이드) |
| "어디까지 왔지?" | 진척 라인 + 다음 권장 |
| "갭 한번 보고 싶다" | 폴더 컨텍스트로 분기 (research-gap 진입 / output-gap-finder / 선택지) |

### 2. 응답 끝 진척 라인 자동 출력 ⭐

**모든 작업 완료 응답 끝에** main agent가 다음 1-2줄을 자동 부착. 사용자가 별도 `"현재 상태"` 명령 없이도 *항상 위치*를 인지하도록.

**형식**:
```
📍 {stage 진척} · {축별 핵심 상태}
👉 다음 권장: {백틱 명령 또는 자연어 힌트} — {짧은 이유}
```

**예시**:
```
📍 research-gap ✓ · flow 평가 ✓ (🟠 axis3) · output 미진입 · final 미진입
👉 다음 권장: "리서치 진행해줘" — R-04·R-07·R-12 미해결 (axis1 보강)
```

```
📍 flow 작성 중 (101자) · 평가 미실행
👉 다음 권장: flow.md를 좀 더 채운 후 "평가해줘" — RQ·thesis 1문장씩 명시 권고
```

```
📍 output 평가 ✓ (🟢 모든 축) · final 미진입
👉 다음 권장: "최종 완성했어" — 통합본 머지 후 final 평가 가능
```

**진척 라인 산출 규칙** (main agent 매 응답 시) — 4-stage 표준 + 생략 패턴 인식:

**stage 상태 판정** (각 stage마다 4 상태):
- `research-gap`:
  - 폴더 부재 → "미초기화" (드뭄, 옛 프로젝트)
  - research-gap.md 비어있음 (메타데이터 골격만) → "건너뜀" (사용자 의식적 생략)
  - research-gap.md 작성됨 + research-plan.md 미생성 → "작성 중"
  - research-plan.md 있고 검색·분석 진행 중 → "진행 중 (H-NN 검색·분석 일부)"
  - gap-report.md 있음 → "✓ 완료"
- `flow`:
  - flow.md 100자 미만 → "미작성"
  - 100자 이상 + 평가 없음 → "작성 중"
  - 평가 있음 → "평가 ✓ (최저 axis 표시)"
- `output`:
  - 0N-*.md 0개 → "미진입"
  - 1개 이상 + 평가 없음 → "작성 중 (N chapter)"
  - 평가 있음 → "평가 ✓ (verdict 표시)"
- `final`:
  - complete-draft.md 부재 → "미진입"
  - 있음 + 평가 없음 → "통합본 ✓"
  - 평가 있음 → "평가 ✓ (verdict)"

**생략 패턴 자동 인식**:
- research-gap.md가 빈 템플릿 그대로 (사용자 입력 없음) + flow.md 작성됨 → research-gap "건너뜀" 표시 (생략 정상)
- 동일 패턴이 다른 stage에도 적용

**예시 (생략 케이스)**:
```
📍 research-gap (건너뜀) · flow 평가 ✓ (🟡) · output 미진입 · final 미진입
👉 다음 권장: "리서치 진행해줘" — 미해결 R-NN 3건
```

**다음 권장 우선순위**:
   - 미해결 R-NN/H-NN 있음 → "리서치 진행해줘"
   - candidates에 PDF 있음 → "논문 처리해줘"
   - evaluation에 🔴/🟠 있음 → 해당 축 보강 (자연어 힌트)
   - 모든 축 🟢/🟡 → 다음 stage 진입 권유
   - 막힌 곳 없음 → "현재 잘 진행 중"

**제외 대상** (진척 라인 안 붙이는 응답):
- 정보 조회만 (예: "현재 상태", "버전 체크" — 이미 진척이 본문)
- 단순 질문 답변 (작업 수행 X)
- 에러·blocked 응답 (이미 다음 행동 본문에)

### 3. 모호 시 conversational confirmation (선택지 대신 질문)

기계적인 선택지보다 자연어 확인:
- ❌ "어느 작업을 의도하셨나요? 1. flow 평가 / 2. output 평가"
- ✅ "지금 flow.md 보강 후 첫 평가인 것 같은데, flow 평가로 진행할까요? 아니면 output 쪽인가요?"

진짜 모호할 때만. 폴더 컨텍스트로 자명하면 그냥 진행 + 진척 라인에 무엇 했는지 표시.

### 4. 응답 톤 — 대화체 유지

- ❌ rigid 시스템 메시지 ("⚠️ 단계를 명시해주세요")
- ✅ 친근한 대화체 ("flow 쪽 평가 진행할게요. 결과는 evaluation.md에 정리됩니다.")
- 사용자가 *작업 도구*가 아닌 *대화 상대*로 느끼도록

### 5. 결과를 응답 안에 충분히

매번 사용자가 evaluation.md를 *열어야* 알 수 있게 강요 X. 핵심 결과 (verdict, 시급한 약점 1-3개, 다음 권장)는 응답 본문에 요약. 상세는 파일 참조.

---

## 🎓 research-gap 단계 — 박사생 Hybrid 워크플로 (anchor discovery)

research-gap은 *분야 anchor 탐색·갭 발견*. flow 단계의 광범위 thesis-supportive 검색과 다름. **사용자가 anchor 판단의 주체**, AI는 후보 추천 사서 역할.

### 핵심 원칙

1. **양 < 질** — 1 H에 결정적 anchor 3-5편. 광범위 20편 노이즈 검색 X.
2. **Narrow query** — 좁은 3-4 keyword. 광범위 6+ keyword X.
3. **AI 추천 / 사용자 채택** — AI는 abstract 평가로 후보 리스트만, anchor 채택은 사용자 정독 후.
4. **Iterative loop** — anchor 부족 시 사용자가 research-gap.md '6) 앵커 논문 리서치 방향' 수정 → 재검색.

### 워크플로 (사용자 시점)

```
1. research-gap.md 작성 (5+6 요소 — '6) 앵커 논문 리서치 방향' 포함)
       ↓
2. "리서치 갭 분석해줘"  → research-plan.md (gap-analyzer)
       ↓
3. "앵커 논문 찾아줘"  → anchor-candidates.md (anchor-recommender)
       AI: narrow 검색 + abstract 정합 평가 + 후보 리스트 추천 (채택 X)
       ↓
4. 사용자: 추천 paper 다운로드 → 정독 → anchor 선별
       선별한 paper → papers/candidates/research-gap/ 이동
       나머지 폐기 또는 별도
       ↓
5. "논문 분석해줘"  → [R][D].*.md (gap-paper-analyst, 옮긴 PDF만)
       ↓
6. 검토:
   (a) 충분 → "갭 리포트 만들어줘" → gap-report.md → flow 단계로
   (b) 부족 → research-gap.md '6) 앵커 논문 리서치 방향' 수정 → step 2 재진입
```

### 사용자 결정 포인트 (의사결정 부담 최소화)

- ① research-gap.md 작성 (5+6 요소)
- ④ anchor 판단·이동 (정독 후 본인 thesis 기준)
- ⑥ 충분 여부 + 부족 시 6) 섹션 수정

명령은 단순 (2·3·5·6번 — 4-5회). 매 step confirmation 부담 X.

### flow 단계 검색과 분리

| | research-gap (anchor discovery) | flow (thesis-supportive) |
|---|---|---|
| 목적 | 분야 anchor·갭 발견 | thesis 보강 인용 |
| 쿼리 | narrow 3-4 keyword | 광범위 5-8 keyword |
| 결과 | 5점 5-10편 후보 | 20편 6 카테고리 curation |
| Anchor 채택 | 사용자 정독 후 | claim-extraction 자동 매칭 |
| Loop | 6) 섹션 수정 → 재검색 | 1회 (UNMATCHED → search) |
| Agent | anchor-recommender | research-processor (4-stage) |

### Anchor 부재 = valuable signal

검색 결과 정합 5점 0편 ≠ 실패. **anchor 부재가 본 thesis의 contribution 기회 신호**.

이 경우 anchor-candidates.md에 명시:
> "H-04에 대해 narrow 검색 결과 5점 anchor 부재. 본 thesis가 *분야 dry spot*에 위치할 가능성. 6) 섹션 수정으로 frame 재검토 권장 OR contribution으로 강조."

---

## 🎯 핵심 데이터 흐름 — writing-spec.md 중심

**문제 진단**: 기존엔 agent 결과 → 사용자 피드백 → 본문 반영. 사용자 부담 큼 + 결과 누수 발생 → quality 저하.

**해결**: agent 결과를 **writing-spec.md (internal)** 로 통합 → writing-architect/output-editor가 *체크리스트처럼* 본문에 자동 반영. 반영 못 한 잔여만 feedback.md로 사용자에게.

### Architecture

```
agents (24개 그대로)
   ↓ (모든 결과 → output/.internal/)
main agent가 writing-spec.md 자동 작성
   ↓ (primary input)
writing-architect / output-editor가 본문에 자동 반영 (체크리스트)
   ↓
chapter (반영된 결과)
   ↓
feedback.md (반영 못 한 잔여 + 사용자 결정 필요한 부분)
   ↓ (사용자 답변)
writing-spec.md에 carry-over → 다음 round 자동 반영
```

### writing-spec.md 형식 (internal, sub-agent input용)

`output/.internal/writing-spec.md` 위치. main agent가 자동 작성·갱신.

```markdown
---
generated_by: main-agent (auto-extracted)
generated_at: {ISO}
round: N
based_on:
  flow_md_hash: {hash}
  generative_outputs: [thesis-developer, output-cross-paper-insights, steelman-dialectic, field-positioning-oracle]
  adversarial: outline-critique + chapter-critique
  peer-review: peer-review-simulation
  user_answers: feedback.md (이전 round)
---

# Writing Spec — Round N

## 1. Must-Have (본문에 반드시 등장)

### Positioning Statement
"{4-component statement 그대로}"
→ Ch1 도입에 등장

### Commitments (auto-extracted + 사용자 답변 carry-over)
- C-001: {내용} → Ch{N} 문단 {N}
- C-002: ...
- C-USER-001 [사용자 답변 from Round {M}]: ... → Ch{N} 문단 {N}

### Counterargument Anticipation (chapter별 layer)
- Ch1: L1·L2·L3 (구체)
- Ch2: ...

### Quote Framing 매핑
- {paper} {p.N}: Ch{N} ({framing}), Ch{M} ({다른 framing})

### Foil 차단 (반박 미리 방어)
- Ch{N}: {hedge 명시}

## 2. Self-Critique 체크리스트 (chapter별)
- [ ] Layered argumentation (large/medium/fine)
- [ ] Counterargument 3-step
- [ ] Quote framing 정밀 (다른 chapter와 다른 framing)
- [ ] Scholarly voice
- [ ] Novel synthesis 명시
- [ ] 모든 commitment 등장

## 3. 사용자 결정 필요 (이번 round writing-spec에 반영 못 함)
- Q1: {질문} — feedback.md로 노출
- Q2: ...
```

### feedback.md 형식 (사용자 출력, 1 페이지)

`output/feedback.md` 위치. writing-spec에 자동 반영된 항목은 **표시 안 함**. 잔여만.

**🚫 절대 규칙 — 사용자 출력에 internal ID 노출 금지**:
- ❌ "C-AGE-001", "8 C-AUTO 적용", "C-USER-NNN", "Q1.1" 등 internal tracking ID 사용 X
- ❌ "Phase 2.5", "outline-critique·chapter-critique × 4" 같은 internal agent stage 명칭 X
- ❌ "47 항목 자동 적용", "8 C-AGE 보강" 같은 internal commit 카운트 X
- ✅ 자연어로만: "Round 2 연령대 보강", "Royall 노인 표본 명시", "사분면 3 학령기 공백"
- 이유: 사용자는 internal tracking 코드 모르고 알 필요 없음. 자연어가 의사결정에 충분.

같은 원칙: `flow/feedback.md`, `output/feedback.md`, 사용자 메시지 모두 적용. internal ID는 `output/.internal/writing-spec.md` / agent 보고 / activity log 등 *internal*에서만.

```markdown
# 피드백 — Round N

## 종합 평가
- Verdict: {accept / minor / major / reject}
- 강점 1줄 / 약점 1줄

## 우선 수정 권고 (top 3-5, 자동 적용 못 한 것만)
1. Ch{N}: {구체 수정}
2. ...

## 사용자 결정 필요 (top 3-5)
1. {critical 질문}
   > 답변:
2. ...

## 다음 단계
- 답변 작성 → `다음 단계 진행`
- 직접 수정 → `Chapter X 수정해줘: ...`
- 추가 논문 → `리서치 진행해줘`

---
*상세: output/.internal/ (agent별 산출, 디버깅용)*
```

### 사용자 출력 = 2종

```
output/
├── 0N-{section}.md          ← chapter (사용자 ✓)
├── 00-positioning.md         ← positioning (사용자 ✓ optional)
├── feedback.md              ← 단일 피드백 (사용자 ✓)
└── .internal/                ← hidden (사용자 안 봄, 필요 시 read)
    ├── writing-spec.md       ← 핵심 데이터 흐름 hub
    ├── outline.md
    ├── outline-critique.md
    ├── chapter-critique-0N.md
    ├── peer-review-simulation.md
    ├── critical-questions.md ← critical-companion 산출 (writing-spec으로 흡수)
    └── generative/
        ├── thesis-development-notes.md
        ├── cross-paper-insights.md
        ├── steelman-dialectic.md
        └── field-positioning.md

final/
├── complete-draft.md / .docx ← 완성본
└── references.md             ← 자동 추출 레퍼런스
```

**사이클**:
1. 사용자: "초안 작성해줘" → internal pipeline 자동 (agents → writing-spec → write → feedback)
2. 사용자가 chapter + feedback 검토
3. 답변 작성 → "다음 단계 진행" → writing-spec carry-over → 자동 revise
4. (반복) → "완성본 만들어줘" → final/

## 🚫 단방향 진행 원칙 (research-gap → flow → output → final, 역방향 금지)

프로젝트는 4 단계: **research-gap** (선택, 분야 anchor 탐색·갭 발견) → **flow** (논증 구조·연구 질문·thesis outline) → **output** (실제 chapter 작성·수정) → **final** (통합본).

폴더가 곧 단계 — 폴더의 존재·내용으로 무엇이 진행 중인지 결정. **stage flag 추적 안 함**.

### 절대 규칙

**다음 단계 진입 후 이전 단계 작성 파일 수정 X**.

- output 단계 진입 = `output/`에 chapter 파일 존재 OR `초안 작성해줘` 명령으로 진입
- 그 시점부터 `flow/flow.md`는 *frozen* — agent·main agent 모두 *수정 권장 X·실제 수정 X*
- 마찬가지로 flow 단계 진입 후 `research-gap/research-gap.md`도 *frozen*
- 수정 가이드·diff 제안·"flow.md 업데이트하시겠어요?" 같은 권유 모두 **금지**

### 왜 단방향인가

1. **버전 관리 일관성** — research-gap → flow → output → final 누적 진행. 후속 단계 작성 중 이전 단계 변경하면 base가 흔들림.
2. **Generative phase 결과 처리 명확성** — thesis-developer / cross-paper-insight / steelman-dialectic / field-positioning 산출은 *output 단계 input*. flow에 반영하지 않고 직접 작성에 활용.
3. **사용자 의도 보호** — 이전 단계에서 사용자가 정한 구조를 후속 작성 중간에 LLM이 흔들지 않음.

### 산출물 위치 표준 (폴더가 SSOT)

| 단계 | 산출 위치 |
|------|---------|
| research-gap (표준 시작점) | `research-gap/research-gap.md`, `research-gap/research-plan.md`, `research-gap/gap-report.md`, `papers/candidates/research-gap/`, `papers/analyzed/research-gap/[R]\|[R][D].*.md`, `papers/search-results/research-gap.md` |
| flow 단계 | `flow/flow.md`, `flow/claim-extraction-flow.md`, `flow/critical/critical-questions.md`, `flow/critical/archive/{date}-{trigger}/`, `papers/candidates/flow/`, `papers/analyzed/flow/[A]\|[N].*.md`, `papers/search-results/flow.md` |
| output 단계 | `output/0N-{section}.md`, `output/00-positioning.md`, `output/generative/{agent}.md` (internal), `output/outline-critique.md`, `output/chapter-critique-0N.md`, `output/peer-review-simulation.md`, `output/claim-extraction-output.md`, `output/critical/critical-questions.md`, `output/critical/archive/{date}-{trigger}/` |
| Cross-stage | `critical-commitments.md` (프로젝트 루트, 양 단계에서 누적), `papers/collected/{Author_Year}.pdf` (모든 단계 공유 PDF), `activity.log` |
| 최종 | `final/complete-draft.md`, `final/complete-draft.docx` |

### Critical 파일 단계별 분리

**critical-questions.md는 단계별 분리** — 현재 작업 단계에 해당하는 위치에 생성:
- flow 단계 작업 (`flow 평가해줘`, `flow 업데이트해줘`) 후 → `flow/critical/critical-questions.md`
- output 단계 작업 (`초안 작성해줘`, `Chapter X 수정해줘`) 후 → `output/critical/critical-questions.md`

**자동 재생성 + Archive**:
- 작성·수정·평가 완료 시마다 critical-companion 자동 호출
- 기존 `critical-questions.md`가 있고 *답변되지 않은 항목 있으면* → `archive/{date}-{trigger}/` 으로 이동
- 답변된 항목은 `critical-commitments.md` (cross-stage)에 누적
- 새 critical-questions.md 생성 (현재 상태 반영)

**generative phase 산출 (`output/generative/*.md`)은 internal 작업물** — 사용자에게 직접 노출 X. main agent가 자동 종합해서 critical-commitments.md / output/critical/critical-questions.md / writing-architect input으로 활용.

### 만약 flow.md 수정이 *진짜* 필요하다면

- 답: **output 작업 중단 → output stage에서 빠져나옴 → flow 단계로 명시적 회귀** (드문 케이스, 사용자 명시 요청 시만)
- 회귀 명령: `"flow 단계로 돌아가줘"` (별도 명령) — output/ archive snapshot 후 flow 수정 가능
- 단순 수정 권유로는 X. 의식적·명시적 회귀만.

### Agent별 적용

- **Generative agents 4종**: 산출은 *제안*만. flow.md 수정 X. critical-commitments.md 또는 writing-architect Phase 0 input으로만 활용.
- **adversarial-reviewer**: critique는 chapter 수정 input. flow.md 수정 X.
- **peer-reviewer**: simulated review는 chapter revision 권장. flow.md 수정 X.
- **flow-refiner**: 유일하게 flow.md 수정 가능 — 단 *flow 단계*에서만. `flow 업데이트해줘` 명령은 output 단계에서 reject.
- **gap-analyzer / gap-paper-analyst / gap-synthesizer**: research-gap 단계 전용. flow 단계 진입 후 호출 안 됨.

## 🚫 실행 중 리팩터링 금지 원칙

사용자가 작업 실행 중 구조/스펙 이슈를 지적하면:

1. **즉시 TaskCreate로 follow-up 태스크 등록** (backlog에 적재)
2. **현재 실행은 기존 구조로 완수** — 시간·토큰 이미 투입된 진행을 버리지 않는다
3. **완료 후 backlog 훑으며 단 한 번만 묻기**: "지금 구조 개선 진행할지 / 다음 실행부터 적용할지"

예외 (실행 즉시 중단 허용):
- **치명적 correctness 결함**: 데이터 소실 확정 (예: HIT 번역 플레이스홀더 사태), 잘못된 파일 덮어쓰기 직전, user/privacy 정보 유출 위험
- **사용자 명시적 stop 지시**

"멈추고 시스템 전반 리팩터 → 다시 실행" 패턴 금지. 그렇게 하면 한 세션이 90분+로 늘어난다 (2026-04-24).

## 🧭 TaskCreate 사용 의무

**≥3단계 파이프라인**에서는 실행 시작 시점에 반드시 `TaskCreate`로 각 단계를 태스크화한다. 대상:

- `{stage} 평가해줘` — claim-extract → 축별 dispatch → aggregator → (stage=final 한정) final-holistic-reviewer → delta mark-done → sync update → evaluation.md 갱신 (≥6 단계 / final은 +1)
- `리서치 갭 분석해줘` (research-gap 진입) — research-gap.md 검증 → gap-analyzer → research-plan.md (사용자 6) 섹션 carry-over) (≥3 단계)
- `앵커 논문 찾아줘` ⭐ (research-gap, anchor discovery) — research-plan.md + 사용자 6) → anchor-recommender → narrow 검색 → abstract 정합 평가 → anchor-candidates.md (후보만, 채택 X) (≥4 단계)
- `리서치 진행해줘` (flow 단계용) — `flow/claim-extraction-flow.md`의 미해결 R-NN → Consensus 4-stage 파이프라인 → search-results/flow.md (≥6 단계). research-gap 단계는 `앵커 논문 찾아줘` 사용 권장.
- `논문 처리해줘`·`논문 분석해줘` — `papers/candidates/{research-gap,flow}/` 양쪽 스캔 → 폴더에 따라 gap-paper-analyst (research-gap, [R][D]) / paper-analyst (flow, [A]/[N]) × N (≥4 단계). research-gap PDF는 *사용자가 anchor라고 판단해서 옮긴 것*만 분석.
- `갭 리포트 만들어줘` — `papers/analyzed/research-gap/[R][D].*.md` 1개 이상 확인 → gap-synthesizer → research-gap/gap-report.md (≥2 단계)
- `초안 작성해줘` — (옵션) generative phase (thesis-developer / output-cross-paper-insights / steelman-dialectic / field-positioning-oracle) → writing-architect Phase 0/1 → adversarial-reviewer (Phase 1.5) → writing-architect Phase 2 (chapter별) + adversarial-reviewer (Phase 2.5) + output-editor (자동 수정) → peer-reviewer (Phase 3) → claim-extract → 평가 (≥6 단계)
- `Chapter X 수정해줘` — snapshot → output-editor → citation-checker → claim-extract (≥4 단계)
- `flow 업데이트해줘` — snapshot → flow-refiner → 사용자 승인 → 반영 → 평가 (≥4 단계)
- `영어로 번역해줘` (출고 단계) — 사전 조건 점검 (writing-architect Phase 2 + adversarial-reviewer + output-editor + citation-checker 통과) → output-en-translator dispatch (chapter별 ≤4 병렬) → 영문 파일 저장 (`output/en/*.en.md`) (≥3 단계)

**왜 필요한가 (2026-04-24 실패 사례)**: 다단계 파이프라인에서 중간 단계(예: abstract 번역)가 조용히 누락된 채 "완료" 보고가 올라오는 사고가 발생. 태스크 리스트가 있었다면 열린 in_progress 항목이 사용자 보고 전 불일치를 가시화. 태스크 누락 자체가 품질 signal.

**태스크 granularity**: 각 태스크는 **완료 조건(post-condition)이 검증 가능**해야 함. "번역" 같은 추상 태스크 금지. "번역 대기 placeholder가 0건" 같이 grep으로 확인 가능한 조건으로 잘게 쪼갠다.

## 5축 평가 기준

flow/원고를 top-tier 저널 심사 엄격도로 평가한다. 각 축은 4개 sub-criteria로 구성.

| 축 | 이름 | 핵심 질문 | 전문 에이전트 |
|---|------|----------|-------------|
| **1** | 논문 레퍼런스 충실도 | Coverage + Accuracy + Authority + Balance | **axis1-reference-scorer** |
| **2** | 논리 전개 완성도 | Argument chain + Transition + Thesis alignment + Scope closure | **axis2-logic-scorer** |
| **3** | 반박/강화 논리 | Steelman + Falsifiability + Limitations + Reviewer attack surface | **axis3-defense-scorer** |
| **4** | 독창성·기여도 | "So What?" + Novelty positioning + Contribution layer + Implications | **axis4-originality-scorer** |
| **5** | 구성개념 정의 정밀도 | Definition + Operationalization + Boundary + Categorical/Dimensional | **axis5-concept-scorer** |
| **6** | 비판 렌즈 (Critical Mode) | Paradigm Mapping + Fault-line + Bold Defense + Minority Recovery | **axis6-critical-scorer** |

### 카테고리 시스템 (메인 시그널)

각 sub-criteria + 축 전체에 5단계 중 하나를 부여:

| 상태 | 라벨 |
|------|------|
| 🟢 | 충실 (Strong) — 분야 표준 충족, 약점 minimal |
| 🟡 | 적정 (Adequate) — 통과 가능, 작은 보강만 |
| 🟠 | 보강 필요 (Needs Work) — 통과 위해 의미 있는 보강 |
| 🔴 | 구조적 결함 (Critical Gap) — 통과 어려움, 구조적 보강 |
| ⚫ | 측정 불가 (Cannot Assess) — 측정 데이터 부재 (0-state) |

### Verdict roll-up (점수 평균 폐기)

```
Reject              : ≥2 axes at 🔴 OR (axis1 AND axis5 둘 다 🔴) OR ≥3 axes at ⚫
Major Revision      : ≥1 axis at 🔴 (Reject 미달) OR ≥3 axes at 🟠
Revise & Resubmit   : ≥2 axes at 🟠 (Major 미달) OR ≥1 axis at ⚫ (Reject 미달)
Accept              : all axes ≥ 🟡 Adequate, 🔴/⚫ 0개
```

axis1+axis5는 "구조적 축" 가중 — 레퍼런스+개념 정의는 학술 논문의 기초 인프라이므로.

### 신뢰 가능 vs 보조

- **신뢰 가능 (메인 시그널)**: 카테고리 (🟢🟡🟠🔴⚫), 진단 텍스트, Critical Issues, RESEARCH/Action item, 카테고리 변화 방향 (Δ)
- **보조 (trend tracking 전용)**: 절대점수 X/100, sub-criteria 점수 X/25 — 추세 모니터링용. 절대 판정·등급 산출에 사용 금지. axis 파일에는 `<details>` 접이식 안에만 노출.

### 0-State 규칙

측정 데이터 부재 시 (예: MATCHED 0편, steelman tag 논문 0편) sub-criteria 카테고리는 **⚫ 측정 불가**로 명시. **잠정 만점·N/A 보류·임의 평균값 부여 금지**.

**병렬 delta 오케스트레이션**: `evaluation-orchestrator`가 변경된 축만 병렬 디스패치. stale 판정은 `scripts/evaluation_delta.py`의 입력 해시 비교. 축 6은 Critical Mode 활성 시에만 포함. 감사(citation-checker) · 구조 설계(writing-architect) · 심사 시뮬레이션(peer-reviewer)은 별개 명령으로 호출되며 채점 주체가 아님.

**Dispatch 규율**: orchestrator는 axis-scorer prompt에 사양 + 선로드 context만 주입. 평가 가이드·점수 힌트·사전 작성된 체크리스트 주입 금지 (채점자 독립성 보호).

## 자동 재분석 규칙 (Stage-aware claim-extraction)

claim-extractor는 *평가의 input*. 평가 명령 (`평가해줘`)에서만 자동 체이닝. **작성·수정 명령에서는 호출하지 않음** (평가에 무관).

| 명령 | 자동 재분석 조건 | 대상 | 출력 |
|------|----------------|-----|-----|
| `flow 평가해줘` | flow.md mtime > `flow/claim-extraction-flow.md` mtime | flow | `flow/claim-extraction-flow.md` |
| `output 평가해줘` | 어느 chapter든 mtime > `output/claim-extraction-output.md` mtime | chapters 통합 | `output/claim-extraction-output.md` |
| `final 평가해줘` | `final/complete-draft.md` mtime > `final/claim-extraction-final.md` mtime | 통합본 | `final/claim-extraction-final.md` |
| `flow 업데이트해줘` | flow-refiner 승인 반영 후 | flow | `flow/claim-extraction-flow.md` |
| `최종 완성했어` | output/*.md 머지 시점에 final/ 생성 (claim-extraction은 다음 `final 평가해줘`에서 lazy 갱신) | — | — |

**작성/수정 명령은 자동 체이닝 X**:
- `초안 작성해줘` 직후엔 sync_state + build_index만 (단계 9). claim-extractor는 사용자가 다음 `평가해줘` 호출 시점에 lazy 갱신.
- `Chapter X 수정해줘` 직후도 동일 — output-editor + citation-checker만 자동, claim-extractor 미호출.

**Snapshot 정책 — 두 메커니즘이 공존**:

| 메커니즘 | 트리거 | 무엇이 보존되나 | 위치 |
|---------|-------|--------------|------|
| **자동 (version_manager)** | 모든 frontmatter v++ 직전 | 이전 버전 파일 그대로 | `history/{stage}/{type}/{NNN}-...-vN-pre-bump/` |
| **명시 (sync_state.py snapshot-*)** | LLM이 doc 따라 호출 | 의미 있는 마일스톤 + manifest | 동일 |

**원칙**: 일반 변경은 자동 백업으로 충분. **특수 마일스톤만** 명시 snapshot:
- `snapshot-flow {P} pre-refine` — flow-refiner가 사용자 승인 직전
- `snapshot-output {P} pre-redraft {chapter}` — output 전면 재작성 직전
- `snapshot-evaluation {P} pre-respin` — 평가 시스템 큰 변경 전 (manifest 기반 증분)
- `snapshot-research-gap {P} pre-replan` — research-plan.md 재생성 직전

**Critical 질문 자동 재생성 규칙** (always-on, ambition 무관):

모든 flow/output 작업 후 critical-companion 자동 호출. 단계별 위치:
- flow 단계 작업 (`flow 평가/업데이트/리서치/논문 처리해줘`) 후 → `flow/critical/critical-questions.md`
- output 단계 작업 (`초안 작성/Chapter 수정/output 평가/적대적 리뷰`) 후 → `output/critical/critical-questions.md`

새 critical 생성 시 기존 답변된 항목은 `critical-commitments.md` 누적, 답변 안 된 항목은 archive 자동 이동.

ambition은 **강도 조절**만 (게이트 X):
- `incremental`: 5-10 질문, 기본 강도
- `critical`: 15-25 질문, 강한 강도, axis6 + Iconoclast 자동 활성
- `paradigm-shifting`: 25-40 질문, 가장 강함, axis6 우선·Iconoclast 주 심사자

(원래 "Critical Mode 자동 재분석 규칙"은 이 always-on 정책으로 대체됨)

| 트리거 | 자동 실행 | 출력 |
|-------|---------|------|
| 첫 `평가해줘` 실행 + flow.md critical 신호 ≥ 3 자동 감지 | critical-companion Phase 1-5 호출 | `critical-questions.md` 생성 (v1) |
| `critical-questions.md` mtime > `critical-commitments.md` mtime | `"답변 반영해줘"` 자동 → critical-companion Phase 6 호출 | `critical-commitments.md` 갱신·신규 생성 |
| `초안 작성해줘` / `Chapter X 수정해줘` 실행 직전 | 위 mtime 비교 prehook → 필요 시 Phase 6 | commitment 최신화 후 실제 작업 진행 |

**R-NN 식별자 (단순화)**: claim-extractor가 UNMATCHED를 식별하고 R-01, R-02… 로 번호 부여. work-plan.md·card_registry·R-NN/WRITE-NNN ID 시스템은 **모두 폐기**. R-NN은 `claim-extraction-{stage}.md` 파일 안에 그대로 보존되며, 같은 R이 다음 평가에서 재식별되면 같은 번호로 매칭(자연어 dedup_key — claim 텍스트 정규화 기반).

**검색 dedup**:
- `papers/search-results/{stage}.md`에 R-NN 섹션이 이미 있으면 같은 R 재검색 skip
- `papers/analyzed/{stage}/[A]\|[N]\|[R]\|[R][D].{Author_Year}.md` 존재 → 같은 PDF 재분석 skip
- 폴더 자체가 dedup state. 별도 registry JSON 없음.

**research-gap 단계의 H-NN**:
- gap-analyzer가 H-01, H-02… 형태로 가설 식별. `research-gap/research-plan.md`에 보존.
- 같은 H가 재식별되면 같은 번호 유지. 새 H면 다음 번호.

## 🔒 프로젝트 컨텍스트 규약 (세션 추적)

여러 프로젝트가 `projects/` 안에 공존할 수 있다. 어떤 프로젝트로 명령이 라우팅되는지는 **명시 신호로만 결정**한다 — silent 추측 금지.

**프로젝트 식별 우선순위 (모든 명령에 적용)**:
1. 사용자 메시지에 `projects/X` 경로 직접 등장
2. 사용자 메시지에 프로젝트 이름 직접 등장 (예: `"CDEA flow 평가해줘"`)
3. 같은 conversation 내 이전 메시지에서 사용자가 명시한 프로젝트 (Claude가 컨텍스트로 추적)
4. CWD가 `projects/X` 또는 그 하위 — 사용자가 그 폴더에서 Claude를 실행한 경우
5. 위 모두 모호하면 → **사용자에게 명시 요청 후 중단**. "가장 최근 폴더" 같은 fallback 추측 절대 금지.

**세션 시작 시 규약**:
- 새 conversation의 첫 명령에서 프로젝트가 모호하면 Claude는 먼저 묻는다:
  > "어느 프로젝트인가요? 현재 `projects/` 안에 있는 프로젝트: CDEA, …"
- 사용자가 `"CDEA로 작업할게"` 같이 한 번 명시하면, **이 conversation이 끝날 때까지 그 프로젝트만 작업**. 다른 프로젝트로 옮기려면 사용자가 명시적으로 전환 선언.

**자동 hook 처리**:
- `activity_log.py:detect_project`는 명시 신호 부재 시 None 반환 → 로그 스킵 (silent 라우팅 사고 방지).
- `mode_manager` 폐기와 같은 원칙: hidden state 추측 대신 명시 신호 강제.

**프로젝트 격리 보장**:
- 디스크 수준: 각 `projects/{X}/` 폴더가 자기 research-gap·flow·output·final·papers를 가짐 — 폴더 간 cross-contamination 없음. 폴더 = SSOT (registry·work-plan 같은 별도 state 파일 없음).
- 명령 수준: 위 우선순위로 라우팅 → conversation 컨텍스트가 깨지지 않는 한 추적 유지.

**옛 버전 프로젝트 폴더 가져왔을 때**:

다른 사용자에게서 받은 또는 옛 시점 백업에서 복구한 프로젝트 폴더는 v3.2 구조와 다를 수 있다 (`.current-mode` 잔존, `chapters/`, `evaluations/latest/` 옛 위치 등). 첫 작업 전 한 번 마이그레이션:

```bash
# dry-run으로 변경 예정 항목 미리 보기
python3 scripts/migrate_project.py {PROJECT} --dry-run

# 실제 적용 (멱등 — 두 번 실행해도 안전)
python3 scripts/migrate_project.py {PROJECT}
```

또는 사용자가 `"프로젝트 마이그레이션해줘 {P}"`라고 말하면 Claude가 위 명령을 실행. 이미 최신 구조면 모든 단계 skip 메시지로 끝남.

## evaluation.md 사용 사이클 (공통, work-plan 대체)

`projects/{P}/{stage}/evaluations/latest/evaluation.md`가 사용자 진입 단일 파일입니다. work-plan.md는 **폐기**. 평가 결과·다음 액션·축별 상태·미해결 RESEARCH 항목·WRITE 권고가 모두 이 파일에 통합. **포맷 규율은 `skills/EVALUATION-FORMAT.md` 필수 준수**.

### 명령어 체계

| 카테고리 | 명령어 | 동작 |
|---------|-------|------|
| **research-gap (표준 시작점)** | `"리서치 갭 분석해줘"` | research-gap.md → gap-analyzer → research-plan.md (H-NN + 사용자 6) 검색 방향 반영) |
| **research-gap** | `"앵커 논문 찾아줘"` ⭐ | research-plan.md + research-gap.md '6) 앵커 논문 리서치 방향' → anchor-recommender → research-gap/anchor-candidates.md (후보 추천만, 채택 X). 사용자 정독 후 anchor 선별·이동 |
| **research-gap** | `"논문 분석해줘"` | 사용자가 papers/candidates/research-gap/으로 옮긴 PDF만 → gap-paper-analyst → papers/analyzed/research-gap/[R][D].*.md |
| **research-gap** | `"갭 리포트 만들어줘"` | analyzed/research-gap/[R][D].*.md 통합 → gap-synthesizer → gap-report.md |
| **분석** | `"flow 평가해줘"` | flow/flow.md 통합 평가 (claim-extractor + axis1~6 병렬 + aggregator) → flow/evaluations/latest/evaluation.md |
| **분석** | `"output 평가해줘"` | output/*.md 통합 평가 → output/evaluations/latest/evaluation.md |
| **분석** | `"final 평가해줘"` | final/complete-draft.md 6-axis + final-holistic-reviewer (통합 adjudication) → final/evaluations/latest/{evaluation,holistic-review}.md (통합본 부재 시 에러) |
| **분석** | `"final 평가해줘 --mode coursework"` | Oxford Coursework rubric (8 criteria × 6-band) — `final-coursework-evaluator` 단독 → coursework-evaluation.md (~3분) |
| **분석** | `"final 평가해줘 --mode coursework --committee"` | rubric + 5인 페르소나 위원회 절차 → coursework-committee-evaluation.md + committee/*.md |
| **분석** | `"final 평가해줘 --mode dissertation"` | Dissertation rubric (10 criteria) — `final-dissertation-evaluator` 단독 |
| **실행** | `"리서치 진행해줘"` | `research-gap/research-plan.md`(H-NN)·`flow/claim-extraction-flow.md`(R-NN) 양쪽 스캔 → 미해결 발견 시 사용자 1회 확인 후 Consensus 4-stage 파이프라인 → 결과를 `papers/search-results/{stage}.md`에 저장 |
| **실행** | `"논문 처리해줘"` | `papers/candidates/{research-gap,flow}/` 양쪽 스캔 → research-gap PDF는 gap-paper-analyst, flow PDF는 paper-analyst → `papers/analyzed/{stage}/[R][D]\|[A]\|[N].*.md` |
| **실행** | `"논문 재분석해줘"` | flow.md 변경 영향 paper에 v2 append (Mode B) |
| **실행** | `"비판적으로 분석해줘 X"` | critique_target=true → analyzed/{stage}/{X}.md에 비판 섹션 추가 (Mode C) |
| **실행** | `"이 논문 flow anchor로 분석해줘 Author_Year"` | research-gap 분석된 논문을 flow anchor frame으로 추가 분석 → `papers/analyzed/flow/[A].Author_Year.md` 신규 생성 (research-gap 분석은 보존) |
| **실행** | `"초안 작성해줘"` | flow → output 신규 작성 |
| **실행** | `"output {파일명} 수정해줘: ..."` | output-editor 자연어 수정 |
| **실행** | `"최종 완성했어"` ≡ `"최종 완성해줘"` | output/*.md → final/complete-draft.md 머지 |
| **실행** | `"적대적 리뷰 해줘"` | adversarial-reviewer 학파별 반박 시뮬 |
| **실행** | `"인용 확인해줘"` | citation_check output ↔ analyzed/*.md 정합성 |
| **실행** | `"참고문헌 만들어줘"` | analyzed/*.md frontmatter → bibliography.md |
| **메타** | `"현재 상태"` | 폴더 스캔 → 진행도·다음 권장 명령 한눈 |
| **메타** | `"버전 체크"` | 모든 파일 frontmatter version + based_on sync 검증 |
| **메타** | `"프로젝트 마이그레이션해줘 {P}"` | 옛 버전 폴더 구조 정리 (`scripts/migrate_project.py`) |
| **Flow 보강** | `"flow 업데이트해줘"` | flow-refiner interactive diff (사용자 승인 후 즉시 반영) |

**중요 원칙**:

1. **명령어 prefix는 옵션** — 사용자가 `flow` / `output` / `final` 명시 시 의도 우선 사용. 미명시 시 main agent가 폴더 컨텍스트로 자동 추론 (위 §"폴더 자동 추론 + 모호 시 선택지" 참조). 모호하면 1회 선택지 제시.

2. **분석 ≡ 평가**(혼용) — 두 표현 어느 쪽이든 같은 명령으로 인식. 사용자 자연스러운 표현 그대로.

3. **평가 명령 통합** — 이전의 `"X 레퍼런스 분석해줘"` + `"X 내용 분석해줘"` 두 명령은 **`"X 평가해줘"` 단일**로 통합. 내부적으로 claim-extractor(axis1 input) + axis1~6 병렬 모두 자동 dispatch. 별도 입력 줄일 필요 없음.

4. **stage flag 폐기, 폴더가 SSOT** — 명령어 prefix가 폴더를 지정. `mode_manager.py`·`.current-mode` 같은 hidden state 없음.

5. **`final` stage 사전 조건** — `final/complete-draft.md`가 없으면 `final 평가해줘` 거부. 사용자가 먼저 `"최종 완성했어"`로 통합본을 만들어야 함.

6. **Final stage 통합 평가 의무 (Coherence Prior)** — `최종 완성했어`로 통합본을 만들었다는 건 사용자가 *"이 글은 한 덩어리로서 정합성·흐름·메시지가 살아있다"*고 선언한 상태. 따라서 final 평가는:
   - 6축 결과는 *국소 진단*. 그것만으로 actionable로 보지 않음.
   - `final-holistic-reviewer`가 통합본 척추(메시지·thesis·논증 backbone·voice)를 prior로 받아 axis 카드를 adjudicate.
   - 5개 verdict로 분류: 🟢 APPLY · 🟡 APPLY-SCOPED · 🟠 DEFER · 🔵 REROUTE-{output|flow} · 🔴 REJECT(veto).
   - REJECT는 "결함은 있으나 적용 시 척추 net harm" → veto. REROUTE는 "결함이 thesis·구조 수준이라 final 본문 수정으로는 못 고침 → output/flow로 backtrack 필요" → 사용자 결정 사안.
   - 후속 명령(`Chapter X 수정해줘` 등)은 evaluation.md의 `holistic_verdict` 필드를 점검 후 적용. REJECT/DEFER/REROUTE 권고는 사용자 명시 override 없으면 skip.

7. **Final 평가 `--mode` 옵션 (Oxford rubric 단독 평가)**:
   - 기존 6-axis · holistic-reviewer · claim-extractor · aggregator **모두 skip**
   - 해당 mode evaluator 단독 dispatch — Oxford MSc Education marking rubric 적용
   - 산출: `final/evaluations/latest/{coursework|dissertation}-evaluation.md` (단일 파일)
   - mode evaluator는 `final/complete-draft.md`만 읽음. analyzed papers·flow·claim-extraction 일절 사용 X.
   - mode 옵션 없는 `final 평가해줘`는 기존 파이프라인 그대로 (6-axis + holistic). 두 모드는 완전 격리.

⛔ **Blind Protocol (모든 평가에 적용)** — `skills/BLIND-PROTOCOL.md` 준수. 모든 evaluator (axis 1-6 · claim-extractor · final-holistic · mode evaluators · 위원회 5인)는:
   - 같은 session에서 *이전 essay context · prior conversation history* 사용 X
   - 다른 essay와의 *anchoring · comparative reasoning · "한 칸 위/아래 등급"* 식 추론 X
   - 각 mark는 *rubric descriptor 직접 비교*만으로 결정 (어느 descriptor 매칭됐는지 명시)
   - **사용자 권고**: 한 conversation session = 한 essay 평가. 여러 essay는 각각 fresh conversation에서 실행

8. **Coursework 위원회 모드 (`--mode coursework --committee`, opt-in)** — Oxford PDF §3.3 절차를 그대로 모델링한 5-Phase 채점:
   - 5인 페르소나: Marker 1 (methods-leaning) · Marker 2 (theory-leaning) · Third Marker · External Examiner · Chair
   - Phase 1 (blind 병렬) → Phase 2 (reconciliation) → Phase 3 (Third, 조건부) → Phase 4 (External) → Phase 5 (Chair final)
   - 산출: `coursework-committee-evaluation.md` + `committee/*.md`
   - 비용: ~5× token, ~3-4× wall time. 제출 직전 정밀 채점 시뮬레이션 시 권장.

### 공통 실행 사이클

work-plan 카드 lifecycle은 폐기됨. 모든 실행 명령은 다음 단계:

```
① 폴더 스캔 — 입력 파일·미해결 항목 식별 (예: candidates/{stage}/*.pdf, search-results/*.md, claim-extraction-{stage}.md의 R-NN)
② 사용자 확인 (필요 시) — 양 폴더에 작업 있을 때 1회 확인
③ 실제 작업 (에이전트 dispatch)
④ 결과 파일 작성 — 약속된 경로에 원자 쓰기
⑤ evaluation.md 갱신 (평가 명령일 때) — 다음 액션 + 축별 상태 + 미해결 R-NN 반영
⑥ activity.log append
```

### 파싱 규칙

- `claim-extraction-{stage}.md`: `### R-NN —` 헤더로 R 섹션 식별
- `evaluation.md`: `## 🧭 다음 액션` 섹션 안 백틱 명령 추출
- `papers/search-results/{stage}.md`: `## R-NN` 헤더로 검색 완료 dedup
- `papers/analyzed/{stage}/[X].{name}.md`: 파일명 prefix가 분석 진행 상태 (`[R]` 대기 / `[R][D]` 완료 / `[A]` anchor / `[N]` normal)

### 자세한 포맷 규율

- `skills/EVALUATION-FORMAT.md` — evaluation.md 포맷 (work-plan 대체)
- `skills/RESEARCH-GAP-TEMPLATE.md` — research-gap.md 작성 가이드
- `skills/GAP-REPORT-FORMAT.md` — gap-report.md 포맷
- `skills/FLOW-TEMPLATE.md` — flow.md 작성 가이드
- `skills/BLIND-PROTOCOL.md` — 평가 blind 프로토콜

## 에이전트 시스템

이 스킬은 **36개의 에이전트**를 사용합니다 (research-gap 단계용 3개 포함). 각 에이전트의 상세 프롬프트와 노하우는 `skills/agents/` 폴더에 정의되어 있습니다. 에이전트를 호출할 때는 해당 파일의 전체 내용을 읽어서 Agent 도구의 prompt에 포함하세요.

**에이전트 분류 (5 카테고리, MECE)**:

1. **🧬 Synthesis** — 줄글 분해·thesis 발전·multi-paper 종합 (8): claim-extractor / gap-analyzer / gap-synthesizer / output-cross-paper-insights / thesis-developer / field-positioning-oracle / methodology-advisor / critical-companion
2. **✍️ Writing** — 작성·수정·번역 (4): writing-architect / output-editor / flow-refiner / output-en-translator
3. **⚔️ Critique** — 비판 시뮬 (3, 명령 분리 유지 — 사용자 mental model 보호): adversarial-reviewer (학파별 반박) / peer-reviewer (reviewer 채점) / steelman-dialectic (full dialectic loop)
4. **🎯 Evaluation** — axis 채점·verdict (15): evaluation-orchestrator + axis 1-6 + final-holistic-reviewer + final-coursework-evaluator + final-dissertation-evaluator + coursework 위원회 5인
5. **📚 Paper Processing** — PDF·검색·인용 (6): paper-analyst (flow) / gap-paper-analyst (research-gap) / output-gap-finder / research-processor / abstract-translator / citation-checker

**카테고리 원칙**:
- 단계별로 sweet spot이 다른 작업은 **별도 agent로 분리** (예: paper-analyst ↔ gap-paper-analyst, claim-extractor ↔ gap-analyzer). 통합하지 않음.
- 통합 X 이유: 분리가 frame leakage 방지·prompt 단순성·sweet spot 최적화·테스트 격리 측면에서 우위.
- MECE는 **카테고리·이름·문서화**로 달성. 코드 통합으로 달성하지 않음.

**모델 라우팅 원칙**: 작업 성격에 따라 서브에이전트를 다른 모델로 실행하여 비용·속도 최적화. 평가·글쓰기는 opus, 분석·검증은 sonnet, 번역 같은 기계적 작업은 haiku. 각 에이전트 정의 파일의 frontmatter `model` 필드에 기본값 표기. Agent 도구 호출 시 `model` 파라미터로 오버라이드 가능.

| 에이전트 | 파일 | 호출 시점 | 방식 |
|----------|------|-----------|------|
| **gap-analyzer** 🔬 | `skills/agents/gap-analyzer.md` | "리서치 갭 분석해줘" — research-gap.md → H-NN 분해 → research-plan.md (opus). **claim-extractor와 분리 — sweet spot 다름**: gap-discovery frame ("어디에 anchor가 비어 있나?", thesis 형성 *전* 가정) | 수동 (research-gap 진입점) |
| **gap-paper-analyst** 🔬 | `skills/agents/gap-paper-analyst.md` | research-gap PDF 갭 frame 분석 → [R][D].*.md (opus). **paper-analyst와 분리 — sweet spot 다름**: gap-discovery frame ("이 논문이 *무엇을 안 했나*?", 정량 추출표 8개) | 자동 ("논문 처리해줘"의 research-gap 분기) |
| **gap-synthesizer** 🔬 | `skills/agents/gap-synthesizer.md` | "갭 리포트 만들어줘" — 모든 [R][D] 통합 → 가설 매트릭스·분포 분석·갭 식별 (opus). **output-cross-paper-insights와 분리 — 분석 목적 정반대**: 이쪽은 *없는 것 찾기*, 그쪽은 *있는 것 찾기 (emergent pattern)* | 수동 |
| **evaluation-orchestrator** 🎯 | `skills/agents/evaluation-orchestrator.md` | "flow 평가해줘" — delta 감지 + 병렬 디스패치 + aggregate | 자동 (평가 진입점) |
| **axis1-reference-scorer** | `skills/agents/axis1-reference-scorer.md` | 축 1 레퍼런스 충실도 (sonnet) | 자동 (orchestrator dispatch) |
| **axis2-logic-scorer** | `skills/agents/axis2-logic-scorer.md` | 축 2 논리 전개 완성도 (opus) | 자동 |
| **axis3-defense-scorer** | `skills/agents/axis3-defense-scorer.md` | 축 3 반박·강화 논리 (opus, steelman tag 논문) | 자동 |
| **axis4-originality-scorer** | `skills/agents/axis4-originality-scorer.md` | 축 4 독창성·기여도 (opus, delta tag 논문) | 자동 |
| **axis5-concept-scorer** | `skills/agents/axis5-concept-scorer.md` | 축 5 구성개념 정의 정밀도 (sonnet) | 자동 |
| **axis6-critical-scorer** 🎭 | `skills/agents/axis6-critical-scorer.md` | 축 6 비판적 시각 (opus, minority tag 논문, ambition ≥ critical) | 자동 |
| **final-holistic-reviewer** 🛡 | `skills/agents/final-holistic-reviewer.md` | **stage=final 전용**. aggregator 직후 dispatch. 통합본 척추 articulation (Phase A) + 통합 전용 검사 (Phase B) + 6축 카드 adjudication (Phase C, 5 verdict) + protected revision plan (Phase D). evaluation.md WRITE 권고에 `holistic_verdict` prefix 부여 (opus) | 자동 (final stage orchestrator) |
| **final-coursework-evaluator** 🎓 | `skills/agents/final-coursework-evaluator.md` | **`final 평가해줘 --mode coursework` 한정**. Oxford Coursework rubric (8 criteria × 6-band). `--committee` 없으면 단독 평가, 있으면 5-Phase orchestrator로 작동 (opus) | 자동 (--mode coursework) |
| **coursework-marker-1** 👤 | `skills/agents/coursework-marker-1.md` | **위원회 모드 한정**. Internal Examiner, methods-leaning 페르소나. Phase 1 blind 채점. 구조·rigour·체계 strict (opus) | 자동 (위원회 Phase 1) |
| **coursework-marker-2** 👤 | `skills/agents/coursework-marker-2.md` | **위원회 모드 한정**. Internal Examiner, theory-leaning 페르소나. Phase 1 blind 채점. 이론·비판·독창성 strict (opus) | 자동 (위원회 Phase 1) |
| **coursework-third-marker** 👤 | `skills/agents/coursework-third-marker.md` | **위원회 모드 한정**. Senior Generalist 페르소나. Phase 3 blind tie-breaker (Marker 1·2 합의 실패 시만 발동) (opus) | 조건부 (위원회 Phase 3) |
| **coursework-external-examiner** 👤 | `skills/agents/coursework-external-examiner.md` | **위원회 모드 한정**. External Examiner 페르소나. Phase 4 cross-field calibration. raw mark 미부여 (opus) | 자동 (위원회 Phase 4) |
| **coursework-chair** 👤 | `skills/agents/coursework-chair.md` | **위원회 모드 한정**. Chair of Examiners. Phase 5 reconciliation·최종 mark 결정. PDF §3.3 절차 준수 (opus) | 자동 (위원회 Phase 5) |
| **final-dissertation-evaluator** 🎓 | `skills/agents/final-dissertation-evaluator.md` | **`final 평가해줘 --mode dissertation` 한정**. Oxford MSc Education Dissertation rubric (10 criteria × 6-band, methodology stack 포함). 통합본 단독 평가. 6-axis·holistic·claim-extractor 미사용 (opus) | 자동 (--mode dissertation) |
| **claim-extractor** 📝 | `skills/agents/claim-extractor.md` | 줄글 flow/output 문장 주장 추출 → R-NN 식별 (axis1 선행). **gap-analyzer와 분리 — sweet spot 다름**: thesis-supportive frame ("이 주장의 근거는?") | 자동 |
| **critical-companion** 🤔 | `skills/agents/critical-companion.md` | Socratic 질문 생성 + commitment 추출 (마일스톤마다 자동). **steelman-dialectic과 분리** — 이쪽은 *질문→답변→commitment*, steelman은 *full dialectic loop (critic→답변→재반박→thesis 정교화)* | 자동/수동 |
| **paper-analyst** | `skills/agents/paper-analyst.md` | flow PDF 분석 (Mode A 분석 / B 재분석 / C 비판). **gap-paper-analyst와 분리 — sweet spot 다름**: thesis-supportive frame (anchor [A]/normal [N], "이 논문을 본 글에 어떻게 활용?") | `논문 처리해줘` 진입점 |
| **thesis-developer** 🌱 | `skills/agents/thesis-developer.md` | "thesis 발전시켜줘" — implicit assumption·tension·extension·operationalization (generative phase) | 자동/수동 |
| **output-cross-paper-insights** 🔍 | `skills/agents/output-cross-paper-insights.md` | "cross-paper insight 찾아줘" — output 단계 N편 paper emergent pattern·field-level implicit assumption·citation silence. **gap-synthesizer와 분리 — 정반대 목적**: 이쪽은 *있는 패턴 발견*, 그쪽은 *없는 갭 발견* | 자동/수동 |
| **steelman-dialectic** ⚔️ | `skills/agents/steelman-dialectic.md` | "steelman 해줘" — 최강 critic 구축 + 사용자 답변 + critic 재반박 + thesis 정교화. **critical-companion과 분리** — 이쪽은 *full dialectic loop*, 그쪽은 *질문→답변→commitment* | 자동/수동 |
| **field-positioning-oracle** 🧭 | `skills/agents/field-positioning-oracle.md` | "field positioning 분석해줘" — 학파 좌표 + thesis novel positioning 옵션 + 추천 (generative phase, writing-architect Phase 0 직전) | 자동/수동 |
| **writing-architect** ✍️ | `skills/agents/writing-architect.md` | "초안 작성" Phase 0 (positioning) / Phase 1 (outline) / Phase 1.5 (adversarial review) / Phase 2 (chapter별 작성 + self-critique loop) / Phase 2.5 (chapter critique) / Phase 3 (peer-review 시뮬). Elite Scholarly 패턴 (layered argumentation·counterargument anticipation·quote framing·scholarly voice·novel synthesis·self-critique). | 자동 |
| **output-editor** ✏️ | `skills/agents/output-editor.md` | "Chapter X 수정해줘" (기존 챕터 국소 수정 + adversarial-reviewer Phase 2.5 결과 자동 적용) | 자동 |
| **flow-refiner** 📝 | `skills/agents/flow-refiner.md` | "flow 업데이트해줘" (flow.md diff 제안만) | 자동 |
| **citation-checker** | `skills/agents/citation-checker.md` | chapter 수정 후 자동 + 평가(output/final stage) 자동 체이닝 (Stage별 샘플→전량 escalate) | 자동 |
| **output-gap-finder** | `skills/agents/output-gap-finder.md` | output 단계 — 분야 빈틈 탐색 (방법론·응용·데이터·이론·시간 5종 Gap). **research-gap 단계의 gap-analyzer/gap-paper-analyst/gap-synthesizer와 분리**: 이쪽은 *output 글*에서 약점 위치 찾기, 그쪽은 *thesis 형성 전*의 분야 anchor 탐색 | 수동 |
| **methodology-advisor** | `skills/agents/methodology-advisor.md` | "방법론 추천/검증해줘" (empirical 프로젝트 전용) | 수동 |
| **peer-reviewer** ⚔️ | `skills/agents/peer-reviewer.md` | **저널 reviewer 채점** 시뮬 + reviewer comment 답변 연습. Iconoclast 페르소나 ambition ≥ critical 시 자동 추가 | 수동 ("리뷰 체크해줘") |
| **abstract-translator** 🌐 | `skills/agents/abstract-translator.md` | RESEARCH 결과/PDF abstract 한글 번역 (haiku 모델) | 자동 (RESEARCH 단계 2 내장) |
| **output-en-translator** 🇬🇧 | `skills/agents/output-en-translator.md` | 한글 chapter/output을 학술 영어로 번역 — 인용·hedging·voice 보존, 분야 컨벤션(APA 등) 적용 (opus 모델). 사전 조건: writing-architect Phase 2 + adversarial-reviewer + output-editor + citation-checker 통과 후 | 수동 ("영어로 번역해줘") |

### 에이전트 호출 방법

에이전트를 호출할 때는 Agent 도구를 사용하세요:

1. 해당 에이전트 파일(`skills/agents/{agent-name}.md`)을 Read 도구로 읽기
2. 에이전트 프롬프트에 다음을 포함:
   - 에이전트 파일의 전체 내용 (노하우 + 출력 형식)
   - 현재 프로젝트의 flow.md 내용
   - 처리할 대상 파일 경로
3. Agent 도구로 실행 (독립된 컨텍스트에서 작업)
4. 결과를 지정된 파일에 저장

### ⚔️ 비판 시뮬 3종 활용 가이드

세 agent는 **비판을 시뮬레이션**하지만 sweet spot이 다릅니다. 단일 명령으로 통합하지 않은 이유: 각자의 활용 시점·결과가 명확히 달라야 사용자가 *언제 무엇을 부를지* 의식적으로 선택 가능 (mental model 보호).

| 상황 | 호출 명령 | Agent | 산출 |
|---|---|---|---|
| Section 결론 직전 — *학파별 반박을 미리 막기* | `"적대적 리뷰 해줘"` | adversarial-reviewer | 학파(예: Vygotskyan)별 단락 단위 반박 + 선제 차단 권고 |
| 출고 직전 — *저널 reviewer가 채점한다면?* | `"리뷰 체크해줘"` | peer-reviewer | reviewer 시뮬 채점 + reviewer comment 답변 연습 |
| Thesis 정교화 — *가장 강한 반론을 만들어 보강* | `"steelman 해줘"` | steelman-dialectic | full dialectic loop (critic 구축 → 답변 → 재반박 → thesis 정교화) |

main agent가 사용자 의도를 파악하지 못하면 위 표를 기반으로 **선택지 제시**:
> "비판 시뮬 종류가 3가지인데 어느 것이 필요하신가요?
> 1. 학파별 반박 (adversarial)
> 2. reviewer 채점 (peer)
> 3. thesis 정교화 (steelman)"

### 🤔 critical-companion vs ⚔️ steelman-dialectic 명문화

둘 다 *비판적 사고를 자극*하지만 도구가 다름.

| | critical-companion | steelman-dialectic |
|---|---|---|
| 카테고리 | 🧬 Synthesis | ⚔️ Critique |
| 입력 | flow/output + 직전 평가 | thesis 명제 |
| 출력 | 질문 리스트 + commitment 추출 | full dialectic loop (critic 답변 재반박) |
| 호출 | 마일스톤 자동 (initial / post-research / post-draft / pre-final) | 사용자 명시 (`"steelman 해줘"`) |
| 사용자 부담 | 답변 작성 → commitment 자동 추출 | dialectic 라운드 참여 |
| 결과 파일 | `critical/critical-questions.md` + `critical-commitments.md` | `output/.internal/generative/steelman-dialectic.md` |

→ **둘은 다른 도구. 통합 안 함**.

### 🗺 폴더 자동 추론 + 모호 시 선택지 (사용자 인터페이스 핵심)

**원칙**: 사용자는 *작업 의도*만 자연어로 입력. main agent가 폴더 컨텍스트로 단계를 추론. 모호하면 선택지 제시.

폴더 자체가 SSOT — agent·script·main agent 모두 stage flag 추적 안 함. metadata에 `stage:` 같은 field 저장도 금지 (이전 폐기 결정 — LLM이 누락하거나 세션 종료 시 휘발).

**자동 추론 규칙** (main agent가 매 명령마다 폴더 스캔):

| 명령 패턴 | main agent 분기 |
|---|---|
| `"평가해줘"` (prefix 없음) | `flow.md` 있고 `flow/evaluations/latest/` 부재 → flow / `output/0N-*.md` 있고 flow 평가 후 → output / `final/complete-draft.md` 있음 → final / 동시 진행 모호 → 선택지 |
| `"X 평가해줘"` (prefix 있음, X = flow/output/final) | 명시 의도 우선, 그대로 실행 (옵션 — 강제 아님) |
| `"논문 처리해줘"` | `papers/candidates/{research-gap, flow}/` 양쪽 스캔 → 한쪽만 → 자동 / 양쪽 다 → 1회 확인 |
| `"리서치 진행해줘"` | `research-gap/research-plan.md` H-NN + `flow/claim-extraction-flow.md` R-NN 양쪽 스캔 → 미해결 발견 시 사용자 1회 확인 |
| `"갭 분석해줘"` | `research-gap/research-gap.md` 있고 미실행 → gap-analyzer (research-gap 진입점) / `output/0N-*.md` 있음 → output-gap-finder / 둘 다 → 선택지 |
| `"비판 시뮬해줘"` (페르소나 미명시) | 위 §"비판 시뮬 3종 활용 가이드" 표 기반 선택지 |
| `"수정해줘"` (대상 미명시) | `output/0N-*.md` 있음 → output-editor / `flow/flow.md`만 있음 → flow-refiner / 모호 → 선택지 |

**선택지 제시 패턴** (모호 시):
```
어느 작업을 의도하셨나요?
1. {옵션 1} — {짧은 설명}
2. {옵션 2} — {짧은 설명}
숫자 입력 또는 자연어로 답변.
```

**stage prefix는 옵션** (강제 X):
- 사용자가 명시하면 그 의도 우선 사용
- 미명시면 폴더 추론 + 모호 시 선택지
- "X 평가해줘 prefix 누락 에러"식 강제 폐기 — 의도 명시 시 효율↑, 안 해도 무난

### 🛡 LLM 정책 거부 (Usage Policy false positive) Fallback v3.2

학술 논문 분석은 cross-cultural / WEIRD critique / methodological critique 콘텐츠를 다룰 수 있고, Anthropic 자동 정책 분류기가 학술 작업을 false positive로 거부하는 케이스 발생. 거부 패턴:

> `API Error: Claude Code is unable to respond to this request, which appears to violate our Usage Policy ...`

이는 시스템 정상 동작이며 **사용자 책임이 아님**. main agent가 자동 우회.

### ⚠ Layer 0 — 절대 규칙 (실측 학습)

**main agent는 paper body 직접 Read 절대 금지**. paper 본문이 분류기에 걸리면 main agent의 Read tool 결과 자체가 거부되어 **대화 세션이 죽고 복구 불가**.

- ❌ main agent는 `papers/markdown/{canonical}.md` 본문 절대 Read 안 함
- ❌ "main agent 직접 처리" final fallback 폐기 (이전 spec의 step 5)
- ✅ paper 본문 read는 **반드시 sub-agent dispatch 안에서만** — sub-agent는 자기 컨텍스트에서 거부돼도 main 세션은 안전

### 실측 학습 (Doebel 2020 케이스)

1. **방어적 학술 boilerplate 역효과** — "cross-cultural / WEIRD / political 데이터는 학술 메타분석" 같은 메타 진술이 *오히려* 트리거 단어 누적으로 거부율 ↑. 분류기는 컨텍스트를 이해하지 않고 단어를 본다.
2. **opus 분류기가 더 엄격** — prompt 정제만으로 opus 통과 어려움.
3. **sonnet + 미니멀 prompt = robust** — 1차 통과. 인용 7개·페이지 번호·stance/use 메타·cross-ref 모두 충분 작동.
4. **수정된 원칙**: 모델은 *고정 우선*이지만 분류기 거부 시 **sonnet 강등이 prompt 정제보다 효과적**. 따라서 모델 강등을 정식 fallback step으로 편입.

### Fallback Chain (paper-analyst v3.2 정합)

| 단계 | 조치 | 거부율 영향 | quality 영향 |
|-----|------|-----------|--------------|
| **1** | **미니멀 prompt baseline** — 학술 컨텍스트는 작업 동사로 짧게 ("학술 인용 노트 작성 task"). **방어적 boilerplate 금지** (cross-cultural / WEIRD / racial 메타 진술 X). 트리거 단어 정제: "비판 타겟" → "이론 비교 대상", "공격" → "검토". | 중 ↓ | 무영향 |
| **2** | **Prompt 단계 분할** — sub-agent를 여러 번 dispatch. ① 메타데이터 + 핵심 주장 ② 인용 후보 추출 ③ 본 글 활용·cross-ref. 각 step도 step 1 baseline 유지. | 큰 폭 ↓ | 무영향 (병합 시 동일) |
| **3** | **Same-model retry** — 같은 opus·prompt 1-2회 재시도 (classifier noise). | 중 ↓ | 무영향 |
| **4** | **모델 강등 opus → sonnet** ★ **실측 가장 효과적**. Step 1 baseline prompt 그대로, 모델만 sonnet으로. frontmatter `model_used: sonnet` 기록. A-anchor 품질에서 sonnet 결과도 7 quotes·페이지 번호·stance/use·cross-ref 모두 충분 (실측 검증). | 0 (거의 항상 통과) | 약간 ↓ (sonnet은 nuance 인용 정밀도가 opus보다 얕을 수 있음) |
| **5** | **Chunk-based partial analysis** — 페이지 단위 chunk Read·분석. 트리거 chunk paraphrase로 우회. frontmatter `policy_quarantined_pages: [N, M]` 기록. (드문 케이스) | 0 | 부분 분석 (인용 일부 paraphrase) |
| **6** | **Skip + 사용자 보고 (final)** — frontmatter `policy_blocked: true` + `last_attempt: <ISO>`. 파일명 `[A]`/`[N]` skeleton 유지 (rename 안 함). 사용자에게 보고: "X편 정책 거부로 분석 불가 — 수동 처리 필요". | — | — |

### 적용 대상

paper-analyst (Mode A-anchor·B·C), output-gap-finder, peer-reviewer (Iconoclast 페르소나), critical-companion, axis6-critical-scorer.

### Main agent 동작

1. Layer 0 절대 규칙 준수 (paper body 직접 Read 금지)
2. 1차 sub-agent dispatch는 step 1 baseline (미니멀 prompt, 방어 boilerplate 금지)
3. 정책 거부 응답 감지 시 자동 step 2 → 3 → 4 → 5 → 6 (silent, 사용자에게 묻지 않음)
4. step 6까지 가면 사용자 보고 + 수동 처리 결정 요청
5. activity.log: `policy-fallback | paper={canonical} | mode={X} | passed_at_step={1-6} | model={opus|sonnet}`

### 거부 발생 paper 기록

- frontmatter `policy_fallback_step: {1-6}` — 다음 재분석 (Mode B) 시 처음부터 해당 step 적용
- frontmatter `model_used: opus | sonnet` — 어떤 모델로 통과했는지

### 예방 — Prompt 작성 baseline (모든 호출 1차부터 적용)

- 학술 컨텍스트는 *작업 동사*로 짧게 ("학술 인용 노트 작성 task")
- **방어적 boilerplate 금지** ("본 작업은 ... cross-cultural 데이터는 학술 활동" 같은 메타 진술 X)
- 트리거 단어 정제: "비판 타겟" → "이론 비교 대상", "공격" → "검토", "도전" → "관점 차이"
- PDF 본문 직접 인용은 인용블록 + 페이지: `> "..." (p.N)` 형식
- paper의 cross-cultural / methodological 데이터는 학술 인용 메타와 함께: "이 paper는 ... 보고한다", "저자는 ...라 주장한다"

**거부 발생 paper 기록**: paper의 frontmatter에 `policy_fallback_step: {1-4}` 기록. 다음 재분석 (Mode B) 시 처음부터 해당 step 이후 prompt 사용 (불필요한 1단계 retry 생략).

## 프로젝트 생성

사용자가 "프로젝트 만들어줘", "[이름] 프로젝트 생성", "[이름] 과제 만들어줘" 등을 말하면:

### 단계 1: projects 폴더 확인

현재 research-agent 폴더에 있는지 확인하고, projects 폴더가 없으면 생성:

```bash
mkdir -p projects
```

### 단계 2: 프로젝트 폴더 구조 생성

프로젝트 이름을 추출하여 다음 폴더 구조를 생성하세요:

```bash
# papers/ — 모든 단계가 공유하는 paper 자산 단일 hub
mkdir -p projects/{PROJECT_NAME}/papers/candidates/research-gap
mkdir -p projects/{PROJECT_NAME}/papers/candidates/flow
mkdir -p projects/{PROJECT_NAME}/papers/collected
mkdir -p projects/{PROJECT_NAME}/papers/analyzed/research-gap
mkdir -p projects/{PROJECT_NAME}/papers/analyzed/flow
mkdir -p projects/{PROJECT_NAME}/papers/search-results
mkdir -p projects/{PROJECT_NAME}/papers/.research-raw
mkdir -p projects/{PROJECT_NAME}/papers/.translations
mkdir -p projects/{PROJECT_NAME}/papers/.curation

# 단계별 작성 폴더
mkdir -p projects/{PROJECT_NAME}/research-gap
mkdir -p projects/{PROJECT_NAME}/flow
mkdir -p projects/{PROJECT_NAME}/output/history
mkdir -p projects/{PROJECT_NAME}/final
mkdir -p projects/{PROJECT_NAME}/history
```

### 단계 2b: evaluations 폴더 구조 생성

```bash
mkdir -p projects/{PROJECT_NAME}/flow/evaluations/latest
mkdir -p projects/{PROJECT_NAME}/output/evaluations/latest
mkdir -p projects/{PROJECT_NAME}/final/evaluations/latest
```

**경로 규약**:
- **`research-gap/`** (표준 시작점): research-gap.md, research-plan.md, gap-report.md, history/
- **`flow/`**: flow.md, FLOW-TEMPLATE.md, claim-extraction-flow.md, evaluations/, history/
- **`output/`**: 실제 챕터 파일(`0N-*.md`), claim-extraction-output.md, evaluations/, history/{chapter_id}/
- **`final/`**: complete-draft.md, evaluations/, .docx (최종)
- **`papers/`**: 모든 단계의 PDF·분석·검색 결과 — 단계별 서브폴더로 frame 격리
- **`{stage}/evaluations/latest/`**: evaluation.md (work-plan 대체) + axis1~6-*.md
- **work-plan.md 폐기** — 평가 결과·다음 액션·미해결 R-NN 등 모두 evaluation.md로 통합. card_registry·status JSON 없음 (폴더 자체가 SSOT).

### 단계 2c: .sync-state.json 초기화

```bash
python3 scripts/sync_state.py init {PROJECT_NAME}
```

이 파일은 flow.md·papers·chapters·evaluations·final 간 의존성을 추적하여 아티팩트가 조용히 어긋나는 것을 방지한다. 모든 주요 명령이 실행 전 `check`, 실행 후 `update-*`로 이 파일을 갱신한다.

### 단계 3: 작성 가이드 및 시작 파일 생성

#### 3a. flow 단계용 (필수)

projects/{PROJECT_NAME}/flow/FLOW-TEMPLATE.md 와 projects/{PROJECT_NAME}/flow/flow.md 두 파일을 생성하세요.

- **FLOW-TEMPLATE.md**: `skills/FLOW-TEMPLATE.md`의 내용을 복사. 줄글(prose) 작성 가이드.
- **flow.md**: 빈 파일 + 메타데이터 골격:
  ```markdown
  # [과제명]

  과제명: 
  코스: 
  마감: YYYY-MM-DD
  분량: 
  인용 스타일: APA

  ---

  (여기에 줄글로 자유롭게 작성. 연구 질문과 핵심 주장은 반드시 한 문장씩 명시.
   작성법은 FLOW-TEMPLATE.md 참고. 완료 후 "flow 평가해줘" 입력.)
  ```

#### 3b. research-gap 단계용 (표준 — 모든 프로젝트에서 자동 생성)

`projects/{P}/research-gap/RESEARCH-GAP-TEMPLATE.md`와 `projects/{P}/research-gap/research-gap.md` 두 파일을 자동 생성하세요.

- **RESEARCH-GAP-TEMPLATE.md**: `skills/RESEARCH-GAP-TEMPLATE.md` 내용 복사 (참고용)
- **research-gap.md**: 빈 파일 + 메타데이터 골격 + 4 요소 안내:
  ```markdown
  # [주제명]

  주제명: 
  필드: 
  잠정 마감: YYYY-MM-DD

  ---

  (여기에 줄글로 자유롭게 작성. 작성 가이드는 RESEARCH-GAP-TEMPLATE.md 참고.

  자연스럽게 담을 4 요소:
  1. **문제의식**: 어떤 영역이 궁금한가? 왜?
  2. **잠정 thesis** (provisional, 거칠어도 OK)
  3. **확인하고 싶은 것**: 선행 연구가 무엇을 다뤘는지 알고 싶은 항목
  4. **본인 가정·전제**

  작성 완료 후 "리서치 갭 분석해줘" 입력 → research-plan.md 자동 발급.

  ❗ 이미 thesis가 명확해서 research-gap 단계 건너뛰려면 이 파일을 비워두고
     바로 flow/flow.md부터 작성하면 됩니다.)
  ```

**모든 프로젝트에서 자동 생성**. research-gap.md는 표준 시작점이지만, 사용자가 의식적으로 비워두면 그 단계 자동 skip (폴더가 SSOT). thesis 이미 명확해서 건너뛸 사용자는 그냥 flow.md부터 작성하면 됨 — 시스템이 강제하지 않음.

**작성 방식**: 사용자가 자유 줄글(prose)로 작성하면 시스템이 가설 H-NN(research-gap) 또는 R-NN(flow) 단위로 자동 분석합니다. 구조적 템플릿을 강요하지 않습니다.

### 단계 4: .paper-metadata.json 생성

projects/{PROJECT_NAME}/.paper-metadata.json 파일을 다음 내용으로 생성하세요:

```json
{
  "papers": [],
  "last_updated": null,
  "project_name": "{PROJECT_NAME}",
  "version": "1.2",
  "research_type": null,
  "intellectual_ambition": "incremental"
}
```

`research_type`은 사용자가 flow.md 작성 후 첫 `"flow 평가해줘"` + `"flow 평가해줘"` 실행 시 자동 판별하여 채워진다:
- `"theoretical"` — 이론·개념 에세이 (기존 개념 비판, 새 프레임워크 제안)
- `"empirical"` — 경험 연구 (데이터 수집·분석·해석)

**추가 필드: intellectual_ambition** (질문 강도 + axis6/Iconoclast 활성 조절):

```json
{
  ...
  "research_type": "theoretical",
  "intellectual_ambition": "incremental"
}
```

3단계 값:
- `"incremental"` (기본): 분야 내 점진적 기여. critical-companion·axis6-critical-scorer·Iconoclast 비활성.
- `"critical"`: 비판적 시각을 능동적으로 지원. 위 3개 agent 자동 체이닝. Hedging 기본 엄격도 유지.
- `"paradigm-shifting"`: 대담한 주장을 방어. Hedging 관대, 비주류 인용 환영, 모든 critical agent 자동 호출.

**용도**: 
- `theoretical`인 프로젝트에서는 methodology-advisor 명령을 **명령 추천 목록에서 숨김**
- `critical` 이상인 프로젝트에서는 **critical-companion·axis6-critical-scorer·peer-reviewer Iconoclast**를 자동 체이닝
- `paradigm-shifting`인 프로젝트에서는 **peer-reviewer가 Iconoclast를 주 심사자로 승격**, 대담한 주장 penalty 완화

### 단계 5: 안내 메시지 출력

프로젝트 생성 완료 후 다음과 같이 사용자에게 안내하세요:

```
✅ 프로젝트 생성 완료: projects/{PROJECT_NAME}/

📁 구조:
   research-agent/
   └── projects/
       └── {PROJECT_NAME}/
           ├── research-gap/                    (표준 시작점 — 모든 프로젝트 기본)
           │   ├── research-gap.md              (사용자 줄글, 빈 템플릿 자동 생성)
           │   ├── RESEARCH-GAP-TEMPLATE.md     (가이드 — 수정 금지)
           │   ├── research-plan.md             (gap-analyzer 산출 H-NN별 검색 계획)
           │   ├── gap-report.md                (gap-synthesizer 통합 리포트)
           │   └── history/
           ├── flow/
           │   ├── flow.md                      (실제 작성용)
           │   ├── FLOW-TEMPLATE.md             (가이드 — 수정 금지)
           │   ├── claim-extraction-flow.md     (R-NN 자동 생성)
           │   ├── evaluations/latest/          (evaluation.md + axis1~6)
           │   ├── critical/                    (🎭 critical-questions.md)
           │   └── history/
           ├── output/
           │   ├── 0N-*.md                      (초안 각 섹션)
           │   ├── claim-extraction-output.md   (자동 생성)
           │   ├── evaluations/latest/
           │   ├── critical/
           │   ├── feedback.md                  (사용자 피드백)
           │   ├── .internal/                   (writing-spec.md 등 internal)
           │   └── history/{chapter_id}/
           ├── final/
           │   ├── complete-draft.md            ("최종 완성했어" 후 생성)
           │   └── evaluations/latest/
           ├── papers/                          (모든 단계 paper 자산 단일 hub)
           │   ├── candidates/
           │   │   ├── research-gap/            (research-gap PDF 입구)
           │   │   └── flow/                    (flow PDF 입구)
           │   ├── collected/                   (논문당 1개 PDF, 단계 공유)
           │   ├── analyzed/
           │   │   ├── research-gap/            ([R].* 대기, [R][D].* 완료)
           │   │   └── flow/                    ([A].* anchor, [N].* normal)
           │   ├── search-results/
           │   │   ├── research-gap.md          (anchor 검색 결과)
           │   │   └── flow.md                  (thesis-supportive 검색 결과)
           │   ├── .research-raw/                   (Stage A — MCP 원본 응답 JSON)
           │   ├── .translations/               (Stage B — haiku 한글 번역)
           │   ├── .curation/                   (Stage C — 6 카테고리 curated)
           │   └── .context-pack.md             (workers 공유 입력)
           ├── critical-commitments.md          (🎭 답변에서 추출한 actionable spec, cross-stage)
           ├── activity.log                     (모든 명령 자동 로그)
           ├── .paper-metadata.json             (메타데이터 + intellectual_ambition)
           └── history/                          (단계 변경·snapshot 보관)

👉 다음 단계:
   표준 4단계 흐름: research-gap → flow → output → final
   research-gap·flow 빈 템플릿이 자동 생성되었습니다. 사용자 상황에 따라
   research-gap·flow 중 어디서 시작할지 선택하세요.

   📌 표준 (분야 anchor 탐색부터):
     1. projects/{PROJECT_NAME}/research-gap/research-gap.md 작성 (줄글, 4 요소 안내 포함)
     2. "리서치 갭 분석해줘" → research-plan.md (H-NN별 anchor 검색 계획)
     3. "리서치 진행해줘" → papers/search-results/research-gap.md (anchor 후보)
     4. PDF 다운로드 → papers/candidates/research-gap/ 에 떨어뜨림
     5. "논문 처리해줘" → papers/analyzed/research-gap/[R][D].*.md
     6. "갭 리포트 만들어줘" → research-gap/gap-report.md (한눈에 보는 갭)
     7. flow.md 작성 (잠정 thesis 다듬어 정식 outline) → 다음 단계로

   ⏩ thesis 이미 명확하면 (research-gap 의식적 생략):
     1. research-gap/research-gap.md는 **그대로 비워두기** (시스템이 자동 skip)
     2. projects/{PROJECT_NAME}/flow/flow.md 작성 (RQ + Thesis 1문장씩 명시)
     3. "평가해줘" → flow 평가
     4. 이후 "리서치 진행해줘" → "논문 처리해줘" → "초안 작성해줘"

   필요하면 시스템이 자연어로 도와줍니다 — 정확한 명령어 외울 필요 없습니다.
   ("어디까지 왔지?", "이거 어떻게 보강해야 할까?", "근거 좀 더 찾아줘" 등)
```

### 단계 6: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "프로젝트 생성" "stage=init" "target={PROJECT_NAME}" "result=created" "ambition=incremental"
```

---

## 🎯 6축 평가 (evaluation-orchestrator, 병렬 delta 아키텍처)

평가는 **stage별 단일 통합 명령**:
- `"flow 평가해줘"` (= `"flow 분석해줘"`)
- `"output 평가해줘"`
- `"final 평가해줘"`

이전의 `"X 레퍼런스 분석해줘"` + `"X 내용 분석해줘"` 분리는 폐기. 단일 명령이 claim-extractor(axis1 input) + axis1~6 병렬 모두 자동 dispatch.

**stage prefix는 옵션**: 사용자 명시 시 그대로 사용. 미명시 시 main agent가 폴더 추론 (예: flow.md 있고 flow/evaluations/latest 없음 → flow 평가). 모호하면 1회 선택지 제시.

**플래그 지원**:
- `"output 평가해줘"` — delta 모드 (변경된 축만 재계산, 기본)
- `"output 평가해줘 --full"` — 전체 6축 강제 재실행
- `"output 평가해줘 axis3,4"` — 명시 축만 실행 (쉼표 구분)

### 단계 0a: 최소 요구사항 검증 (gate)

`flow/flow.md`가 다음 **최소 요건**을 만족하는지 먼저 확인:

1. 파일 자체가 존재
2. **연구 질문(RQ) 1문장** 명시 (예: `## 연구 질문` 섹션 또는 `"이 글은 X를 묻는다"` 패턴)
3. **핵심 주장(Thesis) 1문장** 명시 (예: `## Thesis` 섹션 또는 `"본 에세이는 Y라고 주장한다"` 패턴)
4. 전체 **최소 100자 이상**의 본문 내용

미달이면 평가 중단하고 안내:
```
⚠️ flow.md 최소 요건 미달

필요:
  [ ] 연구 질문 1문장
  [ ] 핵심 주장 1문장
  [ ] 본문 최소 100자

현재: {체크 결과}

"flow/flow.md"를 먼저 채운 후 다시 "flow 평가해줘"를 실행하세요.
`flow/FLOW-TEMPLATE.md`를 참고하세요.
```

### 단계 0b: Sync 선행 점검 (gate)

`python3 scripts/sync_state.py check {PROJECT_NAME}` 실행 — Critical stale 시 사용자 확인, Minor stale 시 경고만, Clean 시 진행.

### 단계 1: stage 결정 (사용자 prefix 그대로)

- `"flow 평가해줘"` → stage=`flow`, 대상 `flow/flow.md`
- `"output 평가해줘"` → stage=`output`, 대상 `output/*.md`
- `"final 평가해줘"` → stage=`final`, 대상 `final/complete-draft.md` (부재 시 에러: "먼저 '최종 완성했어'로 통합본 만들어주세요")

자동 감지 없음. 사용자 명시 prefix로만 결정.

### 단계 2: Delta 감지

```bash
python3 scripts/evaluation_delta.py check {PROJECT_NAME} --stage={flow|output|final}
```

출력(JSON)에서 `stale_axes` 배열을 얻는다. 이것이 이번에 재계산할 축 집합.

**Critical Mode 보정**: `.paper-metadata.json`의 `intellectual_ambition >= critical`이면 `axis6`을 `stale_axes`에 강제 포함 (critical-questions 변경 감지 필수).

**플래그 처리**:
- `--full` → 먼저 `scripts/evaluation_delta.py reset {PROJECT_NAME}` 실행 → 전체 6축 stale로 만들고 check
- `axisN,M` → stale_axes를 명시 집합으로 덮어쓰기

### 단계 3: Archive 스냅샷

```bash
python3 scripts/sync_state.py snapshot-evaluation {PROJECT_NAME} {stage}
```
기존 `evaluations/latest/`를 `history/{stage}/evaluations/{NNN}-{date}-{stage}/`로 복사. 이후 새 점수는 `latest/`에 덮어쓴다.

### 단계 4: claim-extractor 선행 호출 (자동 재분석)

stage는 사용자 prefix 그대로 (`flow | output | final`). 각 stage 폴더 안의 `claim-extraction-{stage}.md`에 출력.

| Stage | 조건 | 호출 전 snapshot | 호출 | 출력 |
|-------|------|------------------|------|------|
| flow   | `flow/flow.md` mtime > `flow/claim-extraction-flow.md` (또는 부재) | `sync_state.py snapshot-flow {P} pre-claim-extract` | claim-extractor(stage=flow) | `flow/claim-extraction-flow.md` |
| output | 어느 `output/*.md` mtime > `output/claim-extraction-output.md` (또는 부재) | 변경된 각 챕터마다 `sync_state.py snapshot-output {P} pre-claim-extract {chapter}` | claim-extractor(stage=output) | `output/claim-extraction-output.md` |
| final  | `final/complete-draft.md` mtime > `final/claim-extraction-final.md` (또는 부재) | `sync_state.py snapshot-final {P} pre-claim-extract` | claim-extractor(stage=final) | `final/claim-extraction-final.md` |

이미 최신이면 스킵. final stage 평가 시 `final/complete-draft.md`가 없으면 진행 거부.

### 단계 5: 축별 워커 병렬 디스패치

`stale_axes`에 포함된 축 각각을 **하나의 응답에서 동시에 Agent 도구로 호출**.

| 축 | 에이전트 파일 | 모델 | 출력 파일 |
|----|--------------|------|----------|
| axis1 | `axis1-reference-scorer.md` | sonnet | `evaluations/latest/axis1-reference.md` |
| axis2 | `axis2-logic-scorer.md` | opus | `axis2-logic.md` |
| axis3 | `axis3-defense-scorer.md` | opus | `axis3-defense.md` |
| axis4 | `axis4-originality-scorer.md` | opus | `axis4-originality.md` |
| axis5 | `axis5-concept-scorer.md` | sonnet | `axis5-concept.md` |
| axis6 | `axis6-critical-scorer.md` | opus | `axis6-critical.md` |

각 Agent 호출에 해당 `axis{N}-*-scorer.md` 전체 내용 + 선로드 context + 축이 요구하는 selective 입력만 전달.

**Axis-input map (Stage `flow`)**:
- axis1: `flow/flow.md` + `flow/claim-extraction-flow.md` + `papers/analyzed/*.md` (전체)
- axis2: `flow/flow.md`만
- axis3: `flow/flow.md` + `papers/analyzed/*.md` 중 `axis_tags`에 `"steelman"`
- axis4: `flow/flow.md` + `papers/analyzed/*.md` 중 `axis_tags`에 `"delta"`
- axis5: `flow/flow.md`만
- axis6: `flow/flow.md` + `critical-questions.md` + `critical-commitments.md` + `papers/analyzed/*.md` 중 `axis_tags`에 `"minority"`

**Axis-input map (Stage `output`)**:
- axis1: `output/*.md` + `output/claim-extraction-output.md` + `papers/analyzed/*.md`
- axis2: `output/*.md`만
- axis3: `output/*.md` + `papers/analyzed/*.md` 중 `"steelman"`
- axis4: `output/*.md` + `papers/analyzed/*.md` 중 `"delta"`
- axis5: `output/*.md`만
- axis6: `output/*.md` + `critical-questions.md` + `critical-commitments.md` + `papers/analyzed/*.md` 중 `"minority"`

**Axis-input map (Stage `final`)**:
- axis1: `final/complete-draft.md` + `final/claim-extraction-final.md` + `papers/analyzed/*.md`
- axis2: `final/complete-draft.md`만
- axis3: `final/complete-draft.md` + `papers/analyzed/*.md` 중 `"steelman"`
- axis4: `final/complete-draft.md` + `papers/analyzed/*.md` 중 `"delta"`
- axis5: `final/complete-draft.md`만
- axis6: `final/complete-draft.md` + `critical-questions.md` + `critical-commitments.md` + `papers/analyzed/*.md` 중 `"minority"`

**stale_axes에 없는 축**은 이전 archive의 동명 파일(`axis{N}-*.md`)을 그대로 `latest/`에 유지(복사). 재계산 없음.

### 단계 6: 병렬 완료 대기

모든 dispatch한 축 워커의 응답을 수신한 뒤에만 단계 7로 진행. 부분 완료 상태에서 aggregator 실행 금지.

### 단계 7: Aggregator — evaluation.md 생성

```bash
python3 scripts/evaluation_aggregator.py {PROJECT_NAME}
```

이것이 `axis{1..6}-*.md` 점수 섹션을 파싱하여 `evaluation.md`(요약 + delta 표 + 심사 판정)를 자동 생성.

### 단계 8: citation-checker 체이닝 (조건부)

stage가 `output/final`이고 axis1이 stale이었다면 `citation-checker`를 호출:
- output: chapters 무작위 30% 샘플
- final: 전량 + archive 대비 new-error diff

### 단계 9: critical-companion (stage 마일스톤)

Critical Mode이고 해당 stage가 마일스톤이면 `critical-companion`을 별도 호출해 `critical-questions.md` v{N+1} 생성. 이전 답변과 현재 원고의 정합성 점검 포함.

| stage | trigger |
|-------|---------|
| flow 첫 평가 | `initial` |
| 리서치 완료 후 | `post-research` |
| output 첫 평가 | `post-draft` |
| output 재평가 (수정 후) | `post-revision` |
| final 평가 직전 | `pre-final` |

### 단계 10: 캐시 갱신

평가가 완료된 축만 delta 캐시에 기록:

```bash
python3 scripts/evaluation_delta.py mark-done {PROJECT_NAME} axis2,axis3
```

### 단계 11: Sync 갱신

```bash
python3 scripts/sync_state.py update-evaluation {PROJECT_NAME}
```

### 단계 12: evaluation.md 종합 갱신

aggregator(`scripts/evaluation_aggregator.py`)가 단계 7에서 이미 `evaluation.md`를 생성. 이 단계에서는 다음 액션 섹션·미해결 R-NN 섹션·WRITE 권고 섹션을 채워 사용자가 한 파일만 보면 다음 무엇을 할지 알 수 있게 한다 (포맷: `skills/EVALUATION-FORMAT.md`).

work-plan.md 갱신·card_registry 호출 등은 모두 폐기. evaluation.md가 단일 진입 파일.

### 단계 13: 사용자 보고

```
🎯 평가 완료 (delta 모드, stale {N}/{total_axes})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🩺 종합 판정: [🔴 Reject / 🟠 Major Revision / 🟡 R&R / 🟢 Accept]
평가 단계: [flow / output / final]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| 축 | 이름 | 상태 | 변화 | 핵심 진단 |
|---|------|------|------|----------|
| 1 | 레퍼런스 충실도 | 🟠 보강 필요 | (이전 🔴) | <한 줄> |
| 2 | 논리 전개 완성도 | 🟡 적정 | (재평가) | <한 줄> |
| ... | | | | |

🚨 Critical Issues (이번 평가 가장 시급):
1. ...
2. ...

📂 축별 상세: axis1-reference.md ~ axis5-concept.md
📋 다음 액션: evaluation.md "🧭 다음 액션" 섹션
⏱ 소요: {N}분 (재계산 {N}축, 캐시 {M}축)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💾 저장 결과:
   ✓ {stage}/evaluations/latest/evaluation.md      (종합 요약 + 다음 액션 + 미해결 R-NN)
   ✓ {stage}/evaluations/latest/axis1-reference.md ~ axis6-critical.md
   ✓ {stage}/claim-extraction-{stage}.md           (stage 변경 시)
   📦 이전 평가 → {stage}/evaluations/{NNN}-{date}/ 증분 스냅샷 (manifest.json)

👉 다음 단계:
   1. evaluation.md 검토 (특히 "🧭 다음 액션" 섹션)
   2. 다음 액션 실행:
      - "리서치 진행해줘" → 미해결 R-NN로 Consensus 검색
      - "논문 처리해줘" → PDF 처리
      - "초안 작성해줘" → output stage 진입
      - "Chapter X 수정해줘" → output 수정
   3. 변경 후 같은 "{stage} 평가해줘" 재실행 → delta 모드로 빠르게 재진단
```

### 단계 14: 자동 권장 — flow-refiner · output-gap-finder · adversarial-reviewer

평가 결과가 특정 패턴이면 후속 agent 자동 권장 (자동 호출 X — 사용자에게 묻기). 활용 미흡 agent 보장 메커니즘.

#### a. flow-refiner 자동 권장 트리거

다음 조건 시 권장 메시지 자동 출력:
- axis1 (레퍼런스 충실도) 또는 axis5 (개념 정의) verdict가 🟠 Major Revision 이상
- axis2 (논리 전개) 결과에 "flow 구조 자체 재검토" 권고 포함
- axis_tags 분포에서 *flow의 §섹션이 paper와 잘 맞지 않음* 신호

권장 출력:
```
🔧 flow-refiner 호출 권장

평가 결과 axis{N} 진단으로 flow.md 자체 보강이 필요할 수 있습니다.
다음 명령으로 flow-refiner 호출 가능:
  "flow 업데이트해줘"

flow-refiner는 flow.md diff 제안만 (직접 수정 X) — 사용자가 채택 결정.

호출하시겠어요? (yes / 나중에)
```

#### b. output-gap-finder 자동 권장 트리거

다음 조건 시:
- axis4 (독창성) verdict 결과에 "gap 보강 필요" 또는 "기여 약함" 진단
- axis1·5 결과에 "분야 빈틈 추가 탐색 권장" 신호
- INDEX C section의 *axis 부족* 또는 *underexplored region* 표시 다수

권장 출력:
```
🔍 output-gap-finder 호출 권장

평가에서 분야 gap 추가 탐색이 필요한 것으로 진단됨.
다음 명령으로 output-gap-finder 호출 가능:
  "gap 분석해줘"

output-gap-finder는 output 단계의 분야 빈틈 탐색 → gap-analysis.md 산출 (research-gap 단계의 gap-analyzer/gap-paper-analyst/gap-synthesizer와 분리).

호출하시겠어요? (yes / 나중에)
```

#### c. adversarial-reviewer 자동 권장 트리거

다음 조건 시:
- axis3 (반박·강화) verdict 결과에 "steelman 부족" 진단
- axis6 (비판적 시각) Critical Mode 결과에 "학파 X 입장 반박 안 다뤄짐" 신호
- output stage에 chapter 작성 후 *학파별 반박 simul 미실행*

권장 출력:
```
🎭 adversarial-reviewer 호출 권장

평가에서 학파별 반박 시뮬이 부족한 것으로 진단됨.
다음 명령:
  "적대적 리뷰 해줘" 또는 "X 학파 입장에서 반박해줘"

adversarial-reviewer는 학파별 simulated reviewer로 단락 단위 반박 + 선제 차단 권고.

호출하시겠어요? (yes / 나중에)
```

#### d. 통합 — 자동 권장 메시지 형식

단계 13 사용자 보고 *마지막에 추가*:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 추천 후속 작업 (활용 미흡 agent 보장)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{조건 충족 agent별 권장 메시지 출력}
{없으면 "현재 권장 후속 없음" 표시}

응답: "all 호출" / "1,2번만" / "건너뛰기"
```

이 단계는 활용 미흡 agent (flow-refiner / output-gap-finder / adversarial-reviewer)가 *주기적으로 사용자 시야에 들어오게* 하는 보장 메커니즘.

### 단계 6: 반복 평가 규칙

- **각 Stage 완료 시 재평가 권장**:
  - 리서치 후 → `"flow 평가해줘"` (delta 모드로 변경된 axis1만 재계산)
  - 초안 작성 후 → `"output 평가해줘"` (전체 6축 첫 평가)
  - 수정 후 → `"output 평가해줘"` (delta — 변경 chapter 영향 축만)
  - 최종 머지 후 → `"final 평가해줘"` (6축 + holistic-reviewer)
- **이전 평가 대비 delta 추적**: 두 번째 이후 평가 시 `evaluation.md`에 이전 round 대비 카테고리 변화 표시
- **카테고리 기반 verdict**: 점수 평균 폐기. 카테고리 룰만 사용 (§5축 평가 기준 참조)

### 단계 7: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "평가 완료" "stage={flow|output|final}" "verdict={Reject|Major|R&R|Accept}" "categories=Crit:{N},Need:{M},Adeq:{K},Strong:{S},NA:{X}" "ref=ref:eval-{NNN}" "agents=evaluation-orchestrator,axis1-5{,citation-checker}" "ambition={ambition}" "commits={fulfilled}/{total}"
```

(점수 기반 `result={score}/500` 폐기 — verdict + 카테고리 카운트로 대체)

---

## 논문 처리 (2-pass + Tier)

사용자가 `"논문 처리해줘"`를 말하면 main agent가 **두 candidates 폴더를 병렬 스캔**:
- `papers/candidates/research-gap/*.pdf` → `gap-paper-analyst` (갭 frame, 결과 → `papers/analyzed/research-gap/[R][D].*.md`)
- `papers/candidates/flow/*.pdf` → `paper-analyst` (anchor/normal frame, 결과 → `papers/analyzed/flow/[A]|[N].*.md`)

폴더 = SSOT. PDF가 어느 candidates 서브폴더에 있느냐로 처리 frame이 결정.

**명령 플래그**:
- `"논문 처리해줘"` → 두 폴더 모두 자동 처리
- `"논문 처리해줘 --batch=N"` → 배치 크기 오버라이드
- (특정 단계만) `"flow 논문 처리해줘"` / `"research-gap 논문 처리해줘"` → 한쪽만 처리

flow 단계 처리는 매핑 기반 자동 분류 (anchor/non-anchor 이진):
- `papers/search-results/flow.md`의 🎯 최우선 OR 🔴 Steelman → `[A].{name}.md` (anchor)
- 그 외 매칭 → `[N].{name}.md` (non-anchor)
- 매칭 없음 → `[?].{name}.md` (paper-analyst가 MANUAL curation)

research-gap 단계 처리는 단순:
- 모든 PDF → `[R].{name}.md` placeholder 생성 → gap-paper-analyst 분석 → `[R][D].{name}.md`로 rename
- gap frame 분석: 대상 연령·통제 변인·종속 변수·갭 시그널 (skills/agents/gap-paper-analyst.md 참조)

### 단계 1: 두 candidates 폴더 스캔

```bash
ls projects/{PROJECT_NAME}/papers/candidates/research-gap/*.pdf 2>/dev/null
ls projects/{PROJECT_NAME}/papers/candidates/flow/*.pdf 2>/dev/null
```

양쪽 모두 0이면 "candidates 비어 있습니다" 메시지 후 종료. 한쪽만 있으면 그쪽만 처리. 양쪽 다 있으면 사용자에게 1회 보고 후 양쪽 진행.

### 단계 2: 파일명 정규화 + 메타 추출

```bash
python3 scripts/normalize_filename.py {PROJECT_NAME}
```

### 단계 3: 🤖 paper-analyst 호출

1. `skills/agents/paper-analyst.md` 파일을 읽는다
2. Agent 도구로 실행 (model: opus, 가볍게 오케스트레이션만):
   - 전달: candidates 파일 목록 + flow 요약 (flow/flow.md의 thesis + 섹션 제목 + 핵심 구성개념 리스트 300-500 단어) + 플래그
   - 수행: 단계 3-7 (Pass 1 triage → tier 분배 → Pass 2 dispatch → sync)

### 단계 3.1: Pass 1 — triage 병렬 (haiku)

orchestrator가 관리. `paper-analyst`를 `Mode A-triage`로 각 PDF에 대해 병렬 호출 (model=haiku, 배치 20-25편). 각 결과는 `papers/analyzed/{파일명}-triage.json`으로 저장.

### 단계 3.2: Tier 분배 + 사용자 보고

```bash
```

Tier 분포를 사용자에게 먼저 보고. 사용자 개입 없이 진행 (단 `--priority` 등이 지정되었으면 그에 맞춰 재분배).

### 단계 3.3: Pass 2 — Tier별 병렬 dispatch

| Tier | 모델 | 배치 | Mode |
|------|------|------|------|
| 1 | opus | 5 | A-tier1 (full + Critical Reading) |
| 2 | sonnet | 10 | A-tier2 (full, Critical 제외) |
| 3 | sonnet | 20 | A-tier3 (간소판) |

Anchor·non-anchor 병렬 dispatch. 각 워커는 `paper-analyst.md` + flow.md + analyzed/[A|N|?].{name}.md (frontmatter prior) + markdown/{name}.md 를 prompt로 받음.

결과: `papers/analyzed/{파일명}-analysis.md`

### 단계 4: sync-state + PDF 이동

각 분석 완료 파일마다:
```bash
python3 scripts/sync_state.py update-paper {PROJECT_NAME} {파일명}.pdf
```

전체 완료 후 PDF 이동:
```bash
mv projects/{PROJECT_NAME}/papers/candidates/{파일명}.pdf projects/{PROJECT_NAME}/papers/collected/
```

### 단계 5: 결과 보고

처리된 모든 논문에 대해 다음과 같이 보고하세요:

```
✅ 논문 처리 완료: {N}개

📄 Smith_2023_Attention.pdf
   제목: Attention is All You Need
   저자: Vaswani et al.
   페이지: 15
   → papers/collected/로 이동 완료

   🤖 paper-analyst 분석:
   ├── 3줄 요약: Transformer 아키텍처를 제안...
   ├── 관련성: ⭐⭐⭐⭐⭐ (5/5)
   ├── 활용: Section 1 (Introduction), Section 2 (Background)
   └── 분석 파일: papers/analyzed/Smith_2023_Attention-analysis.md

📄 Brown_2020_GPT3.pdf
   [같은 형식]

💾 .paper-metadata.json 업데이트 완료
📊 현재 보유 논문: {TOTAL}개 | 분석 완료: {ANALYZED}개
```

### 단계 6: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "논문 처리" "stage=stage1" "target={N} PDFs" "result=processed" "agents=paper-analyst"
```

---

## Consensus 검색 (작업 시작) — 폴더 기반 자동 실행

사용자가 `"리서치 진행해줘"`, `"논문 검색해줘"` 등을 말하면 main agent가 **두 plan 폴더를 병렬 스캔**:
- `research-gap/research-plan.md`의 H-NN (gap-analyzer 산출, anchor 검색)
- `flow/claim-extraction-flow.md`의 R-NN (claim-extractor 산출, thesis-supportive 검색)

### 단계 1: 폴더 스캔 + 미해결 항목 수집

1. `research-gap/research-plan.md` 존재 시 → H-NN 중 `papers/search-results/research-gap.md`에 아직 없는 항목 수집
2. `flow/claim-extraction-flow.md` 존재 시 → R-NN 중 `papers/search-results/flow.md`에 아직 없는 항목 수집 + UNMATCHED-INTERNAL (보유 PDF 재스캔 대상) 수집
3. 양쪽 다 비어 있으면 "검색 대상 없음. 먼저 `'리서치 갭 분석해줘'` 또는 `'flow 평가해줘'` 실행하세요" 안내
4. 양쪽 다 있으면 사용자에게 1회 확인: "research-gap H-{N}건, flow R-{M}건. 모두 진행 / 한쪽만 / 취소"
5. 사용자 선택대로 진행. 결과는 `papers/search-results/research-gap.md` / `papers/search-results/flow.md`에 각각 저장.

### 단계 2a: UNMATCHED-INTERNAL 먼저 처리 (보유 PDF 재스캔, flow 단계만)

flow 단계에 한해, claim-extractor가 표시한 UNMATCHED-INTERNAL R-NN 각각:

1. 해당 논문의 `papers/analyzed/flow/[A]|[N].{name}.md` 읽기 (v1 존재 확인)
2. `skills/agents/paper-analyst.md` 읽기
3. Agent 도구로 paper-analyst를 **Mode B**로 호출:
   - 전달: PDF 경로 + 현재 flow.md + 기존 analyzed/*.md + 재분석 각도 지시
   - 수행: PDF 재스캔 → analyzed/*.md에 `## [v2 — {date}] 재분석: {각도}` append
4. `python3 scripts/sync_state.py update-paper {PROJECT} {파일명}` 실행
5. `claim-extraction-flow.md`에서 해당 R-NN을 INTERNAL→MATCHED 후보로 전환 (사용자 확정 시 MATCHED). work-plan 갱신 단계 없음.

### 단계 2b: Context pack 사전 빌드 (main 세션, ~30s)

**의도**: workers가 flow.md·claim-extraction·axis1-reference를 각자 읽지 않도록, main이 한 번만 요약 파일을 만들어 공유.

```bash
mkdir -p projects/{P}/papers/.research-raw projects/{P}/papers/.translations projects/{P}/papers/.curation
```

main 세션이 다음 3개 파일을 읽고 `projects/{P}/papers/.context-pack.md` 한 파일로 요약 작성:
- `flow/flow.md` — thesis + key argument skeleton (3-5줄)
- `flow/claim-extraction-flow.md` — R-NN → S-NNN 매핑 + 카테고리 요약표
- `evaluations/latest/evaluation.md` + `axis1-reference.md` — 점수 가장 낮은 축·하위 기준·복원 우선순위

이 파일은 세션 종료 시까지 읽기 전용. workers는 이 하나만 읽으면 됨.

### 단계 2c: Stage A — 검색 + B+C 파이프라인 dispatch (main 세션, 각 RESEARCH 1~3분)

**RESEARCH = 실행 단위**: claim-extractor가 이미 R(Research Target)들을 병합해 RESEARCH(execution unit)로 제안. 각 RESEARCH 카드 = 1 Consensus 쿼리 = 1 raw JSON = 1 curation 블록.

**파이프라인 원칙 (중요 — 2026-04-24 2차 실행 사례)**: Stage A가 모두 끝나기를 기다리지 않고, 각 카드의 raw JSON이 저장되는 **즉시** 해당 카드의 B+C combo worker를 background dispatch한다. Stage C가 카드당 3-5분이므로, Stage A 나머지를 도는 wall-clock 시간이 Stage C 대기를 흡수한다. 전체 wall clock ≈ (Stage A total) + 1×(Stage C typical) 수준으로 단축.

**Rate limit 정책 (adaptive)**: 초기 **1-serial**. 연속 3회 성공 시 2-parallel 승격. 429 시 30s 대기 + 1-serial로 강등. 처음부터 3-parallel 시도 금지.

**B+C worker concurrency cap**: 최대 6 병렬 (sub-agent 조정 부하 방지). cap 초과 직전이면 main은 `TaskList`로 completed worker가 생길 때까지 다음 dispatch 보류.

각 미완료 RESEARCH 카드마다 main 세션이 직접:

1. `mcp__consensus__search` 호출 (RESEARCH 카드의 `query` 필드 사용)
2. 응답 전체를 `papers/.research-raw/R-NN.json`에 즉시 저장 — **SSOT**. 다음 스테이지는 여기만 읽음:
   ```json
   {"card_id": "R-01", "covers": ["R-01", "R-04"], "query": "...", "executed_at": "...",
    "papers": [{"url": "...", "title": "...", "authors": "...", "year": 2025,
                "journal": "...", "citations": 2, "abstract": "<full English text>"}]}
   ```
3. 429 시 sleep 30 후 단일 직렬로 강등 재시도
4. **즉시 research-processor worker dispatch (`run_in_background=true`)** — R-NN의 B+C 수행. 반환 기다리지 않고 다음 카드의 Stage A로 진행.

**중단 복구**: 이미 `.research-raw/R-NN.json` 존재하면 재검색 스킵 (단 `.curation/R-NN.md` 없으면 B+C worker는 재디스패치).

### 단계 2d: Stage B+C — research-processor combo worker (background, 각 3-5분)

각 카드마다 **research-processor(sonnet) worker 1개** background dispatch. 단일 컨텍스트에서 번역(B) → curation(C) 순차 수행.

> **왜 단일 worker인가**: B/C를 별개 worker로 두면 main이 B 완료 감지 후 C dispatch하는 coord 로직이 필요. 합치면 (1) coord 불필요 (2) raw JSON/translations를 한 번만 읽음 (3) 동일 sonnet 컨텍스트가 번역 ↔ 판단 사이 용어 일관성 유지. 번역도 sonnet이면 cost 약간 상승하나 wall clock 단축 이득이 크다.

Worker 한 개의 단일 책임 (내부 2-phase):
1. `papers/.context-pack.md` 읽기 (단계 2b 산출, 공용)
2. `papers/.research-raw/R-NN.json` 로드
3. **Phase B (번역)** — `skills/agents/abstract-translator.md` 규칙 따름:
   - 각 abstract 한글 전문 번역 (요약 금지, `> `-quoted 블록)
   - `papers/.translations/R-NN.md`에 원자 저장 (`.tmp.{pid}` → `mv`)
4. **Phase C (curation)**:
   - 논문 필터링 (off-topic 제거)
   - 6 카테고리 분류 (🎯 최우선 / 🟢 보조 / 🔴 Steelman / 🌏 발달·횡문화 / ⚙️ 방법론 비판 / 🔗 Cross-RESEARCH)
   - 논문마다 3줄 주석 (claim / 본 에세이 활용 섹션·S-NNN / 인용 강도 suggest/indicate/demonstrate)
   - 📌 액션 아이템 `[ ]` 3+개
   - `papers/.curation/R-NN.md`에 원자 저장
5. "OK: R-NN (translations={K}, curation={M} papers)" 한 줄 반환

**프롬프트 길이 제한**: worker 프롬프트는 800 토큰 이하 (`skills/agents/research-processor.md` 경로 참조만, 스펙 copy-paste 금지).

**중단 복구**:
- `.translations/R-NN.md` 이미 존재 & `.curation/R-NN.md` 없음 → curation만 재수행
- 양쪽 모두 존재 → 스킵
- 거부/실패된 worker만 재디스패치

### 단계 2e: Barrier — 모든 B+C worker 완료 대기 (main)

Stage A를 완료한 main은 `TaskList`로 남은 research-processor worker들이 모두 completed 될 때까지 대기. 30-60초 간격 polling 또는 notification 활용. 이 barrier를 건너뛰고 Stage D로 진입하면 불완전한 `.curation/*.md` 집합으로 assembly → post-check 실패.

### 단계 2f: Stage D — Assembly (2-step: mechanical concat + thin summarizer, ~1.5-2.5분)

**원칙**: 본문(15 RESEARCH 블록)은 mechanical concat + Python URL dedup만 사용 — LLM이 2000줄을 재생성하면 미묘한 누락·왜곡이 거의 확실히 생기므로 금지. LLM은 판단이 필요한 누적 요약 4섹션에만 쓴다.

**Step 1 — mechanical assembly (main 세션, ~1초)**:
```bash
python3 scripts/assemble_consensus_results.py {PROJECT}
```
이 스크립트가:
- `.curation/R-NN.md`를 RESEARCH 번호 순으로 concat
- Cross-RESEARCH URL dedup 자동 처리 (첫 등장 full + 재등장은 `⚠️ 중복 — RESEARCH-XXX #N 참조` one-liner)
- `# R-NN Curation — topic` → `## [R-NN] topic` 헤딩 강등 (post-check 요건)
- 마스터 헤더(생성 시각·유니크 URL 수·dedup 수) prepend
- `papers/search-results/{stage}.md` 원자 저장 + JSON stats 출력

**Step 2 — 누적 요약 4섹션 append (thin sonnet subagent, ~1-2분)**:
생성된 `search-results/{stage}.md`를 읽고 끝에 아래 4섹션만 **append** (기존 RESEARCH 블록 수정 금지):
- 🏆 최중요 발견 Top-10 (각 카드의 🎯에서 thesis 영향도 기준)
- 📥 PDF 다운로드 우선순위 10편 (각 카드의 📌 액션 아이템 통합)
- 🔗 Cross-RESEARCH 교차 논문 표 (Step 1에서 생성된 `⚠️ 중복` 라인을 grep해 표로 렌더링)
- 👉 다음 단계 권장

**Step 3 — 상태 파일 업데이트 (main 직접 Edit)**:
- `papers/search-results/{stage}.md`: 새로 검색된 R-NN/H-NN 섹션 추가
- `evaluation.md`의 다음 액션 섹션 갱신 — 미해결 R-NN 줄어든 만큼 반영
- `activity.log`: 검색 완료 엔트리 append

⚠️ **claim-extraction-flow.md의 UNMATCHED는 RESEARCH 완료로 자동 전환되지 않는다**. RESEARCH는 논문 *후보* 확보 단계이고, MATCHED는 사용자가 PDF를 읽고 특정 문장에 특정 논문을 인용하기로 확정한 상태. 이 둘을 합치면 추적 불가능. MATCHED 전환은 Stage 2(초안 작성) 이후 writing-architect의 섹션별 인용 매핑에서 이루어진다. RESEARCH Stage 1 완료 시 claim-extraction은 그대로 둘 것.

### 단계 2g: Post-condition 검증 (⚠️ 보고 전 gate)

```bash
python3 scripts/research_postcheck.py {PROJECT}
```

이 스크립트가 다음을 모두 확인 (하나라도 실패 시 "완료" 보고 차단):

1. 처리 대상 R-NN/H-NN 수 == `.research-raw/*.json` 수 == `.curation/*.md` 수 (1:1:1)
2. 각 `.curation/*.md`에 6 카테고리 헤더 모두 존재 + 액션 아이템 3+개
3. `search-results/{stage}.md`에 `번역 대기` 0건
4. `search-results/{stage}.md`의 RESEARCH 블록 수 == `.curation/*.md` 수

**검증 실패 시 재진입**: 누락 카드만 개별 단계로 재개 (Stage A 필요하면 1개만, Stage B or C는 해당 worker만).

### 단계 2h: Curation 출력 포맷 스펙

**단계 2b에서 search-results/{stage}.md에 쓰는 각 RESEARCH 블록은 다음 구조를 반드시 따른다.** 단순 번호 리스트 금지. curation(판단·분류·주석) 없이는 사용자가 225편 raw 리스트를 직접 훑어야 하는 상황이 재발한다 (2026-04-24 1차 실행 사례).

**Sub-agent 입력**: RESEARCH 실행 전 다음 파일을 **반드시 읽어** "synthesize context"를 확보:
- `flow/flow.md` (thesis + argument chain)
- `flow/claim-extraction-flow.md` (문장별 NEEDS_CITATION 분류)
- `evaluations/latest/evaluation.md` + `axis1-*.md` (낮은 축 복원 우선순위)
- `critical-questions.md` + `critical-commitments.md` (Critical Mode일 때)

**각 RESEARCH 블록 포맷**:

```markdown
## [R-NN] (covers R-NN, R-MM) {topic from search[].topic}

**검색 쿼리**: `{query}`
**실행일**: YYYY-MM-DD
**확보 논문**: M편 (신규 X / 중복 Y)

### 🎯 최우선 인용 (MUST CITE)
 thesis backbone 또는 세미널 원전. 인용 없으면 축 1·3·4 심각 감점.

1. **저자 (연도)** — [제목](URL). *저널*. 인용 N회.
   {1-3문장 주석: flow.md §어느 Section·S어느 문장을 뒷받침/공격하는지, 어떤 역할(backbone / Steelman target / 정의 차용)인지. 인용 필수성 근거.}
   > {영어 abstract 원문 전체의 한글 번역, abstract-translator 결과}

2. ...

### 🟢 보조 증거 (Supporting)
 최우선을 뒷받침하는 실증·리뷰·추가 근거. triangulation용.

{동일 포맷}

### 🔴 반론·Steelman (Counter / Steelman)
 저자 thesis에 도전하는 경쟁 이론 또는 강력 반론. 축 3 방어 논리 보강용.

{동일 포맷}

### 🌏 발달·횡문화 (Developmental / Cross-cultural)
 연령·문화·SES 차이를 다루는 실증. 축 1-Balance + 4-Implications 보강.

{동일 포맷}

### ⚙️ 방법론 비판 (Methodological critique)
 측정·설계·재현성 이슈. 축 3 Falsifiability + Limitations 방어.

{동일 포맷}

### 🔗 Cross-RESEARCH 재등장
 이미 다른 카드의 full 섹션에 수록된 논문. 현 RESEARCH 맥락에서의 의의만 1-2줄. 전체 번역·주석은 원 위치 참조.

1. **저자 (연도)** — [제목](URL). ⚠️ **중복** — RESEARCH-XXX §카테고리 #M 참조. 현 맥락 의의: {1-2줄}.

### 📌 액션 아이템
 사용자가 바로 실행할 구체적 다음 단계. `[ ]` 체크박스 형태.

- [ ] **저자(연도)** PDF 다운로드 → `papers/candidates/`
- [ ] flow.md §Section X 문단 Y의 `(레퍼런스)` 자리 = {논문1} + {논문2} 공동 인용
- [ ] {저자 주장 S-NNN} ↔ {논문} 교차 확인 (paper-analyst 조사)

---
```

**모든 RESEARCH 블록 완료 후, 파일 끝에 누적 요약 섹션**:

```markdown
---

## 🏆 가장 중요한 발견 (thesis 영향도 순)

1. **저자(연도)** — 왜 중요한지 1문장 (어느 축 복원, 어느 section backbone 등)
2. ...

## 📥 PDF 다운로드 우선순위

Stage 1 → 2 전환을 위해 **최우선 10편** (인용수·역할 가중):
1. **저자(연도)** — MUST (thesis 출발점)
2. **저자(연도)** — MUST (Steelman 핵심)
...

## 🔗 Cross-RESEARCH 교차 논문 (복수 역할)

| 논문 | 교차 RESEARCH | 교차 의의 |
|------|----------|----------|
| 저자(연도) | RESEARCH-010 + RESEARCH-034 | {역할1} ↔ {역할2} |

## 👉 다음 단계

1. PDF 우선순위 10편 수동 다운로드 → `papers/candidates/`
2. `"새 논문 처리해줘"` → paper-analyst 일괄 분석
3. `"flow 업데이트해줘"` → `(레퍼런스)` 자리 실제 인용 교체
4. `"flow 평가해줘"` 재실행 → 축 1 점수 복원 확인
```

**카테고리 배정 원칙**:
- 논문 1편은 원칙적으로 **한 카테고리만**. 여러 역할 가능하면 가장 주된 역할 선택.
- 명백히 2+ 역할이면 "최우선 인용"으로 올리고 주석에 추가 역할 명시.
- 카테고리 간 이동 기준 모호하면 주석에서 명시적으로 판단 근거 밝힘.

**논문 수 가이드**: 카드당 ~15-25편 확보 (Consensus max 20). 카테고리별 편차 허용 — 강제 분배 금지. 중복은 전체 수 제한 없이 one-liner로 기재.

**Curation 품질 체크리스트 (sub-agent 자기 검증)**:
- [ ] 각 카테고리 헤더 존재 (해당 카테고리 논문 0편이면 `_(해당 없음)_`)
- [ ] 모든 신규 논문에 주석 1-3문장 (단순 "중요함" 같은 공허 문구 금지 — flow §Section / S-NNN 참조 포함)
- [ ] 액션 아이템 `[ ]` 체크박스 최소 3개 (PDF 다운로드 + flow 배치 + 교차 확인 등)
- [ ] 전체 파일 끝에 누적 요약 4 섹션 (최중요 발견 · PDF 우선순위 · Cross-RESEARCH · 다음 단계)

### 단계 3: 결과 보고

각 RESEARCH 결과는 `papers/search-results/{stage}.md`에 `[R-NN]` 태그로 누적 저장된다 (단계 2b에서 이미 수행). 각 논문은 클릭 가능한 마크다운 링크 (`[제목](URL)`) 형식으로 포함.

화면 요약 예시:
```
🔍 RESEARCH 실행 완료

📊 요약
   🔄 RESEARCH(reanalyze): {N}개 완료 ({M}편 PDF 재분석, v2 append)
   🔍 RESEARCH: {K}개 완료 ({L}편 신규 후보 확보)
   ⚠️  재검색 권장: {R}개 (기대 프로필 미달)

📄 papers/search-results/{stage}.md에 {L}편 추가
🔄 flow/claim-extraction-flow.md 또는 output/claim-extraction-output.md 매칭 갱신: {T}건

👉 다음 단계:
   1. search-results/{stage}.md 링크에서 필요한 논문 PDF 다운로드
   2. papers/candidates/에 저장 → "새 논문 처리해줘"
```

### 단계 4: 다음 단계 권장 (현실적 분기)

RESEARCH 전량 완료 후, 사용자에게 다음 두 옵션을 제시:

```
📚 Stage 1 리서치 완료

축 1 점수는 새 논문 확보로 상승할 것으로 기대되지만, 축 2·3·4·5는 flow.md 텍스트가
그대로이므로 전체 5축을 재평가해도 변화는 미미합니다.

다음 중 선택:

  [A] "레퍼런스 점검해줘"  → 축 1만 빠르게 재평가 (권장, 가벼움)
  [B] "flow 업데이트해줘"  → 새 논문 반영하여 flow.md 보강 제안
                            (이 후 "flow 평가해줘" 시 축 3·4도 유의미하게 움직임)
  [C] "초안 작성해줘"      → Stage 2로 바로 진입 (flow가 이미 충분하다면)
```

### 단계 6: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "RESEARCH 실행" "stage=stage1" "target=search-results/{stage}.md" "result={N_search} RESEARCH(search) + {N_reanalyze} RESEARCH(reanalyze) done"
```

---

## 🔍 레퍼런스 점검 (축 1 경량 재평가 — 신 아키텍처 alias)

사용자가 "레퍼런스 점검해줘", "축 1 재평가", "reference check" 등을 말하면 **`평가해줘 axis1`과 동등**:

1. `claim-extractor` 선행 호출 (prose flow인 경우)
2. `axis1-reference-scorer`만 dispatch (병렬 무관, 단일 호출)
3. `evaluation_aggregator.py` 실행 → `evaluation.md`의 축 1 블록만 갱신 (축 2-6은 이전 archive 값 보존)
4. `evaluation_delta.py mark-done {PROJECT_NAME} axis1` 실행

**Archive 스냅샷 생략**: 단일 축 재평가이므로 `sync_state.py snapshot-evaluation` 호출하지 않음 (전체 평가와 차별점).

**PDF 샘플링**: axis1-reference-scorer 에이전트 내부 절차 — MATCHED 중 2-3편 무작위로 `papers/collected/*.pdf` 원문 대조. 불일치 시 `axis1-reference.md`에 `⚠️ 재검증 필요` 플래그.

### 단계 3: 보고

```
🔍 레퍼런스 점검 완료 (축 1 전용)

축 1 레퍼런스 충실도: 52 → 84 (+32 🟢)
  ├─ 1-1 Coverage: 40 → 92 (+52)
  ├─ 1-2 Accuracy: 65 → 88 (+23)
  ├─ 1-3 Authority: 60 → 82 (+22)
  └─ 1-4 Balance: 43 → 74 (+31)

⚠️ 잔존 이슈:
  - [RESEARCH-007] S055에 대한 매칭 논문이 기대 프로필 미달 → 재검색 권장
  - [RESEARCH-012] S089의 MATCHED 논문 3편 중 1편이 원문 확인 결과 over-claim

👉 다음 단계:
   - 잔존 이슈 해소 후 "flow 업데이트해줘"
   - 또는 "초안 작성해줘"로 Stage 2 진입
   - 축 2-5 전체 재평가는 Stage 2 초안 완료 후 권장
```

### 단계 4: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "레퍼런스 점검 완료" "stage=post-research" "axis1_status={emoji} {label}" "axis1_prev={prev_emoji} {prev_label}" "ref=ref:eval-{NNN}"
```

---

## 📝 flow 업데이트 (새 논문 반영 보강)

사용자가 "flow 업데이트해줘", "flow 보강", "새 논문 반영해서 flow 고쳐줘" 등을 말하면:

### 단계 1: 🤖 flow-refiner 에이전트 호출

1. `skills/agents/flow-refiner.md` 파일을 읽는다
2. Agent 도구로 flow-refiner를 호출:
   - 전달: flow/flow.md + `.sync-state.json` + 신규 analyzed/*.md + evaluations/latest/evaluation.md + flow/claim-extraction-flow.md
   - 수행: Phase 1 새 논문 집계 → Phase 2-4 축 3·4·기타 보강 후보 탐색 → Phase 5 diff 제안 작성
3. 에이전트가 제안 리스트를 화면에 출력

### 단계 2: 사용자 확인

```
📝 flow.md 업데이트 제안

📌 축 3 보강 제안 (Steelman):
  현재: "latent variable 접근으로 순수 EF를 추출할 수 있다는 주장도 있다."
  제안: "Friedman & Miyake (2017)는 latent variable로 순수 EF 추출 가능성을
       제시했으나, 최근 Löffler et al. (2024)는 drift-diffusion 분석에서
       공통 요인이 정보 흡수 속도에 완전히 환원됨을 보였다."
  변화: 반론의 steelman 강도 ↑ + 재반박 근거 추가

📌 축 4 보강 제안 (Novelty Delta):
  [...]

👉 이 제안들을 flow.md에 반영할까요? [전체 수락 / 개별 선택 / 거부]
```

### 단계 3: 반영 후 권장 사항

사용자가 수락하면 flow-refiner가 flow.md를 갱신하고 `sync_state.py update-flow` 실행. 이후 **전체 5축 재평가 권장** (이제는 의미 있는 변화 예상).

### 단계 4: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "flow 업데이트" "stage=post-research" "target=flow.md" "result={N} 제안 중 {M} 반영" "agents=flow-refiner"
```

---

## 초안 작성 (v3 — Generative + Reactive 하이브리드)

사용자가 "초안 작성해줘", "draft 생성", "글 써줘" 등을 말하면:

### 단계 0: Commitment 추출 Prehook (always-on)

`output/critical/critical-questions.md` 또는 `flow/critical/critical-questions.md`가 존재하고 답변 작성됐으면:

1. `critical-questions.md`의 mtime > `critical-commitments.md` mtime 확인
2. 최신이면 → `"답변 반영해줘"` 자동 실행 (critical-companion Phase 6) → `critical-commitments.md` 갱신
3. 단계 1로 진행

### 단계 1: 준비 확인

1. **flow/flow.md 읽기** (thesis 본문)
2. **.paper-metadata.json 읽기** (intellectual_ambition 등)
3. **papers/analyzed/INDEX.md 읽기** (drafting 시작점 — §매핑·학파 좌표)
4. **papers/analyzed/[A][D].*.md / [N][D].*.md 읽기** (paper별 index_fields)
5. **critical-commitments.md 읽기** (있으면)
6. **generative phase 산출물 읽기** (있으면, `output/generative/` 안): thesis-development-notes.md / cross-paper-insights.md / steelman-dialectic.md / field-positioning.md

**On-demand만 read**:
- `papers/markdown/{canonical}.md` (paper 본문 캐시) — analyzed 인용 부족 시 sub-agent가 읽음
- `papers/collected/*.pdf` — markdown 부족 시 *최후* 검증 (거의 안 씀)

### 단계 1b: 기존 chapters 자동 스냅샷

`output/` 비어있지 않으면:
```bash
python3 scripts/sync_state.py snapshot-output {PROJECT_NAME} pre-redraft
```
결과: `output/archive/{NNN}-{date}-pre-redraft/`에 백업.

### 단계 2: 🌱 Generative Phase (internal 자동 종합)

작성 *전*에 thesis 자체를 발전시키는 단계. **디폴트는 "all 4 agents 병렬 실행 + main agent 자동 종합"**. 사용자에게 4 산출 검토 부담 없음.

#### 단계 2-A: 4 agents 병렬 launch (internal, 사용자에게 안 보임)

자동:
- thesis-developer → `output/generative/thesis-development-notes.md`
- output-cross-paper-insights → `output/generative/cross-paper-insights.md`
- steelman-dialectic → `output/generative/steelman-dialectic.md`
- field-positioning-oracle → `output/generative/field-positioning.md`

(각 산출은 *internal 작업물*. 사용자에게 직접 노출 X. 디버깅·audit 시에만 참조.)

#### 단계 2-B: main agent 자동 종합

4 산출 cross-cut 후:

1. **강한 수렴 신호** (3-4 agent 일치) → `critical-commitments.md`에 자동 commitment 추가:
   ```
   [C-AUTO-NNN] {수렴 항목} (autoextracted from generative phase)
     - 출처: {agent list 일치}
     - 기준: 4 agents 중 N개 합의
     - 처리: writing-architect Phase 0/2가 본문에 자동 반영
   ```

2. **권장 positioning option** (field-positioning Phase 4) → writing-architect Phase 0 input

3. **약한 또는 상충 신호** → `output/critical/critical-questions.md` 생성 자료로 critical-companion에 전달:
   - 4 agents 의견 갈림 또는
   - 사용자 의식적 결정 필요한 trade-off
   - 단순 채택·거부 X — 사용자가 답변 작성

4. `critical-commitments.md` 갱신 + writing-architect Phase 0 input pack 준비

#### 단계 2-C: 사용자에게 보여주는 화면 (간결)

```
🌱 Generative Phase 완료 (4 agents 병렬 + 자동 종합, ~15-30분 소요)

📊 자동 종합 결과:
  ✓ critical-commitments.md에 {N}개 commitment 자동 추가 (강한 수렴 신호)
  ✓ output/00-positioning.md 결정 — Option #{X}: {제목}
  ✓ output/critical/critical-questions.md 생성 — 사용자 결정 필요 {N}개 핵심 질문

📁 internal 작업물 (검토 옵션, 보통 안 봐도 됨):
  output/generative/ 4 파일

→ 다음: writing-architect Phase 0/1로 자동 진행. 
   사용자는 critical-questions.md 답변만 (선택, 작성 후 또는 작성 중 답변).
```

**Skip 요청 시** — 명시 요청 (`"generative phase 건너뛰고 작성"`)만:

```
⚠️ Generative phase skip — elite 도달 어려움 (유능한 박사 과정생 수준)
계속하려면 "yes skip" 응답.
```

핵심: **사용자 부담 ↓** — 4 파일 검토 X, 채택 표기 X. 자동 종합 + critical 질문만.

### 단계 3: ✍️ writing-architect Phase 0 — Field Positioning 통합

`field-positioning.md` (있으면) Phase 4 Recommendation 우선 참조. 없으면 INDEX.md + flow.md로 추정.

산출: positioning statement (Introduction 첫 문단 또는 §1에 *명시적*으로 등장).

### 단계 4: ✍️ writing-architect Phase 1 — 논증 구조 설계

각 섹션의 논증 구조 설계. flow.md §구조 그대로 chapter화 (예: §EF의 보편성과 특수성 → 01-ef-universality.md). IMRaD 강제 X — flow.md가 결정.

설계 결과 사용자에게 보여주고 **승인 대기**.

### 단계 5: 🔍 adversarial-reviewer Phase 1.5 — Outline Review

writing-architect Phase 1 outline에 adversarial critique:
- 학파 위치 잡기 명확성
- Layered argumentation depth
- Counterargument anticipation 충분성
- Novel synthesis 잠재력

산출: `output/outline-critique.md`. 심각도 high → outline 재설계 (단계 4 복귀).

**사용자 명시 skip 가능**: `"reviewer 건너뛰고 작성해줘"`.

### 단계 6: ✍️ writing-architect Phase 2 + 🔍 adversarial-reviewer Phase 2.5 (chapter별 loop)

각 chapter:
1. **writing-architect Phase 2** — outline에 따라 chapter 작성. self-critique loop 1-2회 (Topic Sentence·Evidence→Analysis·Layered claim·Counterargument depth·Quote framing·Scholarly voice·Novel synthesis 점검)
2. **chapter 저장** — `output/0N-{section-name}.md`
3. **adversarial-reviewer Phase 2.5** — chapter별 critique 자동 호출. Part A (학파 반박) + Part B (Elite 패턴 위반)
4. **output-editor 자동 호출** — Phase 2.5 critique 심각도 high·medium 자동 적용 (chapter 부분 재작성)
5. 다음 chapter로 진행

### 단계 7: 🎭 peer-reviewer Phase 3 — Full Draft Simulated Review

전체 draft 완성 후 simulated journal reviewer (페르소나):
- 기본: senior reviewer (분야 표준)
- ambition ≥ critical: Iconoclast 페르소나 자동 추가

산출: `output/peer-review-simulation.md` + 권장 수정사항 list.

큰 재구성 필요 → 사용자 보고 + Phase 1 복귀 권장.
경미한 수정 → output-editor 자동 적용.

### 단계 8: 파일 저장 + DOCX

```bash
projects/{PROJECT_NAME}/output/00-positioning.md           # Phase 0 산출 (선택)
projects/{PROJECT_NAME}/output/0N-{section-name}.md        # 각 §
projects/{PROJECT_NAME}/output/generative/{4 agents}.md    # Generative phase (Stage 7-C)
projects/{PROJECT_NAME}/output/outline-critique.md         # Phase 1.5
projects/{PROJECT_NAME}/output/chapter-critique-0N.md      # Phase 2.5 (chapter별)
projects/{PROJECT_NAME}/output/peer-review-simulation.md   # Phase 3
projects/{PROJECT_NAME}/final/complete-draft.md            # 통합본
projects/{PROJECT_NAME}/final/complete-draft.docx          # Word (docx skill)
```

### 단계 9: 자동 체이닝 (sync + INDEX만)

작성 직후 자동 (작성 자체 마무리만):
1. `python3 scripts/sync_state.py snapshot-output {PROJECT} post-draft`
2. `sync_state.py update-output {PROJECT} {chapter}` 각 chapter
3. `sync_state.py update-final {PROJECT}`
4. `python3 scripts/build_index.py {PROJECT} --quiet` — INDEX A2/A3 (output 실제 인용·discrepancy) 갱신, 각 paper `citation_state.use_count_in_output` 자동 갱신

**claim-extractor는 여기서 호출하지 않음** — 작성 자체와 무관, 평가 prep용. `평가해줘` 명령 prehook에서만 호출 (단계 4 평가 prehook 참조).
- 이유: claim-extractor는 *주장 추출*해서 axis1-reference-scorer의 input. 작성에 직접 관여 X.
- 효율: 사용자가 작성 후 수정만 반복하면 매번 claim-extraction 무의미. 평가 호출 시점에만 lazy 갱신.

### 단계 10: 결과 보고

```
✅ 초안 작성 완료!

📊 통계:
   - 총 단어 수: {W} words
   - 챕터: {N}개
   - 총 인용: {C}개
   - 사용된 논문: {P}편 (80% threshold 권장)

📁 생성된 파일:
   ✓ output/generative/{4 agents}.md (Generative phase 산출, 활용 시)
   ✓ output/00-positioning.md (positioning statement)
   ✓ output/0N-*.md (chapter별)
   ✓ output/outline-critique.md
   ✓ output/chapter-critique-0N.md (chapter별)
   ✓ output/peer-review-simulation.md
   ✓ output/claim-extraction-output.md
   ✓ final/complete-draft.md (통합본)
   ✓ final/complete-draft.docx (Word)
   ✓ INDEX.md 갱신 (A2 실제 인용 + A3 discrepancy)

🌱 Generative phase 사용 여부: {적용된 4 agent list 또는 skip}

📌 Critical Commitment 반영: {fulfilled}/{total}
🎭 Peer review verdict: {accept / minor revision / major revision / reject}

👉 다음 단계:
   - chapter 수정: "Chapter X 수정해줘: [구체 지시]"
   - 평가 실행: "flow 평가해줘"
   - 적대적 리뷰 추가: "X 학파 입장에서 반박해줘"
```

### 단계 11: 활동 로그 기록

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "초안 작성" "stage=output" "target=output/*" "result={N}챕터 {W}단어" "ref=ref:ch-{NNN}" "agents=writing-architect,adversarial-reviewer,peer-reviewer{,thesis-developer,output-cross-paper-insights,steelman-dialectic,field-positioning-oracle}" "commits={fulfilled}/{total}"
```

---

## 챕터 수정 (v3 — 수정 규모별 4 단계 분기)

사용자가 `"Chapter X 수정해줘: [내용]"` 또는 `"X장 수정: [내용]"` 등을 말하면 **수정 규모를 먼저 판단**하고 그에 맞는 흐름 적용.

### 단계 -1: Commitment 추출 Prehook (Critical Mode 활성 시)

`intellectual_ambition ≥ critical`이고 `critical-questions.md` mtime > `critical-commitments.md` mtime이면:
- `"답변 반영해줘"` 자동 실행 → critical-commitments.md 갱신
- 사용자에게 `🔄 답변에서 commitment 추출 완료` 알림

### 단계 0: 수정 규모 판단 + 사용자 확인

main agent가 사용자 수정 지시를 분석해 다음 중 하나로 분류 후 사용자 확인:

| 규모 | 판단 기준 | 사용자 명령 패턴 예시 |
|------|---------|---------------------|
| **국소** | 1-3 문단·문장 단위, 구체 지시 | "1문단 hedge 추가", "p.5 Smith 인용 강도 약화", "section 2 마지막 문장 수정" |
| **중간** | chapter 부분 재작성·논증 보강 | "Section 3 논증 더 정교하게", "반박 단락 추가", "페이지 5-7 재구성" |
| **큰** | chapter 전면 재작성 | "Chapter 2 전체 다시 써줘", "이 chapter 방향 바꿔서 재작성" |
| **Thesis-level** | 입장·positioning·핵심 주장 자체 변경 | "thesis 자체를 X에서 Y로 변경", "core argument 재정초", "분야 위치 잡기 다시" |

**확인 패턴**:
```
🔍 수정 규모 판단: 중간 (Section 3 논증 보강)

이 규모로 진행할까요?
1. 국소 (output-editor + citation-checker만, 빠름)
2. 중간 (output-editor + adversarial-reviewer Phase 2.5 + citation-checker, 권장)
3. 큰 (writing-architect Phase 2 재작성 + adversarial 1.5/2.5 + peer-review mini)
4. Thesis-level (generative phase 재실행 + writing-architect Phase 0/1/2/3)

응답: 번호 또는 "다른 규모로"
```

### 단계 1: 수정 전 자동 스냅샷

```bash
python3 scripts/sync_state.py snapshot-output {PROJECT_NAME} ch{X}-edit-{규모} 0{X}-{name}.md
```

규모 큰·Thesis-level이면 *전체 chapters* 스냅샷 (`pre-revise-{규모}`).

### 단계 2: 규모별 분기 흐름

#### 분기 A — 국소 수정 (3-agent 흐름)

```
1. output-editor 호출 — 사용자 지시 + 대상 chapter + 관련 analyzed/*.md
   └ Phase 1-4 (지시 해석 → 재료 수집 → 수정 적용 → 일관성 체크)
2. citation-checker 자동 (output-editor Phase 5)
3. sync_state.py update-output {chapter}
```

#### 분기 B — 중간 수정 (5-agent 흐름)

```
1. output-editor 호출 — 사용자 지시 적용 (chapter 부분 재작성)
2. adversarial-reviewer Phase 2.5 호출 — chapter critique (학파별 + Elite 패턴 위반)
   └ 산출: output/chapter-critique-0{X}-revise.md
3. critique 심각도 high·medium → output-editor 재호출 (자동 적용)
4. citation-checker 자동
5. sync_state.py update-output
```

#### 분기 C — 큰 수정 (chapter 전면 재작성, 6-agent 흐름)

```
1. writing-architect Phase 1 — outline 재설계 (chapter만)
   └ 사용자 승인 ✋
2. adversarial-reviewer Phase 1.5 — outline critique (mini)
3. writing-architect Phase 2 — chapter 작성 (self-critique loop)
4. adversarial-reviewer Phase 2.5 — chapter critique
5. output-editor — Phase 2.5 critique 자동 적용
6. peer-reviewer (mini, single chapter) — chapter-level simulated review
7. citation-checker + sync_state
```

#### 분기 D — Thesis-level 수정 (전체 재구성, 10+ agent 흐름)

```
[Generative phase 재실행] (옵션, 사용자 선택 — 권장)
  ├ thesis-developer — 새 입장의 implicit assumption 재점검
  ├ output-cross-paper-insights — emergent pattern 재평가
  ├ steelman-dialectic — 새 입장에 대한 critic 재구축
  └ field-positioning-oracle — 새 positioning 좌표

[flow.md 갱신] (사용자가 generative 산출 검토 후 직접 또는 flow-refiner)

[전체 재작성]
  ├ writing-architect Phase 0 — 새 positioning statement
  ├ writing-architect Phase 1 — 모든 chapter outline 재설계
  ├ adversarial-reviewer Phase 1.5 — outline critique
  ├ chapter별 loop:
  │   writing-architect Phase 2 + adversarial 2.5 + output-editor
  ├ peer-reviewer Phase 3 — full draft simulated review
  └ citation-checker + sync_state + build_index
```

### 단계 3: 통합 결과 보고

규모별 호출된 agents 명시:
```
✅ Chapter {X} 수정 완료 (규모: {국소/중간/큰/thesis-level})

📝 변경사항:
   - [변경 내용 요약]

🤖 호출된 agents (순서):
   1. output-editor → {요약}
   {규모별 추가 agents 순서대로}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 일관성 체크: ✅
🎭 Adversarial review (있으면): {high N건 / medium M건}
👨‍🏫 Peer review verdict (있으면): {accept / minor / major}
🤖 인용 감사: 정확 N개 / 수정 필요 M개
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 단계 4: 활동 로그 기록

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "챕터 수정" "stage=output" "target=Ch{X}" "scale={국소/중간/큰/thesis}" "result={변경 요약}" "ref=ref:ch-{NNN}" "agents={규모별 호출 list}"
```

---

## Gap 분석 (수동 호출)

사용자가 "gap 분석해줘", "연구 gap 찾아줘", "뭐가 안 다뤄졌어?" 등을 말하면:

### 단계 1: 🤖 output-gap-finder 에이전트 호출

1. `skills/agents/output-gap-finder.md` 파일을 읽는다
2. 현재 프로젝트의 `flow.md`와 `papers/analyzed/` 전체를 읽는다
3. Agent 도구로 output-gap-finder를 실행한다:
   - 전달: flow.md + 모든 analyzed/*.md + output-gap-finder.md 지침
   - 수행: 방법론/응용/데이터/이론/시간 Gap 5종 탐색
4. 결과를 `projects/{PROJECT_NAME}/gaps-analysis.md`에 저장한다

### 단계 2: 결과 보고

```
🔍 연구 Gap 분석 완료

📊 발견된 Gap: {N}개

| # | 유형 | Gap | 난이도 | 임팩트 |
|---|------|-----|--------|--------|
| 1 | 방법론 | [설명] | 🟢 낮음 | ⭐⭐⭐⭐⭐ |
| 2 | 응용 | [설명] | 🟡 중간 | ⭐⭐⭐⭐ |
| 3 | 데이터 | [설명] | 🔴 높음 | ⭐⭐⭐ |

⭐ 최우선 추천: Gap 1 — [이유]

💾 상세 분석: projects/{PROJECT_NAME}/gaps-analysis.md
```

### 단계 3: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "gap 분석" "result={N}개 gap" "agents=output-gap-finder"
```

---

## 방법론 추천/검증 (수동 호출 + empirical 자동 제안)

### 자동 제안 트리거

`.paper-metadata.json`의 `research_type == "empirical"`일 때 다음 시점에 **시스템이 능동적으로 methodology-advisor 사용을 제안**:

| 시점 | 제안 메시지 |
|------|-----------|
| 프로젝트 생성 직후 flow.md 저장 시 | "empirical 프로젝트로 감지됨. 방법론 추천을 받아보시겠습니까? → `방법론 추천해줘`" |
| 첫 `"flow 평가해줘"` + `"flow 평가해줘"` 실행 시 | "이 프로젝트는 empirical이지만 방법론이 flow.md에 아직 명시되지 않음. `방법론 추천해줘` 권장" |
| `"리서치 진행해줘"` 실행 시 | "Stage 1 리서치 전 방법론 방향 확정 권장. `방법론 추천해줘` 또는 `방법론 검증해줘`" |
| Stage 2 초안 작성 직전 | "초안 작성 전 `방법론 검증해줘`로 최종 점검 권장" |

사용자는 이 제안을 무시하거나 "skip" 가능. 그러나 **Stage 3 수정** 단계에서 방법론 약점이 축 2·3 감점의 주요 원인으로 나타나면 강력히 권고.

### 수동 호출 (모드 A/B)

사용자가 "방법론 추천해줘", "어떻게 접근해야 해?", "방법론 검증해줘" 등을 말하면:

### 단계 1: 모드 판별

- **Advisor 모드**: "추천", "어떻게", "방법 제안" 등 → 사전 추천
- **Critic 모드**: "검증", "괜찮아?", "체크" 등 → 사후 검증

### 단계 2: 🤖 methodology-advisor 에이전트 호출

1. `skills/agents/methodology-advisor.md` 파일을 읽는다
2. Agent 도구로 methodology-advisor를 실행한다:
   - Advisor: flow.md + analyzed/*.md + 연구 질문 전달 → 3가지 방법론 비교 표 생성
   - Critic: flow.md + 해당 챕터(output/03-methodology.md) 전달 → 타당성/신뢰성/윤리 검증
3. 결과를 화면에 보고한다

### 단계 3: 결과 보고 (Advisor 예시)

```
🧪 방법론 추천 결과

연구 질문 유형: [설명적/탐색적/...]

| 기준 | 방법 1 | 방법 2 | 방법 3 |
|------|--------|--------|--------|
| 방법 | [이름] | [이름] | [이름] |
| 난이도 | 🟢 | 🟡 | 🔴 |
| 소요 시간 | 2주 | 4주 | 8주 |
| 임팩트 | 중간 | 높음 | 매우 높음 |

⭐ 추천: 방법 1 — [현실적 이유]
```

### 단계 4: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "방법론 {advisor|critic}" "agents=methodology-advisor"
```

---

## 리뷰 체크/답변 (수동 호출)

사용자가 "리뷰 체크해줘", "심사 시뮬레이션", "리뷰 답변 도와줘" 등을 말하면:

### 단계 1: 모드 판별

- **Mode A (시뮬레이션)**: "리뷰 체크", "심사 시뮬레이션", "제출 전 체크" → 사전 심사
- **Mode B (대응)**: "리뷰 답변", "리뷰 분석", 리뷰 텍스트 붙여넣기 → 사후 대응

### 단계 2: 🤖 peer-reviewer 에이전트 호출

1. `skills/agents/peer-reviewer.md` 파일을 읽는다
2. Agent 도구로 peer-reviewer를 실행한다:
   - Mode A: final/complete-draft.md + papers/analyzed/ 전달 → 가상 심사자 2~3명 시뮬레이션
   - Mode B: 사용자가 붙여넣은 리뷰 텍스트 + 원고 전달 → 이슈 분류 + 답변 전략 + 초안
3. 결과를 화면에 보고한다

### 단계 3: 결과 보고 (Mode A 예시)

```
💬 사전 심사 시뮬레이션 결과

📋 종합 판정: Minor Revision

Reviewer 1 (방법론): Minor Revision
   🔴 [Major] 표본 크기 정당화 부족 → 검정력 분석 추가 필요
   🟡 [Minor] 변수 측정 방법 불명확

Reviewer 2 (분야 전문가): Major Revision
   🔴 [Major] 핵심 선행연구 Johnson (2022) 누락
   🟡 [Minor] 이론적 프레임워크 보강 필요

Reviewer 3 (실용주의자): Accept with Minor
   🟡 [Minor] Conclusion에서 실무적 함의 보강

🔴 반드시 수정 (2건):
   1. 표본 크기 정당화 → Section 3에 power analysis 추가
   2. Johnson (2022) → Background에 통합

🟡 수정 권장 (3건):
   [...]
```

### 단계 3: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "리뷰 {시뮬|대응}" "stage=final" "result={판정}" "agents=peer-reviewer"
```

---

## 🔄 Sync 확인 (sync 확인해줘)

사용자가 "sync 확인해줘", "sync 점검", "상태 확인해줘", "stale 체크" 등을 말하면:

> **참고**: 분석 명령은 단계 0에서 동일한 sync 체크를 자동 실행. 이 명령은 평가 없이 **sync만 독립 점검**할 때 사용.

### 단계 1: sync_state.py check 실행

```bash
python3 scripts/sync_state.py check {PROJECT_NAME}
```

출력 JSON에서 `stales` 배열을 파싱하여 사람이 읽을 수 있는 형태로 변환.

### 단계 2: 사용자 보고 (priority 등급별)

sync_state.py의 JSON 응답에서 `tier_counts`, `stales` (긴급도 순), `ordered_resolution_plan` (의존성 순) 를 파싱하여:

```
🔄 Sync 점검 결과

✅ 전체 동기화 상태 양호 (stale 0건 시 이 줄만)

⚠️ Stale 감지: {총 N}건
   🔴 P1-Critical: {Na}건  🟡 P2-High: {Nb}건  🟢 P3-Medium: {Nc}건

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 P1-Critical (먼저 해결)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. [flow_changed] flow.md 변경됨 (score: 30)
   영향: analyzed/*.md 일부 구버전, evaluations/latest/ 재생성 필요
   → "논문 재분석해줘" 후 "flow 평가해줘"

2. [paper_removed] Zelazo_2022.pdf 제거됨 (score: 40, dangling 2챕터)
   영향: Chapter 2, 4에 dangling citation 3건
   → "논문 제거해줘: Zelazo_2022.pdf"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 P2-High
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. [chapter_flow_drift] 챕터 2건이 구 flow 기반 (score: 30)
   → "Chapter 3 수정해줘", "Chapter 4 수정해줘"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 P3-Medium
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. [final_stale] final/* 가 chapters 현재와 불일치 (score: 5)
   → "최종 통합해줘"
```

### 단계 3: 의존성 순 실행 계획 제시

`ordered_resolution_plan`은 **의존성 순서**로 정렬된다 — 단순히 긴급도가 아니라 cascade 영향 기반. P1을 먼저 풀어야 P2/P3가 의미 있음:

```
📋 권장 실행 순서 (의존성 순):

1. "새 논문 처리해줘" (paper_added_untracked 해소)       — P3
2. "논문 제거해줘: Zelazo_2022.pdf" (dangling 해소)      — P1
3. "논문 재분석해줘" (flow_changed 전파)                 — P1
4. "Chapter 3 수정해줘", "Chapter 4 수정해줘" (drift 해소) — P2
5. "최종 통합해줘" (final 재빌드)                        — P3
6. "flow 평가해줘" (전체 재평가 마지막)                       — P3

⚠️ 이 순서로 진행하지 않으면 후속 단계에서 같은 stale이 다시 감지됩니다
   (예: Chapter 수정 전에 평가해도 여전히 구버전 기반 경고).
```

### 단계 4: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "sync 점검" "result=stale P1:{a} P2:{b} P3:{c}"
```

---

## 🗑 논문 제거 (논문 제거해줘)

사용자가 "논문 제거해줘: {파일명}", "Kroupin_2025 논문 빼줘", "논문 {파일명} 삭제해줘" 등을 말하면:

### 단계 1: 대상 확인

1. `papers/collected/{파일명}.pdf` 존재 확인 — 없으면 중단
2. `.sync-state.json`의 papers 엔트리 존재 확인
3. 해당 논문을 인용하는 챕터 탐지 (dangling 후보):
   ```bash
   python3 scripts/sync_state.py check {PROJECT_NAME}
   ```
   의 `dangling_in_chapters` 필드 활용

### 단계 2: 사용자 확인

```
🗑 논문 제거 전 확인

대상: Zelazo_2022.pdf
영향:
  - papers/collected/에서 archived/로 이동
  - papers/analyzed/Zelazo_2022-analysis.md를 archived/analyzed/로 이동
  - .paper-metadata.json 엔트리 제거
  - 해당 stage의 claim-extraction에서 관련 MATCHED 3건이 UNMATCHED-EXTERNAL로 전환
  - Chapter 2, Chapter 4에 dangling citation 가능성 (사후 citation-checker로 확인 권장)

진행할까요? [예 / 아니오]
```

### 단계 3: 안전 이동 (archived 폴더로)

사용자 승인 시:

```bash
mkdir -p projects/{PROJECT_NAME}/papers/archived
mkdir -p projects/{PROJECT_NAME}/papers/archived/analyzed
mv projects/{PROJECT_NAME}/papers/collected/{파일명}.pdf \
   projects/{PROJECT_NAME}/papers/archived/
mv projects/{PROJECT_NAME}/papers/analyzed/{파일명}-analysis.md \
   projects/{PROJECT_NAME}/papers/archived/analyzed/ 2>/dev/null || true
```

### 단계 4: 메타데이터·sync 갱신

1. `.paper-metadata.json`에서 해당 엔트리 제거
2. `python3 scripts/sync_state.py remove-paper {PROJECT} {파일명}` 실행
3. `claim-extraction-flow.md / claim-extraction-output.md` (stage에 맞게)에서 해당 논문을 인용하던 MATCHED 문장을 UNMATCHED-EXTERNAL 또는 UNMATCHED-INTERNAL(다른 PDF로 대체 가능 여부 판별)로 재분류

### 단계 5: dangling 경고 + 수정 가이드

```
✅ 논문 제거 완료: Zelazo_2022.pdf → archived/

⚠️ Dangling citation 감지:
  - Chapter 2 p.3: "Zelazo (2022) argues..."
  - Chapter 2 p.5: "(Zelazo, 2022)"
  - Chapter 4 p.2: "Zelazo (2022) demonstrated..."

권장 조치:
  "Chapter 2 수정해줘: Zelazo (2022) 인용을 Doebel (2020)으로 대체 또는 제거"
  "Chapter 4 수정해줘: Zelazo (2022) 인용 재검토"

이후 분석 명령 실행하여 축 1 점수 변화 확인.
```

### 단계 6: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "논문 제거" "target={파일명}.pdf" "result=archived" "dangling={N}"
```

---

## 📦 최종 통합 (최종 통합해줘)

사용자가 "최종 통합해줘", "final 재빌드", "docx 재생성", "chapter 합쳐줘" 등을 말하면:

### 단계 1: 전제 조건 확인

1. `output/*.md` 파일이 존재하는지 확인 — 없으면 "먼저 초안 작성해줘"로 안내
2. `scripts/sync_state.py check`로 챕터 간 inconsistency 사전 탐지

### 단계 2: chapters 병합 → complete-draft.md

`output/`의 모든 `*.md` 파일을 번호순으로 병합하여 `final/complete-draft.md` 생성:

```bash
cat projects/{PROJECT_NAME}/output/*.md \
  > projects/{PROJECT_NAME}/final/complete-draft.md
```

필요 시 섹션 구분자(`---`) 삽입.

### 단계 3: docx 생성

docx skill 또는 pandoc을 사용하여 `final/complete-draft.docx` 생성.

### 단계 4: Sync 갱신

```bash
python3 scripts/sync_state.py update-final {PROJECT_NAME}
```

### 단계 5: 보고

```
✅ 최종 통합 완료

📄 생성:
   - final/complete-draft.md ({N} words)
   - final/complete-draft.docx

📊 포함 챕터:
   - 01-introduction.md
   - 02-background.md
   - 03-analysis.md
   - 04-conclusion.md

💾 sync 상태 갱신 완료

👉 다음 단계:
   - "리뷰 체크해줘" → peer-reviewer 심사 시뮬레이션
   - 분석 명령 → 최종 평가
```

### 단계 6: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "최종 통합" "stage=final" "target=final/complete-draft.md" "result={W}단어"
```

---

## 🔄 논문 재분석 (논문 재분석해줘) — Delta 모드 기본

사용자가 "논문 재분석해줘", "paper 재분석", "Zelazo 논문 다시 분석", "모든 논문 재스캔" 등을 말하면:

**플래그**:
- `논문 재분석해줘` → **delta 기본** (flow 변경 섹션에 영향받는 논문만)
- `논문 재분석해줘 --full` → 모든 논문 Mode B 재실행
- `논문 재분석해줘 {파일명}` → 지정 논문만 (delta 무시)
- `"{파일명} 비판적으로 분석해줘"` → critique_target=true 설정 + Mode C critical reading 추가

### 단계 1: Delta 대상 선정

```bash
python3 scripts/paper_reanalysis_delta.py {PROJECT_NAME}
```

이것이 반환하는 JSON의 `affected_papers` 리스트가 재분석 대상. `--full` 플래그 시 `paper_reanalysis_delta.py {P} --full`로 전량 반환.

출력 예시:
```json
{
  "mode": "delta",
  "changed_sections": ["Section 3: Impurity Problem", "Section 4: Four EFs"],
  "affected_papers": ["Loffler_2024", "Doebel_2020", "BussSpencer_2014"],
  "total_analyzed": 138,
  "skipped": 135
}
```

### 단계 2: paper-analyst Mode B 호출

각 대상 PDF마다 `paper-analyst`를 통해 병렬 호출:

1. `skills/agents/paper-analyst.md` 읽기
2. Agent 도구로 paper-analyst를 **Mode B**로 호출 (model: sonnet, 재분석은 opus 불필요):
   - 전달: PDF 경로 + **현재 flow/flow.md** + 기존 `analyzed/{파일명}-analysis.md` + 변경 섹션 목록 + 재분석 각도
   - 수행: PDF 재스캔 → analyzed/*.md에 `## [v{N+1}] 재분석: {각도}` append (v1 내용은 절대 수정/삭제 금지)
3. `python3 scripts/sync_state.py update-paper {PROJECT} {파일명}` 실행

### 단계 2b: Tier 승격 (선택)

`--tier=1` 플래그가 있으면:
1. triage.json의 tier를 1로 승격 (v3에서는 paper-analyst Mode B 직접 호출)
2. Mode A-tier1 Critical Reading 섹션을 **추가로** 호출하여 append (opus)

### 단계 3: claim-extraction 반영

`claim-extraction-flow.md / claim-extraction-output.md` (stage에 맞게)에서 UNMATCHED-INTERNAL이었던 문장들을 재확인:
- 재분석 결과 새 v{N+1}에 해당 주장이 커버되었으면 → MATCHED로 전환
- 여전히 커버 못하면 → UNMATCHED-EXTERNAL로 재분류 (RESEARCH 필요)

### 단계 4: 챕터 sync 경고

이미 `output/*.md`가 존재하고 `.sync-state.json`의 `chapters[x].papers_used[파일명]` 버전이 구버전이면:

```
⚠️ 챕터 sync 경고

다음 챕터가 재분석 전 버전(v1)의 논문 분석을 기반으로 작성됨:
  - Chapter 3: Kroupin_2025 v1 → 현재 v2
  - Chapter 4: Zelazo_2022 v1 → 현재 v2

새 분석 반영을 위해 수정 권장:
  "Chapter 3 수정해줘: Kroupin v2 새 인용 다발 반영"
  "Chapter 4 수정해줘: Zelazo v2 반영"
```

### 단계 5: 보고

```
✅ 논문 재분석 완료: {N}편

📄 버전 갱신:
   - Kroupin_2025.pdf: v1 → v2 (+ Section 4 pretend play 각도 추가)
   - Zelazo_2022.pdf: v1 → v2 (+ hot EF 보편성 수치 추가)

🔄 claim-extraction 반영:
   - UNMATCHED-INTERNAL {N}건 → MATCHED 전환
   - 잔존 UNMATCHED-INTERNAL: {N}건 (추가 재분석 또는 RESEARCH 필요)

⚠️ 챕터 sync 경고: {N}건 (위 참조)

👉 다음 단계:
   - "Chapter X 수정해줘: 새 분석 반영"
   - 모든 sync 확인: "sync 확인해줘"
   - 평가 갱신: "flow 평가해줘"
```

### 단계 6: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "논문 재분석" "target={파일}" "result=v{N}→v{N+1}" "agents=paper-analyst"
```

---

## 🎭 비판 모드 설정 (intellectual_ambition)

사용자가 `"비판 모드 설정해줘"`, `"intellectual_ambition 설정해줘"`, `"비판 모드 {level}"` 등을 말하면:

### 단계 1: 요청 파싱

사용자 입력에서 레벨 추출:
- `"incremental"` / `"비판 모드 끄기"` / `"점진적"` → incremental
- `"critical"` / `"비판적"` → critical
- `"paradigm-shifting"` / `"패러다임 도전"` → paradigm-shifting

명시 없으면 flow.md를 분석하여 권장값 제시 후 사용자 확인.

### 단계 2: flow.md 기반 자동 감지 (레벨 미명시 시)

flow.md를 스캔하여 다음 단서 탐지:

**critical 신호**:
- "비판한다", "재개념화한다", "문제가 있다", "대안을 제시한다"
- 특정 논문의 **근본 가정을 의심**하는 문장
- "이분법은 타당한가?" 같은 **분야 전제 의심**

**paradigm-shifting 신호**:
- "새로운 프레임워크", "근본적 재정의", "revolution"
- "이 분야는 X라는 잘못된 전제 위에 서 있다"
- 저자 기여가 **개념적 신개념 도입**

**incremental 신호**:
- 데이터 수집·분석 중심
- 기존 이론 **검증·확장**
- 특정 맥락·집단으로 **적용 범위 확대**

### 단계 3: 사용자 확인

```
현재 설정: intellectual_ambition = "incremental"

flow.md 분석 결과:
- "Kroupin의 이분법은 타당한가?" → critical 신호
- "규칙의 속성으로 재개념화" → critical 신호
- "보편적 EF와 특수적 EF의 양립" → critical 신호

→ 권장: **critical**로 변경

변경하시겠습니까? [yes / no / paradigm-shifting로 승격]
```

### 단계 4: 설정 반영

`.paper-metadata.json` 업데이트:
```json
{
  "intellectual_ambition": "critical",
  "ambition_updated_at": "2026-04-18T10:00:00"
}
```

### 단계 5: 후속 동작 안내

```
✅ intellectual_ambition을 "critical"로 설정

이제 활성화되는 기능:
  🎭 axis6-critical-scorer (축 6 추가)
  🤔 critical-companion (Stage 마일스톤마다 Socratic 질문)
  👹 peer-reviewer Reviewer 4 (Iconoclast)
  🔍 paper-analyst Mode C (핵심 논문 비판적 읽기)

비활성화 (incremental로 되돌리려면):
  "비판 모드 incremental로 설정해줘"

다음 단계:
  "flow 평가해줘"로 Critical Mode 포함 전체 평가 실행
```

### 자동 제안 트리거

첫 `"flow 평가해줘"` + `"flow 평가해줘"` 실행 시, intellectual_ambition이 `incremental`이고 flow.md에서 critical 신호 ≥ 3개 감지되면 evaluation-orchestrator가 사용자에게 자동 제안:

```
💡 제안: 이 프로젝트는 "critical" 성향이 강합니다.
   intellectual_ambition을 critical로 변경하면 Critical Mode가 활성화되어
   새로운 관점·비판적 시각 지원이 강화됩니다.
   
   변경: "비판 모드 critical로 설정해줘"
   현 상태 유지: 그대로 평가 진행
```

### 단계 6: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "비판 모드 설정" "ambition={level}"
```

---

## 💬 답변 반영 (답변 반영해줘 — 경량 commitment 추출)

사용자가 `"답변 반영해줘"`, `"commitments 추출해줘"` 등을 말하면:

### 단계 1: 선행 조건 확인

1. `critical-questions.md` 존재 확인 (없으면 "먼저 질문 업데이트해줘" 안내)
2. 기존 `critical-commitments.md`가 있으면 snapshot:
   ```bash
   python3 scripts/sync_state.py snapshot-critical-commitments {PROJECT_NAME} manual-extract
   ```

### 단계 2: 경량 critical-companion 호출 (Phase 6만 실행)

critical-companion의 Phase 1-5는 스킵하고 **Phase 6 (commitment 추출)만** 실행:

1. `skills/agents/critical-companion.md` 읽기
2. Agent 도구로 호출 시 "EXTRACT_ONLY_MODE" 플래그 전달:
   - 입력: 현재 critical-questions.md + output/*.md (반영 상태 판정용) + 기존 critical-commitments.md
   - 수행: Phase 6만 — commitment 추출·분류·상태 업데이트
   - 출력: critical-commitments.md 갱신

### 단계 3: 결과 보고

```
📌 Commitment 추출 완료

💾 critical-commitments.md 갱신:
  🟢 FULFILLED: 2건
  🟡 PARTIAL: 1건
  🔴 UNFULFILLED: 2건
  ⚠️ CONFLICTING: 0건
  
  총 반영률: 50% (2.5/5)

🔴 UNFULFILLED commitment (2건):
  - [C-003] 급진적 대안 steelman (Section 5)
  - [C-004] 동양 철학 관점 재고 (Section 4)

👉 다음 단계:
  1. UNFULFILLED 해소: "Chapter 5 수정해줘: [C-003] 급진적 대안 steelman 강화"
  2. 또는 답변 자체를 재고: critical-questions.md 답변 수정 후 다시 "답변 반영해줘"
  3. 전체 평가: "flow 평가해줘"
```

**이 명령의 가치**: 사용자가 답변만 쓰고 끝내는 것이 아니라, **답변이 시스템에 actionable하게 등록되었음을 즉시 확인**. writing 작업 전에 commitment 추출을 보장.

### 단계 4: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "답변 반영" "result={N} commitments extracted" "agents=critical-companion"
```

---

## 🤔 비판적 질문 업데이트 (critical-companion)

사용자가 `"질문 업데이트해줘"`, `"비판적 질문 생성해줘"`, `"critical questions"` 등을 말하면:

### 단계 1: 선행 조건 확인

1. `.paper-metadata.json`의 `intellectual_ambition` 확인
   - `incremental`이면: "이 기능은 ambition이 critical 이상일 때 활성화됩니다. 변경하시겠습니까?" 안내
2. 기존 `critical-questions.md` 존재 여부 확인 (있으면 버전 관리 대상)

### 단계 2: 이전 버전 스냅샷

기존 `critical-questions.md`가 존재하면:
```bash
python3 scripts/sync_state.py snapshot-critical-questions {PROJECT_NAME} {trigger}
```

trigger 예: `post-research`, `post-draft`, `post-revision`, `manual-update`

### 단계 3: 🤖 critical-companion 호출

1. `skills/agents/critical-companion.md` 파일을 읽는다
2. Agent 도구로 critical-companion 실행:
   - 전달: flow.md + output/* (있으면) + evaluations/latest/evaluation.md + 이전 critical-questions.md + intellectual_ambition
   - 수행: Stage 판별 → 카테고리별 질문 생성 → 이전 답변과 원고 정합성 점검 → 다음 버전 예고
3. 에이전트가 새 버전 `critical-questions.md` 저장, 이전은 archive로 이동

### 단계 4: 사용자 알림

```
📝 비판적 질문 v{N} 업데이트 완료

경로: projects/{PROJECT}/critical-questions.md
이전 버전: projects/{PROJECT}/history/{stage}/critical/{NNN}-{trigger}.md

📊 요약:
   🆕 신규 질문: {M}개
   🔁 Carry-over: {K}개
   ⚠️ 정합성 경고: {L}건

⚠️ 중요: 시스템이 답변하지 않습니다. 직접 작성하세요.
    답변 작성이 새로운 관점의 발견 과정입니다.
    답변 후 "flow 평가해줘" 재실행하면 axis6-critical-scorer가 반영합니다.

👉 다음 단계:
   1. critical-questions.md 열어 질문에 자기 언어로 답변
   2. 답변한 내용을 원고에 반영할지 결정
   3. 분석 명령 → 답변·원고 정합성 점검
```

### 단계 5: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "질문 업데이트" "result=v{N}" "ref=ref:q-{NNN}" "agents=critical-companion" "categories={list}"
```

---

## 🎭 비판적 시각 평가 (axis6-critical-scorer, 단독 호출)

사용자가 `"비판적 시각 평가해줘"`, `"critical lens 평가"`, `"paradigm 평가"` 등을 말하면:

### 단계 1: 선행 조건 확인

`.paper-metadata.json`의 `intellectual_ambition ≥ critical` 확인. `incremental`이면 다음 메시지 후 중단:
> "이 평가는 ambition이 critical 이상일 때만 의미 있습니다. `intellectual_ambition`을 변경하시겠습니까?"

### 단계 2: 🤖 axis6-critical-scorer 호출

1. `skills/agents/axis6-critical-scorer.md` 파일을 읽는다
2. Agent 도구로 실행:
   - 전달: flow.md 또는 초안 + critical-questions.md (있으면 답변 정합성 점검 핵심) + analyzed/*.md (Mode C 것 우선) + evaluations/latest/axis4-originality.md
   - 수행: C-1 Paradigm Mapping / C-2 Fault-line / C-3 Bold Defense / C-4 Minority Recovery 4축 평가 + critical-questions.md 답변-원고 정합성 검증
3. 결과를 `projects/{PROJECT_NAME}/evaluations/latest/axis6-critical.md`에 저장

### 단계 3: 화면 보고

축별 카테고리 (🟢🟡🟠🔴⚫) + critical-questions.md 정합성 요약 + 심사자 예상 공격 + 개선 권장 우선순위. 점수는 보조 (axis6-critical.md의 `<details>` 안).

### 단계 4: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "축 6 심층" "axis6_status={emoji} {label}" "agents=axis6-critical-scorer"
```

---

## 🔍 논문 비판적 분석 (paper-analyst Mode C)

사용자가 `"비판적으로 분석해줘: {파일}"`, `"{논문} critical read"` 등을 말하면:

### 단계 1: paper-analyst Mode C 호출

1. `skills/agents/paper-analyst.md` 파일을 읽는다
2. Agent 도구로 **Mode C**로 호출:
   - 전달: 대상 PDF + flow.md + 기존 analyzed/*.md + Mode C 지침
   - 수행: Hidden assumptions / Methodological biases / Field politics / Alternative interpretations / Silences 추출
3. `analyzed/{파일}-analysis.md`에 `## [critical] 비판적 읽기` 섹션 **append** (기존 v1/v2 보존)

### 단계 2: 비판적 발견 사항 알림

```
🔍 비판적 분석 완료: {파일}

📌 주요 발견:
   • Hidden assumptions: {N}개
   • Methodological biases: {M}개
   • Field politics: {분석}
   • Alternative interpretations: {K}개
   • Silences: {L}개

💡 이 발견을 critical-questions.md 다음 버전 질문 후보로 제안합니다.
   "질문 업데이트해줘" 실행 권장.
```

마지막으로 활동 로그 기록 (MD Layer 4):
```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "논문 Mode C" "target={파일}" "result=critical reading appended" "agents=paper-analyst"
```

---

## 독창성 심층 평가 (축 4, 단독 호출)

사용자가 "독창성 평가해줘", "contribution 평가", "novelty 확인해줘" 등을 말하면:

1. `skills/agents/axis4-originality-scorer.md` 파일을 읽는다
2. 현재 프로젝트의 평가 대상(flow.md 또는 초안) + `papers/analyzed/*.md` + `papers/search-results/{stage}.md`를 전달하여 Agent 실행
3. 결과를 `projects/{PROJECT_NAME}/evaluations/latest/axis4-originality.md`에 저장

**주요 출력**: Novelty Delta Map (선행 연구 3편 대비 차별점 테이블) + "So What?" 명시 여부 + 심사자 예상 공격.

**활동 로그** (MD Layer 4):
```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "축 4 심층" "axis4_status={emoji} {label}" "agents=axis4-originality-scorer"
```

---

## 구성개념 정의 정밀도 심층 평가 (축 5, 단독 호출)

사용자가 "정의 정밀도 평가해줘", "개념 평가", "construct clarity" 등을 말하면:

1. `skills/agents/axis5-concept-scorer.md` 파일을 읽는다
2. 현재 프로젝트의 평가 대상을 전달하여 Agent 실행
3. 결과를 `projects/{PROJECT_NAME}/evaluations/latest/axis5-concept.md`에 저장

**주요 출력**: 핵심 구성개념 정의 감사 테이블 + 의미 drift 탐지 + 범주/차원 선택 근거 감사.

**활동 로그** (MD Layer 4):
```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "축 5 심층" "axis5_status={emoji} {label}" "agents=axis5-concept-scorer"
```

---

## 🧠 작업 추천 (작업 추천해줘)

사용자가 `"작업 추천해줘"`, `"뭘 해야 해?"`, `"next step"`, `"추천해줘"` 등을 말하면:

**입력 소스 4종 통합**:
1. **폴더 스캔** — 어떤 단계에 무엇이 있는지 직접 확인 (research-gap·flow·output·final + papers/) ← **primary**
2. 각 단계의 `evaluation.md` 다음 액션 섹션 (있으면) ← **primary**
3. `activity.log` 기반 최근 활동 (보강)
4. `sync_state.py check` 기반 stale 항목 (주의사항)

### 단계 1: 폴더 스캔으로 진척 상태 파악

main agent가 다음을 직접 확인:
- `research-gap/research-gap.md` 존재? `research-plan.md` 존재? `gap-report.md` 존재?
- `flow/flow.md` 존재 + 본문 100자 이상? `flow/evaluations/latest/evaluation.md` 존재 + 최신?
- `output/0N-*.md` 존재? `output/evaluations/latest/evaluation.md` 존재?
- `final/complete-draft.md` 존재?
- `papers/candidates/{research-gap,flow}/` 미처리 PDF?
- `papers/search-results/{research-gap,flow}.md`의 R-NN/H-NN 미처리?

### 단계 2: evaluation.md 다음 액션 추출

존재하는 모든 `evaluation.md`의 `## 🧭 다음 액션` 섹션 읽기. 이것이 추천의 1차 뼈대.

### 단계 3: activity.log 기반 보강

```bash
python3 scripts/activity_log.py recommend {PROJECT_NAME} 14
```

반환 JSON에서 `current_state` (마지막 활동·stage·평가 결과) 추출.

### 단계 3: sync check

```bash
python3 scripts/sync_state.py check {PROJECT_NAME}
```

### 단계 2: 종합 보고 (사용자 친화 포맷)

JSON을 파싱하여 아래 형식으로 출력:

```
📍 현재 상태 (최근 14일 로그 기반)

   마지막 활동: 평가 완료 (3일 전)
   마지막 stage: output
   평가 판정: 🟠 Major Revision (카테고리: 🔴:1 🟠:3 🟡:1)
   로그 엔트리: 42건

   🔄 Sync 상태: P1:0 / P2:1 / P3:0 (총 1건 stale)

💡 작업 추천 (우선순위 순)

1. 🔴 "Chapter 5 수정해줘: 급진적 steelman 강화"
   이유: [C-003] UNFULFILLED commitment 감지. Iconoclast 지적 예상.
   예상 효과: critical-lens 축 6 +12점, commitment 커버리지 60%→80%
   🔗 근거 로그: [2026-04-20 14:30] 답변 반영 | ... | 2 UNFULFILLED

2. 🟡 "flow 평가해줘"
   이유: 초안 후 3일 경과, 전체 5축 재평가 시점
   예상 효과: delta 기준으로 어느 축이 움직였는지 확인
   🔗 근거 로그: [2026-04-20 11:00] 초안 작성 | ...

3. 🟢 "sync 확인해줘"
   이유: P2 stale 1건 있음 — 해소 후 다음 단계 진행 권장
   🔗 근거 로그: sync 점검 결과 (방금)

👉 위 중 하나를 실행하거나, 직접 명령을 입력하세요.
```

### 단계 3: 로깅

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "작업 추천 제시" "result=3 recommendations"
```

(이는 hook도 자동 기록하지만 MD Layer 4 fallback으로 명시)

---

## ⏪ Time-travel Archive 조회 (로그 라인 기반)

사용자 입력에서 `ref:TYPE-NNN` 패턴이 감지되고 "이 시점 ... 보여줘" 같은 요청이 오면:

### 단계 1: ref 패턴 추출

사용자 입력에서 다음 정규식으로 추출:
```
ref:([a-z\-]+)-(\d{3})
```

### 단계 2: archive 경로 해석

```bash
python3 scripts/activity_log.py resolve-ref {PROJECT_NAME} ref:{kind}-{NNN}
```

반환되는 경로 목록 (kind별):
- `ref:eval-NNN` → `history/{stage}/evaluations/NNN-{date}-{stage}/`
- `ref:ch-NNN` → `output/archive/NNN-{date}-{trigger}/`
- `ref:q-NNN` → `history/{stage}/critical/NNN-{date}-{trigger}.md`
- `ref:commits-NNN` → `history/{stage}/critical/NNN-{date}-{trigger}.md`

### 단계 3: 사용자 요청에 따라 파일 조회·출력

- "evaluation 보여줘" → `archive/{folder}/evaluation.md` Read 후 출력
- "상태 요약" → 해당 폴더 모든 파일 짧게 요약
- "되돌려줘" / "복원" → **거부**: "archive는 읽기 전용입니다. 직접 `cp archive/{path}/* {dest}/`로 복사하시면 됩니다."

### 단계 4: 로깅

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "⏪ time-travel 조회" "ref=ref:{kind}-{NNN}" "result=displayed"
```

---

## 📝 MD Layer 4: Activity Log Fallback 지시

**시스템 설계**: activity.log는 Claude Code hooks(harness 레벨)에서 자동 기록됩니다. 그러나 hook이 실패하거나 우회되는 경우를 대비해 각 주요 명령은 **완료 후 명시적으로 로그를 남겨야** 합니다.

### 명령별 로깅 원칙

모든 주요 명령 섹션은 **최종 단계**에서 다음을 실행:

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "{action_label}" \
  "stage={stage}" "target={target}" "result={result}" \
  "ref=ref:{kind}-{NNN}" "agents={agent_list}" \
  "{meta_key}={meta_value}"
```

### 명령별 표준 action_label

| 명령 | action_label | 핵심 필드 |
|------|------------|----------|
| 프로젝트 생성 | "프로젝트 생성" | target=이름, ambition 메타 |
| 평가해줘 | "평가 완료" | stage, result=점수/판정, ref:eval-NNN, agents |
| 레퍼런스 점검해줘 | "레퍼런스 점검 완료" | result=축1 delta |
| flow 업데이트해줘 | "flow 업데이트" | result=제안/반영 수 |
| 리서치 진행해줘 | "RESEARCH 실행" | result=완료 수 |
| 새 논문 처리해줘 | "논문 처리" | target=PDF 수, agents=paper-analyst |
| 논문 재분석해줘 | "논문 재분석" | target=파일, result=v→v+1 |
| 논문 제거해줘 | "논문 제거" | target=파일, dangling 메타 |
| 초안 작성해줘 | "초안 작성" | result=챕터/단어 수, ref:ch-NNN, commits 메타 |
| Chapter X 수정해줘 | "챕터 수정" | target=ChX, result=변경 요약, ref:ch-NNN |
| 최종 통합해줘 | "최종 통합" | result=단어 수 |
| 리뷰 체크해줘 | "리뷰 시뮬" | result=판정 |
| 질문 업데이트해줘 | "질문 업데이트" | result=v번호, categories 메타 |
| 답변 반영해줘 | "답변 반영" | result=commitments count |
| 비판 모드 설정해줘 | "비판 모드 설정" | ambition 메타 |
| sync 확인해줘 | "sync 점검" | result=stale tier 집계 |
| gap 분석해줘 | "gap 분석" | result=gap 수 |
| 방법론 추천/검증 | "방법론 {A/C}" | - |
| 독창성 평가해줘 | "축 4 심층" | result=점수 |
| 정의 정밀도 평가해줘 | "축 5 심층" | result=점수 |
| 비판적 시각 평가해줘 | "축 6 심층" | result=점수 |
| 비판적으로 분석해줘 | "논문 Mode C" | target=파일 |
| 작업 추천해줘 | "작업 추천 제시" | result=추천 수 |

### 왜 Layer 4도 필요한가

Hooks는 **시스템이 실행되는 환경**을 전제로 함:
- 사용자가 `.claude/settings.json`을 수정하거나 지운 경우 → hooks 비활성
- Claude Code 버전 차이로 hooks spec 변경 시 → 작동 안 함
- 프로젝트 감지 실패 시 → hook이 로그를 쓰지 못함

MD 지시는 **Claude가 명령 처리 중 직접 호출**하므로 hooks 장애와 무관하게 작동. **두 계층이 서로 보완**하여 신뢰도 보장.

---

## 명령어 레퍼런스

명령어 전체 리스트·플래그·에이전트 매핑은 본 파일 상단 §전체 작업 흐름과 각 명령 섹션의 스펙을 참조. 사용자 대상 요약은 `GUIDE.md`, 전체 레퍼런스는 `MANUAL.md`.

**주요 명령 실행 시 자동 sync 동작**:
- 실행 시작 시 → `sync_state.py check` → Critical stale 시 사용자 확인
- 실행 완료 후 → `sync_state.py update-*` → 해당 아티팩트 상태 기록
