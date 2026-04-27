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
14. [Critical Mode — 새로운 관점·비판적 시각의 능동적 지원](#-critical-mode--새로운-관점비판적-시각의-능동적-지원)
15. [활동 로그와 4계층 방어 철학](#-활동-로그와-4계층-방어-철학)
16. [결론](#-결론)

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
- 빠진 인용을 RESEARCH 과제로 자동 생성

#### 1-2. Accuracy — 인용이 실제로 주장을 뒷받침

**원칙**: "Smith (2023) proves X"로 썼다면 Smith (2023)가 실제로 X를 증명해야 한다. 상관관계를 인과로 말하는 건 흔한 over-claim이며, 심사자 1순위 공격 대상.

**구현**:
- `paper-analyst`가 각 논문의 "조건·한계" 필드를 명시
- `writing-architect`가 이 필드를 준수
- `citation-checker`가 **PDF 원문과 대조**하여 over-claim·misattribution 탐지
- 평가 단계별 자동 체이닝: v1(30% 샘플) / revised(전량) / final(전량 + new-error diff)

#### 1-3. Authority & Recency — 세미널 + 최신 논문 균형

**원칙**: 분야의 세미널 논문은 피할 수 없다 (못 알고 쓰면 심사자 즉시 간파). 동시에 최근 3-5년 반론·확장 문헌을 빠뜨리면 시대에 뒤처진 글이 된다.

**구현**:
- Consensus MCP 검색 결과의 **저널 등급·인용 수·발행 연도** 메타데이터 활용
- `axis1-reference-scorer` 축 1-3 채점에서 세미널 누락·최신 부재 모두 감점
- `axis4-originality-scorer`의 Delta Map이 "유사 선행 연구 TOP 3"를 명시적으로 요구하여 누락 방지

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
- `axis2-logic-scorer`가 warrant 누락을 축 2-1 감점으로 처리
- `output-editor`는 기존 사슬을 보존하며 수정

#### 2-2. Section Transition — 섹션 간 논리적 다리

**원칙**: Section N의 결론이 Section N+1의 전제로 정확히 이어져야 한다. "Section 2는 X를 보였다. **따라서 이제 Y를 다루기 위해** Section 3으로 넘어간다" 형식의 transition 문장 필수.

**구현**:
- `writing-architect` Phase 1 설계 시 각 섹션에 "다음 섹션 연결" 명시
- `axis2-logic-scorer`가 섹션 간 Logic jump를 축 2-2 감점으로 지적
- `output-editor`가 수정 후 자동 일관성 체크 (Phase 4)

#### 2-3. Thesis Alignment — 모든 단락이 thesis에 기여

**원칙**: 각 문단은 전체 thesis에 **구체적으로 어떻게 기여하는지** 물을 때 답이 있어야 한다. 답이 없으면 그 문단은 탈선.

**구현**:
- `flow.md` 작성 시 **thesis를 한 문장으로 명시** 강제 (claim-extractor가 탐지)
- `axis2-logic-scorer`가 각 문단에 대해 "이 문단이 thesis에 기여하는가?" 체크
- 탈선 문단은 축 2-3 감점 + 삭제 권고

#### 2-4. Scope Closure — RQ에 실제로 답함

**원칙**: Research Question이 "어떻게 X?"인데 결론이 "왜 X?"만 답하면 scope error. RQ를 시작 섹션에 명시했으면 마지막 섹션에서 **같은 형태로** 답해야 한다.

**구현**:
- `claim-extractor`가 prose flow에서 RQ를 명시적으로 추출
- `axis2-logic-scorer`의 "Mirror Introduction" 원칙 (Conclusion 섹션 전략)
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
- `axis3-defense-scorer` 축 3-1 감점 사유: "이 반론의 더 강한 버전은 X"

#### 3-2. Falsifiability — 주장이 틀릴 조건 명시

**원칙**: 어떤 조건에서 내 주장이 틀렸다고 볼 것인가를 **명시적으로** 밝혀야 한다. 밝히지 않으면 "non-falsifiable" 지적.

**구현**:
- Section 5 (Implications & Counterarguments)에서 반증 조건 명시 요구
- `axis3-defense-scorer` 축 3-2 감점: "이 주장이 틀렸다고 판단할 조건이 명시되지 않음"

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
- `axis4-originality-scorer`가 Introduction·Conclusion에서 "So What?" 증거 문장 탐색
- 부재 시 축 4-1 −15점 감점
- 개선 방향 제시: "이 연구가 없으면 [구체적 공백]이 해결되지 않는다" 형식 권장

#### 4-2. Novelty Positioning — 선행 연구 Delta Map

**원칙**: "기존 연구와 다르게"는 너무 약하다. **가장 유사한 선행 연구 3편을 지명**하고 각각과의 구체적 차별점을 명시해야 한다.

**구현**:
- `axis4-originality-scorer`가 **Delta Map 테이블** 자동 생성:
  ```
  | 선행 | 이미 한 것 | 이 논문의 Delta | 강도 |
  ```
- `flow-refiner`가 새 논문 발견 시 Delta Map에 추가

#### 4-3. Contribution Layer Clarity — 개념/이론/방법론/경험 층위 명시

**원칙**: "이 논문의 기여는 **개념적**이다 — 기존 cool EF 중심 연구를 규칙 속성 4분면으로 재개념화"처럼 기여 층위가 명시되고 일관되어야 한다. 이론 에세이에서 경험적 주장을 섞는 층위 혼재는 심사자 불안 유발.

**구현**:
- `axis4-originality-scorer`의 4-3 체크: "기여 층위가 명시되고 일관되는가?"
- 층위 혼재 시 수정 권고

#### 4-4. Downstream Implications — 후속 경로 구체화

**원칙**: 이 기여가 열어주는 후속 연구·실무 경로를 **3가지 이상 구체적으로** 제시. "향후 연구가 필요하다" 수준은 empty.

**구현**:
- Conclusion 전략에 "What Next?" 섹션 필수
- `axis4-originality-scorer`가 implications 구체성 평가

---

## 🔬 축 5: 구성개념 정의 정밀도

### 왜 이 축이 존재하는가

이론 에세이·개념 논문의 **가장 쉽게 털리는 지점**입니다. 핵심 용어가 모호하게 쓰이거나, 중간에 의미가 드리프트하거나, 조작화되지 않으면 심사자가 "What exactly do you mean by X?"로 공격합니다. 이 질문 하나에 걸려도 논문은 revise됩니다.

### 4대 하위 원칙

#### 5-1. Core Construct Definition — 첫 등장 시 정의

**원칙**: 핵심 용어는 **첫 등장 시점**에 정의되어야 하며, 이후 **일관되게** 사용되어야 한다. 같은 용어가 다른 섹션에서 다른 의미로 쓰이면 concept drift.

**구현**:
- `axis5-concept-scorer`가 **용어 정의 감사 테이블** 작성:
  ```
  | 용어 | 첫 등장 | 명시 정의? | 후속 사용 drift? | 감점 |
  ```
- Drift 탐지 시 수정 권고

#### 5-2. Operationalization — 관찰 가능한 지표

**원칙**: 추상 개념이라도 "이런 행동은 개념 A, 저런 행동은 개념 B"의 **구체적 예시와 non-example**이 있어야 한다.

**구현**:
- `axis5-concept-scorer` 5-2 체크리스트
- `paper-analyst`의 섹션별 인용 다발에 "구체적 수치·예시" 필드

#### 5-3. Boundary Conditions — 적용 범위 명확화

**원칙**: 개념·프레임워크가 **어디에 적용되고 어디에 적용되지 않는지** 명시. 무제한 일반화는 over-claim.

**구현**:
- Section 4 또는 5에 **적용 경계 박스** 권장
- `axis5-concept-scorer` 5-3 감점

#### 5-4. Categorical vs Dimensional — 선택 근거 명시

**원칙**: 분류 축을 범주적(discrete)으로 쓰는지 연속적(continuous)으로 쓰는지, 그리고 **그 선택의 근거**를 밝혀야 한다. 최소한 "heuristic 채택" 같은 disclaimer 필수.

**구현**:
- `axis5-concept-scorer` 5-4 체크
- flow.md Section 4 등 핵심 개념 도입 시 범주/차원 선택 명시 요구

---

## ✍️ 학술 글쓰기의 공통 원칙

5축과 독립적으로 **모든 학술 글쓰기에 적용되는** 원칙. 모든 writing agent(`writing-architect`, `output-editor`, `flow-refiner`)에 내장.

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
| 1 | **Over-claim** (correlation → causation) | paper 요약만 보고 원문 조건 무시 | paper-analyst의 "조건·한계" 필드 + citation-checker PDF 대조 |
| 2 | **Strawman 반론** | 약한 반론을 공격해서 논증 강화한 것처럼 보이려 함 | peer-reviewer Mode A의 Reviewer 2 steelman 요구 |
| 3 | **Reference inflation** | 저널 심사 통과 목적으로 관련 없는 인용 남발 | claim-extractor가 문장별 인용 매핑 — 각 인용이 실제로 어떤 주장 뒷받침하는지 추적 |
| 4 | **Circular argument** | A 때문에 B, B 때문에 A (같은 주장 반복) | axis2-logic-scorer 축 2-1 argument chain 검사 |
| 5 | **Moving goalpost** | RQ와 Thesis, Conclusion이 서로 다름 | claim-extractor가 RQ·Thesis 추출 강제 + 축 2-4 Scope Closure |
| 6 | **Construct concept drift** | 같은 용어를 섹션마다 다른 의미로 사용 | axis5-concept-scorer 정의 감사 테이블 |
| 7 | **Placeholder citation** | `[Smith]`, `[논문 이름 미정]` 같은 임시 표기 | claim-extractor의 UNMATCHED 탐지 → RESEARCH 과제 자동 생성 |
| 8 | **Missing key references** | 세미널 논문 누락 | axis1-reference-scorer 축 1-3 Authority + Consensus MCP의 인용수 필터링 |
| 9 | **Confirmation bias** | 자기 주장 뒷받침 문헌만 인용, 반대 증거 배제 | 축 1-4 Balance 채점 + peer-reviewer의 반대 증거 시뮬레이션 |
| 10 | **Logic jump** | A에서 C로 점프, 전제 B 생략 | writing-architect Phase 1의 "premise → warrant → claim" 설계 |
| 11 | **Scope creep** | Section이 주제에서 벗어나 방황 | axis2-logic-scorer 축 2-3 Thesis Alignment |
| 12 | **Vague operationalization** | 추상 개념만 나열, 관찰 가능 지표 없음 | axis5-concept-scorer 축 5-2 체크리스트 |
| 13 | **"So What?" 답 부재** | 왜 이 연구가 중요한지 본문에 설명 없음 | axis4-originality-scorer 축 4-1 first-question test |

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

각 평가 회차마다 `{stage}/history/{stage}/evaluations/{NNN}/`로 스냅샷을 남겨:
- **축별 점수 delta 추적** (어느 수정이 어느 축을 몇 점 올렸는가)
- **과거 평가 복기**
- **논문 투고 포트폴리오**로 활용 (성장 기록)

### Backward Navigation 지원

연구는 선형적이지 않습니다. 초안 쓰다 논문 더 찾기, 평가 보고 flow 재설계, 챕터 수정 중 근본 재검토. 이 모든 전이를 **안전하게** 지원:

- **output/archive/**: 덮어쓰기 전 자동 스냅샷 → 구버전 복구 가능
- **{stage}/history/{stage}/evaluations/**: 평가 스냅샷 → delta 추적
- **papers/archived/**: 논문 제거 시 보관 → dangling citation 자동 탐지
- **analyzed/*.md의 v1/v2/v3 append 모드**: 재분석 시 덮어쓰지 않음 → 분석 진화 이력 보존
- **.sync-state.json**: 아티팩트 간 의존성 추적 → stale 자동 감지 + priority 기반 순차 해소

---

## 🏛 시스템 설계 철학

### 1. Single Source of Truth (SSOT)

각 정보는 **한 곳에만** 있어야 한다. 중복은 불일치의 원천.

- `flow.md`: RQ·Thesis·논증 구조의 SSOT
- `analyzed/*.md`: 각 논문의 섹션별 인용 재료 SSOT
- `{stage}/evaluations/latest/`: 현재 평가 상태 SSOT
- `.sync-state.json`: 아티팩트 간 관계 SSOT

### 2. Automatic Invalidation

한 아티팩트가 변하면 의존 아티팩트가 자동으로 **stale** 표시됨. 조용히 어긋나지 않음.

```
flow.md 변경 → analyzed/ RESEARCH(reanalyze) 권장
            → output/ chapter_flow_drift
            → evaluations/ evaluation_stale
            → final/ final_stale
```

### 3. Safe Backtracking

모든 덮어쓰기 직전 archive 생성. 사용자가 언제든 이전 상태로 복귀 가능.

### 4. Cold Evaluation — 관대하지 않음

이 시스템의 평가는 **top-tier 저널 심사자 엄격도**를 시뮬레이션. "대체로 잘 썼네" 수준의 관대한 피드백 **금지**. 각 감점은 구체적 섹션·문장·이유를 명시.

이는 불편하지만, 실제 심사보다 먼저 결함을 발견하게 해서 **실제 심사에서의 reject를 예방**합니다.

### 5. Modular Agents — Single Responsibility

20개 에이전트 각각이 **하나의 책임**만 가진다. `writing-architect`는 초안 창작, `output-editor`는 한글 수정, `flow-refiner`는 flow 보강, `abstract-translator`는 영→한 abstract 번역, `output-en-translator`는 한→영 chapter 출고 번역 — 기능이 겹치지 않음. 평가는 **evaluation-orchestrator(디스패처) + axis1-6 scorer(각 축 전담)**, 논문 처리는 **paper-analyst** 단일 agent (단순화 v3 — anchor/non-anchor 이진, orchestration 흡수). 이유:

- 호출 토큰 효율 (Chapter 수정 15회 × 경량 output-editor = 큰 절감)
- 유지보수 용이 (각 파일 단일 책임)
- 역할 경계가 사용자에게 명확
- **작업별로 다른 모델 할당 가능** (다음 섹션 참조)

### 5a. 모델 라우팅 (비용·속도 최적화)

단일 책임 원칙이 **모델 차별화**를 가능하게 한다. 서브에이전트는 Agent 도구 호출 시 `model` 파라미터로 `haiku`·`sonnet`·`opus` 중 선택 가능하며, 각 에이전트 정의 파일 frontmatter의 `model` 필드가 기본값을 지정한다.

**할당 원칙**:

| 모델 | 대상 작업 | 에이전트 예시 |
|------|----------|-------------|
| **opus** | 심사자 엄격도 판단·패러다임 분석·글쓰기 품질 결정·Critical Reading | evaluation-orchestrator, axis2-logic-scorer, axis3-defense-scorer, axis4-originality-scorer, axis6-critical-scorer, critical-companion, writing-architect, output-editor, output-en-translator, flow-refiner, peer-reviewer, **paper-analyst anchor 분석 (+ Mode C critique_target)** |
| **sonnet** | 구조화된 분석·규칙 기반 검증·카운팅 | **paper-analyst non-anchor 분석 + Mode B 재분석** (frontmatter 기본값), claim-extractor, citation-checker, axis1-reference-scorer, axis5-concept-scorer, gap-finder, methodology-advisor |
| **haiku** | 기계적·대량·저창의 작업 | abstract-translator, **paper-analyst Pass 1 (triage)** |

**판단 기준**:
- **창의성·판단력이 품질을 결정하는가?** → opus (실패 시 복구 비용이 크다)
- **명확한 절차·스키마가 있는가?** → sonnet (opus까진 과함)
- **매핑·변환이 본질인가?** → haiku (1/10 비용)

**메인 세션(opus)은 오케스트레이션 전담**: RESEARCH 단계 2에서 메인 opus가 abstract를 직접 번역하는 것은 낭비 — 번역은 haiku 서브에이전트에 위임하고 메인은 큐레이션·annotation·액션 아이템 작성에만 집중. 평가도 동일: 메인 opus는 evaluation-orchestrator 호출만, 실제 채점은 axis scorer들이 병렬 수행.

**평가 축별 모델 근거** (2026-04-23 리팩터 시 결정):
- **axis1 (sonnet)**: Coverage·Accuracy·Authority·Balance는 claim-extraction 집계 + PDF spot-check로 규칙 기반. 대부분 카운팅 + 간단 대조이므로 sonnet 충분.
- **axis2·3·4·6 (opus)**: 논증 품질·반박 질·독창성·비판적 시각은 미묘한 판단을 요구 — sonnet으로 다운그레이드 시 감점 사유 식별 품질 하락.
- **axis5 (sonnet)**: 정의 존재·조작화·경계·범주형 여부는 체크리스트 기반. 판단보다 구조 확인이 주.

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
| **evaluation-orchestrator** | 병렬 delta 아키텍처 + 모델 라우팅 + Archive 스냅샷 + sync gate | 순차 체이닝 낭비, 변경 없는 축 재계산, 관대한 평가 |
| **axis1-reference-scorer** | 1-1~1-4 (Coverage·Accuracy·Authority·Balance) + PDF spot-check | 세미널 누락, placeholder citation, confirmation bias |
| **axis2-logic-scorer** | 2-1~2-4 (Argument Chain·Transition·Thesis·Scope) | Warrant 누락, 섹션 간 logic jump |
| **axis3-defense-scorer** | 3-1~3-4 (Steelman·Falsifiability·Limitations·Attack Surface) | Strawman, 반증 조건 부재 |
| **axis4-originality-scorer** | 4-1~4-4 (So What·Novelty·Layer·Implications) + Delta Map | "So What?" 답 부재, Novelty 드리프트 |
| **axis5-concept-scorer** | 5-1~5-4 (Definition·Operationalization·Boundary·Categorical) | Concept drift, Vague operationalization |
| **axis6-critical-scorer** | 축 6 (C-1 Paradigm ~ C-4 Minority Recovery) + 자기 배신 탐지 | orthodox 편향, timidity, 소수 의견 배제 |
| **claim-extractor** | 1-1 Coverage, 1-2 Accuracy 예비, 5-1 Definition 탐지 | #7 Placeholder citation, #5 Moving goalpost |
| **critical-companion** | Socratic 질문 (답변 생산 금지) + commitment 추출 + 정합성 점검 | 지적 자기 배신 (답변 → 원고 누락), 회피 중인 질문 |
| **paper-analyst** | 인용 재료의 "조건·한계" 필드 + axis_tags + Mode C (hidden assumptions) | #1 Over-claim (근본 예방), confirmation bias 재생산 |
| **writing-architect** | Topic Sentence First, Synthesis, Hedging, Evidence→Analysis | #4 Circular, #10 Logic jump |
| **output-editor** | 기존 구조 보존 + writing 원칙 유지 + commitment 충돌 검증 | 수정 과정의 구조 붕괴, commitment 후퇴 |
| **flow-refiner** | 4-2 Novelty Positioning, 3-1 Steelman 보강 | Novelty 드리프트 |
| **citation-checker** | 1-2 Accuracy (PDF 원문 대조) | #1 Over-claim (실시간 탐지), misattribution |
| **gap-finder** | 1-4 Balance (disconfirming evidence 발굴) | #9 Confirmation bias |
| **methodology-advisor** | (empirical 전용) 방법론 정당화 | 방법론 임의 선택 |
| **peer-reviewer** | 3-1 Steelman, 3-4 Reviewer Attack Surface, Iconoclast (timidity 지적) | #2 Strawman, reject 유발 major issue, 자기 배신 미탐지 |
| **abstract-translator** | 모델 라우팅 (원칙 5a): 번역은 haiku에 위임 | 메인 opus 세션의 기계적 번역 낭비 |
| **output-en-translator** | 출고 직전 한→영 번역, 인용·hedging·voice 1:1 보존, claim 강도 보존 | round-trip distortion (한글 인용블록 재번역), overclaim/underclaim, 인용 누락·임의 추가 |

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

## 🎭 Critical Mode — 새로운 관점·비판적 시각의 능동적 지원

### 왜 기본 5축만으로는 부족한가

5축 평가는 **top-tier 저널 주류 심사** 기준을 근사합니다. 그러나 Oxford·Cambridge·ENS·German humanities 같은 **비판 전통이 강한 학문 환경**, 그리고 **paradigm-shifting 논문**에서는 기본 5축이 **조용히 보수적 편향**을 만듭니다:

- Delta Map(축 4-2)은 "분야 내 incremental 차별"을 묻고, 프레임 자체의 전복은 묻지 않음
- Hedging 원칙은 대담한 주장을 "over-claim"으로 플래그할 수 있음
- Authority & Recency(축 1-3)는 주류·최신을 선호하여 **잊혀진 소수 전통**을 배제
- peer-reviewer 3인은 전부 orthodox (Reviewer 2는 paradigm 수호자 성향)

Critical Mode는 이 구조적 편향을 **의식적으로 보정**합니다.

### Critical Mode의 6번째 평가 축

| 기준 | 질문 |
|------|------|
| **C-1 Paradigm Mapping** | 분야의 dominant assumption을 명시 지명했나? |
| **C-2 Fault-line Identification** | 그 paradigm의 구조적 약점(내부 모순·외부 반증·배제 패턴)을 지명했나? |
| **C-3 Bold Defense** | Over-hedge 없이 대담한 주장을 내고 falsifiability를 제시했나? |
| **C-4 Minority Evidence Recovery** | 주류가 잊은 소수 목소리·비주류 전통을 복원했나? |

### Socratic 동반자 (critical-companion)

가장 근본적인 기능. Stage 마일스톤마다 **질문만** 생성:

**제1 제약 — 절대적**: 답변·예시·힌트·leading question 전면 금지. 답을 찾는 과정 자체가 새로운 관점의 발견이며, 그 과정은 **반드시 사용자의 것**.

### 답변 → Actionable → 결과물 반영 파이프라인

그러나 사용자 답변이 **허공에 묻히면** 의미 없습니다. 시스템의 근본 설계 원칙:

**"답변은 곧 spec이다"** — 사용자가 {stage}/critical/questions.md에 쓴 답변은 해당 프로젝트의 **사양**으로 취급되며, 모든 writing 에이전트가 반드시 참조·반영.

구현 메커니즘:

1. **{stage}/critical/commitments.md** — 답변에서 자동 추출된 actionable 사양
   - 사용자 원문 직접 인용 (추측 금지)
   - 대상 섹션·행동·완료 조건 명시
   - 4-상태 분류 (FULFILLED/PARTIAL/UNFULFILLED/CONFLICTING)

2. **모든 writing 에이전트가 필수 입력으로 참조**:
   - writing-architect: 초안 구조에 commitment 할당
   - output-editor: 수정이 commitment를 깎지 않는지 검증
   - flow-refiner: UNFULFILLED를 flow 보강 제안으로 승격

3. **투명한 반영 보고** — 작업 완료 후 반드시 출력:
   ```
   ✅ [C-001] Luria 복원 → Section 2 pp.5-7에 추가
   🟡 [C-003] 급진적 steelman → 부분 반영, 추가 수정 권장
   🔴 [C-004] 동양 철학 → 범위 부족으로 미반영
   ```

4. **sync 시스템이 미이행 탐지**: `commitment_unfulfilled` stale type으로 자동 탐지, P2-High priority로 해소 유도.

이 설계의 의미: 사용자가 **답변을 쓰는 것 자체가 설계 작업**이 된다. 답변이 단순 기록이 아니라 시스템에 대한 **명세(specification)**로 기능하며, 원고가 그 명세와 괴리되면 자동으로 드러난다. **"말과 글의 일치"**를 시스템적으로 강제.

**8 카테고리 × 버전 진화**:
1. 패러다임 의식 (분야가 당연시하는 것은?)
2. 대담성 자가 점검 (충분히 용감한가?)
3. 소수 의견 복원 (잊혀진 목소리는?)
4. 반대 사고 (정반대가 맞는다면?)
5. 지적 계보 (누구를 잇는가?)
6. 지도교수의 도전 (어디를 공격당할까?)
7. 5년 후 독자 (embarrassing할 부분?)
8. 숨은 가정 (자신이 당연시하는 것?)

매 버전마다 이전 답변과 현재 원고의 **정합성**을 자동 점검 — 답한 대담함을 원고가 구현했는가? 자기 배신 탐지.

### 철학적 배경

Critical Mode는 다음 학술 비판 전통에 근거:

- **Thomas Kuhn** (*Structure of Scientific Revolutions*): paradigm의 가정을 의식할 때만 paradigm-shift가 가능
- **Karl Popper** (*Conjectures and Refutations*): 대담한 추측 + 엄격한 검증. Over-hedging은 지적 겁.
- **Michel Foucault** (*Archaeology of Knowledge*): 지식 체제가 조직적으로 무엇을 말하지 못하게 만드는가
- **Jürgen Habermas** (*Knowledge and Human Interests*): 모든 지식은 이해관계에 서 있다
- **Ludwig Wittgenstein** (후기 *Philosophical Investigations*): 개념은 사용 맥락에서 의미를 얻는다 — 새 개념은 새 language game
- **Mary Douglas** (*How Institutions Think*): 분야는 자기 경계를 방어하며 사고 패턴을 강제한다
- **Michel de Certeau** (*The Practice of Everyday Life*): 주류 체제 밖에서 "전술적" 저항이 발생

이들의 공통 통찰: **주류는 주류인 이유로 보지 못하는 것이 있다**. 좋은 연구자는 그 맹점을 발견하는 사람.

### intellectual_ambition 설정 가이드

| 값 | 적합 케이스 |
|----|----------|
| `incremental` | 분야 내 정밀한 기여, 실증 연구, 세분화·확장 작업 |
| `critical` | 기존 프레임워크 비판 + 대안 제시, Oxford·Cambridge style 에세이 |
| `paradigm-shifting` | 분야 근본 재정의, Kuhn적 혁명 시도 |

대부분의 학위논문은 **critical**에서 시작해서 단계적으로 담대해지는 것이 현실적.

### Critical Mode와 시스템 본원 철학의 관계

이 모드는 기본 5축에 **덧붙은 것**이 아니라, 기본 철학을 **극한까지 밀고 간 형태**입니다. 시스템의 근본 원칙은 "사용자의 지적 주체성 보존"이며, Critical Mode는 특히 **비판적 주체성**을 보호합니다.

- **Cold evaluation**은 관대하지 않지만, **critical-companion은 질문만 하고 답은 안 함** — 관대함과 다른 차원의 존중
- **단일 책임 원칙**은 axis6-critical-scorer와 axis4-originality-scorer를 분리 — 전자는 paradigm 밖, 후자는 분야 내
- **Safe backtracking**은 critical-questions.archive로 확장 — 사용자의 지적 진화 전체를 보존

---

## 📓 활동 로그와 4계층 방어 철학

### 왜 로그가 필요한가

연구 글쓰기는 **수 주~수 개월**에 걸친 작업이다. 사용자는 2주 전에 쓴 초안, 3주 전의 평가, 한 달 전의 flow 구조를 종종 참조해야 한다. 인간의 기억은 이를 지탱하지 못하며, 파일 시스템도 이를 기록하지 않는다.

또한 긴 프로젝트는 필연적으로 **정체기**를 겪는다. "뭘 해야 하지?"라는 질문이 생산성을 막는 가장 큰 이유. 로그는 이 두 문제를 동시에 해결한다:

1. **Time-travel**: 과거 시점의 상태를 **구체적으로** 재조회 — archive 참조를 통해
2. **Task recommendation**: 현재 상태와 최근 활동을 **분석**하여 다음 단계 제시

### 왜 4계층인가 — LLM 불안정성에 대한 구조적 대응

LLM은 본질적으로 **procedural instruction을 누락하는 경향**이 있다. 특히:
- 긴 지시 문서 후반부에서 주의가 약화
- 부가 작업(로깅 같은)은 핵심 추론에 비해 생략될 확률 높음
- 세션/컨텍스트 전환 시 지시 기억 약해짐

이를 시뮬레이션만으로 극복할 수 없다. 따라서 **harness-level 강제**가 필요:

| 계층 | 실행 주체 | 신뢰도 | 역할 |
|------|----------|-------|------|
| 1. UserPromptSubmit hook | Claude Code harness | 100% | 사용자 입력 감지 즉시 기록 |
| 2. Stop hook | Claude Code harness | 100% | turn 종료 시 outcome 통합 |
| 3. PostToolUse(Bash) hook | Claude Code harness | 100% | 핵심 스크립트 호출 추적 |
| 4. MD 지시 | Claude | 60-80% | 각 명령 섹션의 명시적 append 호출 (fallback) |

**핵심 통찰**: Layer 1-3은 **LLM의 판단과 무관하게** 실행된다. Layer 4는 Claude가 지시를 따라야 동작. 이중 덮어쓰기로 **실제 누락률을 0에 수렴**시킨다.

### 왜 자동 복원(auto-restore)이 없는가

archive를 통해 과거 상태 **조회**는 가능하되 **자동 복원**은 거부한다. 이유:

- 복원은 **현재 파일을 덮어씀** → 사용자가 잃는 것이 복구되는 것보다 클 수 있음
- 복원 의도의 정확한 범위(어느 파일? 어느 시점까지?)를 자연어로 명확히 표현하기 어려움
- 사용자가 직접 `cp archive/{path}/* {dest}/` 수동 실행하는 것이 **명시적이고 안전**

"convenience"가 "safety"를 이기지 않는 원칙.

### 왜 프로젝트 로컬 hook인가

`.claude/settings.json`을 **프로젝트 루트**에 두는 이유:

- **Blast radius 최소화**: 이 hook은 다른 Claude Code 세션(연구와 무관한 작업)에 영향 안 줌
- **Git 추적 가능**: 팀원과 동일한 hook 구성 공유
- **사용자 전역 설정과 분리**: `~/.claude/settings.json`(전역)을 건드리지 않음
- **끄기 쉬움**: 프로젝트에서만 끄면 됨 (전역 영향 X)

### 포맷 설계 철학

```
[YYYY-MM-DD HH:MM:SS] ACTION | STAGE | TARGET | RESULT | ref:ID | agents:A,B | key=value
```

- 앞 4 필드 **고정 파이프** — 사용자가 **복사해서 바로 읽음**
- 뒤 필드 **key=value** — 기계 파싱 + 확장 가능
- **사용자가 한 줄만 복사**해도 시스템이 timestamp·ref 추출 가능

이는 "human-readable" vs "machine-parseable"의 **양립**을 목표로 한 설계. 사용자 경험과 시스템 기능이 같은 포맷에서 공존.

### 추천은 블랙박스가 아니다

`"작업 추천해줘"` 응답에는 **반드시 근거 로그 라인**이 동반된다:

```
1. 🔴 "Chapter 5 수정해줘"
   이유: [C-003] UNFULFILLED commitment
   🔗 근거 로그: [2026-04-20 14:30] 답변 반영 | 2 UNFULFILLED
```

사용자는 추천을 받고 **그것이 어디서 왔는지 검증**할 수 있다. 시스템이 "그냥 이게 좋을 것 같아요"라고 말하지 않는다. 모든 추천이 **설명 가능**해야 한다는 원칙은 이 시스템의 다른 cold evaluation·citation audit 원칙과 일관.

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
- [GUIDE.md](./GUIDE.md) — 3분 빠른 사용 가이드 (핵심만)
- [MANUAL.md](./MANUAL.md) — 전체 참고 매뉴얼 (모든 기능 상세)
- [skills/SKILL.md](./skills/SKILL.md) — 시스템 동작 정의 (Claude Code 스킬)
