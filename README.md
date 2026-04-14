# Research Agent System

AI-powered academic research project management for Claude Code.

## 🚀 Quick Install

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/research-agent.git ~/Documents/research-agent
cd ~/Documents/research-agent

# 2. Run install script (자동 설치)
./install.sh

# 3. 완료! 사용 시작
cd ~/Documents/research-test
claude
```

---

## 📦 Manual Install (수동 설치)

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/research-agent.git ~/Documents/research-agent
cd ~/Documents/research-agent

# 2. Python 패키지
pip install -r requirements.txt --break-system-packages

# 3. Skill 링크
mkdir -p ~/.claude/skills/user
ln -s ~/Documents/research-agent/skills ~/.claude/skills/user/research-agent

# 4. Consensus MCP (선택)
claude mcp add-json consensus '{"type":"http","url":"https://mcp.consensus.app/mcp"}'

# 5. 확인
ls -la ~/.claude/skills/user/
```

---

## 🎯 사용법

### 1. 프로젝트 생성

```bash
# 작업 폴더로 이동
cd ~/Documents/research-test  # 또는 원하는 폴더
claude

# Claude에서
> "literature-review 프로젝트 만들어줘"
```

**결과**:
```
literature-review/
├── papers/
│   ├── collected/      (보유 논문)
│   ├── candidates/     (검색 결과)
│   └── staging/
├── .flow.md           (과제 구조)
├── chapters/
└── final/
```

### 2. Flow 작성

`literature-review/.flow.md` 파일을 열어서 과제 구조 작성:

```markdown
## Section 1: Introduction
**목표**:
- [ ] 연구 주제 소개

**필요 레퍼런스**: 
- 주제: `transformer attention mechanism`
- 최소: 3개
```

### 3. 논문 검색

```
> "작업 시작해줘"
```

→ Consensus로 필요한 논문 검색 & 추천

### 4. 논문 다운로드

검색 결과에서 논문 다운로드 → `papers/candidates/`에 저장

### 5. 논문 처리

```
> "새 논문 처리해줘"
```

→ PDF 메타데이터 추출 & `collected/`로 이동

### 6. 초안 작성

```
> "초안 작성해줘"
```

→ Flow 기반으로 챕터별 초안 생성

### 7. 챕터 수정

```
> "Chapter 2 수정해줘: Linear attention 부분 확장해줘"
```

→ 수정 + 자동 일관성 체크

---

## 📁 프로젝트 구조

```
your-project/
├── papers/
│   ├── collected/         # 보유 논문 (PDF)
│   ├── candidates/        # 다운로드한 논문 (임시)
│   └── staging/           # 사용할 논문
├── .flow.md              # 과제 구조 정의
├── .paper-metadata.json  # 논문 메타데이터
├── chapters/             # 챕터별 파일
│   ├── 01-introduction.md
│   ├── 02-background.md
│   └── ...
└── final/                # 최종 결과물
    ├── complete-draft.md
    └── complete-draft.docx
```

---

## 💡 주요 명령어

| 명령어 | 설명 |
|--------|------|
| `"[이름] 프로젝트 만들어줘"` | 새 프로젝트 생성 |
| `"작업 시작해줘"` | Flow 분석 & Consensus 검색 |
| `"새 논문 처리해줘"` | candidates PDF 처리 |
| `"초안 작성해줘"` | Flow 기반 초안 생성 |
| `"Chapter X 수정해줘: [내용]"` | 챕터 수정 + 일관성 체크 |

---

## 🔧 Requirements

- macOS / Linux
- Python 3.8+
- Claude Code
- PyPDF2

---

## 🌟 Features

- ✅ 프로젝트 자동 생성
- ✅ Consensus 논문 검색
- ✅ PDF 메타데이터 자동 추출
- ✅ Flow 기반 초안 생성
- ✅ 챕터 수정 시 자동 일관성 체크
- ✅ Word 문서 자동 생성

---

## 📝 Example Workflow

```bash
# 1. 프로젝트 생성
cd ~/Documents/research-test
claude
> "my-thesis 프로젝트 만들어줘"

# 2. Flow 작성 (nano/vim으로)
nano my-thesis/.flow.md

# 3. 논문 검색
> "작업 시작해줘"

# 4. 논문 다운로드 (브라우저에서)
# → my-thesis/papers/candidates/에 저장

# 5. 논문 처리
> "새 논문 처리해줘"

# 6. 초안 작성
> "초안 작성해줘"

# 7. 수정
> "Chapter 2 수정해줘: 더 자세하게"
```

---

## 🆘 Troubleshooting

### Skill이 인식 안 됨
```bash
# 링크 확인
ls -la ~/.claude/skills/user/

# 다시 링크
rm ~/.claude/skills/user/research-agent
ln -s ~/Documents/research-agent/skills ~/.claude/skills/user/research-agent
```

### PyPDF2 에러
```bash
pip install pypdf2 --break-system-packages
```

### Consensus 검색 안 됨
```bash
# MCP 다시 추가
claude mcp add-json consensus '{"type":"http","url":"https://mcp.consensus.app/mcp"}'
```

---

## 📄 License

MIT

---

## 🤝 Contributing

Issues and PRs welcome!
