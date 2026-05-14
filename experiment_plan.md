# TransferJudge 실험 계획서

> **TransferJudge: 선택적 전이를 위한 Profiler-Judge 구조의 LLM 기반 교차 도메인 추천 프레임워크**
> *TransferJudge: A Profiler-Judge LLM-Based Framework for Selective Transfer in Cross-Domain Recommendation*
>
> 2026.02 빅데이터학과 17기 곽민아

---

## 1. 실험 개요

### 1.1 목표
Cross-Domain Cold-Start 환경(Movies & TV → Books)에서 TransferJudge의 Profiler-Judge Transfer Gate 프레임워크가 추천 성능을 향상시키는지 검증한다.

### 1.2 Research Questions

본 연구는 단순 자기 ablation을 넘어 전통 CDR + LLM 기반 CDR baselines를 포함한
4가지 핵심 질문을 검증한다 (외부 리뷰 권장 반영, 2026-05-15).

| RQ | 질문 | 핵심 비교 |
|----|------|----------|
| **RQ1** | 구조화된 preference profile은 raw review 입력 및 **전통 CDR baseline** 대비 cold-start CDR 성능을 개선하는가? | (c) vs (f), (c) vs (e) |
| **RQ2** | Pattern-level Transfer Gate는 모든 preference signal을 균일하게 전이하는 방식보다 negative transfer를 줄이고 추천 성능을 높이는가? | (c) vs (d) |
| **RQ3** | Profiler-Judge 구조와 Judge 파인튜닝은 single-prompt LLM / prompt-only / **LLM-based CDR baseline** 대비 더 효과적인가? | (c) vs (a)(b)(g) |
| **RQ4** | Movies-to-Books 전이에서 어떤 preference pattern이 transferable, partially transferable, domain-specific으로 작동하는가? | Phase 5a Per-Pattern Ablation |

**Baseline 카테고리 (7 conditions, Codex 권장 현실 버전)**:
- 단순 LLM: (a) Single LLM zero-shot, (b) Prompt-only zero-shot
- 본 연구 자기검증: (c) Ours ★, (d) w/o Gate, (f) Raw Review (no Profile)
- **전통 CDR (1개)**: (e) EMCDR (IJCAI 2017) — 가장 인용 많은 고전 baseline
- **LLM 기반 CDR (1개)**: (g) **LLM4CDR-style** single-LLM CDR baseline

PTUPCDR (WSDM 2022)은 §2 Related Work에서 최신 전통 CDR 흐름으로 논의하되, 직접 baseline에는 포함하지 않음.
이유: (i) 본 연구의 차별성은 LLM 기반 selective transfer이며 전통 CDR SOTA 재현이 아님,
(ii) PTUPCDR은 meta-learning(MAML) 기반으로 재현 구현 부담 큼,
(iii) 전통 CDR 1개로도 "LLM 기반이 전통 대비 효과적인가" 검증 가능.

TALLRec(RecSys 2023)은 single-domain LLM recommendation tuning 논문으로, 본 연구의
LLM SFT 기법적 근거로 Related Work에서만 인용. 직접 CDR baseline은 LLM4CDR-style로 통일.

### 1.3 리소스 예산

| 항목 | 예상 비용 | 근거 |
|------|----------|------|
| GPT-4o-mini — Profiler (1,000명) | ~$0.86 | 실측 토큰: mean input 2,900 / output 700 |
| GPT-4o-mini — Teacher (800명) | ~$2.0 | 실측 토큰: mean input 7,700 / output 1,500 |
| GPT-4o-mini — Pilot + 재시도 여유 | ~$1.0 | 20% 버퍼 |
| 클라우드 GPU (Colab Pro / RunPod) | ~$10~30 | QLoRA 파인튜닝 6~12h |
| **총 예상 비용** | **~$15~35** | |

---

## 2. 데이터 수집 및 전처리

### 2.1 데이터 다운로드

- **소스**: Amazon Review 2023 (McAuley Lab)
- **도메인**: Movies_and_TV, Books
- **다운로드 항목**: Review 데이터 + Item Metadata

### 2.2 Overlapping User 추출

```
조건:
- Movies & TV 리뷰 >= 15개
- Books 리뷰 >= 5개 AND <= 10개 (Cold-Start 구간)
- 양쪽 도메인에 모두 존재하는 사용자
- 목표: 1,000명 추출
```

#### Cold-Start 기준 근거 (Target 리뷰 5~10개)

| 구간 | 리뷰 수 | 문제점 | 비고 |
|------|---------|--------|------|
| Zero-Shot | 0개 | Target 정보 전무 → CDR 전이 효과 측정 자체가 어려움 | 평가 불가 |
| **Cold-Start (본 연구)** | **5~10개** | **Target 단독으로는 부족하되, CDR 효과를 측정할 수 있는 최적 구간** | **선택** |
| Warm-Start | 10개 초과 | Target 단독으로도 추천 품질 확보 → CDR 필요성 희석 | 제외 |

- 선행연구 기준: 대부분의 CDR 논문은 Target 상호작용 < 20개를 Cold-Start로 정의 (EMCDR, LLM4CDR 등)
- 본 연구는 이 범위 내에서 "CDR이 가장 필요한 구간"을 구체화한 것
#### Source 도메인 >= 15개 기준 근거

| 근거 | 설명 |
|------|------|
| **패턴 추출 최소 요건** | Profiler가 7개 Core Pattern을 안정적으로 추출하려면 최소 10~15개의 리뷰가 필요. 리뷰 10개 미만이면 genre_preference 외 패턴(narrative_complexity, quality_sensitivity 등)이 누락되는 빈도가 높아짐 (Pilot Study에서 검증 예정) |
| **선행연구 Source 기준** | CDR 연구에서 Source 도메인은 "data-rich" 조건을 전제로 함. EMCDR(IJCAI 2019)은 Source 최소 10개, LLM4CDR(WWW 2025)은 Source 최소 5개 상호작용을 사용. 본 연구는 텍스트 리뷰 기반이므로 패턴 다양성 확보를 위해 15개로 상향 설정 |
| **토큰 예산과의 정합성** | **EDA 실측(1,000명 샘플)**: Movies & TV 리뷰 평균 **80.4 tokens**, P95 **343 tokens**. 15개 × 80.4 tokens = **~1,206 tokens**으로 최소 입력도 GPT-4o-mini 128K context 내 충분 (0.9%) |

#### Source 입력 최대 30개 근거

| 근거 | 설명 |
|------|------|
| **토큰 예산 역산 (EDA 실측)** | Movies & TV 평균 **80.4 tokens/건** × 30개 = **~2,412 tokens**. Target Books 평균 **67.3 tokens/건** × 10개 = **~673 tokens**. 합산 ~3,085 tokens + 시스템 프롬프트 ~500 tokens = **~3,585 tokens** → GPT-4o-mini 128K의 **2.8%**. P95 worst-case도 **~13,448 tokens (10.5%)**로 리뷰 truncation 불필요 |
| **최신순 선택 이유** | 최근 리뷰가 현재 선호를 더 잘 반영 (temporal preference drift). 30개는 최근 2~3년 시청 이력에 해당하여 현재 취향 파악에 적절 |
| **수확 체감 (diminishing returns)** | 30개 이상 추가해도 새로운 패턴 발견 확률 감소. Profiler는 7개 Core Pattern만 추출하므로 15~30개면 패턴 포화에 충분 (Pilot Study에서 15개 vs 30개 비교 검증 예정) |
| **선행연구 참조** | arXiv 2503.07761 (CDR + LLM)은 도메인당 최대 10개 상호작용 사용. 본 연구는 텍스트 리뷰의 풍부한 정보를 활용하므로 30개까지 확장하되, 토큰 한도를 초과하지 않는 범위로 설정 |

> **참고 토큰 통계**
> - **선행연구 역산값**: Amazon Reviews 2023 공식 페이지(amazon-reviews-2023.github.io) 전체 통계 역산 Movies ~58 tokens, Books ~98 tokens; arXiv 2503.07761 Movies 평균 38.18 words ≈ 50 tokens
> - **본 연구 EDA 실측값 (1,000명 샘플, tiktoken cl100k_base)**: Movies mean **80.4** / P95 **343**, Books mean **67.3** / P95 **266**
> - 선행연구 역산값 대비 Movies는 유사, Books는 낮음. P95가 평균의 4~6배인 right-skewed 분포 확인 (소수의 장문 리뷰가 꼬리를 끌어올림)

#### 데이터 규모 근거 (1,000명)

| 근거 | 설명 |
|------|------|
| **LLM 기반 CDR 분야 규모 대비 상위권** | LLM4CDR(WWW 2025) **100명**, TALLRec(RecSys 2023) few-shot **16~256 샘플**, LLM 기반 콜드스타트 벤치마크(Serendipity-2018) **500명**. 본 연구 1,000명은 이들 대비 **2~10배 큰 규모** |
| **비용 제약과의 균형** | Profiler GPT-4o-mini API 호출 + Qwen3-14B QLoRA Teacher Distillation 학습 데이터 ~50,000건(800명 × 평균 60 후보) 생성을 위한 균형점. 석사 연구 예산(~$5) 내 실현 가능 |
| **통계적 충분성** | Test 100명에서 Bootstrap CI 적용 시 95% 신뢰구간 폭 ±8~10%p로 조건 간 차이 검출 가능 |

#### 무작위 샘플링(seed=42) 근거

**선행연구 샘플링 방식 비교:**

| 논문 | 샘플링 방식 | 시간 필터 |
|------|-------------|-----------|
| TALLRec (RecSys 2023) | Books: 사용자별 무작위 1건 / Movies: 최근 10K interaction | 부분적용 (Movies만) |
| **LLM4CDR (WWW 2025)** | **무작위 100명** | ❌ 없음 |
| EMCDR (IJCAI 2017) | 무작위 비율 분할 (5%/50%/80%) | ❌ 없음 |
| CDRNP (WSDM 2024) | 무작위 50% cold-start 시뮬레이션 | ❌ 없음 |
| **본 연구** | **무작위 1,000명 (seed=42)** | ❌ 없음 |

| 근거 | 설명 |
|------|------|
| **학계 표준 관행** | CDR 분야에서 무작위 샘플링 + 고정 seed는 재현성 확보의 표준 프로토콜. "최신 사용자 우선" 샘플링을 채택한 주요 CDR 논문은 확인되지 않음 |
| **시점 편향 관리** | EDA 검증 결과: Source-Target 시점 갭 **중앙값 1.2년**, 2018년 이전 사용자 **25.8%**(30% 미만)로 시점 편향이 허용 범위 내 |
| **과적합 방지** | 특정 시점 사용자에게 모델이 과적합되는 것을 방지. 무작위 샘플링이 전체 기간(1996~2023) 분포를 자연스럽게 반영 |
| **선행연구 정합성** | 4편의 주요 CDR 논문(TALLRec, LLM4CDR, EMCDR, CDRNP) 모두 시간 필터 미적용. 본 연구도 동일 프로토콜 |

> **시점 타당성 보고**: 선행연구는 샘플링 시점 분포를 명시적으로 보고하지 않았으나, 본 연구는 EDA(섹션 7)에서 시점 분포·갭을 정량화하여 투명성을 강화한다.

### 2.3 데이터 분할

| 구분 | 인원 | 용도 | 비율 근거 |
|------|------|------|----------|
| Train | 800명 | Teacher Distillation 학습 데이터 생성 | SFT에 충분한 학습량 (TALLRec: 100건으로도 일반화 달성) |
| Validation | 100명 | 파인튜닝 early stopping | overfitting 방지를 위한 최소 규모 |
| Test | 100명 | 최종 성능 평가 | Bootstrap CI로 통계적 신뢰성 확보 |

> 8:1:1 분할은 추천 시스템 연구의 표준 비율이며, TALLRec, LLM4CDR 등 주요 선행연구와 동일한 프로토콜을 따른다.

### 2.4 Ground Truth 구성

- 각 사용자의 Books 도메인에서 **rating ≥ 4인 구매 중 가장 최근 아이템** 1개를 GT로 사용
- GT를 제외한 나머지 리뷰(최대 9개)를 Profiler 입력으로 사용
- 후보: GT 1개 + Random Negative 49개 = **50개**
- Negative 아이템은 사용자가 구매하지 않은 Books 도메인 아이템에서 무작위 선정

#### GT 선정 방식 근거: 왜 Explicit Positive (rating ≥ 4)인가?

**선행연구 GT 방식 비교:**

| 논문 | GT 방식 | 평점 처리 | 비고 |
|------|---------|---------|------|
| NCF (He et al., WWW 2017) | 마지막 상호작용 | 모든 평점 → implicit(1)로 변환 | 평점 무시, 구매 자체가 positive |
| TALLRec (RecSys 2023) | 마지막 상호작용 | 4점 이상=Yes, 미만=No | binary classification |
| LLM4CDR (WWW 2025) | 마지막 상호작용 | **5점만** 남기고 전처리 | 전체 데이터에서 5점 외 제거 |
| TrineCDR (KDD 2024) | 마지막 상호작용 | implicit 변환 | NCF와 동일 |
| **본 연구** | **4점 이상 중 가장 최근** | **rating ≥ 4만 GT 대상** | Explicit positive |

**Implicit 방식을 채택하지 않은 이유:**

본 연구의 핵심 기여인 Transfer Gate는 Negative Transfer를 방지하여 **사용자가 만족할 아이템**을 추천하는 것이 목표이다. Implicit feedback(구매=positive) 방식은 이 목표와 충돌한다:

| 시나리오 | Implicit GT | Transfer Gate 효과 측정 |
|---------|------------|----------------------|
| GT가 2점짜리 아이템 | "맞혀야 할 정답" 취급 | Transfer Gate가 올바르게 BLOCK했는데 성능이 낮게 측정됨 → **효과 과소 측정** |
| GT가 5점짜리 아이템 | "맞혀야 할 정답" 취급 | 정상적으로 측정 |

→ Implicit 방식에서는 Transfer Gate가 나쁜 패턴을 차단한 **올바른 판단**이 오히려 **성능 하락**으로 나타날 수 있어, RQ2(Transfer Gate 필터링 효과)의 검증이 왜곡된다.

**Explicit Positive (rating ≥ 4) 방식의 장점:**

| 근거 | 설명 |
|------|------|
| **연구 목적 정합성** | Transfer Gate는 "좋은 추천"을 위한 필터링 → GT도 "사용자가 만족한 아이템"이어야 Transfer/Block 판단의 효과를 정확히 측정 가능 |
| **Negative Transfer 증명** | BLOCK 판정의 가치를 보이려면, GT가 실제 positive여야 "올바르게 TRANSFER해서 맞힌 것"과 "잘못 BLOCK해서 놓친 것"을 구분 가능 |
| **LLM4CDR와의 비교** | LLM4CDR은 5점만 사용 — 본 연구는 4점 이상으로 더 넓은 범위를 사용하여 오히려 더 현실적 |
| **사용자 탈락 최소화** | "마지막 구매가 반드시 4점 이상"이 아닌 "4점 이상인 구매 중 가장 최근"을 사용하므로, 한 번이라도 4점 이상을 준 사용자는 모두 포함 |

> **입력 리뷰는 전체 평점(1~5점) 사용**: GT만 4점 이상이며, Profiler 입력 리뷰는 평점과 무관하게 전체를 사용한다. 낮은 평점 리뷰도 "무엇을 싫어하는지"를 나타내는 유용한 선호 패턴 정보이다 (예: 1점 호러 리뷰 → quality_sensitivity, genre_preference 패턴 추출에 기여).

#### 한눈에 보는 Implicit vs Explicit Positive

| 방식 | 정답(GT)으로 인정하는 기준 | 비유 |
|------|---------------------------|------|
| **Implicit** (구매=positive) | "구매했다" → 무조건 좋아한 것으로 간주 (평점 1점도 정답으로 취급) | 장바구니에 담은 모든 책을 "이 사람이 좋아하는 책"이라고 가정. 환불·후회한 책도 포함. |
| **Explicit Positive ★** (rating ≥ 4) | "4점 이상 평점을 줬다" → 명시적으로 만족한 것만 정답 | 실제로 별점 4~5점을 준 책만 "정말 좋아한 책"으로 인정. 후회한 구매는 제외. |

**구체 시나리오 비교:**

| 시나리오 | Implicit이라면 | Explicit Positive라면 |
|---------|----------------|------------------------|
| 사용자가 영화 "놀란 감독 팬"이라 책 분야에서도 "놀란 자서전(2점)"을 구매 *(Negative Transfer 사례)* | "놀란 자서전 = 정답" → Transfer Gate가 brand_loyalty를 BLOCK해서 추천 안 함 → **성능 하락**으로 측정 → Gate의 올바른 판단이 **왜곡 평가** | "놀란 자서전(2점) = 정답 아님" → Gate가 올바르게 BLOCK → **Gate 효과 정확 반영** |
| 사용자가 "복잡한 서사 선호" 패턴이 있고 "Cloud Atlas(5점)"를 구매 | "Cloud Atlas = 정답" → TRANSFER로 추천 시 점수 ↑ → 정상 측정 | "Cloud Atlas = 정답" → TRANSFER로 추천 시 점수 ↑ → 정상 측정 |

> **핵심 정리**: Implicit 방식에서는 "사용자가 후회한 구매(낮은 평점)"까지 정답 취급하므로, Transfer Gate가 그것을 BLOCK한 **올바른 판정**이 평가에서 "맞히지 못한 것"으로 잘못 측정된다. Explicit Positive는 "사용자가 진짜 만족한 것"만 정답으로 두어, BLOCK의 가치를 정확히 측정 가능하게 한다. 즉, **본 연구의 핵심 가설(Transfer Gate가 부정 전이를 막아 추천 품질을 높인다)을 검증하려면 GT가 Explicit Positive여야 한다.**

#### 후보 50개 선정 방법 및 근거

**선정 절차:**
1. 사용자의 Books 도메인에서 rating ≥ 4인 구매 중 **가장 최근 아이템**을 GT로 설정
2. 해당 사용자가 **구매하지 않은** Books 도메인 아이템 중에서 49개를 균일 랜덤 샘플링
3. GT 1개 + Negative 49개 = 50개를 섞어 후보 리스트 구성
4. **후보 아이템 정보 구성**: 제목 + **저자** + 카테고리 + 평균 평점 + **features 첫 50 tokens** (아래 참조)

**후보 아이템 정보 구성 방침 (EDA 기반 확정):**

| 포함 필드 | 결측률 | 역할 |
|-----------|--------|------|
| `title` | 0.0% | 아이템 식별 (필수) |
| **`author_name`** | **27.4%** | **저자 정보 (Judge의 brand_loyalty 판단 근거)**. str로 저장된 dict를 `ast.literal_eval`로 파싱하여 추출 (72.6% 추출 성공) |
| `categories` | 0.0% | 장르/계층 정보 (Judge의 genre_preference 판단 근거) |
| `average_rating` | 0.0% | 품질 지표 (Judge의 quality_sensitivity 판단 근거) |
| **`features`** (줄거리 첫 50 tokens) | **11.7%** | **책의 내용 요약 (Judge의 narrative_complexity, sensory_preference 등 전이 가능성 판단 근거)** |

**features 포함 결정의 근거:**

| 근거 | 설명 |
|------|------|
| **Selective Transfer 판단의 필수 정보** | 제목·카테고리·평점만으로는 "이 책이 사용자의 영화 선호 패턴과 맞는지" 판단이 제한적. 줄거리가 있어야 "이 사용자는 복잡한 서사를 선호하는데 이 책은 단순한 모험물이다" 같은 세밀한 전이 판단 가능 |
| **description 대비 품질 우위** | EDA에서 `description`은 리뷰 인용/저자 소개 혼재로 부적합 확인. `features`가 실제 줄거리를 담은 유일한 필드 |
| **토큰 예산 내** | 아이템당 평균 20 tokens(제목+카테고리+평점) + author_name ~4 tokens + features 첫 50 tokens = **~74 tokens × 50개 = ~3,700 tokens**. Profiler Output ~800 + 시스템 프롬프트 ~500 합산해도 총 ~5,000 tokens로 GPT-4o-mini 128K의 **3.9%**로 여유 |
| **결측 처리** | features 결측(11.7%) 아이템은 제목+카테고리+평점만 제공. Judge가 정보 부족 상황에서도 판단하도록 학습 |

**description 제외 근거 (EDA 샘플링 결과)**:
- description 예시: "Review 'This uplifting story...'" (리뷰 인용) · "About the Author..." (저자 소개)
- features 예시: "In the year 2032, eighty-year-old Moira Burke watches as life on Earth becomes..." (실제 줄거리)
- → 본 연구는 **description 미사용, features 사용**으로 확정

**왜 50개 후보인가?**
| 근거 | 설명 |
|------|------|
| **선행연구 표준** | LLM4CDR(WWW 2025)은 후보 20개, TALLRec(RecSys 2023)은 후보 없이 pairwise 판정. 50개는 LLM의 컨텍스트 한도 내에서 충분한 난이도를 제공하는 규모 |
| **LLM 토큰 제약 (EDA 실측)** | 후보 1개당 ~20 tokens(제목+카테고리+평점) + author_name ~4 + features 50 tokens = ~74 tokens × 50개 = **~3,700 tokens**. Profiler Output + 프롬프트 포함 총 ~5,000 tokens → GPT-4o-mini 128K의 3.9%로 여유 |
| **랜덤 확률 보정** | 후보 50개 중 랜덤 추천 시 HR@1 기대값 = 2%, HR@10 기대값 = 20% → 모델의 실질적 성능을 측정하기에 적절한 난이도 |
| **평가 안정성** | 후보가 너무 적으면(20개) HR@10이 천장 효과로 조건 간 차이 미검출, 너무 많으면(100개) LLM 토큰 한도 초과 또는 추론 비용 증가 |

**왜 균일 랜덤 샘플링인가?**
- **Popularity-based sampling** 대비 단순하고 재현 가능
- TALLRec, LLM4CDR 등 LLM 기반 추천 연구의 표준 프로토콜과 동일하여 **결과 비교가 공정**
- 랜덤 시드 고정(seed=42)으로 모든 Ablation 조건이 동일 후보 셋을 공유 → 변인 통제

### 2.5 전처리 체크리스트

- [ ] 리뷰 텍스트 정제 (HTML 태그 제거, 길이 제한)
- [x] Source 리뷰: 최대 30개 (최신순) — **EDA 실측 토큰 예산**: 30 × mean 80.4 = **~2,412 tokens** (P95 worst-case: 30 × 343 = ~10,290)
- [x] Target 리뷰: 전체 사용 (GT 제외, 최대 10개) — **EDA 실측 토큰 예산**: 10 × mean 67.3 = **~673 tokens** (P95 worst-case: 10 × 266 = ~2,660)
- [x] **EDA 검증 완료**: Profiler 입력 합계 mean **~3,585 tokens** (128K의 2.8%), P95 worst-case **~13,448 tokens** (10.5%) → **리뷰 truncation 불필요**
- [x] 아이템 메타데이터 정리: 제목(결측 0%), 카테고리(결측 0%), 평균 평점(결측 0%), **features 줄거리(존재율 88.3%)** 추가
- [ ] user_id 매핑 테이블 생성

### 2.6 선행연구 데이터 구성 비교

| 항목 | TALLRec (RecSys 2023) | LLM4CDR (WWW 2025) | EMCDR (IJCAI 2017) | TrineCDR (KDD 2024) | **본 연구** |
|------|----------------------|--------------------|--------------------|---------------------|-----------|
| **데이터셋** | MovieLens + Amazon | Amazon Review 2018 (5-core) | Amazon Reviews (5-core) | Amazon + Douban | **Amazon Review 2023** |
| **도메인** | 단일 (Movie, Book 각각) | Movies&TV, Games, CDs, Electronics | Book↔Movie, Book↔Music | Electronics, Books, DVD | **Movies&TV → Books** |
| **사용자 필터** | Few-shot (16~256건) | Rating=5.0, 구매>20 | 5-core | 10-core (Douban) | **Source≥15, Target 5~10** |
| **날짜 필터** | ❌ 없음 | ❌ 없음 | ❌ 없음 | ❌ 없음 | **❌ 없음 (EDA에서 시점 분포 보고)** |
| **사용자 수** | 비공개 | ~100명 (랜덤) | 비공개 | 비공개 | **1,000명** |
| **분할** | train/valid/test | 없음 (zero-shot) | 80/20 | 비공개 | **8:1:1** |
| **후보 수** | 없음 (binary) | 20개 | 없음 (MAE/RMSE) | 100개 (1+99) | **50개 (1+49)** |
| **Cold-Start** | 미정의 | Target 구매 0 | 매핑 함수 예측 | NT 완화 중심 | **Target 5~10 (CDR 최적 구간)** |
| **평가** | AUC | HR@K, NDCG@K | MAE, RMSE | HR@K, NDCG@K | **HR@K, NDCG@K, MRR** |

> **날짜 필터 미적용 근거**: 조사한 CDR 선행연구 4편 모두 시간/날짜 기반 필터를 적용하지 않음. 상호작용 수(n-core)와 평점 기준만 사용하는 것이 CDR 연구의 관행. 단, EDA에서 대상 사용자의 마지막 리뷰 시점 분포와 Source-Target 시점 갭을 보고하여, 데이터의 시간적 타당성을 문서화한다. 만약 2018년 이전 사용자가 30% 이상이면 날짜 필터 추가를 검토한다.

---

## 3. 데이터 EDA (탐색적 데이터 분석)

### 3.1 목적
Pilot Study 및 실험 설계 전에 데이터의 분포와 특성을 파악하여, 실험 조건의 타당성을 확인한다.

### 3.2 EDA 항목 및 실측 결과

| 분석 항목 | EDA 실측 결과 | 판정 |
|----------|------------|----------|
| Overlapping User 분포 | Source≥15 & Target 5~10 조건에서 **22,465명** 확보 (전체 overlapping 2,530,704명 중) | ✅ 목표 1,000명 대비 **22배 여유** |
| Source 리뷰 수 분포 | 1,000명 샘플: mean **31.7** / median **22** / P95 **71** / min **15** / max **629** | ✅ 최신순 30개 입력 시 대부분 전체 또는 대부분의 리뷰 활용 가능 |
| Target 리뷰 수 분포 | 1,000명 샘플: mean **7.0** / median **7** / min **5** / max **10** | ✅ 5~10개 Cold-Start 구간 정확히 분포 |
| 리뷰 길이 분석 (tiktoken cl100k_base) | Movies mean **80.4** / median **28** / P95 **343** / max **4,749**; Books mean **67.3** / median **30** / P95 **266** / max **1,872** | ✅ Profiler 입력 mean **~3,585 tokens** (128K의 2.8%), P95 worst-case **~13,448** (10.5%) → truncation 불필요 |
| 평점 분포 (J-shaped) | Movies Rating≥4 비율 **79.5%**, Books **85.0%** | ✅ GT(rating≥4) 확보에 유리한 고평점 편향 |
| GT 확보율 | 방식 A(마지막 구매 ≥4점): 84.1% → 방식 B(≥4점 중 가장 최근): **99.6%** → 1,000명 샘플 후 **100%** | ✅ 채택 방식으로 전원 GT 확보 |
| 시점 분포 | 마지막 리뷰 중앙값 Movies **2019-04** / Books **2018-11** / 어느 쪽이든 **2020-08** | ✅ 2018년 이전 **25.8%** (30% 미만), 시점 갭 중앙값 **1.2년** (3년 미만) → 날짜 필터 불필요 |
| 카테고리/메타데이터 품질 | Books 핵심 필드(title, average_rating, categories) 결측률 **0%**, features(줄거리) 존재율 **88.3%**, description 품질 부적합 | ✅ 후보 아이템 정보 구성 충분, features 기반 구성 가능 |
| 후보 아이템 토큰 | 제목+카테고리+평점 기준 아이템당 mean **20 tokens**, 50개 합계 **~998 tokens** | ✅ 예산 내. features 첫 50 tokens 추가해도 ~3,500 tokens |
| **GAP-2** Source 평점 다양성 (Profiler negative polarity 검증) | rating ≤ 2 보유 사용자 **64.2%**, ≤ 3 보유 **81.6%**, std mean **0.90** | ✅ Profiler의 polarity=negative 패턴 추출 가능성 데이터로 입증 |
| **GAP-1** Source-Target Top-Genre 매핑 | 양 도메인 매핑 가능 **98.3%** / 동일 명칭 직접 매칭 **0건** / Suspense→Lit&Fic 33.3%, Drama→Mystery 22.8% 등 | ✅ CDR 데이터 근거 + **PARTIAL 판정 필수성 증명** (직접 매칭 불가) |
| **GAP-4** GT vs Negative 분포 비교 | 평점 차이 **+0.15** (KS=0.158), Top-10 카테고리 분포 거의 동일 | ✅ 단순 baseline(평점·카테고리 정렬)으로 GT 식별 불가 → 평가 공정성 확보 |

### 3.3 산출물
- EDA 노트북: `notebooks/eda.ipynb` (53셀, GAP 분석 코드 포함)
- EDA 보고서 PDF: `docs/TransferJudge_EDA_Report.pdf` (11개 섹션, GAP 검증 §11 포함)
- GAP 분석 스크립트: `scripts/analyze_eda_gaps.py`
- GAP 분석 산출 그래프: `data/eda_rating_diversity.png`, `eda_cross_domain_categories.png`, `eda_gt_vs_negative.png`
- 전처리 parquet: `data/` 폴더
- 시각화 PNG: `data/eda_*.png`

### 3.4 주요 설계 결정 (EDA 기반)

| 결정 사항 | 선택 | 근거 |
|-----------|------|------|
| GT 선정 방식 | rating ≥ 4 중 가장 최근 (Explicit Positive) | 방식 A 대비 +3,466명 (99.6% 확보), Transfer Gate BLOCK 효과 정확 측정 |
| 날짜 필터 | 미적용 | 선행연구 4편 동일. 2018년 이전 25.8%, 시점 갭 1.2년으로 허용 범위 |
| 리뷰 truncation | 미적용 (전체 리뷰 사용) | P95 worst-case 13,448 tokens → GPT-4o-mini 128K의 10.5% |
| 후보 아이템 정보 구성 | 제목 + 카테고리 + 평점 + **features 첫 50 tokens** | features(줄거리) 88.3% 존재. description은 품질 부적합으로 제외 |
| description 제외 | 미사용 | 리뷰 인용, 저자 소개 등 비정형 내용 혼재 |
| Profiler polarity=negative 활용 | 채택 (낮은 평점 리뷰도 입력에 포함) | **GAP-2 검증**: rating ≤ 2 보유 사용자 64.2%, ≤ 3 보유 81.6%로 비선호 신호 추출 가능성 충분 |
| Transfer Gate **PARTIAL** 판정 필수성 | 채택 (3단계 유지) | **GAP-1 검증**: Movies-Books 동일 명칭 직접 매칭 0건. 도메인 간 카테고리 분류 체계가 달라 **PARTIAL 매핑이 데이터상 본질적 필요** |
| HR@K/NDCG@K 평가 공정성 | 단순 baseline 차단 확인 | **GAP-4 검증**: GT vs Negative 평점 차이 0.15, 카테고리 분포 유사 → 패턴 매칭 능력 측정으로 의미 있게 작용 |

---

## 4. Pilot Study: Core Pattern 도출

### 4.1 목적
7개 Core Pattern의 선정 근거를 4가지 측면(이론·Pilot·CDR·직교) 종합 검토로 확보한다.

### 4.2 샘플 규모 근거
- Train set 800명 중 **100명** 무작위 샘플링 (12.5%)
- 100명 근거: LLM4CDR (RecSys 2025) Pilot norm 동일 수준. 패턴 빈도 분포의 안정성 확보를 위한 최소 규모
- 실제 비용: $0.081 (GPT-4o-mini, 2026-04 실행)

### 4.3 절차 (실제 수행)

1. Train set에서 **100명** 무작위 샘플링 (seed=42)
2. GPT-4o-mini에게 자유 추출 prompt로 패턴 추출 (`prompts/pilot_profiler_prompt.md`) — 100명 × 평균 8개 = **806개 raw 패턴**
3. **HDBSCAN 클러스터링으로 391 canonical 도출**:
    - 각 패턴의 **"이름 + ': ' + 설명" 텍스트**를 `sentence-transformers all-MiniLM-L6-v2`로 384차원 임베딩 (L2 normalized)
    - HDBSCAN 파라미터: `min_cluster_size=3`, `min_samples=1`, `cluster_selection_epsilon=0.15`, normalized 벡터에 대해 euclidean = cosine 거리
    - 각 군집에서 **빈도(n_users) 최고 멤버**를 canonical로 자동 선정 (데이터 기반, 사람 결정 X)
    - 군집 미형성 단독 패턴(노이즈)은 개별 canonical로 보존
    - 이름만 아니라 설명까지 임베딩하여 같은 이름·다른 의미 패턴 분리 (robust 정규화)
4. 이론 anchor(Thet et al. 2010, Liu 2012)에서 도출한 6개 후보의 영문 정의 텍스트를 동일 임베딩 모델로 벡터화 → 391 canonical과 6×391=2,346쌍 cosine similarity 자동 매칭
5. 4가지 측면 종합 검토 → 7개 확정 (Pilot에서 emerge한 emotional_resonance 추가)

### 4.4 산출물
- `data/pilot_users.parquet`, `pilot_outputs/user_*.json` × 100
- `data/pilot_patterns_canonical.parquet` (391 canonical)
- `data/pilot_to_predefined_matching.csv`, `pilot_pattern_categories.csv`, `pilot_pattern_orthogonality.csv`
- `data/pilot_decision_table.csv`, `pilot_summary_metrics.json`
- 시각화: `pilot_pattern_frequency.png`, `pilot_categories_summary.png`, `pilot_pattern_orthogonality.png`
- 보고서: `docs/Pilot_Study_Report.md`, `docs/TransferJudge_Pilot_Report_v3.pdf`

### 4.5 채택된 7개 Core Patterns (Pilot 검증 결과)

| Pattern | 설명 | Transfer Gate | Pilot sim |
|---------|------|:---:|:---:|
| genre_preference | 선호 장르/카테고리 | TRANSFER | 0.70 |
| narrative_complexity | 서사 복잡도 선호 수준 | TRANSFER | 0.80 (직접) |
| pacing_preference | 전개 속도 선호 | TRANSFER | 0.81 |
| quality_sensitivity | 품질 민감도 | PARTIAL | 0.55 |
| brand_loyalty | 특정 브랜드/제작자 충성도 | BLOCK 후보 | 0.70 |
| sensory_preference | 감각적 경험 선호 | BLOCK 후보 | 0.59 |
| **emotional_resonance** ★ | 감정적 울림·여운 (Pilot 도출) | TRANSFER | 0.82 (직접) |

★ = Pilot Study에서 강하게 emerge한 패턴 (14% 빈도, 직접 매칭)

### 4.6 Pilot 검증 핵심 결과
- **사전 검토 5/5 통과** (Pilot 발현·자유 추출 한계·직교성·BLOCK 식별·emotional 매칭)
- **자유 추출의 한계 정량 확인**: 391 canonical 中 90.8%가 비-CDR-적합 → 명시 prompt 설계 정당화
- **직교성 max 0.669** (≤ 0.7) → 7개 의미적 독립 확보
- **Movies-only 키워드 자동 검출**: brand_loyalty(actor·director), sensory_preference(cinematograph) → BLOCK 후보 자동 식별

---

## 5. Profiler 구현

> 전체 설계 상세: [`prompts/profiler_prompt.md`](prompts/profiler_prompt.md) · 실행 스크립트: [`scripts/run_profiler.py`](scripts/run_profiler.py)

### 5.1 모델 및 설정

| 항목 | 설정 | 근거 |
|------|------|------|
| LLM | GPT-4o-mini | 비용 효율 + 텍스트 분석 태스크 적합성 |
| 방식 | 프롬프트 기반 (파인튜닝 없음) | Profiler는 범용 언어이해 능력 범위 |
| `temperature` | `0.0` | 재현성 |
| `seed` | `42` | 추가 재현성 |
| `response_format` | `{"type": "json_object"}` | JSON mode 강제 |
| `max_tokens` | `1500` | P95 출력(~1,200) + 여유 |
| Input 토큰 (실측) | mean **~2,900** / P95 **~11,000** | 15~30 리뷰 × 80.4/343 tokens |
| Output 토큰 (실측) | mean **~800** / P95 **~1,400** | Core 7 + Additional 3 + summary |
| 128K context 사용률 | 평균 **2.3%**, P95 **9.5%** | 충분한 여유 |

#### LLM 선정 근거: 왜 GPT-4o-mini인가?

| 선정 기준 | 설명 |
|----------|------|
| **태스크 특성** | 텍스트 분석(Analytical) — 범용 LLM의 언어 이해 능력 범위 내로 파인튜닝 불필요 |
| **API vs 로컬** | 파인튜닝이 불필요하므로 API 호출이 가장 효율적 (인프라 불필요) |
| **비용 효율** | GPT-4o-mini: $0.15/1M input, $0.60/1M output — 1,000명 처리 시 **~$0.86** (예산 $1~2 내) |
| **성능 충분성** | 리뷰 텍스트에서 선호 패턴을 추출하는 것은 요약/분류 태스크의 변형으로, GPT-4o-mini 수준에서 충분한 품질 달성 가능 |
| **재현성** | 상용 API 모델은 동일 프롬프트에 대해 일관된 출력 → 실험 재현성 확보 |

### 5.2 프롬프트 설계 (확정)

**입력 범위**: **Source 도메인(Movies & TV) 리뷰만** 사용. Target(Books) 리뷰는 **Profiler 입력에서 제외**되며, 이는 Cold-Start의 이론적 극한을 시뮬레이션하는 엄격한 평가 조건을 반영한 결정이다.

**출력 스키마 (JSON, strict)**:

```json
{
  "user_id": "<string>",
  "core_patterns": {
    "genre_preference":       {"value": "...", "evidence": ["..."], "confidence": 0.0-1.0, "polarity": "positive|negative|mixed", "transferability_hint": "high|medium|low"},
    "narrative_complexity":   {...},
    "pacing_preference":      {...},
    "quality_sensitivity":    {...},
    "brand_loyalty":          {...},
    "sensory_preference":     {...}
  },
  "additional_patterns": [ ... 최대 3개 ],
  "summary": "<2-3 sentence overall taste summary>"
}
```

**스키마 설계 원칙**:

| 필드 | 역할 | 이유 |
|------|------|------|
| `evidence` | 원문 인용 배열 (최대 2개) | Hallucination 방지, 검증 가능성 |
| `confidence` ∈ [0.0, 1.0] | 패턴 강도 | Judge가 약한 신호 필터링 가능 |
| `polarity` ∈ {positive, negative, mixed} | 극성 | 낮은 평점 리뷰의 "비선호" 정보 활용 |
| `transferability_hint` ∈ {high, medium, low} | Books 전이 가능성 초기 추정 | Judge의 최종 판단에 참고 (힌트만) |
| `additional_patterns` (최대 3개) | Semi-Structured 영역 | Pilot의 long-tail 패턴 보존 |

**User Message 템플릿** (최신순 정렬 15~30개 리뷰):
```
User ID: {user_id}

=== Source Domain (Movies & TV) Reviews ===

[Review 1] Rating: {rating}/5.0 | Title: "{review_title}"
"{review_text}"
...

=== Instruction ===
Analyze the above {N} reviews and extract the user's preference patterns following the schema.
Output valid JSON only.
```

### 5.3 실행 계획 및 오류 처리

| 단계 | 내용 |
|------|------|
| 대상 | 1,000명 (Train 800 + Valid 100 + Test 100) |
| 비용 | **~$0.86** (예산 $1~2 내) |
| 저장 | `profiler_outputs/user_{id}.json` |
| Resume 지원 | 이미 처리된 user_id.json 자동 스킵 (재실행 시 비용 절약) |
| JSON 파싱 실패 | temperature를 0.1씩 올려 최대 3회 재시도 |
| 스키마 위반 | 7개 Core Pattern 누락 시 재시도 |
| Rate Limit | Exponential backoff (1 → 2 → 4 → 8s), 최대 5회 |
| 저품질 출력 | confidence 평균 < 0.3이면 경고 로그 (Judge가 신뢰도 활용) |

### 5.4 Pilot Study 품질 검증

1. **수동 검토 (30명)**: 높은 confidence 패턴이 실제 리뷰 증거와 일치하는지 확인
2. **자동 검증**: 7 core_patterns 키 존재율 100%, evidence 비공백 비율 95%+
3. **일관성 검증**: 동일 사용자 2회 실행 시 패턴 값 cosine 유사도 0.85+
4. **Long-tail 분석**: additional_patterns 빈도 집계 → Core 7개 외 후보 패턴 발굴 (논문 Appendix)

### 5.5 Profiler Input / Output 구체 예시 (라인별 주석)

**Input (Source 리뷰 — 최신순 15~30개 발췌):**

```
[Review 1] Rating: 5/5 | "Another brilliant Nolan epic, the time-loop structure was genius"
   ↑                ↑                    ↑                              ↑
   리뷰 번호    별점(5점=강한 긍정)   감독 충성도 신호           복잡한 서사 선호 신호

[Review 2] Rating: 5/5 | "Cinematography alone makes this a masterpiece"
                                  ↑
                          영상미 중시 → sensory_preference 신호 (영화 매체 한정)

[Review 3] Rating: 2/5 | "Generic rom-com, predictable and boring"
                ↑                ↑                   ↑
            낮은 점수도 사용 (싫어하는 장르 신호)   rom-com 비선호    단순한 서사 비선호

[Review 4] Rating: 4/5 | "Slow-burn but rewarding character study"
                                  ↑
                          느린 전개 선호 → pacing_preference 신호

... (총 15~30개, 토큰 예산 ~2,400 tokens)
```

**Input 핵심 포인트**:
- **최신순 정렬** — 최근 취향이 더 정확. Review 1이 가장 최근.
- **전체 평점 사용 (1~5점)** — 낮은 평점도 "싫어하는 것"의 정보. GT만 4점 이상 제한.
- **제목 + 본문 모두 포함** — 짧은 제목에도 강한 감정 신호 ("masterpiece", "boring") 존재.

**Output (Profiler가 추출한 JSON 일부):**

```jsonc
{
  "core_patterns": {
    "narrative_complexity": {                          // ← 7개 패턴 중 하나
      "value": "Strongly prefers complex, multi-layered narratives",
      "evidence": ["Review 1: 'time-loop structure was genius'"],
                  // ↑ 원문 인용 — 패턴이 데이터에 근거함을 증명 (hallucination 방지)
      "confidence": 0.85,                              // ← 0~1, 값이 클수록 강한 신호
      "polarity": "positive",                          // ← 좋아함/싫어함/혼합
      "transferability_hint": "high"                   // ← Books 도메인으로 전이 쉬움 힌트
    },
    "brand_loyalty": {
      "value": "Strong loyalty to Christopher Nolan",
      "confidence": 0.80,
      "polarity": "positive",
      "transferability_hint": "low"                    // ← ★ 영화감독은 책에 매핑 어려움
                                                       //   → Judge에게 "BLOCK 후보" 신호
    }
    // genre_preference, pacing_preference, quality_sensitivity, sensory_preference ...
    // (총 7개 Core + 추가 패턴 최대 3개)
  },
  "summary": "Sophisticated viewer preferring complex, slow-burn narratives..."
                  // ↑ 사람이 한눈에 이해 가능한 2~3문장 요약 (Judge의 추가 컨텍스트)
}
```

**Output 핵심 포인트**:
- **evidence (원문 인용)**: Profiler가 "왜 이 패턴이라 판단했는지" 증거. Judge·심사위원 검증 가능.
- **confidence (신뢰도 0~1)**: 약한 신호 패턴은 Judge가 필터링하거나 비중 낮춤.
- **polarity (극성)**: positive(선호) / negative(비선호) / mixed. "싫어하는 장르"도 추천 회피에 활용.
- **transferability_hint**: Profiler가 주는 초기 힌트일 뿐, **최종 TRANSFER/PARTIAL/BLOCK 판정은 Judge가 결정**.

---

## 6. Teacher Distillation: 학습 데이터 생성

> 전체 설계 상세: [`prompts/teacher_prompt.md`](prompts/teacher_prompt.md) · 실행 스크립트: [`scripts/run_teacher.py`](scripts/run_teacher.py)

### 6.1 목적
Transfer Judge 파인튜닝을 위한 SFT 학습 데이터를 GPT-4o-mini Teacher로 생성한다.

### 6.2 왜 Teacher Distillation인가? — 방법론적 정당성

#### 문제: 학습 데이터가 존재하지 않는다
Transfer Gate의 3단계 판정(TRANSFER/PARTIAL/BLOCK)은 본 연구가 새롭게 정의한 태스크이므로, 기존에 레이블링된 데이터셋이 존재하지 않는다. 따라서 학습 데이터를 확보하는 방법은 다음 3가지 중 하나이다:

| 대안 | 장점 | 한계 | 적합성 |
|------|------|------|--------|
| **(A) 수동 레이블링** | 정확도 최고 | 800건 × 6~9패턴 = 5,000건+ 판정 필요, 비현실적 비용 | ✗ |
| **(B) Teacher Distillation** | 비용 효율적, 일관성 높음, 대규모 생성 가능 | Teacher 품질에 의존 | **✓ 채택** |
| **(C) Self-Training** | Teacher 불필요 | 초기 품질 매우 낮음, 수렴 불안정 | ✗ |

#### 선행연구 근거
- **Knowledge Distillation 패러다임**: 대형 Teacher LLM이 생성한 합성 데이터로 소형 Student 모델을 학습시키는 것은 NLP에서 확립된 방법론이다 (Hinton et al. 2015). 최근 LLM 시대에서는 GPT-4급 모델이 생성한 합성 데이터로 소형 모델을 파인튜닝하는 것이 표준 관행이다.
- **TALLRec (RecSys 2023)**: LoRA 파인튜닝 시 50건 미만의 학습 데이터만으로도 추천 능력 달성을 보고 — 본 연구의 700건은 이에 비해 충분한 규모.
- **Chain-of-Thought Distillation**: Teacher가 rationale(판정 이유)을 포함한 출력을 생성하고, Student가 이를 학습하면 단순 레이블만 학습하는 것보다 일반화 성능이 향상된다 (Wei et al. 2022).

#### Teacher에게 GT를 제공하는 이유
> Teacher에게 GT를 제공하는 것은 **정답 암기가 아니라 올바른 판정 과정(rationale) 시연을 위함**이다. GT를 알려주면 Teacher는 "이 아이템이 추천되어야 하는 이유"를 역추론하여, 어떤 패턴이 TRANSFER이고 어떤 것이 BLOCK인지를 일관성 있게 판정할 수 있다. Student는 "패턴을 어떻게 판정하고 추천 근거를 어떻게 구성하는지"라는 **과정(process)**을 학습하며, 추론 시에는 GT 없이 수행된다.

### 6.3 Transfer Gate 3-Level 판정 기준 (프롬프트 확정)

| Level | 기준 | 예시 |
|-------|------|------|
| **TRANSFER** | 패턴이 도메인 독립적(medium-agnostic)이어서 Books에 그대로 적용 가능 | `narrative_complexity: complex` → 복잡한 서사 구조의 책 / `pacing_preference: slow` → 느린 전개 소설 |
| **PARTIAL** | 패턴이 부분적 전이 가능하나 도메인 간 의미 조정 필요 | `genre_preference: sci-fi movies` → sci-fi 책 (트로프 차이, 비중 축소) |
| **BLOCK** | 패턴이 medium-specific이거나 부정 전이 위험 | `sensory_preference: IMAX visuals` (책에 부재) / `brand_loyalty: Christopher Nolan (director)` (감독 = 작가 아님) |

### 6.4 Few-Shot 예시 설계 (System Prompt에 포함)

Teacher System Prompt에 3가지 대표 케이스 예시 포함 → Chain-of-Thought 학습 데이터 생성의 일관성 확보:

| 예시 | 특징 | 커버 범위 |
|------|------|-----------|
| **Example 1: TRANSFER-heavy** | 철학적 사용자 + Nolan 충성도. 대부분 TRANSFER, 감독·IMAX만 BLOCK | 도메인 독립적 패턴의 모범 |
| **Example 2: BLOCK-heavy** | 액션·Statham 팬. 감각·배우 충성도 BLOCK, 장르·페이스만 PARTIAL/TRANSFER | medium-specific 제거 시연 |
| **Example 3: PARTIAL-mixed** | 혼합 취향, 약한 신호. 대부분 PARTIAL 판정 | 저신뢰도 처리 모범 |

### 6.5 절차

1. **입력 준비**: Profiler Output + 후보 50개 (GT 1개 + Negative 49개 shuffle) + GT 힌트
2. **Teacher 실행**: GPT-4o-mini에 전이 판정 + Top-10 추천 생성 요청
3. **품질 필터링** (5단계, 자동 검증):

| 단계 | 검사 항목 | 위반 시 조치 |
|------|----------|--------------|
| **① 형식** | JSON 파싱 성공 | temperature 0.1씩 올려 최대 3회 재시도 |
| **② 완전성** | 7 core patterns + 10 recommendations 존재 | 재시도 |
| **③ BLOCK 누출** | BLOCK 판정 패턴이 `applied_patterns`에 미포함 | 샘플 배제 (Transfer Gate 설계 원칙 위반) |
| **④ GT 텍스트 누출** | `rationale`/`reasoning`에 GT title·item_id 미등장 | 샘플 배제 (leakage 방지) |
| **⑤ GT Top-10 포함** | GT가 Top-10 recommendations에 포함 | `train.jsonl`에서 제외 (`teacher_outputs/`에는 저장) |

4. **필터링 통과율 목표**: **87.5% 이상** (800명 → 700건 이상 확보)
5. **저장**: `data/train.jsonl` (학습용, GT 제거 SFT 포맷) / `teacher_outputs/user_{id}.json` (원본)

#### 품질 필터링이 충분한 이유
- **형식 + 완전성**: JSON 구조와 필수 필드 존재를 기계적으로 검증 가능
- **BLOCK 누출 검사**: Transfer Gate의 핵심 설계 원칙(BLOCK 패턴은 추천 근거로 활용 금지) 자동 검증
- **GT 텍스트 누출 검사**: Student 학습 시 GT 정보가 입력에 섞여들어가는 leakage 원천 차단
- **GT Top-10 포함**: Teacher가 전이 판정을 잘못 수행한 출력은 배제. "올바른 판정 → 올바른 추천" 파이프라인 가정 검증
- **일관성 검사** (Pilot 10명): 동일 사용자 2회 실행 시 판정 일치율 90% 이상 확인 후 본실행 진행

### 6.6 학습 데이터 형식 (SFT, GT 제거)

Student 학습 시 GT hint는 **user_message와 system_prompt 양쪽에서 완전히 제거**된다:

```json
{
  "messages": [
    {"role": "system", "content": "<Transfer Judge system prompt (GT calibration 섹션 제거)>"},
    {"role": "user", "content": "=== USER PROFILE === ... === CANDIDATES === ... (GT hint 없음)"},
    {"role": "assistant", "content": "<Teacher가 생성한 JSON (validated)>"}
  ]
}
```

→ `scripts/run_teacher.py`의 `to_sft_record()`가 자동 변환

### 6.7 비용 및 토큰 예산 (실측)

| 항목 | 값 |
|------|----|
| 평균 input | **~7,700 tokens/user** (System 3,000 + Profile 800 + Candidates 3,700 + 기타 200) |
| 평균 output | **~1,500 tokens/user** (decisions 640 + recommendations 600 + 요약 100) |
| 128K context 사용률 | 평균 **7.2%**, P95 **8.8%** |
| 800명 총 비용 | **~$2.0** (예산 $2~3 내) |

### 6.8 Transfer Judge Input / Output 구체 예시 (라인별 주석)

> 본 섹션은 **Teacher가 생성하고, Student가 모방 학습할** Input/Output 형식을 보여준다.

**Input (Profiler Output + 후보 50개 일부):**

```jsonc
{
  "user_profile": { "core_patterns": { /* §5.5의 Profiler 출력 그대로 */ } },
  // ↑ Profiler가 추출한 7개 패턴 JSON을 통째로 입력 (구조화된 사용자 프로파일)

  "candidates": [
    {"id": "B002", "title": "Cloud Atlas", "author": "David Mitchell",
     "categories": "Literary Fiction", "rating": 4.0,
     "synopsis": "Six nested timelines spanning centuries..."},
    // ↑ 후보 1개 정보: 제목 + 저자 + 카테고리 + 평균평점 + 줄거리 첫 50 토큰
    //   Judge가 패턴 매칭 판단할 수 있도록 충분한 정보 제공

    {"id": "B045", "title": "Nolan biography", "author": "T. Shone",
     "categories": "Biography", "rating": 4.2, "synopsis": "..."},
    // ↑ ★ 함정 케이스: "Nolan"이라는 이름이 들어 있지만 저자는 다름
    //   사용자가 영화감독 Nolan의 팬이라고 해서 이 책을 추천하면 Negative Transfer

    /* ... 총 50개: GT 1개 + 사용자가 구매하지 않은 Books 무작위 49개 shuffle ... */
  ]
}
```

**Input 핵심 포인트**:
- **Profiler 출력을 그대로 입력** — 두 LLM이 JSON 스키마를 공유하여 정보 손실 없음.
- **후보당 5개 필드** — 제목·저자·카테고리·평점·줄거리. Judge의 패턴별 매칭 근거.
- **shuffle 후 입력** — GT 위치 노출 방지 (LOO 평가 시에도 동일).

**Output (transfer_decisions + Top-10):**

```jsonc
{
  "transfer_decisions": {
    "narrative_complexity": {"decision": "TRANSFER",
                                          // ↑ 패턴이 책에도 그대로 적용 가능
       "rationale": "Multi-layered storytelling is medium-agnostic.",
                  // ↑ 왜 TRANSFER인지 설명 (Chain-of-Thought 학습용)
       "confidence": 0.90},

    "brand_loyalty": {"decision": "BLOCK",
                                  // ↑ ★ 핵심 — 영화감독 충성도는 책에 전이 불가
       "rationale": "Nolan is a film director, not an author.",
                  // ↑ "Nolan biography"를 추천에서 제외할 이유
       "confidence": 0.95},

    "sensory_preference": {"decision": "BLOCK",
       "rationale": "IMAX cinematography is film-specific.",
                  // ↑ 영상미는 책에 존재하지 않음 → 매체 특화 패턴
       "confidence": 0.95}
    // genre_preference: PARTIAL (장르 매핑 필요),
    // pacing_preference: TRANSFER (페이싱은 책에도 존재) ...
  },

  "recommendations": [
    {"rank": 1, "item_id": "B002", "title": "Cloud Atlas", "score": 0.92,
                              // ↑ 후보 50개 중 1위로 추천 (점수 0~1)
     "applied_patterns": ["narrative_complexity", "pacing_preference"],
     // ↑ ★ 이 책을 추천한 근거 패턴들 — BLOCK 패턴은 절대 들어가지 않음
     //   (만약 brand_loyalty가 여기 있으면 학습 데이터에서 자동 배제: §6.5 5단계 필터)

     "reasoning": "Six nested timelines match preference for complex narratives."}
                // ↑ 사람이 읽을 수 있는 추천 근거 (rationale의 추천 버전)

    /* rank 2~10 (총 10개 추천)
       주의: "Nolan biography(B045)"는 평점 4.2로 높지만 BLOCK 판정으로 Top-10 진입 못함 */
  ]
}
```

**Output 핵심 포인트 — 왜 이게 Transfer Gate의 가치인가?**:
- **"Nolan biography"는 평점 4.2 (높음)**이지만 BLOCK 판정으로 추천에서 **자동 제외**.
- 단순 평점·인기도 기반 추천이라면 이 책이 추천될 가능성이 있음 → Negative Transfer 발생.
- Transfer Judge는 사용자의 "Nolan 충성도"가 **영화 한정**임을 인식하고 책에는 적용 안 함.
- 이것이 본 연구의 핵심 가설: **BLOCK이 추천 품질을 높인다**.

### 6.9 학습 데이터 구축 프로세스 — 가상 사용자 A를 따라가며 이해하기

> Train 사용자 1명("사용자 A")의 데이터가 어떻게 학습 데이터 1줄로 만들어지는지 단계별로 추적.
> 이 과정을 800명 모두에 반복 → ~700건의 train.jsonl 구축.

**👤 가상 사용자 A — Train 800명 中 1명**
- **Movies&TV 리뷰 22개** (다양한 평점)
  - Review 1 (5점, 최근): "Another brilliant Nolan epic..."
  - Review 2 (5점): "Cinematography alone makes this a masterpiece"
  - ... (총 22개)
- **Books 리뷰 6개**
  - 2019: "Foundation" rating 3
  - 2020: "Dune" rating 4
  - **2023: "Cloud Atlas" rating 5 ← ★ 가장 최근 4점 이상**
  - ... (총 6개)

**↓**

**① GT 분리 (Books 리뷰에서 정답 1건 추출)**
- **규칙**: rating ≥ 4 중 가장 최근 1건 → **"Cloud Atlas" (B002)** 선정
- **왜**: Teacher의 판정 품질을 검증할 정답으로 사용. "이 책이 Top-10에 들어가야 학습 데이터로 인정"
- **저장**: 다음 단계의 input/output에서 별도 변수로 보관

**↓**

**② 후보 50개 구성**
- **구성**: GT "Cloud Atlas" 1개 + 사용자 A가 구매하지 않은 Books 49개 무작위 샘플 = 50개
- **shuffle 결과 (예)**: `[B045 Nolan biography, B002 Cloud Atlas, B091 Foundation, ...]`
- **왜 50개**: 너무 적으면 천장 효과, 너무 많으면 토큰 초과 (§2.4 근거)
- **왜 shuffle**: Teacher가 위치 단서로 GT를 찾지 못하게

**↓**

**③ Profiler 실행 (GPT-4o-mini API)**
- **입력**: Movies&TV 리뷰 22개 텍스트 전체 (Books 리뷰는 ❌ 제외 — Cold-Start 시뮬레이션)
- **출력 (요약)**:
  ```
  narrative_complexity: complex multi-layered, confidence 0.85
  brand_loyalty:        Christopher Nolan,      confidence 0.80
  sensory_preference:   IMAX cinematography,    confidence 0.70
  // genre_preference, pacing_preference, quality_sensitivity ...
  ```
- **왜**: Source 리뷰의 다양한 신호를 7개 구조화 패턴으로 추출 → Judge가 후보별 판단할 근거

**↓**

**④ Teacher 실행 (GPT-4o-mini API, GT 힌트 포함)**
- **입력**: Profile(③의 출력) + 후보 50개(②) + **GT 힌트: "Cloud Atlas" (B002)**
- **출력 (요약)**:
  ```
  transfer_decisions:
    narrative_complexity:  TRANSFER  // 책에 그대로 적용 가능
    brand_loyalty:         BLOCK     // Nolan은 영화감독, 책엔 안 맞음
    sensory_preference:    BLOCK     // IMAX는 책에 없음
  recommendations:
    rank 1: B002 "Cloud Atlas" — applied: [narrative_complexity, pacing_preference]
    // rank 2~10 (B045 Nolan biography는 BLOCK으로 추천에서 제외)
  ```
- **왜 GT 힌트?**: Teacher가 "이 책이 추천되어야 한다"는 결과를 알고, 거기에 도달하는 **올바른 판정 과정**을 시연하기 위함. Student는 이 과정을 학습.

**↓**

**⑤ 5단계 품질 필터 (자동 검증)**
1. 형식: JSON 파싱 OK ✅
2. 완전성: 7개 패턴 + 10개 추천 모두 존재 ✅
3. **BLOCK 누출**: recommendations의 applied_patterns에 brand_loyalty/sensory_preference 등장? ❌ → 통과 ✅
4. **GT 텍스트 누출**: rationale·reasoning에 "Cloud Atlas" 직접 언급? ❌ → 통과 ✅
5. **GT Top-10 포함**: "Cloud Atlas"가 rank 1 → 통과 ✅
- **5/5 통과 → 학습 데이터로 채택**

**↓**

**⑥ SFT 형식 변환 (GT 정보 완전 제거 후 train.jsonl에 1줄 append)**

```jsonc
{"messages": [
  {"role": "system",    "content": "You are a Cross-Domain Transfer Judge..."},
  // ↑ system 프롬프트에서 "GT 힌트" 관련 문구 모두 삭제

  {"role": "user",      "content": "Profile: {...} + Candidates: [...]"},
  // ↑ 사용자 입력에서도 GT 힌트 라인 삭제 (Student는 GT를 평생 모름)

  {"role": "assistant", "content": "{transfer_decisions, recommendations}"}
  // ↑ Teacher가 만든 정답 JSON 그대로 (Student가 모방할 목표)
]}
```

- **왜 GT 제거?**: Student(QLoRA Qwen3-14B)는 추론 시 GT를 절대 보지 않는다. 학습 시에도 같은 조건이어야 일관성 확보.

> **Figure 요약**: 가상 사용자 A 1명 → train.jsonl 1줄. 이 과정을 800명 모두 반복 → ~700건 (87.5%+ 통과율)

**이 walk-through에서 꼭 이해해야 할 3가지**:
1. **GT의 두 가지 역할** — Teacher의 "정답 시연용"(④) + 품질 필터의 "검증용"(⑤). 둘 다 학습 데이터에는 들어가지 않음.
2. **BLOCK이 가치 있는 이유** — "Nolan biography"가 평점 4.2로 높지만 brand_loyalty BLOCK으로 추천에서 제외(④). 이것이 Negative Transfer 방지.
3. **Student의 학습 목표** — Student는 ⑥의 user입력만 보고 ⑥의 assistant출력을 만들어내야 함. GT 힌트 없이도 동일한 추론을 하도록 학습.

### 6.10 800명 → train.jsonl 전체 통계 흐름

| 단계 | 800명 적용 결과 |
|------|------|
| 0. 입력 | Train 800명 (각자 Source 15~30개 + Target 5~10개 리뷰) |
| ① GT 분리 | 800명 모두 rating ≥ 4 보유 (EDA 99.6% + 샘플링 후 100%) → **800건** |
| ② 후보 50개 | 800명 × 50개 = 40,000개 후보 (각자 다른 후보 셋, seed=42) |
| ③ Profiler | 800회 API 호출, ~$0.7 |
| ④ Teacher | 800회 API 호출, ~$2.0 |
| ⑤ 5단계 필터 | 예상 통과율 87.5%+ → **~700건** |
| ⑥ train.jsonl | **~700줄의 SFT 학습 데이터** → Qwen3-14B QLoRA 파인튜닝 입력 |

---

## 7. Transfer Judge QLoRA 파인튜닝

### 7.1 모델 선택 전략

#### LLM 선정 근거: 왜 Qwen3-14B-Instruct인가?

| 선정 기준 | 설명 |
|----------|------|
| **태스크 특성** | 도메인 간 의미 매핑(Judgmental) — 범용 LLM이 사전학습에서 학습하지 않은 능력이므로 파인튜닝 필수 |
| **오픈소스 필수** | QLoRA 파인튜닝을 위해 모델 가중치 접근이 필요 → 오픈소스 모델만 가능 (GPT 계열 사용 불가) |
| **Instruct 튜닝** | JSON 구조화 출력 + 복잡한 지시문 이해가 필요 → 기본 Instruct 튜닝이 완료된 모델이어야 추가 파인튜닝 효율적 |
| **벤치마크 성능** | Qwen3-14B는 14B급 오픈소스 LLM 중 최상위: MMLU 81.05, MMLU-Pro 61.03, BBH 81.07 (Qwen3 Technical Report, 2025) |
| **복잡 추론 능력** | MMLU-Pro 61.03으로 동일 파라미터 Qwen2.5-14B(51.16) 대비 +9.9%p — TRANSFER/PARTIAL/BLOCK 3단계 판정에 요구되는 복잡 추론에 직접적 이점 |
| **라이선스** | Apache 2.0 — 학술 연구 및 상업적 사용 모두 자유 |
| **대안 비교** | LLaMA-3: 8B→70B 점프로 14B급 비교 불가. Mistral: 7B만 존재하여 스케일 ablation 불가. Gemma-3-12B: MMLU-Pro 44.91로 Qwen3-14B(61.03) 대비 열위 |

| 항목 | Qwen3-14B-Instruct |
|------|---------------------|
| VRAM (QLoRA 4-bit) | ~18GB |
| GPU | A100 / L40S |
| 학습 시간 | 4~8시간 |
| 비용 | ~$15~30 |

### 7.2 QLoRA 하이퍼파라미터

| 항목 | 설정값 |
|------|--------|
| 양자화 | 4-bit (NF4) |
| LoRA Rank / Alpha | 64 / 128 |
| Dropout | 0.05 |
| 학습률 | 2e-5 (cosine scheduler, warmup 3%) |
| 배치 | per_device=2, gradient_accumulation=8 (effective=16) |
| Epoch | 3~5 (validation loss 기반 early stopping) |
| 최대 시퀀스 길이 | 4,096 tokens |

### 7.3 학습 체크리스트

- [ ] 환경 설정 (transformers, peft, bitsandbytes, trl)
- [ ] 데이터 로드 및 토크나이저 적용
- [ ] QLoRA 설정 + 모델 로드
- [ ] Training 실행 + validation loss 모니터링
- [ ] Best checkpoint 저장
- [ ] 추론 테스트 (5명 샘플)

---

## 8. Transfer Gate 3단계 판정 근거

### 8.1 왜 3단계(TRANSFER / PARTIAL / BLOCK)인가?

| 대안 | 한계 |
|------|------|
| **2단계 (Transfer/Block)** | "영상미 중시 → 묘사력 중시"처럼 변환하면 유용한 패턴까지 버리게 됨 (정보 손실) |
| **연속적 가중치 (0~1 스코어)** | 해석이 어렵고, 추천 rationale에 "이 패턴을 0.6만큼 반영했다"라고 쓸 수 없음 |
| **4단계 이상** | 판정 기준 모호 + LLM 일관성 저하 + 각 등급에 학습 데이터 부족 |
| **3단계 (본 연구)** | "그대로 쓴다 / 변환해서 쓴다 / 안 쓴다" — 의사결정의 자연스러운 최소 분류 |

### 8.2 선행연구 근거

기존 연구에서 negative transfer의 원인과 강도가 다층적임은 이미 인식되어 왔다.

| 논문 | 학회 | Multi-Level 체계 | 본 연구와의 관계 |
|------|------|-----------------|----------------|
| Zhang & Wu, "A Survey on Negative Transfer" | IEEE/CAA JAS 2023 | NT 완화 접근을 Domain/Instance/Feature **3단계**로 분류 | transferability를 계층적으로 판단해야 한다는 이론적 근거 |
| TrineCDR | KDD 2024 | NT 원인을 Feature/Interaction/Domain **3 level**로 분류 | multi-level 원인 → multi-level 판정 필요라는 직접적 동기 |
| Wang et al. | CVPR 2019 | NT의 **3가지 요인** 식별 + gate 기반 filtering | gate 메커니즘으로 유해 지식 차단의 방법론적 선례 |
| SAN (Cao et al.) | CVPR 2018 | Binary(transfer/block) selective transfer | 2단계 한계 → PARTIAL 확장 필요성의 근거 |
| FedGCDR | NeurIPS 2024 | Soft/Hard NT 2유형 구분 | NT에도 강도 차이가 있다는 근거 |
| Park et al. | CIKM 2023 | Shapley value 연속 가중치 기반 전이 조절 | 연속 가중치 → 이산 판정으로의 발전 선례 |

### 8.3 포지셔닝

> 기존 연구에서 negative transfer의 원인과 강도가 다층적임은 이미 인식되어 왔다 (Zhang et al. 2023; TrineCDR 2024). 그러나 이를 실제 전이 판정에 반영하여 이산적 multi-level decision (TRANSFER/PARTIAL/BLOCK)으로 구현한 연구는 본 연구가 최초이다. 기존의 binary 접근(SAN 2018; RTNet 2020)은 변환하면 활용 가능한 패턴까지 차단하는 정보 손실 문제가 있으며, 연속적 가중치 접근(Park et al. 2023)은 해석이 어렵고 추천 근거(rationale)에 반영할 수 없다.

### 8.4 검증 계획

Ablation으로 3단계의 기여를 검증한다:
- **2단계 vs 3단계**: PARTIAL 판정을 모두 TRANSFER로 통합한 조건과 비교 → PARTIAL 등급의 독립적 기여도 측정
- 이는 기존 Ablation 조건 (d)의 변형으로 추가 비용 없이 구현 가능

---

## 9. Ablation Study: 6개 실험 조건

### 9.1 전체 조건 정의

| 조건 | 구성 | 검증 목적 |
|------|------|----------|
| **(a) Single LLM** | 단일 프롬프트로 전체 수행 | 베이스라인 (LLM4CDR 재현) |
| **(b) Profiler-Judge (Prompt)** | Profiler(P) + Judge(P) 모두 프롬프트 기반 | 구조 분리만의 효과 |
| **(c) Profiler-Judge (FT) ★Ours** | Profiler(P) + Judge(QLoRA) | 파인튜닝 추가 효과 |
| **(d) Profiler-Judge w/o Gate** | Profiler(P) + Judge(FT), 모든 패턴 TRANSFER 강제 | Transfer Gate 효과 |
| **(e) 전통 CDR 베이스라인** | 비LLM 임베딩 기반 CDR (CoNet 등) | LLM 접근의 우위 |
| **(f) Raw Review Input** | Profiler 생략, Judge(FT)에 raw review 직접 입력 | RQ1: 구조화 프로파일 효과 |

### 9.2 조건별 구현 노트

**(a) Single LLM**
- GPT-4o-mini 1개로 리뷰 분석 + 전이 판단 + 추천 생성을 한 번에 수행
- LLM4CDR 논문의 프롬프트 구조 참고

**(b) Profiler-Judge (Prompt)**
- Profiler: (c)와 동일
- Judge: 파인튜닝 없이 GPT-4o-mini 프롬프트로 수행
- (c)와의 차이 = 파인튜닝 효과

**(d) Profiler-Judge w/o Gate**
- (c)와 동일하되, Transfer Judge의 프롬프트에서 "모든 패턴을 TRANSFER로 판정하라" 지시
- 또는 후처리로 모든 decision을 TRANSFER로 강제 변환

**(e) 전통 CDR**
- CoNet 또는 EMCDR 구현체 활용
- 동일 데이터셋, 동일 평가 프로토콜 적용

**(f) Raw Review Input**
- Profiler 단계 생략
- Judge(FT)에 raw review 텍스트를 직접 입력
- 별도 파인튜닝 불필요 (동일 FT 모델에 입력만 변경)

### 9.3 RQ별 비교 쌍 정리

| RQ | 비교 | 기대 결과 |
|----|------|----------|
| RQ1 | (c) vs (f) | 구조화 프로파일 > Raw Review |
| RQ2 | (c) vs (d) | Gate 적용 > Gate 없음 |
| RQ3 | (a) vs (b) vs (c) | Single < Profiler-Judge Prompt < Profiler-Judge FT |

### 9.4 각 조건의 구체적 설계 방법 (차별 변인 명시)

| 조건 | 구현 방식 | 차별 변인 (다른 조건 대비) |
|------|-----------|----------------------------|
| **(a) Single LLM** | GPT-4o-mini 1회 호출. 입력: Source 리뷰 + 후보 50개 + "Top-10을 추천하라" 프롬프트. 별도 패턴 추출/판정 단계 없음. | Profiler-Judge **분리 없음**. 단일 LLM이 모든 작업 수행 (LLM4CDR 방식 재현). |
| **(b) Profiler-Judge (Prompt)** | Profiler: (c)와 동일 GPT-4o-mini API. Judge: Qwen3-14B-Instruct를 **파인튜닝 없이 프롬프트만으로** 사용 (Few-shot 3예시 포함). | (a) 대비 **역할 분리 추가**, (c) 대비 **QLoRA 파인튜닝 제외**. |
| **(c) Ours ★** | Profiler: GPT-4o-mini API. Judge: Qwen3-14B + **QLoRA 파인튜닝** (Teacher Distillation 700건으로 학습). §6의 학습 데이터 사용. | 본 연구의 완전한 구성. (b) 대비 **파인튜닝 추가**. |
| **(d) P-J w/o Gate** | Profiler·Judge 구조는 (c)와 동일. 단, Judge 추론 시 **모든 패턴을 TRANSFER로 강제** (BLOCK/PARTIAL 출력을 후처리로 TRANSFER 변환). | (c) 대비 **Transfer Gate 비활성화**. 패턴별 차단 효과만 분리 검증. |
| **(e) 전통 CDR** | 비LLM 베이스라인. EMCDR(IJCAI 2017) 또는 CATN(SIGIR 2020) 재현 — 사용자/아이템 임베딩 학습 후 cross-domain mapping. 동일 1,000명 데이터 사용. | LLM 접근 자체의 우위 검증. **LLM 미사용**. |
| **(f) Raw Review** | Profiler 단계 생략. Source 리뷰 텍스트를 그대로 Judge(QLoRA)에 입력. Judge는 (c)와 동일하게 학습된 모델 사용. | (c) 대비 **구조화된 Profile 입력 제거** — 패턴 JSON vs raw text 효과 분리. |

### 9.5 RQ별 비교 매핑 (어떤 조건끼리 비교하면 어떤 RQ를 검증하는가)

| RQ | 비교 | 분리되는 효과 |
|----|------|----------------|
| **RQ1** | (c) vs (a) · (c) vs (e) | 본 연구 프레임워크의 전반적 우위 (단일 LLM·전통 CDR 대비) |
| **RQ2** | (c) vs (d) | Transfer Gate(BLOCK·PARTIAL 차단)의 순효과 |
| **RQ3** | (b) vs (c) | QLoRA 파인튜닝의 순효과 (구조 분리는 동일하게 유지) |
| 보조 | (c) vs (f) | Profiler 구조화 출력의 가치 (Profile JSON vs Raw Review) |
| 보조 | (a) vs (b) | 역할 분리 자체의 효과 (파인튜닝 없이도 우위인지) |

> **변인 통제 원칙**: 모든 조건은 동일한 1,000명 데이터·동일 후보 50개(seed=42)·동일 평가 프로토콜(LOO, HR@K/NDCG@K)을 공유한다. 조건 간 차이는 표의 "차별 변인"으로만 발생하므로, 두 조건의 성능 차이는 해당 변인의 순효과로 해석 가능.

### 9.6 Per-Pattern Contribution Ablation

**목적**: 7개 Core Pattern 각각이 추천 성능에 기여하는 marginal 효과 측정. Pilot Study에서 4가지 측면 검토로 선정된 7개가 실제 실험에서도 의미를 갖는지 데이터로 확인.

**구성**:
| 조건 | 제거 패턴 | 비교 대상 |
|------|----------|---------|
| (c-1) | none (full 7개) | 기준선 |
| (c-2) | -genre_preference | (c-1) 대비 |
| (c-3) | -narrative_complexity | (c-1) 대비 |
| (c-4) | -pacing_preference | (c-1) 대비 |
| (c-5) | -quality_sensitivity | (c-1) 대비 |
| (c-6) | -brand_loyalty | (c-1) 대비 |
| (c-7) | -sensory_preference | (c-1) 대비 |
| (c-8) | -emotional_resonance | (c-1) 대비 |

**구현**:
- Profiler 출력 JSON에서 해당 패턴 키만 제거 후 Judge에 입력
- 별도 재학습 불필요 (Judge는 동일 FT 모델 사용)
- Profile 누락 패턴은 빈 객체 `{}`로 대체

**측정**:
- ΔNDCG@10, ΔHR@10, ΔMRR (각 조건의 (c-1) 대비 변화)
- 7×3 (패턴 × 지표) heatmap 시각화

**기대 결과**:
- TRANSFER 후보 4개 (genre, narrative, pacing, emotional) 제거 시 성능 **하락**
- BLOCK 후보 2개 (brand, sensory) 제거 시 성능 **유지 또는 약상승** (어차피 Gate가 차단)
- emotional_resonance 제거 시 가장 큰 하락 예상 (Pilot 14% 빈도)

**해석**:
- 패턴별 marginal contribution이 사전 분류 Transfer Gate 라벨(TRANSFER vs BLOCK)과 정합하는지 확인
- 정합 시 → 패턴 선정의 타당성 데이터 입증
- 불일치 시 → 본 도메인 특수성 또는 선정 절차 한계 토론

### 9.7 Cold-Start Segment 분석

**목적**: Cold-Start 환경에서 본 연구의 우위가 가장 강하게 나타남을 검증 (CDR의 핵심 활용 시나리오).

**Segment 정의**:
| Segment | Books 리뷰 수 | 사용자 수 (1,000명 中 추정) |
|---------|:---:|:---:|
| Severe Cold-Start | 1~2 | ~30% |
| Moderate Cold-Start | 3~5 | ~40% |
| Warm | ≥ 6 | ~30% |

**비교**:
- 각 segment에서 (a) Single LLM, (c) Ours, (e) 전통 CDR의 NDCG@10 비교
- 가설: **Severe Cold-Start에서 본 연구의 우위 폭이 가장 큼**

**측정**:
- Segment × Method × Metric 표
- Segment별 상대 향상률 (vs (a) baseline) 시각화

**해석**:
- Cold-Start 강세는 본 연구의 contribution을 강하게 함
- 일반 segment에서 baseline과 비슷해도 Cold-Start에서 우위면 충분한 학술 기여

> **본 §9의 모든 ablation은 동일 평가 프로토콜(LOO, §10)을 공유한다. 따라서 조건 간 비교가 통계적으로 정합한다.**

### 9.8 본 연구의 한계 및 향후 작업

**한계**:
- 본 연구의 7개 패턴은 Movies&TV → Books 도메인에 한정한 결과로, 다른 CDR 시나리오에서는 다른 패턴이 적합할 수 있음
- Pilot Study 100명 규모는 LLM4CDR (RecSys 2025) norm과 동일 수준이나 통계적 일반화는 본 실험 1,000명에서 검증

**향후 작업**:
- 다른 도메인 쌍(Music → Movies, Books → Music 등)에서 패턴 선정 절차 재적용
- emotional_resonance의 affective recommendation 분야 이론 anchor 보강

---

## 10. 평가 프로토콜: Leave-One-Out

### 10.1 개요
Leave-One-Out(LOO)은 추천 시스템 평가에서 가장 널리 사용되는 프로토콜로, 각 사용자의 마지막 상호작용 1개를 테스트용으로 분리하고 나머지로 모델을 학습/추론한다. 본 연구에서는 Cross-Domain Cold-Start 환경에 맞게 다음과 같이 적용한다.

### 10.2 LOO 적용 절차

```
각 Test 사용자 u에 대해:
  1. Target(Books) 도메인의 마지막 구매 아이템 중 평점 4점 이상인 것을 GT로 설정
  2. GT를 제외한 나머지 Target 리뷰(최대 9개)를 Profiler 입력으로 사용
  3. Source(Movies & TV) 리뷰 최대 30개를 Profiler 입력으로 사용
  4. Profiler → Transfer Judge → Top-10 추천 생성
  5. GT가 Top-K에 포함되는지로 HR@K, NDCG@K, MRR 계산
```

### 10.3 핵심 설계 결정

| 결정 | 선택 | 근거 |
|------|------|------|
| **GT 선정 기준** | 마지막 구매 + 4점 이상 | 시간순으로 가장 최근의 긍정적 상호작용이 사용자의 현재 선호를 가장 잘 반영 |
| **GT 평점 제한** | 4점 이상만 | 3점 이하는 부정/중립 평가로, 이를 GT로 삼으면 "추천 성공"의 정의가 모호해짐 |
| **후보 구성** | GT 1 + Random Negative 49 = 50 | 섹션 2.4의 후보 선정 근거 참조 |
| **GT 제외** | Target 리뷰에서 GT 제거 후 입력 | 정보 누출(data leakage) 방지 — GT를 입력에 포함하면 모델이 이미 본 아이템을 추천하는 trivial solution |
| **LOO 단위** | 사용자 단위 1개 | 다수 GT를 두면 Cold-Start 사용자의 Target 리뷰가 더 줄어 Profiler 입력 품질 저하 |

### 10.4 왜 LOO인가? — 대안과 비교

| 프로토콜 | 설명 | 한계 | 선택 |
|----------|------|------|------|
| **Leave-One-Out** | 마지막 아이템 1개 평가 | 사용자당 평가 1회로 분산 클 수 있음 → Bootstrap CI로 보완 | **✓ 채택** |
| **K-fold** | 상호작용을 K개로 나눠 교차 평가 | Cold-Start 사용자(5~10개 리뷰)를 더 분할하면 입력 데이터가 지나치게 부족 | ✗ |
| **Temporal Split** | 시간 기준 train/test 분리 | LOO의 특수 형태 (마지막 시점 = 1건). 본 연구에서는 LOO와 동일 | — |

- **선행연구 일치성**: TALLRec, LLM4CDR, TrineCDR 모두 LOO 프로토콜 사용 → 결과 비교 가능
- **Bootstrap CI 보완**: Test 100명 × LOO 1회의 분산을 1,000회 부트스트랩으로 95% 신뢰구간 산출하여 통계적 신뢰성 확보

### 10.5 평가 흐름 요약 (1명의 Test 사용자)

```
Input:
  - Source 리뷰 30개 (Movies & TV)
  - Target 리뷰 최대 9개 (Books, GT 제외)
  ↓
Profiler: 선호 패턴 JSON 추출
  ↓
Transfer Judge: 패턴별 TRANSFER/PARTIAL/BLOCK 판정
  ↓
Output: Top-10 추천 리스트 (후보 50개 중 순위화)
  ↓
평가: GT의 순위 확인 → HR@1, HR@5, HR@10, NDCG@10, MRR 계산
```

### 10.6 평가 프로세스 (한눈에 — Test 100명 적용)

| 단계 | 내용 |
|------|------|
| **① Test 사용자** | 100명 (학습에 미사용) |
| **② GT 분리 + 입력 준비** | GT 1건 분리, Source 30개 + Target 9개(GT 제외) 준비 |
| **③ 후보 50개 구성** | GT 1 + Negative 49 (seed=42 동일 후보) |
| **④ Profiler 추론** | GPT-4o-mini, Source 리뷰 → 7개 패턴 JSON |
| **⑤ Transfer Judge 추론** | Qwen3-14B + QLoRA, **GT 모름 상태**에서 TRANSFER/PARTIAL/BLOCK + Top-10 생성 |
| **⑥ Top-10 추천 리스트** | 후보 50개를 점수 기준 순위화 |
| **⑦ GT 순위 확인** | 예: GT가 rank 3이면 HR@5=1, HR@1=0, NDCG@10=0.50 |
| **⑧ 사용자별 점수 집계** | HR@1/5/10, NDCG@10, MRR — 100명 평균 |
| **⑨ Bootstrap 95% CI** | 100명에서 1,000회 재표본 → 조건 간 차이 통계 검정 |

> **학습-평가의 핵심 차이**:
> - 학습 시(§6.9): Teacher는 GT를 알고 시연 → Student가 판정 과정을 학습
> - 평가 시(본 섹션): Student(Transfer Judge)는 **GT를 모르는 상태**로 추론 → 실전 추천 시나리오 그대로 시뮬레이션
> - 모든 6개 Ablation 조건은 이 동일한 평가 절차로 측정되며, 차이는 ④⑤ 단계의 모델 구성에서만 발생.

---

## 11. 평가 지표 및 통계 검증

### 11.1 주요 지표

| 지표 | 설명 |
|------|------|
| HR@1 | 1위 추천이 정답인 비율 |
| HR@5 | Top-5에 정답 포함 비율 |
| HR@10 | Top-10에 정답 포함 비율 |
| NDCG@10 | 정답의 순위를 고려한 점수 |
| MRR | 정답 순위 역수의 평균 |

#### 각 지표가 무엇을 의미하는가 (직관적 설명)

| 지표 | 의미와 계산 예시 | 왜 이 지표를 보는가 |
|------|------|------|
| **HR@1** (Hit Rate) | "1번 추천했을 때 적중한 비율"<br>예: 100명 중 25명이 1위 추천이 정답 → HR@1 = 0.25<br>값 범위: 0~1 (높을수록 좋음) | 가장 엄격한 정확도. **단 1개만 추천**하는 시나리오의 품질을 본다. 추천 시스템의 "최상위 정확도"를 의미. |
| **HR@5** | "Top-5 안에 정답이 포함된 비율"<br>예: GT가 rank 4 → Hit / GT가 rank 7 → Miss<br>100명 중 60명 적중 → HR@5 = 0.60 | 현실적 추천 UI(상위 5개 노출)의 품질. HR@1보다 후하지만 여전히 엄격. |
| **HR@10** | "Top-10 안에 정답이 포함된 비율"<br>후보 50개 중 랜덤 추천 시 기댓값 = 20%<br>모델이 그 이상이어야 의미 있음 | 전체 추천 리스트 도달률. 본 연구의 주요 보고 지표. |
| **NDCG@10** (Normalized DCG) | "정답이 몇 위에 있는지를 가중치로 점수화"<br>GT가 rank 1 → 1.00 / rank 3 → 0.50 / rank 10 → 0.29 / Top-10 밖 → 0<br>로그 감쇠로 상위 순위에 더 큰 가중 | HR은 Top-K 안/밖만 보지만, NDCG는 **"몇 위인지"**까지 본다. rank 1 추천과 rank 10 추천을 다르게 평가. |
| **MRR** (Mean Reciprocal Rank) | "정답 순위의 역수 평균"<br>GT가 rank 1 → 1/1 / rank 2 → 1/2 / rank 5 → 1/5<br>100명의 1/rank 평균값 | "평균적으로 정답이 몇 위쯤에 있는가"의 직관적 표현. 1/MRR ≈ 정답의 평균 순위. |

> **왜 5개 지표를 함께 보는가?**
> - HR@1은 너무 엄격해서 모델 차이가 잘 안 보일 수 있고, HR@10은 너무 후해서 천장 효과 위험.
> - NDCG@10은 순위 품질을 정량화하지만 직관적 해석이 어렵고, HR은 Top-K 안/밖만 본다.
> - 다섯 지표를 함께 보면 **"정확도 + 순위 품질 + 도달률"**의 다면적 평가가 가능하다.
> - **선행연구 일치**: TALLRec, LLM4CDR, NCF 등 추천시스템 표준 보고 지표 그대로 사용 → 결과 비교 가능.

### 11.2 통계적 유의성 검증: Bootstrap Confidence Interval

Test 100명의 표본 크기에서 결과의 신뢰성을 확보하기 위해 Bootstrap CI를 적용한다.

#### 왜 Bootstrap CI가 필요한가?

| 문제 | 설명 |
|------|------|
| **① 단일 점수 보고의 한계** | "HR@10 = 0.72"만 보고하면 그 값이 우연인지 진짜 모델 성능인지 알 수 없다. Test 100명이 다른 100명이었다면 0.65 또는 0.78이 나올 수도 있다. |
| **② 조건 비교의 신뢰성** | (c) HR@10=0.72 vs (a) HR@10=0.68 — 0.04 차이가 통계적으로 유의한가? 우연일 수도 있다. CI 겹침 여부로 판단. |
| **③ Test 샘플 크기 100명의 특수성** | 샘플이 작을수록 단일 점수의 변동성이 커진다. 100명에서 측정한 값이 "모집단 전체에서도 비슷한지" 추정 필요. |
| **④ 정규성 가정 회피** | HR/NDCG는 정규분포를 따르지 않는다(이진/비대칭). Bootstrap은 분포 가정 없이 신뢰구간을 만들 수 있는 비모수적 방법. |

#### Bootstrap CI 계산 절차

| 단계 | 내용 |
|------|------|
| ① | Test 100명 각각의 HR@10 값을 계산 (각 사용자: 0 또는 1) |
| ② | 이 100명에서 **복원 추출(with replacement)**로 100명을 재표본 → 평균 계산 (1개 부트스트랩 표본) |
| ③ | ②를 **1,000회 반복** → 1,000개의 평균값 분포 확보 |
| ④ | 1,000개 값의 **2.5 percentile ~ 97.5 percentile**이 95% 신뢰구간 |
| ⑤ | 모든 지표(HR@1/5/10, NDCG@10, MRR)와 모든 조건(a~f)에 대해 동일 절차 적용 |

#### 해석 예시 — 두 조건 비교

| 조건 | HR@10 | 95% CI | 유의성 판단 |
|------|------|------|------|
| (c) Ours ★ | 0.72 | [0.64, 0.79] | CI가 **겹치지 않음** → (c)가 (a)보다 통계적으로 유의하게 우수 (p < 0.05) |
| (a) Single LLM | 0.55 | [0.48, 0.62] | (위와 동일 비교) |
| (c) Ours ★ | 0.72 | [0.64, 0.79] | CI가 **겹침** → 차이가 통계적 유의성 미달. 더 많은 Test 데이터 필요할 수 있음 |
| (b) P-J Prompt | 0.69 | [0.61, 0.76] | (위와 동일 비교) |

#### 표준 설정 근거

- **왜 1,000회인가?**: 추천시스템 논문 표준 (NCF, TALLRec 등). 100~500회는 신뢰구간이 불안정하고, 5,000회 이상은 계산 비용 대비 추가 정확도 미미. 1,000회가 정확도와 비용의 균형점.
- **왜 95% CI인가?**: 통계학 표준 (alpha=0.05). 99% CI는 너무 보수적이어서 작은 차이를 검출 못하고, 90% CI는 1종 오류 위험 증가.
- **이 분석으로 강화되는 RQ 결론**: 단순히 "(c) HR@10 = 0.72 > (a) HR@10 = 0.55"라고 하지 않고, "(c)가 (a)보다 95% 신뢰수준에서 통계적으로 유의하게 우수 (CI 비겹침)"라고 보고 → **심사 대응력 ↑**.

#### 구현 코드

```python
import numpy as np

def bootstrap_ci(scores, n_bootstrap=1000, ci=0.95):
    """Bootstrap 95% Confidence Interval 계산"""
    boot_means = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(scores, size=len(scores), replace=True)
        boot_means.append(np.mean(sample))
    lower = np.percentile(boot_means, (1 - ci) / 2 * 100)
    upper = np.percentile(boot_means, (1 + ci) / 2 * 100)
    return np.mean(scores), lower, upper

# 사용 예시
# hr10_scores = [1, 0, 1, 1, 0, ...]  # 사용자별 hit 여부
# mean, lower, upper = bootstrap_ci(hr10_scores)
# 논문 표기: HR@10 = 0.72 (95% CI: 0.64-0.79)
```

---

## 12. 결과 분석 계획

### 12.1 주요 결과 테이블
- Ablation 전체 결과 비교 (6개 조건 x 5개 지표 + CI)

### 12.2 추가 분석

| 분석 | 내용 |
|------|------|
| Transfer Gate 판정 분포 | TRANSFER / PARTIAL / BLOCK 비율 통계 |
| 패턴별 전이 성공률 | 7개 Core Pattern 각각의 TRANSFER/PARTIAL/BLOCK 분포 |
| PARTIAL 변환 사례 분석 | "영상미 → 묘사력" 같은 변환 품질 정성 분석 |
| Cold-Start 정도별 분석 | Target 리뷰 5개 vs 10개 사용자 그룹 비교 (선택적) |
| 추천 근거 정성 분석 | BLOCK 패턴이 rationale에 누출되지 않는지 확인 |

---

## 13. 일정 및 마일스톤

| 주차 | 작업 | 산출물 |
|------|------|--------|
| **1주차** | 데이터 수집, 전처리, Overlapping User 추출 | 전처리된 데이터셋 |
| **1주차** | 데이터 EDA (분포 확인, Cold-Start 기준 검증) | notebooks/eda.ipynb |
| **1주차** | Pilot Study (Core Pattern 도출) | 빈도 표 + 7개 패턴 확정 |
| **2주차** | Profiler 프롬프트 설계 및 1,000명 실행 | profiler_outputs/ |
| **2주차** | Teacher Distillation 데이터 생성 | train.jsonl, val.jsonl |
| **3주차** | Transfer Judge QLoRA 파인튜닝 (Qwen3-14B) | best checkpoint |
| **3주차** | Ablation (c) Ours 실행 및 결과 확인 | 초기 결과 |
| **4주차** | 나머지 Ablation 조건 (a)(b)(d)(f) 실행 | 전체 결과 테이블 |
| **4주차** | (e) 전통 CDR 베이스라인 실행 | 비교 결과 |
| **5주차** | 결과 분석, 통계 검증, 추가 분석 | 분석 결과 |
| **5주차** | (선택) Qwen3-8B ablation 추가 실험 | 모델 크기 비교 |
| **6주차~** | 논문 작성 | 졸업 논문 초고 |

---

## 14. 참고문헌

### 14.1 핵심 인용 논문

| # | 논문 | 학회/저널 | 인용 맥락 |
|---|------|----------|----------|
| 1 | Bao et al., "TALLRec: An Effective and Efficient Tuning Framework to Align Large Language Model with Recommendation" | RecSys 2023 | QLoRA 기반 LLM 추천 파인튜닝의 이론적 근거. 50건 미만 학습 데이터로도 추천 능력 달성 보고 → Teacher Distillation 데이터 규모(700건)의 충분성 근거. LOO 평가 프로토콜 참조 |
| 2 | TrineCDR (Chen et al.), "Trinomial CDR" | KDD 2024 | NT 원인을 Feature/Interaction/Domain 3 level로 분류. Multi-level 원인 → multi-level 판정 필요라는 직접적 동기. Transfer Gate 3단계의 개념적 근거 |
| 3 | LLM4CDR (Zhao et al.), "LLM4CDR: LLM-based Cross-Domain Recommendation" | WWW 2025 | Single LLM + 프롬프트 기반 CDR. 가장 직접적인 비교 대상(베이스라인). 후보 20개 기반 평가 프로토콜 참조, 데이터 규모 ~1,000명 참조 |
| 4 | Zhang & Wu, "A Survey on Negative Transfer" | IEEE/CAA JAS 2023 | NT 완화 접근을 Domain/Instance/Feature 3단계로 분류한 서베이. Transferability를 계층적으로 판단해야 한다는 이론적 토대 |
| 5 | Wang et al., "Characterizing and Avoiding Negative Transfer" | CVPR 2019 | NT의 3가지 요인 식별 + gate 기반 filtering 제안. Transfer Gate 메커니즘의 방법론적 선례 |
| 6 | Cao et al. (SAN), "Partial Transfer Learning with Selective Adversarial Networks" | CVPR 2018 | Binary(transfer/block) selective transfer. 2단계 한계 → PARTIAL 등급 확장 필요성의 근거 |
| 7 | FedGCDR (Liu et al.) | NeurIPS 2024 | Soft/Hard NT 2유형 구분. NT에도 강도 차이가 있다는 실증적 근거 |
| 8 | Park et al., "Shapley-value based feature-level transfer" | CIKM 2023 | Shapley value 연속 가중치 기반 전이 조절. 연속 가중치의 해석 어려움 → 이산 판정으로의 발전 동기 |
| 9 | McAuley Lab, "Amazon Review 2023 Dataset" | 2023 | 실험 데이터셋 소스. Movies & TV → Books 도메인 간 공통 사용자 추출 |

### 14.2 방법론 근거 논문

| # | 논문 | 학회/저널 | 인용 맥락 |
|---|------|----------|----------|
| 10 | Hinton et al., "Distilling the Knowledge in a Neural Network" | NeurIPS Workshop 2015 | Knowledge Distillation의 원론적 근거. Teacher-Student 패러다임의 이론적 토대 |
| 11 | Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models" | NeurIPS 2022 | CoT rationale 포함 학습 데이터가 일반화 성능을 향상시킨다는 근거 → Teacher가 rationale을 포함한 출력을 생성하는 설계의 정당화 |
| 12 | Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models" | ICLR 2022 | LoRA/QLoRA 파인튜닝 방법론의 원론적 근거. Transfer Judge 파인튜닝 전략의 기반 |
| 13 | Dettmers et al., "QLoRA: Efficient Finetuning of Quantized Language Models" | NeurIPS 2023 | 4-bit 양자화 + LoRA의 효율성 검증. 제한된 GPU 환경에서 14B 모델 파인튜닝 가능성의 근거 |
| 14 | Qwen Team, "Qwen3 Technical Report" | arXiv 2025 | Qwen3-14B의 벤치마크 성능 데이터 (MMLU 81.05, MMLU-Pro 61.03). Transfer Judge LLM 선정 근거 |

### 14.3 평가 방법론 근거 논문

| # | 논문 | 학회/저널 | 인용 맥락 |
|---|------|----------|----------|
| 15 | He et al., "Neural Collaborative Filtering" | WWW 2017 | Leave-One-Out + Random Negative Sampling 평가 프로토콜의 표준 정립. HR@K, NDCG@K 지표 사용의 근거 |
| 16 | Krichene & Rendle, "On Sampled Metrics for Item Recommendation" | KDD 2020 | 샘플링 기반 평가(50개 후보)의 이론적 정당성. 전체 아이템 대비 샘플링 평가가 순위 상관성을 유지함을 증명 |

---

## 부록: 디렉토리 구조 (현행)

```
논문 작업 폴더/
├── experiment_plan.md          # 본 실험 계획서
├── data/
│   ├── books_meta_filtered.parquet       # 전처리된 Books 메타데이터 (4.4M)
│   ├── books_reviews_filtered.parquet    # 전처리된 Books 리뷰
│   ├── movies_meta_filtered.parquet      # 전처리된 Movies 메타데이터
│   ├── movies_reviews_filtered.parquet   # 전처리된 Movies 리뷰
│   ├── overlapping_users.parquet         # 1,000명 샘플 (seed=42)
│   ├── eda_*.png                         # EDA 시각화 7장
│   ├── train.jsonl                       # ★ Teacher 생성 후 (SFT, GT 제거)
│   └── val.jsonl                         # ★ 검증 세트
├── prompts/                              # ★ 프롬프트 설계 문서
│   ├── profiler_prompt.md                # Profiler 프롬프트 10 섹션 설계 문서
│   └── teacher_prompt.md                 # Teacher 프롬프트 10 섹션 설계 문서
├── profiler_outputs/                     # ★ Profiler 실행 후 user_{id}.json
├── teacher_outputs/                      # ★ Teacher 실행 후 user_{id}.json (원본)
├── models/
│   └── judge_qlora/                      # 파인튜닝 체크포인트
├── results/
│   ├── ablation/                         # Ablation 조건별 결과
│   └── analysis/                         # 분석 결과
├── scripts/                              # 실행 스크립트
│   ├── generate_eda_report.py            # EDA 보고서 PDF 생성
│   ├── generate_framework_diagram.py     # 프레임워크 다이어그램 PDF 생성
│   ├── generate_pdf.py                   # Overview PDF 생성
│   ├── make_diagrams.py                  # 시각화
│   ├── run_profiler.py                   # ★ Profiler 실행 (JSON 검증 + 재시도)
│   ├── run_teacher.py                    # ★ Teacher 실행 (5단계 필터 + SFT 변환)
│   ├── train_judge.py                    # QLoRA 파인튜닝 (예정)
│   ├── run_inference.py                  # 추론 실행 (예정)
│   └── evaluate.py                       # 평가 및 Bootstrap CI (예정)
├── notebooks/
│   └── eda.ipynb                         # EDA 노트북 (완료)
├── docs/                                 # 심사용 PDF 문서
│   ├── TransferJudge_Overview_v5.pdf
│   ├── TransferJudge_EDA_Report.pdf      # 18페이지 부록용
│   └── TransferJudge_Framework_Diagram.pdf  # 한 장짜리 프레임워크 도식
└── diagrams/                             # 다이어그램 PNG
```

**★ = 프롬프트 설계 단계에서 신규 생성 (2026-04-23 완료)**
