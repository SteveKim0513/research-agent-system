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
| **1** | 논문 레퍼런스 충실도 | Coverage + Accuracy + Authority + Balance | **axis1-reference-scorer** |
| **2** | 논리 전개 완성도 | Argument chain + Transition + Thesis alignment + Scope closure | **axis2-logic-scorer** |
| **3** | 반박/강화 논리 | Steelman + Falsifiability + Limitations + Reviewer attack surface | **axis3-defense-scorer** |
| **4** | 독창성·기여도 | "So What?" + Novelty positioning + Contribution layer + Implications | **axis4-originality-scorer** |
| **5** | 구성개념 정의 정밀도 | Definition + Operationalization + Boundary + Categorical/Dimensional | **axis5-concept-scorer** |
| **6** | 비판 렌즈 (Critical Mode) | Paradigm Mapping + Fault-line + Bold Defense + Minority Recovery | **axis6-critical-scorer** |

**병렬 delta 오케스트레이션**: `evaluation-orchestrator`가 변경된 축만 병렬 디스패치. stale 판정은 `scripts/evaluation_delta.py`의 입력 해시 비교. 축 6은 Critical Mode 활성 시에만 포함. 감사(citation-auditor) · 구조 설계(writing-architect) · 심사 시뮬레이션(peer-reviewer)은 별개 명령으로 호출되며 채점 주체가 아님.

## 자동 재분석 규칙 (Stage-aware claim-extraction)

`평가해줘`, `초안 작성해줘`, `Chapter X 수정해줘`, `flow 업데이트해줘` 명령은 다음 조건에서 **자동으로 claim-extractor를 체이닝**한다 (사용자가 별도 명령 없이도 항상 최신 분석 유지):

| 명령 | 자동 재분석 조건 | 대상 | 출력 |
|------|----------------|-----|-----|
| `평가해줘` | 해당 stage의 원고 mtime > claim-extraction mtime | flow | `flow/claim-extraction-flow.md` |
| `평가해줘` (draft) | 어떤 chapter든 mtime > `chapters/claim-extraction-draft.md` mtime | chapters 통합 | `chapters/claim-extraction-draft.md` |
| `초안 작성해줘` | writing-architect Phase 2 완료 후 | chapters 전체 | `chapters/claim-extraction-draft.md` |
| `Chapter X 수정해줘` | chapter-editor 수정 후 | chapters 통합 | `chapters/claim-extraction-draft.md` |
| `flow 업데이트해줘` | flow-refiner 승인 반영 후 | flow | `flow/claim-extraction-flow.md` |

**자동 체이닝 직전 history snapshot 의무**:
- flow 수정: `sync_state.py snapshot-flow {P} {trigger}` — 이전 flow.md + claim-extraction-flow.md 쌍 보존
- chapter 수정: `sync_state.py snapshot-chapter {P} {trigger} {chapter}` — 해당 챕터 + 당시 claim-extraction-draft.md 쌍 보존

**HUNT·DRAFT ID 단일 발급**: claim-extractor는 UNMATCHED를 식별하고 PROPOSAL 라벨로 제안. evaluation-orchestrator/aggregator가 `work-plan.md`의 다음 HUNT-NNN·DRAFT-NNN 번호를 발급하고, claim-extraction 파일의 PROPOSAL 라벨을 확정 ID로 치환.

## 서브 에이전트 시스템

이 스킬은 **19개의 서브 에이전트**를 사용합니다. 각 에이전트의 상세 프롬프트와 노하우는 `skills/agents/` 폴더에 정의되어 있습니다. 에이전트를 호출할 때는 해당 파일의 전체 내용을 읽어서 Agent 도구의 prompt에 포함하세요.

**모델 라우팅 원칙**: 작업 성격에 따라 서브에이전트를 다른 모델로 실행하여 비용·속도 최적화. 평가·글쓰기는 opus, 분석·검증은 sonnet, 번역 같은 기계적 작업은 haiku. 각 에이전트 정의 파일의 frontmatter `model` 필드에 기본값 표기. Agent 도구 호출 시 `model` 파라미터로 오버라이드 가능.

| 에이전트 | 파일 | 호출 시점 | 방식 |
|----------|------|-----------|------|
| **evaluation-orchestrator** 🎯 | `skills/agents/evaluation-orchestrator.md` | "평가해줘" — delta 감지 + 병렬 디스패치 + aggregate | 자동 (평가 진입점) |
| **axis1-reference-scorer** | `skills/agents/axis1-reference-scorer.md` | 축 1 레퍼런스 충실도 (sonnet) | 자동 (orchestrator dispatch) |
| **axis2-logic-scorer** | `skills/agents/axis2-logic-scorer.md` | 축 2 논리 전개 완성도 (opus) | 자동 |
| **axis3-defense-scorer** | `skills/agents/axis3-defense-scorer.md` | 축 3 반박·강화 논리 (opus, steelman tag 논문) | 자동 |
| **axis4-originality-scorer** | `skills/agents/axis4-originality-scorer.md` | 축 4 독창성·기여도 (opus, delta tag 논문) | 자동 |
| **axis5-concept-scorer** | `skills/agents/axis5-concept-scorer.md` | 축 5 구성개념 정의 정밀도 (sonnet) | 자동 |
| **axis6-critical-scorer** 🎭 | `skills/agents/axis6-critical-scorer.md` | 축 6 비판적 시각 (opus, minority tag 논문, ambition ≥ critical) | 자동 |
| **claim-extractor** 📝 | `skills/agents/claim-extractor.md` | 줄글 flow.md 문장 주장 추출 (axis1 선행) | 자동 |
| **critical-companion** 🤔 | `skills/agents/critical-companion.md` | Socratic 질문 생성 (stage 마일스톤마다 자동) | 자동/수동 |
| **paper-processing-orchestrator** 📄 | `skills/agents/paper-processing-orchestrator.md` | "새 논문 처리해줘" — triage → tier 분배 → 병렬 dispatch (opus, 오케스트레이션만) | 자동 (논문 처리 진입점) |
| **paper-analyst** | `skills/agents/paper-analyst.md` | Tier별 Mode (A-triage haiku / A-tier1 opus + Critical / A-tier2 sonnet / A-tier3 sonnet-short / B 재분석 / C 비판적 읽기) | 자동 (orchestrator dispatch) |
| **writing-architect** | `skills/agents/writing-architect.md` | "초안 작성" (신규 챕터 창작 전용) | 자동 |
| **chapter-editor** ✏️ | `skills/agents/chapter-editor.md` | "Chapter X 수정해줘" (기존 챕터 국소 수정) | 자동 |
| **flow-refiner** 📝 | `skills/agents/flow-refiner.md` | "flow 업데이트해줘" (flow.md diff 제안만) | 자동 |
| **citation-auditor** | `skills/agents/citation-auditor.md` | chapter 수정 후 자동 + 평가(v1/revised/final) 자동 체이닝 | 자동 |
| **gap-finder** | `skills/agents/gap-finder.md` | "gap 분석해줘" (분야의 빈틈 탐색) | 수동 |
| **methodology-advisor** | `skills/agents/methodology-advisor.md` | "방법론 추천/검증해줘" (empirical 프로젝트 전용) | 수동 |
| **peer-reviewer** | `skills/agents/peer-reviewer.md` | "리뷰 체크/답변 도와줘" (Iconoclast 페르소나 ambition ≥ critical 시 자동 추가) | 수동 |
| **abstract-translator** 🌐 | `skills/agents/abstract-translator.md` | HUNT 결과/PDF abstract 한글 번역 (haiku 모델) | 자동 (HUNT 단계 2 내장) |

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
mkdir -p projects/{PROJECT_NAME}/flow
mkdir -p projects/{PROJECT_NAME}/chapters
mkdir -p projects/{PROJECT_NAME}/chapters/history
mkdir -p projects/{PROJECT_NAME}/final
mkdir -p projects/{PROJECT_NAME}/work-plan.archive
```

### 단계 2b: evaluations 폴더 구조 생성

```bash
mkdir -p projects/{PROJECT_NAME}/evaluations/latest
mkdir -p projects/{PROJECT_NAME}/evaluations/archive
```

**v2 경로 규약** (2026-04-23 리팩터 이후):
- **`flow/`**: flow.md, FLOW-TEMPLATE.md, claim-extraction-flow.md, history/
- **`chapters/`**: 실제 챕터 파일(`0N-*.md`), claim-extraction-draft.md (**통합 1개**), history/{chapter_id}/
- **`evaluations/latest/`**: evaluation.md + axis1~6-*.md만 (claim-extraction 파일은 여기 두지 않음)
- **`evaluations/archive/{NNN}/`**: 증분 스냅샷 + manifest.json (변경 없는 축은 이전 경로 참조)
- **`work-plan.md`**: **루트** 위치 (HUNT/DRAFT ID 단일 발급처)
- **`work-plan.archive/`**: 변경 시에만 스냅샷 (매 평가마다 복사 아님)

### 단계 2c: .sync-state.json 초기화

```bash
python3 scripts/sync_state.py init {PROJECT_NAME}
```

이 파일은 flow.md·papers·chapters·evaluations·final 간 의존성을 추적하여 아티팩트가 조용히 어긋나는 것을 방지한다. 모든 주요 명령이 실행 전 `check`, 실행 후 `update-*`로 이 파일을 갱신한다.

### 단계 3: FLOW-TEMPLATE.md (가이드) 및 flow.md (작성용) 생성

projects/{PROJECT_NAME}/flow/FLOW-TEMPLATE.md 와 projects/{PROJECT_NAME}/flow/flow.md 두 파일을 생성하세요.

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
           ├── flow/
           │   ├── flow.md                      (실제 작성용 — 이 파일을 수정)
           │   ├── FLOW-TEMPLATE.md             (가이드 — 수정 금지)
           │   ├── claim-extraction-flow.md     (flow 문장 단위 분석 — 자동 생성)
           │   └── history/                     (flow 수정 직전 쌍 보존)
           ├── chapters/
           │   ├── 0N-*.md                      (초안 각 섹션)
           │   ├── claim-extraction-draft.md    (전체 챕터 통합 분석 — 자동 생성)
           │   └── history/{chapter_id}/        (챕터별 수정 직전 쌍 보존)
           ├── work-plan.md                     (HUNT·DRAFT 단일 발급처, 루트)
           ├── work-plan.archive/                (변경 시에만 스냅샷)
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
           ├── final/
           ├── activity.log                     (모든 명령 자동 로그)
           ├── .paper-metadata.json             (메타데이터 + intellectual_ambition)
           └── .sync-state.json                 (아티팩트 의존성·버전 추적)

👉 다음 단계:
   1. projects/{PROJECT_NAME}/flow/flow.md 파일을 열어서 **자유 줄글로** 과제 방향 작성
      - 최소: 과제 메타데이터 + 연구 질문(RQ) 1문장 + 핵심 주장(Thesis) 1문장
      - 권장: 문제 설정 → 기존 비판 → 자기 제안 → 반론 → 함의를 에세이처럼 서술
      - 참고: FLOW-TEMPLATE.md (줄글 작성 가이드)
   2. "평가해줘" 입력 → claim-extractor(stage=flow, 문장 단위 주장 추출) + 6축 평가 실행
      - 생성 파일: evaluations/latest/evaluation.md + axis1~6-*.md, work-plan.md (루트), flow/claim-extraction-flow.md
   3. "작업 시작해줘" 입력 → work-plan.md의 HUNT 과제로 Consensus 자동 검색
   4. "새 논문 처리해줘" → PDF 처리 + paper-analyst 자동 분석
   5. "평가해줘" 재실행 → 점수 변화 확인 후 Stage 2(초안 작성) 진행
```

### 단계 6: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "프로젝트 생성" "stage=init" "target={PROJECT_NAME}" "result=created" "ambition=incremental"
```

---

## 🎯 6축 평가 (evaluation-orchestrator, 병렬 delta 아키텍처)

사용자가 "평가해줘", "flow 평가해줘", "원고 평가해줘", "점수 매겨줘" 등을 말하면:

**플래그 지원**:
- `평가해줘` — delta 모드 (변경된 축만 재계산, 기본)
- `평가해줘 --full` — 전체 6축 강제 재실행
- `평가해줘 axis3,4` — 명시 축만 실행 (쉼표 구분)

### 단계 0: Sync 선행 점검 (gate)

`python3 scripts/sync_state.py check {PROJECT_NAME}` 실행 — Critical stale 시 사용자 확인, Minor stale 시 경고만, Clean 시 진행.

### 단계 1: 평가 대상 판별 + stage 결정

- `flow.md`만 존재 → **flow** 단계
- `chapters/*.md` 존재 + `final/complete-draft.md` 없음 → **v1-draft**
- `final/complete-draft.md` 존재 + 수정 기록 → **revised**
- "최종 평가" 명시 → **final**

### 단계 2: Delta 감지

```bash
python3 scripts/evaluation_delta.py check {PROJECT_NAME}
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
기존 `evaluations/latest/`를 `evaluations/archive/{NNN}-{date}-{stage}/`로 복사. 이후 새 점수는 `latest/`에 덮어쓴다.

### 단계 4: claim-extractor 선행 호출 (자동 재분석)

**Stage 감지**: `chapters/`에 실제 챕터 파일이 있으면 `stage=draft`, 없으면 `stage=flow`.

Stage별로 다음 조건에서 **반드시** claim-extractor를 먼저 실행한다:

| Stage | 조건 | 호출 전 snapshot | 호출 | 출력 |
|-------|------|------------------|------|------|
| flow  | `flow/flow.md` mtime > `flow/claim-extraction-flow.md` mtime (또는 후자 부재) | `sync_state.py snapshot-flow {P} pre-claim-extract` | claim-extractor(stage=flow) | `flow/claim-extraction-flow.md` |
| draft | 어느 `chapters/*.md` mtime > `chapters/claim-extraction-draft.md` mtime (또는 후자 부재) | 변경된 각 챕터마다 `sync_state.py snapshot-chapter {P} pre-claim-extract {chapter}` | claim-extractor(stage=draft) | `chapters/claim-extraction-draft.md` |

이미 최신이면 스킵.

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

**Axis-input map (Stage `draft`)**:
- axis1: `chapters/*.md` + `chapters/claim-extraction-draft.md` + `papers/analyzed/*.md`
- axis2: `chapters/*.md`만
- axis3: `chapters/*.md` + `papers/analyzed/*.md` 중 `"steelman"`
- axis4: `chapters/*.md` + `papers/analyzed/*.md` 중 `"delta"`
- axis5: `chapters/*.md`만
- axis6: `chapters/*.md` + `critical-questions.md` + `critical-commitments.md` + `papers/analyzed/*.md` 중 `"minority"`

**stale_axes에 없는 축**은 이전 archive의 동명 파일(`axis{N}-*.md`)을 그대로 `latest/`에 유지(복사). 재계산 없음.

### 단계 6: 병렬 완료 대기

모든 dispatch한 축 워커의 응답을 수신한 뒤에만 단계 7로 진행. 부분 완료 상태에서 aggregator 실행 금지.

### 단계 7: Aggregator — evaluation.md 생성

```bash
python3 scripts/evaluation_aggregator.py {PROJECT_NAME}
```

이것이 `axis{1..6}-*.md` 점수 섹션을 파싱하여 `evaluation.md`(요약 + delta 표 + 심사 판정)를 자동 생성.

### 단계 8: citation-auditor 체이닝 (조건부)

stage가 `v1-draft/revised/final`이고 axis1이 stale이었다면 `citation-auditor`를 호출:
- v1-draft: chapters 무작위 30% 샘플
- revised: chapters 전량
- final: 전량 + archive 대비 new-error diff

### 단계 9: critical-companion (stage 마일스톤)

Critical Mode이고 해당 stage가 마일스톤이면 `critical-companion`을 별도 호출해 `critical-questions.md` v{N+1} 생성. 이전 답변과 현재 원고의 정합성 점검 포함.

| stage | trigger |
|-------|---------|
| flow 첫 평가 | `initial` |
| Stage 1 리서치 완료 후 | `post-research` |
| v1-draft | `post-draft` |
| revised | `post-revision` |
| final 직전 | `pre-final` |

### 단계 10: 캐시 갱신

평가가 완료된 축만 delta 캐시에 기록:

```bash
python3 scripts/evaluation_delta.py mark-done {PROJECT_NAME} axis2,axis3
```

### 단계 11: Sync 갱신

```bash
python3 scripts/sync_state.py update-evaluation {PROJECT_NAME}
```

### 단계 12: work-plan.md 갱신

각 축의 감점 사유에서 actionable을 뽑아 `work-plan.md`에 반영. 완료된 HUNT는 `[x]`로 체크.

### 단계 13: 사용자 보고

```
🎯 6축 평가 완료 (delta 모드, stale {N}/6)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 종합: XX/600 (평균 XX/100)
평가 단계: [flow / v1-draft / revised / final]
심사 판정: [Reject / Major / R&R / Accept]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| 축 | 이름 | 점수 | 이전 | Δ |
|---|------|------|------|---|
| 1 | 레퍼런스 충실도 | XX | XX | +X |
| 2 | 논리 전개 완성도 | XX | XX | +X |
| 3 | 반박·강화 논리 | XX | XX | +X |
| 4 | 독창성·기여도 | XX | XX | +X |
| 5 | 구성개념 정의 정밀도 | XX | XX | +X |
| 6 | 비판적 시각 | XX | XX | +X |

📂 축별 상세: axis1-reference.md ~ axis6-critical.md
📋 작업 계획: work-plan.md
⏱ 소요: {N}분 (재계산 {N}축, 캐시 {M}축)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 Stage 1 (리서치): {N}개 작업 — 예상 회복 +{X}
✍️ Stage 2 (1차 작성): {N}개 작업 — 예상 회복 +{X}
🔧 Stage 3 (수정): {N}개 작업 — 예상 회복 +{X}
✅ Stage 4 (최종): {N}개 작업 — 예상 회복 +{X}

💾 저장 결과:
   ✓ evaluations/latest/evaluation.md              (종합 요약·aggregator)
   ✓ evaluations/latest/axis1-reference.md         (축 1)
   ✓ evaluations/latest/axis2-logic.md             (축 2)
   ✓ evaluations/latest/axis3-defense.md           (축 3)
   ✓ evaluations/latest/axis4-originality.md       (축 4)
   ✓ evaluations/latest/axis5-concept.md           (축 5)
   ✓ evaluations/latest/axis6-critical.md          (축 6, Critical Mode 활성 시)
   ✓ work-plan.md                                   (루트, HUNT·DRAFT ID 단일 발급처)
   ✓ flow/claim-extraction-flow.md                  (stage=flow 시)
   ✓ chapters/claim-extraction-draft.md             (stage=draft 시)
   📦 이전 평가 → evaluations/archive/{NNN}-{date}-{stage}/ 증분 스냅샷 (manifest.json)
   📦 work-plan 변경 시 → work-plan.archive/{NNN}-{date}-{stage}.md

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

### 단계 7: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "평가 완료" "stage={flow|v1-draft|revised|final}" "target={대상 파일}" "result={score}/500 ({delta})" "ref=ref:eval-{NNN}" "agents=evaluation-orchestrator,axis1-6{,citation-auditor}" "ambition={ambition}" "commits={fulfilled}/{total}"
```

---

## 논문 처리 (2-pass + Tier)

사용자가 "새 논문 처리해줘", "논문 분석해줘", "candidates 처리해줘", "가볍게 처리해줘" 등을 말하면 **`paper-processing-orchestrator`** 에이전트가 진입점이 된다. 본 섹션은 그 흐름의 메인 세션 담당 부분을 기술한다.

**명령 플래그**:
- `새 논문 처리해줘` → 2-pass 기본 (triage → tier1/2/3 분배 분석)
- `새 논문 처리해줘 --batch=N` → 배치 크기 오버라이드
- `새 논문 처리해줘 --skip-triage` → triage 생략, 전부 Tier 2 취급 (경고: tier·axis_tags 미부여)
- `새 논문 처리해줘 --tier=1` → 모두 Tier 1 강제
- `새 논문 처리해줘 --priority Loffler_2024 Doebel_2020` → 지정 파일만 Tier 1, 나머지 triage만
- `가볍게 처리해줘` → 전부 Tier 3 강제 (`--tier=3` alias)

### 단계 1: 현재 프로젝트 + candidates 확인

```bash
ls projects/{PROJECT_NAME}/papers/candidates/*.pdf
```

0개면 "candidates가 비어 있습니다" 메시지 후 종료.

### 단계 2: 파일명 정규화 + 메타 추출

```bash
python3 scripts/normalize_filename.py {PROJECT_NAME}
python3 scripts/extract_metadata.py {PROJECT_NAME}
```

### 단계 3: 🤖 paper-processing-orchestrator 호출

1. `skills/agents/paper-processing-orchestrator.md` 파일을 읽는다
2. Agent 도구로 실행 (model: opus, 가볍게 오케스트레이션만):
   - 전달: candidates 파일 목록 + flow 요약 (flow/flow.md의 thesis + 섹션 제목 + 핵심 구성개념 리스트 300-500 단어) + 플래그
   - 수행: 단계 3-7 (Pass 1 triage → tier 분배 → Pass 2 dispatch → sync)

### 단계 3.1: Pass 1 — triage 병렬 (haiku)

orchestrator가 관리. `paper-analyst`를 `Mode A-triage`로 각 PDF에 대해 병렬 호출 (model=haiku, 배치 20-25편). 각 결과는 `papers/analyzed/{파일명}-triage.json`으로 저장.

### 단계 3.2: Tier 분배 + 사용자 보고

```bash
python3 scripts/paper_triage.py summarize {PROJECT_NAME}
```

Tier 분포를 사용자에게 먼저 보고. 사용자 개입 없이 진행 (단 `--priority` 등이 지정되었으면 그에 맞춰 재분배).

### 단계 3.3: Pass 2 — Tier별 병렬 dispatch

| Tier | 모델 | 배치 | Mode |
|------|------|------|------|
| 1 | opus | 5 | A-tier1 (full + Critical Reading) |
| 2 | sonnet | 10 | A-tier2 (full, Critical 제외) |
| 3 | sonnet | 20 | A-tier3 (간소판) |

Tier 1·2·3을 **병렬로** 시작. 각 워커는 `paper-analyst.md` + flow.md + triage JSON + tier별 Mode 지시를 prompt로 받음.

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

## Consensus 검색 (작업 시작) — work-plan.md 기반 자동 실행

사용자가 "작업 시작해줘", "논문 검색해줘", "HUNT 실행" 등을 말하면:

### 단계 1: 선행 조건 확인

1. `projects/{PROJECT_NAME}/work-plan.md` 존재 여부 확인
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
5. `claim-extraction-flow.md / claim-extraction-draft.md` (stage에 맞게)에서 해당 문장의 분류를 UNMATCHED-INTERNAL → MATCHED로 전환
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

2a. **중복 탐지 (번역 전 필수 단계)**:
   - 새 HUNT 결과를 기록하기 전에 기존 `papers/consensus-results.md`에서 동일 논문이 이미 있는지 확인. 판정 기준 우선순위: (1) consensus.app URL 동일 (가장 확실), (2) URL 부재 시 `저자(연도)` + 제목 조합 일치.
   - 중복 논문은 **번역 호출 대상에서 제외**하고 다음 포맷으로 기재:
     ```
     N. **저자 (연도)** — [제목](URL). ⚠️ **중복** — HUNT-XXX #M에서 전체 번역·주석 참조.
     ```
   - Bash 예시 (URL 기반 dedup 체크):
     ```bash
     grep -oE "consensus\.app/papers/(details/)?[a-z0-9]+" papers/consensus-results.md | sort -u
     ```
   - 중복이어도 **주석(annotation)은 새 HUNT 맥락에 맞게 다시 작성** 가능 (같은 논문이 다른 섹션에서 다른 역할을 할 수 있음)

2b. **Abstract 한글 번역 (중복 제외한 신규 논문만)**:
   - **각 신규 논문마다 영어 abstract 원문 전체를 한글로 번역하여 논문 제목/링크 바로 아래 들여쓰기 인용블록(`> `)으로 기재** (사용자가 논문 선별 속도를 높이기 위함). **요약이 아니라 원문 전체 번역**.
   - **번역은 반드시 `abstract-translator` 서브에이전트(haiku 모델)에 위임** — 메인 세션(opus)에서 직접 번역 금지.
   - 호출 순서:
     1. `skills/agents/abstract-translator.md` 파일을 읽는다
     2. Agent 도구로 호출 (model: `haiku`) — 입력: HUNT-NNN의 신규 논문 abstract 원문 목록 (각 논문마다 `[N] 식별자` 포함). 출력: 각 `[N]`에 대응하는 한글 번역 인용블록
   - 반환된 번역을 `consensus-results.md` 해당 논문 아래에 삽입
   - Abstract가 없는 논문은 `> (abstract 없음)` 표기 (번역 호출 불필요)

3. **claim-extraction 매칭 상태 갱신** (`flow/claim-extraction-flow.md 또는 chapters/claim-extraction-draft.md`):
   - 해당 문장의 MATCHED 상태를 ✅로 변경
   - 찾은 대표 논문 2-3편을 인용 후보로 기록

4. **work-plan.md 진척 갱신** (`work-plan.md`):
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
🔄 flow/claim-extraction-flow.md 또는 chapters/claim-extraction-draft.md 매칭 갱신: {T}건

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

### 단계 6: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "HUNT·REANALYZE 실행" "stage=stage1" "target=consensus-results.md" "result={N_hunt} HUNT + {N_reanalyze} REANALYZE done"
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
  - [HUNT-007] S055에 대한 매칭 논문이 기대 프로필 미달 → 재검색 권장
  - [HUNT-012] S089의 MATCHED 논문 3편 중 1편이 원문 확인 결과 over-claim

👉 다음 단계:
   - 잔존 이슈 해소 후 "flow 업데이트해줘"
   - 또는 "초안 작성해줘"로 Stage 2 진입
   - 축 2-5 전체 재평가는 Stage 2 초안 완료 후 권장
```

### 단계 4: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "레퍼런스 점검 완료" "stage=post-research" "result=axis1 {old}→{new} (+{delta})"
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

### 단계 7: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "초안 작성" "stage=v1-draft" "target=chapters/*" "result={N}챕터 {W}단어" "ref=ref:ch-{NNN}" "agents=writing-architect" "commits={fulfilled}/{total}"
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

### 단계 4: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "챕터 수정" "stage=revised" "target=Ch{X}" "result={변경 요약}" "ref=ref:ch-{NNN}" "agents=chapter-editor,citation-auditor"
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

### 단계 3: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "gap 분석" "result={N}개 gap" "agents=gap-finder"
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
3. `claim-extraction-flow.md / claim-extraction-draft.md` (stage에 맞게)에서 해당 논문을 인용하던 MATCHED 문장을 UNMATCHED-EXTERNAL 또는 UNMATCHED-INTERNAL(다른 PDF로 대체 가능 여부 판별)로 재분류

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

### 단계 6: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "논문 제거" "target={파일명}.pdf" "result=archived" "dangling={N}"
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
- `{파일명} 논문 재분석해줘 --tier=1` → 해당 논문을 Tier 1으로 승격 후 재분석

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

각 대상 PDF마다 `paper-processing-orchestrator`를 통해 병렬 호출:

1. `skills/agents/paper-analyst.md` 읽기
2. Agent 도구로 paper-analyst를 **Mode B**로 호출 (model: sonnet, 재분석은 opus 불필요):
   - 전달: PDF 경로 + **현재 flow/flow.md** + 기존 `analyzed/{파일명}-analysis.md` + 변경 섹션 목록 + 재분석 각도
   - 수행: PDF 재스캔 → analyzed/*.md에 `## [v{N+1}] 재분석: {각도}` append (v1 내용은 절대 수정/삭제 금지)
3. `python3 scripts/sync_state.py update-paper {PROJECT} {파일명}` 실행

### 단계 2b: Tier 승격 (선택)

`--tier=1` 플래그가 있으면:
1. triage.json의 tier를 1로 승격 (`paper_triage.py promote {P} {파일명} --to=1`)
2. Mode A-tier1 Critical Reading 섹션을 **추가로** 호출하여 append (opus)

### 단계 3: claim-extraction 반영

`claim-extraction-flow.md / claim-extraction-draft.md` (stage에 맞게)에서 UNMATCHED-INTERNAL이었던 문장들을 재확인:
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

🔄 claim-extraction 반영:
   - UNMATCHED-INTERNAL {N}건 → MATCHED 전환
   - 잔존 UNMATCHED-INTERNAL: {N}건 (추가 재분석 또는 HUNT 필요)

⚠️ 챕터 sync 경고: {N}건 (위 참조)

👉 다음 단계:
   - "Chapter X 수정해줘: 새 분석 반영"
   - 모든 sync 확인: "sync 확인해줘"
   - 평가 갱신: "평가해줘"
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
  "평가해줘"로 Critical Mode 포함 전체 평가 실행
```

### 자동 제안 트리거

첫 `"평가해줘"` 실행 시, intellectual_ambition이 `incremental`이고 flow.md에서 critical 신호 ≥ 3개 감지되면 evaluation-orchestrator가 사용자에게 자동 제안:

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
    답변 후 "평가해줘" 재실행하면 axis6-critical-scorer가 반영합니다.

👉 다음 단계:
   1. critical-questions.md 열어 질문에 자기 언어로 답변
   2. 답변한 내용을 원고에 반영할지 결정
   3. "평가해줘" → 답변·원고 정합성 점검
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

축별 점수 + critical-questions.md 정합성 요약 + 심사자 예상 공격 + 개선 권장 우선순위.

### 단계 4: 활동 로그 기록 (MD Layer 4)

```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "축 6 심층" "result={score}/100" "agents=axis6-critical-scorer"
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
2. 현재 프로젝트의 평가 대상(flow.md 또는 초안) + `papers/analyzed/*.md` + `papers/consensus-results.md`를 전달하여 Agent 실행
3. 결과를 `projects/{PROJECT_NAME}/evaluations/latest/axis4-originality.md`에 저장

**주요 출력**: Novelty Delta Map (선행 연구 3편 대비 차별점 테이블) + "So What?" 명시 여부 + 심사자 예상 공격.

**활동 로그** (MD Layer 4):
```bash
python3 scripts/activity_log.py append {PROJECT_NAME} "축 4 심층" "result={score}/100" "agents=axis4-originality-scorer"
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
python3 scripts/activity_log.py append {PROJECT_NAME} "축 5 심층" "result={score}/100" "agents=axis5-concept-scorer"
```

---

## 🧠 작업 추천 (작업 추천해줘)

사용자가 `"작업 추천해줘"`, `"뭘 해야 해?"`, `"next step"`, `"추천해줘"` 등을 말하면:

### 단계 1: activity.log 기반 분석

```bash
python3 scripts/activity_log.py recommend {PROJECT_NAME} 14
```

반환 JSON에서 `current_state` + `recommendations` 추출. 추가로 sync 상태도 병합:

```bash
python3 scripts/sync_state.py check {PROJECT_NAME}
```

### 단계 2: 종합 보고 (사용자 친화 포맷)

JSON을 파싱하여 아래 형식으로 출력:

```
📍 현재 상태 (최근 14일 로그 기반)

   마지막 활동: 평가 완료 (3일 전)
   마지막 stage: v1-draft
   평가 점수: 287/500
   로그 엔트리: 42건

   🔄 Sync 상태: P1:0 / P2:1 / P3:0 (총 1건 stale)

💡 작업 추천 (우선순위 순)

1. 🔴 "Chapter 5 수정해줘: 급진적 steelman 강화"
   이유: [C-003] UNFULFILLED commitment 감지. Iconoclast 지적 예상.
   예상 효과: critical-lens 축 6 +12점, commitment 커버리지 60%→80%
   🔗 근거 로그: [2026-04-20 14:30] 답변 반영 | ... | 2 UNFULFILLED

2. 🟡 "평가해줘"
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
- `ref:eval-NNN` → `evaluations/archive/NNN-{date}-{stage}/`
- `ref:ch-NNN` → `chapters/archive/NNN-{date}-{trigger}/`
- `ref:q-NNN` → `critical-questions.archive/NNN-{date}-{trigger}.md`
- `ref:commits-NNN` → `critical-commitments.archive/NNN-{date}-{trigger}.md`

### 단계 3: 사용자 요청에 따라 파일 조회·출력

- "work-plan 보여줘" → `archive/{folder}/work-plan.md` Read 후 출력
- "evaluation 보여줘" → `archive/{folder}/evaluation.md`
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
| 작업 시작해줘 | "HUNT·REANALYZE 실행" | result=완료 수 |
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

## 전체 명령어 요약

| 명령어 | 동작 | 에이전트 | Stage |
|--------|------|----------|-------|
| `"[이름] 프로젝트 만들어줘"` | 프로젝트 생성 (+ .sync-state.json 초기화) | - | 0 |
| 🎯 `"평가해줘"` | **5축 냉정 평가 + 작업계획서** (sync 체크 → archive 스냅샷 → 평가) | 🤖 evaluation-orchestrator (+ claim-extractor + originality + concept-clarity) | flow / v1 / revised / final |
| 🔍 `"레퍼런스 점검해줘"` | **축 1 경량 재평가** (빠름, archive 없음) | evaluation-orchestrator (axis-1 mode) | Stage 1 직후 |
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
| `"독창성 평가해줘"` | 축 4 심층 평가 (단독 호출) | 🤖 axis4-originality-scorer | 모든 단계 |
| `"정의 정밀도 평가해줘"` | 축 5 심층 평가 (단독 호출) | 🤖 axis5-concept-scorer | 모든 단계 |
| 🎭 `"비판적 시각 평가해줘"` | 비판적 시각·패러다임 평가 (ambition ≥ critical) | 🤖 axis6-critical-scorer | 모든 단계 |
| 🤔 `"질문 업데이트해줘"` | Socratic 질문 v+1 생성 + 정합성 점검 | 🤖 critical-companion | Stage 마일스톤 + 수동 |
| 🔍 `"비판적으로 분석해줘: {파일}"` | paper-analyst Mode C — hidden assumptions 등 | 🤖 paper-analyst (Mode C) | 리서치 보조 |
| 🧠 `"작업 추천해줘"` | activity.log 기반 다음 명령 추천 (이유 + 로그 근거) | activity_log.py | 모든 단계 |
| ⏪ 로그 라인 복사 + "이 시점 X 보여줘" | time-travel archive 조회 (읽기 전용) | activity_log.py + Read | 모든 단계 |

**주요 명령 실행 시 자동 sync 동작**:
- `"평가해줘"` / `"작업 시작해줘"` 등 주요 명령 **시작 시** → `sync_state.py check` → stale 이슈 사용자 보고 (중대 이슈 시 중단 옵션)
- 각 명령 **완료 후** → `sync_state.py update-*` → 해당 아티팩트 상태 기록

**권장 흐름 (줄글 prose flow 기준, sync 통합)**:
```
프로젝트 생성 → .sync-state.json 초기화 → flow.md 자유 줄글 작성

  → 🎯 평가해줘 (1차)
     ├── sync 체크 (초기 상태)
     ├── claim-extractor → INTERNAL / EXTERNAL 분류
     ├── evaluation-orchestrator → evaluation.md (5축)
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
