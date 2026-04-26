# Research Agent — 사용 가이드

학술 글을 쓸 때 시스템이 옆에서 **레퍼런스 찾기·평가·수정 추적**을 도와주는 도구.

> **핵심 모델**: 글은 `flow`(계획) → `output`(원고) **두 단계**로 완성합니다. 각 단계에서 사용자는 **work-plan을 통해 시키거나 직접 작업**할 수 있습니다.

---

## 1. ⚡ 1분 시작

```bash
cd <research-agent 설치 폴더>     # 본인이 설치한 경로 (예: ~/Documents/research-agent)
claude
```

세션 안에서 모든 작업이 **자연어 명령**으로 진행됩니다.

설치가 안 됐으면 [README.md § 설치](./README.md#-설치) 먼저.

---

## 2. 🧠 시스템 모델

### 2.1 두 모드 — 글 완성의 두 단계

| 모드 | 폴더 | 사용자 목표 |
|------|------|-----------|
| **flow** | `projects/{P}/flow/` | flow.md 완성 (연구 방향·논증 줄거리) |
| **output** | `projects/{P}/output/` | output/*.md 완성 (실제 원고) |

**순서 (단방향)**: flow 모드 작업 → flow 완성 → **`"초안 작성해줘"` 시 output 모드로 자동 전진** → output 완성.

⚠ output 진입 후 flow로 되돌아가지 않습니다 (flow.md는 보존되지만 직접 수정 단계는 끝).

각 모드는 **self-contained** — 본문·분석 결과·평가·critical을 자기 폴더에 보관 (과거 버전은 `history/`에 자동 백업).

**모드 진행**:
- 자동 전진: `"초안 작성해줘"` 호출 시 시스템이 자동으로 output 단계로 진입
- 명시 명령: `"output으로 진행"` (flow → output 단방향)
- (예외) 강제 reset: `mode_manager.py set <project> flow --force` (CLI, 사용자 명시)

### 2.2 각 모드에서 두 가지 작업 방식

```
┌──────────────────────────────────────────────────────────────┐
│  방식 A:  work-plan을 통해 시키기                             │
│  ──────────────────────────────────                          │
│  카드 생성:                                                   │
│    • 자동 — 분석 명령("레퍼런스/내용 분석해줘")으로 카드 발급  │
│    • 수동 — 자연어로 "X 카드 추가해줘" 또는 파일 직접 편집     │
│                                                              │
│  카드 처리:                                                   │
│    • 카드의 **담당 명령** 필드 그대로 입력                    │
│    • 예: "리서치 진행해줘", "output ch3.md 수정해줘: WRITE-7" │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  방식 B:  직접 작업                                           │
│  ──────────────                                              │
│  • flow.md / output/*.md 에디터로 직접 편집                   │
│  • 논문 PDF를 papers/candidates/ 에 직접 투입                 │
│                                                              │
│  ⚠️ 직접 작업 후 반드시 후속 명령:                            │
│    파일 편집 후  → "레퍼런스 분석해줘" / "내용 분석해줘"      │
│                    (자동 sync + history 백업 + 새 카드 발급)  │
│    PDF 투입 후   → "논문 처리해줘"                            │
│                    (triage + Tier 분석 + analyzed/ 생성)     │
└──────────────────────────────────────────────────────────────┘
```

**핵심**: 두 방식은 섞어 써도 됨. 사용자가 직접 flow.md를 고치고 → AI에 분석 시키고 → 카드 받고 → 카드 처리시키고 → 다시 직접 고치고… 반복.

### 2.3 핵심 파일 (매일 보는 것)

| 파일 | 역할 |
|------|------|
| `projects/{P}/work-plan.md` | **할 일 대시보드** — 활성 카드 + 권장 명령 |
| `projects/{P}/flow/flow.md` | flow 본문 (방향) |
| `projects/{P}/output/*.md` | output 본문 (원고) |
| `projects/{P}/{stage}/evaluations/evaluation.md` | 평가 결과 |

---

## 3. 🚀 첫 프로젝트 7단계

전체 흐름은 **[Stage 1: flow 모드]** → **[Stage 2: output 모드]**.

### ━━━ Stage 1 · flow 모드 ━━━

#### ① 프로젝트 생성

```
"my-essay 프로젝트 만들어줘"
```
→ `projects/my-essay/` 폴더 자동 생성. 시작 모드는 `flow`.

#### ② flow.md 작성 (직접 작업)

`projects/my-essay/flow/flow.md`를 에디터로 열고 **줄글로** 작성:

- 연구 질문 한 문장 (`이 글은 X를 묻는다`)
- 핵심 주장 한 문장 (`본 에세이는 Y라고 주장한다`)
- 권장 흐름: 문제 → 기존 관점 비판 → 자기 제안 → 예상 반론 → 함의

체크박스·목차 형식 ❌. 줄글만.

#### ③ flow 분석 (work-plan 카드 자동 발급)

```
"레퍼런스 분석해줘"     ← flow 문장 분석 + 부족한 논문 → RESEARCH 카드 발급
"내용 분석해줘"         ← 논리·독창성 등 5축 → WRITE 카드 발급
```

생성:
- `flow/claim-extraction-flow.md` — 문장 분류 + R 목록
- `flow/evaluations/axis1~6.md` + `evaluation.md`
- `work-plan.md` — 할 일 카드 모음

#### ④ 리서치 + 논문 처리 (flow 완성)

```
"리서치 진행해줘"        ← work-plan의 RESEARCH 카드 자동 실행
                          → papers/consensus-results.md (논문 후보 리스트)
```

📥 사용자: consensus-results.md 검토 → 필요한 PDF만 `papers/candidates/`에 투입 (직접 작업).

```
"논문 처리해줘"          ← 단순화 시스템 (수집 → anchor 선언 → 분석)
```

자동 흐름 (2 단계):

1. **수집·정규화·분류** (`scripts/process_papers.py`, multiprocessing 병렬, ~3분/200편)
   - candidates/*.pdf → 정규화·dedup·격리
   - collected/{Author_Year}.pdf 이동
   - markdown/{Author_Year}.md 생성 (PDF 본문 캐시 + 페이지 마커)
   - **consensus-results.md 매핑 → 분류 결정**:
     · 🎯 최우선 OR 🔴 Steelman → analyzed/[A].{name}.md (anchor)
     · 그 외 → analyzed/[N].{name}.md (non-anchor)
     · 매칭 없음 → analyzed/[?].{name}.md (MANUAL curation 대기)
   - frontmatter 자동 채움 (consensus_category·citations·anchor 등)

2. **분석** (paper-analyst, 병렬 dispatch — 파일명 prefix로 즉시 분기)
   - **[?] paper 우선 처리**: LLM이 정밀 metadata + (a)(b)(c) 주석·카테고리 생성 → `.curation/MANUAL-NNN.md` 추가 → consensus-results.md 재조립 → [A] 또는 [N]으로 rename
   - **[A]**: opus, 깊은 분석 → ~300줄 (한 줄 요약·nuanced·인용·활용·다른 anchor 대비·비판 등)
   - **[N]**: sonnet, 가벼운 분석 → ~30-50줄 (인용 1-2개·활용 1줄)

→ 산출:
- `papers/analyzed/{Author_Year}.md` (paper별 SSOT 단일 파일)
- 사용자가 직접 편집 가능 — LLM이 다음 분석 시 그대로 존중

→ 필요시 ③④를 반복. **flow 완성**되면 다음 단계.

**관련 명령**:
```
"논문 재분석해줘"          ← flow.md 변경 후 영향 paper에 v2 append
"비판적으로 분석해줘 X"    ← critique_target=true → analyzed에 비판 섹션 추가
"인용 확인해줘"           ← output ↔ analyzed 정합성 (citation_check)
"참고문헌 만들어줘"        ← analyzed/*.md frontmatter → bibliography.md
"적대적 리뷰 해줘"         ← 학파별 반박 시뮬
```

### ━━━ Stage 2 · output 모드 ━━━

#### ⑤ 초안 작성 (flow → output 자동 전진)

```
"초안 작성해줘"
```
→ writing-architect가 구조 설계 (사용자 승인 필요) → `output/*.md` 생성.
→ 자동으로 output 단계로 전진됨 (mode_manager.advance_to_output 호출).

#### ⑥ output 분석 → 수정 반복 (work-plan 카드 처리)

```
"레퍼런스 분석해줘"      ← 자동으로 output 대상 (현재 모드 = output)
"내용 분석해줘"
```

work-plan에 `WRITE-NNN` (mode=modify) 카드 발급되면:

```
"output ch3.md 수정해줘: WRITE-007"
```
→ output-editor가 카드대로 수정 + citation-checker 자동 검증.

**반복**: 수정 → 재분석 → 새 카드 → 수정.

#### ⑦ 최종 통합 + 리뷰 (output 완성)

```
"적대적 리뷰 해줘"        ← 학파별 반박 시뮬 (학파 정의 미리)
                            → output/.adversarial-review.md
"인용 검증해줘"           ← output 인용 ↔ manifest 정합성
                            → output/.citation-lint-report.md
"참고문헌 만들어줘"       ← APA/MLA/Chicago/BibTeX
                            → output/bibliography.md (또는 .bib)
"최종 통합해줘"          ← output → final/*.md + .docx
"리뷰 체크해줘"          ← peer-reviewer 시뮬레이션
"리뷰 답변 도와줘: [리뷰 텍스트]"  ← 실제 리뷰 받았을 때
```

---

## 4. 📜 명령어 한눈

### 모드 (단방향)

| 명령어 | 동작 |
|---|---|
| `"현재 모드"` | 현재 모드 출력 |
| `"output으로 진행"` | flow → output 단방향 전진 (또는 `"초안 작성해줘"`가 자동 호출) |


### 분석 (분석해줘 ≡ 평가해줘 혼용)

| 명령어 | 동작 |
|---|---|
| `"레퍼런스 분석해줘"` | 현재 모드 적용 — claim-extractor + axis1 → RESEARCH 카드 |
| `"내용 분석해줘"` | 현재 모드 적용 — axis2~6 → WRITE 카드 |
| `"flow 레퍼런스 분석해줘"` | **모드를 flow로 자동 전환** + flow 분석 |
| `"output 내용 평가해줘"` | **모드를 output으로 자동 전환** + output 분석 |

> 💡 v3.1: 단방향 진행. flow 단계에서 `"output ..."` prefix는 *자동 전진* 시그널 (output 진입 + 분석). 단, output 단계에서 `"flow ..."` prefix는 거부됨 (flow.md 직접 수정 단계는 끝).

### 실행 (work-plan 카드 처리)

| 명령어 | 동작 |
|---|---|
| `"리서치 진행해줘"` | RESEARCH 카드 일괄 실행 |
| `"논문 처리해줘"` | candidates/ PDF triage + Tier 분석 |
| `"논문 재분석해줘"` | 보유 PDF를 새 각도로 (delta 기본) |
| `"초안 작성해줘"` | flow → output 신규 작성 |
| `"output {파일명} 수정해줘: WRITE-NNN"` | WRITE modify 카드 처리 |

### Critical 모드 (선택)

| 명령어 | 동작 |
|---|---|
| `"크리티컬 모드 켜줘"` | 현재 모드의 `critical/` 폴더 생성 + critical-companion 호출 |
| `"flow 크리티컬 모드 켜줘"` | 명시 prefix |

### 메타

| 명령어 | 동작 |
|---|---|
| `"현재 상태"` | 폴더·진행도·모드·버전/싱크 한눈 |
| `"버전 체크"` | 모든 파일 frontmatter 비교 |
| `"flow 업데이트해줘"` | flow-refiner — interactive diff 제안 (카드 발급 없음) |

---

## 5. 🔁 매일 시작 패턴

```
1. "현재 상태"        ← 어디까지 했는지 한눈 + 모드 확인
2. work-plan.md 열기  ← 활성 카드 + 권장 명령 확인
3. 권장 명령 위에서부터 처리
```

뭘 할지 모르겠으면:
```
"작업 추천해줘"       ← 활동 로그·work-plan 분석해서 다음 명령 + 이유 제시
```

---

## 6. 🎬 자주 쓰는 시나리오

### A. 새 프로젝트 시작
```
"my-essay 프로젝트 만들어줘"
→ flow.md 직접 작성
"레퍼런스 분석해줘"
"내용 분석해줘"
"리서치 진행해줘"
→ PDF 선별 → papers/candidates/ 투입
"논문 처리해줘"
"초안 작성해줘"
```

### B. output 단계 진입
```
"초안 작성해줘"            ← 자동으로 output 단계로 전진
"레퍼런스 분석해줘"        ← output 대상 (현재 모드 = output)
"내용 분석해줘"
"output ch1.md 수정해줘: WRITE-001"
```

### C. flow 단계에서 추가 보강 (output 진입 *전*)
```
flow.md 에디터로 직접 편집 → 저장
"레퍼런스 분석해줘"   ← 시스템이 hash 변경 감지 → flow 자동 v++
                       이전 버전은 history/flow/body/...-pre-bump/에 자동 백업
                       claim-extraction stale 자동 안내 + 새 RESEARCH 카드 발급
```

### D. 사용자가 work-plan에 직접 작업 추가

평가가 잡지 못한 작업도 본인 판단으로 추가 가능. **두 방법**:

**방법 1 — 자연어 채팅으로 요청**:
```
"work-plan에 카드 추가해줘:
 ch3 Section 4 EF 보편성 논증을 Kroupin 2025·Liu 2024 인용으로 강화"
```
→ AI가 의도 읽고 정식 WRITE 카드로 변환 (registry 등록 + dedup 자동).

**방법 2 — work-plan.md 에디터로 직접 편집**:
```markdown
### [TODO] Section 4 EF 보편성 논증 강화

Kroupin 2025·Liu 2024 인용 추가하면 boldness 강해질 것.
```
→ 다음 세션에 `"이 TODO 카드로 만들어줘"` 또는 `"WRITE-NNN 처리해줘"` 호출 시 AI가 정식 카드로 변환.

### E. 정체된 느낌일 때
```
"현재 상태"           ← 진행도·블로커 확인
"작업 추천해줘"
"버전 체크"           ← stale 파일 있는지 확인
```

---

## 7. 📁 폴더 구조

```
projects/{P}/
├── flow/                            계획 단계 (최신만)
│   ├── flow.md                      사용자 본문
│   ├── claim-extraction-flow.md     레퍼런스 분석 결과
│   ├── evaluations/                 axis1~6 + evaluation.md
│   └── critical/                    Critical Mode 시 생성
│
├── output/                          결과물 단계 (최신만)
│   ├── *.md                         실제 원고
│   ├── claim-extraction-output.md
│   ├── evaluations/
│   ├── critical/
│   └── .registry.json               WRITE 카드 SSOT
│
├── papers/                          자료 (4 폴더 평탄)
│   ├── candidates/                  ① 사용자 투입 PDF (대기)
│   │   └── *.pdf                    원본 (처리 후 collected 이동)
│   ├── collected/                   ② 정규화·dedup 통과한 PDF
│   │   └── {Author_Year}.pdf
│   ├── markdown/                    ③ PDF 본문 추출 캐시 (시스템 내부)
│   │   └── {Author_Year}.md         frontmatter + 페이지 마커
│   ├── analyzed/                    ④ paper별 분석 SSOT
│   │   └── {Author_Year}.md         frontmatter + 분석 본문 (사용자도 편집 가능)
│   ├── consensus-results.md         리서치 결과 누적 (4-stage 파이프라인)
│   ├── .quarantine/                 빈/손상 PDF 격리
│   │   ├── empty/
│   │   └── corrupt/
│   ├── .research-raw/               4-stage 리서치 원본 (기존 파이프라인)
│   ├── .translations/
│   └── .curation/
│
├── history/                         모든 과거 버전 통합 (자동 백업)
│   ├── flow/{body, evaluations, claim-extraction, critical}/
│   ├── output/{body, evaluations, claim-extraction, critical}/
│   └── work-plan/
│
├── work-plan.md                     활성 카드 대시보드
├── activity.log                     활동 이력
└── .current-mode                    현재 모드 (flow|output)
```

---

## 8. 🎴 카드 시스템

|  | RESEARCH | WRITE |
|---|---|---|
| **무엇** | 근거 논문 확보 | 글 작성·수정 |
| **mode** | search · reanalyze | create · modify |
| **발급 시점** | 레퍼런스 분석 시 자동 + 사용자 자율 추가 | 내용 분석 시 자동 + citation-checker 사후 + 사용자 자율 추가 |
| **Registry** | `papers/.registry.json` | `output/.registry.json` |
| **실행 명령** | `"리서치 진행해줘"` / `"논문 재분석해줘"` | `"초안 작성해줘"` / `"output X 수정해줘: WRITE-NNN"` |

**flow 수정은 카드 아님** — flow.md는 사용자 자율 영역. `"flow 업데이트해줘"`는 flow-refiner의 interactive 제안 (사용자 승인 후 즉시 반영, 카드 없음).

---

## 9. 🔢 버전 + 싱크 (자동)

각 산출물 상단 frontmatter:
```yaml
---
version: 3
content_hash: a3f8b9c
based_on:
  flow: 3
  claim-extraction: 2
updated_at: ...
updated_by: claim-extractor
---
```

**자동 동작**:
- 사용자가 본문 편집 → 다음 명령 시 hash 변경 감지 → version 자동 increment
- **이전 버전은 history에 자동 백업** (실수 복구 가능)
- 의존 파생 파일은 stale 표시 → 분석 명령 시 자동 선행 갱신 안내
- `"버전 체크"`로 모든 파일 sync 상태 확인

---

## 더 깊이

- [MANUAL.md](./MANUAL.md) — 시스템 아키텍처·내부 동작
- [PRINCIPLES.md](./PRINCIPLES.md) — 설계 철학·평가 기준
- [skills/SKILL.md](./skills/SKILL.md) — 모든 명령어·에이전트 상세
- [skills/WORK-PLAN-FORMAT.md](./skills/WORK-PLAN-FORMAT.md) — work-plan 카드 포맷 스펙
