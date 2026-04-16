---
name: research-agent
description: "Academic research project management with AI agents. Creates projects, manages papers with Consensus, generates drafts with Flow-based structure."
---

# Research Agent System

이 스킬은 research-agent 폴더 안의 projects/ 디렉토리에서 작동합니다.

## 프로젝트 생성

사용자가 "프로젝트 만들어줘", "[이름] 프로젝트 생성", "[이름] 과제 만들어줘" 등을 말하면:

### 단계 1: projects 폴더 확인

현재 research-agent 폴더에 있는지 확인하고, projects 폴더가 없으면 생성:

```bash
mkdir -p projects
```

### 단계 2: 프로젝트 폴더 구조 생성

프로젝트 이름을 추출하여 다음 폴더 구조를 생성하세요:

```bash
mkdir -p projects/{PROJECT_NAME}/papers/collected
mkdir -p projects/{PROJECT_NAME}/papers/candidates
mkdir -p projects/{PROJECT_NAME}/chapters
mkdir -p projects/{PROJECT_NAME}/final
```

### 단계 3: FLOW-TEMPLATE.md (가이드) 및 flow.md (작성용) 생성

projects/{PROJECT_NAME}/FLOW-TEMPLATE.md 와 projects/{PROJECT_NAME}/flow.md 두 파일을 모두 동일한 내용으로 생성하세요. FLOW-TEMPLATE.md는 참고용 가이드로 원본 그대로 유지하고, flow.md는 사용자가 직접 수정하여 사용합니다. 두 파일 모두 보이는 파일이며 점(.)으로 시작하지 않습니다:

```markdown
# Assignment Flow

## 메타데이터
- **과제명**: [과제 제목을 입력하세요]
- **코스**: [과목명]
- **마감일**: YYYY-MM-DD
- **예상 길이**: [단어 수] words
- **인용 스타일**: APA

## 전체 구조

### Section 1: Introduction
**목표**:
- [ ] 연구 주제 소개
- [ ] 문제 제기
- [ ] 연구 질문 명확화

**필요한 레퍼런스**:
- 주제: `[검색 키워드 입력]`
- 최소 논문 수: 3

**예상 길이**: ~500 words

---

### Section 2: Background
**목표**:
- [ ] 관련 연구 정리
- [ ] 이론적 배경 설명
- [ ] 주요 개념 정의

**필요한 레퍼런스**:
- 주제: `[검색 키워드 입력]`
- 최소 논문 수: 5

**예상 길이**: ~1000 words

---

### Section 3: Methodology
**목표**:
- [ ] 연구 방법 설명
- [ ] 데이터 설명
- [ ] 분석 방법

**필요한 레퍼런스**:
- 주제: `[검색 키워드 입력]`
- 최소 논문 수: 3

**예상 길이**: ~800 words

---

### Section 4: Analysis
**목표**:
- [ ] 결과 제시
- [ ] 분석 및 해석

**필요한 레퍼런스**:
- 주제: `[검색 키워드 입력]`
- 최소 논문 수: 2

**예상 길이**: ~1000 words

---

### Section 5: Conclusion
**목표**:
- [ ] 핵심 결과 요약
- [ ] 연구 기여도
- [ ] 한계점
- [ ] 향후 연구 방향

**예상 길이**: ~400 words
```

### 단계 4: .paper-metadata.json 생성

projects/{PROJECT_NAME}/.paper-metadata.json 파일을 다음 내용으로 생성하세요:

```json
{
  "papers": [],
  "last_updated": null,
  "project_name": "{PROJECT_NAME}",
  "version": "1.0"
}
```

### 단계 5: 안내 메시지 출력

프로젝트 생성 완료 후 다음과 같이 사용자에게 안내하세요:

```
✅ 프로젝트 생성 완료: projects/{PROJECT_NAME}/

📁 구조:
   research-agent/
   └── projects/
       └── {PROJECT_NAME}/
           ├── papers/
           │   ├── collected/      (메타데이터 처리 완료된 논문)
           │   └── candidates/     (선택한 논문, 처리 대기)
           ├── FLOW-TEMPLATE.md   (가이드 - 수정하지 마세요)
           ├── flow.md            (실제 작성용 - 이 파일을 수정하세요)
           ├── chapters/
           └── final/

👉 다음 단계:
   1. projects/{PROJECT_NAME}/flow.md 파일을 열어서 과제 구조 작성
      (FLOW-TEMPLATE.md는 참고용으로 두고, flow.md만 수정)
   2. "작업 시작해줘" 입력
```

---

## 논문 처리

사용자가 "새 논문 처리해줘", "논문 분석해줘", "candidates 처리해줘" 등을 말하면:

### 단계 1: 현재 프로젝트 확인

현재 작업 중인 프로젝트를 확인하세요. 사용자가 명시하지 않았다면 가장 최근에 수정된 프로젝트를 사용하세요.

### 단계 2: candidates 폴더 스캔

```bash
ls -la projects/{PROJECT_NAME}/papers/candidates/*.pdf
```

### 단계 3: 각 PDF 파일 처리

candidates 폴더에 있는 각 PDF에 대해:

1. **메타데이터 추출**:
```bash
python scripts/extract_metadata.py projects/{PROJECT_NAME}/papers/candidates/{FILENAME}.pdf
```

2. **결과를 .paper-metadata.json에 추가**:
   - 파일명
   - 제목 (추출된 값 또는 파일명)
   - 저자
   - 페이지 수
   - 추가 날짜

3. **PDF를 collected/로 이동**:
```bash
mv projects/{PROJECT_NAME}/papers/candidates/{FILENAME}.pdf projects/{PROJECT_NAME}/papers/collected/
```

### 단계 4: 결과 보고

처리된 모든 논문에 대해 다음과 같이 보고하세요:

```
✅ 논문 처리 완료: {N}개

📄 Smith_2023_Attention.pdf
   제목: Attention is All You Need
   저자: Vaswani et al.
   페이지: 15
   → projects/{PROJECT_NAME}/papers/collected/로 이동 완료

📄 Brown_2020_GPT3.pdf
   제목: Language Models are Few-Shot Learners
   저자: Brown et al.
   페이지: 75
   → projects/{PROJECT_NAME}/papers/collected/로 이동 완료

💾 .paper-metadata.json 업데이트 완료

📊 현재 보유 논문: {TOTAL}개
```

---

## Consensus 검색 (작업 시작)

사용자가 "작업 시작해줘", "논문 검색해줘", "필요한 논문 찾아줘" 등을 말하면:

### 단계 1: 현재 프로젝트의 flow.md 읽기

```bash
cat projects/{PROJECT_NAME}/flow.md
```

각 섹션의 "필요한 레퍼런스" 주제를 추출하세요.

### 단계 2: Consensus MCP로 검색

각 섹션의 검색 키워드로 Consensus를 검색하세요. 
각 키워드당 최소 5-10개의 결과를 가져오세요.

### 단계 3: 결과를 papers/consensus-results.md 파일에 저장

검색 결과를 화면에 출력하는 것과 동시에 **반드시 projects/{PROJECT_NAME}/papers/consensus-results.md 파일에 저장**하세요. 각 논문의 PDF/DOI URL은 클릭 가능한 마크다운 링크 형식 (`[제목](URL)`)으로 포함해야 합니다.

파일 구조 예시:

```markdown
# Consensus 검색 결과

검색 일시: YYYY-MM-DD HH:MM

---

## Section 1: Introduction
**검색 키워드**: `transformer attention mechanism`

### 1. Vaswani et al. (2017) ⭐⭐⭐⭐⭐
- **제목**: [Attention is All You Need](https://arxiv.org/pdf/1706.03762.pdf)
- **학회**: NeurIPS 2017
- **인용**: 50,000+회
- **핵심 내용**: Transformer 아키텍처 최초 제안, Self-attention으로 RNN/CNN 대체
- **관련성**: 95%
- **활용 방안**: 기초 개념 설명 및 배경 제시
- **PDF 링크**: https://arxiv.org/pdf/1706.03762.pdf

---
```

### 단계 4: 결과 포맷팅 (화면 출력)

**각 섹션별로 구분하여** 다음과 같이 제시하세요:

```
🔍 필요한 논문 검색 결과:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 Section 1: Introduction
검색 키워드: "transformer attention mechanism"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 1. Vaswani et al. (2017) ⭐⭐⭐⭐⭐
   제목: "Attention is All You Need"
   학회: NeurIPS 2017
   인용: 50,000+회
   
   📝 핵심 내용:
   - Transformer 아키텍처 최초 제안
   - Self-attention 메커니즘으로 RNN/CNN 대체
   - 병렬 처리 가능하여 학습 속도 향상
   
   🎯 관련성: 95%
   💡 활용 방안: 기초 개념 설명 및 배경 제시
   
   🔗 PDF: https://arxiv.org/pdf/1706.03762.pdf

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 추천 논문 (우선순위):
   1. [논문 1]
   2. [논문 2]

💾 검색 결과 저장됨: projects/{PROJECT_NAME}/papers/consensus-results.md

👉 다음 단계:
   1. papers/consensus-results.md 파일의 링크에서 필요한 논문을 다운로드
   2. 다운로드한 PDF를 projects/{PROJECT_NAME}/papers/candidates/ 폴더에 저장
   3. "새 논문 처리해줘" 입력
```

---

## 초안 작성

사용자가 "초안 작성해줘", "draft 생성", "글 써줘" 등을 말하면:

### 단계 1: 준비 확인

1. **현재 프로젝트의 flow.md 읽기**
2. **현재 프로젝트의 .paper-metadata.json 읽기**
3. **papers/collected/ 폴더의 논문 목록 확인**

### 단계 2: 각 섹션별로 작성

flow.md의 각 섹션에 대해 순차적으로:

1. **섹션 목표 확인**
2. **관련 논문 선택**
3. **논문 내용을 바탕으로 작성**
4. **적절한 인용 포함**
5. **목표 단어 수에 맞춰 작성**

### 단계 3: 파일 저장

각 섹션을 개별 파일로 저장:

```bash
projects/{PROJECT_NAME}/chapters/01-introduction.md
projects/{PROJECT_NAME}/chapters/02-background.md
projects/{PROJECT_NAME}/chapters/03-methodology.md
projects/{PROJECT_NAME}/chapters/04-analysis.md
projects/{PROJECT_NAME}/chapters/05-conclusion.md
```

통합본도 생성:
```bash
projects/{PROJECT_NAME}/final/complete-draft.md
```

### 단계 4: DOCX 생성

docx skill을 사용하여 Word 문서 생성:
```bash
projects/{PROJECT_NAME}/final/complete-draft.docx
```

### 단계 5: 결과 보고

```
✅ 초안 작성 완료!

📊 통계:
   - 총 단어 수: 3,245 words
   - 챕터: 5개
   - 총 인용: 18개
   - 사용된 논문: 8개

📁 생성된 파일:
   ✓ chapters/01-introduction.md (487 words)
   ✓ chapters/02-background.md (1,245 words)
   ✓ chapters/03-methodology.md (987 words)
   ✓ chapters/04-analysis.md (750 words)
   ✓ chapters/05-conclusion.md (526 words)
   ✓ final/complete-draft.md (전체 통합본)
   ✓ final/complete-draft.docx (Word 문서)

👉 다음 단계:
   챕터를 수정하려면:
   "Chapter 2 수정해줘: [구체적인 수정 내용]"
```

---

## 챕터 수정 + 자동 일관성 체크

사용자가 "Chapter X 수정해줘: [내용]" 또는 "X장 수정: [내용]" 등을 말하면:

### 단계 1: 챕터 파일 읽기

```bash
cat projects/{PROJECT_NAME}/chapters/0{X}-*.md
```

### 단계 2: 수정 사항 적용

사용자가 요청한 수정 사항을 해당 챕터에 적용하세요.

### 단계 3: 수정된 챕터 저장

파일에 수정된 내용을 저장하세요.

### 단계 4: 자동 일관성 체크

**수정 직후 자동으로 다음을 확인하세요:**

1. **Flow 목표 달성 확인**
2. **이전/다음 챕터와의 연결 확인**
3. **인용 적절성 확인**
4. **중복 내용 확인**

### 단계 5: 통합 결과 보고

```
✅ Chapter {X} 수정 완료

📝 변경사항:
   - [변경 내용 요약]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 자동 일관성 체크 결과:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Flow 목표 달성도: 100%
✅ 챕터 간 연결: 자연스러움
✅ 인용 적절성: 양호

💯 전체 평가: A (94/100)
```
