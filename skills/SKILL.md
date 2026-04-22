---
name: research-agent
description: "Academic research project management with AI agents. Creates projects, manages papers with Consensus, generates drafts with Flow-based structure."
---

# Research Agent System

이 스킬은 research-agent 폴더 안의 projects/ 디렉토리에서 작동합니다.

## 전체 작업 흐름 (5축 평가 기반)

```
[프로젝트 생성 + flow.md 작성]
   ↓
[🎯 평가해줘] ← 5축 냉정 평가 + 작업 계획서 생성 (핵심 진입점)
   ↓
┌──────────┬──────────┬──────────┬──────────┐
│ 📚 리서치 │ ✍️ 1차작성 │ 🔧 수정   │ ✅ 최종  │
│ Stage 1  │ Stage 2  │ Stage 3  │ Stage 4  │
└──────────┴──────────┴──────────┴──────────┘
   ↑ 각 단계 완료 후 [🎯 평가해줘] 재실행하여 진척 확인
```

**핵심 원칙**: flow.md가 완성되면 반드시 `평가해줘`를 먼저 실행한다. 평가에서 나온 **work-plan.md**가 이후 4단계(리서치→1차작성→수정→최종)의 작업 순서를 결정한다.

## 5축 평가 기준

flow/원고를 top-tier 저널 심사 엄격도로 평가한다. 각 축은 100점 만점 (하위 기준 각 25점).

| 축 | 이름 | 핵심 질문 | 전문 에이전트 |
|---|------|----------|-------------|
| **1** | 논문 레퍼런스 충실도 | Coverage + Accuracy + Authority + Balance | citation-auditor |
| **2** | 논리 전개 완성도 | Argument chain + Transition + Thesis alignment + Scope closure | writing-architect |
| **3** | 반박/강화 논리 | Steelman + Falsifiability + Limitations + Reviewer attack surface | peer-reviewer |
| **4** | 독창성·기여도 | "So What?" + Novelty positioning + Contribution layer + Implications | **originality-evaluator** |
| **5** | 구성개념 정의 정밀도 | Definition + Operationalization + Boundary + Categorical/Dimensional | **concept-clarity-evaluator** |

## 서브 에이전트 시스템

이 스킬은 14개의 서브 에이전트를 사용합니다. 각 에이전트의 상세 프롬프트와 노하우는 `skills/agents/` 폴더에 정의되어 있습니다. 에이전트를 호출할 때는 해당 파일의 전체 내용을 읽어서 Agent 도구의 prompt에 포함하세요.

| 에이전트 | 파일 | 호출 시점 | 방식 |
|----------|------|-----------|------|
| **flow-evaluator** 🎯 | `skills/agents/flow-evaluator.md` | "평가해줘" / "flow 평가" / "원고 평가" | 자동 (평가 진입점) |
| **claim-extractor** 📝 | `skills/agents/claim-extractor.md` | 줄글 flow.md 문장 주장 추출 (flow-evaluator 자동 호출) | 자동 |
| **originality-evaluator** | `skills/agents/originality-evaluator.md` | 축 4 심층 (flow-evaluator 자동 호출) | 자동/수동 |
| **concept-clarity-evaluator** | `skills/agents/concept-clarity-evaluator.md` | 축 5 심층 (flow-evaluator 자동 호출) | 자동/수동 |
| **critical-lens-evaluator** 🎭 | `skills/agents/critical-lens-evaluator.md` | 비판적 시각 축 (ambition ≥ critical 시 자동) | 자동/수동 |
| **critical-companion** 🤔 | `skills/agents/critical-companion.md` | Socratic 질문 생성 (stage 마일스톤마다 자동) | 자동/수동 |
| **paper-analyst** | `skills/agents/paper-analyst.md` | "논문 처리" (A) / "논문 재분석" (B) / "비판적으로 분석" (C) | 자동 |
| **writing-architect** | `skills/agents/writing-architect.md` | "초안 작성" (신규 챕터 창작 전용) | 자동 |
| **chapter-editor** ✏️ | `skills/agents/chapter-editor.md` | "Chapter X 수정해줘" (기존 챕터 국소 수정) | 자동 |
| **flow-refiner** 📝 | `skills/agents/flow-refiner.md` | "flow 업데이트해줘" (flow.md diff 제안만) | 자동 |
| **citation-auditor** | `skills/agents/citation-auditor.md` | chapter 수정 후 자동 + 평가(v1/revised/final) 자동 체이닝 | 자동 |
| **gap-finder** | `skills/agents/gap-finder.md` | "gap 분석해줘" (분야의 빈틈 탐색) | 수동 |
| **methodology-advisor** | `skills/agents/methodology-advisor.md` | "방법론 추천/검증해줘" (empirical 프로젝트 전용) | 수동 |
| **peer-reviewer** | `skills/agents/peer-reviewer.md` | "리뷰 체크/답변 도와줘" (Iconoclast 페르소나 ambition ≥ critical 시 자동 추가) | 수동 |

### 에이전트 호출 방법

서브 에이전트를 호출할 때는 Agent 도구를 사용하세요:

1. 해당 에이전트 파일(`skills/agents/{agent-name}.md`)을 Read 도구로 읽기
2. 에이전트 프롬프트에 다음을 포함:
   - 에이전트 파일의 전체 내용 (노하우 + 출력 형식)
   - 현재 프로젝트의 flow.md 내용
   - 처리할 대상 파일 경로
3. Agent 도구로 실행 (독립된 컨텍스트에서 작업)
4. 결과를 지정된 파일에 저장

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
mkdir -p projects/{PROJECT_NAME}/papers/collected
mkdir -p projects/{PROJECT_NAME}/papers/candidates
mkdir -p projects/{PROJECT_NAME}/papers/analyzed
mkdir -p projects/{PROJECT_NAME}/chapters
mkdir -p projects/{PROJECT_NAME}/final
```

### 단계 2b: evaluations 폴더 구조 생성

```bash
mkdir -p projects/{PROJECT_NAME}/evaluations/latest
mkdir -p projects/{PROJECT_NAME}/evaluations/archive
```

**경로 규약**:
- 모든 평가 산출물은 `projects/{PROJECT_NAME}/evaluations/latest/`에 저장 (덮어쓰기)
- 매 평가 실행 시 실행 직전의 latest/를 `archive/{NNN}-{YYYY-MM-DD}-{stage}/`로 스냅샷 복사
- 모든 하위 명령(`작업 시작해줘` 등)은 `evaluations/latest/`를 참조

### 단계 2c: .sync-state.json 초기화

```bash
python3 scripts/sync_state.py init {PROJECT_NAME}
```

이 파일은 flow.md·papers·chapters·evaluations·final 간 의존성을 추적하여 아티팩트가 조용히 어긋나는 것을 방지한다. 모든 주요 명령이 실행 전 `check`, 실행 후 `update-*`로 이 파일을 갱신한다.

### 단계 3: FLOW-TEMPLATE.md (가이드) 및 flow.md (작성용) 생성

projects/{PROJECT_NAME}/FLOW-TEMPLATE.md 와 projects/{PROJECT_NAME}/flow.md 두 파일을 생성하세요.

- **FLOW-TEMPLATE.md**: `skills/FLOW-TEMPLATE.md`의 내용을 복사. 줄글(prose) 작성 가이드.
- **flow.md**: **빈 파일** 또는 메타데이터 골격만 있는 파일로 생성:
  ```markdown
  # [과제명]

  과제명: 
  코스: 
  마감: YYYY-MM-DD
  분량: 
  인용 스타일: APA

  ---

  (여기에 줄글로 자유롭게 작성. 연구 질문과 핵심 주장은 반드시 한 문장씩 명시.
   작성법은 FLOW-TEMPLATE.md 참고. 완료 후 "평가해줘" 입력.)
  ```

**작성 방식**: 사용자가 자유 줄글(prose)로 작성하면 `평가해줘` 단계에서 claim-extractor가 문장 단위로 자동 분석합니다. 구조적 템플릿을 강요하지 않습니다.

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

`research_type`은 사용자가 flow.md 작성 후 첫 `"평가해줘"` 실행 시 자동 판별하여 채워진다:
- `"theoretical"` — 이론·개념 에세이 (기존 개념 비판, 새 프레임워크 제안)
- `"empirical"` — 경험 연구 (데이터 수집·분석·해석)

**추가 필드: intellectual_ambition** (Critical Mode 제어):

```json
{
  ...
  "research_type": "theoretical",
  "intellectual_ambition": "incremental"
}
```

3단계 값:
- `"incremental"` (기본): 분야 내 점진적 기여. critical-companion·critical-lens-evaluator·Iconoclast 비활성.
- `"critical"`: 비판적 시각을 능동적으로 지원. 위 3개 agent 자동 체이닝. Hedging 기본 엄격도 유지.
- `"paradigm-shifting"`: 대담한 주장을 방어. Hedging 관대, 비주류 인용 환영, 모든 critical agent 자동 호출.

**용도**: 
- `theoretical`인 프로젝트에서는 methodology-advisor 명령을 **명령 추천 목록에서 숨김**
- `critical` 이상인 프로젝트에서는 **critical-companion·critical-lens-evaluator·peer-reviewer Iconoclast**를 자동 체이닝
- `paradigm-shifting`인 프로젝트에서는 **peer-reviewer가 Iconoclast를 주 심사자로 승격**, 대담한 주장 penalty 완화

### 단계 5: 안내 메시지 출력

프로젝트 생성 완료 후 다음과 같이 사용자에게 안내하세요:

```
✅ 프로젝트 생성 완료: projects/{PROJECT_NAME}/

📁 구조:
   research-agent/
   └── projects/
       └── {PROJECT_NAME}/
           ├── flow.md                          (실제 작성용 — 이 파일을 수정)
           ├── FLOW-TEMPLATE.md                 (가이드 — 수정 금지)
           ├── critical-questions.md            (🎭 Critical Mode 활성 시 생성)
           ├── critical-questions.archive/      (🎭 질문·답변 버전 히스토리)
           ├── critical-commitments.md          (🎭 답변에서 추출한 actionable spec)
           ├── critical-commitments.archive/    (🎭 commitment 상태 히스토리)
           ├── evaluations/
           │   ├── latest/                      (최신 평가 산출물 — 명령이 참조)
           │   └── archive/                     (과거 평가 스냅샷)
           ├── papers/
           │   ├── candidates/                  (다운로드 후 처리 대기)
           │   ├── collected/                   (처리 완료된 PDF)
           │   ├── analyzed/                    (paper-analyst 분석 v1/v2/v3/[critical])
           │   └── archived/                    ("논문 제거해줘"로 이동된 PDF·분석)
           ├── chapters/
           │   └── archive/                     (덮어쓰기 직전 자동 스냅샷)
           ├── final/
           ├── .paper-metadata.json             (메타데이터 + intellectual_ambition)
           └── .sync-state.json                 (아티팩트 의존성·버전 추적)

👉 다음 단계:
   1. projects/{PROJECT_NAME}/flow.md 파일을 열어서 **자유 줄글로** 과제 방향 작성
      - 최소: 과제 메타데이터 + 연구 질문(RQ) 1문장 + 핵심 주장(Thesis) 1문장
      - 권장: 문제 설정 → 기존 비판 → 자기 제안 → 반론 → 함의를 에세이처럼 서술
      - 참고: FLOW-TEMPLATE.md (줄글 작성 가이드)
   2. "평가해줘" 입력 → claim-extractor(문장 단위 주장 추출) + 5축 냉정 평가 실행
      - 생성 파일: evaluation.md, work-plan.md, claim-extraction.md
   3. "작업 시작해줘" 입력 → work-plan.md의 HUNT 과제로 Consensus 자동 검색
   4. "새 논문 처리해줘" → PDF 처리 + paper-analyst 자동 분석
   5. "평가해줘" 재실행 → 점수 변화 확인 후 Stage 2(초안 작성) 진행
```

---

## 🎯 5축 평가 (flow-evaluator)

사용자가 "평가해줘", "flow 평가해줘", "원고 평가해줘", "5축 평가", "점수 매겨줘" 등을 말하면:

### 단계 0: Sync 선행 점검 (gate)

평가 시작 전 반드시 `scripts/sync_state.py check {PROJECT_NAME}` 실행:

- **Critical stale** (dangling citation, paper_removed 등) → 사용자에게 보고하고 해결 권유 후 진행 여부 확인
- **Minor stale** (flow drift 등) → 경고만 보고하고 자동 진행
- **Clean** → 바로 단계 1로

이 단계는 flow-evaluator.md의 Phase -1과 동일한 로직 (참고: `skills/agents/flow-evaluator.md` Phase -1).

별도로 "sync 확인해줘" 명령은 평가 없이 sync만 독립 점검할 때 사용.

### 단계 1: 평가 대상 판별

현재 프로젝트의 상태에 따라 자동으로 평가 단계를 판별:

- `flow.md`만 존재 + `chapters/` 비어있음 → **flow 단계 평가**
- `chapters/*.md` 존재 + `final/complete-draft.md` 없음 → **v1-draft 단계 평가**
- `final/complete-draft.md` 존재 + 수정 기록 있음 → **revised 단계 평가**
- 사용자가 "최종 평가" 명시 → **final 단계 평가**

사용자가 특정 파일을 지정한 경우 (예: "Chapter 2 평가해줘") 해당 파일만 평가.

### 단계 2: prose 여부 사전 판별 + claim-extractor 선행 호출

평가 대상이 `flow.md`이고 **줄글(prose) 형태**(체크박스·구조 테이블 없이 자연어 문장 위주)이면:

1. `skills/agents/claim-extractor.md` 파일을 읽는다
2. Agent 도구로 claim-extractor를 먼저 호출:
   - 전달: flow.md 전체 + papers/consensus-results.md + papers/analyzed/*.md + claim-extractor.md 지침
   - 수행: 문장 ID 부여 → 5종 분류 → 기존 pool 매칭 → UNMATCHED 건에 대한 HUNT 과제 생성
   - 저장: `projects/{PROJECT_NAME}/evaluations/latest/claim-extraction.md`

평가 대상이 이미 작성된 원고(`chapters/*.md`, `final/*.md`)인 경우에도 동일하게 claim-extractor를 선행 호출 (문장 단위 인용 누락 감사용).

### 단계 3: 🤖 flow-evaluator 오케스트레이터 호출 + 병렬 체이닝

#### 3-a. flow-evaluator 실행

1. `skills/agents/flow-evaluator.md` 파일을 읽는다
2. 다음을 수집하여 Agent 도구 prompt에 포함:
   - 평가 대상 파일 전체 내용
   - `flow.md` (기준 문서)
   - `claim-extraction.md` (단계 2 결과, prose flow인 경우)
   - `papers/consensus-results.md` (레퍼런스 pool)
   - `papers/analyzed/*.md` (논문 분석)
   - `papers/collected/` 파일 목록
   - 현재 평가 단계 (flow / v1-draft / revised / final)
   - **`critical-commitments.md`** (존재 시 — 커버리지를 축 4·6 점수에 반영)
3. Agent 도구로 flow-evaluator를 실행한다

#### 3-b. 병렬 체이닝 (자동) — 아래 에이전트들을 flow-evaluator와 동시 호출

**항상 병렬 호출**:
- **originality-evaluator** — 축 4 심층 → `originality-report.md`
- **concept-clarity-evaluator** — 축 5 심층 → `concept-clarity-report.md`

**Critical Mode 활성 시 추가** (`.paper-metadata.json`의 `intellectual_ambition ≥ critical`):
- **critical-lens-evaluator** — 축 6 심층 → `critical-lens-report.md`
- **critical-companion** — stage 마일스톤일 때 (아래 표 참조)

**평가 단계(stage)가 v1-draft/revised/final일 때 추가**:
- **citation-auditor** — PDF 원문 대조 accuracy 검증
  - v1-draft: chapters/*.md 중 **무작위 30% 샘플**
  - revised: **chapters/*.md 전량**
  - final: **전량 + 이전 archive 대비 new-error diff**

#### 3-c. stage 마일스톤 판별 (critical-companion 트리거)

다음 조건에서 critical-companion을 자동 호출:

| 조건 | 트리거 | critical-companion trigger 파라미터 |
|------|-------|----------------------------------|
| flow 단계 첫 평가 | 자동 | `initial` |
| Stage 1 리서치 완료 후 첫 평가 | 자동 | `post-research` |
| v1-draft 평가 | 자동 | `post-draft` |
| revised 평가 | 자동 | `post-revision` |
| final 직전 평가 | 자동 | `pre-final` |

stage 판별 논리는 flow-evaluator가 수행. 해당 trigger로 critical-companion을 별도 호출 (ambition ≥ critical일 때만).

#### 3-d. 모든 병렬 호출 동시 실행

위 에이전트들은 **상호 독립적**이므로 하나의 응답에서 여러 Agent 도구를 **병렬 호출**. flow-evaluator가 최종적으로 모든 결과를 종합하여 evaluation.md 생성.

### 단계 4: 결과 저장

flow-evaluator가 다음을 자동 수행 (상세 절차는 `skills/agents/flow-evaluator.md` 참조):

1. **Archive 스냅샷**: 기존 `evaluations/latest/`를 `evaluations/archive/{NNN}-{date}-{stage}/`로 자동 복사
2. **신규 산출물 저장** (모두 `evaluations/latest/` 하위):
   - `evaluation.md` — 5축 점수 + 감점 사유
   - `work-plan.md` — 작업 계획서 (REANALYZE + HUNT 체크박스 포함)
   - `claim-extraction.md` — 문장 단위 주장 테이블 (prose flow인 경우)
   - `originality-report.md` — 축 4 심층 (선택)
   - `concept-clarity-report.md` — 축 5 심층 (선택)
3. **Delta 추적**: 두 번째 이후 평가 시 `evaluation.md` 상단에 직전 archive 스냅샷 대비 축별 점수 변화 표 자동 삽입
4. **Sync 갱신**: `python3 scripts/sync_state.py update-evaluation {PROJECT_NAME}` 실행

### 단계 5: 사용자 보고

```
🎯 5축 평가 완료

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 종합: XX/500 (평균 XX/100)
평가 단계: [flow / v1-draft / revised / final]
심사 판정 (가상): [Reject / Major / Minor / Accept]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| 축 | 이름 | 점수 | 등급 |
|---|------|------|------|
| 1 | 레퍼런스 충실도 | XX/100 | X |
| 2 | 논리 전개 완성도 | XX/100 | X |
| 3 | 반박/강화 논리 | XX/100 | X |
| 4 | 독창성·기여도 | XX/100 | X |
| 5 | 구성개념 정의 정밀도 | XX/100 | X |

🔴 P1-Critical (축 간 상호작용 문제): N건
🟡 P2-High: N건
🟢 P3-Medium: N건

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 작업 계획서: work-plan.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 Stage 1 (리서치): {N}개 작업 — 예상 회복 +{X}
✍️ Stage 2 (1차 작성): {N}개 작업 — 예상 회복 +{X}
🔧 Stage 3 (수정): {N}개 작업 — 예상 회복 +{X}
✅ Stage 4 (최종): {N}개 작업 — 예상 회복 +{X}

💾 저장 (모두 evaluations/latest/ 하위):
   ✓ evaluations/latest/evaluation.md
   ✓ evaluations/latest/work-plan.md
   ✓ evaluations/latest/claim-extraction.md (prose flow)
   ✓ evaluations/latest/originality-report.md (축 4 심층)
   ✓ evaluations/latest/concept-clarity-report.md (축 5 심층)
   📦 이전 평가 → evaluations/archive/{NNN}-{date}-{stage}/ 자동 스냅샷

👉 다음 단계:
   1. work-plan.md 검토
   2. Stage 1부터 순차 진행:
      - "작업 시작해줘" → REANALYZE(기존 PDF 재분석) + HUNT(신규 검색) 자동 실행
      - "새 논문 처리해줘" → PDF 처리
      - "초안 작성해줘" → Stage 2
      - "Chapter X 수정해줘" → Stage 3
   3. Stage 1 후엔 "레퍼런스 점검해줘"(경량, 축 1만) 권장
   4. 전체 5축 재평가는 flow 업데이트/초안/수정 후에만 실효적
```

### 단계 6: 반복 평가 규칙

- **각 Stage 완료 시 재평가 권장 (차별화)**:
  - Stage 1 (리서치) 후 → `"레퍼런스 점검해줘"` (축 1 경량)
  - Stage 2 (초안) 후 → `"평가해줘"` (전체 5축)
  - Stage 3 (수정) 후 → `"평가해줘"` (전체 5축)
  - Stage 4 (최종) 전 → `"평가해줘"` (최종 5축)
- **이전 평가 대비 delta 추적**: 두 번째 이후 평가 시, `evaluation.md`에 이전 점수 대비 변화(+X, −X)를 함께 표시
- **목표 달성 확인**: 각 축이 90점 이상이면 🟢, 70-89점이면 🟡, 70점 미만이면 🔴

---

## 논문 처리

사용자가 "새 논문 처리해줘", "논문 분석해줘", "candidates 처리해줘" 등을 말하면:

### 단계 1: 현재 프로젝트 확인

현재 작업 중인 프로젝트를 확인하세요. 사용자가 명시하지 않았다면 가장 최근에 수정된 프로젝트를 사용하세요.

### 단계 2: candidates 폴더 스캔

```bash
ls -la projects/{PROJECT_NAME}/papers/candidates/*.pdf
```

### 단계 3: 각 PDF 파일 처리

candidates 폴더에 있는 각 PDF에 대해:

1. **메타데이터 추출**:
```bash
python scripts/extract_metadata.py projects/{PROJECT_NAME}/papers/candidates/{FILENAME}.pdf
```

2. **결과를 .paper-metadata.json에 추가**:
   - 파일명
   - 제목 (추출된 값 또는 파일명)
   - 저자
   - 페이지 수
   - 추가 날짜

3. **PDF를 collected/로 이동**:
```bash
mv projects/{PROJECT_NAME}/papers/candidates/{FILENAME}.pdf projects/{PROJECT_NAME}/papers/collected/
```

### 단계 4: 🤖 paper-analyst 에이전트 자동 호출

각 PDF 처리 후 **자동으로** paper-analyst 서브 에이전트를 호출하여 심층 분석을 수행한다.

1. `skills/agents/paper-analyst.md` 파일을 읽는다
2. 현재 프로젝트의 `flow.md`를 읽는다
3. 각 PDF에 대해 Agent 도구로 paper-analyst를 실행한다:
   - 에이전트에게 전달: PDF 파일 경로 + flow.md 내용 + paper-analyst.md의 전체 지침
   - 에이전트가 수행: 논문 읽기 → 3줄 요약, 핵심 기여, 한계, 관련성 점수, 활용 방안 분석
4. 분석 결과를 `papers/analyzed/{파일명}-analysis.md`에 저장한다

**여러 논문이 있을 경우 병렬로 에이전트를 호출**하여 효율적으로 처리한다.

### 단계 4b: Sync 상태 갱신

각 PDF 분석 완료 후 반드시 실행:

```bash
python3 scripts/sync_state.py update-paper {PROJECT_NAME} {파일명}.pdf
```

이는 `.sync-state.json`의 papers 엔트리에 pdf_hash, analyzed_version, analyzed_flow_hash_at, analyzed_updated_at을 기록한다. 재분석(Mode B)일 경우 analyzed_version이 자동으로 v2, v3... 순으로 증가한다.

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

---

## Consensus 검색 (작업 시작) — work-plan.md 기반 자동 실행

사용자가 "작업 시작해줘", "논문 검색해줘", "HUNT 실행" 등을 말하면:

### 단계 1: 선행 조건 확인

1. `projects/{PROJECT_NAME}/evaluations/latest/work-plan.md` 존재 여부 확인
   - 없으면: "먼저 `평가해줘`를 실행하여 work-plan.md를 생성하세요"로 안내 후 중단
2. work-plan.md의 `Stage 1: 논문 리서치` 섹션에서 **두 종류 작업**을 파싱:
   - `[REANALYZE-NNN]` 블록 — 기존 PDF 재분석 과제
   - `[HUNT-NNN]` 블록 — Consensus 신규 검색 과제
3. 미완료 체크박스(`- [ ]`)만 수집

### 단계 2a: REANALYZE 작업 먼저 실행 (내부 재활용 우선)

각 미완료 REANALYZE 과제마다:

1. 해당 논문의 `papers/analyzed/{파일명}-analysis.md` 읽기 (v1 존재 확인)
2. `skills/agents/paper-analyst.md` 읽기
3. Agent 도구로 paper-analyst를 **Mode B**로 호출:
   - 전달: PDF 경로 + 현재 flow.md + 기존 analyzed/*.md + 재분석 각도 지시
   - 수행: PDF 재스캔 → analyzed/*.md에 `## [v2 — {date}] 재분석: {각도}` append
4. `python3 scripts/sync_state.py update-paper {PROJECT} {파일명}` 실행
5. `claim-extraction.md`에서 해당 문장의 분류를 UNMATCHED-INTERNAL → MATCHED로 전환
6. `work-plan.md`의 REANALYZE 체크박스를 `- [x]`로 갱신

### 단계 2b: HUNT 과제를 Consensus MCP에 투입

각 미완료 HUNT 과제마다:

1. **검색 키워드 리스트를 순차 실행**:
   - 각 키워드에 대해 `mcp__consensus__search` 호출
   - **MCP 지시에 따라 배치당 최대 3개 쿼리 병렬 실행** 후 대기 (rate limit 회피)
   - Rate limit 에러 시 30초 대기 후 재시도

2. **결과 누적**:
   - 각 HUNT 결과를 `papers/consensus-results.md`에 **누적 저장** (기존 내용 유지, 새 섹션 추가)
   - 각 결과에 출처 HUNT ID 태그 (예: `## [HUNT-001] S004 — EF 측정 혼입 요인`)

3. **claim-extraction.md 매칭 상태 갱신** (`evaluations/latest/claim-extraction.md`):
   - 해당 문장의 MATCHED 상태를 ✅로 변경
   - 찾은 대표 논문 2-3편을 인용 후보로 기록

4. **work-plan.md 진척 갱신** (`evaluations/latest/work-plan.md`):
   - 완료된 HUNT는 `- [x]` 체크
   - 찾은 논문이 기대 프로필에 못 미치면 `⚠️ 재검색 필요` 주석 추가

### 단계 3: 결과 보고

각 HUNT 결과는 `papers/consensus-results.md`에 `[HUNT-NNN]` 태그로 누적 저장된다 (단계 2b에서 이미 수행). 각 논문은 클릭 가능한 마크다운 링크 (`[제목](URL)`) 형식으로 포함.

화면 요약 예시:
```
🔍 HUNT 실행 완료

📊 요약
   🔄 REANALYZE: {N}개 완료 ({M}편 PDF 재분석, v2 append)
   🔍 HUNT: {K}개 완료 ({L}편 신규 후보 확보)
   ⚠️  재검색 권장: {R}개 (기대 프로필 미달)

📄 papers/consensus-results.md에 {L}편 추가
🔄 evaluations/latest/claim-extraction.md 매칭 갱신: {T}건

👉 다음 단계:
   1. consensus-results.md 링크에서 필요한 논문 PDF 다운로드
   2. papers/candidates/에 저장 → "새 논문 처리해줘"
```

### 단계 4: 다음 단계 권장 (현실적 분기)

HUNT 전량 완료 후, 사용자에게 다음 두 옵션을 제시:

```
📚 Stage 1 리서치 완료

축 1 점수는 새 논문 확보로 상승할 것으로 기대되지만, 축 2·3·4·5는 flow.md 텍스트가
그대로이므로 전체 5축을 재평가해도 변화는 미미합니다.

다음 중 선택:

  [A] "레퍼런스 점검해줘"  → 축 1만 빠르게 재평가 (권장, 가벼움)
  [B] "flow 업데이트해줘"  → 새 논문 반영하여 flow.md 보강 제안
                            (이 후 "평가해줘" 시 축 3·4도 유의미하게 움직임)
  [C] "초안 작성해줘"      → Stage 2로 바로 진입 (flow가 이미 충분하다면)
```

---

## 🔍 레퍼런스 점검 (축 1 경량 재평가)

사용자가 "레퍼런스 점검해줘", "축 1 재평가", "reference check" 등을 말하면:

### 단계 1: 축 1 전용 평가

1. `evaluations/latest/claim-extraction.md`의 MATCHED/UNMATCHED 현황 재계산
2. **PDF 샘플링 accuracy 검증** (신규):
   - MATCHED 건 중 **2-3개를 무작위 샘플링**
   - 각 샘플에 대해 `papers/collected/{파일명}.pdf`를 Read로 열어 원문 확인
   - analyzed/*.md의 섹션별 인용 다발이 원문과 일치하는지 대조
   - 불일치 발견 시 해당 건을 `⚠️ 재검증 필요`로 플래그 + paper-analyst Mode B 재실행 권장
3. 새 논문을 반영한 **축 1의 4개 하위 기준만** 재채점 (Coverage, Accuracy, Authority, Balance)

**샘플링 근거**: 초안 작성 전 단계이므로 전량 PDF 대조는 과도. 2-3편 랜덤 샘플로 paper-analyst 요약의 신뢰도만 spot-check. 전량 검증은 Stage 3 수정 시 citation-auditor가 담당.

### 단계 2: 저장 (경량, archive 스냅샷 없음)

- `evaluations/latest/evaluation.md`의 축 1 점수 블록만 갱신
- `evaluations/latest/work-plan.md`의 Stage 1 섹션 체크 상태 반영
- 축 2-5 점수는 **변경하지 않음**

### 단계 3: 보고

```
🔍 레퍼런스 점검 완료 (축 1 전용)

축 1 레퍼런스 충실도: 52 → 84 (+32 🟢)
  ├─ 1-1 Coverage: 40 → 92 (+52)
  ├─ 1-2 Accuracy: 65 → 88 (+23)
  ├─ 1-3 Authority: 60 → 82 (+22)
  └─ 1-4 Balance: 43 → 74 (+31)

⚠️ 잔존 이슈:
  - [HUNT-007] S055에 대한 매칭 논문이 기대 프로필 미달 → 재검색 권장
  - [HUNT-012] S089의 MATCHED 논문 3편 중 1편이 원문 확인 결과 over-claim

👉 다음 단계:
   - 잔존 이슈 해소 후 "flow 업데이트해줘"
   - 또는 "초안 작성해줘"로 Stage 2 진입
   - 축 2-5 전체 재평가는 Stage 2 초안 완료 후 권장
```

---

## 📝 flow 업데이트 (새 논문 반영 보강)

사용자가 "flow 업데이트해줘", "flow 보강", "새 논문 반영해서 flow 고쳐줘" 등을 말하면:

### 단계 1: 🤖 flow-refiner 에이전트 호출

1. `skills/agents/flow-refiner.md` 파일을 읽는다
2. Agent 도구로 flow-refiner를 호출:
   - 전달: flow.md + `.sync-state.json` + 신규 analyzed/*.md + evaluations/latest/evaluation.md + claim-extraction.md
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

---

## 초안 작성

사용자가 "초안 작성해줘", "draft 생성", "글 써줘" 등을 말하면:

### 단계 0: Commitment 추출 Prehook (Critical Mode 활성 시)

`.paper-metadata.json`의 `intellectual_ambition ≥ critical`이고 `critical-questions.md`가 존재하면:

1. `critical-questions.md`의 mtime이 `critical-commitments.md`의 mtime보다 **최신**인지 확인
2. 최신이면 (사용자가 답변을 새로 작성했다는 의미) → `"답변 반영해줘"` 명령 자동 실행 (critical-companion Phase 6만):
   ```
   🔄 critical-questions.md 변경 감지 — commitment 자동 추출 실행
   ```
3. `critical-commitments.md` 갱신 완료 후 단계 1로 진행

이 prehook은 **답변이 실제 결과물에 반영되도록 보장**하는 핵심. 사용자가 답변 작성 후 별도 명령 없이도 writing 에이전트가 최신 commitment를 읽게 됨.

### 단계 1: 준비 확인

1. **현재 프로젝트의 flow.md 읽기**
2. **현재 프로젝트의 .paper-metadata.json 읽기**
3. **papers/collected/ 폴더의 논문 목록 확인**
4. **papers/analyzed/ 폴더의 분석 리포트 확인** (paper-analyst 결과)
5. **`critical-commitments.md` 읽기** (존재 시 — writing-architect가 spec으로 사용)

### 단계 1b: 기존 chapters 자동 스냅샷 (데이터 손실 방지)

`chapters/` 폴더가 **이미 비어있지 않다면** 이번 "초안 작성해줘"는 **전면 재작성(re-draft)**을 의미. 덮어쓰기 전 현재 상태를 archive에 보존:

```bash
python3 scripts/sync_state.py snapshot-chapters {PROJECT_NAME} pre-redraft
```

결과: `projects/{PROJECT_NAME}/chapters/archive/{NNN}-{date}-pre-redraft/`에 전체 chapters 파일 복사. 구 초안을 영영 잃지 않음 — 필요 시 복구 가능.

`chapters/`가 비어있으면 이 단계 스킵.

### 단계 2: 🤖 writing-architect 에이전트 호출 — Phase 1: 논증 구조 설계

1. `skills/agents/writing-architect.md` 파일을 읽는다
2. Agent 도구로 writing-architect를 실행한다:
   - 전달: flow.md + 모든 analyzed/*.md 파일 + writing-architect.md 지침
   - 수행: 각 섹션의 논증 구조(주장→근거→반박→재반박) 설계
3. 설계된 구조를 **사용자에게 보여주고 확인을 받는다**:

```
✍️ 논증 구조 설계 완료

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 Section 1: Introduction (4 문단)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
문단 1: [연구 배경 — 넓은 맥락 설정]
  └── 근거: Smith (2023), Lee (2024)
문단 2: [문제 제기 — 기존 접근의 한계]
  └── 근거: Park (2022)
문단 3: [연구 Gap — 왜 이 연구가 필요한지]
  └── 근거: gap-analysis 결과 활용
문단 4: [연구 목적 — 본 연구의 방향]

[다른 섹션도 같은 형식...]

👉 이 구조로 진행할까요? 수정이 필요하면 말씀해주세요.
```

4. **사용자가 승인하면** Phase 2로 진행
5. **수정 요청 시** 구조를 수정하고 다시 확인

### 단계 3: 🤖 writing-architect 에이전트 — Phase 2: 초안 작성

사용자 승인 후 writing-architect 에이전트가 구조에 따라 초안을 작성한다:

1. 각 섹션별로 순차 작성 (Topic Sentence First → Evidence → Analysis → Transition)
2. 종합(Synthesis) 위주 서술 (논문별 요약 나열 금지)
3. 인용 강도를 근거 수준에 맞게 조절 (suggests/indicates/demonstrates)

### 단계 4: 파일 저장

각 섹션을 개별 파일로 저장:

```bash
projects/{PROJECT_NAME}/chapters/01-introduction.md
projects/{PROJECT_NAME}/chapters/02-background.md
projects/{PROJECT_NAME}/chapters/03-methodology.md
projects/{PROJECT_NAME}/chapters/04-analysis.md
projects/{PROJECT_NAME}/chapters/05-conclusion.md
```

통합본도 생성:
```bash
projects/{PROJECT_NAME}/final/complete-draft.md
```

### 단계 5: DOCX 생성

docx skill을 사용하여 Word 문서 생성:
```bash
projects/{PROJECT_NAME}/final/complete-draft.docx
```

### 단계 6: 결과 보고

```
✅ 초안 작성 완료!

📊 통계:
   - 총 단어 수: 3,245 words
   - 챕터: 5개
   - 총 인용: 18개
   - 사용된 논문: 8개

📁 생성된 파일:
   ✓ chapters/01-introduction.md (487 words)
   ✓ chapters/02-background.md (1,245 words)
   ✓ chapters/03-methodology.md (987 words)
   ✓ chapters/04-analysis.md (750 words)
   ✓ chapters/05-conclusion.md (526 words)
   ✓ final/complete-draft.md (전체 통합본)
   ✓ final/complete-draft.docx (Word 문서)

👉 다음 단계:
   챕터를 수정하려면:
   "Chapter 2 수정해줘: [구체적인 수정 내용]"
```

---

## 챕터 수정 + 자동 일관성 체크

사용자가 "Chapter X 수정해줘: [내용]" 또는 "X장 수정: [내용]" 등을 말하면:

### 단계 -1: Commitment 추출 Prehook (Critical Mode 활성 시)

`intellectual_ambition ≥ critical`이고 `critical-questions.md` mtime > `critical-commitments.md` mtime이면:
- `"답변 반영해줘"` 자동 실행 → critical-commitments.md 갱신
- 사용자에게 `🔄 답변에서 commitment 추출 완료` 알림

### 단계 0: 수정 전 단일 챕터 자동 스냅샷

chapter-editor 호출 전에 대상 챕터의 현재 상태를 archive에 보존:

```bash
python3 scripts/sync_state.py snapshot-chapters {PROJECT_NAME} ch{X}-edit 0{X}-{name}.md
```

결과: `chapters/archive/{NNN}-{date}-ch{X}-edit/0{X}-{name}.md`로 스냅샷. 수정 실패·롤백·비교 목적으로 활용 가능.

### 단계 1: 🤖 chapter-editor 에이전트 호출

1. `skills/agents/chapter-editor.md` 파일을 읽는다
2. Agent 도구로 chapter-editor를 호출:
   - 전달: 대상 챕터 경로 + 사용자 수정 지시 + flow.md + 관련 analyzed/*.md + chapter-editor.md 지침
   - 수행: Phase 1 지시 해석 → Phase 2 재료 수집 → Phase 3 수정 적용 → Phase 4 일관성 자동 체크
3. 에이전트가 수정된 챕터 파일을 저장

### 단계 2: citation-auditor 자동 체이닝 + Sync 갱신

chapter-editor Phase 5에서 citation-auditor를 자동 호출하며, Phase 6에서 `sync_state.py update-chapter`를 실행. SKILL.md에서는 이를 중복 기술하지 않고 chapter-editor에 위임.

추가로 SKILL.md가 보장할 것:
- chapter-editor 완료 후 반환된 결과가 citation-auditor 감사 리포트를 포함하는지 확인
- sync 갱신 완료 로그 확인

### 단계 3: 통합 결과 보고

```
✅ Chapter {X} 수정 완료

📝 변경사항:
   - [변경 내용 요약]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 자동 일관성 체크 결과:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Flow 목표 달성도: 100%
✅ 챕터 간 연결: 자연스러움
✅ 중복 내용: 없음

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 인용 감사 결과 (citation-auditor):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 인용 요약: 총 {N}개
   ✅ 정확: {N}개
   ⚠️ 수정 필요: {N}개
   ❌ 검증 불가: {N}개

🔴 즉시 수정 필요:
   - Ch{X} p.{Y}: "Smith는 X를 증명" → 원문은 상관관계만 보고
     💡 수정: "Smith (2023) found a correlation between..."

🟡 권장:
   - APA 형식 오류 {N}건
   - Section {N} 인용 부족 (현재 {N}개, 권장 {N}개 이상)

💯 전체 평가: A (94/100)
```

---

## Gap 분석 (수동 호출)

사용자가 "gap 분석해줘", "연구 gap 찾아줘", "뭐가 안 다뤄졌어?" 등을 말하면:

### 단계 1: 🤖 gap-finder 에이전트 호출

1. `skills/agents/gap-finder.md` 파일을 읽는다
2. 현재 프로젝트의 `flow.md`와 `papers/analyzed/` 전체를 읽는다
3. Agent 도구로 gap-finder를 실행한다:
   - 전달: flow.md + 모든 analyzed/*.md + gap-finder.md 지침
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

---

## 방법론 추천/검증 (수동 호출 + empirical 자동 제안)

### 자동 제안 트리거

`.paper-metadata.json`의 `research_type == "empirical"`일 때 다음 시점에 **시스템이 능동적으로 methodology-advisor 사용을 제안**:

| 시점 | 제안 메시지 |
|------|-----------|
| 프로젝트 생성 직후 flow.md 저장 시 | "empirical 프로젝트로 감지됨. 방법론 추천을 받아보시겠습니까? → `방법론 추천해줘`" |
| 첫 `"평가해줘"` 실행 시 | "이 프로젝트는 empirical이지만 방법론이 flow.md에 아직 명시되지 않음. `방법론 추천해줘` 권장" |
| `"작업 시작해줘"` 실행 시 | "Stage 1 리서치 전 방법론 방향 확정 권장. `방법론 추천해줘` 또는 `방법론 검증해줘`" |
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
   - Critic: flow.md + 해당 챕터(chapters/03-methodology.md) 전달 → 타당성/신뢰성/윤리 검증
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

---

## 🔄 Sync 확인 (sync 확인해줘)

사용자가 "sync 확인해줘", "sync 점검", "상태 확인해줘", "stale 체크" 등을 말하면:

> **참고**: "평가해줘" 명령은 단계 0에서 동일한 sync 체크를 자동 실행. 이 명령은 평가 없이 **sync만 독립 점검**할 때 사용.

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
   → "논문 재분석해줘" 후 "평가해줘"

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
6. "평가해줘" (전체 재평가 마지막)                       — P3

⚠️ 이 순서로 진행하지 않으면 후속 단계에서 같은 stale이 다시 감지됩니다
   (예: Chapter 수정 전에 평가해도 여전히 구버전 기반 경고).
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
  - claim-extraction.md에서 관련 MATCHED 3건이 UNMATCHED-EXTERNAL로 전환
  - Chapter 2, Chapter 4에 dangling citation 가능성 (사후 citation-auditor로 확인 권장)

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
3. `claim-extraction.md`에서 해당 논문을 인용하던 MATCHED 문장을 UNMATCHED-EXTERNAL 또는 UNMATCHED-INTERNAL(다른 PDF로 대체 가능 여부 판별)로 재분류

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

이후 "평가해줘" 실행하여 축 1 점수 변화 확인.
```

---

## 📦 최종 통합 (최종 통합해줘)

사용자가 "최종 통합해줘", "final 재빌드", "docx 재생성", "chapter 합쳐줘" 등을 말하면:

### 단계 1: 전제 조건 확인

1. `chapters/*.md` 파일이 존재하는지 확인 — 없으면 "먼저 초안 작성해줘"로 안내
2. `scripts/sync_state.py check`로 챕터 간 inconsistency 사전 탐지

### 단계 2: chapters 병합 → complete-draft.md

`chapters/`의 모든 `*.md` 파일을 번호순으로 병합하여 `final/complete-draft.md` 생성:

```bash
cat projects/{PROJECT_NAME}/chapters/*.md \
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
   - "평가해줘" → 최종 5축 평가
```

---

## 🔄 논문 재분석 (논문 재분석해줘)

사용자가 "논문 재분석해줘", "paper 재분석", "Zelazo 논문 다시 분석", "모든 논문 재스캔" 등을 말하면:

### 단계 1: 대상 선정

사용자 입력에 따라:
- "{파일명} 논문 재분석해줘" → 지정된 논문만
- "논문 재분석해줘" (지정 없음) → `work-plan.md`의 `[REANALYZE-NNN]` 블록 또는 `.sync-state.json`의 `analyzed_flow_hash_at` != 현재 flow_hash인 모든 논문

### 단계 2: paper-analyst Mode B 호출

각 대상 PDF마다:

1. `skills/agents/paper-analyst.md` 읽기
2. Agent 도구로 paper-analyst를 **Mode B**로 호출:
   - 전달: PDF 경로 + **현재 flow.md** + 기존 analyzed/*.md + 재분석 각도 (work-plan.md의 REANALYZE 블록이 있으면 그 지시, 없으면 flow 변경 전반)
   - 수행: PDF 재스캔 → analyzed/*.md에 `## [v{N+1}] 재분석: {각도}` append (v1 내용은 절대 수정/삭제 금지)
3. `python3 scripts/sync_state.py update-paper {PROJECT} {파일명}` 실행

### 단계 3: claim-extraction 반영

`claim-extraction.md`에서 UNMATCHED-INTERNAL이었던 문장들을 재확인:
- 재분석 결과 새 v{N+1}에 해당 주장이 커버되었으면 → MATCHED로 전환
- 여전히 커버 못하면 → UNMATCHED-EXTERNAL로 재분류 (HUNT 필요)

### 단계 4: 챕터 sync 경고

이미 `chapters/*.md`가 존재하고 `.sync-state.json`의 `chapters[x].papers_used[파일명]` 버전이 구버전이면:

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

🔄 claim-extraction.md 반영:
   - UNMATCHED-INTERNAL {N}건 → MATCHED 전환
   - 잔존 UNMATCHED-INTERNAL: {N}건 (추가 재분석 또는 HUNT 필요)

⚠️ 챕터 sync 경고: {N}건 (위 참조)

👉 다음 단계:
   - "Chapter X 수정해줘: 새 분석 반영"
   - 모든 sync 확인: "sync 확인해줘"
   - 평가 갱신: "평가해줘"
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
  🎭 critical-lens-evaluator (축 6 추가)
  🤔 critical-companion (Stage 마일스톤마다 Socratic 질문)
  👹 peer-reviewer Reviewer 4 (Iconoclast)
  🔍 paper-analyst Mode C (핵심 논문 비판적 읽기)

비활성화 (incremental로 되돌리려면):
  "비판 모드 incremental로 설정해줘"

다음 단계:
  "평가해줘"로 Critical Mode 포함 전체 평가 실행
```

### 자동 제안 트리거

첫 `"평가해줘"` 실행 시, intellectual_ambition이 `incremental`이고 flow.md에서 critical 신호 ≥ 3개 감지되면 flow-evaluator가 사용자에게 자동 제안:

```
💡 제안: 이 프로젝트는 "critical" 성향이 강합니다.
   intellectual_ambition을 critical로 변경하면 Critical Mode가 활성화되어
   새로운 관점·비판적 시각 지원이 강화됩니다.
   
   변경: "비판 모드 critical로 설정해줘"
   현 상태 유지: 그대로 평가 진행
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
   - 입력: 현재 critical-questions.md + chapters/*.md (반영 상태 판정용) + 기존 critical-commitments.md
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
  3. 전체 평가: "평가해줘"
```

**이 명령의 가치**: 사용자가 답변만 쓰고 끝내는 것이 아니라, **답변이 시스템에 actionable하게 등록되었음을 즉시 확인**. writing 작업 전에 commitment 추출을 보장.

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
   - 전달: flow.md + chapters/* (있으면) + evaluations/latest/evaluation.md + 이전 critical-questions.md + intellectual_ambition
   - 수행: Stage 판별 → 카테고리별 질문 생성 → 이전 답변과 원고 정합성 점검 → 다음 버전 예고
3. 에이전트가 새 버전 `critical-questions.md` 저장, 이전은 archive로 이동

### 단계 4: 사용자 알림

```
📝 비판적 질문 v{N} 업데이트 완료

경로: projects/{PROJECT}/critical-questions.md
이전 버전: projects/{PROJECT}/critical-questions.archive/{NNN}-{trigger}.md

📊 요약:
   🆕 신규 질문: {M}개
   🔁 Carry-over: {K}개
   ⚠️ 정합성 경고: {L}건

⚠️ 중요: 시스템이 답변하지 않습니다. 직접 작성하세요.
    답변 작성이 새로운 관점의 발견 과정입니다.
    답변 후 "평가해줘" 재실행하면 critical-lens-evaluator가 반영합니다.

👉 다음 단계:
   1. critical-questions.md 열어 질문에 자기 언어로 답변
   2. 답변한 내용을 원고에 반영할지 결정
   3. "평가해줘" → 답변·원고 정합성 점검
```

---

## 🎭 비판적 시각 평가 (critical-lens-evaluator, 단독 호출)

사용자가 `"비판적 시각 평가해줘"`, `"critical lens 평가"`, `"paradigm 평가"` 등을 말하면:

### 단계 1: 선행 조건 확인

`.paper-metadata.json`의 `intellectual_ambition ≥ critical` 확인. `incremental`이면 다음 메시지 후 중단:
> "이 평가는 ambition이 critical 이상일 때만 의미 있습니다. `intellectual_ambition`을 변경하시겠습니까?"

### 단계 2: 🤖 critical-lens-evaluator 호출

1. `skills/agents/critical-lens-evaluator.md` 파일을 읽는다
2. Agent 도구로 실행:
   - 전달: flow.md 또는 초안 + critical-questions.md (있으면 답변 정합성 점검 핵심) + analyzed/*.md (Mode C 것 우선) + evaluations/latest/originality-report.md
   - 수행: C-1 Paradigm Mapping / C-2 Fault-line / C-3 Bold Defense / C-4 Minority Recovery 4축 평가 + critical-questions.md 답변-원고 정합성 검증
3. 결과를 `projects/{PROJECT_NAME}/evaluations/latest/critical-lens-report.md`에 저장

### 단계 3: 화면 보고

축별 점수 + critical-questions.md 정합성 요약 + 심사자 예상 공격 + 개선 권장 우선순위.

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

---

## 독창성 심층 평가 (축 4, 단독 호출)

사용자가 "독창성 평가해줘", "contribution 평가", "novelty 확인해줘" 등을 말하면:

1. `skills/agents/originality-evaluator.md` 파일을 읽는다
2. 현재 프로젝트의 평가 대상(flow.md 또는 초안) + `papers/analyzed/*.md` + `papers/consensus-results.md`를 전달하여 Agent 실행
3. 결과를 `projects/{PROJECT_NAME}/evaluations/latest/originality-report.md`에 저장

**주요 출력**: Novelty Delta Map (선행 연구 3편 대비 차별점 테이블) + "So What?" 명시 여부 + 심사자 예상 공격.

---

## 구성개념 정의 정밀도 심층 평가 (축 5, 단독 호출)

사용자가 "정의 정밀도 평가해줘", "개념 평가", "construct clarity" 등을 말하면:

1. `skills/agents/concept-clarity-evaluator.md` 파일을 읽는다
2. 현재 프로젝트의 평가 대상을 전달하여 Agent 실행
3. 결과를 `projects/{PROJECT_NAME}/evaluations/latest/concept-clarity-report.md`에 저장

**주요 출력**: 핵심 구성개념 정의 감사 테이블 + 의미 drift 탐지 + 범주/차원 선택 근거 감사.

---

## 전체 명령어 요약

| 명령어 | 동작 | 에이전트 | Stage |
|--------|------|----------|-------|
| `"[이름] 프로젝트 만들어줘"` | 프로젝트 생성 (+ .sync-state.json 초기화) | - | 0 |
| 🎯 `"평가해줘"` | **5축 냉정 평가 + 작업계획서** (sync 체크 → archive 스냅샷 → 평가) | 🤖 flow-evaluator (+ claim-extractor + originality + concept-clarity) | flow / v1 / revised / final |
| 🔍 `"레퍼런스 점검해줘"` | **축 1 경량 재평가** (빠름, archive 없음) | flow-evaluator (axis-1 mode) | Stage 1 직후 |
| 📝 `"flow 업데이트해줘"` | 새 논문 반영한 flow.md 보강 제안 | 🤖 flow-refiner | Stage 1 직후 |
| `"작업 시작해줘"` | work-plan.md REANALYZE 먼저 → HUNT → Consensus 자동 검색 | 🤖 paper-analyst (Mode B) + MCP | 1 리서치 |
| `"새 논문 처리해줘"` | PDF 처리 + 심층 분석 (v1) + sync 갱신 | 🤖 paper-analyst (Mode A, 자동) | 1 리서치 |
| 🔄 `"논문 재분석해줘"` | 기존 PDF를 새 flow 각도로 재스캔 (v2 append) | 🤖 paper-analyst (Mode B, 자동) | 모든 단계 |
| 🗑 `"논문 제거해줘: {파일}"` | 안전 archived 이동 + dangling citation 경고 | - | 모든 단계 |
| `"초안 작성해줘"` | 구조 설계 → 확인 → 초안 | 🤖 writing-architect (Mode A, 자동) | 2 1차작성 |
| `"Chapter X 수정해줘"` | 수정 + 일관성 + 인용 감사 + sync 갱신 | 🤖 chapter-editor + citation-auditor (자동 체이닝) | 3 수정 |
| 📦 `"최종 통합해줘"` | chapters 병합 + docx 재빌드 + sync 갱신 | - | 4 최종 |
| 🔄 `"sync 확인해줘"` | 아티팩트 간 동기화 상태 점검 + 해결 가이드 | sync_state.py | 모든 단계 |
| `"gap 분석해줘"` | 연구 Gap 탐색 | 🤖 gap-finder | 리서치 보조 |
| `"방법론 추천/검증해줘"` | 방법론 제안 또는 검증 | 🤖 methodology-advisor | 리서치/수정 보조 |
| `"리뷰 체크/답변 도와줘"` | 심사 시뮬레이션 또는 대응 | 🤖 peer-reviewer | 4 최종 |
| `"독창성 평가해줘"` | 축 4 심층 평가 (단독 호출) | 🤖 originality-evaluator | 모든 단계 |
| `"정의 정밀도 평가해줘"` | 축 5 심층 평가 (단독 호출) | 🤖 concept-clarity-evaluator | 모든 단계 |
| 🎭 `"비판적 시각 평가해줘"` | 비판적 시각·패러다임 평가 (ambition ≥ critical) | 🤖 critical-lens-evaluator | 모든 단계 |
| 🤔 `"질문 업데이트해줘"` | Socratic 질문 v+1 생성 + 정합성 점검 | 🤖 critical-companion | Stage 마일스톤 + 수동 |
| 🔍 `"비판적으로 분석해줘: {파일}"` | paper-analyst Mode C — hidden assumptions 등 | 🤖 paper-analyst (Mode C) | 리서치 보조 |

**주요 명령 실행 시 자동 sync 동작**:
- `"평가해줘"` / `"작업 시작해줘"` 등 주요 명령 **시작 시** → `sync_state.py check` → stale 이슈 사용자 보고 (중대 이슈 시 중단 옵션)
- 각 명령 **완료 후** → `sync_state.py update-*` → 해당 아티팩트 상태 기록

**권장 흐름 (줄글 prose flow 기준, sync 통합)**:
```
프로젝트 생성 → .sync-state.json 초기화 → flow.md 자유 줄글 작성

  → 🎯 평가해줘 (1차)
     ├── sync 체크 (초기 상태)
     ├── claim-extractor → INTERNAL / EXTERNAL 분류
     ├── flow-evaluator → evaluation.md (5축)
     ├── work-plan.md: 🔄 REANALYZE + 🔍 HUNT 체크박스
     └── archive/001-{date}-flow/

  → [Stage 1 리서치]
     ├── 작업 시작해줘
     │   ├── REANALYZE 먼저 (기존 PDF 재스캔 → analyzed/*.md v2 append)
     │   └── HUNT (Consensus 신규 검색)
     ├── (사용자) PDF 다운로드 → candidates/
     └── 새 논문 처리해줘 → paper-analyst Mode A + sync 갱신

  → 🔍 레퍼런스 점검해줘 (축 1 경량)

  → (선택) 📝 flow 업데이트해줘 → flow-refiner diff 제안

  → [Stage 2] 초안 작성해줘
     ├── writing-architect: analyzed/*.md 섹션별 인용 다발 우선 참조
     ├── 부족 시 on-demand PDF 직접 읽기
     └── sync 갱신 (chapters 각 파일)

  → 🎯 평가해줘 (2차) → archive/002-{date}-v1-draft/

  → [Stage 3] Chapter X 수정해줘 (반복)
     ├── citation-auditor PDF 대조 감사
     └── sync 갱신

  → 🎯 평가해줘 (3차) → archive/003-{date}-revised/

  → [Stage 4]
     ├── 📦 최종 통합해줘 (final/* 재빌드)
     ├── 리뷰 체크해줘 (peer-reviewer 시뮬레이션)
     └── 🎯 평가해줘 (최종) → archive/004-{date}-final/

언제든: 🔄 sync 확인해줘 / 🗑 논문 제거해줘 / 🔄 논문 재분석해줘
```

**핵심 변경점**:
- Stage 1 직후에는 **경량 "레퍼런스 점검"**만 권장 (축 1 외 다른 축은 flow.md 미변경이면 움직이지 않으므로 전체 평가는 낭비)
- 전체 5축 재평가는 **실질적 변화(flow 업데이트 or 초안 작성 or 수정) 이후**에만 실행
- 각 전체 평가마다 `archive/` 스냅샷이 자동 생성되어 delta 추적 가능
