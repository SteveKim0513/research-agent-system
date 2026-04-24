# Research Agent — 사용 가이드

학술 글을 쓸 때 시스템이 옆에서 **레퍼런스 찾기·평가·수정 추적**을 도와주는 도구.

핵심 모델 두 줄 요약:
- 글은 **flow**(계획)와 **output**(원고) 두 단계로 작성
- 각 단계에서 **레퍼런스 분석**(축 1)과 **내용 분석**(축 2~6)을 따로 돌려, 결과를 `work-plan.md`의 카드로 받아 처리

---

## 1분 시작

```bash
cd ~/Documents/research-agent
claude
```

세션 안에서 모든 작업이 **자연어 명령**으로 진행됩니다.

설치가 안 됐으면 [README.md § 설치](./README.md#-설치) 먼저.

---

## 첫 프로젝트 7단계

### ① 프로젝트 만들기

```
"my-essay 프로젝트 만들어줘"
```

→ `projects/my-essay/` 자동 생성.

### ② flow.md 작성

`projects/my-essay/flow/flow.md`를 에디터로 열어 **줄글로** 작성:

- 연구 질문 한 문장 (`이 글은 X를 묻는다`)
- 핵심 주장 한 문장 (`본 에세이는 Y라고 주장한다`)
- 권장 흐름: 문제 → 기존 관점 비판 → 자기 제안 → 예상 반론 → 함의

체크박스·목차 형식 ❌. 줄글만.

### ③ 첫 분석

```
"flow 모드"                  ← 한 번만 (기본값이라 보통 생략 가능)
"레퍼런스 분석해줘"           ← 문장 단위 분석 + 부족한 논문 → RESEARCH 카드 발급
"내용 분석해줘"              ← 논리·독창성 등 5축 평가 → WRITE 카드 발급
```

생성:
- `flow/claim-extraction-flow.md` — 문장 분류 + R 목록
- `flow/evaluations/axis1~6.md` + `evaluation.md`
- `work-plan.md` — 할 일 카드 모음

### ④ 리서치 + 논문 처리

```
"리서치 진행해줘"             ← work-plan의 RESEARCH 카드 자동 실행
                                Consensus MCP로 papers/consensus-results.md 생성
```

→ `consensus-results.md` 열어 후보 논문 검토 → **필요한 PDF만 직접 다운로드** → `papers/candidates/`에 넣기.

```
"논문 처리해줘"               ← candidates/ PDF triage → Tier 1·2·3 분석
                                papers/analyzed/*-analysis.md 생성
```

### ⑤ 초안 작성

```
"초안 작성해줘"
```

→ writing-architect가 구조 설계(승인 필요) → `output/*.md` 생성.
이제 자동으로 **output 모드**로 전환 권장:

```
"output 모드"
```

### ⑥ output 분석 → 수정 반복

```
"레퍼런스 분석해줘"           ← 이제 output 대상 (모드 적용)
"내용 분석해줘"
```

work-plan에 `WRITE-NNN` (mode=modify) 카드 발급되면:

```
"output ch3.md 수정해줘: WRITE-007"
```

→ output-editor가 카드 지시대로 수정 + citation-auditor 자동 체이닝.

**반복**: 수정 → 재분석 → 새 카드 → 수정.

### ⑦ 최종 통합 + 리뷰

```
"최종 통합해줘"     ← output → final/*.md + .docx
"리뷰 체크해줘"     ← peer-reviewer 시뮬레이션
```

---

## 명령어 한눈

### 모드 (지금 어느 단계?)

| 명령어 | 동작 |
|---|---|
| `"flow 모드"` / `"output 모드"` | 현재 모드 전환 |
| `"현재 모드"` | 현재 모드 출력 |

기본값은 `flow`. 한 번 모드를 정하면 prefix 없이 명령 가능.

### 분석 (분석해줘 ≡ 평가해줘 혼용)

| 명령어 | 동작 |
|---|---|
| `"레퍼런스 분석해줘"` | 현재 모드 적용 — claim-extractor + axis1 + RESEARCH 카드 |
| `"내용 분석해줘"` | 현재 모드 적용 — axis2~6 + WRITE 카드 |
| `"flow 레퍼런스 분석해줘"` | 모드 무시, flow 강제 |
| `"output 내용 평가해줘"` | 모드 무시, output 강제 |

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
| `"flow 업데이트해줘"` | flow-refiner — interactive diff (카드 발급 없음) |

---

## 폴더 구조

```
projects/{P}/
├── flow/                           — 계획 단계
│   ├── flow.md                     사용자 본문
│   ├── claim-extraction-flow.md    레퍼런스 분석 결과
│   ├── evaluations/                최신 axis1~6 + evaluation.md
│   └── critical/                   Critical Mode 시 생성
│
├── output/                         — 결과물 단계
│   ├── *.md                        실제 원고
│   ├── claim-extraction-output.md
│   ├── evaluations/
│   ├── critical/
│   └── .registry.json              WRITE 카드 SSOT
│
├── papers/                         — 자료
│   ├── candidates/                 사용자 투입 PDF (대기)
│   ├── collected/                  처리 완료
│   ├── analyzed/                   *-analysis.md
│   ├── consensus-results.md
│   └── .registry.json              RESEARCH 카드 SSOT
│
├── history/                        — 모든 과거 버전 통합
│   ├── flow/{body, claim-extraction, evaluations, critical}/
│   ├── output/{body, claim-extraction, evaluations, critical}/
│   └── work-plan/
│
├── work-plan.md                    — 활성 카드 대시보드 (매일 열기)
├── activity.log                    — 활동 이력
└── .current-mode                   — 현재 모드 (flow|output)
```

**원칙**: stage 폴더에는 **최신만**. 모든 과거 버전은 `history/`에 자동 백업.

---

## 카드 시스템

|  | RESEARCH | WRITE |
|---|---|---|
| **무엇** | 근거 논문 확보 | 글 작성·수정 |
| **mode** | search · reanalyze | create · modify |
| **발급 시점** | 레퍼런스 분석 시 자동 (claim-extractor) | 내용 분석 시 자동 (axis2~6의 🛠 WRITE 후보 섹션) + citation-auditor 사후 체이닝 |
| **Registry** | `papers/.registry.json` | `output/.registry.json` |
| **실행 명령** | `"리서치 진행해줘"` / `"논문 재분석해줘"` | `"초안 작성해줘"` / `"output X 수정해줘: WRITE-NNN"` |

**flow 수정은 카드 아님**. 사용자가 `"flow 업데이트해줘"`로 명시 호출 시 flow-refiner가 interactive diff 제안 → 사용자가 항목별 승인.

---

## 버전 + 싱크 (자동)

각 산출물 상단에 frontmatter 자동 부여:

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
- 사용자가 flow.md 편집 → 다음 명령 시 시스템이 hash 변경 감지 → version 자동 increment
- **이전 버전은 history에 자동 백업** (실수 복구 가능)
- 의존하던 파생 파일들은 `based_on.flow={이전}`이 되어 **stale 표시**
- 분석 명령 실행 시 stale이면 자동 선행 갱신

언제든 `"버전 체크"`로 모든 파일의 sync 상태 확인.

---

## 매일 시작 패턴

```
1. "현재 상태"        ← 어디까지 했는지 한눈
2. "현재 모드"        ← flow? output?
3. work-plan.md 열기 → 🎯 권장 명령부터 처리
```

뭘 할지 모르겠으면:
```
"작업 추천해줘"
```

→ 활동 로그·work-plan 분석해서 다음 명령 + 이유 제시.

---

## 자주 쓰는 시나리오

### 새 프로젝트 시작
```
"my-essay 프로젝트 만들어줘"
→ flow.md 직접 작성
"레퍼런스 분석해줘"
"내용 분석해줘"
"리서치 진행해줘"
→ PDF 선별 → candidates/ 투입
"논문 처리해줘"
"초안 작성해줘"
```

### output 단계 진입
```
"output 모드"
"레퍼런스 분석해줘"   ← output 대상
"내용 분석해줘"
"output ch1.md 수정해줘: WRITE-001"
```

### flow 다시 손볼 때
```
"flow 모드"
flow.md 편집 (에디터로 직접) → 시스템이 다음 명령 시 자동 v++
"flow 업데이트해줘"   ← (선택) flow-refiner의 새 논문 반영 제안
"레퍼런스 분석해줘"   ← stale 자동 선행, 새 R/RESEARCH 카드 발급
```

### 정체된 느낌일 때
```
"현재 상태"           ← 진행도·블로커 확인
"작업 추천해줘"       ← 다음 명령 추천
"버전 체크"           ← stale 파일 있는지 확인
```

---

## 더 깊이

- [MANUAL.md](./MANUAL.md) — 시스템 아키텍처·내부 동작
- [PRINCIPLES.md](./PRINCIPLES.md) — 설계 철학·평가 기준
- [skills/SKILL.md](./skills/SKILL.md) — 모든 명령어·에이전트 상세
- [skills/WORK-PLAN-FORMAT.md](./skills/WORK-PLAN-FORMAT.md) — work-plan 카드 포맷 스펙
