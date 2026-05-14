# 방법론 B 전환 계획서

> **작성일**: 2026-05-10
> **목적**: 7개 패턴 정당화 논리를 "패턴별 학술 인용"에서 "4기준 선정 방법론(4C-PPS)"으로 전환
> **승인 필요**: 본 계획서 검토 후 진행 여부 확정

---

## 0. 전환 배경 (Why)

### 현재 방식의 문제
- 6개 패턴 = 6개 다른 논문 인용 → 짜맞춘 인상
- 각 인용 검증 시 신뢰 하락 위험 (예: NCF가 genre_preference를 정의하지 않음)
- "5차원 분해" 표현도 사실상 본 연구자의 사후 정리 (학술 출처 없음)

### 전환 방향
- **이론 anchor 1개**(Thet et al. 2010 + Liu 2012)로 압축
- 7개 패턴은 **4기준 방법론(4C-PPS)의 적용 결과**로 위치
- 본 연구의 contribution을 "패턴 7개"가 아닌 "**선정 방법론**"으로 격상

---

## 1. 작업 항목 4개 (요약)

| # | 작업 | 파일 경로 | 액션 |
|:---:|---|---|---|
| 1 | 정의서 재작성 | `prompts/core_patterns_definition.md` | 덮어쓰기 (기존 백업) |
| 2 | Pilot Report MD 정비 | `docs/Pilot_Study_Report.md` | 덮어쓰기 (기존 백업) |
| 3 | 실험계획서에 Ablation 섹션 추가 | `experiment_plan.md` | 섹션 추가 (기존 유지) |
| 4 | Pilot Report PDF **신규 생성** | `docs/TransferJudge_Pilot_Report_v2.pdf` | **신규 파일** (기존 PDF 보존) |

---

## 2. 작업 순서 및 의존성

```
[Task 1: 정의서 재작성] (foundation)
        ↓
[Task 2: Pilot Report MD 정비] (정의서 변화 반영)
        ↓
[Task 3: 실험계획서 Ablation 추가] (독립적, 병렬 가능)
        ↓
[Task 4: 신규 PDF 생성] (Task 1~3 결과 종합)
```

**순서 이유**:
- Task 1이 모든 후속 작업의 기준점이 됨
- Task 2는 Task 1의 정의서를 참조해야 함
- Task 3은 독립적이지만 Task 4 이전에 완료되어야 PDF에 반영 가능
- Task 4는 위 셋의 결과를 시각적으로 종합

---

## 3. Task별 상세 계획

### Task 1 — 정의서 재작성

**파일**: `prompts/core_patterns_definition.md`

**변경 내용**:
| 섹션 | 현재 | 변경 후 |
|---|---|---|
| 0. 한눈에 표 | 패턴마다 개별 인용 | 4기준 평가표 + Transfer Gate 라벨 |
| 1~7. 각 패턴 정의서 | 패턴별 학술 근거 + 변형 발현 가설 | **국문/영문 정의 + Pilot 매칭 결과 + Cross-Domain 라벨**로 단순화 |
| 8. 직교성 사전 진단 | (유지) | (유지) |
| 9. CDR 적용 가이드 | (유지) | (유지, 표현 정리) |
| 10. 사전 등록 가설 | H1~H5 (유지) | H1~H5 (방법론 검증 가설로 재해석) |
| 11. 학술적 위치 | 패턴별 ★ | **4C-PPS 방법론 정의** + Thet 2010 anchor |
| **신규** §12 | 없음 | **4C-PPS 방법론 절차 정식 기술** |

**핵심 변경**:
- 전체 인용 6개 → **2개로 압축**: Liu (2012) + Thet et al. (2010)
- 추가 인용 (선택): Pontiki et al. (2016) SemEval, Fernández-Tobías et al. (2012) CDR survey
- "차용" 표현 제거 → "방법론 적용 결과" 표현
- ★ 자기평가 제거 → 4기준 ○/△/✗ 로 대체

**예상 분량**: 기존 360줄 → 약 250~300줄 (간결화)

**백업**: `prompts/core_patterns_definition_v1_backup.md`로 보존

---

### Task 2 — Pilot Report MD 정비

**파일**: `docs/Pilot_Study_Report.md`

**변경 내용**:
| 섹션 | 현재 | 변경 후 |
|---|---|---|
| 0. 한 줄 요약 | "차용 6개 + 도출 1개" | "**4C-PPS 방법론 적용 결과 7개 채택**" |
| 1. Overview | Pilot 100명 + 자기참조 회피 | + **방법론 contribution 명시** |
| 2. 데이터 및 절차 | (유지) | (유지) |
| 3. 7개 패턴 | 패턴별 학술 인용 | **4기준 평가 결과 표**로 대체 |
| 4. 결과 | (유지) | (유지, 4기준 강조) |
| 5. H1~H5 | (유지) | "방법론 검증 가설"로 명시 |
| 6. 결정표 | (유지) | (유지) |
| 7. 결론 | "외부 학술 + Pilot 도출" | "**4C-PPS 방법론 + 본 도메인 적용 결과**" |

**핵심 변경**:
- "외부 학술 표준 6개" 표현 제거
- "Pilot 도출 1개" 표현 유지 (emotional_resonance만)
- 결론 표현 통째로 교체
- 부록 A/B는 유지

**백업**: `docs/Pilot_Study_Report_v1_backup.md`로 보존

---

### Task 3 — 실험계획서에 Ablation 섹션 추가

**파일**: `experiment_plan.md`

**변경 방식**: **추가만** (기존 내용 유지)

**추가 위치**: Section 5 (평가) 다음 또는 Section 6 신설

**신규 섹션 내용**:
```
## 6. Ablation Study (방법론 효과 검증)

### 6.1 Transfer Gate Ablation
- 비교 1: 7개 모두 transfer (Gate OFF) vs Gate ON
- 측정: NDCG@10, HR@10, MRR
- 가설: Gate ON > Gate OFF (BLOCK 후보 차단 효과)

### 6.2 Per-Pattern Contribution
- 각 패턴 1개씩 제거 시 성능 변화
- 측정: 각 패턴의 marginal contribution
- 시각화: 7×3 (NDCG/HR/MRR) heatmap

### 6.3 Cold-Start Segment 분석
- Books 도메인 n_review ≤ 3 사용자만 분리
- baseline 대비 본 연구의 우위 검증

### 6.4 Methodology 일반화 (선택)
- (가능하다면) 다른 도메인 쌍에서 4C-PPS 적용 결과 보고
```

**예상 분량**: 약 50~80줄 추가

**백업**: 불필요 (추가만 함)

---

### Task 4 — Pilot Report PDF **신규 생성**

**신규 파일**: `docs/TransferJudge_Pilot_Report_v2.pdf`

**기존 파일 보존**: `docs/TransferJudge_Pilot_Report.pdf` ← 그대로 둠

**스크립트**: `scripts/generate_pilot_report_v2.py` (기존 generate_pilot_report.py 복제 + 수정)

**변경 핵심**: 
- "본인 검토용"으로 **각 섹션마다 "쉬운 설명" 콜아웃 박스** 추가
- Methodology B 기반 narrative 전면 재구성
- 기존 PNG 3개 + 신규 인포그래픽 4개 재사용 + **방법론 다이어그램 1개 추가**

**섹션 구성**:
| # | 섹션 | 시각 요소 | 쉬운 설명 콜아웃 |
|:---:|---|---|---|
| 1 | 한 줄 요약 + 메타정보 | (기존) | "이 보고서가 답하려는 질문" |
| 2 | 핵심 메커니즘 — 자기참조 회피 | 분리 다이어그램 | "왜 자기참조가 문제이고, 어떻게 피했는가" |
| 3 | **신규: 4C-PPS 방법론 정의** | **신규 다이어그램** | "이 방법론이 무엇을 하는가, 4기준이 왜 중요한가" |
| 4 | 5단계 작업 흐름 | (기존) | "각 단계가 무엇을 산출했는가" |
| 5 | 7개 패턴 (방법론 적용 결과) | 카드 그리드 (★ 제거) | "이 7개가 어떻게 4기준을 통과했는가" |
| 6 | Step 2 매칭 결과 | (기존) | "임베딩 매칭이 무엇을 입증했는가" |
| 7 | Step 3 자유 추출 한계 | Pareto chart | "왜 자유 추출만으론 부족한가 (90.8%)" |
| 8 | Step 4 직교성 + Movies-only | Heatmap | "왜 7개가 서로 겹치지 않아야 하는가" |
| 9 | H1~H5 검증 | 5 카드 ✅ | "사전 등록 가설이 모두 통과한 의미" |
| 10 | 채택 결정표 | 4기준 표 | "각 패턴이 어떤 라벨을 받았는가" |
| 11 | 결론 — 방법론 contribution | 콜아웃 박스 | "본 연구가 학계에 기여하는 것" |
| 12 | 한계 + 향후 작업 | (기존) | "솔직히 인정하는 약점들" |

**예상 분량**: 12~14페이지 (기존 10페이지보다 약간 증가)

**디자인**: 기존 EDA 스타일 유지 + **"💡 쉬운 설명"** 콜아웃 박스 추가

---

## 4. 핵심 변경 표현 요약

### Before → After 표현 매핑

| Before | After |
|---|---|
| "외부 학술 분야에서 차용된 6개" | "4C-PPS 방법론을 본 도메인에 적용한 결과 7개" |
| "패턴마다 학술 출처" (6개 인용) | "Thet et al. (2010) + Liu (2012) anchor 1~2개" |
| "5차원 분해 (WHAT/HOW/...)" | (제거) — 4기준 검증으로 대체 |
| "★ 자기평가 인용 강도" | "4기준 ○/△/✗ 평가" |
| "본 연구의 7개 = 차용 6 + Pilot 1" | "본 연구의 contribution = 방법론 + 적용 사례" |
| "자기참조 회피" (정의 vs 검증 분리) | (유지) — 여전히 강력한 논리 |

### 인용 압축 결과
| 인용 | Before | After |
|---|:---:|:---:|
| NCF (He 2017) | ✓ | (선택, 일반 추천 배경에서만) |
| LLM4CDR (2025) | ✓ | (선택) |
| TALLRec (2023) | ✓ | (선택) |
| Ricci RS Handbook (2015) | ✓ | (선택) |
| Oliver (1999) | ✓ | ✗ 제거 |
| **Thet et al. (2010)** | ✗ | **✓ 메인 anchor** |
| **Liu (2012)** | ✗ | **✓ 메인 anchor** |
| Pontiki et al. (2016) | ✗ | (선택, ABSA 보강) |
| Fernández-Tobías et al. (2012) | ✗ | (선택, CDR 배경) |

---

## 5. 작업 산출물 체크리스트

### Task 1 완료 기준
- [ ] `core_patterns_definition.md` 재작성 완료
- [ ] 백업 파일 존재 (`_v1_backup.md`)
- [ ] 인용 수 6개 → 2개 (필수)
- [ ] §12 4C-PPS 방법론 절차 신규 추가
- [ ] 7개 패턴 정의 일관성 유지

### Task 2 완료 기준
- [ ] `Pilot_Study_Report.md` 정비 완료
- [ ] 백업 파일 존재
- [ ] "방법론 contribution" 표현 일관 적용
- [ ] H1~H5가 "방법론 검증 가설"로 명시

### Task 3 완료 기준
- [ ] `experiment_plan.md`에 §6 Ablation Study 추가
- [ ] 4개 하위 섹션 모두 작성 (6.1~6.4)
- [ ] 기존 섹션 변경 없음

### Task 4 완료 기준
- [ ] `generate_pilot_report_v2.py` 스크립트 신규 생성
- [ ] `TransferJudge_Pilot_Report_v2.pdf` 신규 파일 생성
- [ ] 기존 PDF 보존 확인
- [ ] 각 섹션에 "💡 쉬운 설명" 콜아웃 박스 포함
- [ ] 신규 4C-PPS 방법론 다이어그램 포함
- [ ] 12~14페이지 분량

---

## 6. 예상 소요 시간 및 리스크

| Task | 예상 시간 | 리스크 |
|:---:|:---:|---|
| 1 | 30분 | 정의서 일관성 유지 (7개 패턴 정의는 모두 다시 검토) |
| 2 | 15분 | MD → PDF 표현 정합성 (Task 4와 연동) |
| 3 | 15분 | Ablation 4개 하위 섹션의 구체성 |
| 4 | 45분 | PDF 생성 시 폰트·인포그래픽 렌더링 검증 |
| **총** | **약 1.5~2시간** | — |

---

## 7. 승인 요청

본 계획서를 검토 후 다음 중 선택해주세요:

- **A. 전체 승인** → 4개 작업 순차 진행
- **B. 부분 승인** → 어떤 작업부터 진행할지 지정 (예: "Task 1만 먼저")
- **C. 수정 요청** → 변경할 부분 지정 후 재계획
- **D. 보류** → 다른 작업 우선 진행

---

## 부록 A — Thet et al. (2010) 인용 정합성 사전 검증

**선행연구**: Thet, T. T., Na, J. C., & Khoo, C. S. G. (2010). Aspect-based sentiment analysis of movie reviews on discussion boards. *Journal of Information Science*, 36(6), 823-848.

**왜 이 논문이 anchor로 적합한가**:
- 영화 리뷰를 aspect 단위로 분해한 **표준 선행연구**
- aspect 분류를 명시적으로 제시
- 본 연구의 7개 패턴과 자연스러운 mapping 가능

**Mapping 예시** (Task 1에서 정식 작성):
| Thet 2010 영화 aspect (참고) | 본 연구 패턴 |
|---|---|
| Story (storyline, characters, screenplay) | narrative_complexity, pacing_preference |
| Crew (acting, direction) | quality_sensitivity, brand_loyalty |
| Production (scene, music) | sensory_preference |
| (확장 — Pilot 도출) | emotional_resonance |
| (확장 — 추천시스템 표준) | genre_preference |

**솔직한 표현**: "Thet et al. (2010)이 영화 aspect 분해를 제시하였고, 본 연구는 이를 (a) 사용자 선호 추출로 목적 변환, (b) Cross-Domain 전이 가능성으로 분류 확장하였다."

---

## 부록 B — 변경 이후 가능한 후속 작업 (참고용)

본 계획 완료 후 자연스럽게 이어질 수 있는 작업:

1. **Phase 6 (기존 pending)**: Profiler/Teacher 프롬프트·스크립트 동기화
2. **Overview PDF v6**: 방법론 contribution 반영
3. **논문 본문 §3 (Methodology)**: 4C-PPS 정식 기술

이들은 본 계획 범위 외이며, 별도 승인 후 진행.
