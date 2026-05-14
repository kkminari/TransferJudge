# TransferJudge Pilot Study 실행 계획서

> **목적**: Profiler가 추출하는 Core Pattern 6개를 데이터로부터 도출·검증하여 본 연구 설계의 학술적 정당성 확보
> **상위 문서**: [`experiment_plan.md`](../experiment_plan.md) §4 Pilot Study
> **작성일**: 2026-04-26
> **예상 총 시간**: 6~7시간 (분산 가능, Phase 3 정규화가 가장 큼)
> **예상 비용**: ~$0.2 (GPT-4o-mini API)

---

## 0. 사전 결정 사항 (확정)

| 항목 | 결정 | 근거 |
|------|------|------|
| **Q1. 패턴 도출 방식** | **하이브리드** — 데이터 기반 도출 후 현재 6개와 매칭 | 학술적 정당성 + 안전성 균형 |
| **Q2. LLM 모델** | **GPT-4o-mini** | 본 실험과 일관성, 비용 효율 |
| **Q3. 정규화 방법** | **임베딩 클러스터링 + 수동 검토** | 자동화로 시간 절약 + 품질 검증 |
| **Q4. Pilot 샘플 크기** | **100명** | 빈도 순위 안정성 최소 규모 |
| **Q5. 결과 활용 시나리오** | **데이터 기반 결과를 따름** | 데이터 다르게 나오면 Profiler/Teacher 재작성 |

---

## 1. 성공 조건 (Definition of Done)

Pilot Study가 다음을 모두 충족하면 성공:

- [ ] **명확한 패턴 도출**: 100명에서 일관되게 등장하는 패턴 5~8개 식별
- [ ] **Top-N elbow point**: 상위 N개 이후 빈도 급감(50% 이상 하락)이 그래프상 시각적으로 확인됨
- [ ] **직교성**: 최종 N개 패턴 간 의미적 cosine similarity ≤ 0.7 (중복 미만)
- [ ] **도메인 보편성**: 각 패턴이 Movies/Books 양쪽에 의미 있음을 검증
- [ ] **현재 6개와의 일치율 정량화**: 일치 / 부분 일치 / 신규 도출 패턴 분류 완료
- [ ] **Profiler 정의서 산출**: 최종 N개 패턴의 영문/국문 정의 + 예시 + 토큰 추정 작성
- [ ] **계획서·PDF 동기화**: experiment_plan.md §4, Overview_v5 PDF §6 반영 완료

---

## 2. Phase 1 — 준비 (목표 30분)

### 2.1 목표
샘플링·프롬프트·스키마를 모두 준비하여 즉시 LLM 실행 가능 상태로 만들기.

### 2.2 체크리스트

#### 2.2.1 100명 샘플링

- [ ] 새 스크립트 `scripts/pilot_sample.py` 작성
- [ ] Train 800명 中 100명 무작위 샘플링 (numpy seed=42)
- [ ] 산출: `data/pilot_users.parquet` (100 rows: user_id + 리뷰 수)
- [ ] 검증: Source 리뷰 수 분포가 전체 1,000명과 유사한지 (mean·median ±5% 이내)

#### 2.2.2 비구조화 프롬프트 설계

- [ ] 새 파일 `prompts/pilot_profiler_prompt.md` 작성
- [ ] **핵심 규칙**: Core Pattern 6개 사전 정보 미제공 (편향 방지)
- [ ] System Prompt 골격:
  ```
  You are an expert user preference analyst.
  Read the user's Movies & TV reviews and extract preference patterns
  that you observe in the data — naming and number of patterns is up to you.
  Each pattern must include name (snake_case), description, evidence, confidence.
  ```
- [ ] User Message 템플릿: 본 실험과 동일 (Source 리뷰 최신순 15~30개)
- [ ] 출력 스키마 (개수 무제한):
  ```json
  {
    "user_id": "...",
    "patterns": [
      {"name": "snake_case_name", "description": "...",
       "evidence": ["..."], "confidence": 0.0~1.0,
       "polarity": "positive|negative|mixed"}
    ],
    "summary": "..."
  }
  ```
- [ ] 실험 본 프롬프트와 차이 명시 (Pilot은 free-form, 본 실험은 6개 강제)

#### 2.2.3 환경 점검

- [ ] OpenAI API 키 설정 확인 (`echo $OPENAI_API_KEY`)
- [ ] `pip list | grep -E "openai|sentence-transformers|sklearn|matplotlib"` 확인
- [ ] 누락 시 `pip install openai sentence-transformers scikit-learn`

### 2.3 산출물
- `scripts/pilot_sample.py`
- `data/pilot_users.parquet` (100명)
- `prompts/pilot_profiler_prompt.md`

---

## 3. Phase 2 — LLM 실행 (목표 1시간 + API 대기)

### 3.1 목표
100명 모두에 대해 비구조화 패턴 추출 완료.

### 3.2 체크리스트

#### 3.2.1 실행 스크립트

- [ ] 새 스크립트 `scripts/run_pilot.py` 작성 (run_profiler.py 기반 변형)
- [ ] `prompts/pilot_profiler_prompt.md` 로드
- [ ] 100명 순차 실행 (sequential, rate limit 회피)
- [ ] Resume 지원 (이미 처리된 user 스킵)
- [ ] Retry 로직 (JSON 파싱 실패 시 최대 3회)

#### 3.2.2 실행 + 모니터링

- [ ] `python scripts/run_pilot.py --dry-run --n-users 3` 검증 (프롬프트 확인)
- [ ] 첫 5명 실행 후 출력 수동 검토 — 패턴 추출 품질 확인
- [ ] 만족 시 100명 전체 실행 (~30~40분 예상)
- [ ] 비용 기록: 예상 ~$0.10

#### 3.2.3 출력 검증

- [ ] 100명 모두 JSON 파일 생성 확인
- [ ] 사용자별 평균 패턴 수 (예상 5~15개)
- [ ] 사용자별 confidence 평균 (≥0.5 사용자 비율)
- [ ] 비정상 출력 (빈 patterns 배열, 결측 필드) 확인 → 재실행

### 3.3 산출물
- `scripts/run_pilot.py`
- `pilot_outputs/user_{id}.json` × 100
- 실행 로그 (`pilot_outputs/run.log`)

### 3.4 성공 기준
- [ ] 100/100 사용자에 대해 valid JSON 산출 (실패율 0%)
- [ ] 사용자별 평균 패턴 수 5~15개 범위
- [ ] 모든 패턴이 evidence 인용 포함

---

## 4. Phase 3 — 패턴 정규화 (목표 2시간) ⭐ 가장 까다로움

### 4.1 목표
약 1,000개의 raw 패턴 이름을 의미적으로 정규화하여 ~50~150개의 군집으로 집계.

### 4.2 체크리스트

#### 4.2.1 패턴 수집

- [ ] 새 스크립트 `scripts/collect_patterns.py` 작성
- [ ] `pilot_outputs/*.json` 모두 로드
- [ ] 모든 patterns 추출 → DataFrame 생성:
  ```
  user_id | pattern_name (raw) | description | confidence | polarity
  ```
- [ ] 산출: `data/pilot_patterns_raw.parquet`
- [ ] 통계 출력: 총 raw 패턴 수, unique name 개수

#### 4.2.2 표면 정규화 (1차)

- [ ] snake_case 통일 (`Genre Taste` → `genre_taste`)
- [ ] lowercase
- [ ] 불용어 제거 (`user_`, `_pref`, `_preference`로 끝나는 부분 통일)
- [ ] 산출: `data/pilot_patterns_normalized.parquet`
- [ ] unique name 감소율 보고 (예: 1000 → 600)

#### 4.2.3 임베딩 클러스터링 (2차)

- [ ] 새 스크립트 `scripts/normalize_patterns.py` 작성
- [ ] 라이브러리: `sentence-transformers` (`all-MiniLM-L6-v2` 모델)
- [ ] 입력: 각 unique pattern_name + description 결합 → 임베딩 384차원
- [ ] 클러스터링 알고리즘 선택:
  - [ ] HDBSCAN (자동 클러스터 수, 노이즈 감지) ★ 권장
  - [ ] 또는 KMeans (k=20~40 range로 elbow 탐색)
- [ ] 결과 검증: 클러스터별 멤버 출력
- [ ] 산출: `data/pilot_clusters.parquet` (pattern_name → cluster_id)

#### 4.2.4 수동 검토 (3차)

- [ ] 클러스터별 대표 이름 후보 자동 제안 (가장 빈도 높은 이름 또는 medoid)
- [ ] CSV로 export: `data/pilot_clusters_for_review.csv`
  - 컬럼: cluster_id | suggested_name | n_members | example_names | n_users
- [ ] 사용자가 직접 검토:
  - [ ] 잘못 묶인 클러스터 분리
  - [ ] 분리된 동의어 클러스터 병합
  - [ ] 최종 canonical name 확정
- [ ] 검토 완료 CSV: `data/pilot_clusters_final.csv`
- [ ] 산출: `data/pilot_patterns_canonical.parquet`

### 4.3 산출물
- `scripts/collect_patterns.py`
- `scripts/normalize_patterns.py`
- `data/pilot_patterns_raw.parquet`
- `data/pilot_patterns_normalized.parquet`
- `data/pilot_clusters.parquet`
- `data/pilot_clusters_for_review.csv` (수동 검토 입력)
- `data/pilot_clusters_final.csv` (수동 검토 출력)
- `data/pilot_patterns_canonical.parquet` (최종)

### 4.4 성공 기준
- [ ] Raw 패턴 1,000+ → Canonical 패턴 50~150개 정규화 완료
- [ ] 각 canonical pattern은 최소 3명 이상에서 등장
- [ ] 수동 검토 후 의미적 중복 클러스터 없음

---

## 5. Phase 4 — 빈도 분석 + 컷오프 결정 (목표 30분)

### 5.1 목표
정규화된 패턴 중 Top-N을 데이터 기반으로 결정.

### 5.2 체크리스트

#### 5.2.1 빈도 분석

- [ ] 새 스크립트 `scripts/analyze_pattern_frequency.py` 작성
- [ ] Canonical 패턴별:
  - [ ] 등장 사용자 수 (coverage)
  - [ ] 평균 confidence
  - [ ] 평균 polarity 분포 (positive / negative / mixed 비율)
- [ ] 산출: `data/pilot_pattern_frequency.parquet`

#### 5.2.2 Long-tail 시각화

- [ ] Pareto chart 생성:
  - X축: Top-N 패턴 (빈도 내림차순)
  - Y축: 등장 사용자 수
  - 누적 커버리지 라인 추가
- [ ] 산출: `data/pilot_pattern_frequency.png`

#### 5.2.3 Elbow Point 탐지

- [ ] 라이브러리: `kneed` (`pip install kneed`) 또는 수동 시각 탐지
- [ ] 탐지 결과: 자연스러운 컷오프 N (5/6/7/8 中 후보)
- [ ] 컷오프 검증:
  - [ ] Top-N의 마지막 패턴 빈도 vs Top-(N+1)의 빈도 차이 ≥ 50%
  - [ ] Top-N 누적 커버리지 ≥ 80%

#### 5.2.4 현재 6개와 비교

- [ ] 매핑 표 작성:
  ```
  현재 6개 (계획서)        | 데이터 도출 결과 (Top-N)
  ─────────────────────────┼─────────────────────────
  genre_preference         | genre_preference         (일치)
  narrative_complexity     | narrative_style          (부분 일치 — 이름만 다름)
  pacing_preference        | pacing                   (일치)
  quality_sensitivity      | (다른 이름으로 도출 가능)
  brand_loyalty            | author_loyalty           (도메인 매핑 차이)
  sensory_preference       | (등장 안 함 ← 가능성)
  ─────────────────────────┼─────────────────────────
  ```
- [ ] 일치 / 부분 일치 / 신규 / 누락 패턴 분류
- [ ] 결정: 최종 Core Pattern 확정 (이름·개수)

### 5.3 산출물
- `scripts/analyze_pattern_frequency.py`
- `data/pilot_pattern_frequency.parquet`
- `data/pilot_pattern_frequency.png`
- 비교 표 (마크다운)

### 5.4 성공 기준
- [ ] Elbow point 명확하게 식별 (시각적·정량적)
- [ ] 현재 6개와 도출 결과의 일치율 정량화
- [ ] 최종 N개 Core Pattern 명단 확정

---

## 6. Phase 5 — 직교성 검증 + 정의서 (목표 1시간)

### 6.1 목표
최종 N개 패턴이 서로 독립적이고 모든 사용자에 적용 가능한지 검증.

### 6.2 체크리스트

#### 6.2.1 직교성 검증

- [ ] 새 스크립트 `scripts/check_pattern_orthogonality.py` 작성
- [ ] N×N cosine similarity matrix 계산 (description 임베딩 기반)
- [ ] Heatmap 시각화: `data/pilot_pattern_orthogonality.png`
- [ ] 검증 기준: 모든 off-diagonal similarity ≤ 0.7
- [ ] 위반 시: 두 패턴 병합 또는 한쪽 재정의

#### 6.2.2 도메인 적합성 검증

- [ ] 각 패턴이 Movies 도메인 evidence에서 도출되는 빈도
- [ ] 각 패턴이 Books 도메인에 적용 가능한가 시뮬 (예: 수동으로 5명 책 리뷰에서 동일 패턴 보이는지)
- [ ] Books에 의미 없는 패턴 (예: `cinematography_appreciation`)은 BLOCK 후보로 분류

#### 6.2.3 사용자 커버리지 재확인

- [ ] 100명 中 각 패턴이 등장한 사용자 수 (Phase 4 결과 재사용)
- [ ] 모든 패턴이 ≥30명에서 등장 (안정적 빈도)
- [ ] 100명 中 N개 모두 패턴이 추출된 사용자 비율 (이상적: ≥80%)

#### 6.2.4 패턴 정의서 작성

- [ ] 새 파일 `prompts/core_patterns_definition.md` 작성
- [ ] 각 패턴별 다음 항목 작성:
  - canonical_name (snake_case)
  - 영문 정의 (1~2 문장)
  - 국문 정의
  - Movies 도메인 예시 (실제 리뷰 인용)
  - Books 도메인 예시 (가상 또는 실측)
  - transferability (high/medium/low) — 영화→책 전이 난이도
  - 평균 confidence (Pilot 결과)
  - 등장 사용자 수 / 100

### 6.3 산출물
- `scripts/check_pattern_orthogonality.py`
- `data/pilot_pattern_orthogonality.png`
- `prompts/core_patterns_definition.md` (Profiler·Teacher 프롬프트 업데이트의 기준)

### 6.4 성공 기준
- [ ] 모든 패턴 쌍 cosine similarity ≤ 0.7
- [ ] 모든 패턴이 Movies 도메인에서 충분 빈도 등장
- [ ] 정의서 6~8개 패턴에 대해 작성 완료

---

## 7. Phase 6 — 문서화 + 시스템 동기화 (목표 1~2시간)

### 7.1 목표
Pilot 결과를 모든 관련 문서·코드에 반영하여 일관성 확보.

### 7.2 체크리스트

#### 7.2.1 Pilot 결과 보고서 작성

- [ ] 새 파일 `scripts/generate_pilot_report.py` 작성 (옵션 — PDF 생성)
- [ ] 또는 마크다운 보고서 `docs/Pilot_Study_Report.md`:
  - 1. 목적 및 절차
  - 2. 100명 샘플 통계
  - 3. Raw 패턴 수집 결과
  - 4. 정규화 절차 + 군집 결과
  - 5. Top-N 빈도 분포 (그래프 포함)
  - 6. 현재 6개 vs 도출 결과 매핑 표
  - 7. 직교성·커버리지 검증
  - 8. 최종 Core Pattern 정의서
  - 9. 결론·향후 작업

#### 7.2.2 experiment_plan.md 업데이트

- [ ] §4 Pilot Study 섹션:
  - [ ] 4.5 (예상 Core Patterns) → 4.5 (확정 Core Patterns)로 변경
  - [ ] 도출된 N개 + 정의 + 영문/국문 설명 반영
  - [ ] 빈도 분포 그래프 참조 (`data/pilot_pattern_frequency.png`)
- [ ] §5 Profiler 구현:
  - [ ] 5.2 프롬프트 설계 — 현재 6개 설명을 도출된 N개로 교체
  - [ ] 5.5 I/O 예시 — 새 패턴 이름으로 업데이트

#### 7.2.3 Profiler 프롬프트 업데이트

- [ ] `prompts/profiler_prompt.md`:
  - [ ] §2 6개 Core Pattern 정의 → 도출된 N개로 교체
  - [ ] §3 System Prompt 내 6개 패턴 명시 부분 업데이트
  - [ ] §5 출력 예시 업데이트
- [ ] `scripts/run_profiler.py`:
  - [ ] `REQUIRED_CORE_PATTERNS` 리스트 업데이트
  - [ ] SYSTEM_PROMPT 내 패턴 정의 부분 업데이트
  - [ ] 검증 함수 동작 확인 (`validate_output`)

#### 7.2.4 Teacher 프롬프트 업데이트

- [ ] `prompts/teacher_prompt.md`:
  - [ ] §2 Transfer Gate 3-Level 예시 패턴 업데이트
  - [ ] Few-shot 3 예시의 패턴 이름 업데이트
- [ ] `scripts/run_teacher.py`:
  - [ ] SYSTEM_PROMPT 내 Few-shot 업데이트
  - [ ] `REQUIRED_CORE_PATTERNS` 통일

#### 7.2.5 Overview PDF 업데이트

- [ ] `scripts/generate_pdf.py`:
  - [ ] §6 Core Patterns 표 — 도출된 N개로 업데이트
  - [ ] §6.4 Profiler I/O 예시 — 새 패턴 이름 반영
  - [ ] §7.1 Judge I/O 예시 — 새 패턴 이름 반영
  - [ ] §6.3 Pilot Study 결과 박스 추가:
    ```
    Pilot Study (n=100) 결과:
    - Raw 패턴 X개 → 정규화 Y개 → Top-N 확정
    - 현재 6개와 일치 K/6, 부분 일치 M/6, 신규 도출 P개
    - 빈도 분포: Pareto curve (Top-N 후 50%+ 빈도 하락)
    ```
- [ ] PDF 재생성 후 시각 확인

#### 7.2.6 EDA 보고서 업데이트 (옵션)

- [ ] `scripts/generate_eda_report.py` §11에 GAP-2와 연결:
  - GAP-2 결과(평점 다양성 64.2%)와 Pilot에서 확인된 negative polarity 패턴 빈도 연결
- [ ] PDF 재생성

#### 7.2.7 Cross-Reference 검증

- [ ] experiment_plan.md, Overview PDF, profiler_prompt.md, teacher_prompt.md 4개 문서에서 패턴 이름 grep
  ```bash
  grep -r "genre_preference\|narrative_complexity\|pacing_preference\|quality_sensitivity\|brand_loyalty\|sensory_preference" \
       experiment_plan.md scripts/generate_pdf.py prompts/profiler_prompt.md prompts/teacher_prompt.md
  ```
- [ ] 모든 위치에서 동일 N개 패턴으로 통일 확인
- [ ] 누락된 곳 수정

### 7.3 산출물
- `docs/Pilot_Study_Report.md` (또는 PDF)
- 업데이트된 `experiment_plan.md`
- 업데이트된 `prompts/profiler_prompt.md`, `prompts/teacher_prompt.md`
- 업데이트된 `scripts/run_profiler.py`, `scripts/run_teacher.py`
- 업데이트된 `docs/TransferJudge_Overview_v5.pdf`
- 업데이트된 `docs/TransferJudge_EDA_Report.pdf` (옵션)

### 7.4 성공 기준
- [ ] 모든 문서의 패턴 이름이 일관됨 (cross-reference 검증 통과)
- [ ] PDF 재생성 완료, 시각적으로 결과 확인
- [ ] Pilot Study 결과를 심사위원에 1페이지로 설명 가능 (요약 차트·표 보유)

---

## 8. 산출물 종합 목록

### 신규 스크립트 (scripts/)
- [ ] `pilot_sample.py` — 100명 샘플링
- [ ] `run_pilot.py` — Pilot LLM 실행
- [ ] `collect_patterns.py` — 패턴 수집
- [ ] `normalize_patterns.py` — 표면 + 임베딩 정규화
- [ ] `analyze_pattern_frequency.py` — Pareto + elbow
- [ ] `check_pattern_orthogonality.py` — cosine similarity
- [ ] (옵션) `generate_pilot_report.py` — PDF 보고서

### 신규 프롬프트 (prompts/)
- [ ] `pilot_profiler_prompt.md` — 비구조화 추출
- [ ] `core_patterns_definition.md` — 최종 패턴 정의서

### 신규 데이터 (data/)
- [ ] `pilot_users.parquet`
- [ ] `pilot_patterns_raw.parquet`
- [ ] `pilot_patterns_normalized.parquet`
- [ ] `pilot_clusters.parquet`
- [ ] `pilot_clusters_for_review.csv` / `pilot_clusters_final.csv`
- [ ] `pilot_patterns_canonical.parquet`
- [ ] `pilot_pattern_frequency.parquet` / `.png`
- [ ] `pilot_pattern_orthogonality.png`

### 신규 출력 디렉토리
- [ ] `pilot_outputs/` — user_{id}.json × 100

### 신규 문서 (docs/)
- [ ] `Pilot_Study_Plan.md` (본 문서)
- [ ] `Pilot_Study_Report.md` (Phase 6 결과)

---

## 9. 리스크 및 대응

| 리스크 | 발생 가능성 | 대응 |
|--------|:---:|------|
| **R1.** Raw 패턴이 사용자별로 너무 적음 (≤3개) | 중 | 비구조화 프롬프트가 너무 보수적일 수 있음. 프롬프트 수정 후 10명만 재실행 후 비교 |
| **R2.** 클러스터링이 너무 거시적 (모든 패턴이 1~2 클러스터로) | 중 | HDBSCAN min_cluster_size 조정, 또는 description 가중치 ↑ |
| **R3.** 클러스터링이 너무 세분화 (50+ 군집) | 중 | KMeans k=15~25로 명시적 제한 |
| **R4.** 현재 6개와 도출 결과가 크게 다름 | 중상 | 사전 결정(Q5=A)대로 데이터 기반 결과 따름. Profiler/Teacher 프롬프트 + 모든 문서 1~2일 재작성 필요 |
| **R5.** Top-N elbow가 모호함 (점진적 감소) | 하 | Top-5, Top-7도 후보로 두고 직교성 검증으로 결정 |
| **R6.** Books 도메인에 의미 없는 패턴 (예: visual) 다수 도출 | 중 | 그것이 본 연구의 핵심 발견. BLOCK 후보로 분류하고 Transfer Gate 정당화에 활용 |
| **R7.** API 비용 초과 ($1+) | 하 | 100명에 ~$0.1 예산. 초과 시 즉시 중단·로그 분석 |

---

## 10. 권장 일정 (가변)

| Day | Phase | 시간 | 비고 |
|-----|-------|:---:|------|
| **Day 1 오전** | Phase 1 + Phase 2 | 1.5h | 샘플링 + 프롬프트 + 100명 실행 |
| **Day 1 오후** | Phase 3 | 2h | 패턴 정규화 (수동 검토 포함) |
| **Day 1 저녁** | Phase 4 + Phase 5 | 1.5h | 빈도 분석 + 직교성 검증 |
| **Day 2 오전** | Phase 6 | 2h | 문서·코드 동기화 |

**총 1.5일 (약 7시간)**, 분산 가능.

---

## 11. 시작 전 최종 확인 (5분)

진행 직전 다음 중 하나 선택:

- [ ] **A. Phase 1부터 즉시 시작** — 본 계획서대로 진행
- [ ] **B. 일부 항목 수정 요청** — 어디를 수정?
- [ ] **C. 더 검토 필요** — 어떤 부분?

---

## 12. 진행 추적 메모

> 작업 시작 시 본 섹션에 진행 상황 기록 (예: "Phase 2 완료 — 100명 中 100명 valid")

- 시작일: ____
- Phase 1 완료: ____
- Phase 2 완료: ____ (총 비용: $____)
- Phase 3 완료: ____ (raw → canonical: __ → __)
- Phase 4 완료: ____ (Top-N 확정: __개)
- Phase 5 완료: ____ (직교성 max sim: __)
- Phase 6 완료: ____
- **최종 완료**: ____

---

## 부록 A — 비구조화 프롬프트 초안 (Phase 1)

> 본 부록은 Phase 1.2.2의 참고용 초안. 실제 작성 시 다듬기.

```
You are an expert user preference analyst. Your task is to read a user's
Movies & TV reviews and extract preference patterns that you observe.

## Important Rules

- Naming and number of patterns is up to you. Discover patterns naturally.
- Do NOT use any predefined list of pattern types.
- Pattern names must be snake_case (e.g., "narrative_complexity", "atmospheric_mood").
- Each pattern must include:
  - name (snake_case)
  - description (1-2 sentences explaining what it captures)
  - evidence (1-2 review quotes that support this pattern)
  - confidence (0.0-1.0)
  - polarity (positive | negative | mixed)

- Aim for 5-15 patterns per user — extract what you genuinely observe.
- Avoid trivial patterns (e.g., "user_likes_movies" is too vague).
- Patterns should be actionable for cross-domain recommendation
  (e.g., useful for recommending books to this user).

## Output Schema (strict JSON)

{
  "user_id": "<string>",
  "patterns": [
    {"name": "...", "description": "...", "evidence": ["..."],
     "confidence": <float>, "polarity": "..."}
  ],
  "summary": "<2-3 sentence overall taste summary>"
}

Output ONLY the JSON object.
```

---

## 부록 B — 정규화 클러스터링 의사코드 (Phase 3)

```python
# Phase 3.2.3 임베딩 클러스터링
from sentence_transformers import SentenceTransformer
import hdbscan

# 입력: pattern_name + description 문자열
texts = [f"{name}: {desc}" for name, desc in unique_patterns]
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(texts)  # (N, 384)

# HDBSCAN 클러스터링
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=3,
    min_samples=2,
    cluster_selection_epsilon=0.2,
    metric="cosine",
)
labels = clusterer.fit_predict(embeddings)
# labels == -1 은 노이즈 (개별 처리)

# 클러스터별 대표 이름: 가장 빈도 높은 멤버
for cid in set(labels) - {-1}:
    members = [unique_patterns[i] for i, l in enumerate(labels) if l == cid]
    print(f"Cluster {cid} ({len(members)}): {members[:5]}")
```

---

> 본 계획서를 Phase별로 따라가면 6~7시간 내 Pilot Study 완료 가능.
> 각 체크박스는 작업 진행에 따라 X 표시하여 추적.
> 최종 완료 시 §1 성공 조건 7개를 모두 만족해야 함.
