# Research Agent — 사용자 매뉴얼

Top-tier 저널 심사 엄격도의 **5축 냉정 평가**를 중심으로, 줄글(prose) flow 작성부터 최종 완성까지 이끌어주는 AI 연구 관리 시스템의 **전체 참고 매뉴얼**입니다.

> - **빠르게 시작하고 싶다면** 먼저 [GUIDE.md](./GUIDE.md) (3분) 참고 — 핵심만.
> - 설치가 되어 있지 않다면 [README.md](./README.md) 참고.
> - "왜 이렇게 설계되었는가?" 궁금하면 [PRINCIPLES.md](./PRINCIPLES.md)(설계 철학) 참고.
> - **이 문서(MANUAL.md)**: 19개 에이전트·**병렬 delta 평가 + 2-pass Tier 논문 분석 아키텍처**·sync·Critical Mode·활동 로그·권한 관리·모델 라우팅 등 **모든 기능 상세** + troubleshooting.

---

## 목차

1. [시스템 철학](#-시스템-철학)
2. [전체 User Journey](#-전체-user-journey)
3. [5축 평가 기준 상세](#-5축-평가-기준-상세)
4. [에이전트 시스템](#-서브-에이전트-시스템)
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

### 4 단계 흐름

`research-gap (선택)` → `flow` → `output` → `final`. 분야 anchor 탐색이 필요하면 research-gap부터, thesis가 이미 잡혔으면 flow부터.

**핵심 변경 (2026-04-30)**:
- **명령 통합**: 이전 `"X 레퍼런스 분석해줘"` + `"X 내용 분석해줘"` → **`"X 평가해줘"` 단일** (X = flow/output/final)
- **work-plan 폐기**: 카드 시스템 (`RESEARCH-NNN`·`WRITE-NNN`·card_registry·status JSON) 모두 제거. 작업 항목은 `{stage}/evaluation.md` 내부에서 R-NN(claim-extractor)·H-NN(gap-analyzer) 식별자로 관리.
- **stage flag 추적 폐기**: 폴더가 SSOT. main agent는 매번 폴더를 스캔해 분기.
- **paper 단일 hub + 단계별 서브폴더**: PDF는 `collected/`에 한 번, 분석은 `analyzed/{research-gap,flow}/`에 단계별 frame 분리.

### 각 단계별 에이전트 사용 맵 (한눈에 보기)

| 단계 | 명령 | 핵심 에이전트 | 부가 에이전트 (자동 체이닝) | 산출물 |
|------|------|-------------|-------------------------|--------|
| 1. 프로젝트 생성 | `"[이름] 프로젝트 만들어줘"` | — | sync_state.py init | 폴더 구조 + 빈 flow.md |
| 1b. (선택) research-gap 작성 | (사용자 직접) | — | — | research-gap/research-gap.md |
| 1c. (선택) 갭 분석 | `"리서치 갭 분석해줘"` | **gap-analyzer** | — | research-gap/research-plan.md (H-NN 가설) |
| 1d. (선택) 갭 리포트 | `"갭 리포트 만들어줘"` | **gap-synthesizer** | — | research-gap/gap-report.md |
| 2. flow.md 작성 | (사용자 직접) | — | — | flow.md (prose) |
| 3. 1차 평가 | `"flow 평가해줘"` | **evaluation-orchestrator** (delta 감지·병렬 디스패치) | claim-extractor + axis1~axis6 scorers 병렬 + evaluation_aggregator.py + (ambition ≥ critical: critical-companion 마일스톤) + (output/final: citation-checker 샘플링) | axis1-reference.md ~ axis6-critical.md, **{stage}/evaluation.md** (작업 항목 통합 — R-NN·WRITE 자연어 항목), claim-extraction-{stage}.md, (+critical/questions.md v+1) |
| 4a. 리서치 실행 | `"리서치 진행해줘"` | — (MCP 직접 호출) | **research-processor** (sonnet 병렬) | search-results/{research-gap,flow}.md 누적 (양 plan의 H-NN·R-NN 모두 자동 처리), analyzed/{단계}/*.md v2+ append |
| 4b. PDF 처리 | `"논문 처리해줘"` | **paper-analyst** (단계 frame에 따라 [R][D] / [A][N] 분기), **gap-paper-analyst** (research-gap frame) | — | analyzed/{research-gap,flow}/*.md (단계별 frame, axis_tags 포함) |
| 4c. anchor 격상 | `"이 논문 flow anchor로 분석해줘 X"` | **paper-analyst** (Mode A, flow frame) | — | analyzed/flow/[A].X.md (research-gap PDF 재활용, collected/ 그대로) |
| 5a. 경량 점검 | `레퍼런스 점검해줘` | **evaluation-orchestrator** (axis1만) | **axis1-reference-scorer**, archive 스냅샷 생략 | axis1-reference.md + evaluation.md 축 1 블록만 갱신 |
| 5b. flow 보강 | `flow 업데이트해줘` | **flow-refiner** | — | flow.md 업데이트 제안 → 승인 시 flow.md 갱신 |
| 6. 1차 초안 | `초안 작성해줘` | **writing-architect** (Phase 1 → 사용자 승인 → Phase 2) | (ambition ≥ critical: commitment 추출 prehook 자동) + on-demand PDF 접근 | output/*.md, final/complete-draft.md, .docx, {stage}/critical/commitments.md 갱신 |
| 7. 2차 평가 | `flow 평가해줘` | **evaluation-orchestrator** (delta 모드, flow.md 변경 축만) | stale axis scorers + **citation-checker 30% 샘플** | archive/NNN + 갱신된 {stage}/evaluations/latest/ |
| 8. 챕터 수정 | `output {파일명} 수정해줘: ...` | **output-editor** | (ambition ≥ critical: commitment prehook) + **citation-checker** 자동 체이닝 | 수정된 chapter 파일 + 감사 리포트 + {stage}/critical/commitments.md 상태 갱신 |
| 9. 3차 평가 | `flow 평가해줘` | **evaluation-orchestrator** | stale axis scorers + **citation-checker 전량** | archive/NNN |
| 10a. 최종 통합 | `최종 통합해줘` | — | — | final/complete-draft.md + .docx 재생성 |
| 10b. 심사 시뮬 | `리뷰 체크해줘` | **peer-reviewer** (Mode A) | — | 리뷰어 3명 시뮬 리포트 |
| 10c. 최종 평가 | `flow 평가해줘` | **evaluation-orchestrator** | stale axis scorers + **citation-checker 전량 + 이전 archive 대비 new error** | archive/NNN |
| 11. 출고 영문화 | `영어로 번역해줘` 또는 `논문 제출용 영문 변환해줘` | **output-en-translator** (chapter별 ≤4 병렬, opus) | 사전 조건 점검 (Phase 2 + adversarial-reviewer + output-editor + citation-checker 통과) | output/en/*.en.md (한글 원본 보존, 영문 별도 파일) |
| 언제든 (보조) | `gap 분석해줘` | **output-gap-finder** | — | gaps-analysis.md |
| 언제든 (empirical만) | `방법론 추천/검증해줘` | **methodology-advisor** | — | 화면 보고 |
| 언제든 | `sync 확인해줘` | sync_state.py | — | stale 리스트 + 해결 가이드 |
| 언제든 | `논문 제거해줘: {파일}` | sync_state.py + (자동) citation-checker | — | archived/ 이동 + dangling 경고 |
| 언제든 | `논문 재분석해줘` | **paper-analyst** (Mode B) | — | analyzed/*.md v2+ append |
| 단독 축 재평가 | `평가해줘 axis4` 또는 `평가해줘 axis3,4` | **evaluation-orchestrator** | 명시 축만 dispatch | 해당 axis{N}-*.md 갱신 |
| 전체 강제 재평가 | `평가해줘 --full` | **evaluation-orchestrator** | `evaluation_delta.py reset` → 6축 전부 stale → 병렬 실행 | archive 스냅샷 + evaluations/latest 전량 갱신 |

### 상세 단계별 가이드

### 단계 0 — 최초 설치 (1회)

[README § 설치](./README.md#-설치) 참고.

설치 완료 후 어느 디렉토리에서든 `claude`를 실행하면 research-agent 스킬이 로드됩니다.

### 단계 1 — 프로젝트 생성

```bash
cd <research-agent 설치 폴더>     # 본인 환경의 실제 경로
claude
```

Claude에서:
```
> "my-essay 프로젝트 만들어줘"
```

자동 생성되는 구조 (2026-04-30 — work-plan 폐기 + research-gap 단계 신설 + paper 단계별 frame 분리 반영):
```
projects/my-essay/
├── research-gap/                        🆕 (선택) 분야 anchor 탐색 단계
│   ├── research-gap.md                  ← 사용자 작성 (분야·관심·아는 지형)
│   ├── research-plan.md                 ← gap-analyzer 산출 (H-NN 가설 목록)
│   ├── gap-report.md                    ← gap-synthesizer 산출 (통합 갭 진단)
│   └── history/                         ← 변경 직전 스냅샷
├── flow/                                ← flow 단계 (글의 thesis·줄거리)
│   ├── flow.md                          ← 사용자 자유 줄글
│   ├── claim-extraction-flow.md         ← 문장 단위 R-NN 매핑
│   ├── evaluation.md                    🆕 평가 + 작업 항목 통합 (work-plan 폐기, R-NN·WRITE 자연어 항목 모두 여기)
│   └── history/                         ← flow·evaluation 수정 직전 쌍 보존
├── output/                              ← 초안 섹션별 파일
│   ├── 0N-*.md                          ← 각 챕터
│   ├── claim-extraction-output.md       ← 통합 분석
│   ├── evaluation.md                    🆕 output 평가 + 작업 항목
│   └── history/{chapter_id}/            ← 챕터 수정 직전 스냅샷
├── final/
│   ├── complete-draft.md                ← 통합본
│   ├── complete-draft.docx              ← Word 문서
│   ├── evaluation.md                    🆕 final 평가 (holistic / coursework / dissertation)
│   └── (mode별 산출: holistic-review.md, coursework-evaluation.md, dissertation-evaluation.md, committee/*)
├── papers/                              ← 단일 hub + 단계별 서브폴더
│   ├── candidates/
│   │   ├── research-gap/                ← 단계별 PDF 입구
│   │   └── flow/
│   ├── collected/                       ← 정규화 PDF (단일, 단계 공유)
│   │   └── {Author_Year}.pdf
│   ├── analyzed/
│   │   ├── research-gap/                ← gap frame 분석 ([R][D])
│   │   │   ├── [R].{name}.md
│   │   │   └── [D].{name}.md
│   │   └── flow/                        ← flow frame 분석 ([A][N])
│   │       ├── [A].{name}.md
│   │       └── [N].{name}.md
│   ├── search-results/                  🆕 단계별 분리 (이전 consensus-results.md)
│   │   ├── research-gap.md
│   │   └── flow.md
│   ├── archived/                        ← "논문 제거해줘"로 이동
│   └── .research-raw/ + .translations/ + .curation/ + .context-pack.md  (시스템 내부)
├── {stage}/critical/questions.md        ← 🎭 Critical Mode: 사용자가 답하는 Socratic 질문 (ambition ≥ critical만)
├── {stage}/critical/commitments.md      ← 🎭 답변에서 자동 추출한 actionable commitment
├── history/                             ← 모든 단계 히스토리 통합
│   ├── research-gap/, flow/, output/, final/
│   └── {stage}/critical/                ← 질문·답변·commitment 버전 히스토리
├── activity.log                         ← 📓 모든 주요 작업 append-only 로그
├── .paper-metadata.json                 ← 메타데이터 + intellectual_ambition 필드
└── .sync-state.json                     ← 아티팩트 의존성·버전 추적
```

> **폐기된 것** (2026-04-30 이전 버전과의 차이):
> - `work-plan.md` + `history/work-plan/` — 작업 항목은 각 단계 `evaluation.md` 내부로 통합
> - `RESEARCH-NNN`·`WRITE-NNN` 카드 ID — claim-extractor R-NN, gap-analyzer H-NN으로 통일
> - `papers/candidates/` 평탄 (단계 prefix 없음) — `candidates/{research-gap,flow}/`로 분리
> - `papers/analyzed/*.md` 평탄 — `analyzed/{research-gap,flow}/`로 단계 frame 분리
> - `papers/consensus-results.md` 단일 → `papers/search-results/{research-gap,flow}.md` 단계 분리
> - `evaluations/latest/` + `evaluations/archive/` 별도 폴더 → `{stage}/evaluation.md` + `history/{stage}/evaluations/`

### 단계 2 — flow.md 작성 (자유 줄글)

에디터로 `projects/my-essay/flow/flow.md`를 열어 **자유 줄글**로 작성합니다. 템플릿 빈칸을 채우는 방식이 아닙니다.

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
> "flow 평가해줘"
```

자동으로 일어나는 일:

**3-1. 이전 평가 스냅샷 보존**
`{stage}/evaluations/latest/`가 비어있지 않으면 `{stage}/history/{stage}/evaluations/{NNN}-{date}-{stage}/`로 스냅샷 복사.

**3-2. claim-extractor 실행** (prose flow 전용)
- 모든 문장에 ID 부여 (S001, S002, ...)
- 5종 분류:
  - 🔴 NEEDS_CITATION (A 경험 / B 기술 / C 차용 정의 / D 반론)
  - 🟡 OPTIONAL (E 저자 확장)
  - 🟢 NO_CITATION (F 저자 기여 / G 연결·메타)
- `papers/search-results/flow.md` pool과 매칭하여 MATCHED / UNMATCHED 판정
- Over-claim / Under-claim 경고 생성
- 저장: `flow/claim-extraction-flow.md (flow stage) 또는 output/claim-extraction-output.md (draft stage)`

**3-3. evaluation-orchestrator 실행** (6축 평가, 병렬 delta 아키텍처)
- `evaluation_delta.py check`로 변경된 축(stale)만 선별
- 각 stale 축을 axis{N}-scorer에 병렬 디스패치 (서로 독립 실행)
- 축 간 상호작용 문제는 aggregator 단계 + critical-companion이 감지
- `evaluation_aggregator.py`가 축별 파일을 읽어 단일 통합 `{stage}/evaluation.md` 생성
- 저장: `{stage}/evaluation.md` (5축 + 작업 항목 통합. 이전 `evaluations/latest/axis*-*.md` 별도 파일 구조는 `{stage}/evaluation.md` 내부 섹션으로 흡수)

**3-4. 작업 항목 통합 (이전 work-plan.md 폐기, evaluation.md 안에 통합)**
- evaluation.md 끝 섹션에 작업 항목 자동 등재:
  - **R-NN** (claim-extractor 발급): UNMATCHED 문장마다 검색 키워드·기대 논문 프로필 포함
  - **WRITE 자연어 항목**: axis2~6의 각 감점 사유에서 추출된 보강 권고 (이전 `WRITE-NNN` 카드 ID 폐기)
  - **H-NN** (research-gap 단계가 활성이면): research-plan.md의 미해결 가설 항목
- card_registry·status JSON·dedup 로직 모두 폐기. 폴더가 SSOT — 중복은 evaluation.md 내부 R-NN 충돌만 점검.

**3-5. 화면 보고** — 축별 점수·등급·심사 판정·작업 수 요약.

### 단계 4 — Stage 1: 논문 리서치

#### 4-1. RESEARCH 자동 검색

```
> "리서치 진행해줘"
```

시스템이 두 plan(`research-gap/research-plan.md`의 미해결 H-NN + `flow/evaluation.md`의 미해결 R-NN)을 모두 **A·B+C 파이프라인 + D barrier** 구조의 디스크 SSOT로 처리합니다 (Stage A가 한 H/R 완료할 때마다 B+C를 background로 즉시 dispatch — 전체 wall clock = Stage A total + 1×typical Stage C):

- **Stage A** `.research-raw/{H-NN|R-NN}.json` — MCP 원본 응답 (adaptive rate limit, main 세션 직렬 검색). **저장 직후 research-processor background dispatch**.
- **Stage B+C** `.translations/{H-NN|R-NN}.md` + `.curation/{H-NN|R-NN}.md` — **research-processor(sonnet) combo worker가 단일 컨텍스트에서 번역(Phase B) → 6 카테고리 curation(Phase C) 순차 처리**, main의 Stage A와 병렬 실행. 최대 6 worker 동시.
  - 카테고리: 🎯 최우선 / 🟢 보조 / 🔴 Steelman / 🌏 발달·횡문화 / ⚙️ 방법론 비판 / 🔗 Cross
- **Stage D** `search-results/{research-gap,flow}.md` — **2-step mechanical + thin summarizer** — H-NN은 `search-results/research-gap.md`로, R-NN은 `search-results/flow.md`로 라우팅:
  1. `python3 scripts/assemble_consensus_results.py {P} --stage={research-gap|flow}` — `.curation/*.md` concat + Python URL dedup (LLM이 본문 재생성 금지)
  2. thin sonnet subagent가 파일 끝에 🏆 최중요 발견 Top-10 / 📥 PDF 우선순위 10편 / 👉 다음 단계 append
  모든 worker completed 확인 후 실행 (barrier).
- **Post-check** `scripts/research_postcheck.py {P}` — 4 스테이지 파일 수 1:1 일치 · 각 curation 6 카테고리 + 액션 아이템 3+개 · `번역 대기` 0건 자동 검증

**상세 절차 스펙**: `skills/SKILL.md` §"Consensus 검색" 참조. 각 worker는 `≤5분 wall clock · 디스크 출력 · idempotent` 규율 따름.

실행 후: papers/search-results/{단계}.md에 H-NN/R-NN 섹션 추가 (폴더가 SSOT, registry 폐기).

⚠️ **주의 — claim-extraction-flow.md는 건드리지 않음**: 검색 완료는 *논문 후보 확보*일 뿐, 특정 문장(S-NNN)을 특정 논문으로 근거 삼겠다는 *인용 확정*과 다름. `❌ UNMATCHED`는 "아직 인용 논문이 확정되지 않음"을 의미하며, 검색 Stage 1 완료만으로 자동 `✅ MATCHED` 전환되지 않는다. MATCHED 전환은 사용자가 (1) `search-results/{단계}.md`에서 PDF 다운로드 우선순위 확인 → (2) PDF 받아 `candidates/{단계}/`에 배치 → (3) `"논문 처리해줘"`로 paper-analyst 분석 → (4) `"초안 작성해줘"` 실행 시 writing-architect가 섹션별 인용 매핑을 설계하는 과정에서 비로소 확정된다.

#### 4-2. 사용자가 PDF 다운로드

`search-results/{단계}.md` 끝의 **📥 PDF 다운로드 우선순위** 섹션을 보고 상위 10편을 원문 PDF로 받아 `papers/candidates/{단계}/`에 보관합니다 (현재 작업 단계의 폴더에). 저작권 접근은 사용자 책임.

#### 4-3. PDF 처리 + 심층 분석

```
> "논문 처리해줘"
```

이 한 명령이 **두 candidates 폴더 (research-gap·flow) 모두 자동 스캔**해 처리합니다:
- `scripts/process_papers.py`가 정규화·메타·markdown 캐시 단일 패스 처리
- `.paper-metadata.json` 업데이트
- PDF를 `collected/`로 이동 (단일 hub)
- **paper-analyst 에이전트 병렬 호출** — 각 논문에 대해 단계 frame에 따라 분기:
  - **research-gap 단계 PDF**: `gap-paper-analyst` → `analyzed/research-gap/[R].{name}.md` (gap frame, 분야 어디서 막혔나) 또는 `[D].{name}.md` (비판·dialectic frame)
  - **flow 단계 PDF**: `paper-analyst` → `analyzed/flow/[A].{name}.md` (anchor, 깊은 분석) 또는 `[N].{name}.md` (normal, 가벼운 분석)

#### 4-4. (선택) anchor 격상 — research-gap 논문을 flow에 활용

```
> "이 논문 flow anchor로 분석해줘 Smith_2024"
```

PDF는 `collected/`에 이미 있으므로 재다운로드 X. paper-analyst가 flow frame으로 [A] 분석을 추가 생성 → `analyzed/flow/[A].Smith_2024.md`. 기존 `analyzed/research-gap/[R].Smith_2024.md`는 그대로 보존 (서로 다른 frame).

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
  - [RESEARCH-007] S055의 매칭 논문이 기대 프로필 미달 → 재검색 권장
```

### 단계 6 — (선택) Flow 업데이트

새로 확보한 논문으로 논증 자체를 강화하고 싶다면:

```
> "flow 업데이트해줘"
```

writing-architect가 새 논문 기반으로 축 3(Steelman 보강)·축 4(Novelty Delta 명확화) 관점의 **문단 단위 수정 제안**을 diff 형태로 보고합니다. 사용자가 수락 여부를 개별 선택한 뒤 적용됩니다.

반영 후에는 **전체 재평가 "flow 평가해줘"** 가 의미 있어집니다.

### 단계 7 — Stage 2: 1차 초안 작성

```
> "초안 작성해줘"
```

writing-architect가 2단계로 동작:

**Phase 1 — 논증 구조 설계** (자동, 사용자 승인 필요)
- flow.md + 모든 `papers/analyzed/{stage}/*.md` 종합
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
- 섹션별 파일: `output/01-introduction.md`, `02-background.md`, ...
- 통합본: `final/complete-draft.md` + `final/complete-draft.docx`

### 단계 8 — 2차 평가 (초안 후)

```
> "flow 평가해줘"
```

이제 전체 5축이 **모두 유의미하게 움직입니다**. 평가 직전 현재 `latest/`가 `archive/002-{date}-v1/`로 스냅샷 보존됩니다.

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
3. **citation-checker 에이전트 자동 호출**:
   - 수정된 챕터의 모든 인용을 `papers/collected/`의 원문 PDF와 대조
   - Accuracy: over-claim, misattribution, fabrication 탐지
   - APA 형식 체크
   - 인용 분포 분석
4. 즉시 수정 필요 건을 보고

모든 챕터를 순회 수정 후 다시 "flow 평가해줘" 실행 → `archive/003-{date}-revised/` 생성.

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
> "flow 평가해줘"
```

`archive/004-{date}-final/` 스냅샷 생성. 모든 축이 🟢 충실(또는 🟡 적정 이상)이고 종합 판정이 🟢 Accept이면 제출 준비 완료.

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

**담당 에이전트**: citation-checker (감사), paper-analyst (분석), Consensus MCP (검색)

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

**담당 에이전트**: axis4-originality-scorer

### 축 5. 구성개념 정의 정밀도

| 하위 기준 | 질문 | 감점 예시 |
|----------|------|----------|
| 5-1 Definition | 핵심 용어 정의·일관 사용? | "'규칙 깊이' 정의 부재" −15 |
| 5-2 Operationalization | 관찰 가능 지표? | "자발성 구분 기준 없음" −12 |
| 5-3 Boundary | 적용/비적용 범위 명확? | "경계 조건 부재" −8 |
| 5-4 Categorical/Dimensional | 범주/연속 선택 근거? | "이분법 사용하며 근거 없음" −10 |

**담당 에이전트**: axis5-concept-scorer

---

## 🤖 에이전트 시스템

전문 서브에이전트 (평가 오케스트레이션 8 + final 평가 3 + coursework 위원회 5 + paper 처리 2 [paper-analyst·gap-paper-analyst] + research-gap 2 [gap-analyzer·gap-synthesizer] + 생성·수정 4 + Critical Mode 1 + 보조 3 + 유틸리티 2 + 출고 번역 1). 각 에이전트는 단일 책임을 가지며, 필요 시 서로 체이닝(자동 호출)된다.

**평가 아키텍처 (2026-04-23 리팩터)**: 단일 `evaluation-orchestrator` 오케스트레이터를 **병렬 delta 아키텍처**로 분해. `evaluation-orchestrator`가 delta 감지 후 6개 axis scorer를 동시 디스패치. 이전 10-12분 → 2-5분. 자세히는 `plan.md` 참고.

**모델 라우팅**: 각 에이전트는 작업 성격에 맞는 모델로 실행된다 — 판단·글쓰기는 `opus`, 구조화 분석·검증은 `sonnet`, 기계적 번역은 `haiku`. 각 에이전트 파일의 frontmatter `model` 필드에 기본값. 비용·속도 근거는 [PRINCIPLES.md — 모델 라우팅](./PRINCIPLES.md#모델-라우팅-비용속도-최적화) 참고.

**Critical Mode**는 프로젝트의 `intellectual_ambition`이 `critical` 또는 `paradigm-shifting`일 때 활성화되며, 비판적 시각·새로운 관점·패러다임 도전을 능동적으로 지원한다.

### 📊 에이전트 분류 (6 카테고리)

#### 평가 오케스트레이션 (8개) — 병렬 delta 아키텍처

| 에이전트 | 단일 책임 | 모델 | 호출 시점 |
|---------|----------|------|----------|
| **evaluation-orchestrator** 🎯 | Delta 감지 + stale 축 병렬 디스패치 + aggregator 호출. 스스로 채점하지 않음 | opus | `flow 평가해줘` 진입점 |
| **axis1-reference-scorer** | 축 1 레퍼런스 충실도 (Coverage·Accuracy·Authority·Balance). claim-extraction 집계 + PDF spot-check | sonnet | orchestrator 자동 / `레퍼런스 점검해줘` alias |
| **axis2-logic-scorer** | 축 2 논리 전개 (Argument·Transition·Thesis·Scope). **flow.md만** 읽음 | opus | orchestrator 자동 |
| **axis3-defense-scorer** | 축 3 반박·강화 (Steelman·Falsifiability·Limitations·Attack Surface · **3-5 Engagement Discipline (over-defense penalty)**). `axis_tags: steelman` 논문 3-5편만 | opus | orchestrator 자동 |
| **axis4-originality-scorer** | 축 4 독창성 (So What·Novelty·Layer·Implications). `axis_tags: delta` 논문 3-5편만 | opus | orchestrator 자동 |
| **axis5-concept-scorer** | 축 5 구성개념 정의 (Definition·Operationalization·Boundary·Categorical). **flow.md만** | sonnet | orchestrator 자동 |
| **axis6-critical-scorer** 🎭 | 축 6 비판적 시각 (Paradigm·Fault-line·Bold Defense·Minority Recovery · **C-5 Engagement Discipline (over-defense penalty)**). `axis_tags: minority` 논문 + critical-questions/commitments | opus | ambition ≥ critical 시 orchestrator 자동 |
| **final-holistic-reviewer** 🛡 | **stage=final 전용**. aggregator 직후 dispatch. 통합본 척추 articulation + 통합 전용 검사 + 6축 카드 adjudication (5 verdict). 핵심 요약(Top 3) 산출 | opus | final stage orchestrator 자동 |
| **final-coursework-evaluator** 🎓 | **`final 평가해줘 --mode coursework` 한정**. Oxford Coursework rubric (8 criteria × 6-band). `--committee` 부재 시 단독 평가, 부재 시 5-Phase orchestrator | opus | --mode coursework |
| **coursework-marker-1** 👤 | **위원회 모드 한정**. Internal Examiner (methods-leaning). Phase 1 blind. 구조·rigour·citation detail strict | opus | --committee Phase 1 |
| **coursework-marker-2** 👤 | **위원회 모드 한정**. Internal Examiner (theory-leaning). Phase 1 blind. 이론·비판·originality strict | opus | --committee Phase 1 |
| **coursework-third-marker** 👤 | **위원회 모드 한정**. Senior Generalist. Phase 3 blind tie-breaker (Marker 1·2 합의 실패 시만 발동) | opus | --committee Phase 3 (조건부) |
| **coursework-external-examiner** 👤 | **위원회 모드 한정**. Cross-field calibration. raw mark 미부여, systematic bias 권고만 | opus | --committee Phase 4 |
| **coursework-chair** 👤 | **위원회 모드 한정**. Chair of Examiners. Phase 5 reconciliation·최종 mark·Top 3 결정. PDF §3.3 절차 준수 | opus | --committee Phase 5 |
| **final-dissertation-evaluator** 🎓 | **`final 평가해줘 --mode dissertation` 한정**. Oxford MSc Education Dissertation rubric (10 criteria × 6-band, methodology stack 포함) | opus | --mode dissertation |
| **claim-extractor** 📝 | 문장 단위 주장 추출·5종 분류·3-way 매칭 | sonnet | axis1이 stale일 때 orchestrator가 선행 호출 |

스크립트 동반:
- `scripts/evaluation_delta.py` — 축별 입력 해시 기반 stale 감지. `check` / `mark-done` / `reset` 서브커맨드
- `scripts/evaluation_aggregator.py` — 축별 md 파일을 합쳐 `evaluation.md` 생성 (summary + delta 표 + 심사 판정)
- `scripts/sync_state.py snapshot-evaluation {project} {trigger}` — `{stage}/evaluations/latest/` 전체를 archive로 복사

#### Critical Mode 전용 (1개) — ambition ≥ critical 시 활성화

| 에이전트 | 단일 책임 | 모델 | 호출 시점 |
|---------|----------|------|----------|
| **critical-companion** 🤔 | Socratic 질문 생성 (답변 절대 금지) + 이전 답변-원고 정합성 점검 | opus | Stage 마일스톤 자동 / `질문 업데이트해줘` |

**critical-companion의 절대 원칙**: 질문만 생성하고 **답변 예시·초안·암시·leading question 절대 금지**. 답을 찾는 과정 자체가 새로운 관점의 발견이며, 그 과정은 사용자의 것이어야 한다.

(축 6 심사는 `axis6-critical-scorer`가 담당. critical-companion은 질문 생성 전담.)

#### 생성·수정 (5개)

| 에이전트 | 단일 책임 | 읽는 것 | 쓰는 것 | 호출 시점 |
|---------|----------|--------|---------|----------|
| **paper-analyst** | flow stage 분석: anchor `[A]` (opus, ~300줄) / normal `[N]` (sonnet, ~30-50줄) / Mode B 재분석 / Mode C critical | papers/markdown/{name}.md (PDF 캐시), flow.md, 다른 anchor analyzed/flow/[A].*.md (cross-ref) | papers/analyzed/flow/[A\|N].{name}.md | `논문 처리해줘` (flow candidates 분기) / `논문 재분석해줘` (B) / `비판적으로 분석해줘` (C) / `이 논문 flow anchor로 분석해줘 X` (research-gap → flow 격상) |
| **gap-paper-analyst** 🆕 | research-gap stage 분석: gap 발견 frame `[R]` (sonnet) / 비판·dialectic frame `[D]` (opus) | papers/markdown/{name}.md, research-gap.md, research-plan.md | papers/analyzed/research-gap/[R\|D].{name}.md | `논문 처리해줘` (research-gap candidates 분기) |
| **gap-analyzer** 🆕 | research-gap.md 분해 → research-plan.md (H-NN 가설 발급) | research-gap/research-gap.md | research-gap/research-plan.md | `리서치 갭 분석해줘` |
| **gap-synthesizer** 🆕 | analyzed/research-gap/[R][D].*.md 통합 → gap-report.md | analyzed/research-gap/*.md, research-plan.md | research-gap/gap-report.md | `갭 리포트 만들어줘` |
| **writing-architect** | **신규 챕터 창작** (Phase 1 구조 설계 → 사용자 승인 → Phase 2 초안) | flow.md, papers/analyzed/*.md, on-demand papers/markdown/*.md 또는 PDF | output/*.md, final/*.md(.docx) | `초안 작성해줘` |
| **output-editor** ✏️ | **기존 챕터 국소 수정** (구조 유지, 지정 부분만) — writing-architect와 구분 | 대상 chapter, 수정 지시, papers/analyzed/*.md | 수정된 chapter 파일 | `output {파일명} 수정해줘: ...` (자동) |
| **flow-refiner** 📝 | **flow.md 보강 제안만** (직접 수정 금지, diff 승인 후 반영) | flow.md, 새 papers/analyzed/*.md, evaluation.md 감점 사유 | diff 제안 (승인 시 flow.md 반영) | `flow 업데이트해줘` |
| **citation-checker** | output ↔ analyzed/*.md 정합성 검증 (인용 매칭·페이지 정확성·anchor 미사용·over-claim 위험). citation-checker 단순화 v3 | output/*.md, papers/analyzed/*.md | output/.citation-check-report.md | `인용 확인해줘` / `output {파일} 수정해줘` 후 자동 체이닝 |
| **adversarial-reviewer** | 학파별 단락·문장 단위 반박 시뮬 | output/*.md, flow/adversarial-schools.yaml, papers/analyzed/{anchor}.md | adversarial-review.md | `적대적 리뷰 해줘` |

#### 보조 (3개, 수동 호출)

| 에이전트 | 단일 책임 | 호출 시점 | 노트 |
|---------|----------|----------|------|
| **output-gap-finder** | **분야(field)의 빈틈** 5종(방법론·응용·데이터·이론·시간) 탐색 | `gap 분석해줘` | → *후속 연구 아이디어* 도출용 |
| **methodology-advisor** | 방법론 추천(Advisor 3가지 비교) 또는 검증(Critic) | `방법론 추천/검증해줘` | ⚠️ **empirical 프로젝트 전용** — theoretical essay에서는 사용 안 함 |
| **peer-reviewer** | Mode A 가상 심사자 2~3명 + **Reviewer 4 Iconoclast (ambition ≥ critical 시 자동 추가)** / Mode B 실제 리뷰 대응 | `리뷰 체크해줘` / `리뷰 답변 도와줘` | Stage 4 최종 품질 게이트. Iconoclast는 timidity·paradigm 내부 머무름·자기 배신 탐지 |

#### 유틸리티 (2개, 자동)

| 에이전트 | 단일 책임 | 모델 | 호출 시점 | 노트 |
|---------|----------|------|----------|------|
| **research-processor** 🔄 | 단일 카드의 **Phase B(번역) + Phase C(6-카테고리 curation)** 순차 수행 | **sonnet** | `"리서치 진행해줘"` 실행 중 main이 Stage A 완료 즉시 background dispatch (카드당 1 worker, 최대 6 병렬) | Stage A와 병렬 실행 — 전체 wall clock = Stage A total + 1×typical Stage C로 단축 |
| **abstract-translator** 🌐 | 논문 영어 abstract 원문 → 한글 번역 (요약 금지, 전문 번역) | **haiku** | paper-analyst 후 PDF abstract 번역 / RESEARCH 외 독립 번역 요청 | 비용 최적. **RESEARCH Stage B는 research-processor가 직접 수행**하므로 이 agent는 호출하지 않음 (번역 규칙 스펙만 참조됨) |

#### 출고 번역 (1개, 수동)

| 에이전트 | 단일 책임 | 모델 | 호출 시점 | 노트 |
|---------|----------|------|----------|------|
| **output-en-translator** 🇬🇧 | 완성된 한글 chapter/output을 학술 영어로 번역 — (Author, Year) 인용 1:1 보존, hedging·voice·논증 구조 유지, 분야 컨벤션(APA 7 기본) 적용. abstract-translator의 반대 방향 | **opus** | `"영어로 번역해줘"` / `"논문 제출용 영문 변환해줘"` | **사전 조건**: writing-architect Phase 2 + adversarial-reviewer Phase 2.5 + output-editor + citation-checker 통과 후만. direct quote는 영어 원문 fetch (한글 round-trip 금지). chapter별 ≤4 병렬 |

---

### 🔍 혼동하기 쉬운 쌍 명확화

#### output-gap-finder vs axis4-originality-scorer

| 항목 | output-gap-finder | axis4-originality-scorer |
|------|-----------|---------------------|
| **주어** | **분야(field)** | **이 논문(this paper)** |
| **질문** | "분야 전반에서 뭐가 안 다뤄졌는가?" | "이 논문이 분야에 **새로** 뭐를 더하는가?" |
| **용도** | 후속 연구 아이디어, 미래 방향 | 현 논문의 novelty positioning, "So What?" 검증 |
| **출력** | gaps-analysis.md (5종 Gap + 난이도·임팩트) | axis4-originality.md (Delta Map + 축 4 점수) |
| **호출 시점** | 수동, 아이디어 발상 단계 | evaluation-orchestrator 자동 (stale 시) |

둘 다 "빠진 것"을 다루지만 **주어가 다름**. 혼동 시 gap-finder를 "미래 연구 제안 도구", axis4-originality-scorer를 "현 논문 기여 심사 도구"로 기억.

#### writing-architect vs output-editor vs flow-refiner

| 항목 | writing-architect | output-editor | flow-refiner |
|------|------------------|----------------|--------------|
| **대상** | output/* **신규 창작** | output/* **기존 수정** | **flow.md 보강 제안** |
| **구조 설계** | ✅ Phase 1 필수 | ❌ (기존 구조 유지) | ❌ (제안만) |
| **사용자 승인 시점** | Phase 1 후 (구조 확인) | 즉시 수정 (지시 명확) | 제안 후 (반영 승인) |
| **직접 파일 수정** | ✅ output/* 생성 | ✅ output/* 수정 | ⚠️ 승인 후에만 |
| **후속 에이전트** | — | citation-checker 자동 체이닝 | — |
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
  ├─ analyzed/*.md        → 🔄 RESEARCH(reanalyze) 권장
  ├─ claim-extraction.md  → 재생성 필요
  ├─ evaluation.md         → 재생성 필요
  ├─ evaluation.md        → 재채점 필요
  └─ output/*.md        → sync 경고

papers/collected/ 추가
  ↓ invalidates
  ├─ claim-extraction.md  → MATCHED 재계산
  ├─ evaluation.md         → R-NN 검색 완료 반영
  └─ evaluation.md        → 축 1 재채점 권장

papers/collected/ 삭제
  ↓ invalidates
  ├─ claim-extraction.md  → MATCHED → UNMATCHED 역전환
  ├─ output/*.md        → dangling citation 탐지
  └─ evaluation.md        → 축 1 감점

analyzed/*.md 버전 업 (v1 → v2)
  ↓ invalidates
  └─ output/*.md (해당 논문 사용 챕터)  → "새 분석 반영" 권장

output/0N.md 수정
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

# v2 스냅샷 (모두 자동 호출되지만 수동 사용 가능)
python3 scripts/sync_state.py snapshot-flow {project} <trigger>
#   flow/flow.md + flow/claim-extraction-flow.md 쌍을 history/flow/body/{NNN}-{date}-{trigger}/로

python3 scripts/sync_state.py snapshot-output {project} <trigger> <chapter.md>
#   단일 챕터 + 현재 claim-extraction-output.md를 history/output/body/{chapter_id}/{NNN}-*/로

python3 scripts/sync_state.py snapshot-outputs {project} <trigger> [chapter.md]
#   전체 챕터 일괄 (각 챕터별 개별 NNN 생성) 또는 단일 파일

# snapshot-work-plan 명령은 폐기됨 (work-plan.md 자체가 폐기). evaluation.md는 round 단위 archive.

python3 scripts/sync_state.py snapshot-evaluation {project} <trigger>
#   {stage}/evaluations/latest/를 {stage}/history/{stage}/evaluations/{NNN}-{date}-{trigger}/로 **증분** 복사 + manifest.json

python3 scripts/sync_state.py snapshot-critical-questions {project} <trigger>
python3 scripts/sync_state.py snapshot-critical-commitments {project} <trigger>
#   critical-*.md를 .archive/{NNN}-{date}-{trigger}.md로
```

### 평가·논문 처리 전용 스크립트

```bash
# 평가 delta (축별 stale 판정, stage-aware)
python3 scripts/evaluation_delta.py check {project} --stage=flow|output|final
python3 scripts/evaluation_delta.py compute-inputs {project} --stage=...
python3 scripts/evaluation_delta.py mark-done {project} <axis1,axis2,...> --stage=...
python3 scripts/evaluation_delta.py reset {project}

# 평가 aggregator (axis*-*.md → evaluation.md 단일 갱신)
python3 scripts/evaluation_aggregator.py {project}
#   - 기존 v1 work-plan은 history/work-plan-archive/로 이동 (사용자가 한 번 마이그레이션)
#   - claim-extraction의 R-NN을 evaluation.md `📚 RESEARCH 항목` 섹션으로 그대로 노출 (별도 카드 발급 없음)
#   - 대시보드 재계산 + 사용자 브리핑 섹션 갱신

# 논문 triage 관리 (Pass 1 결과 집계·tier 승격)
python3 scripts/paper_triage.py summarize {project}
python3 scripts/paper_triage.py list {project} --tier=1|2|3
python3 scripts/paper_triage.py promote {project} <filename> --to=1|2|3

# 논문 재분석 delta (flow 섹션 변경 영향 논문만 반환)
python3 scripts/paper_reanalysis_delta.py {project} [--full]

# 프로젝트 v1→v2 마이그레이션 (일회성, 멱등)
python3 scripts/archive/migrate_v2.py {project} [--dry-run]
python3 scripts/archive/migrate_v2.py --all [--dry-run]
```

## 📚 Paper Analysis System (v3.2 — 단일 hub + 단계별 frame)

이전 v3.1 (`analyzed/{name}.md` 평탄)은 **폐기**. 2026-04-30 리팩터로:
- **PDF는 단일 hub** (`collected/`) — 단계 공유, 같은 논문을 양 단계에서 참조 가능
- **분석은 단계별 frame 분리** (`analyzed/{research-gap,flow}/`) — 각 단계의 인지적 frame이 다르므로

### 폴더 구조

```
papers/
   candidates/
      research-gap/{original}.pdf   ← research-gap 단계 PDF 투입
      flow/{original}.pdf           ← flow 단계 PDF 투입
   collected/{Author_Year}.pdf      ← 정규화·dedup 완료 (단일 hub, 단계 공유)
   markdown/{Author_Year}.md        ← PDF 본문 캐시 (시스템 내부)
   analyzed/
      research-gap/
         [R].{Author_Year}.md       ← gap 발견 frame (분야 어디서 막혔나)
         [D].{Author_Year}.md       ← 비판·dialectic frame
      flow/
         [A].{Author_Year}.md       ← Anchor (깊은 분석 ~300줄)
         [N].{Author_Year}.md       ← Normal (가벼운 분석 ~30-50줄)
   search-results/
      research-gap.md               ← Consensus 검색 (research-gap stage)
      flow.md                       ← Consensus 검색 (flow stage)
   .quarantine/{empty,corrupt}/     ← 격리
```

같은 PDF가 두 frame에 동시 존재 가능 (예: research-gap 단계에서 [R]로 분석된 후, `"이 논문 flow anchor로 분석해줘 X"`로 flow 단계 [A] 분석 추가).

### analyzed/{name}.md — paper SSOT (frontmatter + 본문)

```yaml
---
status: analyzed              # collected | analyzed | rejected | scope_out
anchor: true|false
critique_target: false
last_analyzed: 2026-04-25T...
based_on:
  flow_md_hash: <hash>
  markdown_hash: sha256:...
artifacts:
  pdf: papers/collected/{name}.pdf
  markdown: papers/markdown/{name}.md
axis_tags: [steelman, delta]
consensus_category: "🔴 Steelman"
prior_score: 92
cross_research_count: 4
citation_state:
  use_count_in_output: 0
  direct_quotes_used: []
  paraphrase_count: 0
user_overrides: null          # 사용자 dict (Mode B에도 보존)
rejection_reason: null
---

(분석 본문 — 아래 분기별 섹션)
```

### 분석 분기 — anchor / non-anchor 이진

| 분기 | 모델 | 분량 | 섹션 |
|------|------|------|------|
| **anchor** (사용자 선언) | opus | ~300줄 | 한 줄 요약 / nuanced / 인용 가능 / 본 글에서 활용 / 다른 anchor 대비 / 보강 후보 / 사용자 메모 / (critique_target=true 시) 비판적 읽기 |
| **non-anchor** | sonnet | ~30-50줄 | 한 줄 요약 / 인용 가능 (1-2) / 본 글에서 활용 (1줄) |

### Mode B — 재분석 (flow.md 변경 후)

기존 analyzed/{name}.md 본문 그대로 + 끝에 `## [v2 — date]` 섹션 append.
v1 절대 수정 X. user_overrides·사용자 메모 영역 절대 건드리지 않음.

### 명령 흐름 (사용자 관점)

```
1. search-results/flow.md 검토 → PDF candidates/에 투입
2. "논문 처리해줘"
   → process_papers.py (multiprocessing, 정규화·dedup·markdown)
   → paper-analyst dispatch (병렬, anchor 깊은 + non-anchor 가벼운)
3. "초안 써줘" → output.md (analyzed/*.md 활용)
4. "인용 확인해줘" / "참고문헌 만들어줘" / "적대적 리뷰 해줘"
```

### 신규/축소 시스템

**활성 scripts (4)**:
- `process_papers.py` — multiprocessing PDF 단일 패스
- `citation_check.py` — output ↔ analyzed 정합성
- `bibliography.py` — APA/MLA/Chicago/BibTeX

**활성 agents (4 paper 관련)**:
- `paper-analyst.md` — 단일 출력 analyzed/{name}.md (orchestration 흡수)
- `writing-architect.md` — analyzed/*.md 직접 참조
- `citation-checker.md` — 단순화 v2
- `adversarial-reviewer.md` — 학파별 반박 시뮬

**폐기됨 (이미 삭제됨 — git history에서 복원 가능)**:
- paper_registry.py, collect_papers.py, paper_prior_score.py, anchor_candidates.py, distribution_sanity.py, paper_triage.py, extract_metadata.py, render_*.py (5개), citation_lint.py
- paper-processing-orchestrator.md, cross-paper-discourse-mapper.md, citation-auditor.md (→ citation-checker로 대체)

### CLI 빠른 참조

```bash
python3 scripts/process_papers.py {project} [--workers=8] [--dry-run] [--limit=N]
python3 scripts/citation_check.py {project} [--json]
python3 scripts/bibliography.py {project} [--format=apa|mla|chicago|bibtex] [--include-anchor-unused]
```

### 사용자 직접 편집 자유

- **paper.md (analyzed/*.md)는 사람·LLM 공용 SSOT**: 사용자가 메모·수정 자유. LLM이 다음 분석에서 그 변경 존중.
- **frontmatter `user_overrides`**: 사용자가 LLM 판단 위에 영구 override (Mode B에도 보존).
- **`## 사용자 메모` 섹션**: anchor만, LLM 절대 수정 X.

---

### 에이전트별 sync 호출 의무 (누락 시 아티팩트 어긋남)

각 에이전트가 작업 완료 시점에 호출해야 하는 sync·snapshot 명령 매트릭스:

| 에이전트/명령 | 시점 | 호출 명령 |
|--------------|------|----------|
| **evaluation-orchestrator** | 평가 시작 전 | `snapshot-evaluation {P} {stage}` |
| evaluation-orchestrator | claim-extractor 호출 전 (flow) | `snapshot-flow {P} pre-claim-extract` |
| evaluation-orchestrator | claim-extractor 호출 전 (draft, 변경된 각 챕터) | `snapshot-output {P} pre-claim-extract {chapter}` |
| evaluation-orchestrator | 평가 완료 후 | `evaluation_delta.py mark-done {P} {axes} --stage=...` |
| **writing-architect** | Phase 2 시작 전 (pre-redraft) | `snapshot-outputs {P} pre-redraft` |
| writing-architect | 각 chapter 저장 후 | `update-chapter {P} {chapter}` |
| writing-architect | final 통합 후 | `update-final {P}` |
| **output-editor** | Phase 5 수정 직전 | `snapshot-output {P} ch{X}-edit {chapter}` |
| output-editor | Phase 8 수정 후 | `update-chapter {P} {chapter}` |
| **flow-refiner** | Phase 7 반영 직전 | `snapshot-flow {P} pre-refine` |
| flow-refiner | 반영 후 | `update-flow {P}` |
| **paper-analyst** (단순화 v3) | 각 논문 분석 완료 후 | manifest 폐기 — analyzed/{name}.md frontmatter 갱신만 (sync_state 호출 불필요) |
| **critical-companion** | questions 신규 버전 직전 | `snapshot-critical-questions {P} pre-update` |
| critical-companion | commitments 갱신 직전 | `snapshot-critical-commitments {P} pre-update` |
| **aggregator** | evaluation.md 쓰기 전 | 내용 비교 → 실질 변경 없으면 skip (snapshot 불필요) |

**정리**: 모든 "수정 직전"에 snapshot. 모든 "수정 후"에 update-*. 이 두 규칙만 지키면 archive·sync-state 모두 일관. aggregator만은 예외(자동 변경 감지 기반 skip).

### Stale 유형 + Priority 점수

각 stale 항목은 **긴급도 점수**와 **등급(tier)**, **의존성 순서**를 부여받는다.

| kind | 의미 | 기본 score | tier | dependency order | 권장 해결 |
|------|------|-----------|------|------------------|----------|
| `flow_changed` | flow.md 해시 불일치 | 30 | 🔴 P1 | 3 | `"논문 재분석해줘"` 후 `"flow 평가해줘"` |
| `paper_removed` | collected/에서 제거 (dangling당 +10) | 20+ | 🔴 P1 | 2 | `"논문 제거해줘: {파일}"` |
| `chapter_flow_drift` | 챕터가 구 flow 기반 (챕터당 +15) | 15+ | 🟡 P2 | 5 | `"output {파일명} 수정해줘"` |
| `chapter_paper_version_drift` | 구버전 논문 분석 기반 (drift당 +10) | 10+ | 🟡 P2 | 4 | `"output {파일명} 수정해줘: 새 분석 반영"` |
| `paper_added_untracked` | collected/에 미추적 논문 (개당 +4) | 8+ | 🟢/🟡 | 1 | `"논문 처리해줘"` |
| `evaluation_stale` | evaluation이 현재 flow/chapters와 불일치 | 10 | 🟢 P3 | 7 | `"flow 평가해줘"` |
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
output/*.md → final/complete-draft.md + .docx 재생성.

---

## 🔢 Version · Mode · Action 시스템

### 버전·싱크 (`scripts/version_manager.py`)

각 산출물 상단에 YAML frontmatter:

```yaml
---
version: 3
content_hash: a3f8b9c
based_on:
  flow: 3
  claim-extraction: 2
updated_at: 2026-04-25T10:30:00
updated_by: claim-extractor
---
```

**자동 동작**:
- `content_hash` = frontmatter 제외 본문의 SHA-256(8자) — 변경 감지 기준
- 본문 hash 변경 시 `version` 자동 increment (idempotent — 변경 없으면 그대로)
- 사용자 본문(`flow.md`, `output/*.md`)은 aggregator 진입 시 자동 hash 비교 → bump
- 파생 파일(claim-extraction, axis*, evaluation, critical)은 aggregator의 `_apply_frontmatter_to_derivatives`가 후처리로 frontmatter 부여 (LLM 의존 제거)
- **이전 버전 자동 백업**: bump 직전 `history/{stage}/{type}/{NNN}-{date}-v{이전}-pre-bump/` 자동 보존

**싱크 검증**:
- 각 파생 파일의 `based_on.{X}` ↔ 의존 파일의 현재 `version` 비교
- 불일치 시 stale 표시 → aggregator가 분석 명령 진입 시 안내

**사용자 명령**:
- `"버전 체크"` — 모든 파일 sync 상태 표
- `"현재 상태"` — 버전/싱크 통합 표시

### Stage 시스템 (v3.2 — mode 폐기)

이전 버전의 `scripts/mode_manager.py` / `.current-mode` 파일 / `"output으로 진행"` 전환 명령은 **모두 폐기**.

**동작**:
- 평가·분석 명령은 항상 `flow` / `output` / `final` prefix 사용자 명시
- 단독 `"평가해줘"` (prefix 없음) → 에러
- `final` stage는 `"최종 완성했어"` 명령 (`scripts/finalize_draft.py`)으로 `final/complete-draft.md` 통합본을 만든 후에만 평가 가능
- final/ 폴더는 `"최종 완성했어"` 시점에 생성 (그 전엔 존재하지 않음)

### Action 분기 (aggregator 내부)

`evaluation_aggregator.py aggregate(action, stage)` 3종 분기:

| action | 사용자 명령 | 동작 |
|--------|-----------|------|
| `evaluation` | `"{stage} 평가해줘"` | claim-extractor + axis1~6 병렬 + aggregator → evaluation.md (단일 진입 파일) |
| `status` | `"현재 상태"` | 분석 없이 폴더·진행도·모드·버전 출력 |

**stale 자동 감지**: action 진입 직후 의존성 검사 → "📝 claim-extractor Agent 재호출" 등 명시적 dispatch instruction 출력. LLM이 따라 행동.

### 작업 항목 자동 등재 매트릭스 (work-plan 폐기 후, evaluation.md 안에 통합)

| 항목 종류 | 발급 트리거 | evaluation.md 내 섹션 |
|---------|-----------|------|
| **R-NN** (reference 검색) | claim-extraction의 `search[]` UNMATCHED 문장 | `📚 RESEARCH 항목` |
| **R-NN reanalyze** | flow.md bump 감지 + paper_reanalysis_delta | `🔄 재분석 항목` |
| **WRITE 자연어 항목** | axis2~6의 감점 사유 → 보강 권고 | `🛠 보강 항목` (카드 ID 없이 자연어 그대로) |
| **H-NN** (research-gap 가설) | gap-analyzer의 research-gap.md 분석 | `research-gap/research-plan.md` (별도 파일) |

폴더가 SSOT — card_registry·status JSON·dedup 메커니즘 폐기. 같은 R-NN이 재식별되면 claim-extraction-{stage}.md의 동일 번호로 자연 매칭. 사용자가 evaluation.md 작업 항목을 직접 처리하거나 삭제할 자유.

### History 통합 폴더

stage 폴더는 **최신만**, 모든 과거 버전은 `history/`로 통합:

```
history/
├── flow/
│   ├── body/                       flow.md 변경
│   ├── evaluations/                평가 스냅샷
│   ├── claim-extraction/           평가 스냅샷
│   └── critical/                   critical 답변 변경
├── output/
│   ├── body/{file_id}/             output 파일별 sub-folder
│   ├── evaluations/
│   ├── claim-extraction/
│   └── critical/
└── (work-plan/ 폐기)
```

**자동 백업 (version_manager) + 명시 snapshot (sync_state) 두 메커니즘 공존**:
- 자동: 모든 v++ 직전 — 일반 변경 커버
- 명시: pre-refine, pre-redraft, pre-respin 같은 의미 마일스톤만 LLM이 호출

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
첫 `"flow 평가해줘"` 실행 시 flow.md에 critical 신호(≥3개)가 있으면 시스템이 자동 제안. 사용자가 yes/no 선택.

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
- `"critical"`: 비판적 시각 능동 지원. critical-companion·axis6-critical-scorer·Iconoclast 자동 체이닝
- `"paradigm-shifting"`: 패러다임 도전 전용. Hedging 관대, 비주류 인용 환영, Iconoclast를 주 심사자로 승격

### {stage}/critical/questions.md 자동 업데이트 트리거 (ambition ≥ critical 시)

`"flow 평가해줘"` 명령이 stage를 판별하여 critical-companion을 **자동 호출**:

| stage | critical-companion trigger | 생성 버전 |
|-------|--------------------------|---------|
| flow 단계 첫 평가 | `initial` | v1 (패러다임 의식·반대 사고) |
| Stage 1 리서치 완료 후 | `post-research` | v2 (소수 의견·지적 계보) |
| v1 평가 | `post-draft` | v3 (대담성·정합성) |
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
1. 사용자가 {stage}/critical/questions.md의 답변 공간에 작성

2. 다음 중 하나가 trigger (답변 추출):
   a) "질문 업데이트해줘" (전체 critical-companion — 신규 질문 + 추출)
   b) "답변 반영해줘" (경량 — 추출만, 질문 갱신 안 함)
   c) "초안 작성해줘" / "output {파일명} 수정해줘" 실행 시 자동 prehook

3. critical-companion이 답변을 파싱하여:
   - 사용자 원문을 그대로 인용
   - actionable 형식으로 변환 (대상 섹션, 행동, 완료 조건)
   - 현재 output/*와 대조하여 4-상태 분류:
     🟢 FULFILLED / 🟡 PARTIAL / 🔴 UNFULFILLED / ⚠️ CONFLICTING
   - {stage}/critical/commitments.md에 기록

4. writing 에이전트가 commitment를 spec으로 사용:
   - writing-architect Phase 1 구조 설계 시 "이 commitment를 이 섹션에 구현" 명시
   - output-editor가 수정 중 commitment 충돌 여부 검증
   - flow-refiner가 UNFULFILLED를 flow 보강 제안으로 승격

5. 작업 완료 후 에이전트가 반영 결과 보고:
   ✅ [C-001] Luria 복원 → Section 2 pp.5-7에 추가
   🟡 [C-003] 급진적 steelman → 일부만 반영, 추가 수정 권장
   🔴 [C-004] 동양 철학 → 범위 부족으로 미반영

6. 사용자가 투명하게 확인:
   - 답변한 것이 어디에 반영되었는지
   - 무엇이 여전히 미이행인지
   - {stage}/critical/commitments.md 파일을 열어 전체 상태 조회 가능
```

### 답변하지 않을 때

답변을 건너뛰어도 시스템은 계속 작동하지만:
- 해당 질문은 **carry-over**되어 다음 버전에도 등장
- 2회 연속 미답변 → 🔴 "회피 중일 수 있음" 표시
- axis6-critical-scorer가 미답변을 **축 6 soft cap**으로 반영 (예: 답변 없으면 C-1 점수 60점 상한)
- {stage}/critical/commitments.md에 commitment 등록은 **안 됨** (답변이 명시적이어야만)

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

### axis6-critical-scorer의 5 하위 기준 (축 6)

| 기준 | 평가 내용 |
|------|---------|
| C-1 Paradigm Mapping | 분야의 dominant assumption을 명시 지명 |
| C-2 Fault-line Identification | 그 paradigm의 구조적 약점 |
| C-3 Bold Defense | Over-hedge 없는 대담한 주장 + falsifiability |
| C-4 Minority Evidence Recovery | 잊혀진 소수 의견·비주류 전통 복원 |
| **C-5 Engagement Discipline** | **Over-defense penalty (inverted-U)** — under-defense뿐 아니라 over-defense(반박 paragraph 도배·hedge 남용)도 처벌. 메시지 명료성 보호. |

axis3에도 동일 원리의 **3-5 Engagement Discipline** 신설 (Steelman·Falsifiability·Limitations·Attack Surface 다음).

### Final stage 한정 — `--mode` 옵션

`final 평가해줘`에 `--mode coursework` 또는 `--mode dissertation` 옵션 부착 시 기존 6-axis · holistic · aggregator · claim-extractor **모두 skip**. mode evaluator 단독 dispatch:

| 옵션 | rubric | 산출 | 비용 |
|------|--------|------|------|
| (옵션 없음) | 기존 6-axis + holistic | evaluation.md + axis*.md + holistic-review.md | 기본 |
| `--mode coursework` | Oxford Coursework (8 criteria × 6-band) — 단일 LLM | `coursework-evaluation.md` | ~3분, 1× |
| `--mode coursework --committee` | 위 rubric + **5인 페르소나 위원회 절차** (PDF §3.3 그대로 — Marker 1·2 blind → reconciliation → Third → External → Chair) | `coursework-committee-evaluation.md` + `committee/*.md` (5개 페르소나 outputs) | ~10분, ~5× |
| `--mode dissertation` | Oxford Dissertation (10 criteria × 6-band, methodology stack 포함) | `dissertation-evaluation.md` | ~3분, 1× |

**Marking convention** (mode evaluator 한정): `_3` / `_8` mark + 66 (narrow Merit) — Oxford 학과 규칙. Overall mark + 등급(Distinction/Merit/Pass/Fail) + 한 등급 상승 Top 3 actionable.

### ⛔ Blind Protocol — 모든 평가에 적용

`skills/BLIND-PROTOCOL.md` 준수. 핵심:
- 같은 conversation session에서 *이전 essay context*가 모든 평가 페르소나에 contamination — anchoring bias 위험
- 한 conversation session = 한 essay 평가가 원칙. 여러 essay는 각각 *fresh conversation*에서 실행
- 평가 보고서에 *다른 essay 이름·comparative 표·"한 칸 위/아래" 식 추론* 등장 시 polluted — 재평가 필요
- Width 신호 (refs 수·paradigm 수·beyond-field 언급)는 Oxford rubric의 *depth* distinguisher와 구분 필요

### peer-reviewer Iconoclast (Reviewer 4)

`ambition ≥ critical`일 때 자동 추가. 특징:
- **Timidity 지적**: "여기서 한 걸음 더 나아가야 한다"
- **Paradigm 내부 머무름 지적**: "비판한다면서 그 게임 안에 있다"
- **자기 배신 탐지**: {stage}/critical/questions.md 답변과 원고 불일치 적발
- **대담성 등급**: ★★★★★ 5점 척도로 평가

---

## 📓 활동 로그 시스템 (Activity Log)

모든 주요 작업은 `projects/{PROJECT_NAME}/activity.log`에 한 줄씩 누적됩니다. 이 로그는 두 가지 용도로 활용됩니다:

### 용도 1: Time-travel (과거 시점 조회)

```
# 로그 파일에서 과거 라인 복사
[2026-04-10 14:30:15] ✅ 평가 완료 | v1 | - | - | ref:eval-003 | evaluation-orchestrator,axis1-5 | verdict=Major Revision categories=Crit:1,Need:3,Adeq:1

# 채팅에 붙여넣고 요청
"[2026-04-10 14:30:15] ... | ref:eval-003 이 시점 evaluation 보여줘"
```

→ 시스템이 `ref:eval-003`을 파싱하여 `{stage}/evaluations/003-2026-04-10/evaluation.md` 출력.

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
[2026-04-23 14:30:15] ✅ 평가 완료 | v1 | - | - | ref:eval-003 | evaluation-orchestrator,axis1-6 | verdict=R&R categories=Crit:0,Need:2,Adeq:3,Strong:1 ambition=critical commits=3/5
```

- 앞 4 필드 고정 (timestamp, action, stage, target)
- 뒤 필드는 선택적 (result, ref, agents, meta)
- 빈 필드는 `-`로 표시
- **평가 결과**: 점수가 아니라 `verdict=Reject|Major|R&R|Accept` + `categories=Crit:N,Need:M,...` 사용 (카테고리 시스템)

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

- **프로젝트 스크립트**: `python3 scripts/sync_state.py`, `activity_log.py`
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
| `flow/flow.md` | **사용자의 줄글 플랜**. flow 단계의 기준 문서 |
| `research-gap/research-gap.md` | (선택) 분야·관심·아는 지형 — research-gap 단계의 진입 |
| `papers/candidates/{research-gap,flow}/*.pdf` | 다운로드한 PDF 임시 보관 (단계별 폴더, 처리되면 collected/로 이동) |

### 시스템이 자동 생성하는 파일

| 파일 | 생성 시점 | 역할 |
|------|----------|------|
| `skills/FLOW-TEMPLATE.md` | (스킬 영구 자료) | 줄글 작성 가이드 |
| `skills/RESEARCH-GAP-TEMPLATE.md` 🆕 | (스킬 영구 자료) | research-gap.md 작성 가이드 |
| `skills/GAP-REPORT-FORMAT.md` 🆕 | (스킬 영구 자료) | gap-report.md 포맷 스펙 |
| `skills/EVALUATION-FORMAT.md` 🆕 | (스킬 영구 자료) | evaluation.md 포맷 스펙 (work-plan 통합 후) |
| `.sync-state.json` | 프로젝트 생성 시 | **아티팩트 의존성·버전 추적** (sync 아키텍처의 핵심) |
| `{stage}/critical/questions.md` | Stage 마일스톤 (ambition ≥ critical) | **사용자가 답변하는 Socratic 질문** |
| `history/{stage}/critical/` | 매 critical-companion 재실행 | **질문·답변 버전 히스토리** |
| `research-gap/research-plan.md` 🆕 | `"리서치 갭 분석해줘"` (gap-analyzer) | H-NN 가설 목록 — research-gap 단계의 작업 항목 SSOT |
| `research-gap/gap-report.md` 🆕 | `"갭 리포트 만들어줘"` (gap-synthesizer) | 통합 갭 진단 (analyzed/research-gap/[R][D].*.md 종합) |
| **`{stage}/evaluation.md`** 🆕 | `"{stage} 평가해줘"` (aggregator) | 🩺 단일 통합 파일: 종합 판정(Reject/Major/R&R/Accept) + 축별 카테고리(🟢🟡🟠🔴⚫) + 이전 axis*-*.md 섹션 흡수 + **작업 항목 (R-NN·WRITE 자연어, 이전 work-plan 통합)** |
| `flow/claim-extraction-flow.md` 또는 `output/claim-extraction-output.md` | `"{stage} 평가해줘"` | 문장 단위 주장 테이블 (MATCHED / UNMATCHED-INTERNAL / UNMATCHED-EXTERNAL) + R-NN 식별 |
| `final/holistic-review.md` | `"final 평가해줘"` (mode 없음) 자동 | 🛡 final stage 통합 평가: 척추 articulation + 6축 카드 adjudication + Top 3 핵심 요약 |
| `final/coursework-evaluation.md` | `"final 평가해줘 --mode coursework"` | 🎓 Oxford Coursework rubric (8 criteria × 6-band) |
| `final/coursework-committee-evaluation.md` | `"final 평가해줘 --mode coursework --committee"` | 🎓 위 rubric + 5인 위원회 절차 |
| `final/committee/{marker-1,marker-2,third-marker,external-examiner,chair-decision}.md` | (위원회 모드 자동) | 각 페르소나의 독립 output |
| `final/dissertation-evaluation.md` | `"final 평가해줘 --mode dissertation"` | 🎓 Oxford Dissertation rubric (10 criteria × 6-band) |
| `history/{stage}/evaluations/{NNN}-{date}-{stage}/` | 매 평가 실행 직전 | 이전 평가 스냅샷 (delta 추적용) |
| `papers/.research-raw/{H-NN\|R-NN}.json` | `"리서치 진행해줘"` Stage A | MCP 원본 응답 (SSOT) |
| `papers/.translations/{H-NN\|R-NN}.md` | Stage B (research-processor) | sonnet 한글 abstract 번역 |
| `papers/.curation/{H-NN\|R-NN}.md` | Stage C (research-processor) | sonnet 6-카테고리 curation per H/R |
| `papers/.context-pack.md` | `"리서치 진행해줘"` 시작 시 | workers 공용 요약 |
| `papers/search-results/research-gap.md` 🆕 | `"리서치 진행해줘"` Stage D | research-gap 단계 검색 결과 (H-NN 종합) |
| `papers/search-results/flow.md` | `"리서치 진행해줘"` Stage D | flow 단계 검색 결과 (R-NN 종합) |
| `papers/collected/*.pdf` | `"논문 처리해줘"` | 처리 완료 PDF (단일 hub) |
| `papers/analyzed/research-gap/[R\|D].*.md` 🆕 | `"논문 처리해줘"` (research-gap candidates) | gap-paper-analyst 분석 |
| `papers/analyzed/flow/[A\|N].*.md` 🆕 | `"논문 처리해줘"` (flow candidates) / `"논문 재분석해줘"` | paper-analyst 분석 |
| `papers/archived/` | `"논문 제거해줘"` | 제거된 PDF 보관 |
| `output/0N-*.md` | `"초안 작성해줘"` | 섹션별 초안 |
| `output/archive/{NNN}-{date}-{trigger}/` | `"초안 작성해줘"`·`"output {파일명} 수정해줘"` 실행 직전 | 구버전 chapters 자동 스냅샷 |
| `final/complete-draft.md(.docx)` | `"초안 작성해줘"` / `"최종 통합해줘"` | 통합본 |
| `.paper-metadata.json` | `"논문 처리해줘"` | 논문 메타데이터 DB |
| `gaps-analysis.md` | `"gap 분석해줘"` (output-gap-finder) | 분야 갭 5종 (gap-analyzer와 별개 — 후속 연구 아이디어) |
| **(폐기)** ~~`work-plan.md`~~ ~~`history/work-plan/`~~ ~~`papers/.registry.json`~~ ~~`output/.registry.json`~~ ~~`.current-mode`~~ | (2026-04-30) | work-plan·card_registry·status JSON·mode 시스템 모두 제거. evaluation.md + 폴더 SSOT |

---

## 📖 명령어 레퍼런스

### 프로젝트 관리

| 명령 | 동작 |
|------|------|
| `"[이름] 프로젝트 만들어줘"` | 프로젝트 폴더 + 빈 flow.md + evaluations 구조 생성 |

### 평가

| 명령 | 동작 | Archive? |
|------|------|---------|
| 🎯 `"flow 평가해줘"` | 전체 6축 평가 + claim-extraction + evaluation.md (다음 액션 포함) | ✅ 스냅샷 생성 |
| 🔍 `"레퍼런스 점검해줘"` | 축 1 전용 경량 재평가 | ❌ (경량) |
| `"독창성 평가해줘"` | 축 4 단독 심층 | axis4-originality.md만 갱신 |
| `"정의 정밀도 평가해줘"` | 축 5 단독 심층 | axis5-concept.md만 갱신 |

### Research-Gap (선택 단계, 분야 anchor 탐색)

| 명령 | 동작 |
|------|------|
| `"리서치 갭 분석해줘"` 🆕 | research-gap.md → research-plan.md (gap-analyzer가 H-NN 가설 발급) |
| `"갭 리포트 만들어줘"` 🆕 | analyzed/research-gap/[R][D].*.md → gap-report.md (gap-synthesizer 통합) |
| `"이 논문 flow anchor로 분석해줘 X"` 🆕 | research-gap에서 분석한 X를 flow frame [A]로 추가 분석 (PDF 재활용) |

### 리서치 (Consensus 검색)

| 명령 | 동작 |
|------|------|
| `"리서치 진행해줘"` | **두 plan(research-gap·flow) 미해결 H-NN/R-NN 모두 처리** → 🔄 INTERNAL 재스캔 먼저 → 🔍 EXTERNAL search를 Consensus에 순차 투입 |
| `"논문 처리해줘"` | **두 candidates 폴더 (research-gap·flow) 자동 스캔** → 정규화·markdown 캐시 → 단계 frame에 따라 분기 분석 (research-gap → [R]/[D], flow → [A]/[N]) |
| `"논문 재분석해줘"` | **delta 기본** — flow.md 변경 섹션 영향 논문만 Mode B (v2 append) |
| `"논문 재분석해줘 --full"` | 전량 Mode B 재실행 |
| `"{파일명} 논문 재분석해줘"` | 해당 paper anchor 승격 + Mode B 재분석 |
| `"비판적으로 분석해줘 X"` | critique_target=true → analyzed/flow/[A].X.md에 비판 섹션 추가 (Mode C) |
| 🗑 `"논문 제거해줘: {파일}"` | archived/로 안전 이동 + dangling citation 자동 탐지 |
| 📝 `"flow 업데이트해줘"` | 새 논문 반영한 flow.md 보강 제안 (축 3·4 강화) |

### 작성·수정 (Stage 2-3)

| 명령 | 동작 |
|------|------|
| `"초안 작성해줘"` | writing-architect 구조 설계(승인 필요) → 초안 생성 |
| `"output {파일명} 수정해줘: [수정 내용]"` | 해당 챕터 수정 + 일관성 체크 + citation-checker 자동 감사 |

### 최종 완성 (Stage 4)

| 명령 | 동작 |
|------|------|
| 📦 `"최종 통합해줘"` | output/*.md 병합 + docx 재생성 + sync 갱신 |
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

### 권장 흐름 전체도 (4 단계 — research-gap 선택, 폴더가 SSOT)

```
프로젝트 생성 → .sync-state.json 초기화

[선택] research-gap 단계 (thesis 흐릿할 때)
  → research-gap/research-gap.md 작성
  → "리서치 갭 분석해줘"
  │   └── gap-analyzer → research-gap/research-plan.md (H-NN 발급)
  → "리서치 진행해줘"
  │   └── search-results/research-gap.md (H-NN 결과)
  → PDF 다운로드 → papers/candidates/research-gap/
  → "논문 처리해줘"
  │   └── analyzed/research-gap/[R].*.md, [D].*.md
  → "갭 리포트 만들어줘"
  │   └── gap-synthesizer → research-gap/gap-report.md (통합 갭)

[flow 단계]
  → flow/flow.md 자유 줄글 작성 (gap-report.md 입력으로 활용)
  → 🎯 "flow 평가해줘" (1차)
     ├── claim-extractor → INTERNAL / EXTERNAL R-NN 분류
     ├── evaluation-orchestrator → 6축 병렬 delta 평가
     ├── flow/evaluation.md (작업 항목 통합 — R-NN 검색 + WRITE 자연어 권고)
     └── history/flow/evaluations/001-{date}/

  → "리서치 진행해줘" (양 plan의 미해결 H/R 모두)
     ├── 🔄 INTERNAL 재분석 먼저
     └── 🔍 EXTERNAL search → search-results/{단계}.md
  → PDF 다운로드 → papers/candidates/flow/
  → "논문 처리해줘" (두 candidates 폴더 자동 스캔)
     └── analyzed/flow/[A]·[N].*.md
  → (선택) "이 논문 flow anchor로 분석해줘 X" — research-gap → flow 격상
  → (선택) 📝 "flow 업데이트해줘" (flow-refiner)

[output 단계]
  → "초안 작성해줘"
     ├── analyzed/flow/*.md 섹션별 인용 다발 우선
     └── output/0N-*.md
  → 🎯 "output 평가해줘" (2차) → history/output/evaluations/002-{date}/
  → "output {파일명} 수정해줘: ..." (반복, citation-checker PDF 감사)
  → 🎯 "output 평가해줘" (3차)

[final 단계]
  → 📦 "최종 통합해줘" (final/complete-draft.md)
  → "리뷰 체크해줘" (peer-reviewer)
  → 🎯 "final 평가해줘" (옵션: --mode coursework[--committee] / --mode dissertation)

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
- **UNMATCHED 건은 RESEARCH 과제로 자동 이어짐** — 실행 순서만 따르면 됨

### 평가 카테고리 해석 (메인 시그널)

각 축은 axis-scorer가 **5단계 카테고리**로 직접 판정. 점수는 trend tracking용 보조 신호 (`<details>` 안 보존, 절대 판정 사용 금지).

| 카테고리 | 의미 | 권장 조치 |
|---------|------|----------|
| 🟢 충실 (Strong) | 분야 표준 충족 | 다음 Stage 진입 |
| 🟡 적정 (Adequate) | 통과 가능, 작은 보강 | 작은 보강 후 진행 |
| 🟠 보강 필요 (Needs Work) | 의미 있는 보강 필요 | 해당 축 작업 지시 실행 |
| 🔴 구조적 결함 (Critical Gap) | 통과 어려움 | 해당 축 근본 재검토 |
| ⚫ 측정 불가 (Cannot Assess) | 측정 데이터 부재 | RESEARCH 등 데이터 확보 후 재평가 |

### 종합 판정 (verdict roll-up)

점수 평균이 아닌 **카테고리 카운트** 기반:

- 🔴 **Reject**: ≥2축 🔴 OR (axis1 AND axis5 둘 다 🔴) OR ≥3축 ⚫
- 🟠 **Major Revision**: ≥1축 🔴 (Reject 미달) OR ≥3축 🟠
- 🟡 **Revise & Resubmit**: ≥2축 🟠 (Major 미달) OR ≥1축 ⚫
- 🟢 **Accept**: 모든 축 ≥ 🟡 Adequate, 🔴/⚫ 0개

axis1+axis5는 "구조적 축" 가중 — 레퍼런스+개념 정의는 학술 논문의 기초 인프라.

### 제출 준비 기준

**모든 축 ≥ 🟡 Adequate, axis1·5 ≥ 🟢 Strong, 종합 판정 = 🟢 Accept**.

(과거 점수 기준 "450/500 이상"은 폐기 — LLM 채점 noise로 신뢰 불가.)

### Archive 스냅샷 활용

`{stage}/history/{stage}/evaluations/`의 과거 평가를 열어보면 각 수정이 어느 축을 몇 점 올렸는지 확인 가능합니다. 논문 투고 포트폴리오나 연구 일지로도 활용할 수 있습니다.

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
`"리서치 진행해줘"` 실행 중 자동으로 30초 대기 후 재시도하므로 그대로 두세요.

### 평가·작업 관련

**"flow.md에 RQ/Thesis가 없다"고 나옴**
줄글 중에 연구 질문과 핵심 주장을 한 문장씩 명시하세요. "~이다" 같은 단정 형식 권장.

**"평가가 너무 관대하다"**
axis 스코어러들은 Top-tier 저널 엄격도로 설정되어 있습니다. 만약 점수가 지속적으로 높다면 실제로 좋은 상태일 수 있으나, 특정 축만 강제 재실행(`"평가해줘 axis4"`) 또는 `"평가해줘 --full"`로 전체 재평가를 돌려보세요.

**"RESEARCH 과제가 너무 많다"**
첫 평가 시 UNMATCHED가 수십 건 나오는 것은 정상입니다. `"리서치 진행해줘"` 한 번으로 전량 일괄 처리 가능합니다.

**"citation-checker가 over-claim을 지적했다"**
원문 PDF를 직접 확인하고, 주장 강도를 약화시키거나(predict → suggest) 더 강한 근거 논문으로 교체하세요.

### 파일 관련

**"output/ 폴더가 비어있다"**
`"초안 작성해줘"`를 아직 실행하지 않았거나 writing-architect의 구조 승인 단계에서 중단되었을 가능성. 다시 실행하여 Phase 1 구조를 승인하세요.

**"이전 평가를 다시 보고 싶다"**
`{stage}/history/{stage}/evaluations/{NNN}-{date}-{stage}/` 폴더를 열어보세요.

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
삭제된 논문(archived/로 이동)을 챕터가 여전히 인용 중. `"output {파일명} 수정해줘: {삭제된 저자} 인용 제거 또는 대체"`로 수정하세요.

**"챕터가 구버전 논문 분석 기반이라고 경고"**
flow 변경 후 `"논문 재분석해줘"`를 돌려 v2가 생겼는데 챕터는 v1 기반. `"output {파일명} 수정해줘: 새 분석 반영"`으로 업데이트.

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
`output/archive/`에서 자동 스냅샷된 구버전 복구:
```bash
# 최신 pre-redraft 스냅샷 찾기
ls projects/{프로젝트}/output/archive/ | grep pre-redraft

# 예: 003-2026-04-22-pre-redraft 복구
cp projects/{프로젝트}/output/archive/003-2026-04-22-pre-redraft/*.md \
   projects/{프로젝트}/output/
```

**"Chapter X 수정을 롤백하고 싶다"**
```bash
# 해당 수정 직전 스냅샷 찾기
ls projects/{프로젝트}/output/archive/ | grep ch2-edit

# 단일 챕터 복구 (가장 최근 스냅샷 기준)
cp projects/{프로젝트}/output/archive/007-2026-04-23-ch2-edit/02-background.md \
   projects/{프로젝트}/output/
```

---

## 📄 License

MIT
