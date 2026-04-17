# Research Agent System

AI-powered academic research project management for Claude Code.

## 🚀 Quick Install

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/research-agent.git ~/Documents/research-agent
cd ~/Documents/research-agent

# 2. 자동 설치 (권한 상관없이)
bash install.sh

# 완료!
```

---

## 📦 설치 내용

자동으로 확인하고 설치:
- ✅ Claude Code (CLI)
- ✅ Python 패키지 (PyPDF2)
- ✅ Skill 링크
- ✅ Projects 폴더
- ✅ Consensus MCP (선택)

**이미 설치된 것은 자동으로 건너뜁니다!**

---

## 🎯 사용법

### 1. 프로젝트 생성

```bash
claude
```

Claude에서:
```
"literature-review 프로젝트 만들어줘"
```

**결과**:
```
projects/literature-review/
├── papers/
│   ├── collected/      (메타데이터 처리 완료)
│   ├── candidates/     (선택한 논문, 처리 대기)
│   └── analyzed/       (🤖 에이전트 분석 리포트)
├── FLOW-TEMPLATE.md   (가이드 - 수정 금지)
├── flow.md            (작성용 - 이 파일을 수정)
├── chapters/
└── final/
```

### 2. Flow 작성

```bash
nano projects/literature-review/flow.md
```

과제 구조 작성:
```markdown
## Section 1: Introduction
**필요 레퍼런스**: 
- 주제: `transformer attention`
- 최소: 3개
```

### 3. 논문 검색

```
"작업 시작해줘"
```
→ Consensus로 논문 검색 + `papers/consensus-results.md`에 결과 저장 (클릭 가능한 링크 포함)

### 4. 논문 다운로드 후 처리

`consensus-results.md`의 링크에서 PDF 다운로드 → `papers/candidates/`에 저장

```
"새 논문 처리해줘"
```
→ 메타데이터 추출 & `collected/` 이동 + 🤖 **paper-analyst가 자동 심층 분석**

### 5. 초안 작성

```
"초안 작성해줘"
```
→ 🤖 **writing-architect가 논증 구조 설계** → 사용자 확인 → 초안 작성

### 6. 챕터 수정

```
"Chapter 2 수정해줘: Linear attention 부분 확장"
```
→ 수정 + 일관성 체크 + 🤖 **citation-auditor가 인용 감사**

### 7. 추가 에이전트 명령 (선택)

```
"gap 분석해줘"           → 🤖 연구 Gap 탐색
"방법론 추천해줘"         → 🤖 3가지 방법론 비교
"리뷰 체크해줘"           → 🤖 심사자 시뮬레이션
```

---

## 📁 프로젝트 구조

```
research-agent/
├── skills/
│   ├── SKILL.md              (메인 스킬)
│   └── agents/               (서브 에이전트 6개)
│       ├── paper-analyst.md
│       ├── writing-architect.md
│       ├── citation-auditor.md
│       ├── gap-finder.md
│       ├── methodology-advisor.md
│       └── peer-reviewer.md
├── scripts/                   (시스템)
└── projects/                  (사용자 작업 — gitignore)
    └── {project-name}/
```

---

## 💡 주요 명령어

| 명령어 | 설명 | 에이전트 |
|--------|------|----------|
| `"[이름] 프로젝트 만들어줘"` | 새 프로젝트 생성 | - |
| `"작업 시작해줘"` | Flow 분석 & Consensus 검색 | - |
| `"새 논문 처리해줘"` | PDF 처리 + 심층 분석 | 🤖 paper-analyst |
| `"초안 작성해줘"` | 구조 설계 → 확인 → 초안 | 🤖 writing-architect |
| `"Chapter X 수정해줘"` | 수정 + 일관성 + 인용 감사 | 🤖 citation-auditor |
| `"gap 분석해줘"` | 연구 Gap 탐색 | 🤖 gap-finder |
| `"방법론 추천해줘"` | 방법론 제안/검증 | 🤖 methodology-advisor |
| `"리뷰 체크해줘"` | 심사 시뮬레이션/대응 | 🤖 peer-reviewer |

---

## 🔧 Requirements

- macOS / Linux
- Claude Code (CLI)
- Python 3.8+
- PyPDF2

**모두 install.sh가 자동 설치합니다!**

---

## 🆘 문제 해결

### "claude: command not found"

Claude Code CLI가 설치 안 됨:
```bash
npm install -g @anthropic-ai/claude-code
```

### Skill이 인식 안 됨

```bash
rm ~/.claude/skills/user/research-agent
bash install.sh
```

### PyPDF2 에러

```bash
pip3 install pypdf2 --break-system-packages
```

---

## 📝 다른 컴퓨터에서

```bash
# 1. Clone
git clone https://github.com/YOU/research-agent.git ~/Documents/research-agent
cd ~/Documents/research-agent

# 2. 자동 설치
bash install.sh

# 완료!
```

**3분이면 끝!** 🚀

---

## 🌟 Features

- ✅ 프로젝트 자동 생성
- ✅ Consensus 논문 검색
- ✅ PDF 메타데이터 자동 추출
- ✅ Flow 기반 초안 생성
- ✅ 챕터 수정 시 자동 일관성 체크
- ✅ Word 문서 자동 생성
- ✅ 스마트 설치 (이미 설치된 것 건너뜀)

## 🤖 Sub-Agent System

연구자 노하우를 담은 6개 전문 에이전트:

| 에이전트 | 역할 | 호출 |
|----------|------|------|
| **paper-analyst** | 논문 심층 분석 (3줄 요약 + 관련성 점수 + 활용 방안) | 자동 |
| **writing-architect** | 논증 구조 설계 → 확인 → 초안 작성 | 자동 |
| **citation-auditor** | 인용 정확성·형식·분포 검증 | 자동 |
| **gap-finder** | 방법론/응용/데이터 Gap 탐색 + 난이도·임팩트 점수 | 수동 |
| **methodology-advisor** | 방법론 추천(3가지 비교) 또는 선택된 방법론 검증 | 수동 |
| **peer-reviewer** | 심사자 시뮬레이션 또는 실제 리뷰 대응 전략 | 수동 |

---

## 📄 License

MIT
