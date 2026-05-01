# Research Agent — 사용 가이드

> 학술 글(에세이·과제·논문)을 쓸 때 **AI가 옆에서 도와주는 작업 도구**입니다.
> 연구자가 평소 하는 작업 — 읽고·메모하고·생각하고·쓰는 — 그 흐름을 그대로 유지하며,
> 시간이 많이 드는 부분 (검색·일차 분석·인용 정리)을 AI가 대신 처리합니다.

---

## 🎯 이 도구의 위치

연구자가 글 한 편 쓸 때 평소 하는 일:

```
   생각 정리 → 논문 검색 → 다운로드 → 정독 →
       ↓                                ↓
   메모 작성 ←──────── 비교·종합 ─────── 정리
       ↓
   초안 작성 → 다듬기 → 인용 검증 → 참고문헌 → 제출
```

**사람이 그대로 하는 부분** (AI가 못 하거나, 하면 안 되는 것):
- 글의 **방향과 핵심 주장** 결정
- 어떤 논문이 *내 thesis*에 맞는지 판단 (다운로드 결정)
- PDF 원문에서 **그래프·표·방법론 디테일** 확인
- 분석 결과에 **본인 통찰·의문 메모** 추가
- **최종 판단** (이 인용을 쓸지 말지, 이 단락이 충분히 강한지)

**AI가 도와주는 부분** (반복적·시간 소모적):
- 줄거리 약점 자동 진단 (5축 평가)
- 학술 데이터베이스 자동 검색
- PDF 본문 추출·정규화·중복 제거
- 인용 가능 quote 추출 (페이지 번호 포함)
- 본문 초안 작성 (분석 결과 기반)
- 인용 정확성 자동 검증
- 참고문헌 자동 생성

→ **AI는 보조, 연구자가 결정자**. AI가 만든 모든 분석·초안은 사용자가 검토하고 직접 편집할 수 있어요.

---

## ⚡ 시작하기

설치는 [README.md](./README.md) 참고. 끝났으면:

```bash
cd <research-agent 설치 폴더>     # 본인 환경
claude
```

이제 한국어 자연어로 명령하면 됩니다. 명령어를 외울 필요 없어요 — `"이런거 해줘"` 식이면 알아듣습니다.

---

## 💬 어떻게 쓰나요? — 5분 안에 시작

**ChatGPT 대화창 쓰듯**이 사용하세요. 정확한 명령어 외울 필요 없습니다.

```
사용자: "에세이 프로젝트 하나 만들어줘. 이름은 ef-essay"
시스템: ✓ 프로젝트 생성. flow.md 빈 파일 만들었어요. 거기에 줄거리 쓰시면 됩니다.
       📍 새 프로젝트 · flow 미작성
       👉 다음: flow/flow.md를 줄글로 채우기

사용자: (flow.md 직접 작성)

사용자: "이거 어떤지 평가해줘"
시스템: (5축 평가 진행) ... 축 3 (반박 논리)이 약합니다. R-04·R-07 미해결.
       📍 flow 평가 ✓ (🟠 axis3) · output 미진입
       👉 다음 권장: "리서치 진행해줘" — 미해결 R 2건

사용자: "근거 좀 찾아줘"
시스템: (Consensus 자동 검색) ... 12편 후보. papers/search-results/flow.md 참고.
       📍 ... · 미해결 R 0건
       👉 다음 권장: PDF 다운로드 → "논문 처리해줘"
```

**핵심 원칙**:
- 매 응답 끝에 **📍 진척 + 👉 다음 권장**이 자동으로 나옵니다 → 어디까지 왔고 뭐 하면 좋을지 항상 보임
- 명령이 모호하면 시스템이 *대화로* 확인합니다 ("flow 쪽 평가 맞으세요?")
- 막히면 그냥 물어보세요: `"지금 뭐 하면 좋을까?"`, `"어디까지 왔지?"`, `"이거 어떻게 보강해야 해?"`

---

## 🗺 글 한 편 쓰는 전체 과정

```
   ① 프로젝트 생성 (4 stage 폴더·빈 템플릿 모두 자동 마련)
        ↓
   ⓪ research-gap (분야 anchor 탐색·갭 발견)  ←── 표준 시작점
        ↓
   ② flow (줄거리 작성·평가)
        ↓
   ③ 논문 검색·다운로드·분석 (flow 단계 내)
        ↓
   ④ output (초안 작성·평가·수정)
        ↓
   ⑤ final (통합본·최종 평가)
        ↓
      🎉 완성
```

**생략 가능 패턴** (사용자 상황에 따라 의식적으로):
| 상황 | 시작 단계 | 생략하는 것 |
|---|---|---|
| 분야 anchor 탐색 필요 (가장 일반) | ⓪ research-gap | — |
| thesis 이미 명확 | ② flow | research-gap (research-gap.md 비워두면 자동 skip) |
| 외부에서 chapter 일부 가져옴 (드뭄) | ④ output | research-gap·flow |
| 통합본만 채점 (가장 드뭄) | ⑤ final | research-gap·flow·output |

💬 **GPT 대화창처럼 쓰세요**. 정확한 명령어를 외울 필요 없습니다 — 자연어로 의도를 말하면 시스템이 알아듣습니다 ("이 부분 보강하고 싶어", "근거 좀 더 찾아줘", "어디까지 왔지?" 등).

📍 **매 응답 끝에 진척 라인 자동 표시**: 어느 단계에 와있고 다음에 뭐 하면 좋을지 항상 1-2줄로 요약됩니다. 별도로 "현재 상태" 명령 안 해도 위치 파악 가능.

ℹ **stage prefix는 옵션**: `"flow 평가해줘"`처럼 명시하면 그 의도 우선. 미명시 시 폴더 컨텍스트로 자동 추론. 모호하면 자연어로 확인 ("flow 쪽 평가 맞으세요?").

ℹ **명령 통합 (2026-04-30)**: 이전의 `"X 레퍼런스 분석해줘"` + `"X 내용 분석해줘"` 두 명령은 **`"X 평가해줘"` 단일 명령으로 통합**되었습니다. 5축 평가(Critical Mode 시 6축)가 한 번에 실행되며 결과는 `evaluation.md`에 통합 (work-plan.md 폐기).

---

## 📋 단계별 안내

### ① 프로젝트 만들기

**명령**:
```
"my-essay 프로젝트 만들어줘"
```
(my-essay 자리에 본인 글 이름 — 예: `gpt-and-academia`)

**무엇이 생기나요?**
- `projects/my-essay/` 폴더가 통째 생성 (4-stage 표준 구조)
- `research-gap/research-gap.md` 빈 템플릿 (4 요소 안내 포함)
- `flow/flow.md` 빈 템플릿
- `papers/`, `output/`, `final/` 폴더 + 단계별 evaluations/

**다음** — 사용자 상황에 따라 시작점 선택:
- **표준** (분야 anchor 탐색부터): `research-gap/research-gap.md`에 줄글 작성 → `"리서치 갭 분석해줘"`
- **thesis 이미 명확** (생략): `research-gap/research-gap.md` 비워두기 → 바로 `flow/flow.md` 작성 → `"평가해줘"`

---

### ⓪ research-gap 단계 — 분야 anchor 탐색 (표준 시작점)

본인 주제에 대해 **"무엇이 빠져 있나"**를 먼저 조사하는 단계입니다. **박사생이 lit review 시작할 때처럼 — AI는 사서 역할로 후보 추천, anchor 채택은 본인이 결정**.

thesis가 이미 잡혔다면 이 단계 **건너뛰고 ②로** 가도 됩니다.

**작업 흐름** (Hybrid):

```
research-gap.md 작성 (5+6 요소 — '6) 앵커 논문 리서치 방향' 포함)
   ↓
"리서치 갭 분석해줘" → research-plan.md (H-NN + 사용자 검색 방향 반영)
   ↓
"앵커 논문 찾아줘" ⭐ → anchor-candidates.md
   AI가 narrow 검색 + abstract 평가 + 후보 추천 (채택 X)
   ↓
사용자: 추천 paper 다운로드 → 정독 → anchor 선별
   anchor라 판단한 것만 → papers/candidates/research-gap/ 이동
   ↓
"논문 분석해줘" → analyzed/research-gap/[R][D].*.md
   ↓
검토:
  (a) 충분 → "갭 리포트 만들어줘" → gap-report.md → flow 단계로
  (b) 부족 → research-gap.md '6) 앵커 논문 리서치 방향' 수정 → 다시 "앵커 논문 찾아줘"
```

**핵심 명령 4개**:
| 명령 | 무엇 |
|------|------|
| `"리서치 갭 분석해줘"` | research-gap.md → research-plan.md |
| `"앵커 논문 찾아줘"` ⭐ | narrow 검색 → anchor 후보 추천 (채택 X) |
| `"논문 분석해줘"` | 사용자가 옮긴 anchor PDF만 정독·분석 |
| `"갭 리포트 만들어줘"` | [R][D] 통합 → gap-report.md |

**왜 광범위 검색이 아닌가**: 이전 방식은 H 1개당 20편씩 검색해서 60-85% 노이즈가 발생했습니다. anchor discovery는 *분야의 결정적 3-5편*을 찾는 것이 목표. 박사생이 advisor·peer와 함께 *narrow*하게 좁혀가는 방식을 시스템화.

**6) 앵커 논문 리서치 방향이 중요한 이유**: 이 섹션이 검색의 focus를 결정합니다. anchor 부족·부적합 시 이 섹션을 수정하고 재요청 = iterative loop의 pivot. 박사생이 lit review 도중 *검색 방향 자체를 재공식화*하는 것을 시스템화.

**flow 단계로 넘어갈 때**: research-gap에서 분석한 핵심 논문을 flow 작업에서 **anchor로 격상** 가능:
```
"이 논문 flow anchor로 분석해줘 Smith_2024"
```
→ research-gap 단계의 [R][D] 분석을 기반으로 flow 관점의 [A] 분석을 추가 생성.

**작성 가이드**: `skills/RESEARCH-GAP-TEMPLATE.md` 참고. 특히 §6 '앵커 논문 리서치 방향' 작성법 중요.

**다음**: ② flow.md 작성 (gap-report.md를 입력으로)

---

### ② 줄거리(flow.md) 쓰기

연구자가 직접 합니다 — `projects/my-essay/flow/flow.md`를 에디터로 열고 **자유 줄글**로:

```markdown
# 본 에세이 주제

이 글은 "AI가 학술 글쓰기를 어떻게 바꾸는가"를 다룬다.
본 에세이는 AI가 보조 도구일 때만 효과적이고, 대체할 때는
원저자의 사고 형성을 방해한다고 주장한다.

## 1. 도입
AI 글쓰기 도구의 부상...

## 2. 기존 입장 (낙관·비관)
...

## 3. 본 에세이 입장 (보조 vs 대체 구분)
...

## 4. 예상 반론과 응답
...

## 5. 함의
```

**팁**:
- 한 문장으로 **핵심 주장** (`본 에세이는 X라고 주장한다`)
- 권장 흐름: 문제 → 기존 입장 → 본 입장 → 반박 → 함의
- 완벽할 필요 없음. 거친 초안도 OK — 다음 단계에서 약점 찾아줍니다.

**다음**: ③ 분석받기

---

### ③ 줄거리 평가

```
"flow 평가해줘"          ← 5축 평가 + 필요 논문 진단 + 약점·보강 항목 통합 발급
```

(이전의 `"레퍼런스 분석해줘"` + `"내용 분석해줘"` 두 명령이 통합되었습니다.)

**무엇이 생기나요?**

| 파일 | 무엇 |
|------|------|
| `flow/evaluation.md` | **종합 진단 + 작업 항목** — 5축 채점 + R-NN(레퍼런스 필요)·WRITE 항목까지 한 파일 |
| `flow/claim-extraction-flow.md` | 문장 단위 주장 분류 + 인용 매칭 (R-NN 식별자) |

> **work-plan.md는 폐기되었습니다.** 별도 카드 파일·card_registry·status JSON 모두 제거. **폴더 자체가 SSOT** — 작업 항목은 evaluation.md 안에서 관리됩니다.

**연구자가 확인하는 것**:

`evaluation.md` 5축 평가:
- 🟢 충실 / 🟡 적정 / 🟠 보강 필요 / 🔴 구조적 결함 / ⚫ 측정 불가

🔴·🟠가 있으면 evaluation.md의 작업 항목 섹션에 그대로 등재됩니다. 식별자는:
- **R-NN** (claim-extractor 발급): "이 주장의 인용 논문 찾기" — UNMATCHED 문장
- **H-NN** (gap-analyzer 발급): research-gap 단계의 가설 항목 (research-plan.md 안)

(이전의 `RESEARCH-NNN`·`WRITE-NNN` 카드 ID 시스템은 **폐기**되었습니다. 작업은 R-NN/H-NN 식별자로 직접 추적합니다.)

**선택지**:
- evaluation.md의 R-NN 항목을 따라 `"리서치 진행해줘"` 실행 → ④로
- 또는 약점이 보이면 **flow.md 직접 수정 → 다시 평가** (이 사이클 여러 번 반복 가능)

---

### ④ 논문 검색

```
"리서치 진행해줘"
```

`research-gap/research-plan.md`의 H-NN 가설 + `flow/evaluation.md`의 R-NN 항목을 **모두 한 번에** 자동 실행 → AI가 학술 DB(Consensus)에서 관련 논문을 찾아옵니다.

**무엇이 생기나요?**

| 파일 | 무엇 |
|------|------|
| `papers/search-results/research-gap.md` | research-gap 단계 검색 결과 |
| `papers/search-results/flow.md` | flow 단계 검색 결과 |

(이전의 `consensus-results.md` 단일 파일은 **단계별로 분리**되었습니다. PDF는 단계 공유, 검색·분석은 단계별 frame 분리.)

**연구자가 결정하는 것**:

`search-results/{단계}.md`를 읽고 **어떤 논문을 다운로드할지** 결정합니다. 6 카테고리로 분류되어 있음:
- 🎯 **최우선**: 핵심 (꼭 다운로드)
- 🔴 **Steelman**: 본 주장 도전 논문 (반박 재료, 다운로드)
- 🟢 **보조**: 보완 자료
- 🌏 **발달·횡문화**: 비교 문화
- ⚙️ **방법론 비판**: 측정·방법론

각 논문에 (a) 핵심 주장 / (b) 어디에 쓸지 / (c) 인용 강도가 명시.

→ **5-20편** 정도 다운로드 권장 (너무 많으면 분석 시간 ↑).

---

### ⑤ PDF 다운로드 (직접 작업)

`search-results/{단계}.md`의 URL을 클릭해 PDF 받은 후:

```
papers/candidates/research-gap/   ← research-gap 단계 입구
papers/candidates/flow/           ← flow 단계 입구
```

(현재 작업 중인 단계에 맞게 떨어뜨립니다. 둘 다에 떨어뜨려도 시스템이 자동으로 둘 다 스캔.)

파일명은 어떻든 상관없습니다 — 다음 단계에서 자동 정규화됩니다.

> 💡 사용자가 *Consensus 검색에 없는* 논문을 직접 추가해도 됩니다 (예: 지도교수 추천 논문). 시스템이 다음 단계에서 자동으로 분류·분석에 추가해줍니다.

**다음**: ⑥ 논문 처리

---

### ⑥ 논문 처리·분석

```
"논문 처리해줘"
```

이 한 명령이 두 candidates 폴더(research-gap·flow)를 **자동 스캔**해 처리합니다:
1. PDF 정규화 (이름 통일) + 중복 제거
2. PDF 본문 추출 (시스템 내부)
3. search-results와 매핑 → **자동 중요도 분류**
4. 각 논문 분석 — **단계 frame에 맞춰 분기**:
   - research-gap 단계 PDF → `[R]` (gap 발견용) 또는 `[D]` (비판 frame)
   - flow 단계 PDF → `[A]` (anchor) 또는 `[N]` (normal)

**무엇이 생기나요?**

```
papers/
├── collected/{Author_Year}.pdf       ← 정규화된 PDF 원본 (단일, 단계 공유 — 그래프·표 확인용)
└── analyzed/
    ├── research-gap/
    │   ├── [R].논문이름.md            ← research-gap frame 분석
    │   └── [D].논문이름.md            ← 비판·dialectic frame
    └── flow/
        ├── [A].논문이름.md            ← Anchor (핵심 논문, 깊은 분석)
        └── [N].논문이름.md            ← Normal (보조 논문, 간단 분석)
```

> **PDF는 단일 hub**: `collected/`에 한 번만 보관. 같은 논문을 다른 frame으로 분석하고 싶으면 `"이 논문 flow anchor로 분석해줘 X"` 같은 명령으로 별도 frame 분석을 추가 생성합니다.

**파일명 표시 (flow 단계)**:
- `[A]` = **Anchor** (search-results 🎯 또는 🔴 — 본 글의 핵심 자료)
- `[N]` = **Normal** (보조 — 가볍게 인용)

**[A] 논문 분석에 들어있는 내용** (~300줄):
- **한 줄 요약** + **저자가 실제로 한 말 (nuanced)**
- **인용 가능**: 페이지 번호 + 인용문 + 사용 권장 (support / foil / over-claim 차단)
- **본 글에서 활용**: 어느 섹션에 어떻게 쓸지 + 권장 인용 동사
- **다른 anchor 대비**: 다른 핵심 논문과 차이점·일치점
- **사용자 메모**: 본인 통찰·의문 적는 공간 (AI는 안 건드림)

**[N] 논문**: ~30-50줄 (인용 1-2개 + 활용 한 줄)

**다음**: ⑦ 정독 (선택) 또는 바로 ⑧ 초안 작성

---

### ⑦ 정독 + 메모 (선택, 핵심 논문만)

연구자가 깊이 engage할 anchor 논문 5-10편은 **AI 분석만으로 끝내지 말고 직접 정독**하는 게 좋습니다. AI 분석은 1차 도움이고, 본인의 비판적 읽기·통찰이 글의 깊이를 만듭니다.

**연구자가 자주 하는 작업 + 어디서**:

| 하고 싶은 것 | 어디서 |
|------------|--------|
| 인용문 정확한지 확인 | `papers/analyzed/flow/[A].이름.md` ("인용 가능" 섹션) |
| 그래프·표·이미지 확인 | `papers/collected/이름.pdf` (PDF 원본 직접 열기) |
| 방법론 디테일 확인 | `papers/collected/이름.pdf` (Methods 섹션) |
| 저자 가정·한계 점검 | analyzed/flow/[A].md "다른 anchor 대비" + collected/ 원문 |
| 본인 의문·메모 적기 | `analyzed/flow/[A].이름.md` "## 사용자 메모" 섹션 직접 편집 |

> 💡 **사용자 메모 섹션은 AI가 절대 안 건드립니다**. 자유롭게 적으세요. 다음 분석·초안 작성에서 AI가 본인 메모를 *prior*로 활용합니다 — 메모를 적을수록 글이 본인 색으로.

**비판적 읽기 강화 필요할 때**:
```
"비판적으로 분석해줘 Loffler_2024_common_factor"
```

→ 해당 논문 분석에 **Hidden Assumptions / Methodological Bias / Field Politics / Alternative Interpretations / Silences** 섹션 추가됨.

(critique_target=true 표시 + Mode C critical reading 추가)

**다음**: ⑧ 초안 작성

---

### ⑧ 초안 작성 (flow → output 자동 전진)

```
"초안 작성해줘"
```

자동으로 output 단계로 전진. AI가 두 단계로 진행:

1. **구조 설계**: "이런 챕터로 쓸 거다" → 사용자 승인
2. **본문 작성**: 승인된 구조대로 작성

**AI가 참조하는 것** (= 이전 단계의 산출물 활용):
- `flow/flow.md` (thesis 줄거리)
- `papers/analyzed/flow/[A].*.md`의 "인용 가능"·"본 글에서 활용" 섹션
- `papers/analyzed/flow/[N].*.md`의 인용 1-2개
- 사용자 메모 (있으면)
- `flow/evaluation.md` 약점 (보강 가이드)
- (research-gap 단계를 거쳤다면) `research-gap/gap-report.md`

**무엇이 생기나요?**

```
output/
├── 01-introduction.md
├── 02-background.md
├── 03-thesis.md
├── 04-counter.md
└── 05-conclusion.md
```

**연구자가 검토할 것**:
- 인용이 정확한지 (페이지·맥락)
- 논리 전개가 본인 thesis와 일치하는지
- 추가하고 싶은 본인 통찰이 있는지

→ 검토 후 직접 수정 가능. 또는 다음 단계 분석으로 자동 약점 진단.

---

### ⑨ 평가 + 수정 반복 (output 단계)

```
"output 평가해줘"        ← 인용 충실도 + 논리·약점 통합 진단
```

(이전의 두 명령 `"레퍼런스 분석해줘"` + `"내용 분석해줘"`가 통합되었습니다.)

**무엇이 생기나요?**

| 파일 | 무엇 |
|------|------|
| `output/evaluation.md` | 평가 결과 + 작업 항목(R-NN·WRITE) 통합 |
| `output/claim-extraction-output.md` | 문장 단위 인용 매핑 |

**작업 항목 처리**:

evaluation.md의 작업 항목을 보고 직접 명령:
```
"output 03-thesis.md 수정해줘: 인용 보강 + 반박 단락 추가"
```

→ AI가 지시대로 수정 + **인용 정확성 자동 검증**.

**반복 사이클**:
```
평가 → evaluation.md 작업 항목 확인 → 수정 → 평가 → ...
```

언제 끝내나? `evaluation.md`의 모든 축이 🟢 또는 🟡일 때 (🟠·🔴 없음).

**연구자가 직접 수정도 OK**:
- output/*.md를 에디터로 열고 직접 편집
- AI가 다음 분석에서 그 변경 반영

---

### ⑩ 마무리

#### 10-1. 적대적 리뷰 (강력 추천)

```
"적대적 리뷰 해줘"
```

특정 학파·관점에서 본 글을 공격해보는 시뮬레이션.

→ `adversarial-review.md` — 학파별 단락·문장 단위 반박.

연구자: 발견된 반박을 미리 막을 수 있도록 글 보강.

#### 10-2. 인용 검증

```
"인용 확인해줘"
```

→ `output/.citation-check-report.md` — 잘못된 인용·페이지 mismatch·anchor 미사용 검출.

#### 10-3. 참고문헌

```
"참고문헌 만들어줘"
```

→ `output/bibliography.md` (APA / MLA / Chicago / BibTeX 선택).

#### 10-4. 최종 통합

```
"최종 통합해줘"
```

→ `final/complete-draft.md` (모든 챕터 합본, .docx 옵션).

#### 10-4-1. 최종 평가 (4가지 모드)

```
"final 평가해줘"                                ← 기본: 6축 + holistic-reviewer (척추 보호 + Top 3 핵심 요약)
"final 평가해줘 --mode coursework"              ← Oxford Coursework rubric 단일 LLM (~3분)
"final 평가해줘 --mode coursework --committee"  ← 위 rubric + 5인 위원회 절차 (~10분, 적중률↑)
"final 평가해줘 --mode dissertation"            ← Oxford Dissertation rubric (10 criteria, methodology stack 포함)
```

- **기본 모드**: 통합본의 척추(메시지·thesis)를 보호하면서 6축 결과를 adjudicate. Top 3 임팩트 큰 액션만 추려서 어디까지 손볼지 명확히.
- **`--mode coursework` / `--mode dissertation`**: Oxford MSc Education marking rubric 단독 적용. Distinction/Merit/Pass/Fail 등급 + 한 등급 상승 Top 3 actionable feedback. 기존 6축·holistic 미사용 (summative grading 전용).
- **`--mode coursework --committee`** (opt-in): PDF §3.3 절차 그대로 모델링한 5인 페르소나 위원회 — Marker 1 (methods-leaning) + Marker 2 (theory-leaning) blind 1차 → Reconciliation → Third Marker (조건부 blind) → External Examiner calibration → Chair 최종 결정. 단일 LLM의 systematic bias를 페르소나 차별화로 노출 → 적중률 향상. 비용 ~5×, 제출 직전 정밀 채점 시뮬레이션 권장.

⛔ **여러 essay 평가 시 주의**: 한 conversation session에서 essay A 평가 후 essay B 평가하면 prior context가 *모든 페르소나*에 contamination됨 (anchoring bias). **각 essay는 fresh conversation에서 실행 권장**. 자세히는 `skills/BLIND-PROTOCOL.md` 참조.

#### 10-5. 모의 심사 (선택)

```
"리뷰 체크해줘"
```

가상 심사자 2-3명이 본 글 읽고 피드백.

→ `review-feedback.md`.

**🎉 완성!** 제출 또는 인쇄.

---

## 📂 폴더 구조 (연구자 시점)

```
projects/my-essay/
│
├── research-gap/                      ← ⓪ 분야 anchor 탐색 단계 (표준 시작점, 생략 가능)
│   ├── research-gap.md                ← 본인이 작성 (분야·관심·아는 지형)
│   ├── research-plan.md               ← gap-analyzer 산출 (H-NN 가설)
│   └── gap-report.md                  ← gap-synthesizer 산출 (통합 갭)
│
├── flow/                              ← flow 단계 (글의 thesis·줄거리)
│   ├── flow.md                        ← ② 본인이 작성하는 줄거리
│   ├── evaluation.md                  ← ③ 평가 + 작업 항목 통합 (work-plan 폐기)
│   └── claim-extraction-flow.md       ← 문장 단위 R-NN 매핑
│
├── papers/                            ← 연구자료 (단일 hub + 단계별 서브폴더)
│   ├── candidates/
│   │   ├── research-gap/              ← ⑤ research-gap 단계 PDF 입구
│   │   └── flow/                      ← ⑤ flow 단계 PDF 입구
│   │
│   ├── collected/                     ← 📚 정규화된 PDF 원본 (단일, 단계 공유)
│   │   └── Author_Year.pdf            ← 그래프·표·방법론 확인 시 여기 직접 열기
│   │
│   ├── analyzed/                      ← 📝 단계별 frame 분석 (사용자 ↔ AI 공용)
│   │   ├── research-gap/
│   │   │   ├── [R].이름.md            ← gap 발견 frame
│   │   │   └── [D].이름.md            ← 비판·dialectic frame
│   │   └── flow/
│   │       ├── [A].이름.md            ← Anchor (정독 + 메모 추천)
│   │       └── [N].이름.md            ← Normal (간단 인용 후보)
│   │
│   └── search-results/                ← ④ Consensus 검색 결과 (단계별 분리)
│       ├── research-gap.md
│       └── flow.md
│
├── output/                            ← 본문
│   ├── 01-introduction.md             ← ⑧ 자동 생성 본문
│   ├── 02-background.md
│   ├── ...
│   ├── bibliography.md                ← 10-3 자동 참고문헌
│   ├── evaluation.md                  ← ⑨ output 평가 + 작업 항목
│   └── claim-extraction-output.md
│
├── final/
│   ├── complete-draft.md              ← 10-4 최종본
│   └── evaluation.md                  ← 10-4-1 final 평가
│
└── adversarial-review.md              ← 10-1 반박 시뮬 (선택)
```

> **work-plan.md는 폐기**되었습니다. card_registry·status JSON 모두 제거. **폴더 자체가 SSOT** — 작업 항목은 각 단계의 `evaluation.md`에서 관리됩니다.

> 위 구조에서 **연구자가 자주 보는 곳 (5)**:
> 1. `flow/flow.md` — 본인 작성·수정
> 2. `papers/collected/*.pdf` — **PDF 원문 (그래프·표·방법론)**
> 3. `papers/analyzed/flow/[A].*.md` — 분석 + 메모 추가
> 4. `output/*.md` — 본문 검토·수정
> 5. `flow/evaluation.md` (또는 `output/evaluation.md`) — 평가·작업 항목 확인
>
> 다른 폴더 (`history/`, `.research-raw/` 등)는 시스템 내부. 신경 안 써도 됩니다.

---

## 🔁 연구자 일상 — 작업 패턴

### 며칠 만에 다시 작업할 때

```
"현재 상태"
```

→ 진행도·다음 권장 명령·미처리 카드 한눈에.

뭘 할지 모르겠으면:
```
"작업 추천해줘"
```

→ 시스템이 활동 로그 분석 → **다음 명령 + 이유** 제안.

### 글이 잘 안 풀릴 때

```
"flow 평가해줘"   (또는 "output 평가해줘")
```

→ 5축 평가가 약점을 정확히 진단. 그 진단 기반으로:
- flow.md (또는 output) 직접 수정
- 또는 evaluation.md의 작업 항목(R-NN·H-NN) 따라 진행

### 특정 논문 더 깊이 보고 싶을 때

```
"비판적으로 분석해줘 Author_Year"
```

→ Hidden Assumptions / Methodological Bias / Field Politics 등 critical 섹션 추가.

### 영감이 떠올랐을 때 — 메모만 추가

`papers/analyzed/flow/[A].이름.md` 직접 열고 `## 사용자 메모` 섹션에 자유 작성. AI는 안 건드리고 다음 작업에서 prior로 활용.

### 새 논문이 추가됐을 때 (지도교수 추천 등)

PDF를 `candidates/flow/` (또는 `candidates/research-gap/`)에 떨어뜨리고:
```
"논문 처리해줘"
```

→ 두 candidates 폴더 자동 스캔 + 단계 frame에 맞춰 분류·분석.

### research-gap 논문을 flow 단계에 활용하고 싶을 때

```
"이 논문 flow anchor로 분석해줘 Smith_2024"
```

→ research-gap 단계의 [R] 분석을 기반으로 flow 관점의 [A] 분석을 추가 생성. PDF는 `collected/`에 이미 있으니 재다운로드 X.

### flow.md를 큰 폭으로 바꿨을 때

```
"논문 재분석해줘"
```

→ 기존 분석된 논문 중 **변경 영향 받는 것만** 자동 재분석 (전체 X).

---

## 📜 명령어 빠른 참조

### 매일 쓰는 6개

| 명령 | 언제 |
|------|------|
| `"X 프로젝트 만들어줘"` | 처음 시작 |
| `"flow 평가해줘"` / `"output 평가해줘"` | flow.md / output 작성 후 (5축 평가 + 작업 항목 통합) |
| `"리서치 진행해줘"` | research-gap·flow plan의 미해결 H/R 모두 검색 |
| `"논문 처리해줘"` | PDF 받은 후 자동 분류·분석 (두 candidates 폴더) |
| `"현재 상태"` / `"작업 추천해줘"` | 매일 시작·막혔을 때 |
| `"final 평가해줘"` | 최종 통합 후 (holistic / coursework / dissertation) |

### research-gap 단계 (표준 시작점)

| 명령 | 언제 |
|------|------|
| `"리서치 갭 분석해줘"` | research-gap.md 작성 후 → research-plan.md 발급 |
| `"갭 리포트 만들어줘"` | analyzed/research-gap/ 분석 후 통합 갭 리포트 |
| `"이 논문 flow anchor로 분석해줘 X"` | research-gap 논문을 flow anchor로 격상 |

### 가끔 쓰는 8개

| 명령 | 언제 |
|------|------|
| `"초안 작성해줘"` | flow 다 됐을 때 (자동 output 진입) |
| `"output X.md 수정해줘: [지시]"` | 평가 항목 따라 수정 |
| `"논문 재분석해줘"` | flow.md 큰 변경 후 |
| `"비판적으로 분석해줘 X"` | 특정 논문 깊은 비판 |
| `"적대적 리뷰 해줘"` | 글 끝 — 학파별 반박 |
| `"인용 확인해줘"` | 글 끝 — 인용 정확성 |
| `"참고문헌 만들어줘"` | 글 끝 — 자동 bibliography |
| `"최종 통합해줘"` | 모든 챕터 합본 |
| `"리뷰 체크해줘"` | 모의 심사 |

---

## ❓ 자주 묻는 질문

**Q. AI가 만든 분석을 직접 수정해도 되나요?**
A. **됩니다.** `papers/analyzed/flow/[A].이름.md`를 에디터로 열고 자유롭게 수정·메모 추가. AI는 다음 분석에서 사용자 변경을 존중합니다. 특히 `## 사용자 메모` 섹션은 AI가 절대 안 건드립니다.

**Q. PDF 원문을 봐야 할 때 어떻게 하나요?**
A. `papers/collected/{Author_Year}.pdf` 를 PDF 리더(Preview·Acrobat·Skim 등)로 직접 엽니다. 그래프·표·이미지·방법론 디테일은 원문에서만 보입니다.

**Q. Consensus 검색에 없는 논문을 추가하고 싶어요.**
A. 현재 작업 단계의 candidates 폴더 (`papers/candidates/research-gap/` 또는 `papers/candidates/flow/`)에 PDF 떨어뜨리고 `"논문 처리해줘"`. 시스템이 단계 frame에 맞춰 자동 분류·분석.

**Q. AI가 잘못된 인용을 만들면?**
A. ⑩-2 `"인용 확인해줘"` 가 자동으로 잡습니다. 또는 사용자가 paper 분석 파일을 직접 수정해도 됩니다.

**Q. 명령어를 정확히 외워야 하나요?**
A. 아니요. `"리서치 시작해"`, `"논문 좀 찾아줘"`, `"이 글 어디가 약한지 봐줘"` 같은 자연어로도 알아듣습니다.

**Q. flow.md를 잘 못 쓰겠어요.**
A. `skills/FLOW-TEMPLATE.md` 가이드 참고. 또는 한 문단만 써놓고 `"flow 평가해줘"` → AI가 약점 알려주면 그 기반으로 보강. thesis가 흐릿하면 ⓪ research-gap 단계부터 시작해도 좋습니다.

**Q. research-gap 단계는 꼭 거쳐야 하나요?**
A. **research-gap은 표준 시작점**입니다. 분야 anchor 탐색·갭 발견을 통해 thesis를 다듬는 단계라 새 프로젝트는 일반적으로 여기부터 시작합니다. **단 thesis가 이미 명확하면 의식적으로 생략 가능** — `research-gap/research-gap.md`를 빈 템플릿 그대로 두고 바로 `flow/flow.md`부터 작성하세요. 시스템이 빈 research-gap을 자동 skip하고 flow부터 진행합니다.

**Q. PDF가 분석 안 됩니다.**
A. 빈 PDF·손상 PDF는 자동으로 격리됩니다. 다른 PDF로 다시 시도.

**Q. output 단계로 갔는데 flow를 더 보강하고 싶어요.**
A. flow.md는 그대로 두고 `"flow 업데이트해줘"`를 호출하세요. flow-refiner가 변경 제안을 만들고 승인 후 반영합니다. 그 후 `"flow 평가해줘"`로 다시 평가 가능합니다.

**Q. 작업 항목이 너무 많이 쌓여요.**
A. 정상입니다. 한꺼번에 다 처리할 필요 X. `"작업 추천해줘"`로 우선순위 높은 것부터. 작업 항목은 각 단계의 `evaluation.md`에서 관리됩니다 (work-plan 별도 파일 X).

**Q. 백업은 자동인가요?**
A. 네. 시스템이 변경 직전 `history/` 폴더에 자동 백업합니다. 망쳐도 복구 가능 (필요 시 AI에 `"이전 버전 보여줘"`).

---

## 🆘 막혔을 때

```
"현재 상태"             ← 진행도 확인
"작업 추천해줘"          ← 다음 명령 제안
"버전 체크"             ← 파일 sync 확인 (보통 AI가 알아서 함)
```

이래도 안 되면 [README.md 트러블슈팅](./README.md) 또는 [MANUAL.md](./MANUAL.md) 참고.

---

## 📚 더 깊이

| 문서 | 언제 |
|------|------|
| [README.md](./README.md) | 설치 |
| [MANUAL.md](./MANUAL.md) | 모든 기능 상세 (전문가용) |
| [PRINCIPLES.md](./PRINCIPLES.md) | 왜 이렇게 만들었나 (설계 철학) |

---

## 🎯 한 줄 요약

> **연구자는 평소처럼 읽고·메모하고·생각합니다. AI는 검색·일차 분석·인용 정리를 대신해 시간을 벌어줍니다. 글의 방향과 최종 판단은 항상 연구자.**

핵심 5가지만 기억:
1. `"X 프로젝트 만들어줘"` 시작 (thesis가 흐릿하면 → `"리서치 갭 분석해줘"`로 ⓪부터)
2. `flow.md` 줄글로 작성
3. `"flow 평가해줘"` → 약점 진단·필요 논문 R-NN 발급 (한 명령에 통합)
4. PDF 다운로드 → `"논문 처리해줘"` → `analyzed/flow/[A]` 정독·메모 추가
5. `"초안 작성해줘"` → `"output 평가해줘"` 반복 → `"final 평가해줘"`로 마무리
