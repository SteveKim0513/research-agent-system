# Research Agent — 빠른 사용 가이드

**3분 안에 사용 가능**. 복잡한 원리·아키텍처는 [MANUAL.md](./MANUAL.md) 참조.

---

## 🚀 시작

```bash
cd ~/Documents/research-agent
claude
```

---

## 📝 7단계 표준 흐름

```
① 프로젝트 생성
② flow.md 작성 (에세이처럼 자유 서술)
③ 평가 (5축 점수 + 작업 계획서)
④ 리서치 (논문 자동 검색 + PDF 처리)
⑤ 초안 작성
⑥ 챕터 수정 (반복)
⑦ 최종 통합 + 리뷰 체크
```

### ① 프로젝트 생성

```
"my-essay 프로젝트 만들어줘"
```
`projects/my-essay/` 폴더 자동 생성. 이 안에서만 작업합니다.

### ② flow.md 작성

`projects/my-essay/flow.md` 파일을 에디터로 열어 **자유 줄글**로 씁니다:

- **필수 2가지**:
  - 연구 질문 한 문장: `"이 글은 X를 묻는다"`
  - 핵심 주장 한 문장: `"본 에세이는 Y라고 주장한다"`
- **권장**: 문제 → 기존 관점 비판 → 자기 제안 → 예상 반론 → 함의를 **에세이처럼** 서술

체크박스·목차 형식 **금지**. 시스템이 줄글을 알아서 분석.

### ③ 평가

```
"평가해줘"
```

**생성되는 것**:
- 5축 점수 (레퍼런스·논리·반박·독창성·구성개념)
- `work-plan.md` — 해야 할 작업 목록 (HUNT·REANALYZE 체크박스 포함)

### ④ 리서치

```
"작업 시작해줘"
```
→ work-plan.md의 HUNT 과제가 Consensus에서 자동 검색 → `papers/consensus-results.md` 누적

**사용자가 할 일**: 링크에서 PDF 다운로드 → `projects/my-essay/papers/candidates/`에 저장

그 다음:
```
"새 논문 처리해줘"
```
→ PDF 자동 분석 (paper-analyst)

### ⑤ 초안 작성

```
"초안 작성해줘"
```
→ 구조 설계 제시 → 사용자 승인 → `chapters/*.md` 생성 + `final/complete-draft.md` + `.docx`

### ⑥ 챕터 수정

```
"Chapter 2 수정해줘: impurity problem 부분을 Löffler 2024 논증으로 강화"
```
→ 자동 일관성 체크 + PDF 대조 인용 감사

여러 챕터 반복 가능.

### ⑦ 최종 통합 + 리뷰

```
"최종 통합해줘"
"리뷰 체크해줘"
```
→ 통합본 재생성 + 가상 심사자 3~4명 시뮬레이션

---

## 🎯 전체 명령어 (실행 가능한 모든 것)

### 필수 워크플로우 (대부분의 사용자가 쓰는 것)

| 명령 | 용도 |
|------|------|
| `"[이름] 프로젝트 만들어줘"` | 새 프로젝트 시작 |
| 🎯 `"평가해줘"` | 5축 냉정 평가 + 작업 계획서 |
| `"작업 시작해줘"` | work-plan HUNT→Consensus 자동 검색 |
| `"새 논문 처리해줘"` | candidates/의 PDF 처리 + 분석 |
| `"초안 작성해줘"` | Phase 1 구조 설계 → Phase 2 초안 |
| `"Chapter X 수정해줘: ..."` | 챕터 부분 수정 + 인용 감사 자동 |
| 📦 `"최종 통합해줘"` | chapters → final/*.md + .docx 재빌드 |
| 💬 `"리뷰 체크해줘"` | peer-reviewer 심사 시뮬 (Stage 4) |
| 💬 `"리뷰 답변 도와줘: [리뷰 텍스트]"` | 실제 심사 대응 전략 + 답변 초안 |

### Stage별 경량 보조 (선택)

| 명령 | 시점 |
|------|------|
| 🔍 `"레퍼런스 점검해줘"` | Stage 1 후 축 1만 경량 재평가 (빠름) |
| 📝 `"flow 업데이트해줘"` | 새 논문 반영한 flow.md diff 제안 |
| 🔄 `"논문 재분석해줘"` | flow 변경 시 기존 PDF를 새 각도로 재스캔 |
| 🗑 `"논문 제거해줘: {파일명}"` | 안전 archived/ 이동 + dangling citation 탐지 |

### 심층 평가 (개별 축 깊이 검토)

| 명령 | 평가 축 |
|------|--------|
| `"독창성 평가해줘"` | 축 4 — "So What?" + Novelty Delta Map |
| `"정의 정밀도 평가해줘"` | 축 5 — 구성개념 정의 감사 |
| 🎭 `"비판적 시각 평가해줘"` | 축 6 — Paradigm/Fault-line/Bold Defense (Critical Mode 전용) |

### Critical Mode (비판적 시각 지원, 선택 활성화)

| 명령 | 용도 |
|------|------|
| 🎭 `"비판 모드 critical로 설정해줘"` | Critical Mode 활성화 (incremental/critical/paradigm-shifting) |
| 🤔 `"질문 업데이트해줘"` | Socratic 질문 v+1 생성 (답은 사용자 몫) |
| 💬 `"답변 반영해줘"` | 답변을 actionable commitment로 추출 |
| 🔍 `"비판적으로 분석해줘: {파일}"` | paper-analyst Mode C — hidden assumptions 등 발굴 |

### 보조 도구

| 명령 | 용도 |
|------|------|
| `"gap 분석해줘"` | 분야의 빈틈 5종 탐색 (후속 연구 아이디어) |
| `"방법론 추천해줘"` / `"방법론 검증해줘"` | empirical 연구 전용 — 방법론 3종 비교 또는 검증 |

### 상태 관리 (언제든)

| 명령 | 용도 |
|------|------|
| 🔄 `"sync 확인해줘"` | 아티팩트 동기화 상태 점검 + 우선순위 해결 가이드 |
| 🧠 `"작업 추천해줘"` | **뭘 해야 할지 모를 때** — 로그 기반 추천 + 이유 |
| ⏪ **로그 라인 복사** + `"이 시점 X 보여줘"` | time-travel archive 조회 (읽기 전용) |

---

## 💡 사용 팁

### 평가 점수 해석

| 구간 | 의미 |
|------|------|
| 450+/500 | 제출 가능 |
| 350-449 | 소폭 수정 필요 (Minor Revision) |
| 250-349 | 대폭 수정 (Major Revision) |
| <250 | 근본 재설계 |

각 축(5개) 100점 만점. 90+는 🟢, 70-89 🟡, <70 🔴.

### 정체 구간 탈출

3일 이상 작업 안 했거나 뭘 해야 할지 모르면:
```
"작업 추천해줘"
```
시스템이 로그 분석해서 다음 명령과 **이유**를 제시합니다.

### 과거 상태 조회

`projects/{프로젝트}/activity.log` 파일을 열어 과거 라인을 복사:
```
[2026-04-10 14:30] 평가 완료 | v1-draft | ... | ref:eval-003 | ...
```

채팅에 붙여넣고 요청:
```
"이 시점 work-plan 보여줘"
```
→ 해당 시점의 archive 내용 출력 (읽기 전용).

### 비판 모드 (선택)

Oxford·Cambridge 스타일의 **비판적 시각**을 원하면:
```
"비판 모드 critical로 설정해줘"
```
→ 추가 평가 축 + Socratic 질문 (critical-questions.md) 생성. 답변은 **사용자가 직접** 작성.

---

## 🆘 자주 만나는 문제

**"claude: command not found"**
```bash
npm install -g @anthropic-ai/claude-code
```

**Consensus 검색이 3개만 나옴**
```
claude
> /mcp → consensus → Authenticate
```

**스킬이 인식 안 됨**
```bash
bash install.sh
```

**권한 prompt가 여전히 자주 뜸**
→ `.claude/settings.json`에 해당 명령 패턴 추가. 또는 `claude --dangerously-skip-permissions` (비권장).

**초안이 이상해서 재작성하고 싶음**
→ `"초안 작성해줘"` 재실행. 기존 챕터는 `chapters/archive/`에 자동 스냅샷되어 복구 가능.

---

## 📚 더 깊이 알고 싶다면

| 문서 | 내용 |
|------|------|
| [README.md](./README.md) | 시스템 개요, 설치, 사전 준비 |
| **GUIDE.md** (이 문서) | 3분 빠른 사용법 |
| [MANUAL.md](./MANUAL.md) | **전체 참고** — 18개 에이전트 상세, **병렬 delta 평가 아키텍처**, sync, Critical Mode, 활동 로그, 권한 관리, 모델 라우팅, 모든 명령, troubleshooting |
| [PRINCIPLES.md](./PRINCIPLES.md) | 설계 철학 + 학술 글쓰기 원칙 (5축의 학술적 근거, Kuhn·Popper·Foucault 전통) |

---

## ⚡ 한 줄 요약

```
프로젝트 만들어줘 → flow.md 줄글 작성 → 평가 → 작업 시작
→ 논문 처리 → 초안 → 수정 반복 → 최종 통합 + 리뷰
```

이게 전부입니다. 복잡한 건 시스템이 알아서 처리합니다.
