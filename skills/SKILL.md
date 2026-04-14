# SKILL.md
---
name: research-agent
description: "Academic research project management with AI agents. Creates projects, manages papers with Consensus, generates drafts with Flow-based structure."
---

# Research Agent System

## 프로젝트 생성

사용자가 "프로젝트 만들어줘", "[이름] 프로젝트 생성", "[이름] 과제 만들어줘" 등을 말하면:

### 단계 1: 폴더 구조 생성

프로젝트 이름을 추출하여 다음 폴더 구조를 생성하세요:

```bash
mkdir -p {PROJECT_NAME}/papers/collected
mkdir -p {PROJECT_NAME}/papers/candidates  
mkdir -p {PROJECT_NAME}/papers/staging
mkdir -p {PROJECT_NAME}/chapters
mkdir -p {PROJECT_NAME}/final
```

### 단계 2: .flow.md 템플릿 생성

{PROJECT_NAME}/.flow.md 파일을 다음 내용으로 생성하세요:

```
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
- [ ] 이론적 배경

**필요한 레퍼런스**:
- 주제: `[검색 키워드 입력]`
- 최소 논문 수: 5

**예상 길이**: ~1000 words

---

### Section 3: Methodology
**목표**:
- [ ] 연구 방법 설명
- [ ] 데이터 설명

**필요한 레퍼런스**:
- 주제: `[검색 키워드 입력]`
- 최소 논문 수: 3

**예상 길이**: ~800 words

---

### Section 4: Conclusion
**목표**:
- [ ] 핵심 결과 요약
- [ ] 한계점 및 향후 연구

**예상 길이**: ~400 words
```

### 단계 3: .paper-metadata.json 생성

{PROJECT_NAME}/.paper-metadata.json 파일을 다음 내용으로 생성하세요:

```json
{
  "papers": [],
  "last_updated": null,
  "project_name": "{PROJECT_NAME}",
  "version": "1.0"
}
```

### 단계 4: 안내 메시지 출력

프로젝트 생성 완료 후 다음과 같이 사용자에게 안내하세요:

```
✅ 프로젝트 생성 완료: {PROJECT_NAME}/

📁 구조:
   {PROJECT_NAME}/
   ├── papers/
   │   ├── collected/      (보유 논문을 여기에 복사하세요)
   │   ├── candidates/     (검색된 논문이 여기 저장됩니다)
   │   └── staging/        (사용할 논문)
   ├── .flow.md           (템플릿이 생성되었습니다 - 수정 필요)
   ├── chapters/
   └── final/

👉 다음 단계:
   1. Finder에서 보유 논문을 papers/collected/에 복사
   2. .flow.md 파일을 열어서 과제 구조 작성
   3. "작업 시작해줘" 입력
```

---

## 논문 처리

사용자가 "새 논문 처리해줘", "논문 분석해줘", "candidates 처리해줘" 등을 말하면:

### 단계 1: candidates 폴더 확인

현재 프로젝트의 papers/candidates/ 폴더를 확인하세요.

### 단계 2: 각 PDF 파일 처리

candidates 폴더에 있는 각 PDF에 대해:

1. Python 스크립트 실행하여 메타데이터 추출
2. 결과를 .paper-metadata.json에 추가
3. PDF를 collected/로 이동

### 단계 3: 결과 보고

```
✅ 논문 처리 완료: {N}개

📄 Smith_2023_Attention.pdf
   제목: [추출된 제목]
   저자: [추출된 저자]
   → papers/collected/로 이동 완료

💾 .paper-metadata.json 업데이트 완료
```

---

## Consensus 검색 (작업 시작)

사용자가 "작업 시작해줘", "논문 검색해줘", "필요한 논문 찾아줘" 등을 말하면:

### 단계 1: .flow.md 읽기

현재 프로젝트의 .flow.md 파일을 읽어서 각 섹션의 "필요한 레퍼런스" 주제를 추출하세요.

### 단계 2: Consensus MCP로 검색

각 섹션의 검색 키워드로 Consensus를 검색하세요.

### 단계 3: 결과 포맷팅

```
🔍 필요한 논문 검색 결과:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Section 1: Introduction 검색

📄 1. [논문 제목]
   저자: [저자]
   학회: [학회]
   인용: [횟수]
   
   📝 핵심 내용: [요약]
   🎯 관련성: [점수]%
   🔗 PDF: [링크]

[더 많은 결과...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 추천 논문 (우선순위):
   1. [논문 1]
   2. [논문 2]

👉 다음 단계:
   위 링크에서 필요한 논문을 다운로드하여
   papers/candidates/ 폴더에 저장한 후
   "새 논문 처리해줘" 입력
```

---

## 초안 작성

사용자가 "초안 작성해줘", "draft 생성", "글 써줘" 등을 말하면:

### 단계 1: 준비 확인

1. .flow.md 읽기
2. .paper-metadata.json 읽기
3. papers/collected/ 폴더의 논문 목록 확인

### 단계 2: 각 섹션 작성

.flow.md의 각 섹션에 대해:

1. 섹션 목표 확인
2. 관련 논문 선택
3. 논문 내용을 바탕으로 작성
4. 인용 포함

### 단계 3: 파일 저장

```
chapters/01-introduction.md
chapters/02-background.md
chapters/03-methodology.md
chapters/04-conclusion.md
final/complete-draft.md
```

### 단계 4: DOCX 생성

docx skill을 사용하여 Word 문서 생성:
```
final/complete-draft.docx
```

### 단계 5: 결과 보고

```
✅ 초안 작성 완료!

📊 통계:
   - 총 단어 수: [단어 수]
   - 챕터: 4개
   - 인용: [개수]
   - 사용 논문: [개수]

📁 생성된 파일:
   - chapters/01-introduction.md
   - chapters/02-background.md
   - chapters/03-methodology.md
   - chapters/04-conclusion.md
   - final/complete-draft.md
   - final/complete-draft.docx

👉 다음 단계:
   챕터를 수정하려면:
   "Chapter 2 수정해줘: [수정 내용]"
```

---

## 챕터 수정 + 일관성 체크

사용자가 "Chapter X 수정해줘: [내용]"이라고 하면:

### 단계 1: 챕터 수정

요청된 수정 사항을 해당 챕터에 적용하세요.

### 단계 2: 자동 일관성 체크

**수정 직후 자동으로 다음을 확인하세요:**

1. Flow 목표 달성 확인
2. 이전/다음 챕터와의 연결 확인
3. 인용 적절성 확인
4. 중복 내용 확인

### 단계 3: 통합 보고

```
✅ Chapter X 수정 완료

📝 변경사항:
   - [변경 내용]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 자동 일관성 체크 결과:

✅ Flow 목표 달성도: [점수]
✅ 챕터 간 연결: [평가]
✅ 인용 적절성: [평가]

⚠️ 발견된 이슈: [이슈 내용]
💡 제안: [개선 제안]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💯 전체 평가: [등급]
```
