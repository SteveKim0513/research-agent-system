# Research Agent — 사용자 매뉴얼

Top-tier 저널 심사 엄격도의 **5축 냉정 평가**를 중심으로, 줄글(prose) flow 작성부터 최종 완성까지 이끌어주는 AI 연구 관리 시스템의 **전체 참고 매뉴얼**입니다.

> - **빠르게 시작하고 싶다면** 먼저 [GUIDE.md](./GUIDE.md) (3분) 참고 — 핵심만.
> - 설치가 되어 있지 않다면 [README.md](./README.md) 참고.
> - "왜 이렇게 설계되었는가?" 궁금하면 [PRINCIPLES.md](./PRINCIPLES.md)(설계 철학) 참고.
> - **이 문서(MANUAL.md)**: 14개 에이전트·sync 아키텍처·Critical Mode·활동 로그·권한 관리 등 **모든 기능 상세** + troubleshooting.

---

## 목차

1. [시스템 철학](#-시스템-철학)
2. [전체 User Journey](#-전체-user-journey)
3. [5축 평가 기준 상세](#-5축-평가-기준-상세)
4. [서브 에이전트 시스템](#-서브-에이전트-시스템)
5. [Sync 아키텍처](#-sync-아키텍처)
6. [Critical Mode (비판적 시각 지원)](#-critical-mode-비판적-시각-지원)
7. [활동 로그 시스템](#-활동-로그-시스템-activity-log)
8. [권한 자동 승인](#-권한-자동-승인-permissions)
9. [파일 구조와 역할](#-파일-구조와-역할)
10. [명령어 레퍼런스](#-명령어-레퍼런스)
11. [작성 팁](#-작성-팁)
12. [트러블슈팅](#-트러블슈팅)

---

## 🧭 시스템 철학

### 왜 5축 평가인가

학술 글쓰기의 실패 지점은 대체로 다섯 가지 중 하나입니다:

1. **레퍼런스 부실** — 주장은 있는데 근거가 없거나, 인용이 원문과 일치하지 않음
2. **논리 비약** — 섹션 간 전환이 끊기거나 thesis와 무관한 탈선
3. **반론 대비 미흡** — 심사자의 steelman 공격에 무방비
4. **독창성 불투명** — "So what?"에 답이 없음
5. **구성개념 모호** — 핵심 용어가 정의 없이 쓰이거나 중간에 의미가 변함

이 시스템은 각 축을 **top-tier 저널 심사자 엄격도**로 냉정하게 채점하고, 각 감점 사유마다 구체적 작업을 지시합니다.

### 왜 줄글 flow인가

연구자는 본래 에세이처럼 생각합니다. 체크박스 템플릿을 채우는 방식은 창의적 논증의 흐름을 끊습니다.

이 시스템은 사용자가 쓴 자유 줄글을 **claim-extractor**가 문장 단위로 읽어 자동 구조화합니다. 사용자는 사고를 흐름으로 서술하고, 시스템이 기계적 구조화를 맡습니다.

### 왜 재평가 루프인가

한 번의 평가는 의미 없습니다. 연구 글쓰기는 **"작성 → 평가 → 수정 → 재평가"** 의 반복입니다. 이 시스템은 매 평가 시 `archive/` 스냅샷을 보존해 **점수 delta를 추적**하고, 어느 수정이 어느 축을 몇 점 올렸는지 정량적으로 확인할 수 있게 합니다.

### 왜 Sync 아키텍처인가

연구 글쓰기에서 가장 자주 발생하는 "조용한 오류"는 아티팩트 간 불일치입니다:
- 논문을 삭제했는데 초안에 여전히 그 인용이 남아 있음 (dangling citation)
- flow의 논리 흐름을 바꿨는데 기존 논문 분석이 옛 각도만 담음 (stale analysis)
- 챕터를 수정했는데 최종 통합본이 구버전 (out-of-date final)
- 초안이 특정 논문 v1 기반인데 v2로 재분석됐으나 초안은 갱신 안 됨

이 시스템은 `.sync-state.json`으로 **모든 아티팩트의 해시·버전·의존성을 추적**하고, 명령 시작 시 자동으로 stale 감지, 명령 완료 후 자동으로 상태 갱신합니다. [§ Sync 아키텍처](#-sync-아키텍처)에서 상세 설명.

---

## 🗺 전체 User Journey

### 각 단계별 에이전트 사용 맵 (한눈에 보기)

| 단계 | 명령 | 핵심 에이전트 | 부가 에이전트 (자동 체이닝) | 산출물 |
|------|------|-------------|-------------------------|--------|
| 1. 프로젝트 생성 | `"[이름] 프로젝트 만들어줘"` | — | sync_state.py init | 폴더 구조 + 빈 flow.md |
| 2. flow.md 작성 | (사용자 직접) | — | — | flow.md (prose) |
| 3. 1차 평가 | `평가해줘` | **flow-evaluator** (오케스트레이터) | claim-extractor + originality-evaluator + concept-clarity-evaluator + (ambition ≥ critical: critical-lens-evaluator + critical-companion) + (v1-draft/revised/final: citation-auditor 단계별 샘플링) | evaluation.md, work-plan.md, claim-extraction.md, originality-report.md, concept-clarity-report.md, (+critical-lens-report.md, critical-questions.md v+1) |
| 4a. 리서치 실행 | `작업 시작해줘` | — (MCP 직접 호출) | **paper-analyst Mode B** (REANALYZE 과제), Consensus MCP (HUNT 과제) | consensus-results.md 누적, analyzed/*.md v2+ append |
| 4b. PDF 처리 | `새 논문 처리해줘` | **paper-analyst** (Mode A) | — | analyzed/*.md v1 |
| 5a. 경량 점검 | `레퍼런스 점검해줘` | **flow-evaluator** (axis-1 mode) | PDF 2-3편 샘플링 자동 검증 | evaluation.md 축 1만 갱신 |
| 5b. flow 보강 | `flow 업데이트해줘` | **flow-refiner** | — | flow.md 업데이트 제안 → 승인 시 flow.md 갱신 |
| 6. 1차 초안 | `초안 작성해줘` | **writing-architect** (Phase 1 → 사용자 승인 → Phase 2) | (ambition ≥ critical: commitment 추출 prehook 자동) + on-demand PDF 접근 | chapters/*.md, final/complete-draft.md, .docx, critical-commitments.md 갱신 |
| 7. 2차 평가 | `평가해줘` | **flow-evaluator** | claim-extractor + axis-4/5 + **citation-auditor 30% 샘플** | archive/002 + 갱신된 evaluations/latest/ |
| 8. 챕터 수정 | `Chapter X 수정해줘: ...` | **chapter-editor** | (ambition ≥ critical: commitment prehook) + **citation-auditor** 자동 체이닝 | 수정된 chapter 파일 + 감사 리포트 + critical-commitments.md 상태 갱신 |
| 9. 3차 평가 | `평가해줘` | **flow-evaluator** | claim-extractor + axis-4/5 + **citation-auditor 전량** | archive/003 |
| 10a. 최종 통합 | `최종 통합해줘` | — | — | final/complete-draft.md + .docx 재생성 |
| 10b. 심사 시뮬 | `리뷰 체크해줘` | **peer-reviewer** (Mode A) | — | 리뷰어 3명 시뮬 리포트 |
| 10c. 최종 평가 | `평가해줘` | **flow-evaluator** | claim-extractor + **citation-auditor 전량 + 이전 archive 대비 new error** | archive/004 |
| 언제든 (보조) | `gap 분석해줘` | **gap-finder** | — | gaps-analysis.md |
| 언제든 (empirical만) | `방법론 추천/검증해줘` | **methodology-advisor** | — | 화면 보고 |
| 언제든 | `sync 확인해줘` | sync_state.py | — | stale 리스트 + 해결 가이드 |
| 언제든 | `논문 제거해줘: {파일}` | sync_state.py + (자동) citation-auditor | — | archived/ 이동 + dangling 경고 |
| 언제든 | `논문 재분석해줘` | **paper-analyst** (Mode B) | — | analyzed/*.md v2+ append |
| 단독 심층 평가 | `독창성 평가해줘` | **originality-evaluator** | — | originality-report.md |
| 단독 심층 평가 | `정의 정밀도 평가해줘` | **concept-clarity-evaluator** | — | concept-clarity-report.md |

### 상세 단계별 가이드

### 단계 0 — 최초 설치 (1회)

[README § 설치](./README.md#-설치) 참고.

설치 완료 후 어느 디렉토리에서든 `claude`를 실행하면 research-agent 스킬이 로드됩니다.

### 단계 1 — 프로젝트 생성

```bash
cd ~/Documents/research-agent
claude
```

Claude에서:
```
> "my-essay 프로젝트 만들어줘"
```

자동 생성되는 구조:
```
projects/my-essay/
├── flow.md                             ← 당신이 자유 줄글로 작성
├── FLOW-TEMPLATE.md                    ← 작성 가이드 (수정 금지)
├── critical-questions.md               ← 🎭 Critical Mode: 사용자가 답하는 Socratic 질문
│                                         (intellectual_ambition ≥ critical일 때만 생성)
├── critical-questions.archive/         ← 🎭 질문·답변 버전 히스토리 (v1, v2, ...)
├── critical-commitments.md             ← 🎭 답변에서 자동 추출한 actionable commitment
│                                         (writing 에이전트가 필수 참조)
├── critical-commitments.archive/       ← 🎭 commitment 상태 버전 히스토리
├── evaluations/
│   ├── latest/                         ← 평가 결과 (최신본)
│   │   ├── evaluation.md
│   │   ├── work-plan.md
│   │   ├── claim-extraction.md
│   │   ├── originality-report.md
│   │   ├── concept-clarity-report.md
│   │   └── critical-lens-report.md     ← 🎭 (Critical Mode 활성 시)
│   └── archive/                        ← 평가 스냅샷 히스토리
├── papers/
│   ├── candidates/                     ← 다운로드한 PDF 임시 보관
│   ├── collected/                      ← 처리 완료된 PDF
│   ├── analyzed/                       ← paper-analyst 분석 (v1/v2/v3/[critical] append)
│   └── archived/                       ← "논문 제거해줘"로 이동된 PDF + 분석
├── chapters/                           ← 초안 섹션별 파일
│   └── archive/                        ← 덮어쓰기 직전 자동 스냅샷 (롤백 가능)
├── final/                              ← 통합본 + docx
├── activity.log                        ← 📓 모든 주요 작업 append-only 로그
├── .paper-metadata.json                ← 메타데이터 + intellectual_ambition 필드
└── .sync-state.json                    ← 아티팩트 의존성·버전 추적
```

### 단계 2 — flow.md 작성 (자유 줄글)

에디터로 `projects/my-essay/flow.md`를 열어 **자유 줄글**로 작성합니다. 템플릿 빈칸을 채우는 방식이 아닙니다.

**최소 요구사항**:
- 메타데이터 5줄 (과제명·코스·마감·분량·인용 스타일)
- 연구 질문(RQ) 한 문장 — 예: "이 글은 X인가를 묻는다"
- 핵심 주장(Thesis) 한 문장 — 예: "본 에세이는 X라고 주장한다"

**권장**: 에세이처럼 서술하며 다음 요소를 녹여 쓰세요:
- 문제 설정 / 왜 중요한가
- 기존 관점의 한계
- 당신의 제안
- 예상 반론
- 함의·기여

**작성 예시**는 `FLOW-TEMPLATE.md` 참고.

**하지 말 것**:
- 체크박스 목표 리스트로 쪼개기
- `[논문 이름 미정]` 같은 placeholder 넣기
- thesis 없이 "이 글은 ~을 다룬다"로만 끝내기

### 단계 3 — 1차 평가 (평가해줘)

```
> "평가해줘"
```

자동으로 일어나는 일:

**3-1. 이전 평가 스냅샷 보존**
`evaluations/latest/`가 비어있지 않으면 `evaluations/archive/{NNN}-{date}-{stage}/`로 스냅샷 복사.

**3-2. claim-extractor 실행** (prose flow 전용)
- 모든 문장에 ID 부여 (S001, S002, ...)
- 5종 분류:
  - 🔴 NEEDS_CITATION (A 경험 / B 기술 / C 차용 정의 / D 반론)
  - 🟡 OPTIONAL (E 저자 확장)
  - 🟢 NO_CITATION (F 저자 기여 / G 연결·메타)
- `papers/consensus-results.md` pool과 매칭하여 MATCHED / UNMATCHED 판정
- Over-claim / Under-claim 경고 생성
- 저장: `evaluations/latest/claim-extraction.md`

**3-3. flow-evaluator 실행** (5축 평가)
- 축 1~5 각 100점 만점, 하위 기준 25점씩
- 각 감점 사유를 섹션·문장 단위로 구체적으로 기록
- 축 간 상호작용 문제(예: 구성개념 모호 → 심사자 공격 표면 확대) 점검
- originality-evaluator(축 4), concept-clarity-evaluator(축 5) 병렬 자동 호출
- 저장: `evaluations/latest/evaluation.md`

**3-4. 작업 지시서 생성**
- 4단계(리서치 / 1차작성 / 수정 / 최종)별 작업 큐 구성
- 각 작업에 `[RESEARCH/DRAFT/REVISION/FINAL]` 태그 + 담당 에이전트 + 예상 점수 회복
- **핵심**: Stage 1 섹션에 **HUNT 체크박스 목록**이 자동 생성됨 — UNMATCHED 문장마다 검색 키워드·기대 논문 프로필 포함
- 저장: `evaluations/latest/work-plan.md`

**3-5. 화면 보고** — 축별 점수·등급·심사 판정·작업 수 요약.

### 단계 4 — Stage 1: 논문 리서치

#### 4-1. HUNT 자동 검색

```
> "작업 시작해줘"
```

시스템이 `evaluations/latest/work-plan.md`의 미완료 `[HUNT-NNN]` 체크박스를 전량 파싱하여 순차 Consensus 검색을 실행합니다:

- 쿼리는 **3개씩 병렬 배치** (MCP rate limit 회피)
- Rate limit 발생 시 30초 대기 후 재시도
- 결과를 `papers/consensus-results.md`에 **누적 저장** (각 결과에 HUNT ID 태그)
- `claim-extraction.md`의 MATCHED 상태를 ✅로 갱신
- `work-plan.md`의 HUNT 체크박스를 `- [x]` 로 갱신

#### 4-2. 사용자가 PDF 다운로드

`consensus-results.md`에 저장된 각 논문의 링크에서 원문 PDF를 받아 `papers/candidates/`에 보관합니다. (저작권 접근은 사용자 책임)

#### 4-3. PDF 처리 + 심층 분석

```
> "새 논문 처리해줘"
```

자동으로:
- `scripts/extract_metadata.py`로 각 PDF의 메타데이터 추출
- `.paper-metadata.json` 업데이트
- PDF를 `collected/`로 이동
- **paper-analyst 에이전트 병렬 호출** — 각 논문에 대해:
  - 3줄 요약
  - 핵심 기여
  - 한계
  - 관련성 점수
  - 섹션별 활용 방안
  - 저장: `papers/analyzed/{파일명}-analysis.md`

### 단계 5 — 경량 점검 (축 1 전용)

Stage 1 직후 전체 재평가는 **낭비**입니다. flow.md 텍스트가 그대로이므로 축 2·5는 0점 변화, 축 3·4는 미미합니다.

대신 경량 명령을 사용하세요:

```
> "레퍼런스 점검해줘"
```

축 1 네 가지 하위 기준(Coverage, Accuracy, Authority, Balance)만 빠르게 재채점합니다. Archive 스냅샷은 생성하지 않습니다.

보고 예:
```
축 1 레퍼런스 충실도: 52 → 84 (+32 🟢)
  ├─ 1-1 Coverage: 40 → 92 (+52)
  ├─ 1-2 Accuracy: 65 → 88 (+23)
  ├─ 1-3 Authority: 60 → 82 (+22)
  └─ 1-4 Balance: 43 → 74 (+31)

⚠️ 잔존 이슈:
  - [HUNT-007] S055의 매칭 논문이 기대 프로필 미달 → 재검색 권장
```

### 단계 6 — (선택) Flow 업데이트

새로 확보한 논문으로 논증 자체를 강화하고 싶다면:

```
> "flow 업데이트해줘"
```

writing-architect가 새 논문 기반으로 축 3(Steelman 보강)·축 4(Novelty Delta 명확화) 관점의 **문단 단위 수정 제안**을 diff 형태로 보고합니다. 사용자가 수락 여부를 개별 선택한 뒤 적용됩니다.

반영 후에는 **전체 재평가 "평가해줘"** 가 의미 있어집니다.

### 단계 7 — Stage 2: 1차 초안 작성

```
> "초안 작성해줘"
```

writing-architect가 2단계로 동작:

**Phase 1 — 논증 구조 설계** (자동, 사용자 승인 필요)
- flow.md + 모든 `papers/analyzed/*.md` + work-plan.md 종합
- 각 섹션의 논증 구조(주장 → 근거 → 반박 → 재반박)와 **문단 단위 인용 매핑** 설계
- 사용자에게 구조 확인 요청

예시:
```
📖 Section 1: Introduction (4 문단)
문단 1: [연구 배경 — 넓은 맥락]
  └── 근거: Kroupin (2025), Jukes (2024)
문단 2: [문제 제기 — 이분법의 한계]
  └── 근거: Miller (2023), Gago-Galvagno (2024)
...

👉 이 구조로 진행할까요?
```

**Phase 2 — 사용자 승인 후 초안 작성**
- Topic Sentence First 원칙
- Synthesis 위주(논문별 나열 금지)
- 인용 강도 조절(suggests / indicates / demonstrates)
- 섹션별 파일: `chapters/01-introduction.md`, `02-background.md`, ...
- 통합본: `final/complete-draft.md` + `final/complete-draft.docx`

### 단계 8 — 2차 평가 (초안 후)

```
> "평가해줘"
```

이제 전체 5축이 **모두 유의미하게 움직입니다**. 평가 직전 현재 `latest/`가 `archive/002-{date}-v1-draft/`로 스냅샷 보존됩니다.

`evaluation.md` 최상단에 직전 archive와의 **축별 delta 표**가 자동 삽입됩니다:
```
## 📈 Delta (vs archive/001-2026-04-18-flow)
| 축 | 이전 | 현재 | 변화 |
| 1 | 52 | 89 | +37 🟢 |
| 2 | 68 | 81 | +13 🟢 |
| 3 | 54 | 72 | +18 🟢 |
| 4 | 58 | 77 | +19 🟢 |
| 5 | 55 | 68 | +13 🟡 |
```

### 단계 9 — Stage 3: 챕터 수정

```
> "Chapter 2 수정해줘: impurity problem 부분을 Löffler 2024 논증으로 강화"
```

자동으로:
1. 해당 챕터 파일 읽기 → 수정 적용 → 저장
2. 자동 일관성 체크 (flow 목표 달성 / 챕터 간 연결 / 중복)
3. **citation-auditor 에이전트 자동 호출**:
   - 수정된 챕터의 모든 인용을 `papers/collected/`의 원문 PDF와 대조
   - Accuracy: over-claim, misattribution, fabrication 탐지
   - APA 형식 체크
   - 인용 분포 분석
4. 즉시 수정 필요 건을 보고

모든 챕터를 순회 수정 후 다시 "평가해줘" 실행 → `archive/003-{date}-revised/` 생성.

### 단계 10 — Stage 4: 최종 완성

#### 10-1. 심사 시뮬레이션

```
> "리뷰 체크해줘"
```

peer-reviewer Mode A 실행:
- 가상 심사자 2~3명(방법론·분야 전문·실용주의) 시뮬레이션
- 각 리뷰어의 Major/Minor issue 도출
- 종합 판정(Reject / Major Revision / Minor Revision / Accept)

#### 10-2. 최종 평가

```
> "평가해줘"
```

`archive/004-{date}-final/` 스냅샷 생성. 모든 축이 90점 이상 🟢이고 종합이 450/500 이상이면 제출 준비 완료.

#### 10-3. 실제 리뷰 대응 (제출 후)

학술지 심사 결과를 받으면:
```
> "리뷰 답변 도와줘: [리뷰 텍스트 전체 붙여넣기]"
```

peer-reviewer Mode B:
- 이슈 분류(필수 수정 / 권장 / 거부 가능)
- 답변 전략
- Response to Reviewer 초안 작성

---

## 📊 5축 평가 기준 상세

각 축은 100점 만점, 하위 기준 4개 × 25점.

### 축 1. 논문 레퍼런스 충실도

| 하위 기준 | 질문 | 감점 예시 |
|----------|------|----------|
| 1-1 Coverage | 모든 empirical/descriptive 주장에 인용이 있는가? | "문단 2의 3개 주장 중 1개만 인용" −10 |
| 1-2 Accuracy | 인용된 논문이 실제로 그 주장을 뒷받침하는가? | "'proves X' 표현했으나 원문은 상관관계만 보고" −15 |
| 1-3 Authority | 세미널 논문 + 최신 반론 모두 커버? | "이 분야 세미널 Miller (2000) 누락" −10 |
| 1-4 Balance | disconfirming evidence를 배제하지 않았는가? | "반대 증거 논문 0편" −10 |

**담당 에이전트**: citation-auditor (감사), paper-analyst (분석), Consensus MCP (검색)

### 축 2. 논리 전개 완성도

| 하위 기준 | 질문 | 감점 예시 |
|----------|------|----------|
| 2-1 Argument Chain | premise → evidence → warrant → claim 연결? | "warrant 누락" −10 |
| 2-2 Section Transition | 앞 섹션 결론이 뒷 섹션 전제로? | "Sec 2 결론과 Sec 3 전제 불일치" −15 |
| 2-3 Thesis Alignment | 모든 단락이 thesis에 기여? | "Sec 5 단락 2는 탈선" −8 |
| 2-4 Scope Closure | RQ에 실제로 답했는가? | "RQ의 '어떻게'를 '왜'로만 답함" −15 |

**담당 에이전트**: writing-architect

### 축 3. 반박/강화 논리

| 하위 기준 | 질문 | 감점 예시 |
|----------|------|----------|
| 3-1 Steelman | 반론을 가장 강한 형태로 제시? | "strawman 버전만 다룸" −12 |
| 3-2 Falsifiability | 주장이 틀릴 조건을 명시? | "반증 조건 없음" −10 |
| 3-3 Limitations | 한계를 productive하게 제시? | "'향후 연구' 수준으로만 처리" −8 |
| 3-4 Reviewer Attack | 심사자 예상 공격 대응? | "major objection 미대응" −15 |

**담당 에이전트**: peer-reviewer

### 축 4. 독창성·기여도

| 하위 기준 | 질문 | 감점 예시 |
|----------|------|----------|
| 4-1 "So What?" | 이 논문이 없으면 분야가 잃는 것? | "답 부재" −15 |
| 4-2 Novelty Positioning | 선행 연구 3편 대비 Delta 명시? | "Doebel과의 차별점 불명" −12 |
| 4-3 Contribution Layer | 개념/이론/방법론/경험 층위 명확? | "층위 혼재" −8 |
| 4-4 Implications | 후속 경로가 구체적? | "일반론 수준" −7 |

**담당 에이전트**: originality-evaluator

### 축 5. 구성개념 정의 정밀도

| 하위 기준 | 질문 | 감점 예시 |
|----------|------|----------|
| 5-1 Definition | 핵심 용어 정의·일관 사용? | "'규칙 깊이' 정의 부재" −15 |
| 5-2 Operationalization | 관찰 가능 지표? | "자발성 구분 기준 없음" −12 |
| 5-3 Boundary | 적용/비적용 범위 명확? | "경계 조건 부재" −8 |
| 5-4 Categorical/Dimensional | 범주/연속 선택 근거? | "이분법 사용하며 근거 없음" −10 |

**담당 에이전트**: concept-clarity-evaluator

---

## 🤖 서브 에이전트 시스템

총 **14개** 전문 에이전트 (12 기본 + 2 Critical Mode). 각 에이전트는 단일 책임을 가지며, 필요 시 서로 체이닝(자동 호출)된다.

**Critical Mode**는 프로젝트의 `intellectual_ambition`이 `critical` 또는 `paradigm-shifting`일 때 활성화되며, 비판적 시각·새로운 관점·패러다임 도전을 능동적으로 지원한다 (Oxford·Cambridge·프랑스 고등연구원 style).

### 📊 에이전트 분류 (3 카테고리)

#### 평가 전용 (4개)

| 에이전트 | 단일 책임 | 읽는 것 | 쓰는 것 | 호출 시점 |
|---------|----------|--------|---------|----------|
| **flow-evaluator** | 5축 평가 오케스트레이션, work-plan.md 생성, sync gate | flow.md, claim-extraction.md, analyzed/*.md, chapters/*, consensus-results.md | evaluation.md, work-plan.md, archive/ 스냅샷 | `평가해줘` |
| **claim-extractor** | 문장 단위 주장 추출·5종 분류·3-way(MATCHED/INTERNAL/EXTERNAL) 매칭 | flow.md 또는 chapters/*, analyzed/*.md (모든 버전), consensus-results.md | claim-extraction.md (REANALYZE+HUNT 과제 포함) | flow-evaluator 자동 호출 (prose flow) |
| **originality-evaluator** | 축 4 심층 평가, 선행 연구 Delta Map | flow 또는 초안, analyzed/*.md | originality-report.md | flow-evaluator 자동 / `독창성 평가해줘` 단독 |
| **concept-clarity-evaluator** | 축 5 심층 평가, 구성개념 정의 감사 테이블 | flow 또는 초안 | concept-clarity-report.md | flow-evaluator 자동 / `정의 정밀도 평가해줘` 단독 |

#### Critical Mode 전용 (2개) — ambition ≥ critical 시 활성화

| 에이전트 | 단일 책임 | 읽는 것 | 쓰는 것 | 호출 시점 |
|---------|----------|--------|---------|----------|
| **critical-lens-evaluator** 🎭 | 축 6 비판적 시각 (C-1 Paradigm Mapping, C-2 Fault-line, C-3 Bold Defense, C-4 Minority Recovery) | flow/chapters, critical-questions.md 답변, Mode C 분석 | critical-lens-report.md | flow-evaluator 자동 / `비판적 시각 평가해줘` 단독 |
| **critical-companion** 🤔 | Socratic 질문 생성 (답변 절대 금지) + 이전 답변-원고 정합성 점검 | flow/chapters, evaluations, 이전 critical-questions.md | critical-questions.md (신규 버전), archive/에 이전 버전 | Stage 마일스톤 자동 / `질문 업데이트해줘` 수동 |

**critical-companion의 절대 원칙**: 질문만 생성하고 **답변 예시·초안·암시·leading question 절대 금지**. 답을 찾는 과정 자체가 새로운 관점의 발견이며, 그 과정은 사용자의 것이어야 한다.

#### 생성·수정 (5개)

| 에이전트 | 단일 책임 | 읽는 것 | 쓰는 것 | 호출 시점 |
|---------|----------|--------|---------|----------|
| **paper-analyst** | PDF → 섹션별 인용 다발 (v1/v2/v3 버전 관리) + Mode C (Critical Reading: hidden assumptions/biases/politics/alternatives/silences) | papers/collected/*.pdf, flow.md | analyzed/*.md (append) | `새 논문 처리해줘` (A 자동) / `논문 재분석해줘` (B) / `비판적으로 분석해줘` (C, ambition ≥ critical 자동) |
| **writing-architect** | **신규 챕터 창작** (Phase 1 구조 설계 → 사용자 승인 → Phase 2 초안) | flow.md, analyzed/*.md (모든 버전), on-demand PDF | chapters/0N-*.md, final/complete-draft.md(.docx) | `초안 작성해줘` |
| **chapter-editor** ✏️ | **기존 챕터 국소 수정** (구조 유지, 지정 부분만) — writing-architect와 구분 | 대상 chapter, 수정 지시, analyzed/*.md, on-demand PDF | 수정된 chapter 파일 | `Chapter X 수정해줘: ...` (자동) |
| **flow-refiner** 📝 | **flow.md 보강 제안만** (직접 수정 금지, diff 승인 후 반영) | flow.md, 새 analyzed/*.md, evaluation.md 감점 사유 | diff 제안 (승인 시 flow.md 반영) | `flow 업데이트해줘` |
| **citation-auditor** | PDF 원문 대조 accuracy 감사 (over-claim·misattribution·APA 형식·분포) | chapter, papers/collected/*.pdf, analyzed/*.md | 감사 리포트 (화면) | `Chapter X 수정해줘` 후 자동 체이닝 + `평가해줘` v1/revised/final 단계 자동 체이닝 |

#### 보조 (3개, 수동 호출)

| 에이전트 | 단일 책임 | 호출 시점 | 노트 |
|---------|----------|----------|------|
| **gap-finder** | **분야(field)의 빈틈** 5종(방법론·응용·데이터·이론·시간) 탐색 | `gap 분석해줘` | → *후속 연구 아이디어* 도출용 |
| **methodology-advisor** | 방법론 추천(Advisor 3가지 비교) 또는 검증(Critic) | `방법론 추천/검증해줘` | ⚠️ **empirical 프로젝트 전용** — theoretical essay에서는 사용 안 함 |
| **peer-reviewer** | Mode A 가상 심사자 2~3명 + **Reviewer 4 Iconoclast (ambition ≥ critical 시 자동 추가)** / Mode B 실제 리뷰 대응 | `리뷰 체크해줘` / `리뷰 답변 도와줘` | Stage 4 최종 품질 게이트. Iconoclast는 timidity·paradigm 내부 머무름·자기 배신 탐지 |

---

### 🔍 혼동하기 쉬운 쌍 명확화

#### gap-finder vs originality-evaluator

| 항목 | gap-finder | originality-evaluator |
|------|-----------|---------------------|
| **주어** | **분야(field)** | **이 논문(this paper)** |
| **질문** | "분야 전반에서 뭐가 안 다뤄졌는가?" | "이 논문이 분야에 **새로** 뭐를 더하는가?" |
| **용도** | 후속 연구 아이디어, 미래 방향 | 현 논문의 novelty positioning, "So What?" 검증 |
| **출력** | gaps-analysis.md (5종 Gap + 난이도·임팩트) | originality-report.md (Delta Map + 축 4 점수) |
| **호출 시점** | 수동, 아이디어 발상 단계 | flow-evaluator 자동 (모든 평가 시) |

둘 다 "빠진 것"을 다루지만 **주어가 다름**. 혼동 시 gap-finder를 "미래 연구 제안 도구", originality-evaluator를 "현 논문 기여 심사 도구"로 기억.

#### writing-architect vs chapter-editor vs flow-refiner

| 항목 | writing-architect | chapter-editor | flow-refiner |
|------|------------------|----------------|--------------|
| **대상** | chapters/* **신규 창작** | chapters/* **기존 수정** | **flow.md 보강 제안** |
| **구조 설계** | ✅ Phase 1 필수 | ❌ (기존 구조 유지) | ❌ (제안만) |
| **사용자 승인 시점** | Phase 1 후 (구조 확인) | 즉시 수정 (지시 명확) | 제안 후 (반영 승인) |
| **직접 파일 수정** | ✅ chapters/* 생성 | ✅ chapters/* 수정 | ⚠️ 승인 후에만 |
| **후속 에이전트** | — | citation-auditor 자동 체이닝 | — |
| **호출 빈도** | 1회 (초안) | 반복 (5챕터 × 2-3회) | 0-1회 (선택) |

---

## 🔄 Sync 아키텍처

### 핵심 파일: `.sync-state.json`

프로젝트 루트에 생성되며 모든 아티팩트의 해시·버전·의존성을 추적:

```json
{
  "schema_version": "1.0",
  "project_name": "CDEA",
  "updated_at": "2026-04-18T10:30:00",
  "flow_md": { "hash": "abc123", "mtime": "..." },
  "papers": {
    "Kroupin_2025.pdf": {
      "pdf_hash": "def456",
      "analyzed_version": "v2",
      "analyzed_flow_hash_at": "abc123",
      "analyzed_updated_at": "..."
    }
  },
  "chapters": {
    "01-introduction.md": {
      "hash": "...",
      "flow_hash_at_write": "abc123",
      "papers_used": { "Kroupin_2025.pdf": "v2" },
      "written_at": "..."
    }
  },
  "evaluations": {
    "flow_hash_at_run": "abc123",
    "chapter_hashes_at_run": {...},
    "ran_at": "..."
  },
  "final": {
    "chapter_hashes_at_build": {...},
    "built_at": "..."
  }
}
```

### 의존성 그래프 (invalidation rules)

어떤 이벤트가 어떤 아티팩트를 stale로 만드는지:

```
flow.md 변경
  ↓ invalidates
  ├─ analyzed/*.md        → 🔄 REANALYZE 권장
  ├─ claim-extraction.md  → 재생성 필요
  ├─ work-plan.md         → 재생성 필요
  ├─ evaluation.md        → 재채점 필요
  └─ chapters/*.md        → sync 경고

papers/collected/ 추가
  ↓ invalidates
  ├─ claim-extraction.md  → MATCHED 재계산
  ├─ work-plan.md         → HUNT 완료 체크
  └─ evaluation.md        → 축 1 재채점 권장

papers/collected/ 삭제
  ↓ invalidates
  ├─ claim-extraction.md  → MATCHED → UNMATCHED 역전환
  ├─ chapters/*.md        → dangling citation 탐지
  └─ evaluation.md        → 축 1 감점

analyzed/*.md 버전 업 (v1 → v2)
  ↓ invalidates
  └─ chapters/*.md (해당 논문 사용 챕터)  → "새 분석 반영" 권장

chapters/0N.md 수정
  ↓ invalidates
  ├─ final/complete-draft.*  → 재통합 필요
  └─ evaluation.md           → 재채점 권장
```

### Sync 점검 자동화

모든 주요 명령은 다음 패턴으로 sync와 상호작용합니다:

**시작 시 (stale gate)**:
```bash
python3 scripts/sync_state.py check {PROJECT}
```
- stale 이슈 없으면 → 진행
- 중대 이슈 (dangling citation, 삭제된 논문) 있으면 → 사용자 확인 후 진행 또는 중단

**완료 시 (상태 갱신)**:
```bash
python3 scripts/sync_state.py update-{artifact} {PROJECT} [filename]
```
- flow.md 수정 → `update-flow`
- 논문 분석 완료 → `update-paper`
- 챕터 작성/수정 → `update-chapter`
- 평가 실행 → `update-evaluation`
- 최종 통합 → `update-final`
- 논문 제거 → `remove-paper`

### sync_state.py CLI

```bash
# 초기화
python3 scripts/sync_state.py init {project}

# 점검 (stale 리스트를 JSON으로 반환)
python3 scripts/sync_state.py check {project}

# 개별 갱신
python3 scripts/sync_state.py update-flow {project}
python3 scripts/sync_state.py update-paper {project} <filename.pdf>
python3 scripts/sync_state.py update-chapter {project} <filename.md>
python3 scripts/sync_state.py update-evaluation {project}
python3 scripts/sync_state.py update-final {project}
python3 scripts/sync_state.py remove-paper {project} <filename.pdf>

# chapters 스냅샷 (자동 호출되지만 수동 사용 가능)
python3 scripts/sync_state.py snapshot-chapters {project} <trigger> [chapter.md]
#   trigger 예: "pre-redraft", "ch2-edit", "manual-backup"
#   chapter.md 지정 시 단일 파일, 미지정 시 chapters/ 전체
```

### Stale 유형 + Priority 점수

각 stale 항목은 **긴급도 점수**와 **등급(tier)**, **의존성 순서**를 부여받는다.

| kind | 의미 | 기본 score | tier | dependency order | 권장 해결 |
|------|------|-----------|------|------------------|----------|
| `flow_changed` | flow.md 해시 불일치 | 30 | 🔴 P1 | 3 | `"논문 재분석해줘"` 후 `"평가해줘"` |
| `paper_removed` | collected/에서 제거 (dangling당 +10) | 20+ | 🔴 P1 | 2 | `"논문 제거해줘: {파일}"` |
| `chapter_flow_drift` | 챕터가 구 flow 기반 (챕터당 +15) | 15+ | 🟡 P2 | 5 | `"Chapter X 수정해줘"` |
| `chapter_paper_version_drift` | 구버전 논문 분석 기반 (drift당 +10) | 10+ | 🟡 P2 | 4 | `"Chapter X 수정해줘: 새 분석 반영"` |
| `paper_added_untracked` | collected/에 미추적 논문 (개당 +4) | 8+ | 🟢/🟡 | 1 | `"새 논문 처리해줘"` |
| `evaluation_stale` | evaluation이 현재 flow/chapters와 불일치 | 10 | 🟢 P3 | 7 | `"평가해줘"` |
| `final_stale` | final/* 가 chapters 현재와 불일치 | 5 | 🟢 P3 | 6 | `"최종 통합해줘"` |

### Priority Tier 의미

- **🔴 P1-Critical (score ≥ 30)**: downstream 모든 stale을 재촉발하는 루트. 먼저 해결 필수.
- **🟡 P2-High (15-29)**: 특정 챕터들에 영향. P1 해소 후 처리.
- **🟢 P3-Medium (< 15)**: 마지막 재빌드·재평가. 다른 stale 해소 후 자연 해결되는 경우 많음.

### Dependency Order (실행 순서)

점수 크기와 **별개로**, 의존성에 따라 해결 순서가 정해진다. 순서를 지키지 않으면 후속 단계에서 같은 stale이 재감지됨:

```
1. paper_added_untracked     → 새 논문 메타데이터 등록 먼저
2. paper_removed             → dangling 해소 (후속 수정의 전제)
3. flow_changed              → cascade 시작점
4. chapter_paper_version_drift
5. chapter_flow_drift        → papers 정리 후 chapters 수정
6. final_stale               → chapters 정리 후 재빌드
7. evaluation_stale          → 모든 것 정리 후 재평가
```

`"sync 확인해줘"` 명령이 자동으로 이 순서대로 실행 계획을 제시함.

### 편의 명령

**언제든지 상태 점검**:
```
> "sync 확인해줘"
```

현재 모든 아티팩트의 정합 상태를 점검하고 순차 해결 가이드를 제시.

**안전한 논문 제거**:
```
> "논문 제거해줘: Zelazo_2022.pdf"
```
- `collected/` → `archived/`로 이동 (복구 가능)
- 해당 논문 사용 챕터의 dangling citation 자동 탐지
- 수정 필요 챕터 리스트 제공

**최종 통합 재빌드**:
```
> "최종 통합해줘"
```
chapters/*.md → final/complete-draft.md + .docx 재생성.

---

## 🎭 Critical Mode (비판적 시각 지원)

### 활성화 방법

**방법 1: 명령으로 설정 (권장)**
```
"비판 모드 critical로 설정해줘"
"비판 모드 paradigm-shifting로 설정해줘"
"비판 모드 incremental로 되돌려줘"
```

**방법 2: 자동 제안 수용**
첫 `"평가해줘"` 실행 시 flow.md에 critical 신호(≥3개)가 있으면 시스템이 자동 제안. 사용자가 yes/no 선택.

**방법 3: 직접 편집 (비권장)**
프로젝트의 `.paper-metadata.json`에 `intellectual_ambition` 필드를 수동 설정:

```json
{
  "research_type": "theoretical",
  "intellectual_ambition": "critical"
}
```

3단계 값:
- `"incremental"` (기본): 분야 내 점진적 기여. Critical Mode 비활성
- `"critical"`: 비판적 시각 능동 지원. critical-companion·critical-lens-evaluator·Iconoclast 자동 체이닝
- `"paradigm-shifting"`: 패러다임 도전 전용. Hedging 관대, 비주류 인용 환영, Iconoclast를 주 심사자로 승격

### critical-questions.md 자동 업데이트 트리거 (ambition ≥ critical 시)

`"평가해줘"` 명령이 stage를 판별하여 critical-companion을 **자동 호출**:

| stage | critical-companion trigger | 생성 버전 |
|-------|--------------------------|---------|
| flow 단계 첫 평가 | `initial` | v1 (패러다임 의식·반대 사고) |
| Stage 1 리서치 완료 후 | `post-research` | v2 (소수 의견·지적 계보) |
| v1-draft 평가 | `post-draft` | v3 (대담성·정합성) |
| revised 평가 | `post-revision` | v4 (수정이 대담함을 깎았나) |
| final 직전 | `pre-final` | v5 (지도교수 심판·5년 후 독자) |

사용자는 stage 전환 시 자동으로 새 질문을 받음. 수동 업데이트는 `"질문 업데이트해줘"`.

### 사용자의 책임

critical-companion은 **질문만** 만들고 **답은 절대 제공하지 않습니다**. 사용자가 답을 쓰는 과정 자체가 새로운 관점의 발견입니다.

답변 작성 팁:
1. **짧게 쓰지 마세요** — 한 문장 답은 생각 안 한 것
2. **정합성 경고를 무시하지 마세요** — "v2에서 X라고 답했는데 원고는 Y"는 지적 자기 배신 신호
3. **답하지 않은 질문도 가치** — carry-over되며 "2회째 미답변"이 되면 회피 중임을 자기 진단

### 답변이 결과물에 자동 반영되는 메커니즘 🎯

가장 중요한 기능. 사용자가 답변을 **허공에 쓰는 것이 아니라** 시스템이 actionable하게 등록하여 모든 writing 에이전트가 참조합니다.

```
1. 사용자가 critical-questions.md의 답변 공간에 작성

2. 다음 중 하나가 trigger (답변 추출):
   a) "질문 업데이트해줘" (전체 critical-companion — 신규 질문 + 추출)
   b) "답변 반영해줘" (경량 — 추출만, 질문 갱신 안 함)
   c) "초안 작성해줘" / "Chapter X 수정해줘" 실행 시 자동 prehook

3. critical-companion이 답변을 파싱하여:
   - 사용자 원문을 그대로 인용
   - actionable 형식으로 변환 (대상 섹션, 행동, 완료 조건)
   - 현재 chapters/*와 대조하여 4-상태 분류:
     🟢 FULFILLED / 🟡 PARTIAL / 🔴 UNFULFILLED / ⚠️ CONFLICTING
   - critical-commitments.md에 기록

4. writing 에이전트가 commitment를 spec으로 사용:
   - writing-architect Phase 1 구조 설계 시 "이 commitment를 이 섹션에 구현" 명시
   - chapter-editor가 수정 중 commitment 충돌 여부 검증
   - flow-refiner가 UNFULFILLED를 flow 보강 제안으로 승격

5. 작업 완료 후 에이전트가 반영 결과 보고:
   ✅ [C-001] Luria 복원 → Section 2 pp.5-7에 추가
   🟡 [C-003] 급진적 steelman → 일부만 반영, 추가 수정 권장
   🔴 [C-004] 동양 철학 → 범위 부족으로 미반영

6. 사용자가 투명하게 확인:
   - 답변한 것이 어디에 반영되었는지
   - 무엇이 여전히 미이행인지
   - critical-commitments.md 파일을 열어 전체 상태 조회 가능
```

### 답변하지 않을 때

답변을 건너뛰어도 시스템은 계속 작동하지만:
- 해당 질문은 **carry-over**되어 다음 버전에도 등장
- 2회 연속 미답변 → 🔴 "회피 중일 수 있음" 표시
- critical-lens-evaluator가 미답변을 **축 6 soft cap**으로 반영 (예: 답변 없으면 C-1 점수 60점 상한)
- critical-commitments.md에 commitment 등록은 **안 됨** (답변이 명시적이어야만)

→ 답변 없음은 **미반영**으로 이어지며, 시스템이 그 사실을 숨기지 않는다.

### 8개 질문 카테고리

| # | 이름 | 핵심 질문 예시 |
|---|------|--------------|
| 1 | 패러다임 의식 | "분야가 당연시하는 가정 중 당신이 의심하는 것?" |
| 2 | 대담성 자가 점검 | "10배 더 대담해지면 주장이 어떻게 바뀌나?" |
| 3 | 소수 의견 복원 | "주류가 인용하지 *않는* 결정적 논문은?" |
| 4 | 반대 사고 | "당신 thesis의 정반대가 맞는다면 왜?" |
| 5 | 지적 계보 | "당신 논증 스타일은 누구와 가장 닮았나?" |
| 6 | 지도교수의 도전 | "지도교수 스타일로 상상할 때 어느 지점이 지적당하나?" |
| 7 | 5년 후 독자 | "5년 후 이 논문의 embarrassing할 부분은?" |
| 8 | 숨은 가정 | "당신 자신이 당연하게 받아들이는 것은?" |

### critical-lens-evaluator의 4축 (축 6)

| 기준 | 평가 내용 |
|------|---------|
| C-1 Paradigm Mapping | 분야의 dominant assumption을 명시 지명 |
| C-2 Fault-line Identification | 그 paradigm의 구조적 약점 |
| C-3 Bold Defense | Over-hedge 없는 대담한 주장 + falsifiability |
| C-4 Minority Evidence Recovery | 잊혀진 소수 의견·비주류 전통 복원 |

### peer-reviewer Iconoclast (Reviewer 4)

`ambition ≥ critical`일 때 자동 추가. 특징:
- **Timidity 지적**: "여기서 한 걸음 더 나아가야 한다"
- **Paradigm 내부 머무름 지적**: "비판한다면서 그 게임 안에 있다"
- **자기 배신 탐지**: critical-questions.md 답변과 원고 불일치 적발
- **대담성 등급**: ★★★★★ 5점 척도로 평가

---

## 📓 활동 로그 시스템 (Activity Log)

모든 주요 작업은 `projects/{PROJECT_NAME}/activity.log`에 한 줄씩 누적됩니다. 이 로그는 두 가지 용도로 활용됩니다:

### 용도 1: Time-travel (과거 시점 조회)

```
# 로그 파일에서 과거 라인 복사
[2026-04-10 14:30:15] ✅ 평가 완료 | v1-draft | chapters | 287/500 | ref:eval-003 | ...

# 채팅에 붙여넣고 요청
"[2026-04-10 14:30:15] ... | ref:eval-003 이 시점 work-plan 보여줘"
```

→ 시스템이 `ref:eval-003`을 파싱하여 `evaluations/archive/003-2026-04-10-v1-draft/work-plan.md` 출력.

**지원 패턴**:
- `ref:eval-NNN` — 평가 스냅샷
- `ref:ch-NNN` — chapters 스냅샷
- `ref:q-NNN` — critical-questions 버전
- `ref:commits-NNN` — critical-commitments 버전

**자동 복원은 제공 안 함** — 읽기 전용 조회만. 복원이 필요하면 수동 `cp`.

### 용도 2: 작업 추천 (`"작업 추천해줘"`)

```
🧠 "작업 추천해줘"
```

시스템이 최근 14일 로그를 분석하여:
- **P1 차단 요소** (stale, dangling, UNFULFILLED commitment)
- **P2 자연 다음 단계** (stage 흐름 기준)
- **P3 장기 정체 해소** (3일+ 미활동 시 재개)
- **P4 선택적 강화** (방법론, gap 등)

각 추천에 **근거 로그 라인** 동반. 블랙박스 추천 금지.

### 로그 포맷

```
[YYYY-MM-DD HH:MM:SS] ACTION | STAGE | TARGET | RESULT | ref:ID | agents:A,B | key=value
```

실제 예시:
```
[2026-04-23 14:30:15] ✅ 평가 완료 | v1-draft | chapters | 287/500 (+32) | ref:eval-003 | flow-evaluator,critical-lens | ambition=critical commits=3/5
```

- 앞 4 필드 고정 (timestamp, action, stage, target)
- 뒤 필드는 선택적 (result, ref, agents, meta)
- 빈 필드는 `-`로 표시

### 아키텍처: 4계층 방어

활동 로그는 **누락 방지를 위한 4계층 구조**로 기록됩니다:

| 계층 | 실행 주체 | 신뢰도 | 트리거 |
|------|----------|-------|-------|
| 1. UserPromptSubmit hook | Claude Code harness | 100% | 매 사용자 입력 |
| 2. Stop hook | Claude Code harness | 100% | 매 turn 종료 |
| 3. PostToolUse(Bash) hook | Claude Code harness | 100% | 핵심 스크립트 호출 |
| 4. MD 지시 (fallback) | Claude | 60-80% | SKILL.md 명령 완료 시 |

Layer 1-3은 **harness-level**이라 LLM 상태와 무관하게 실행. Layer 4는 보조 안전망. 이중 덮어쓰기로 **누락률을 실질적 0으로 수렴**.

### Hooks 설정 파일

```
.claude/settings.json
```

프로젝트 로컬(research-agent 루트) — git 추적되어 팀원 간 공유.

### Hooks 끄는 법

`.claude/settings.json`의 `hooks` 섹션을 지우거나 빈 객체로 설정:
```json
{
  "hooks": {}
}
```

끄면 Layer 1-3 비활성, Layer 4(MD 지시)만 작동. 로그는 여전히 쌓이지만 누락 가능성 증가.

### 로그 파일 관리

- **위치**: `projects/{PROJECT_NAME}/activity.log` (가시 파일)
- **append-only**: 수정·삭제 금지 (사용자가 수동 편집해도 시스템은 존중)
- **로테이션**: 없음 (프로젝트 수명 기준 ~2000 라인 예상)
- **gitignore**: `projects/`가 이미 ignore 대상

### 수동 조작

```bash
# 특정 프로젝트 로그 확인
cat projects/CDEA/activity.log

# 최근 N일치만
python3 scripts/activity_log.py recent CDEA 7

# 추천 JSON (디버그)
python3 scripts/activity_log.py recommend CDEA

# 수동 append (Claude가 하는 일을 직접)
python3 scripts/activity_log.py append CDEA "수동 로그" "result=test"
```

### 주의사항

- **hook이 작동 안 한다면**: `.claude/settings.json`이 존재하는지, `$CLAUDE_PROJECT_DIR`이 올바른지 확인
- **로그 파싱 오류**: 수동 편집으로 포맷이 깨진 라인은 skip (경고만 출력)
- **다중 프로젝트**: 가장 최근 수정된 프로젝트로 로그가 라우팅됨. 의도와 다르면 작업 전 해당 프로젝트 폴더를 `touch`로 mtime 갱신

---

## 🔐 권한 자동 승인 (Permissions)

Claude Code의 반복적 "yes" 확인 prompt를 줄이기 위해 이 프로젝트는 **안전한 명령 패턴을 사전 승인**합니다.

### 작동 방식

프로젝트 루트의 `.claude/settings.json`에 `permissions` 섹션이 있으며, clone하는 모든 사용자에게 자동 적용됩니다.

```json
{
  "permissions": {
    "allow": [ "Bash(python3 scripts/*)", "Bash(git add *)", ... ],
    "deny": [ "Bash(rm -rf *)", "Bash(git push --force*)", ... ]
  }
}
```

### ✅ 사전 승인 범위 (prompt 없음)

- **프로젝트 스크립트**: `python3 scripts/sync_state.py`, `activity_log.py`, `extract_metadata.py`
- **Git 기본**: add / commit / push / status / diff / log / show / branch / remote
- **파일 읽기·탐색**: ls / cat / head / tail / grep / sed -n / awk / sort
- **파일 조작**: mkdir / touch / cp / mv / chmod
- **Consensus MCP**: `mcp__consensus__search` 포함 전체
- **패키지 설치**: `npm install claude-code`, `pip3 install`

### 🚫 명시적 차단 (deny)

다음은 **실수로도 실행되지 않도록** deny 목록에 등록:
- `rm -rf *`, `rm -r /*`
- `git push --force*`, `git push -f *`
- `git reset --hard *`
- `git checkout -- *` (변경사항 폐기)
- `git clean -*`

deny는 `--dangerously-skip-permissions` flag로도 우회되지 않습니다.

### 사용자 개인 설정

자신만의 추가 허용·거부 패턴은 `.claude/settings.local.json`에 작성. 이 파일은 `.gitignore` 대상이라 공유되지 않습니다.

```json
{
  "permissions": {
    "allow": [ "Bash(my-custom-command *)" ],
    "deny": []
  }
}
```

### 전체 무제한 모드 (⚠️ 비권장)

특수한 경우 모든 권한 prompt를 생략:
```bash
claude --dangerously-skip-permissions
```
`rm -rf` 같은 위험 명령도 질문 없이 실행됨. **신뢰된 환경에서만** 사용.

---

## 📁 파일 구조와 역할

### 사용자가 작성·관리하는 파일

| 파일 | 역할 |
|------|------|
| `flow.md` | **사용자의 줄글 플랜**. 모든 워크플로우의 기준 문서 |
| `papers/candidates/*.pdf` | 다운로드한 PDF 임시 보관 (처리되면 collected/로 이동) |

### 시스템이 자동 생성하는 파일

| 파일 | 생성 시점 | 역할 |
|------|----------|------|
| `FLOW-TEMPLATE.md` | 프로젝트 생성 시 | 줄글 작성 가이드 (수정 금지) |
| `.sync-state.json` | 프로젝트 생성 시 | **아티팩트 의존성·버전 추적** (sync 아키텍처의 핵심) |
| `critical-questions.md` | Stage 마일스톤 (ambition ≥ critical) | **사용자가 답변하는 Socratic 질문** — 답변 없이는 평가 불완전 |
| `critical-questions.archive/` | 매 critical-companion 재실행 | **질문·답변 버전 히스토리** (지적 여정 기록) |
| `evaluations/latest/critical-lens-report.md` | `"비판적 시각 평가해줘"` 또는 ambition ≥ critical 자동 | 축 6 심층, paradigm 평가 + 답변 정합성 점검 |
| `evaluations/latest/evaluation.md` | "평가해줘" | 5축 점수 + 감점 사유 + delta |
| `evaluations/latest/work-plan.md` | "평가해줘" | 4단계별 작업 지시서 (🔄 REANALYZE + 🔍 HUNT 체크박스) |
| `evaluations/latest/claim-extraction.md` | "평가해줘" (prose flow) | 문장 단위 주장 테이블 (MATCHED / UNMATCHED-INTERNAL / UNMATCHED-EXTERNAL) |
| `evaluations/latest/originality-report.md` | "평가해줘" (선택) | 축 4 심층, Novelty Delta Map |
| `evaluations/latest/concept-clarity-report.md` | "평가해줘" (선택) | 축 5 심층, 정의 감사 테이블 |
| `evaluations/archive/{NNN}-{date}-{stage}/` | 매 평가 실행 직전 | 이전 평가 스냅샷 (delta 추적용) |
| `papers/consensus-results.md` | "작업 시작해줘" | HUNT 검색 결과 누적 |
| `papers/collected/*.pdf` | "새 논문 처리해줘" | 처리 완료 PDF |
| `papers/analyzed/*.md` | "새 논문 처리해줘" / "논문 재분석해줘" | paper-analyst 심층 분석 (v1, v2, ... append) |
| `papers/archived/` | "논문 제거해줘" | 제거된 PDF 보관 (복구 가능) |
| `papers/archived/analyzed/` | "논문 제거해줘" | 제거된 논문의 분석 리포트 보관 |
| `chapters/0N-*.md` | "초안 작성해줘" | 섹션별 초안 |
| `chapters/archive/{NNN}-{date}-{trigger}/` | "초안 작성해줘"·"Chapter X 수정해줘" 실행 직전 | **구버전 chapters 자동 스냅샷** (데이터 손실 방지). trigger 예: `pre-redraft`, `ch2-edit` |
| `final/complete-draft.md` | "초안 작성해줘" / "최종 통합해줘" | 통합본 |
| `final/complete-draft.docx` | "초안 작성해줘" / "최종 통합해줘" | Word 문서 |
| `.paper-metadata.json` | "새 논문 처리해줘" | 논문 메타데이터 DB |
| `gaps-analysis.md` | "gap 분석해줘" | Gap 탐색 결과 |

---

## 📖 명령어 레퍼런스

### 프로젝트 관리

| 명령 | 동작 |
|------|------|
| `"[이름] 프로젝트 만들어줘"` | 프로젝트 폴더 + 빈 flow.md + evaluations 구조 생성 |

### 평가

| 명령 | 동작 | Archive? |
|------|------|---------|
| 🎯 `"평가해줘"` | 전체 5축 평가 + claim-extraction + work-plan 생성 | ✅ 스냅샷 생성 |
| 🔍 `"레퍼런스 점검해줘"` | 축 1 전용 경량 재평가 | ❌ (경량) |
| `"독창성 평가해줘"` | 축 4 단독 심층 | originality-report.md만 갱신 |
| `"정의 정밀도 평가해줘"` | 축 5 단독 심층 | concept-clarity-report.md만 갱신 |

### 리서치 (Stage 1)

| 명령 | 동작 |
|------|------|
| `"작업 시작해줘"` | work-plan.md의 🔄 REANALYZE 먼저 → 🔍 HUNT를 Consensus에 순차 투입 |
| `"새 논문 처리해줘"` | candidates/의 PDF 메타데이터 추출 + paper-analyst Mode A 분석 + sync 갱신 |
| 🔄 `"논문 재분석해줘"` | 기존 PDF를 새 flow 각도로 재스캔 (paper-analyst Mode B, v2 append) |
| 🗑 `"논문 제거해줘: {파일}"` | archived/로 안전 이동 + dangling citation 자동 탐지 |
| 📝 `"flow 업데이트해줘"` | 새 논문 반영한 flow.md 보강 제안 (축 3·4 강화) |

### 작성·수정 (Stage 2-3)

| 명령 | 동작 |
|------|------|
| `"초안 작성해줘"` | writing-architect 구조 설계(승인 필요) → 초안 생성 |
| `"Chapter X 수정해줘: [수정 내용]"` | 해당 챕터 수정 + 일관성 체크 + citation-auditor 자동 감사 |

### 최종 완성 (Stage 4)

| 명령 | 동작 |
|------|------|
| 📦 `"최종 통합해줘"` | chapters/*.md 병합 + docx 재생성 + sync 갱신 |
| `"리뷰 체크해줘"` | peer-reviewer Mode A — 가상 심사 시뮬레이션 |
| `"리뷰 답변 도와줘: [리뷰 전문]"` | peer-reviewer Mode B — 답변 전략 + 초안 |

### Sync 관리 (언제든)

| 명령 | 동작 |
|------|------|
| 🔄 `"sync 확인해줘"` | 모든 아티팩트 간 정합성 점검 + 순차 해결 가이드 |
| 🔄 `"논문 재분석해줘"` | flow 변경 시 기존 PDF 재스캔 |
| 🗑 `"논문 제거해줘: {파일}"` | 안전 제거 + 전파 처리 |

### 보조

| 명령 | 동작 |
|------|------|
| `"gap 분석해줘"` | 연구 Gap 5종 탐색 |
| `"방법론 추천해줘"` | 3가지 방법론 비교 표 |
| `"방법론 검증해줘"` | 선택한 방법론 타당성 심사 |

### 권장 흐름 전체도 (sync 통합)

```
프로젝트 생성 → .sync-state.json 초기화
  → flow.md 자유 줄글 작성
  → 🎯 평가해줘 (1차)
     ├── sync 체크 (시작 gate)
     ├── claim-extractor → INTERNAL / EXTERNAL 분류
     ├── flow-evaluator → 5축 평가
     ├── work-plan.md: 🔄 REANALYZE + 🔍 HUNT
     └── archive/001-{date}-flow/

  → [Stage 1]
     ├── 작업 시작해줘
     │   ├── 🔄 REANALYZE 먼저 (내부 재활용 우선)
     │   └── 🔍 HUNT (Consensus 신규 검색)
     ├── PDF 다운로드 (사용자)
     └── 새 논문 처리해줘 (paper-analyst Mode A + sync 갱신)

  → 🔍 레퍼런스 점검해줘 (축 1 경량)
  → (선택) 📝 flow 업데이트해줘 (flow-refiner)

  → [Stage 2] 초안 작성해줘
     ├── analyzed/*.md 섹션별 인용 다발 우선
     ├── 부족 시 on-demand PDF 접근
     └── sync 갱신 (각 챕터)

  → 🎯 평가해줘 (2차) → archive/002-{date}-v1-draft/

  → [Stage 3] Chapter X 수정해줘 (반복, citation-auditor PDF 감사)
  → 🎯 평가해줘 (3차) → archive/003-{date}-revised/

  → [Stage 4]
     ├── 📦 최종 통합해줘 (final/* 재빌드)
     ├── 리뷰 체크해줘 (peer-reviewer)
     └── 🎯 평가해줘 (최종) → archive/004-{date}-final/

언제든 병행:
  🔄 sync 확인해줘 (상태 점검)
  🔄 논문 재분석해줘 (flow 각도 변경 반영)
  🗑 논문 제거해줘: {파일} (안전 제거 + 전파)
```

---

## 💡 작성 팁

### flow.md 작성

- **RQ와 Thesis는 반드시 한 문장씩** — "연구 질문은 ~이다", "핵심 주장은 ~이다"로 명시하면 claim-extractor가 확실히 인식
- **Section 구조를 자기 지시적으로 녹여 쓰기** — "Section 1에서는 ~을 다룬다" 식으로 써두면 시스템이 섹션 구조를 자동 복원
- **저자 기여 vs 선행 연구 요약 구분** — "본 에세이는 ~을 제안한다" (저자) vs "Kroupin (2025)는 ~을 주장했다" (선행)

### claim-extractor 결과 활용

- **Over-claim 경고를 무시하지 마세요** — 심사자 공격 1순위
- **모호 분류(🟠)는 사용자 판단** — 저자의 해석이면 E로, 근거가 있으면 A로
- **UNMATCHED 건은 HUNT 과제로 자동 이어짐** — 실행 순서만 따르면 됨

### 평가 점수 해석

| 구간 | 의미 | 권장 조치 |
|------|------|----------|
| 90+ 🟢 | Accept 수준 | 다음 Stage 진입 |
| 70-89 🟡 | Minor Revision | 해당 축 작업 지시 실행 |
| 70 미만 🔴 | Major Revision | 해당 축 근본 재검토 필요 |

전체 평균이 **450/500 이상**이면 제출 준비 완료.

### Archive 스냅샷 활용

`evaluations/archive/`의 과거 평가를 열어보면 각 수정이 어느 축을 몇 점 올렸는지 확인 가능합니다. 논문 투고 포트폴리오나 연구 일지로도 활용할 수 있습니다.

---

## 🆘 트러블슈팅

### 설치 문제

**`claude: command not found`**
```bash
npm install -g @anthropic-ai/claude-code
```
Node.js가 없다면: `brew install node`

**스킬이 인식 안 됨**
```bash
rm ~/.claude/skills/user/research-agent
bash install.sh
```

**PyPDF2 오류**
```bash
pip3 install pypdf2 --break-system-packages
```

### Consensus MCP 문제

**"Consensus 연결 끊김"**
```
claude
> /mcp → consensus 선택 → Authenticate
```

**"검색당 3개 결과만 반환됨"**
Consensus 무료 계정 로그인 안 된 상태. 브라우저에서 [consensus.app/sign-up](https://consensus.app/sign-up/?utm_source=claude_code&auth=claude_code) 가입 후 `/mcp`로 재인증.

**Rate limit 에러**
`"작업 시작해줘"` 실행 중 자동으로 30초 대기 후 재시도하므로 그대로 두세요.

### 평가·작업 관련

**"flow.md에 RQ/Thesis가 없다"고 나옴**
줄글 중에 연구 질문과 핵심 주장을 한 문장씩 명시하세요. "~이다" 같은 단정 형식 권장.

**"평가가 너무 관대하다"**
flow-evaluator는 Top-tier 저널 엄격도로 설정되어 있습니다. 만약 점수가 지속적으로 높다면 실제로 좋은 상태일 수 있으나, 심층 평가(`"독창성 평가해줘"`, `"정의 정밀도 평가해줘"`)를 추가로 돌려보세요.

**"HUNT 과제가 너무 많다"**
첫 평가 시 UNMATCHED가 수십 건 나오는 것은 정상입니다. `"작업 시작해줘"` 한 번으로 전량 일괄 처리 가능합니다.

**"citation-auditor가 over-claim을 지적했다"**
원문 PDF를 직접 확인하고, 주장 강도를 약화시키거나(predict → suggest) 더 강한 근거 논문으로 교체하세요.

### 파일 관련

**"chapters/ 폴더가 비어있다"**
`"초안 작성해줘"`를 아직 실행하지 않았거나 writing-architect의 구조 승인 단계에서 중단되었을 가능성. 다시 실행하여 Phase 1 구조를 승인하세요.

**"이전 평가를 다시 보고 싶다"**
`evaluations/archive/{NNN}-{date}-{stage}/` 폴더를 열어보세요.

**"projects/ 폴더가 git에 올라간다"**
`.gitignore`에 `projects/`가 등록되어 있어야 합니다. 기본 설치로 자동 설정됩니다.

### Sync 관련

**"sync 확인해줘 결과가 이상하다"**
`.sync-state.json`이 손상되었을 가능성. 수동으로 복구:
```bash
# 프로젝트의 현재 상태를 기준으로 재초기화
python3 scripts/sync_state.py init {프로젝트명}
# 이후 기존 analyzed, chapters에 대해 update-* 명령을 한 번씩 실행
```

**"dangling citation 경고가 떴다"**
삭제된 논문(archived/로 이동)을 챕터가 여전히 인용 중. `"Chapter X 수정해줘: {삭제된 저자} 인용 제거 또는 대체"`로 수정하세요.

**"챕터가 구버전 논문 분석 기반이라고 경고"**
flow 변경 후 `"논문 재분석해줘"`를 돌려 v2가 생겼는데 챕터는 v1 기반. `"Chapter X 수정해줘: 새 분석 반영"`으로 업데이트.

**"final 파일이 stale이라고 뜬다"**
챕터 수정 후 통합본 재빌드 필요. `"최종 통합해줘"` 실행.

**"논문을 실수로 제거했다"**
`papers/archived/`에서 `collected/`로 파일 복구:
```bash
mv projects/{프로젝트}/papers/archived/{파일}.pdf \
   projects/{프로젝트}/papers/collected/
mv projects/{프로젝트}/papers/archived/analyzed/{파일}-analysis.md \
   projects/{프로젝트}/papers/analyzed/
python3 scripts/sync_state.py update-paper {프로젝트} {파일}.pdf
```

**"초안 재작성했는데 구버전이 더 좋았다"**
`chapters/archive/`에서 자동 스냅샷된 구버전 복구:
```bash
# 최신 pre-redraft 스냅샷 찾기
ls projects/{프로젝트}/chapters/archive/ | grep pre-redraft

# 예: 003-2026-04-22-pre-redraft 복구
cp projects/{프로젝트}/chapters/archive/003-2026-04-22-pre-redraft/*.md \
   projects/{프로젝트}/chapters/
```

**"Chapter X 수정을 롤백하고 싶다"**
```bash
# 해당 수정 직전 스냅샷 찾기
ls projects/{프로젝트}/chapters/archive/ | grep ch2-edit

# 단일 챕터 복구 (가장 최근 스냅샷 기준)
cp projects/{프로젝트}/chapters/archive/007-2026-04-23-ch2-edit/02-background.md \
   projects/{프로젝트}/chapters/
```

---

## 📄 License

MIT
