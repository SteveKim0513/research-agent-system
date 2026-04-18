# PRINCIPLES.md

**이 시스템이 "좋은 논문"을 쓰기 위해 고려하는 모든 것**

이 문서는 Research Agent System의 **설계 철학과 학술 글쓰기 원칙**을 정리합니다. `README.md`가 "무엇을 할 수 있는가", `MANUAL.md`가 "어떻게 쓰는가"를 다룬다면, 이 문서는 **"왜 이렇게 설계되었는가"**를 다룹니다.

학부~박사 과정 연구자가 이 시스템을 쓸 때 "왜 5축인가", "왜 이 순서로 에이전트가 발동하는가", "왜 줄글 flow인가"에 대한 답을 여기서 찾을 수 있습니다.

---

## 📑 목차

1. [들어가며 — 이 문서가 필요한 이유](#-들어가며)
2. ["좋은 논문"이란 무엇인가](#-좋은-논문이란-무엇인가)
3. [축 1: 레퍼런스 충실도의 4대 원칙](#-축-1-레퍼런스-충실도)
4. [축 2: 논리 전개 완성도의 4대 원칙](#-축-2-논리-전개-완성도)
5. [축 3: 반박/강화 논리의 4대 원칙](#-축-3-반박강화-논리)
6. [축 4: 독창성·기여도의 4대 원칙](#-축-4-독창성기여도)
7. [축 5: 구성개념 정의 정밀도의 4대 원칙](#-축-5-구성개념-정의-정밀도)
8. [학술 글쓰기의 공통 원칙](#-학술-글쓰기의-공통-원칙)
9. [시스템이 방지하는 전형적 실수 13가지](#-시스템이-방지하는-전형적-실수-13가지)
10. [반복과 진화: 왜 평가→수정→재평가 루프인가](#-반복과-진화)
11. [시스템 설계 철학](#-시스템-설계-철학)
12. [에이전트별 원칙 매핑](#-에이전트별-원칙-매핑)
13. [학술 전통과 근거 문헌](#-학술-전통과-근거-문헌)

---

## 🌱 들어가며

학술 글쓰기는 단순한 "쓰기"가 아니라 **여러 층위의 품질 기준을 동시에 만족시키는 설계 작업**입니다. 좋은 논문은:

- 모든 주장에 **정확한 인용**이 붙어 있고 (축 1)
- 논증이 **끊김 없이 전개**되며 (축 2)
- 가장 강한 반론에도 **방어되고** (축 3)
- 분야에 **구체적 기여**를 하며 (축 4)
- 핵심 용어가 **정밀하게 정의**됩니다 (축 5)

이 다섯 가지를 **동시에** 만족시키는 일은 매우 어려워서, 대다수 대학원생·연구자가 어느 하나를 놓치고 심사에서 만나는 평가:

- "All claims require citations." (축 1)
- "The argument doesn't flow." (축 2)
- "The authors fail to address obvious counter-arguments." (축 3)
- "The contribution is unclear." (축 4)
- "Key terms are used inconsistently." (축 5)

이 시스템은 이 다섯 가지 실패 모드를 **체계적으로 방지**하도록 설계되었습니다. 모든 에이전트·명령·데이터 구조가 궁극적으로 이 목적을 위해 존재합니다.

---

## 📐 "좋은 논문"이란 무엇인가

### 5축 평가의 출처

이 시스템의 5축은 임의로 만든 것이 아니라 **top-tier 저널(Nature, Psychological Review, PNAS 등) 심사 가이드**에서 반복적으로 나타나는 평가 기준을 종합한 것입니다:

| 축 | 대응되는 심사 기준 (전형적 표현) |
|---|----------------------------|
| 1 | "Adequate and accurate citation of relevant literature" |
| 2 | "Logical coherence and clarity of argumentation" |
| 3 | "Engagement with competing views / addressing limitations" |
| 4 | "Novelty, significance, and contribution to the field" |
| 5 | "Clarity and precision of key constructs" |

### 왜 5축인가? 왜 3도 7도 아닌가

- **3축 이하**: 너무 거칠어 구체적 작업 지시 생성이 어려움
- **7축 이상**: 서로 중첩되어 감점 사유 귀속이 불명확
- **5축**: 독립적이면서 상호보완적. 하나씩 개선해도 다른 축이 덜 움직이는 **직교성** 유지

### 심사 판정 매핑

시스템이 사용하는 가상 심사 판정은 학술지 표준을 따릅니다:

| 종합 점수 | 판정 | 의미 |
|----------|------|------|
| 450-500 | Accept | 제출 가능 |
| 350-449 | Minor Revision | 소폭 수정 후 제출 |
| 250-349 | Major Revision | 대폭 수정 필요 |
| <250 | Reject | 근본 재설계 필요 |

---

## 📚 축 1: 레퍼런스 충실도

### 왜 이 축이 존재하는가

학술 글쓰기에서 "인용 없는 주장"은 **저자의 개인적 의견**일 뿐입니다. 분야의 지식 체계에 연결되지 않은 글은 **저널에 실릴 수 없습니다**. 또한 부정확한 인용은 **학술 부정행위**로 간주될 수 있어 논문이 철회될 수 있습니다.

### 4대 하위 원칙

#### 1-1. Coverage — 모든 경험/기술적 주장에 인용

**원칙**: 사실 관계를 다루는 모든 문장은 출처를 가져야 한다. 단, 저자의 novel claim (이 논문의 기여)은 예외.

**구현**:
- `claim-extractor`가 문장을 5종으로 분류 (A 경험 / B 기술 / C 차용 정의 / D 반론 / E 저자 확장 / F 저자 기여 / G 연결)
- A/B/C/D는 NEEDS_CITATION, E는 OPTIONAL, F/G는 NO_CITATION
- 빠진 인용을 HUNT·REANALYZE 과제로 자동 생성

#### 1-2. Accuracy — 인용이 실제로 주장을 뒷받침

**원칙**: "Smith (2023) proves X"로 썼다면 Smith (2023)가 실제로 X를 증명해야 한다. 상관관계를 인과로 말하는 건 흔한 over-claim이며, 심사자 1순위 공격 대상.

**구현**:
- `paper-analyst`가 각 논문의 "조건·한계" 필드를 명시
- `writing-architect`가 이 필드를 준수
- `citation-auditor`가 **PDF 원문과 대조**하여 over-claim·misattribution 탐지
- 평가 단계별 자동 체이닝: v1-draft(30% 샘플) / revised(전량) / final(전량 + new-error diff)

#### 1-3. Authority & Recency — 세미널 + 최신 논문 균형

**원칙**: 분야의 세미널 논문은 피할 수 없다 (못 알고 쓰면 심사자 즉시 간파). 동시에 최근 3-5년 반론·확장 문헌을 빠뜨리면 시대에 뒤처진 글이 된다.

**구현**:
- Consensus MCP 검색 결과의 **저널 등급·인용 수·발행 연도** 메타데이터 활용
- `flow-evaluator` 축 1-3 채점에서 세미널 누락·최신 부재 모두 감점
- `originality-evaluator`의 Delta Map이 "유사 선행 연구 TOP 3"를 명시적으로 요구하여 누락 방지

#### 1-4. Balance — Disconfirming evidence 포함

**원칙**: 자기 주장을 뒷받침하는 문헌만 인용하는 것은 **confirmation bias**. 반대 증거를 **인정하고 답변**하지 않으면 심사자가 그 반대 증거로 공격.

**구현**:
- `claim-extractor`가 Over-claim / Under-claim 경고 생성
- `gap-finder`가 방법론·응용·데이터·이론·시간 5종 Gap 탐색으로 사각지대 노출
- `peer-reviewer` Mode A가 심사자 페르소나로 "이 주장에 대한 반대 증거는?" 시뮬레이션

---

## 🔗 축 2: 논리 전개 완성도

### 왜 이 축이 존재하는가

심사자가 읽는 중 "갑자기 왜 이 이야기로 넘어가지?"라는 생각이 들면 그 논문은 **reject** 방향으로 기울어집니다. 논증이 A→B→C→D→결론으로 **끊김 없이** 이어져야 합니다.

### 4대 하위 원칙

#### 2-1. Argument Chain — Premise → Evidence → Warrant → Claim

**원칙**: 각 주장은 **전제 → 증거 → 정당화(warrant) → 결론**의 사슬을 완결해야 한다. Warrant(왜 이 증거가 이 주장을 뒷받침하는가)를 생략하는 것이 가장 흔한 실수.

**구현**:
- `writing-architect` Phase 1에서 각 문단의 "주장 → 근거 → 연결"을 명시적으로 설계
- `flow-evaluator`가 warrant 누락을 축 2-1 감점으로 처리
- `chapter-editor`는 기존 사슬을 보존하며 수정

#### 2-2. Section Transition — 섹션 간 논리적 다리

**원칙**: Section N의 결론이 Section N+1의 전제로 정확히 이어져야 한다. "Section 2는 X를 보였다. **따라서 이제 Y를 다루기 위해** Section 3으로 넘어간다" 형식의 transition 문장 필수.

**구현**:
- `writing-architect` Phase 1 설계 시 각 섹션에 "다음 섹션 연결" 명시
- `flow-evaluator`가 섹션 간 Logic jump를 축 2-2 감점으로 지적
- `chapter-editor`가 수정 후 자동 일관성 체크 (Phase 4)

#### 2-3. Thesis Alignment — 모든 단락이 thesis에 기여

**원칙**: 각 문단은 전체 thesis에 **구체적으로 어떻게 기여하는지** 물을 때 답이 있어야 한다. 답이 없으면 그 문단은 탈선.

**구현**:
- `flow.md` 작성 시 **thesis를 한 문장으로 명시** 강제 (claim-extractor가 탐지)
- `flow-evaluator`가 각 문단에 대해 "이 문단이 thesis에 기여하는가?" 체크
- 탈선 문단은 축 2-3 감점 + 삭제 권고

#### 2-4. Scope Closure — RQ에 실제로 답함

**원칙**: Research Question이 "어떻게 X?"인데 결론이 "왜 X?"만 답하면 scope error. RQ를 시작 섹션에 명시했으면 마지막 섹션에서 **같은 형태로** 답해야 한다.

**구현**:
- `claim-extractor`가 prose flow에서 RQ를 명시적으로 추출
- `flow-evaluator`의 "Mirror Introduction" 원칙 (Conclusion 섹션 전략)
- 평가 시 RQ와 Conclusion이 동일 subject/verb 구조인지 체크

---

## 🛡 축 3: 반박/강화 논리

### 왜 이 축이 존재하는가

Top-tier 저널 심사자의 핵심 태도는 "이 주장이 틀렸다면 어떻게 틀리는가?"입니다. 스스로 그 질문에 답하지 않은 논문은 심사자가 공격해서 **revision 루프**에 갇힙니다. **자기 논문의 첫 심사자는 자기 자신이어야** 합니다.

### 4대 하위 원칙

#### 3-1. Steelman — 반론을 가장 강한 형태로

**원칙**: 반론을 반박할 때는 반론의 **가장 강한 버전**을 제시해야 한다. 약한 버전(strawman)을 공격하면 "실제 반론은 더 강한데 피했다"는 지적.

**구현**:
- `peer-reviewer` Mode A의 "Reviewer 2 (분야 전문가)" 페르소나가 steelman 버전 제시
- `flow-refiner`가 새 논문 발견 시 steelman 보강 제안
- `flow-evaluator` 축 3-1 감점 사유: "이 반론의 더 강한 버전은 X"

#### 3-2. Falsifiability — 주장이 틀릴 조건 명시

**원칙**: 어떤 조건에서 내 주장이 틀렸다고 볼 것인가를 **명시적으로** 밝혀야 한다. 밝히지 않으면 "non-falsifiable" 지적.

**구현**:
- Section 5 (Implications & Counterarguments)에서 반증 조건 명시 요구
- `flow-evaluator` 축 3-2 감점: "이 주장이 틀렸다고 판단할 조건이 명시되지 않음"

#### 3-3. Productive Limitations — 한계를 자산으로

**원칙**: 한계(limitations)를 **방어적**으로 "향후 연구 필요"로 처리하면 약점으로 남는다. **productive**하게 "이 한계가 정확히 어떤 후속 연구 경로를 여는가"로 제시하면 기여로 전환된다.

**구현**:
- `writing-architect` Conclusion 전략: "What Next?" 섹션 필수
- `peer-reviewer` Mode A가 한계 처리 품질 평가
- `gap-finder`가 발견한 분야 Gap을 한계 섹션과 연결

#### 3-4. Reviewer Attack Surface — 심사자 예상 공격 대응

**원칙**: 제출 전에 3-5명의 심사자 페르소나로 예상 공격을 모의하고 **본문에서 선제 답변**해야 한다.

**구현**:
- `peer-reviewer` Mode A가 Reviewer 1 (방법론 엄격) / Reviewer 2 (분야 전문) / Reviewer 3 (실용주의) 3명 시뮬레이션
- 각 리뷰어의 Major/Minor issue를 원고에 본문 답변으로 반영
- 축 3-4 감점: "이 심사자 major objection 미대응"

---

## 🌟 축 4: 독창성·기여도

### 왜 이 축이 존재하는가

Top-tier 저널 심사자의 **첫 번째 질문**은 "So What?"입니다. 기존 문헌에 이미 있는 것을 반복하는 논문은 새로운 지식 기여가 없어 accept되지 않습니다. 반대로 기여가 명확하면 다른 축에 흠이 있어도 revision 기회를 얻습니다.

### 4대 하위 원칙

#### 4-1. "So What?" Test — 분야가 잃는 것

**원칙**: "이 논문이 존재하지 않았다면 분야는 무엇을 잃는가?"에 **구체적으로** 답해야 한다. "이 주제는 중요하다" 같은 일반론은 통하지 않음.

**구현**:
- `originality-evaluator`가 Introduction·Conclusion에서 "So What?" 증거 문장 탐색
- 부재 시 축 4-1 −15점 감점
- 개선 방향 제시: "이 연구가 없으면 [구체적 공백]이 해결되지 않는다" 형식 권장

#### 4-2. Novelty Positioning — 선행 연구 Delta Map

**원칙**: "기존 연구와 다르게"는 너무 약하다. **가장 유사한 선행 연구 3편을 지명**하고 각각과의 구체적 차별점을 명시해야 한다.

**구현**:
- `originality-evaluator`가 **Delta Map 테이블** 자동 생성:
  ```
  | 선행 | 이미 한 것 | 이 논문의 Delta | 강도 |
  ```
- `flow-refiner`가 새 논문 발견 시 Delta Map에 추가

#### 4-3. Contribution Layer Clarity — 개념/이론/방법론/경험 층위 명시

**원칙**: "이 논문의 기여는 **개념적**이다 — 기존 cool EF 중심 연구를 규칙 속성 4분면으로 재개념화"처럼 기여 층위가 명시되고 일관되어야 한다. 이론 에세이에서 경험적 주장을 섞는 층위 혼재는 심사자 불안 유발.

**구현**:
- `originality-evaluator`의 4-3 체크: "기여 층위가 명시되고 일관되는가?"
- 층위 혼재 시 수정 권고

#### 4-4. Downstream Implications — 후속 경로 구체화

**원칙**: 이 기여가 열어주는 후속 연구·실무 경로를 **3가지 이상 구체적으로** 제시. "향후 연구가 필요하다" 수준은 empty.

**구현**:
- Conclusion 전략에 "What Next?" 섹션 필수
- `originality-evaluator`가 implications 구체성 평가

---

## 🔬 축 5: 구성개념 정의 정밀도

### 왜 이 축이 존재하는가

이론 에세이·개념 논문의 **가장 쉽게 털리는 지점**입니다. 핵심 용어가 모호하게 쓰이거나, 중간에 의미가 드리프트하거나, 조작화되지 않으면 심사자가 "What exactly do you mean by X?"로 공격합니다. 이 질문 하나에 걸려도 논문은 revise됩니다.

### 4대 하위 원칙

#### 5-1. Core Construct Definition — 첫 등장 시 정의

**원칙**: 핵심 용어는 **첫 등장 시점**에 정의되어야 하며, 이후 **일관되게** 사용되어야 한다. 같은 용어가 다른 섹션에서 다른 의미로 쓰이면 concept drift.

**구현**:
- `concept-clarity-evaluator`가 **용어 정의 감사 테이블** 작성:
  ```
  | 용어 | 첫 등장 | 명시 정의? | 후속 사용 drift? | 감점 |
  ```
- Drift 탐지 시 수정 권고

#### 5-2. Operationalization — 관찰 가능한 지표

**원칙**: 추상 개념이라도 "이런 행동은 개념 A, 저런 행동은 개념 B"의 **구체적 예시와 non-example**이 있어야 한다.

**구현**:
- `concept-clarity-evaluator` 5-2 체크리스트
- `paper-analyst`의 섹션별 인용 다발에 "구체적 수치·예시" 필드

#### 5-3. Boundary Conditions — 적용 범위 명확화

**원칙**: 개념·프레임워크가 **어디에 적용되고 어디에 적용되지 않는지** 명시. 무제한 일반화는 over-claim.

**구현**:
- Section 4 또는 5에 **적용 경계 박스** 권장
- `concept-clarity-evaluator` 5-3 감점

#### 5-4. Categorical vs Dimensional — 선택 근거 명시

**원칙**: 분류 축을 범주적(discrete)으로 쓰는지 연속적(continuous)으로 쓰는지, 그리고 **그 선택의 근거**를 밝혀야 한다. 최소한 "heuristic 채택" 같은 disclaimer 필수.

**구현**:
- `concept-clarity-evaluator` 5-4 체크
- flow.md Section 4 등 핵심 개념 도입 시 범주/차원 선택 명시 요구

---

## ✍️ 학술 글쓰기의 공통 원칙

5축과 독립적으로 **모든 학술 글쓰기에 적용되는** 원칙. 모든 writing agent(`writing-architect`, `chapter-editor`, `flow-refiner`)에 내장.

### Topic Sentence First

각 문단의 **첫 문장이 그 문단의 핵심 주장**이어야 한다. 심사자는 시간이 없어 첫 문장만 훑는다. 첫 문장이 약하면 그 문단은 안 읽힌다.

### Synthesis over Summary

> ❌ "Smith (2023)은 X를 주장했다. Lee (2024)는 Y를 주장했다. Park (2022)는 Z를 주장했다."
>
> ✅ "X라는 관점에서 Smith (2023)와 Lee (2024)는 공통적으로 ~을 보이지만, Park (2022)는 반대로 ~을 시사한다."

개별 논문 요약 나열은 **bad academic writing**의 1순위 증상. 주제별로 종합 서술.

### Evidence → Analysis

인용만 달고 끝나면 안 된다. 반드시 **그 인용이 왜 중요한지, 이 논문에서 어떻게 활용되는지**의 분석이 뒤따라야 한다.

### Hedging Appropriate to Evidence Strength

근거 강도에 맞는 표현 선택:

| 근거 강도 | 표현 |
|----------|------|
| 약 (1 study, correlation only) | "Smith (2023) suggests that..." |
| 중 (multiple replication) | "Research indicates that... (Smith, 2023; Lee, 2024)" |
| 강 (meta-analysis, causal) | "Smith (2023) demonstrated that..." |
| 매우 강 | "Well-established finding (Smith, 2023; Meta-Analysis X, 2024)" |

근거가 약한데 "demonstrates"로 쓰면 **over-claim 감지** 즉시 발동.

### Condition Preservation — Over-claim 방지

`paper-analyst`의 섹션별 인용 다발에 있는 "조건·한계" 필드를 **절대 무시하지 말 것**. 저자가 "특정 조건 하에서" 주장한 것을 "일반적으로"로 바꾸는 것이 over-claim의 핵심 패턴.

---

## 🚫 시스템이 방지하는 전형적 실수 13가지

| # | 실수 | 왜 일어나는가 | 시스템이 막는 방식 |
|---|------|-------------|----------------|
| 1 | **Over-claim** (correlation → causation) | paper 요약만 보고 원문 조건 무시 | paper-analyst의 "조건·한계" 필드 + citation-auditor PDF 대조 |
| 2 | **Strawman 반론** | 약한 반론을 공격해서 논증 강화한 것처럼 보이려 함 | peer-reviewer Mode A의 Reviewer 2 steelman 요구 |
| 3 | **Reference inflation** | 저널 심사 통과 목적으로 관련 없는 인용 남발 | claim-extractor가 문장별 인용 매핑 — 각 인용이 실제로 어떤 주장 뒷받침하는지 추적 |
| 4 | **Circular argument** | A 때문에 B, B 때문에 A (같은 주장 반복) | flow-evaluator 축 2-1 argument chain 검사 |
| 5 | **Moving goalpost** | RQ와 Thesis, Conclusion이 서로 다름 | claim-extractor가 RQ·Thesis 추출 강제 + 축 2-4 Scope Closure |
| 6 | **Construct concept drift** | 같은 용어를 섹션마다 다른 의미로 사용 | concept-clarity-evaluator 정의 감사 테이블 |
| 7 | **Placeholder citation** | `[Smith]`, `[논문 이름 미정]` 같은 임시 표기 | claim-extractor의 UNMATCHED 탐지 → HUNT 과제 자동 생성 |
| 8 | **Missing key references** | 세미널 논문 누락 | flow-evaluator 축 1-3 Authority + Consensus MCP의 인용수 필터링 |
| 9 | **Confirmation bias** | 자기 주장 뒷받침 문헌만 인용, 반대 증거 배제 | 축 1-4 Balance 채점 + peer-reviewer의 반대 증거 시뮬레이션 |
| 10 | **Logic jump** | A에서 C로 점프, 전제 B 생략 | writing-architect Phase 1의 "premise → warrant → claim" 설계 |
| 11 | **Scope creep** | Section이 주제에서 벗어나 방황 | flow-evaluator 축 2-3 Thesis Alignment |
| 12 | **Vague operationalization** | 추상 개념만 나열, 관찰 가능 지표 없음 | concept-clarity-evaluator 축 5-2 체크리스트 |
| 13 | **"So What?" 답 부재** | 왜 이 연구가 중요한지 본문에 설명 없음 | originality-evaluator 축 4-1 first-question test |

---

## 🔁 반복과 진화

### 왜 한 번에 쓰지 않는가

좋은 학술 글쓰기는 **선형적 생산**이 아니라 **반복적 증류**입니다. 연구자도 처음 쓴 초안을 7-10차례 수정합니다. 이유:

1. **평가 없이 쓰면 자기 맹점이 안 보임** — 쓰는 사람과 읽는 사람은 다르다
2. **외부 관점 없이는 5축 중 일부 축에 영구히 맹점** — 특히 독창성·구성개념 정의
3. **새 논문이 계속 발견됨** — 기존 논증이 new evidence로 재구성되어야 할 수 있음

### 시스템의 반복 루프 구조

```
작성(v1) → 평가(1차) → 수정 → 평가(2차) → 수정 → ... → 최종 평가
              ↓              ↓              ↓
         archive/001    archive/002    archive/003
```

각 평가 회차마다 `evaluations/archive/{NNN}/`로 스냅샷을 남겨:
- **축별 점수 delta 추적** (어느 수정이 어느 축을 몇 점 올렸는가)
- **과거 평가 복기**
- **논문 투고 포트폴리오**로 활용 (성장 기록)

### Backward Navigation 지원

연구는 선형적이지 않습니다. 초안 쓰다 논문 더 찾기, 평가 보고 flow 재설계, 챕터 수정 중 근본 재검토. 이 모든 전이를 **안전하게** 지원:

- **chapters/archive/**: 덮어쓰기 전 자동 스냅샷 → 구버전 복구 가능
- **evaluations/archive/**: 평가 스냅샷 → delta 추적
- **papers/archived/**: 논문 제거 시 보관 → dangling citation 자동 탐지
- **analyzed/*.md의 v1/v2/v3 append 모드**: 재분석 시 덮어쓰지 않음 → 분석 진화 이력 보존
- **.sync-state.json**: 아티팩트 간 의존성 추적 → stale 자동 감지 + priority 기반 순차 해소

---

## 🏛 시스템 설계 철학

### 1. Single Source of Truth (SSOT)

각 정보는 **한 곳에만** 있어야 한다. 중복은 불일치의 원천.

- `flow.md`: RQ·Thesis·논증 구조의 SSOT
- `analyzed/*.md`: 각 논문의 섹션별 인용 재료 SSOT
- `evaluations/latest/`: 현재 평가 상태 SSOT
- `.sync-state.json`: 아티팩트 간 관계 SSOT

### 2. Automatic Invalidation

한 아티팩트가 변하면 의존 아티팩트가 자동으로 **stale** 표시됨. 조용히 어긋나지 않음.

```
flow.md 변경 → analyzed/ REANALYZE 권장
            → chapters/ chapter_flow_drift
            → evaluations/ evaluation_stale
            → final/ final_stale
```

### 3. Safe Backtracking

모든 덮어쓰기 직전 archive 생성. 사용자가 언제든 이전 상태로 복귀 가능.

### 4. Cold Evaluation — 관대하지 않음

이 시스템의 평가는 **top-tier 저널 심사자 엄격도**를 시뮬레이션. "대체로 잘 썼네" 수준의 관대한 피드백 **금지**. 각 감점은 구체적 섹션·문장·이유를 명시.

이는 불편하지만, 실제 심사보다 먼저 결함을 발견하게 해서 **실제 심사에서의 reject를 예방**합니다.

### 5. Modular Agents — Single Responsibility

12개 에이전트 각각이 **하나의 책임**만 가진다. `writing-architect`는 초안 창작, `chapter-editor`는 수정, `flow-refiner`는 flow 보강 — 기능이 겹치지 않음. 이유:

- 호출 토큰 효율 (Chapter 수정 15회 × 경량 chapter-editor = 큰 절감)
- 유지보수 용이 (각 파일 단일 책임)
- 역할 경계가 사용자에게 명확

### 6. Prose over Template

구조적 템플릿 (체크박스, 빈칸 채우기) 대신 **자유 줄글(prose) flow.md**를 받는다. 이유:

- 연구자는 본래 에세이처럼 사고 — 체크박스는 사고의 흐름을 끊는다
- 시스템이 `claim-extractor`로 prose를 문장 단위 구조로 자동 변환 — 사용자가 구조화 부담 없음
- 자유 서술이 sterile한 템플릿보다 **thesis와 논증 강도**가 더 잘 드러남

### 7. Sentence-Level Granularity

주장의 최소 단위는 **문단이 아니라 문장**이다. claim-extractor가 문장마다:
- 분류 (7종)
- 인용 매핑 (MATCHED / UNMATCHED-INTERNAL / UNMATCHED-EXTERNAL)
- 검증 (over-claim / under-claim 경고)

이것이 "모든 문장이 레퍼런스가 필요하다"는 제약을 실제로 **강제 가능하게** 만듭니다.

---

## 🗺 에이전트별 원칙 매핑

| 에이전트 | 구현 원칙 | 방어하는 실수 |
|---------|---------|------------|
| **flow-evaluator** | 5축 전체 + cold evaluation + delta 추적 + sync gate | 관대한 평가, 다른 에이전트가 놓친 축 간 상호작용 |
| **claim-extractor** | 1-1 Coverage, 1-2 Accuracy 예비, 5-1 Definition 탐지 | #7 Placeholder citation, #5 Moving goalpost |
| **originality-evaluator** | 4-1 ~ 4-4 | #13 "So What?" 답 부재 |
| **concept-clarity-evaluator** | 5-1 ~ 5-4 | #6 Concept drift, #12 Vague operationalization |
| **paper-analyst** | 인용 재료의 "조건·한계" 필드 | #1 Over-claim (근본 예방) |
| **writing-architect** | Topic Sentence First, Synthesis, Hedging, Evidence→Analysis | #4 Circular, #10 Logic jump |
| **chapter-editor** | 기존 구조 보존 + writing 원칙 유지 | 수정 과정의 구조 붕괴 |
| **flow-refiner** | 4-2 Novelty Positioning, 3-1 Steelman 보강 | Novelty 드리프트 |
| **citation-auditor** | 1-2 Accuracy (PDF 원문 대조) | #1 Over-claim (실시간 탐지), misattribution |
| **gap-finder** | 1-4 Balance (disconfirming evidence 발굴) | #9 Confirmation bias |
| **methodology-advisor** | (empirical 전용) 방법론 정당화 | 방법론 임의 선택 |
| **peer-reviewer** | 3-1 Steelman, 3-4 Reviewer Attack Surface | #2 Strawman, reject 유발 major issue |

---

## 📖 학술 전통과 근거 문헌

이 시스템은 아래 학술 글쓰기 전통·기준을 종합하여 설계되었습니다:

### 학술 글쓰기 고전
- **Booth, W. C., Colomb, G. G., & Williams, J. M.** — *The Craft of Research* (4th ed.). 연구 질문 → 주장 → 근거 → 정당화(warrant) → 반론 → 자격조건의 5단계 논증 구조
- **Williams, J. M.** — *Style: Toward Clarity and Grace*. Topic Sentence First, 문장 결속의 원칙
- **Zinsser, W.** — *On Writing Well*. Hedging, 군더더기 제거
- **Pinker, S.** — *The Sense of Style*. Classical style, 독자 입장 작성
- **Strunk, W., & White, E. B.** — *The Elements of Style*. 간결·명확의 원칙

### 학술 심사 기준
- **APA Publication Manual** (7th ed.) — 인용 형식·수치 보고·글 구조
- **Nature / Nature Human Behaviour** editorial criteria — novelty·contribution·rigor
- **Psychological Review / Psychological Bulletin** — theoretical contribution 평가 관습
- **CONSORT / STROBE / PRISMA** — 방법론 보고 표준 (empirical 연구)

### 비판적 사고
- **Kahneman, D.** — *Thinking, Fast and Slow*. Confirmation bias의 인지 기반
- **Popper, K.** — *Conjectures and Refutations*. Falsifiability 원칙
- **Rauch, J.** — *The Constitution of Knowledge*. 학술 공동체의 지식 생성 메커니즘

### 학술 글쓰기 교육
- **Belcher, W. L.** — *Writing Your Journal Article in Twelve Weeks*. 저널 투고 실무
- **Silvia, P. J.** — *How to Write a Lot*. 생산성과 수정 반복
- **Sword, H.** — *Stylish Academic Writing*. 가독성 연구

### 인용·논증 이론
- **Toulmin, S.** — *The Uses of Argument*. Claim-Data-Warrant-Backing-Qualifier-Rebuttal 모델
- **Walton, D.** — *Argumentation Schemes*. 학술 논증의 유형 분류

---

## 🎯 결론

이 시스템은 **좋은 논문이 되기 위한 모든 고려사항**을 다음 세 층위로 구현합니다:

1. **철학 층 (이 문서)**: 왜 이 기준들이 좋은 논문의 본질인가
2. **평가 층 (`evaluations/`)**: 이 기준들을 어떻게 측정하고 작업 지시서로 환원하는가
3. **실행 층 (12 에이전트 + sync 시스템)**: 이 지시를 어떻게 안전하게 반복·개선하는가

사용자가 시스템을 의심할 때 — "왜 이 에이전트가 이걸 지적하지?", "왜 이 순서로 해야 하지?" — 답은 대부분 이 문서 안에 있습니다. 이 시스템을 잘 쓰는 유일한 방법은 **top-tier 저널 심사자처럼 생각하는 것**이며, 이 문서는 그 사고의 지도입니다.

---

**관련 문서**:
- [README.md](./README.md) — 설치, 개요, 빠른 시작
- [MANUAL.md](./MANUAL.md) — 사용자 매뉴얼, 각 명령 상세
- [skills/SKILL.md](./skills/SKILL.md) — 시스템 동작 정의 (Claude Code 스킬)
