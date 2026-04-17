---
name: research-agent
description: "Academic research project management with AI agents. Creates projects, manages papers with Consensus, generates drafts with Flow-based structure."
---

# Research Agent System

이 스킬은 research-agent 폴더 안의 projects/ 디렉토리에서 작동합니다.

## 서브 에이전트 시스템

이 스킬은 6개의 서브 에이전트를 사용합니다. 각 에이전트의 상세 프롬프트와 노하우는 `skills/agents/` 폴더에 정의되어 있습니다. 에이전트를 호출할 때는 해당 파일의 전체 내용을 읽어서 Agent 도구의 prompt에 포함하세요.

| 에이전트 | 파일 | 호출 시점 | 방식 |
|----------|------|-----------|------|
| **paper-analyst** | `skills/agents/paper-analyst.md` | "논문 처리" (Step 5) | 자동 |
| **writing-architect** | `skills/agents/writing-architect.md` | "초안 작성" (Step 6) | 자동 |
| **citation-auditor** | `skills/agents/citation-auditor.md` | "챕터 수정" (Step 7) | 자동 |
| **gap-finder** | `skills/agents/gap-finder.md` | "gap 분석해줘" | 수동 |
| **methodology-advisor** | `skills/agents/methodology-advisor.md` | "방법론 추천/검증해줘" | 수동 |
| **peer-reviewer** | `skills/agents/peer-reviewer.md` | "리뷰 체크/답변 도와줘" | 수동 |

### 에이전트 호출 방법

서브 에이전트를 호출할 때는 Agent 도구를 사용하세요:

1. 해당 에이전트 파일(`skills/agents/{agent-name}.md`)을 Read 도구로 읽기
2. 에이전트 프롬프트에 다음을 포함:
   - 에이전트 파일의 전체 내용 (노하우 + 출력 형식)
   - 현재 프로젝트의 flow.md 내용
   - 처리할 대상 파일 경로
3. Agent 도구로 실행 (독립된 컨텍스트에서 작업)
4. 결과를 지정된 파일에 저장

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
mkdir -p projects/{PROJECT_NAME}/papers/analyzed
mkdir -p projects/{PROJECT_NAME}/chapters
mkdir -p projects/{PROJECT_NAME}/final
```

### 단계 3: FLOW-TEMPLATE.md (가이드) 및 flow.md (작성용) 생성

projects/{PROJECT_NAME}/FLOW-TEMPLATE.md 와 projects/{PROJECT_NAME}/flow.md 두 파일을 생성하세요. FLOW-TEMPLATE.md는 참고용 가이드 원본, flow.md는 사용자가 직접 수정합니다. 두 파일 모두 보이는 파일이며 점(.)으로 시작하지 않습니다.

**FLOW-TEMPLATE.md의 원본은 `skills/FLOW-TEMPLATE.md`에 보관되어 있습니다.** 프로젝트 생성 시 이 파일을 읽어서 `projects/{PROJECT_NAME}/FLOW-TEMPLATE.md`와 `projects/{PROJECT_NAME}/flow.md`에 복사하세요. 이 범용 템플릿에는 두 가지 트랙이 포함되어 있습니다:

- **Track A: 이론적·개념적 에세이** — 기존 개념 비판, 새 프레임워크 제안
  - Introduction → Literature Review → Theoretical Framework → Core Argument → Counterarguments → Implications → Conclusion
- **Track B: 경험적 연구 (IMRaD)** — 데이터 수집 → 분석 → 결과 해석
  - Introduction → Literature Review → Methodology → Results → Discussion & Conclusion

두 트랙 모두 다음 구조를 각 섹션에 포함합니다:
1. **핵심 앵커**: 연구 질문 (RQ) + 핵심 주장 (Thesis) — 모든 섹션이 이것에 답해야 함
2. **하위 질문**: "이 섹션이 답하는 질문은?" — 섹션의 존재 이유
3. **논증 설계**: 주장 → 근거 → 반론 → 다음 섹션 연결 — 섹션 간 논리 흐름
4. **핵심 레퍼런스 테이블**: 논문 + 뒷받침할 주장 — 논문-주장 매핑

flow.md는 FLOW-TEMPLATE.md를 복사한 뒤 사용자가 해당 트랙을 선택하고 내용을 채웁니다.

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
           │   ├── candidates/     (선택한 논문, 처리 대기)
           │   └── analyzed/       (에이전트 분석 리포트)
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

### 단계 4: 🤖 paper-analyst 에이전트 자동 호출

각 PDF 처리 후 **자동으로** paper-analyst 서브 에이전트를 호출하여 심층 분석을 수행한다.

1. `skills/agents/paper-analyst.md` 파일을 읽는다
2. 현재 프로젝트의 `flow.md`를 읽는다
3. 각 PDF에 대해 Agent 도구로 paper-analyst를 실행한다:
   - 에이전트에게 전달: PDF 파일 경로 + flow.md 내용 + paper-analyst.md의 전체 지침
   - 에이전트가 수행: 논문 읽기 → 3줄 요약, 핵심 기여, 한계, 관련성 점수, 활용 방안 분석
4. 분석 결과를 `papers/analyzed/{파일명}-analysis.md`에 저장한다

**여러 논문이 있을 경우 병렬로 에이전트를 호출**하여 효율적으로 처리한다.

### 단계 5: 결과 보고

처리된 모든 논문에 대해 다음과 같이 보고하세요:

```
✅ 논문 처리 완료: {N}개

📄 Smith_2023_Attention.pdf
   제목: Attention is All You Need
   저자: Vaswani et al.
   페이지: 15
   → papers/collected/로 이동 완료

   🤖 paper-analyst 분석:
   ├── 3줄 요약: Transformer 아키텍처를 제안...
   ├── 관련성: ⭐⭐⭐⭐⭐ (5/5)
   ├── 활용: Section 1 (Introduction), Section 2 (Background)
   └── 분석 파일: papers/analyzed/Smith_2023_Attention-analysis.md

📄 Brown_2020_GPT3.pdf
   [같은 형식]

💾 .paper-metadata.json 업데이트 완료
📊 현재 보유 논문: {TOTAL}개 | 분석 완료: {ANALYZED}개
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
4. **papers/analyzed/ 폴더의 분석 리포트 확인** (paper-analyst 결과)

### 단계 2: 🤖 writing-architect 에이전트 호출 — Phase 1: 논증 구조 설계

1. `skills/agents/writing-architect.md` 파일을 읽는다
2. Agent 도구로 writing-architect를 실행한다:
   - 전달: flow.md + 모든 analyzed/*.md 파일 + writing-architect.md 지침
   - 수행: 각 섹션의 논증 구조(주장→근거→반박→재반박) 설계
3. 설계된 구조를 **사용자에게 보여주고 확인을 받는다**:

```
✍️ 논증 구조 설계 완료

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 Section 1: Introduction (4 문단)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
문단 1: [연구 배경 — 넓은 맥락 설정]
  └── 근거: Smith (2023), Lee (2024)
문단 2: [문제 제기 — 기존 접근의 한계]
  └── 근거: Park (2022)
문단 3: [연구 Gap — 왜 이 연구가 필요한지]
  └── 근거: gap-analysis 결과 활용
문단 4: [연구 목적 — 본 연구의 방향]

[다른 섹션도 같은 형식...]

👉 이 구조로 진행할까요? 수정이 필요하면 말씀해주세요.
```

4. **사용자가 승인하면** Phase 2로 진행
5. **수정 요청 시** 구조를 수정하고 다시 확인

### 단계 3: 🤖 writing-architect 에이전트 — Phase 2: 초안 작성

사용자 승인 후 writing-architect 에이전트가 구조에 따라 초안을 작성한다:

1. 각 섹션별로 순차 작성 (Topic Sentence First → Evidence → Analysis → Transition)
2. 종합(Synthesis) 위주 서술 (논문별 요약 나열 금지)
3. 인용 강도를 근거 수준에 맞게 조절 (suggests/indicates/demonstrates)

### 단계 4: 파일 저장

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

### 단계 5: DOCX 생성

docx skill을 사용하여 Word 문서 생성:
```bash
projects/{PROJECT_NAME}/final/complete-draft.docx
```

### 단계 6: 결과 보고

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
3. **중복 내용 확인**

### 단계 5: 🤖 citation-auditor 에이전트 자동 호출

일관성 체크와 함께 **자동으로** citation-auditor 서브 에이전트를 호출한다.

1. `skills/agents/citation-auditor.md` 파일을 읽는다
2. Agent 도구로 citation-auditor를 실행한다:
   - 전달: 수정된 챕터 내용 + papers/collected/의 원문 PDF + papers/analyzed/의 분석 리포트 + citation-auditor.md 지침
   - 수행: 인용 내용 정확성 검증, APA 형식 체크, 인용 분포 분석
3. 감사 결과를 보고에 포함한다

### 단계 6: 통합 결과 보고

```
✅ Chapter {X} 수정 완료

📝 변경사항:
   - [변경 내용 요약]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 자동 일관성 체크 결과:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Flow 목표 달성도: 100%
✅ 챕터 간 연결: 자연스러움
✅ 중복 내용: 없음

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 인용 감사 결과 (citation-auditor):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 인용 요약: 총 {N}개
   ✅ 정확: {N}개
   ⚠️ 수정 필요: {N}개
   ❌ 검증 불가: {N}개

🔴 즉시 수정 필요:
   - Ch{X} p.{Y}: "Smith는 X를 증명" → 원문은 상관관계만 보고
     💡 수정: "Smith (2023) found a correlation between..."

🟡 권장:
   - APA 형식 오류 {N}건
   - Section {N} 인용 부족 (현재 {N}개, 권장 {N}개 이상)

💯 전체 평가: A (94/100)
```

---

## Gap 분석 (수동 호출)

사용자가 "gap 분석해줘", "연구 gap 찾아줘", "뭐가 안 다뤄졌어?" 등을 말하면:

### 단계 1: 🤖 gap-finder 에이전트 호출

1. `skills/agents/gap-finder.md` 파일을 읽는다
2. 현재 프로젝트의 `flow.md`와 `papers/analyzed/` 전체를 읽는다
3. Agent 도구로 gap-finder를 실행한다:
   - 전달: flow.md + 모든 analyzed/*.md + gap-finder.md 지침
   - 수행: 방법론/응용/데이터/이론/시간 Gap 5종 탐색
4. 결과를 `projects/{PROJECT_NAME}/gaps-analysis.md`에 저장한다

### 단계 2: 결과 보고

```
🔍 연구 Gap 분석 완료

📊 발견된 Gap: {N}개

| # | 유형 | Gap | 난이도 | 임팩트 |
|---|------|-----|--------|--------|
| 1 | 방법론 | [설명] | 🟢 낮음 | ⭐⭐⭐⭐⭐ |
| 2 | 응용 | [설명] | 🟡 중간 | ⭐⭐⭐⭐ |
| 3 | 데이터 | [설명] | 🔴 높음 | ⭐⭐⭐ |

⭐ 최우선 추천: Gap 1 — [이유]

💾 상세 분석: projects/{PROJECT_NAME}/gaps-analysis.md
```

---

## 방법론 추천/검증 (수동 호출)

사용자가 "방법론 추천해줘", "어떻게 접근해야 해?", "방법론 검증해줘" 등을 말하면:

### 단계 1: 모드 판별

- **Advisor 모드**: "추천", "어떻게", "방법 제안" 등 → 사전 추천
- **Critic 모드**: "검증", "괜찮아?", "체크" 등 → 사후 검증

### 단계 2: 🤖 methodology-advisor 에이전트 호출

1. `skills/agents/methodology-advisor.md` 파일을 읽는다
2. Agent 도구로 methodology-advisor를 실행한다:
   - Advisor: flow.md + analyzed/*.md + 연구 질문 전달 → 3가지 방법론 비교 표 생성
   - Critic: flow.md + 해당 챕터(chapters/03-methodology.md) 전달 → 타당성/신뢰성/윤리 검증
3. 결과를 화면에 보고한다

### 단계 3: 결과 보고 (Advisor 예시)

```
🧪 방법론 추천 결과

연구 질문 유형: [설명적/탐색적/...]

| 기준 | 방법 1 | 방법 2 | 방법 3 |
|------|--------|--------|--------|
| 방법 | [이름] | [이름] | [이름] |
| 난이도 | 🟢 | 🟡 | 🔴 |
| 소요 시간 | 2주 | 4주 | 8주 |
| 임팩트 | 중간 | 높음 | 매우 높음 |

⭐ 추천: 방법 1 — [현실적 이유]
```

---

## 리뷰 체크/답변 (수동 호출)

사용자가 "리뷰 체크해줘", "심사 시뮬레이션", "리뷰 답변 도와줘" 등을 말하면:

### 단계 1: 모드 판별

- **Mode A (시뮬레이션)**: "리뷰 체크", "심사 시뮬레이션", "제출 전 체크" → 사전 심사
- **Mode B (대응)**: "리뷰 답변", "리뷰 분석", 리뷰 텍스트 붙여넣기 → 사후 대응

### 단계 2: 🤖 peer-reviewer 에이전트 호출

1. `skills/agents/peer-reviewer.md` 파일을 읽는다
2. Agent 도구로 peer-reviewer를 실행한다:
   - Mode A: final/complete-draft.md + papers/analyzed/ 전달 → 가상 심사자 2~3명 시뮬레이션
   - Mode B: 사용자가 붙여넣은 리뷰 텍스트 + 원고 전달 → 이슈 분류 + 답변 전략 + 초안
3. 결과를 화면에 보고한다

### 단계 3: 결과 보고 (Mode A 예시)

```
💬 사전 심사 시뮬레이션 결과

📋 종합 판정: Minor Revision

Reviewer 1 (방법론): Minor Revision
   🔴 [Major] 표본 크기 정당화 부족 → 검정력 분석 추가 필요
   🟡 [Minor] 변수 측정 방법 불명확

Reviewer 2 (분야 전문가): Major Revision
   🔴 [Major] 핵심 선행연구 Johnson (2022) 누락
   🟡 [Minor] 이론적 프레임워크 보강 필요

Reviewer 3 (실용주의자): Accept with Minor
   🟡 [Minor] Conclusion에서 실무적 함의 보강

🔴 반드시 수정 (2건):
   1. 표본 크기 정당화 → Section 3에 power analysis 추가
   2. Johnson (2022) → Background에 통합

🟡 수정 권장 (3건):
   [...]
```

---

## 전체 명령어 요약

| 명령어 | 동작 | 에이전트 |
|--------|------|----------|
| `"[이름] 프로젝트 만들어줘"` | 프로젝트 생성 | - |
| `"작업 시작해줘"` | Consensus 검색 → consensus-results.md | - |
| `"새 논문 처리해줘"` | PDF 처리 + 심층 분석 | 🤖 paper-analyst (자동) |
| `"초안 작성해줘"` | 구조 설계 → 확인 → 초안 | 🤖 writing-architect (자동) |
| `"Chapter X 수정해줘"` | 수정 + 일관성 + 인용 감사 | 🤖 citation-auditor (자동) |
| `"gap 분석해줘"` | 연구 Gap 탐색 | 🤖 gap-finder |
| `"방법론 추천/검증해줘"` | 방법론 제안 또는 검증 | 🤖 methodology-advisor |
| `"리뷰 체크/답변 도와줘"` | 심사 시뮬레이션 또는 대응 | 🤖 peer-reviewer |
