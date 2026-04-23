# Research Agent System

학술 과제·논문 작성을 위한 **5축 냉정 평가 기반 AI 연구 관리 시스템**.
Claude Code 스킬로 동작하며, 줄글(prose)로 쓴 flow를 문장 단위로 분석해 자동으로 Consensus 논문 검색 → 초안 생성 → 수정 → 최종 완성까지 관리합니다.

---

## 🧭 이게 어떤 시스템인가

학부~박사 과정 학생·연구자가 에세이·리포트·저널 투고 논문을 쓸 때 가장 어려운 지점을 자동화합니다:

- **"모든 주장에 레퍼런스를 달아야 한다"** — 문장 단위로 주장을 추출해 자동으로 Consensus 검색 키워드를 생성
- **"내 논문이 심사자 눈에 어떻게 보이는가?"** — Top-tier 저널 심사 엄격도로 **5축 냉정 평가** 제공
- **"어디부터 고쳐야 하나?"** — 평가 결과를 바탕으로 **만점 달성 작업 지시서** 자동 생성
- **"인용을 실제로 정확히 했는가?"** — 인용마다 원문 PDF와 대조해 over-claim·misattribution 탐지

### 5축 평가 기준

| 축 | 이름 | 핵심 질문 |
|---|------|----------|
| 1 | 논문 레퍼런스 충실도 | Coverage · Accuracy · Authority · Balance |
| 2 | 논리 전개 완성도 | Argument chain · Transition · Thesis alignment · Scope |
| 3 | 반박/강화 논리 | Steelman · Falsifiability · Limitations · Reviewer attack |
| 4 | 독창성·기여도 | "So What?" · Novelty positioning · Contribution layer · Implications |
| 5 | 구성개념 정의 정밀도 | Definition · Operationalization · Boundary · Categorical/Dimensional |

### 🎭 Critical Mode (비판적 시각 지원)

`"비판 모드 critical로 설정해줘"` 또는 flow.md 기반 자동 제안으로 활성화. Oxford·Cambridge·ENS style의 비판 전통을 시스템에 통합:

- **축 6 critical-lens**: Paradigm Mapping / Fault-line / Bold Defense / Minority Recovery
- **critical-companion**: Stage마다 Socratic 질문 자동 생성 (답은 사용자 몫 — 시스템이 절대 암시하지 않음)
- **critical-commitments.md**: 사용자 답변을 **actionable spec으로 자동 추출** → 모든 writing 에이전트가 필수 참조 → 작업 완료 후 반영 결과 투명 보고 (답변이 허공에 묻히지 않음)
- **peer-reviewer Iconoclast**: "충분히 대담한가?" 심사자 페르소나
- **paper-analyst Mode C**: hidden assumptions / methodological biases / field politics 발굴

**답변 → 반영 → 확인 흐름**:
```
critical-questions.md 답변 작성
  → "답변 반영해줘" (또는 writing 명령 시 자동)
  → critical-commitments.md에 actionable 추출
  → 초안/수정 명령 실행
  → 결과 완료 후 "✅ [C-001] ... Section 2에 추가" 반영 보고
```

### 18개 서브 에이전트

**평가 오케스트레이션 (8)**: evaluation-orchestrator + axis1-reference-scorer ~ axis6-critical-scorer + claim-extractor
**생성·수정 (5)**: paper-analyst (A/B/C modes), writing-architect, chapter-editor, flow-refiner, citation-auditor
**Critical Mode 전용 (1)**: critical-companion (axis6-critical-scorer가 축 6 심사 담당)
**보조 (3)**: gap-finder, methodology-advisor, peer-reviewer (Iconoclast 페르소나 포함)
**유틸리티 (1)**: abstract-translator (haiku — HUNT·PDF abstract 한글 번역)

**평가는 병렬 delta 아키텍처** — evaluation-orchestrator가 변경된 축만 병렬 디스패치. 각 에이전트는 작업 성격에 맞는 모델로 실행됩니다 (opus = 판단, sonnet = 구조화, haiku = 기계적). 자세히는 [PRINCIPLES.md](./PRINCIPLES.md) 참고.

---

## 🚀 설치

### 사전 준비

- macOS / Linux
- Node.js (Claude Code 설치용)
- Python 3.8+
- Claude Code 계정 (Anthropic API 접근)
- [Consensus](https://consensus.app) 무료 계정 (논문 검색용 — 미로그인 시 검색당 3개만 반환)

### 자동 설치

```bash
git clone https://github.com/SteveKim0513/research-agent-system.git ~/Documents/research-agent
cd ~/Documents/research-agent
bash install.sh
```

`install.sh`가 자동으로 확인·설치:
- ✅ Claude Code CLI
- ✅ Python 패키지 (PyPDF2)
- ✅ Skill 심볼릭 링크 (`~/.claude/skills/user/research-agent` → `./skills`)
- ✅ `projects/` 폴더
- ✅ Consensus MCP 등록 (`claude mcp add-json consensus ...`)
- ✅ Consensus 로그인 안내 (브라우저 자동 오픈)

**이미 설치된 항목은 자동으로 건너뜁니다.**

### Consensus 인증 (필수)

설치 후 Claude Code 실행하여:
```
claude
> /mcp
→ consensus 선택 → Authenticate → 브라우저에서 로그인
```

---

## ⚡ 빠른 시작 (30초)

```bash
cd ~/Documents/research-agent
claude
```

Claude에서:
```
> "my-essay 프로젝트 만들어줘"
```

그다음 `projects/my-essay/flow.md`를 열어 자유 줄글로 연구 방향을 작성하고:
```
> "평가해줘"      ← 5축 평가 + 작업지시서 생성
> "작업 시작해줘" ← HUNT 과제 자동 Consensus 검색
> "새 논문 처리해줘" ← PDF 처리 + 심층 분석
> "초안 작성해줘" ← writing-architect가 구조 설계 → 초안
```

**빠른 사용법은 [GUIDE.md](./GUIDE.md) (3분) 참고.**
**전체 참고 매뉴얼은 [MANUAL.md](./MANUAL.md) 참고.**
**시스템의 설계 철학·학술 글쓰기 원칙은 [PRINCIPLES.md](./PRINCIPLES.md) 참고.**

📓 **활동 로그 시스템**: Claude Code hooks가 모든 명령을 `projects/{이름}/activity.log`에 자동 기록. `"작업 추천해줘"`로 로그 기반 다음 명령 추천. 자세히는 [MANUAL.md § 활동 로그](./MANUAL.md#-활동-로그-시스템-activity-log).

🔐 **권한 자동 승인** (`.claude/settings.json`): clone 즉시 이 프로젝트의 스크립트·git 기본 작업·파일 읽기/쓰기가 **사전 승인**되어 반복 권한 prompt가 뜨지 않습니다. 위험한 명령(`rm -rf`, `git push --force`, `git reset --hard` 등)은 **deny 목록으로 명시적 차단** — 실수로 실행 불가. 설정 변경 원하면 `.claude/settings.json`의 `permissions` 섹션 편집.

---

## 📁 시스템 구성

```
research-agent/
├── skills/
│   ├── SKILL.md              (메인 스킬 정의)
│   ├── FLOW-TEMPLATE.md      (줄글 flow 작성 가이드)
│   └── agents/               (18개 서브 에이전트)
│       ├── evaluation-orchestrator.md
│       ├── claim-extractor.md
│       ├── axis1-reference-scorer.md ~ axis6-critical-scorer.md
│       ├── critical-companion.md         (Critical Mode — Socratic 질문)
│       ├── paper-analyst.md              (A/B/C modes)
│       ├── writing-architect.md
│       ├── chapter-editor.md
│       ├── flow-refiner.md
│       ├── citation-auditor.md
│       ├── gap-finder.md
│       ├── methodology-advisor.md
│       └── peer-reviewer.md              (+ Iconoclast persona)
├── scripts/                   (메타데이터 추출 등 시스템 스크립트)
├── projects/                  (사용자 작업 공간 — gitignore)
│   └── {project-name}/
│       ├── flow.md
│       ├── activity.log                (📓 모든 명령 자동 로그)
│       ├── critical-questions.md       (🎭 사용자가 답하는 Socratic 질문)
│       ├── critical-questions.archive/ (🎭 질문·답변 버전 히스토리)
│       ├── critical-commitments.md     (🎭 답변에서 자동 추출한 actionable 사양)
│       ├── critical-commitments.archive/ (🎭 commitment 상태 히스토리)
│       ├── evaluations/       (latest/ + archive/)
│       ├── papers/            (candidates/ + collected/ + analyzed/ + archived/)
│       ├── chapters/          (+ archive/ for draft rollback)
│       └── final/
├── install.sh
├── README.md                  (이 파일 — 설치·개요)
├── GUIDE.md                   (빠른 사용 가이드 — 3분)
├── MANUAL.md                  (전체 참고 매뉴얼 — 모든 기능 상세)
└── PRINCIPLES.md              (설계 철학·학술 글쓰기 원칙)
```

---

## 🎯 핵심 명령어 요약

| 명령어 | 동작 |
|--------|------|
| `"[이름] 프로젝트 만들어줘"` | 프로젝트 생성 |
| 🎯 `"평가해줘"` | 5축 냉정 평가 + 작업지시서 |
| 🔍 `"레퍼런스 점검해줘"` | 축 1 전용 경량 재평가 |
| 📝 `"flow 업데이트해줘"` | 새 논문 반영한 flow 보강 제안 |
| `"작업 시작해줘"` | work-plan.md HUNT → Consensus 자동 검색 |
| `"새 논문 처리해줘"` | PDF 처리 + paper-analyst 분석 |
| `"초안 작성해줘"` | writing-architect 초안 생성 |
| `"Chapter X 수정해줘: ..."` | 수정 + citation-auditor 감사 |
| `"리뷰 체크해줘"` | peer-reviewer 심사 시뮬레이션 |
| `"리뷰 답변 도와줘: [리뷰 텍스트]"` | peer-reviewer Mode B — 실제 리뷰 코멘트에 답변 초안 작성 |
| 🧠 `"작업 추천해줘"` | activity.log 기반 다음 명령 추천 (이유 포함) |

전체 명령어·사용 흐름은 [MANUAL.md](./MANUAL.md) 참고.

---

## 🆘 빠른 문제 해결

**`claude: command not found`**
```bash
npm install -g @anthropic-ai/claude-code
# 방금 설치했는데도 못 찾으면 쉘 캐시 갱신:
hash -r && which claude
```

**npm 설치 중 `ENOTEMPTY` 에러** (이전 설치 잔존물)
```bash
# 기존 디렉토리 정리 후 재설치
sudo rm -rf "$(npm config get prefix)/lib/node_modules/@anthropic-ai/claude-code"
npm install -g @anthropic-ai/claude-code
# install.sh 재실행 시 자동 정리됨 (2026-04-23 이후 버전)
```

**스킬이 인식 안 됨**
```bash
rm ~/.claude/skills/user/research-agent
bash install.sh
```

**Consensus MCP 연결 끊김**
```bash
claude
> /mcp → consensus 선택 → Authenticate
```

**PyPDF2 오류**
```bash
pip3 install pypdf2 --break-system-packages
```

자세한 트러블슈팅은 [MANUAL.md § 트러블슈팅](./MANUAL.md#-트러블슈팅) 참고.

---

## 📋 Requirements

- macOS / Linux
- Claude Code CLI (설치 스크립트가 자동 설치)
- Python 3.8+
- PyPDF2
- Node.js (npm 경유 Claude Code 설치 시)
- Consensus 계정 (무료 — 검색 결과 확장)

---

## 📄 License

MIT
