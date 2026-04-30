# EVALUATION-FORMAT.md — evaluation.md 포맷 규율

> 이 문서는 `projects/{P}/{stage_folder}/evaluations/latest/evaluation.md`의 **엄격한 포맷 스펙**입니다. `evaluation_aggregator.py`의 `render()` 함수가 유일한 생성자.
>
> **이전의 `WORK-PLAN-FORMAT.md`를 대체**합니다. work-plan.md는 폐기되었고, 평가 결과 + 다음 액션 + 진행 상태가 모두 `evaluation.md`로 통합되었습니다.

---

## 1. 파일 위치

| stage | 경로 |
|---|---|
| flow | `flow/evaluations/latest/evaluation.md` |
| output | `output/evaluations/latest/evaluation.md` |
| final | `final/evaluations/latest/evaluation.md` |

`final/evaluations/latest/holistic-review.md` (final stage 한정) 별도 파일 — final-holistic-reviewer 산출.

이전 평가는 `evaluations/{NNN}-{date}/`에 archive (사본 보존).

---

## 2. 파일 전체 구조

```markdown
---
generated_at: ISO timestamp
generated_by: evaluation_aggregator.py
stage: flow | output | final
prev_eval: {NNN-date}/ or null
---

# Evaluation — {프로젝트명} ({stage})

> 📅 생성: YYYY-MM-DD HH:MM
> 단계: {stage}
> intellectual_ambition: {incremental | critical | paradigm-shifting}

---

## 🧭 다음 액션 (사용자가 지금 할 것)

{1–3개의 명확한 명령. work-plan.md를 대체하는 핵심 섹션}

---

## 📊 축별 상태 요약

{6축 카테고리 한 줄 요약}

---

## 🎯 Verdict

{Reject / Major Revision / R&R / Accept — verdict roll-up 룰 적용}

---

## ⚠️ Critical Issues (🔴 구조적 결함)

{🔴 카테고리 받은 sub-criteria만 — 없으면 "_(없음)_"}

---

## 🟠 보강 필요 (Needs Work)

{🟠 카테고리 받은 sub-criteria}

---

## 📚 RESEARCH 항목 (미해결 R-NN)

{claim-extractor가 식별한 미검색 R 항목들 — `"리서치 진행해줘"`로 일괄 처리}

---

## ✏️ WRITE 권고 (수정·작성 필요)

{axis2~6이 식별한 본문 수정·작성 권고 — 사용자가 자연어로 "X 부분 수정해줘"식 처리}

---

## 📈 이전 평가 대비 변화

{prev_eval 있을 때만 — 축별 카테고리 변동}

---

## 📦 산출 파일

{이 평가 round에서 생성·갱신된 파일 목록}
```

---

## 3. 섹션별 상세 포맷

### 3.1 다음 액션 (work-plan.md 대체)

`work-plan.md`의 "🎯 지금 실행할 명령"이 이 섹션으로 흡수됨. 우선순위 순으로 1–3개:

```markdown
## 🧭 다음 액션 (사용자가 지금 할 것)

1. `"리서치 진행해줘"` — 미해결 RESEARCH R-04, R-07, R-12 (3건). axis 1·3 보강에 필요.
2. `"03-thesis.md 수정해줘: ..."` — Section 3 보강. axis 4 🟠 → 🟡 가능.
3. `"적대적 리뷰 해줘"` — output 거의 마무리. 학파별 반박 미리 점검 권고.
```

각 액션은 **명령(백틱)** + **이유 1줄** + (선택) **예상 효과**. work-plan의 RESEARCH-NNN 카드 ID 같은 internal 식별자 노출 금지. 자연어로만.

비어 있을 때:

```markdown
## 🧭 다음 액션

_(권장 명령 없음 — 모든 축 🟢/🟡. 다음 stage로 진행 권고: 현재 flow 단계 → `"초안 작성해줘"`)_
```

### 3.2 축별 상태 요약

```markdown
## 📊 축별 상태 요약

| 축 | 이름 | 상태 | 핵심 진단 (1줄) |
|---|---|---|---|
| 1 | 레퍼런스 충실도 | 🟠 보강 필요 | UNMATCHED-EXTERNAL 4건, anchor balance 부족 |
| 2 | 논리 전개 완성도 | 🟡 적정 | thesis alignment OK, transition 일부 약함 |
| 3 | 반박·강화 논리 | 🔴 구조적 결함 | steelman 부재, falsifiability 미명시 |
| 4 | 독창성·기여도 | 🟠 보강 필요 | "So What" 블록 부재 |
| 5 | 구성개념 정의 | 🟡 적정 | 4분면 정의 명확, boundary 일부 모호 |
| 6 | 비판 렌즈 | — | Critical Mode 비활성 |

> 상세는 axis{N}-*.md 참조
```

축 emoji: 🟢 충실 / 🟡 적정 / 🟠 보강 필요 / 🔴 구조적 결함 / ⚫ 측정 불가

### 3.3 Verdict

```markdown
## 🎯 Verdict

**Major Revision**

근거: 축 3 🔴 (반박·강화 논리 구조적 결함). 통과 가능하나 의미 있는 보강 필요. 축 4 🟠도 함께 보강 시 R&R 가능.
```

Verdict 룰 (점수 평균 폐기, 카테고리 기반):

```
Reject              : ≥2 axes at 🔴 OR (axis1 AND axis5 둘 다 🔴) OR ≥3 axes at ⚫
Major Revision      : 1 axis at 🔴 (위 조건 미해당)
R&R (보강 후 통과)   : ≥2 axes at 🟠, no 🔴
Accept w/ Minor     : ≤1 axis at 🟠, 나머지 🟡 이상
Accept              : 모든 축 🟢/🟡
```

### 3.4 Critical Issues (🔴)

```markdown
## ⚠️ Critical Issues

### 축 3 — 반박·강화 논리 (🔴)
- **Steelman 부재** — 본인 4분면 이론에 대한 가장 강한 반론 (예: Doebel 2020의 가변 EF 이론과 본질적으로 다른가?)을 본문에서 정면 다루지 않음.
- **Falsifiability 미명시** — 이 4분면 이론이 어떤 데이터로 반증될 수 있는지 명시 부재.
- **권고**: Section 5에 적어도 1개 강한 반론 + 응답 블록 추가.

### 축 N — ...
```

### 3.5 보강 필요 (🟠)

```markdown
## 🟠 보강 필요

### 축 1 — 레퍼런스 충실도 (🟠)
- **Coverage**: 4 UNMATCHED-EXTERNAL claim 미해결 (R-04, R-07, R-08, R-12)
- **Authority**: latent variable approach 비판에 대한 anchor 약함 (Friedman 2017만 인용)
- → 처리: `"리서치 진행해줘"`

### 축 4 — ...
```

### 3.6 RESEARCH 항목

claim-extractor가 식별한 미검색 R-NN을 그대로 노출. 별도 RESEARCH-NNN 카드 ID 발급 안 함:

```markdown
## 📚 RESEARCH 항목 (미해결)

다음 R-NN은 `"리서치 진행해줘"` 한 번으로 일괄 검색됩니다.

### R-04 — EF의 hot/cool 통합 가능성
- 출처 문장: "두 과제 타입 간에 ... 1요인으로 수렴할 수 있다는 연구 결과들이 있다"
- 검색 쿼리: `executive function hot cool unity factor children`
- 기대 논문: hot/cool EF 단일요인 검증 / 아동기 EF 통합

### R-07 — 비-WEIRD EF 측정 invariance
- 출처: "...횡문화 EF 측정의 invariance"
- 검색 쿼리: `executive function non-WEIRD measurement invariance cross-cultural`
- 기대 논문: 횡문화 invariance 검증

### R-08 — ...
```

상세 R 정의는 `claim-extraction-{stage}.md` 참조 (이 섹션은 요약 view).

이전 round에 검색 완료된 R은 이 섹션에서 사라짐 (claim-extraction의 MATCHED 전환은 사용자 인용 확정 후).

### 3.7 WRITE 권고

WRITE-NNN 카드 ID 폐기됨. 자연어 권고만:

```markdown
## ✏️ WRITE 권고

### Section 3 (axis 4 🟠) — "So What" 블록 부재
- 위치: Section 3 Introduction 후반 또는 Section 4 시작
- 요구: (a) 분야가 잃는 것 (해결 안 되면) (b) 본 thesis가 채우는 지점 (c) 파급 경로
- → `"03-thesis.md 수정해줘: So What 블록 추가"` 또는 직접 편집

### Section 5 (axis 3 🔴) — Steelman + 응답 추가
- 위치: 결론 직전
- 요구: Doebel 2020 또는 Zelazo hot/cool 재배열에 대한 가장 강한 반론 + 4분면 이론의 차별성 응답
- → `"05-conclusion.md 수정해줘: Steelman 블록 추가"` 또는 직접 편집

### ...
```

### 3.8 이전 평가 대비 변화

```markdown
## 📈 이전 평가 대비 변화 (vs eval #003 2026-04-25)

- 축 1: 🔴 → 🟠 (UNMATCHED 8 → 4)
- 축 2: 🟡 → 🟡 (변동 없음)
- 축 3: 🟠 → 🔴 (steelman 미보강 + 새 chapter에서 반박 noise 발견)
- 축 4: 🔴 → 🟠 (positioning 보강됨)
- 축 5: 🟡 → 🟡 (변동 없음)

순효과: Major Revision 유지. 축 3 회귀 주의.
```

### 3.9 산출 파일

```markdown
## 📦 산출 파일

이 평가 round에서 생성/갱신:
- `evaluation.md` (이 파일)
- `axis1-reference.md` ... `axis5-concept.md` (축별 상세)
- `flow/claim-extraction-flow.md` (R-NN 갱신)
- 이전 평가 → `flow/evaluations/003-2026-04-25/` archive
```

---

## 4. 헤더 frontmatter 스펙

```yaml
---
generated_at: 2026-04-30T15:42:00
generated_by: evaluation_aggregator.py
stage: flow                              # flow | output | final
prev_eval: 003-2026-04-25                # 이전 평가 archive 경로 (없으면 null)
intellectual_ambition: incremental       # incremental | critical | paradigm-shifting
critical_mode: false                     # 축 6 활성화 여부
---
```

---

## 5. 작성 원칙

1. **work-plan.md는 사라짐** — 카드 ID·진행 로그·dashboard 등 work-plan 잔재 사용 금지
2. **사용자 출력에 internal ID 노출 금지** — RESEARCH-NNN, WRITE-NNN, R-NN, axis ID 등 internal tracking 코드 사용 금지. R-NN은 RESEARCH 항목·claim-extraction에서만 internal 식별자로 사용 (사용자가 보긴 하지만 자연어 컨텍스트와 함께)
3. **다음 액션이 항상 최상단** — 사용자가 파일을 열어 첫 화면에서 무엇을 해야 할지 알 수 있어야
4. **🟢/🟡만 있는 평가는 다음 stage 권고** — `"초안 작성해줘"` 또는 `"최종 완성했어"` 등으로 자연 진전
5. **모든 verdict는 카테고리 기반** (점수 평균 폐기)

---

## 6. 파싱 규칙

### 6.1 다음 액션 추출

```
정규식: /^## 🧭 다음 액션/  →  다음 ## 헤더 전까지
액션 항목: /^\d+\.\s+`"([^"]+)"`/m
```

### 6.2 미해결 R-NN 추출

```
정규식: /^### (R-\d+)/m  (## 📚 RESEARCH 항목 섹션 내)
```

### 6.3 축별 상태 추출

```
표 행 정규식: /^\| (\d) \| .+ \| (🟢|🟡|🟠|🔴|⚫) /m
```

---

## 7. 금지 사항

- ❌ work-plan.md 또는 RESEARCH-NNN/WRITE-NNN ID 참조
- ❌ task lifecycle (Active/In-progress/Blocked) 표현
- ❌ 카드 진행 로그 (이미 evaluation.md는 round 단위 산출이므로 진행 로그 불필요)
- ❌ Stage 진척도 progress bar (work-plan의 잔재 — 폴더 존재가 진척 시그널)
- ❌ R-NN별 별도 파일 출력 (claim-extraction-{stage}.md에 통합)
