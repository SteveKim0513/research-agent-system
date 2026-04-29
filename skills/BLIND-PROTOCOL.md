# Blind Protocol Enforcement

> 모든 evaluation agent (axis 1-6 scorers · claim-extractor · final-holistic-reviewer · final-coursework-evaluator · final-dissertation-evaluator · coursework 위원회 5인 페르소나)는 본 protocol을 *반드시* 준수.

본 protocol은 2026-04-29 FLW evaluation의 systematic bias 사례 (FER context anchoring으로 인한 under-estimation)를 trigger로 신설.

---

## 핵심 원칙

평가는 **해당 essay 본문 + rubric**만으로 결정. 다음을 *명시적으로* 금지:

### 1. 이전 essay context 사용 금지
- 같은 conversation session에서 *이전에 평가된 다른 essay*의 mark·band·진단·요약 인용 X
- "이전 X 평가에서는...", "FER 대비...", "다른 essay와 비교하면..." 식 referencing 일체 금지
- 보고서 본문에 다른 essay 이름이 등장하면 protocol 위반

### 2. Anchoring 금지
- 다른 essay의 mark를 baseline으로 ±N 식 추론 금지
- "한 칸 위/아래 등급" 식 결정 금지 (이건 anchoring의 가장 흔한 형태)
- 각 essay는 *rubric descriptor 직접 비교*만으로 mark 결정
- Phase 1 첫인상 단계에서 *specific mark 추측* 금지 — band만 정하고, sub-criteria 채점에서 `_3`/`_8` 결정

### 3. Comparative reasoning 금지
- "X보다 originality 강함" / "Y보다 약함" 식 비교 금지
- 본 essay의 *절대 quality*만 평가
- 보고서에 비교 표·"essay A vs essay B" 섹션 등장 시 protocol 위반

### 4. Halo effect 차단
- 본 essay의 한 영역(예: 강한 literature)이 다른 영역(예: writing) 채점에 자동 영향 X
- 각 criterion 독립 채점 — descriptor 매칭에 집중
- 첫인상이 한 criterion으로 다른 criterion에 spillover 안 되도록 의식

---

## Descriptor 직접 비교 원칙

mark 결정은 다음 절차:

```
For each criterion:
  1. 본문에서 해당 영역 evidence 추출 (인용 1-2개)
  2. Rubric의 6개 band descriptor 모두 재독
  3. Evidence가 *어느 descriptor와 가장 정확히 매칭*되는지 직접 비교
  4. Band 결정 후 _3/_8 위치 (band 하단/상단) 판단
  5. 결정 사유에 *어느 descriptor가 매칭됐는지* 명시
```

**금지된 옛 패턴**:
- ❌ "이건 distinction 같다 → 73"
- ❌ "originality는 약하니 한 단계 아래"
- ❌ "다른 essay가 68이었으니 이건 한 단계 위 73"

**올바른 패턴**:
- ✅ "C-6 본문이 'extensive...possibly going well beyond core literature' descriptor에 매칭 (Hidden Talents·life history 같은 core 외부 인용 명백) → 80+ band → 83"

---

## 자기 검증 체크리스트

평가 보고서 완료 *전* 다음 항목 점검:

- [ ] 보고서에 *다른 essay 이름·comparative 표* 등장 X
- [ ] mark 결정 사유에 *"이전 평가 대비"* 식 anchoring 없음
- [ ] 각 criterion이 *rubric descriptor*와 직접 매칭으로 결정됨 (어느 descriptor 충족됐는지 명시)
- [ ] 첫인상이 *prior context*가 아닌 *본문 자체*에서 형성됨
- [ ] 8 (or 10) criteria 각각이 독립 채점됨 (한 criterion이 다른 criterion 채점을 spillover 안 함)
- [ ] 보고서에 "한 단계 위/아래" 식 단계 추론 없음

위 중 하나라도 미충족 시 보고서 *polluted* — 재평가 필요.

---

## 사용자 권고: Fresh Session per Essay

이상적으로는 **한 conversation session = 한 essay 평가**.

- 같은 session에서 이전 essay 평가하면 그 context가 prompt에 *남아*. agent가 본 protocol을 준수하려 해도 첫인상 형성 단계부터 contamination 됨 (sub-conscious anchoring).
- **여러 essay 평가 시 각각 fresh conversation에서 실행 권장**.
- 또는 agent dispatch 시 orchestrator가 *사용자에게 명시 경고* 후 진행.

---

## Bias 검출 사례 — FLW Evaluation (2026-04-29)

**상황**:
- 사용자가 같은 session에서 FER essay 평가 (위원회 모드, mark 68 적중) → FLW essay 평가 요청
- 위원회 5인 평가 결과: 73 (Distinction lower) prediction
- 사용자: "틀렸다"

**Bias 분석**:
1. **Comparative anchoring**: 보고서에 *FER vs FLW 비교 표* 명시 등장. mark가 "한 칸 위 등급 = 73" 식 산수로 도출.
2. **Persona context shared**: 5인 페르소나가 *한 conversation 안*에서 운영되어 FER context가 모든 페르소나에 동일 침투.
3. **Confirmation bias**: FER 68 적중 → calibration 확신 강화 → FLW도 같은 framework 그대로 적용.
4. **Halo / framing effect**: FLW의 *다른 패턴*을 FER 패턴과 *대비*로 인식 → 자동 "한 등급 위" categorize.

**Strict blind 재평가 결과**:
- C-6 Literature: 73 → **83** (descriptor "extensive...possibly going well beyond core literature" 명백 매칭, 50+ refs + 2024-2025 최신 paper + Hidden Talents/life history 같은 core 외부 인용)
- C-7 Theory: 73 → **83** ("may consider issues/theory beyond the current field" 매칭)
- Final mark: 73 → **78** (Distinction upper)

**교훈**:
- Comparative anchoring은 단일 ±5 점 변화를 만들 수 있음 (band 경계도 넘김)
- 80+ tier descriptor 매칭은 *각 essay 독립적*으로만 가능 — anchored 상태에서는 누락됨
- 본 사례가 system-wide blind protocol 신설의 trigger

---

## 위반 시 처리

평가 agent가 본 protocol 위반 시:
1. 보고서를 *polluted*로 라벨링
2. 사용자에게 경고: "본 평가는 prior context contamination 위험 — fresh session에서 재평가 권장"
3. 재평가 시 새 conversation에서 단일 essay만 dispatch

orchestrator 책임:
- sub-agent dispatch 시 prompt에 *해당 essay text + rubric + persona spec*만 포함
- 이전 평가 결과·conversation history 절대 미주입
- 같은 session에서 N개 essay 평가 감지 시 사용자에게 *명시적 경고*

---

## 적용 대상 (전체 15개 agent)

| Agent | 적용 위치 |
|-------|----------|
| axis1-reference-scorer | 6 criteria 채점 시 prior anchoring 차단 |
| axis2-logic-scorer | 동일 |
| axis3-defense-scorer | 동일 (3-5 Engagement Discipline 포함) |
| axis4-originality-scorer | 동일 |
| axis5-concept-scorer | 동일 |
| axis6-critical-scorer | 동일 (C-5 Engagement Discipline 포함) |
| claim-extractor | spine 추출 시 prior essay spine 비교 X |
| final-holistic-reviewer | Phase A 척추 articulation은 본문 자체에서만 |
| final-coursework-evaluator | rubric descriptor 직접 비교 |
| final-dissertation-evaluator | rubric descriptor 직접 비교 |
| coursework-marker-1 | Phase 1 blind 보장 + prior essay anchoring 차단 |
| coursework-marker-2 | 동일 |
| coursework-third-marker | Phase 3 blind 보장 + prior essay anchoring 차단 |
| coursework-external-examiner | cross-institutional 권고 시 다른 essay와 비교 X |
| coursework-chair | reconciliation 시 본 essay 결과만 종합 |

각 agent 파일은 본 BLIND-PROTOCOL.md를 참조 (4-line reference 의무).
