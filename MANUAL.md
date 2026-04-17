# Research Agent — 사용자 매뉴얼

Top-tier 저널 심사 엄격도의 **5축 냉정 평가**를 중심으로, 줄글(prose) flow 작성부터 최종 완성까지 이끌어주는 AI 연구 관리 시스템의 사용 가이드입니다.

> 설치가 되어 있지 않다면 먼저 [README.md](./README.md)를 참고하세요.

---

## 목차

1. [시스템 철학](#-시스템-철학)
2. [전체 User Journey](#-전체-user-journey)
3. [5축 평가 기준 상세](#-5축-평가-기준-상세)
4. [서브 에이전트 시스템](#-서브-에이전트-시스템)
5. [파일 구조와 역할](#-파일-구조와-역할)
6. [명령어 레퍼런스](#-명령어-레퍼런스)
7. [작성 팁](#-작성-팁)
8. [트러블슈팅](#-트러블슈팅)

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

---

## 🗺 전체 User Journey

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
├── flow.md                   ← 당신이 자유 줄글로 작성
├── FLOW-TEMPLATE.md          ← 작성 가이드 (수정 금지)
├── evaluations/
│   ├── latest/               ← 평가 결과 (최신본)
│   └── archive/              ← 평가 스냅샷 히스토리
├── papers/
│   ├── candidates/           ← 다운로드한 PDF 임시 보관
│   ├── collected/            ← 처리 완료된 PDF
│   └── analyzed/             ← paper-analyst 분석 리포트
├── chapters/                 ← 초안 섹션별 파일
├── final/                    ← 통합본 + docx
└── .paper-metadata.json
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

### 평가 전용 (4개)

| 에이전트 | 역할 | 호출 시점 |
|---------|------|----------|
| **flow-evaluator** | 5축 오케스트레이터, work-plan.md 생성 | "평가해줘" |
| **claim-extractor** | 문장 단위 주장 추출·분류·HUNT 생성 | flow-evaluator가 자동 호출 |
| **originality-evaluator** | 축 4 심층 평가, Delta Map 작성 | flow-evaluator 자동 / "독창성 평가해줘" 단독 |
| **concept-clarity-evaluator** | 축 5 심층 평가, 정의 감사 테이블 | flow-evaluator 자동 / "정의 정밀도 평가해줘" 단독 |

### 생성·수정 (3개)

| 에이전트 | 역할 | 호출 시점 |
|---------|------|----------|
| **writing-architect** | 논증 구조 설계 → 초안 작성, flow 업데이트 제안 | "초안 작성해줘", "flow 업데이트해줘" |
| **citation-auditor** | 인용 accuracy 감사, APA 형식 체크 | "Chapter X 수정해줘" (자동) |
| **paper-analyst** | 논문 심층 분석 (요약·기여·한계·관련성) | "새 논문 처리해줘" (자동) |

### 보조 (3개, 수동 호출)

| 에이전트 | 역할 | 호출 시점 |
|---------|------|----------|
| **gap-finder** | 방법론·응용·데이터·이론·시간 Gap 5종 탐색 | "gap 분석해줘" |
| **methodology-advisor** | 방법론 추천(3가지 비교) 또는 검증 | "방법론 추천/검증해줘" |
| **peer-reviewer** | 심사 시뮬레이션(Mode A) 또는 대응(Mode B) | "리뷰 체크해줘", "리뷰 답변 도와줘" |

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
| `evaluations/latest/evaluation.md` | "평가해줘" | 5축 점수 + 감점 사유 + delta |
| `evaluations/latest/work-plan.md` | "평가해줘" | 4단계별 작업 지시서 (HUNT 체크박스 포함) |
| `evaluations/latest/claim-extraction.md` | "평가해줘" (prose flow) | 문장 단위 주장 테이블 |
| `evaluations/latest/originality-report.md` | "평가해줘" (선택) | 축 4 심층, Novelty Delta Map |
| `evaluations/latest/concept-clarity-report.md` | "평가해줘" (선택) | 축 5 심층, 정의 감사 테이블 |
| `evaluations/archive/{NNN}-{date}-{stage}/` | 매 평가 실행 직전 | 이전 평가 스냅샷 (delta 추적용) |
| `papers/consensus-results.md` | "작업 시작해줘" | HUNT 검색 결과 누적 |
| `papers/collected/*.pdf` | "새 논문 처리해줘" | 처리 완료 PDF |
| `papers/analyzed/*.md` | "새 논문 처리해줘" | paper-analyst 심층 분석 |
| `chapters/0N-*.md` | "초안 작성해줘" | 섹션별 초안 |
| `final/complete-draft.md` | "초안 작성해줘" | 통합본 |
| `final/complete-draft.docx` | "초안 작성해줘" | Word 문서 |
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
| `"작업 시작해줘"` | work-plan.md의 HUNT 체크박스를 Consensus에 순차 투입 |
| `"새 논문 처리해줘"` | candidates/의 PDF 메타데이터 추출 + paper-analyst 분석 |
| 📝 `"flow 업데이트해줘"` | 새 논문 반영한 flow.md 보강 제안 (축 3·4 강화) |

### 작성·수정 (Stage 2-3)

| 명령 | 동작 |
|------|------|
| `"초안 작성해줘"` | writing-architect 구조 설계(승인 필요) → 초안 생성 |
| `"Chapter X 수정해줘: [수정 내용]"` | 해당 챕터 수정 + 일관성 체크 + citation-auditor 자동 감사 |

### 최종 완성 (Stage 4)

| 명령 | 동작 |
|------|------|
| `"리뷰 체크해줘"` | peer-reviewer Mode A — 가상 심사 시뮬레이션 |
| `"리뷰 답변 도와줘: [리뷰 전문]"` | peer-reviewer Mode B — 답변 전략 + 초안 |

### 보조

| 명령 | 동작 |
|------|------|
| `"gap 분석해줘"` | 연구 Gap 5종 탐색 |
| `"방법론 추천해줘"` | 3가지 방법론 비교 표 |
| `"방법론 검증해줘"` | 선택한 방법론 타당성 심사 |

### 권장 흐름 전체도

```
프로젝트 생성
  → flow.md 자유 줄글 작성
  → 🎯 평가해줘 (1차 전체)
     └── archive/001-{date}-flow/ 스냅샷

  → [Stage 1]
     ├── 작업 시작해줘 (HUNT 자동 검색)
     ├── PDF 다운로드 (사용자)
     └── 새 논문 처리해줘 (paper-analyst 분석)

  → 🔍 레퍼런스 점검해줘 (축 1 경량)
  → (선택) 📝 flow 업데이트해줘

  → [Stage 2] 초안 작성해줘
  → 🎯 평가해줘 (2차)
     └── archive/002-{date}-v1-draft/

  → [Stage 3] Chapter X 수정해줘 (반복)
  → 🎯 평가해줘 (3차)
     └── archive/003-{date}-revised/

  → [Stage 4] 리뷰 체크해줘
  → 🎯 평가해줘 (최종)
     └── archive/004-{date}-final/
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

---

## 📄 License

MIT
