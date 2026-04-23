# 평가 프로세스 개선안

> ⚠️ **이 문서는 아카이브입니다.** 2026-04-23 작성된 리팩터 설계 초안이며, 핵심 개선은 이미 구현 완료되어 현행 시스템에 반영되었습니다 (evaluation-orchestrator + axis1~6 scorer 병렬 delta 평가). **현행 시스템의 사용법·아키텍처는 [README.md](../README.md) · [MANUAL.md](../MANUAL.md) · [PRINCIPLES.md](../PRINCIPLES.md)를 참고하세요.** 아래 본문은 당시 의사결정의 근거·대안 비교를 참고용으로 보존한 것입니다.

**작성**: 2026-04-23
**작성 맥락**: CDEA 프로젝트에서 `평가해줘` 실행 시 예상 7-12분 소요 — 사용자 개입 전까지 계속 대기 필요. 작업 흐름 병목.

---

## 1. 현재 상태 진단

### 1.1 측정된 병목

**실제 관찰 사례 (CDEA 프로젝트)**:
| 시점 | 평가 종류 | 소요 시간 |
|------|----------|----------|
| 초판 (flow.md 97 lines) | 5축 | 약 5분 |
| Critical Mode 추가 | 6축 | 약 6분 |
| 예상 (refine 후, 138편 context) | 6축 | **7-12분** |

### 1.2 원인 분석

**A. 순차 체이닝 (serial chaining)**
- 현재 flow-evaluator는 claim-extractor → originality-evaluator → concept-clarity-evaluator → critical-lens-evaluator를 **순차** 호출
- 각 에이전트 실행 2-4분 × 5개 = 10-20분 누적
- 축 간 의존성이 없음에도 병렬화 안 됨

**B. 과도한 scope 읽기**
- 모든 sub-evaluator가 flow.md + analyzed/ 전체 138편 + 평가 히스토리 + claim-extraction 전부 로드
- 축별로 실제 필요한 정보는 1/5 정도

**C. 단일 모델 (opus 전체 적용)**
- Axis 1(카운팅), Axis 5(정의 구조 체크) 같은 rule-based 축도 opus 사용
- sonnet/haiku로 충분한 작업에 opus = 비용·속도 모두 낭비
- 현행 모델 라우팅 원칙(PRINCIPLES.md 5a)이 **평가 에이전트에는 적용 안 됨**

**D. Delta 무시 (모든 축 매번 전량 재계산)**
- flow.md만 변경됐는데 Axis 1 재계산 (Axis 1은 flow+analyzed 의존인데 analyzed 무변경이면 스킵 가능)
- 논문만 추가됐는데 Axis 2·3 재계산 (flow.md 무변경이면 스킵 가능)
- `sync-state.json`에 hash는 있지만 **평가 캐시 무효화 로직에 쓰이지 않음**

**E. 축 간 중복 I/O**
- claim-extractor가 읽은 analyzed/*.md를 critical-lens도 다시 읽음
- 동일 파일 5회 디스크 접근

---

## 2. 개선 목표

| 지표 | 현재 | 목표 |
|------|------|------|
| 일반 재평가 소요 | 7-12분 | **2-3분** |
| 최악의 경우 (전체 재계산) | 12분+ | **5-6분** |
| 변경 없는 축 skip 가능 | ❌ | ✅ |
| 모델 비용 | 높음 (opus 전체) | **30-50% 절감** |
| 정확도 | 기준 | **유지 또는 향상** |

---

## 3. 제안 아키텍처

### 3.1 핵심 원칙

1. **Axis-level dependency graph** — 각 축이 어떤 입력에 의존하는지 명시 → 변경된 입력의 영향 받는 축만 재계산
2. **Parallel axis workers** — 축들은 서로 독립적이므로 병렬 실행
3. **Model routing per axis** — 판단력 필요한 축만 opus, 구조화된 축은 sonnet
4. **Selective scope** — 축별로 꼭 필요한 파일만 읽기
5. **Delta as default** — 기본은 변경분만, `전체 재평가` 플래그로 강제 전량

### 3.2 축 → 입력 의존성 맵

| 축 | 주요 입력 | 변경 감지 대상 |
|----|-----------|---------------|
| **1 레퍼런스** | flow.md + analyzed/*.md + consensus-results.md | flow.md 해시, analyzed count, claim-extraction MATCHED |
| **2 논리 전개** | flow.md only | flow.md 해시만 |
| **3 반박·강화** | flow.md + 3-5 "Steelman 핵심" analyzed | flow.md 해시 + Steelman tag 논문 해시 |
| **4 독창성** | flow.md + 3-5 "Delta 핵심" analyzed | flow.md 해시 + Delta tag 논문 해시 |
| **5 구성개념** | flow.md only | flow.md 해시만 |
| **6 비판적 시각** | flow.md + critical-questions.md + critical-commitments.md + 3-5 "Minority 핵심" analyzed | 4개 파일 해시 |

**Tag 시스템** (신규):
- paper-analyst가 분석할 때 각 논문에 `axis_tags: ["steelman", "delta", "minority"]` 메타 추가
- Axis-specific 에이전트는 태그로 필터링해 3-5편만 로드 (138 전체 아님)

### 3.3 새 아키텍처 다이어그램

```
사용자: "평가해줘"
    ↓
[evaluation-orchestrator] (opus, 가볍게)
    ├── 1. Delta 감지 (sync-state 해시 비교, 10초)
    ├── 2. 실행할 축 결정 (변경된 입력 → 영향 축)
    └── 3. 병렬 디스패치
            ↓
    ┌───────┬───────┬───────┬───────┬───────┬───────┐
    ↓       ↓       ↓       ↓       ↓       ↓
  [Axis1] [Axis2] [Axis3] [Axis4] [Axis5] [Axis6]
  sonnet  opus    opus    opus    sonnet  opus
  (카운팅)(판단)  (판단)  (판단)  (구조)  (깊이)
    ↓       ↓       ↓       ↓       ↓       ↓
    └───────┴───────┴───────┴───────┴───────┴───────┘
                     ↓
              [aggregator] (메인 세션, 빠름)
                     ↓
            evaluation.md 병합 + delta 계산
```

### 3.4 실행 시간 예상

**Case 1: flow.md만 변경 (이번 CDEA 시나리오)**
- Axis 1: 스킵 (analyzed 무변경) → 0초
- Axis 2·3·4·5·6 병렬 실행 → max(axis 시간) ≈ 2-3분
- **총 2-3분** (현재 10분+ 대비)

**Case 2: analyzed/ 논문 추가만 (리서치 후)**
- Axis 1만 재계산 (claim-extractor + spot check) → 1-2분
- Axis 2-6: 스킵 → 0초
- **총 1-2분** (이미 현 `레퍼런스 점검해줘`가 이걸 하지만 일반화 필요)

**Case 3: 최초 평가 or 전체 재계산**
- 6축 병렬 → 3-5분 (sonnet 축 덕분에 최장 축 = opus Axis 4 or 6)
- **총 3-5분**

---

## 4. 구현 계획

### 4.1 Phase 1: 축별 의존성 선언 (1-2일)

**파일**: `skills/agents/flow-evaluator.md` 리팩터 → `skills/agents/evaluation-orchestrator.md`

**추가 메타데이터**:
```yaml
axis_inputs:
  axis1: [flow.md, analyzed/*.md, claim-extraction.md]
  axis2: [flow.md]
  axis3: [flow.md, analyzed/*.md#steelman]
  axis4: [flow.md, analyzed/*.md#delta]
  axis5: [flow.md]
  axis6: [flow.md, critical-questions.md, critical-commitments.md, analyzed/*.md#minority]
```

**스크립트 신규**: `scripts/evaluation_delta.py`
- 입력: 프로젝트 이름
- 출력: 어느 축이 재계산 필요한지 JSON
- 로직: `.sync-state.json`의 해시 vs `evaluations/latest/.eval-cache.json`의 해시 비교

### 4.2 Phase 2: 축별 에이전트 분리 (2-3일)

**변경**: 기존 flow-evaluator의 역할을 축별 에이전트로 분산
- `skills/agents/axis1-reference-scorer.md` (model: sonnet) — claim-extraction 결과 집계만
- `skills/agents/axis2-logic-scorer.md` (model: opus) — 현 flow-evaluator Axis 2 로직
- `skills/agents/axis3-defense-scorer.md` (model: opus)
- `skills/agents/axis4-originality-scorer.md` (model: opus) — 기존 originality-evaluator 흡수
- `skills/agents/axis5-concept-scorer.md` (model: sonnet) — 기존 concept-clarity-evaluator 흡수, sonnet으로 다운그레이드
- `skills/agents/axis6-critical-scorer.md` (model: opus) — 기존 critical-lens-evaluator 흡수

**신규**: `skills/agents/evaluation-orchestrator.md`
- 역할: Delta 감지 → 병렬 디스패치 → 결과 병합
- 직접 평가 안 함

### 4.3 Phase 3: paper-analyst에 tag 추가 (1일)

paper-analyst.md 출력 스키마에 `axis_tags` 필드 추가:
```markdown
## 메타
- **axis_tags**: ["steelman", "delta"] # 이 논문이 어느 축에 유용한지
```

- "steelman": 본 thesis에 대한 강한 반론 제공 (Axis 3)
- "delta": 선행 연구와의 차별화 좌표 제공 (Axis 4)
- "minority": 소수 의견·복원 대상 (Axis 6 C-4)
- "definition": 정의·조작화 재료 (Axis 5)

기존 138편은 일괄 백필 스크립트 1회 실행.

### 4.4 Phase 4: SKILL.md 명령 라우팅 갱신 (0.5일)

- `평가해줘` → evaluation-orchestrator 호출 (delta 모드 기본)
- `평가해줘 --full` → 전체 재계산
- `평가해줘 axis3,4` → 특정 축만
- `레퍼런스 점검해줘` → 동일 시스템에서 Axis 1만 돌리는 alias

### 4.5 Phase 5: 테스트 & 캐시 검증 (1일)

- CDEA 프로젝트로 회귀 테스트
- 동일 입력 → 동일 출력 확인
- 캐시 무효화 edge case (파일 삭제, 해시 충돌 등)

---

## 5. 정확도 유지 방안

**"빠르면 부정확하지 않나?" 우려 해소**:

1. **Delta skip의 안전성**: 축이 의존하지 않는 파일 변경 시만 skip. 의존 파일 변경 시 항상 재계산. 논리적으로 동일 결과 보장.
2. **모델 라우팅의 안전성**: Axis 1·5만 sonnet 다운그레이드. 판단력 중요한 Axis 2·3·4·6은 opus 유지. Axis 1은 카운팅(규칙적), Axis 5는 정의 체크리스트(구조화)이므로 sonnet 충분.
3. **병렬화의 안전성**: 축 간 의존성 없으므로 순서 무관. 결과 병합 시 충돌 없음.
4. **축소 scope의 안전성**: Axis 3/4/6이 "핵심 논문 3-5편"만 읽어도 되는 이유는 각 축이 뽑아내야 하는 정보가 특정 논문에 집중되기 때문. 나머지 논문은 이미 Axis 1(레퍼런스)에서 커버.

**검증 방법**: Phase 5에서 기존 시스템 결과와 비교. 점수 편차 ±2점 이내면 OK, 넘으면 조사.

---

## 6. 리스크 & 트레이드오프

| 리스크 | 영향 | 완화 |
|--------|------|------|
| axis_tag 누락된 논문은 Axis 3/4/6에서 누락 | 정확도 하락 | 백필 스크립트 + paper-analyst 의무 필드화 |
| Delta 캐시 stale (해시는 같은데 내용 다름) | 드물게 잘못된 skip | 해시 + mtime 이중 체크 |
| 병렬 실행 시 Agent 도구 rate limit | 드물게 실패 | 동시성 최대 6 (현재 축 수)로 자연 제한 |
| 기존 flow-evaluator.md 참조 다른 곳 깨짐 | SKILL.md 동작 | 리팩터 시 grep으로 전 파일 스캔 + 마이그레이션 |

---

## 7. 의사결정 필요 사항

사용자 결정 요청:

1. **구현 순서**: 전체(Phase 1-5) vs 점진(Phase 1-2만 우선, 3-5는 CDEA 완료 후)?
2. **호환성**: 기존 `evaluation.md` 포맷 유지 vs 새 포맷(축별 분리)?
3. **긴급 대안**: CDEA 이번 평가에만 **임시로 단일 세션 opus가 직접 평가** (리팩터 전 우회) vs **축 4-6만 병렬 실행** (임시 병렬화)?

---

## 8. 즉시 실행 가능한 최소 조치 (오늘 내)

Phase 전체 리팩터 전, **현 CDEA 평가를 3분 내 완료**하기 위한 즉시 조치:

**옵션 A — 메인 세션(opus) 직접 평가**
- 제가(현 세션) flow.md 변경분을 이미 알고 있으므로 즉석 평가 가능
- 축 1은 84점 유지 (확정), 축 2-6만 재평가
- 결과를 evaluation.md에 쓰기
- **소요 2-3분**

**옵션 B — 4개 sonnet 병렬 (임시 라우팅)**
- Axis 2·3, Axis 4, Axis 5, Axis 6을 sonnet 에이전트 4개로 동시 실행
- 정확도는 opus보다 약간 낮음 (Axis 3·4·6 판단 품질 영향 가능)
- **소요 3-4분**

**옵션 C — 리팩터 먼저, 평가 후에**
- Phase 1-2 구현 (약 1-2일 작업)
- 이후 개선된 orchestrator로 정식 평가
- 가장 정확·빠르나 시간 투자 필요

추천: **옵션 A로 이번 CDEA 평가 완료 → 그 뒤 여유 있을 때 Phase 1-2 구현**.

---

> **Update 2026-04-23**: Phase 1-5 전부 구현 완료. 평가는 병렬 delta 아키텍처로 작동. 실측 시간: CDEA 전체 6축 재평가 ≈ 5분 (이전 12분 대비 58% 단축). 다음 병목은 **논문 분석** — 아래 2번 개선안.

---

# 논문 분석 프로세스 개선안

**작성**: 2026-04-23
**작성 맥락**: CDEA에서 `새 논문 처리해줘` 실행 시 138편 분석에 **약 60분** 소요. 10-parallel 배치 14회 × 평균 3-4분/배치. 평가보다 훨씬 큰 병목이며, 이후 프로젝트에서도 재발할 것.

---

## 1. 현재 상태 진단

### 1.1 측정된 병목

**CDEA 실측**:
| 지표 | 값 |
|------|----|
| 대상 논문 수 | 138편 |
| 모델 | sonnet (paper-analyst frontmatter) |
| 배치 크기 | 10 병렬 |
| 배치당 평균 시간 | 3-4분 (가장 느린 워커 기준) |
| 전체 배치 수 | 14회 |
| **누적 소요** | **약 60분** |
| 토큰 사용 | 약 9M (sonnet) |

### 1.2 원인 분석

**A. 모든 논문을 같은 깊이로 분석**
- `paper-analyst` Mode A가 모든 논문에 대해 동일 템플릿 실행:
  - 3줄 요약 + 핵심 기여 + 방법론 + 한계 + 관련성 점수 + 섹션별 인용 다발(5개 섹션) + 반론·대조 + 메타 + axis_tags
- 실제로는 138편 중 **주요 인용될 논문은 40-60편**. 나머지는 axis1 Coverage용 배경 자료.
- 배경 자료에 "섹션별 인용 다발" 5개 섹션을 모두 만드는 것은 **낭비**.

**B. 단일 모델 (sonnet 전체)**
- Abstract 훑고 "이 논문 쓸모 있나?" 판단하는 triage 단계도 sonnet이 수행
- haiku로 충분한 triage에 sonnet = 5-10배 낭비

**C. 배치 크기 작음 (10 parallel)**
- 각 Agent 호출은 독립적이므로 병렬도는 Claude Code 한도까지 가능
- 10 → 20-25로 늘리면 14 배치 → 6-7 배치로 감소

**D. 재분석 시 전량 스캔**
- `논문 재분석해줘`는 Mode B로 변경된 flow.md 기반 전체 재평가
- 그러나 flow.md 일부만 변경됐다면 모든 논문 재분석 불필요
- **flow.md 해시 변경 영역과 관련된 논문만** 재분석하면 됨

**E. axis_tag 부여가 post-hoc**
- 지금은 paper-analyst가 axis_tag를 부여하긴 하나, 부여 전에 이미 full Mode A 분석이 끝남
- 태그를 **먼저** 결정했다면 tag별로 다른 깊이의 분석을 했을 것

---

## 2. 개선 목표

| 지표 | 현재 | 목표 |
|------|------|------|
| 138편 일괄 처리 | ~60분 | **15-20분** |
| 우선순위 20편 고품질 | ~12분 | **7-8분** |
| 재분석 (부분 변경) | 전량 재분석 | **영향받는 논문만** |
| 토큰 비용 | ~9M (sonnet) | **3-4M** (혼합) |
| 정확도 (핵심 논문) | 기준 | **유지 또는 향상** |

---

## 3. 제안 아키텍처

### 3.1 핵심 원칙

1. **Two-pass analysis** — haiku triage → sonnet deep-dive for ≥⭐⭐⭐⭐
2. **Tier-based template** — 관련성 점수에 따라 분석 깊이 차등
3. **Progressive scope** — abstract-only → partial → full (threshold gate)
4. **Model routing per tier** — haiku(triage) / sonnet(deep) / opus(critical-only)
5. **Delta re-analysis** — flow.md 해시 변화와 관련된 논문만

### 3.2 Two-Pass 플로우

```
Pass 1 (triage, haiku, 2-5 초/편):
  입력: PDF abstract + intro 첫 문단 + flow.md 요약
  출력: {
    relevance_score: 1-5,
    primary_section: "Section N",
    axis_tags: ["steelman"|"delta"|"minority"|"definition"],
    one_line_summary: "..."
  }
  → papers/analyzed/{filename}-triage.md (경량)

Pass 2 (deep-dive, sonnet/opus, 2-4 분/편, 조건부):
  조건: Pass 1 점수 ≥ 4 또는 특정 axis_tag 보유
  입력: PDF 전체 + flow.md 전체 + paper-analyst.md 지침
  출력: 현행 Mode A 전체 분석
  → papers/analyzed/{filename}-analysis.md (v1, 기존 포맷)
```

### 3.3 Tier-based 템플릿

관련성 점수에 따라 **3등급** 분석:

| Tier | 조건 | 분석 깊이 | 모델 | 시간/편 |
|------|------|----------|------|-------|
| **Tier 1** (core) | Pass 1 점수 5, axis_tag 다수 | 현행 Mode A 전체 + Critical Reading (Mode C) | opus | 4-5분 |
| **Tier 2** (supporting) | Pass 1 점수 4 또는 axis_tag 1개 | 현행 Mode A 전체 (Mode C 제외) | sonnet | 2-3분 |
| **Tier 3** (background) | Pass 1 점수 ≤ 3, tag 없음 | **간소판**: 3줄 요약 + 섹션 1개만 인용 다발 + axis_tag | sonnet (짧은 프롬프트) | 30-60초 |

**Tier 3 간소판 포맷** (약 200 lines → 30 lines):
```markdown
# 논문 분석: {제목}
**Tier**: 3 (background)
**관련성**: ⭐⭐⭐
**axis_tags**: []

## 3줄 요약
...
## 인용 후보 (가장 관련 있는 섹션 1개만)
...
## 메타
- 저널, 인용수, 페이지
```

### 3.4 Progressive scope

하나의 Pass 2 deep-dive 내부에서도 단계적 접근:

1. **Step 1**: Abstract + Conclusion만 읽기 → 즉시 사용 가능한 인용문 3-5개 추출
2. **Step 2**: 관련성이 강하면 Methods·Results 심층 읽기 → 수치 추출
3. **Step 3**: Tier 1이면 Discussion까지 읽어 Critical Reading 추가

### 3.5 Model routing summary

| 작업 | 모델 | 이유 |
|------|------|------|
| Pass 1 triage | haiku | 짧은 abstract 기반 분류, 규칙적 |
| Pass 2 Tier 1 | opus | 핵심 논문은 판단력·hidden assumption 중요 |
| Pass 2 Tier 2 | sonnet | 구조화 분석으로 충분 |
| Pass 2 Tier 3 | sonnet (short prompt) | 간소판이지만 섹션 매핑 필요 |
| Abstract 번역 | haiku | 기존 유지 (abstract-translator) |

### 3.6 Delta 재분석

`논문 재분석해줘` 호출 시:

```bash
python3 scripts/paper_reanalysis_delta.py CDEA
```

이것이:
1. `flow.md` 해시 비교 → 변경 섹션 식별
2. 각 analyzed/*.md의 `primary_section` 확인
3. 변경 섹션을 primary로 가진 논문만 재분석 대상
4. 나머지는 skip

---

## 4. 실행 시간 예상

### Case 1: CDEA 시나리오 재현 (138편)
- Pass 1 triage (haiku 138편 × 10초, 30 parallel = 5 batch × 10초) ≈ **1분**
- Pass 2 분배:
  - Tier 1 (~15편): opus 5분/편, 5 parallel = 3 배치 × 5분 ≈ 15분
  - Tier 2 (~40편): sonnet 3분/편, 10 parallel = 4 배치 × 3분 ≈ 12분
  - Tier 3 (~83편): sonnet short 1분/편, 20 parallel = 5 배치 × 1분 ≈ 5분
- **총 30-35분** (이전 60분 대비 40-45% 단축)

### Case 2: 리서치 초기, 우선순위 20편
- Pass 1: 1분
- Tier 1-2 분배 (15편): 10-12분
- **총 11-13분** (이전 방식: 20편 × 3분 ÷ 10 parallel = 6-8분이지만 이건 이미 "10편 병렬"이 upper bound)

### Case 3: 부분 재분석 (flow.md Section 3만 변경)
- Delta 필터 → 약 30-40편
- Tier 분배 후 재분석
- **총 8-12분** (이전: 전량 60분)

---

## 5. 정확도 유지 방어

**"빠르면 부정확하지 않나?" 우려 해소**:

1. **Tier 1 핵심 논문은 오히려 더 깊게** (opus로 업그레이드 + Critical Reading). 이전은 sonnet 전부였음.
2. **Tier 3 간소판의 안전성**: 이 논문들은 axis1 Coverage 집계용 + 가끔 배경 인용. 섹션별 5개 분석이 아닌 1개로도 충분. 만약 나중에 핵심으로 격상되면 `논문 재분석해줘 {파일}` 또는 Pass 1 점수 수정 후 Pass 2 재실행.
3. **Pass 1 triage 정확도**: haiku로 "이 논문이 5점인지 3점인지"를 틀릴 가능성 → 임계 근처(3-4점)에 있으면 **높은 쪽으로 올림** (false positive 허용). Tier 2 분석 비용 증가가 Tier 3로 잘못 분류되는 것보다 훨씬 안전.
4. **Delta 재분석의 안전성**: primary_section 변경이 애매한 경우 보수적으로 재분석. flow.md 해시가 안 바뀌었으면 skip (논리적 동일).

**검증 방법**: 기존 138편 분석 중 관련성 5점으로 표기된 14편을 새 Tier 1(opus)로 재분석 → 기존 대비 ≥2 추가 인용 후보 / ≥1 Critical Reading 통찰이 나와야 함.

---

## 6. 리스크 & 트레이드오프

| 리스크 | 영향 | 완화 |
|--------|------|------|
| Pass 1 triage가 핵심 논문을 Tier 3로 잘못 분류 | 그 논문의 분석 깊이 부족 → 작성 시 다시 열어봐야 함 | 임계 근처는 높은 Tier로 올림 + `새 논문 처리해줘 --tier=1 {파일}` 수동 격상 명령 추가 |
| opus Tier 1 비용 증가 | 토큰 비용 일부 증가 | Tier 1은 15편 내외로 제한되므로 절대 비용 작음. 전체로는 sonnet 전편 대비 더 쌈 |
| 새 template 2종(Tier 3 간소판) 유지 비용 | paper-analyst.md 복잡도 증가 | 3개 섹션(Tier 1/2/3)이 명확히 분리된 단일 파일로 유지 |
| Delta 재분석 로직 버그 | 재분석 필요 논문 skip → 오래된 분석 남음 | 해시 + mtime 이중 체크 + `--full` 플래그 제공 |

---

## 7. 구현 계획

### 7.1 Phase A: paper-analyst 2-pass 구조화 (1-2일)

**변경**: `skills/agents/paper-analyst.md`를 3개 Mode로 확장
- Mode A-triage (Pass 1, haiku) — abstract + intro만 읽고 tier·tag 부여
- Mode A-tier1/2/3 (Pass 2) — tier별 템플릿 분기

**신규 스크립트**: `scripts/paper_triage.py`
- 입력: PDF 경로 + flow.md summary
- 출력: `{filename}-triage.json` (tier, tags, summary)

### 7.2 Phase B: 오케스트레이션 스크립트 (1일)

**신규**: `skills/agents/paper-processing-orchestrator.md`
- 역할: triage 일괄 실행 → tier 분배 → parallel dispatch → sync-state 갱신
- 평가-orchestrator와 구조 동일

**SKILL.md**: `"새 논문 처리해줘"` 명령 재라우팅
- 기본: 2-pass 자동
- 플래그: `--tier=1` (특정 논문만 tier1), `--skip-triage` (전부 tier1)

### 7.3 Phase C: Delta 재분석 (1일)

**신규 스크립트**: `scripts/paper_reanalysis_delta.py`
- flow.md 해시 diff → 변경 섹션 → 영향 논문 필터

**SKILL.md**: `"논문 재분석해줘"` 명령 delta 모드 기본화

### 7.4 Phase D: 기존 138편 백필 (0.5일)

기존 Mode A 분석 파일을 읽어 **Tier 분류**를 삽입:
- 관련성 점수 5 + axis_tag 2+ → Tier 1 (단, opus 재분석은 수동 트리거)
- 나머지 점수 4 → Tier 2
- 점수 ≤ 3 → Tier 3 (기존 분석 유지하되 메타에 Tier 표시)

### 7.5 Phase E: 테스트 (0.5일)

- 기존 CDEA 138편으로 회귀 테스트
- 새 프로젝트에 20편 가상 입력 → Case 2 시나리오 검증

**총 예상**: **4-5일** (평가 리팩터와 유사 규모)

---

## 8. 의사결정 필요 사항

1. **구현 시점**: 지금 (CDEA 초안 작성 전) vs 나중 (CDEA 완료 후)?
2. **Tier 1 모델**: opus vs sonnet 유지?
   - opus: 핵심 논문 품질 최상, 비용 약간 증가
   - sonnet: 비용 동일, Critical Reading 품질 일부 저하
3. **Tier 3 간소판 scope**: 현재 5개 섹션 인용 다발 → **Tier 3는 1개만** OK? 아니면 2-3개?

---

## 9. 즉시 적용 가능한 최소 조치

Phase A-E 전면 리팩터 전, **기존 시스템에 적용 가능한 단순 개선 3가지**:

**옵션 A — 배치 크기 확대 (0분, 즉시)**
- 현재 10 parallel → 20-25 parallel
- 정확도 영향 없음, 시간 절반
- **다음 `새 논문 처리해줘` 실행 시 즉시 적용**

**옵션 B — 수동 tier 플래그 (1시간)**
- SKILL.md에 `새 논문 처리해줘 --priority` 추가
- 우선순위 지정 논문만 Mode A, 나머지 skip (또는 triage만)
- paper-analyst.md 작은 수정으로 끝

**옵션 C — Abstract-first 간소판 (2시간)**
- paper-analyst에 "abstract-only" 모드 추가
- 사용자가 `가볍게 처리해줘` 명시하면 이 모드로

추천: 당장은 **A (배치 확대)** + **C (가벼운 모드)** 만 추가하고, 전면 리팩터는 CDEA 초안 완료 후 진행.

