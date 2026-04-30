# GAP-REPORT-FORMAT.md — gap-report.md 포맷 규율

> 이 문서는 `research-gap/gap-report.md`의 **엄격한 포맷 스펙**입니다. `gap-synthesizer` 에이전트가 이 파일에 출력합니다.
>
> 목적: research-gap 단계에서 분석한 모든 [R][D] 논문을 한 곳에서 비교하고, 어디에 리서치 갭이 있는지 한눈에 보이게 만든다.

---

## 1. 파일 전체 구조

```markdown
# Gap Report — {프로젝트명}

> 생성일: YYYY-MM-DD HH:MM
> 분석 논문 수: N편 (분석 완료 [R][D]: M편 / 등록 대기 [R]: K편)
> 가설 수: H-01 ~ H-NN (N개)
> 기반 자료: research-gap/research-gap.md, research-plan.md, papers/analyzed/research-gap/*.md

---

## 1. 가설별 Anchor 매트릭스
{가설 × 논문 — 어느 H에 어떤 anchor 후보가 있는지}

## 2. 논문 비교 표 (갭 발견 핵심)
{모든 [R][D] 논문의 정량 frame을 한 표에}

## 3. 분포 분석 — 어디가 비어 있는가
### 3.1 연령 분포
### 3.2 문화권·표본 분포
### 3.3 측정 도구 분포
### 3.4 종속 변수 분포
### 3.5 통제 변인·연구 디자인 분포

## 4. 식별된 갭 (가설별)
{각 H에 대해 발견된 anchor의 한계 + 발견된 갭}

## 5. 본인 thesis 진행 시 활용 권고

## 6. 추가 anchor 검색 권고
```

---

## 2. 섹션별 상세 포맷

### 2.1 가설별 Anchor 매트릭스

논문이 어느 H에 어떤 역할로 anchor가 되는지 표로:

```markdown
## 1. 가설별 Anchor 매트릭스

|  | H-01 | H-02 | H-03 | H-04 | H-05 |
|---|---|---|---|---|---|
| Kroupin 2025 | direct | — | — | — | — |
| Doebel 2020 | counter | — | — | — | — |
| Miyake 2000 | foundational | methodology | — | — | — |
| Author Year | — | — | direct | counter | — |

**역할 (cell value)**:
- `direct` — 해당 H를 직접 다룬 anchor
- `counter` — H에 반대되는 입장의 anchor
- `foundational` — H의 전제가 되는 seminal 연구
- `methodology` — H를 다룰 때 방법론 참고
- `tangent` — 부분적으로 관련 (보조 인용)
- `—` — 무관
```

### 2.2 논문 비교 표

```markdown
## 2. 논문 비교 표 (갭 발견 핵심)

| Author Year | 핵심 주장 (1줄) | 대상 연령 | 표본 (N, 특성) | 통제 변인 | 독립 변수 | 종속 변수 | 측정 도구 | 분석 방법 | 저자 명시 한계 |
|---|---|---|---|---|---|---|---|---|---|
| Kroupin 2025 | EF는 보편/특수 둘 중 하나 | — | — (theoretical) | — | — | — | — | conceptual | 경험 데이터 부재 |
| Doebel 2020 | EF는 상황가변 skill | — | — (theoretical) | — | — | — | — | conceptual | 측정 어려움 |
| Friedman 2017 | unity/diversity model | 청년 (18–25) | N=582, US WEIRD | gender, IQ | task type | latent EF | 9 EF tasks | SEM | 횡문화 미점검 |

> 줄이 너무 길면 원본 [R][D].Author_Year.md 참조하도록 footnote.
```

### 2.3 분포 분석

각 분포는 **구간별 카운트** + **비어 있는 구간** 명시:

```markdown
### 3.1 연령 분포
- 영아 (0–2세): 0편
- 미취학 (3–5세): 3편 (Hongwanishkul 2005, Kochanska 2010, ...)
- 학령기 (6–12세): 12편
- 청소년 (13–17세): 2편
- 청년 (18–25세): 8편
- 중장년 (26–60세): 1편
- 노년 (60+): 0편
- 횡-연령 (life-span): 1편

⚠️ **갭**: 영아·노년·중장년 anchor 부재. 학령기-청년에 편중.

### 3.2 문화권·표본 분포
- WEIRD only: 18편
- 비-WEIRD 단독: 2편 (Bansal 2023 인도, Kroupin 2024 사하라 이남)
- 횡문화 비교: 3편

⚠️ **갭**: 비-WEIRD anchor 5편으로 부족. 본인 thesis가 횡문화 일반화 의존하면 추가 검색 필요.

### 3.3 측정 도구 분포
- Stroop 단독: 4편
- DCCS 단독: 3편
- 다중 task battery: 8편
- Hot EF 과제 포함: 5편
- Pretend play 관찰: 2편
- Ecological 측정 (실생활): 1편

⚠️ **갭**: ecological measurement 부재. 본인 4분면 이론은 자연 환경 적용 가능성을 주장하므로 ecological 측정 anchor 추가 권고.

### 3.4 종속 변수 분포
{같은 패턴}

### 3.5 통제 변인·연구 디자인 분포
- Cross-sectional: 15편
- Longitudinal: 4편
- Experimental: 3편
- Meta-analysis: 2편
- Theoretical: 4편

{각 디자인의 분포 + 갭 명시}
```

### 2.4 식별된 갭

가설 단위로:

```markdown
## 4. 식별된 갭

### 갭 #1: H-01 (보편/특수 논쟁) — 비-WEIRD 표본 부재
- **현재 anchor 한계**: Kroupin 2025·Doebel 2020 등 *이론적* 논의가 우세. 실증은 대부분 WEIRD.
- **부재 영역**: 비-WEIRD 표본에서 동일 EF task의 latent structure를 검증한 연구
- **본인 thesis와의 관계**: 4분면 이론이 횡문화 일반화 가능성을 강조하므로 이 갭은 결정적
- **추천 후속**: H-01-supp 검색 키워드 — `executive function non-WEIRD samples factor structure`

### 갭 #2: H-04 (자발성·임의성) — 직접 연결 anchor 부재
- **현재 anchor**: SDT 계열 (Ryan & Deci) + pretend play 계열 (Lillard 2013) 분리되어 있음. EF와의 직접 통합 anchor 부재.
- **부재 영역**: 자발성/임의성 dimension에 따라 EF 수행 차이를 검증한 실증 연구
- **본인 thesis와의 관계**: 본 thesis의 핵심 차원이므로 갭이 곧 contribution 기회. 단 *방어 가능한 1차 anchor* 부재가 약점.
- **추천 후속**: 인접 분야 (motivation × cognitive control intersect) 추가 검색

### 갭 #N: ...
```

### 2.5 본인 thesis 진행 시 활용 권고

```markdown
## 5. 본인 thesis 진행 시 활용 권고

### 5.1 이미 강한 anchor (flow.md 작성 시 직접 인용 가능)
- H-01: Kroupin 2025 (direct), Doebel 2020 (counter), Miyake 2000 (foundational)
- H-02: Karr 2018 review, Friedman 2021 unity/diversity
- ...

### 5.2 약한 영역 (현재 자료로 강한 주장 어려움 — hedge 필요)
- H-04 (자발성·임의성 구분의 EF 적용) — 직접 anchor 부재. 본인 contribution으로 강조 가능하나, *defensible*하려면 인접 분야 인용으로 logic chain 보강 필요.

### 5.3 본인 contribution으로 강조 가능한 갭
- **갭 #1 (비-WEIRD 표본)**: thesis 도입에서 분야 한계로 명시 → 4분면 이론이 이 갭을 채운다는 positioning
- **갭 #2 (자발성·임의성 통합)**: 핵심 contribution. 단 방어 anchor 1편 이상 추가 권고.
```

### 2.6 추가 anchor 검색 권고

```markdown
## 6. 추가 anchor 검색 권고

다음 H 또는 갭에 대해 추가 검색을 권고:

| 검색 ID | 대상 갭 | 검색 쿼리 | 기대 논문 프로필 |
|---|---|---|---|
| H-01-supp | 갭 #1 | `executive function non-WEIRD samples factor structure invariance` | 횡문화 invariance 검증 / 비교문화 EF measurement |
| H-04-supp | 갭 #2 | `self-determination motivation cognitive control children` | SDT × EF intersect / 자기 선택 vs 외부 부과 EF |

→ `"리서치 갭 분석해줘"` 다시 실행하면 위 검색이 research-plan.md에 자동 추가됨.
```

---

## 3. 작성 원칙

1. **갭 frame 일관성** — 매 섹션이 "어디에 anchor가 있고 어디에 없는가"에 답해야 함. anchor 나열만 하면 무의미.
2. **본인 thesis 연결 명시** — 식별된 갭이 본인 thesis 진행에 결정적인지 부수적인지 항상 명시.
3. **defensibility 평가 포함** — 약한 영역은 hedge 권고. 강한 영역은 자신감 있게 인용 가능 표시.
4. **추가 검색 actionable** — 갭 식별만으로 끝나지 않고 후속 검색 쿼리까지 제시.

---

## 4. 갱신 정책

`gap-report.md`는 매 `"갭 리포트 만들어줘"` 호출 시 **전체 재생성**. 이전 리포트는 `history/gap-report/{NNN}-{date}.md`에 스냅샷.

새 [R][D] 논문이 추가되거나 기존 [R][D] 분석이 갱신되면 리포트 재생성 권고. 사용자가 `"갭 리포트 다시 만들어줘"`로 명시 호출.
