# Activity Log 시스템 기획서

**작성일**: 2026-04-23
**상태**: 설계 검토 중 (구현 전)

---

## 1. 🎯 목적

사용자의 모든 주요 작업을 **한 줄 로그**로 append-only 기록하여 두 가지 활용을 가능하게 한다:

1. **Time-travel recovery**: 사용자가 로그 줄을 복사해 "이 시점 상태 보여줘"로 요청 → 시스템이 해당 시점 archive 아티팩트를 찾아 제시
2. **작업 추천**: 사용자가 "작업 추천해줘" 입력 → 시스템이 로그를 분석해 다음에 할 명령과 **그 이유**를 제시

---

## 2. 📋 두 가지 핵심 Use Case

### Use Case A: Time-travel Recovery

**시나리오**:
- 사용자가 2주 전 평가 내용 일부를 참고하려 함
- `.activity.log`를 열어 "[2026-04-10 14:30] 평가 완료 | v1-draft | 287/500..." 라인 복사
- 채팅에 붙여넣고 "이 시점 work-plan 보여줘"
- 시스템: 해당 로그 라인의 `ref:eval-002`를 파싱 → `evaluations/archive/002-2026-04-10-v1-draft/work-plan.md` 조회 → 전체 출력

**필요 조건**:
- 각 로그 라인이 **archive 참조**를 가져야 함 (evaluations/chapters/critical-questions/commitments archive ID)
- ref 포맷이 일관적이어야 함
- 한 라인만으로 시점 복원이 가능해야 함 (다른 라인을 조합할 필요 없음)

### Use Case B: 작업 추천 (Task Recommendation)

**시나리오**:
- 사용자가 3일간 작업 안 함. 다시 프로젝트로 돌아와 "뭘 할지 모르겠음"
- `"작업 추천해줘"` 입력
- 시스템: 최근 N일 로그 분석 → 다음 추천
  ```
  📍 현재 상태
  - 마지막 활동: 2026-04-20 (3일 전) 초안 작성 완료
  - 평가 점수: 378/500 (v1-draft)
  - Commitment 커버리지: 60% (2건 UNFULFILLED)
  - 미해결 stale: 0건

  💡 추천 (우선순위 순)
  1. "Chapter 5 수정해줘: 급진적 steelman 강화"
     → 이유: [C-003] UNFULFILLED, Section 5 대상, Iconoclast 지적 예상
  2. "평가해줘"
     → 이유: 초안 후 3일 경과, v2 평가 시점
  3. "질문 업데이트해줘"
     → 이유: critical-questions v3가 초안 작성 전 기준. v4로 갱신하면 원고 반영 점검 가능
  ```

**필요 조건**:
- 로그가 **현재 상태**를 파싱 가능하게 구조화됨 (점수·커버리지·stale 등)
- **시간 정보**로 "얼마나 오래 안 했는가" 판단 가능
- **미완 작업** 판별 가능 (UNFULFILLED commitment, 미완 HUNT 등)
- 추천 논리를 구성할 신호들이 로그에 누적되어 있어야 함

---

## 3. 📐 로그 엔트리 필수 필드

Use Case A/B를 동시 만족하는 필드 설계:

| 필드 | 설명 | 예시 |
|------|------|------|
| **timestamp** | ISO 8601 축약 | `2026-04-23 14:30` |
| **action** | 명령 또는 이벤트 이름 (한국어) | `평가 완료`, `초안 작성`, `챕터 수정` |
| **stage** | 현재 작업 stage | `flow`, `stage1`, `v1-draft`, `revised`, `final` |
| **target** | 작업 대상 (파일·섹션·논문 등) | `flow.md`, `chapters/02-*`, `Zelazo_2022.pdf` |
| **result** | 결과 요약 (수치 포함) | `287/500 (+32)`, `5 HUNT done`, `3 commitments fulfilled` |
| **ref** | archive 참조 ID (Use Case A 핵심) | `ref:eval-003`, `ref:ch-002`, `ref:q-005` |
| **agents** | 실행된 에이전트 목록 | `flow-evaluator+critical-lens+citation-auditor` |
| **meta** | 부가 상태 (필요 시) | `ambition=critical`, `commits=2/5`, `stale=P1:1` |

### Use Case별 필드 매핑

| 필드 | UC-A 필수? | UC-B 필수? |
|------|----------|----------|
| timestamp | ✅ | ✅ (시간 간격 분석) |
| action | ✅ | ✅ (최근 활동 파악) |
| stage | 🟡 (맥락용) | ✅ (다음 단계 추천) |
| target | ✅ (파일 위치) | 🟡 |
| result | 🟡 | ✅ (미완·성공 판단) |
| ref | ✅ (archive 경로 복원) | ❌ |
| agents | 🟡 | 🟡 |
| meta | ❌ | ✅ (현재 상태 스냅샷) |

---

## 4. 🎨 포맷 설계

### 선택지 비교

| 포맷 | 가독성 | 파싱 | 확장성 |
|------|-------|------|-------|
| A. 자유 텍스트 | 🟢 최고 | 🔴 어려움 | 🟡 |
| B. 파이프 구분 고정 필드 | 🟢 좋음 | 🟢 쉬움 | 🔴 필드 추가 어려움 |
| C. Key=value 반구조 | 🟡 보통 | 🟢 쉬움 | 🟢 |
| D. JSONL (한 줄 JSON) | 🔴 어려움 | 🟢 최고 | 🟢 |

### 채택 포맷: **B + C 하이브리드**

앞부분은 고정 파이프 구분 (사용자가 읽기 쉬움), 뒷부분은 key=value (확장 가능):

```
[TIMESTAMP] ACTION | STAGE | TARGET | RESULT | ref:ID | agents:A,B | key=value key=value
```

**실제 예시**:
```
[2026-04-23 14:30] 평가 완료 | v1-draft | chapters/* | 287/500 (+32) | ref:eval-003 | agents:flow-evaluator,critical-lens,citation-auditor | ambition=critical commits=3/5 stale=P2:1
```

- 앞 4개 필드 (`timestamp`, `action`, `stage`, `target`)는 **고정 위치** — 사용자 눈에 바로 들어옴
- `result`, `ref`, `agents`, `meta`는 **선택적** — 해당 액션에 없는 필드는 생략

### 복사·붙여넣기 최적화

사용자가 로그 라인을 **한 줄 통째로 복사해도 의미 전달**되어야 함. 복사된 라인에서 시스템이 timestamp·action·ref 추출 가능.

---

## 5. 📁 저장 위치와 관리

### 경로

```
projects/{PROJECT_NAME}/.activity.log
```

- **Hidden file** (점으로 시작): 사용자 평소 시야에서 벗어남, 필요 시 `cat`·에디터로 열람
- **프로젝트별 분리**: 프로젝트 간 혼선 없음
- **gitignore 대상**: `projects/`가 이미 gitignore이므로 자동 적용

### 쓰기 방식

- **Append-only**: 절대 수정·삭제 금지
- 새 라인을 파일 끝에 추가
- 신규 라인 쓰기 실패 시 경고 출력하되 명령은 계속 실행 (로그 실패가 작업을 막으면 안 됨)

### 로테이션

- **당분간 불필요**: 프로젝트 수명 내 로그 ≤ 2000 라인 예상 (~150KB)
- 1만 라인 초과 시 `.activity.log.archive/{date}` 로테이션 고려 (향후)

### 읽기 방식

- `"작업 추천해줘"` 시 최근 N일치 (기본 14일) 파싱
- Time-travel 요청 시 사용자가 제공한 라인 하나만 파싱

---

## 6. 📝 로깅 대상 이벤트 전체 목록

### User Commands (모두 로깅)

| 명령 | action 값 | 기록할 주요 필드 |
|------|---------|---------------|
| 프로젝트 생성 | `프로젝트 생성` | target=프로젝트명, meta=ambition |
| 평가해줘 | `평가 완료` | stage, result=점수/판정, ref, agents |
| 레퍼런스 점검해줘 | `레퍼런스 점검` | result=axis1 점수 변화 |
| flow 업데이트해줘 | `flow 업데이트` | result=반영 제안 수 |
| 작업 시작해줘 | `HUNT·REANALYZE 실행` | result=완료수, target=consensus-results.md |
| 새 논문 처리해줘 | `논문 처리` | target=PDF 파일 수, agents=paper-analyst |
| 논문 재분석해줘 | `논문 재분석` | target=파일, result=v→v+1 |
| 논문 제거해줘 | `논문 제거` | target=파일, meta=dangling count |
| 초안 작성해줘 | `초안 작성` | result=챕터 수/단어 수, ref, meta=commits 반영률 |
| Chapter X 수정해줘 | `챕터 수정` | target=Chapter X, result=변경 요약, ref |
| 최종 통합해줘 | `최종 통합` | result=단어 수 |
| 리뷰 체크해줘 | `리뷰 시뮬` | result=판정 |
| 질문 업데이트해줘 | `질문 업데이트` | result=v번호, meta=categories |
| 답변 반영해줘 | `답변 반영` | result=commitments count |
| 비판 모드 설정 | `비판 모드 설정` | meta=level |
| sync 확인해줘 | `sync 점검` | result=stale count by tier |
| gap 분석해줘 | `gap 분석` | result=gap count |
| 방법론 추천/검증 | `방법론 {A/C}` | — |
| 독창성/정의 평가 | `{axis} 심층` | result=axis score |

### System Events (자동 감지 후 로깅)

- flow.md 수정 감지 (다음 명령 실행 시): `flow 수정 감지 | mtime=... | word count=...`
- critical-questions.md 답변 수정 감지: `답변 감지 | v{N} | +{M} chars`
- 논문 PDF candidates/ 추가 감지: `PDF 추가 감지 | +{N} files`
- Stale 감지 (각 명령 gate에서): `stale 감지 | {kind} | P{tier}`

---

## 7. 🧠 "작업 추천" 명령 설계

### 명령어

`"작업 추천해줘"`, `"뭘 해야 해?"`, `"next step"` 등

### 동작 알고리즘

#### 단계 1: 최근 로그 파싱

- `.activity.log`의 최근 14일치 라인 로드
- 현재 **상태 스냅샷** 구성:
  - 마지막 활동 시점
  - 마지막 평가 점수·stage
  - 마지막 commitment 커버리지
  - 미완 HUNT·REANALYZE 과제 수
  - 미해결 stale (sync_state.py check 병행)
  - Critical Mode 활성 여부

#### 단계 2: 휴리스틱 추천 규칙

**Priority 1 — 차단 요소 먼저**:
- stale P1-Critical 있음 → 해당 해결 명령 추천
- dangling citation 있음 → "논문 제거해줘: {파일}" 추천
- UNFULFILLED commitment 있음 → "Chapter X 수정해줘" 추천

**Priority 2 — 다음 자연 단계**:
- 마지막 stage가 flow이고 평가 통과 → "작업 시작해줘"
- Stage 1 리서치 후 → "레퍼런스 점검해줘" + "flow 업데이트해줘"
- 초안 완료 후 → "평가해줘"
- 평가 Major Revision 후 → "Chapter X 수정해줘"
- 평가 Minor Revision 후 → "리뷰 체크해줘" → "최종 통합해줘"

**Priority 3 — 장기 정체 해소**:
- 3일 이상 미활동 → 가장 최근 미완 과제 재개
- 1주 이상 재평가 없음 + 변경 있음 → "평가해줘"
- critical-questions 답변 없이 진행 중 (ambition ≥ critical) → "질문 업데이트해줘"

**Priority 4 — 선택적 강화**:
- empirical 프로젝트 + 방법론 미논의 → "방법론 추천해줘"
- Stage 3 진입 + gap 미분석 → "gap 분석해줘"

#### 단계 3: 추천 출력 형식

```
📍 현재 상태 (로그 최근 {N}일 기반)

   마지막 활동: {action} ({time_ago})
   현재 stage: {stage}
   평가 점수: {score} ({judgment})
   Critical Mode: {ambition}
   Commitment 커버리지: {X}%
   미해결 stale: {N}건 (P1:{a} P2:{b} P3:{c})

💡 작업 추천 (우선순위 순)

1. "{command}"
   이유: {why — 로그 기반 근거}
   예상 효과: {what would change}

2. "{command}"
   이유: ...

3. "{command}"
   이유: ...

🔗 참고 로그 라인:
- [timestamp] {ref 라인}
- [timestamp] {ref 라인}
```

각 추천은 **반드시 로그의 어느 라인을 근거로 하는지** 명시. 블랙박스 추천 금지.

---

## 8. ⏪ "로그 기반 복원" 동작 설계

### 명령어 (암묵적)

사용자가 로그 라인을 채팅에 붙여넣고 후속 요청:
- `"[2026-04-10 14:30] 평가 완료 | v1-draft | ... | ref:eval-003 이 시점 work-plan 보여줘"`
- `"이 로그 상태로 되돌릴 수 있어?"` (복원은 제공 안 함 — 조회만)

### 동작 알고리즘

1. 사용자 입력에서 `ref:` 패턴 추출 (정규식: `ref:([a-z\-]+)-(\d{3})`)
2. ref 타입별 아티팩트 경로 매핑:
   - `ref:eval-NNN` → `evaluations/archive/NNN-{date}-{stage}/`
   - `ref:ch-NNN` → `chapters/archive/NNN-{date}-{trigger}/`
   - `ref:q-NNN` → `critical-questions.archive/NNN-{date}-{trigger}.md`
   - `ref:commits-NNN` → `critical-commitments.archive/NNN-{date}-{trigger}.md`
3. 해당 폴더·파일 내용 조회 후 사용자에게 제시 (읽기 전용)
4. 사용자 요청에 따라 특정 파일만 보여주거나 전체 내용 요약

### 사용자 행동별 응답

| 사용자 요청 | 동작 |
|------------|------|
| "이 시점 work-plan 보여줘" | `archive/NNN/work-plan.md` 출력 |
| "이 시점 evaluation 보여줘" | `archive/NNN/evaluation.md` 출력 |
| "이 시점 챕터 보여줘" | `chapters/archive/NNN/` 전체 출력 |
| "이 시점 상태 요약해줘" | 해당 ref의 모든 파일을 짧게 요약 |
| "이 시점으로 되돌려줘" | ⚠️ 거부 — 사용자 직접 `cp` 안내. 자동 복원은 데이터 파괴 위험 |

---

## 9. 🛠 구현 범위 및 작업

### 최소 구현 (MVP)

1. **로그 쓰기 유틸** (`scripts/activity_log.py`)
   - `append(project, action, fields...)` 함수
   - 포맷 강제, 파일 잠금, append-only

2. **SKILL.md 각 명령 섹션에 로깅 지시 추가**
   - 각 명령 실행 완료 후 activity_log.py 호출
   - 어떤 필드를 기록할지 명령별로 명시

3. **`"작업 추천해줘"` 명령** (신규 SKILL.md 섹션)
   - activity_log.py 파싱 유틸 + sync_state.py check 조합
   - 추천 휴리스틱 실행

4. **Time-travel 패턴 인식** (신규 SKILL.md 섹션 또는 기존 명령 확장)
   - 사용자 입력에서 `ref:` 패턴 감지 시 archive 조회

### 선택적 확장 (Phase 2)

- 로그 시각화 (`"로그 보여줘"` → 최근 30일 타임라인 요약)
- 추천 피드백 루프 (사용자가 추천 수용 여부를 추가 로그)
- 추천 품질 향상용 LLM 기반 분석 (현재는 휴리스틱)

### 비구현 (명시적 제외)

- ❌ 로그 기반 **자동 복원**: 데이터 손실 위험 + 디렉토리 상태 비결정적
- ❌ 실시간 모니터링: 필요 없음
- ❌ 다른 프로젝트와 통합: 프로젝트 단위 격리 유지

---

## 10. 🕳 엣지 케이스

### E1. 로그 파일 없음

신규 프로젝트 첫 명령 시 `.activity.log` 부재.
→ 첫 명령 시 자동 생성, 헤더 주석 추가:
```
# Research Agent Activity Log — {PROJECT_NAME}
# Created: 2026-04-23T09:00:00
# Format: [TIMESTAMP] ACTION | STAGE | TARGET | RESULT | ref:ID | agents:... | key=value...
```

### E2. 로그 쓰기 실패 (disk full 등)

→ 경고 출력하되 **명령은 계속 실행**. 로그 실패로 사용자 작업이 막히면 안 됨.

### E3. 사용자가 로그 수동 편집

→ 포맷 파싱 시 malformed 라인은 **skip**. 경고만 출력. 시스템은 자기 기록을 신뢰하되, 사용자 수정을 침범하지 않음.

### E4. ref가 가리키는 archive가 삭제됨

→ Time-travel 조회 시 archive 부재 감지 → "해당 시점의 {ref}가 보존되어 있지 않습니다" 안내.

### E5. 추천 대상이 없음 (모두 완료)

→ "현재 추천할 작업 없음. 프로젝트가 최종 상태에 도달했거나 {N}일 휴지 중입니다. 제출 준비되었다면 `"최종 통합해줘"` → `"평가해줘"` 권장"

### E6. ambition 수준 변경 중간

→ 로그의 `meta=ambition=X`를 통해 변경 이력 추적. 추천 시 **현재 값** 우선 사용.

### E7. 로그 라인이 여러 ref를 가질 수 있는가?

→ **한 라인 한 ref**로 제한. 여러 archive가 동시 갱신되면 각각 별도 라인 (예: 평가는 eval ref, 같은 명령에서 critical-questions도 갱신되면 별도 라인).

---

## 11. 📊 우선순위 및 구현 단계

### Phase 1 (필수, 단일 commit)

1. `scripts/activity_log.py` 신설 (append + parse 유틸)
2. SKILL.md 모든 명령 섹션에 로그 호출 추가 (~20 곳)
3. `"작업 추천해줘"` 명령 섹션 신설
4. Time-travel 패턴 인식 명령 섹션 신설
5. MANUAL.md에 새 기능 문서화
6. README.md 명령 요약표에 추가

### Phase 2 (선택, 향후)

- `"로그 보여줘"` / `"최근 활동 요약"` 명령
- 추천 품질 개선
- 프로젝트 건강 대시보드

### 예상 변경 규모

- 신규 파일: `scripts/activity_log.py` (~200 lines)
- 수정 파일: SKILL.md (~150 lines 추가), MANUAL.md (~60 lines), README.md (~5 lines)
- 커밋 1개, 약 400 lines 변경

---

## 12. 🎯 성공 지표 (설계 완료 후 검증할 것)

Phase 1 구현 후 다음을 확인:

- [ ] 사용자가 한 달 사용 후 `.activity.log`를 열어 프로젝트 타임라인을 읽을 수 있음
- [ ] 로그 라인 하나를 복사 + 채팅 붙여넣기로 해당 시점 아티팩트 조회 성공
- [ ] 3일 이상 미활동 상태에서 `"작업 추천해줘"`가 구체적·실행 가능한 명령 3개 이상 제시
- [ ] 추천 이유가 로그 라인 참조로 제시됨 (블랙박스 아님)
- [ ] 추천 명령을 수용했을 때 실제로 프로젝트 상태가 개선됨

---

## 13. ❓ 검토 필요 항목 (사용자 확인 요청)

구현 전 다음 사항 확인 부탁드립니다:

1. **포맷 결정**: 제안된 파이프+key=value 하이브리드 OK? 다른 선호 있음?
- 좋아 하이브리드
2. **로그 파일 이름**: `.activity.log` 괜찮은가, `activity.log`(가시)? 다른 이름?
- 보이게 해줘.
3. **로테이션**: 현재 없음. 필요하면 어느 크기/기간 기준?
- 필요없음
4. **Time-travel 자동 복원**: 현재 **거부** 상태. 자동 복원이 정말 필요한지?
- 필요없음
5. **추천 범위**: 기본 14일치 분석. 다른 기본값 선호?
- 14일 좋아
6. **Phase 1 범위**: 위 5개 항목 모두 포함 OK? 줄이거나 늘릴 항목?
- 모두 포함

확인되면 바로 구현 진행하겠습니다.
