# Phase 4 평가 지표 정의

> 본 연구의 추천 성능 + 추론 품질을 측정하는 모든 지표의 수식과 의미.
> Phase 4·5에서 6개 조건 모두 동일한 지표로 평가.

---

## 1. 추천 정확도 (Recommendation Accuracy)

### 1.1 Hit Rate @ k (HR@k)

**정의**: Top-k 추천 안에 GT 책이 포함되었으면 1, 아니면 0의 평균.

$$
HR@k = \frac{1}{|U|} \sum_{u \in U} \mathbb{1}[GT_u \in TopK_u]
$$

| k | 의미 | 본 연구 목표 |
|---|------|------|
| 1 | 가장 자신 있는 추천 1개에 정답 | ≥ 0.05 |
| 5 | Top-5 안에 정답 | ≥ 0.30 |
| 10 | Top-10 안에 정답 (Teacher와 직접 비교) | ≥ 0.60 (Teacher 60.2% 기준) |

### 1.2 NDCG @ k (Normalized Discounted Cumulative Gain)

**정의**: 정답이 Top-k에서 더 높은 순위일수록 높은 점수.

$$
NDCG@k = \frac{1}{|U|} \sum_{u \in U} \frac{DCG_u@k}{IDCG_u@k}
$$

$$
DCG_u@k = \sum_{i=1}^{k} \frac{2^{rel_i} - 1}{\log_2(i+1)}
$$

여기서 $rel_i = 1$ if $i$-th 추천이 GT, else 0.

| k | 의미 | 본 연구 목표 |
|---|------|------|
| 5 | Top-5 순위 가중 | ≥ 0.20 |
| 10 | Top-10 순위 가중 | ≥ 0.25 |

### 1.3 MRR (Mean Reciprocal Rank)

**정의**: GT의 역순위 평균.

$$
MRR = \frac{1}{|U|} \sum_{u \in U} \frac{1}{rank_u}
$$

GT가 Top-10에 없으면 $rank_u = \infty$ → 0 기여.

목표: ≥ 0.15

---

## 2. 출력 품질 (Output Quality)

### 2.1 JSON 유효율 (JSON Validity Rate)

**정의**: 모델 출력 텍스트가 valid JSON으로 파싱되는 비율.

$$
JSONValid = \frac{|\{u : json.loads(output_u) \text{ success}\}|}{|U|}
$$

목표: ≥ 0.95

### 2.2 스키마 완전성 (Schema Completeness)

**정의**: JSON이 본 연구의 출력 스키마를 따르는 비율.

검증 항목:
- `transfer_decisions` 키 존재 + 7개 패턴 모두 포함
- 각 패턴: `decision` ∈ {TRANSFER, PARTIAL, BLOCK}, `confidence` ∈ [0, 1]
- `recommendations` 길이 = 10, 각 item에 `rank`, `item_id`, `score`, `applied_patterns`

목표: ≥ 0.95

### 2.3 Candidate Membership (후보 내 추천 비율)

**정의**: 추천된 `item_id`가 50개 후보 안에 있는 비율.

$$
CandMembership = \frac{|\{(u,i) : rec_{u,i} \in candidates_u\}|}{10 \cdot |U|}
$$

목표: = 1.00 (Phase 2의 정합성 검증과 동일)

### 2.4 BLOCK Leakage Rate

**정의**: BLOCK으로 판정된 패턴이 추천 근거(`applied_patterns`)에 포함된 비율.

목표: = 0.00 (절대 발생 금지)

---

## 3. 추론 품질 (Reasoning Quality) — 신규 메트릭

### 3.1 Pattern Decision Accuracy

**정의**: Judge의 `transfer_decisions`가 Teacher와 일치하는 비율 (test set 한정).

$$
PDA = \frac{1}{7 \cdot |U|} \sum_{u \in U} \sum_{p=1}^{7} \mathbb{1}[dec_u^p (Judge) = dec_u^p (Teacher)]
$$

목표: ≥ 0.80

### 3.2 Per-Pattern Decision Distribution

**정의**: 각 패턴별 TRANSFER/PARTIAL/BLOCK 비율이 Teacher와 얼마나 일치하는지.

**측정 방식**: JSD (Jensen-Shannon Divergence)

$$
JSD(P || Q) = \frac{1}{2} KL(P || M) + \frac{1}{2} KL(Q || M), \quad M = \frac{P+Q}{2}
$$

목표: JSD ≤ 0.05 (Teacher 분포와 거의 동일)

### 3.3 Brand Loyalty BLOCK Rate

**정의**: brand_loyalty 패턴이 BLOCK으로 판정된 비율 (논문 핵심 가설).

목표: ≥ 0.90 (Teacher의 98.8%와 근접)

### 3.4 Sensory Pattern TRANSFER Rate

**정의**: sensory_preference 패턴이 TRANSFER로 판정된 비율 (subtype 분리 가설).

목표: 30~75% 범위 (Teacher 68% 근처)

---

## 4. 통계적 유의성

### 4.1 Paired t-test

두 조건 간 NDCG@10 차이의 통계적 유의성:

$$
t = \frac{\bar{d}}{s_d / \sqrt{n}}
$$

여기서 $d_i = NDCG_i^{condA} - NDCG_i^{condB}$.

목표: p < 0.05 (Ours > Baseline)

### 4.2 Cohen's d (Effect Size)

$$
d = \frac{\bar{X}_A - \bar{X}_B}{s_{pooled}}
$$

해석:
- d > 0.2: small
- d > 0.5: medium
- d > 0.8: large

목표: Ours vs Single LLM d > 0.5

---

## 5. Per-Pattern Ablation 지표 (Phase 5)

### 5.1 Pattern Importance Score (PIS)

특정 패턴 $p$를 제거했을 때의 성능 하락:

$$
PIS_p = NDCG@10_{full} - NDCG@10_{w/o\ p}
$$

PIS가 클수록 그 패턴이 중요.

### 5.2 Negative Transfer Detection

특정 패턴 $p$를 강제 TRANSFER로 했을 때 성능 변화:

$$
NTD_p = NDCG@10_{force\ p=TRANSFER} - NDCG@10_{full}
$$

NTD < 0이면 그 패턴은 BLOCK이 정답 (예: brand_loyalty 예상).

---

## 6. Cold-Start Segment 분석 (Phase 5b)

### 6.1 Segment 정의 (Target Domain 활동량 기준)

| Segment | Books 리뷰 수 | 추정 빈도 |
|---------|-------------|----------|
| Severe | 5권 | ~30% |
| Moderate | 6~7권 | ~40% |
| Warm | 8~10권 | ~30% |

### 6.2 Segment별 NDCG@10 비교

본 연구는 cold-start에 강하다는 주장 → Severe segment에서도 충분한 성능이 나와야 함.

목표: NDCG@10 (Severe) ≥ NDCG@10 (Warm) × 0.85

---

## 7. 평가 자동화 — `evaluate_judge.py` 출력 예시

```json
{
  "condition": "c_ours",
  "n_users": 100,
  "metrics": {
    "HR@1": 0.07,
    "HR@5": 0.34,
    "HR@10": 0.61,
    "NDCG@5": 0.22,
    "NDCG@10": 0.28,
    "MRR": 0.18,
    "JSONValid": 0.99,
    "SchemaComplete": 0.97,
    "CandMembership": 1.00,
    "BLOCKLeakage": 0.00,
    "PDA": 0.83,
    "DecisionJSD": 0.03,
    "BrandLoyaltyBLOCK": 0.96,
    "SensoryTRANSFER": 0.62
  },
  "per_segment": {
    "severe": {"NDCG@10": 0.26, "n": 30},
    "moderate": {"NDCG@10": 0.28, "n": 42},
    "warm": {"NDCG@10": 0.31, "n": 28}
  }
}
```

---

## 8. 조건 간 비교표 (Phase 4 최종, 8 conditions)

| 조건 | 모델·방식 | HR@10 | NDCG@10 | PDA | 비고 |
|------|----------|-------|---------|-----|------|
| (a) Single LLM | GPT-4o-mini (Profile 없이, zero-shot) | ? | ? | N/A | 단순 LLM baseline |
| (b) Prompt-only | GPT-4o-mini (Profile 있음, gate·학습 없음) | ? | ? | ? | LLM 본인 추론력 |
| **(c) Ours** | **Qwen3-14B QLoRA (Profile + Gate + 578줄 SFT)** | **?** | **?** | **?** | **본 연구 주장** |
| (d) w/o Gate | Qwen3-14B QLoRA (Profile만, gate 비활성) | ? | ? | ? | Gate 효과 측정 |
| (e1) EMCDR | Embedding mapping (Man et al., 2017) | ? | ? | N/A | 전통 CDR (고전) |
| **(e2) PTUPCDR** | **Personalized Transfer (Zhu et al., 2022)** | ? | ? | N/A | **전통 CDR 최신** |
| (f) Raw Review | Qwen3-14B (Profile 없이 raw review로 SFT) | ? | ? | N/A | Profile 효과 검증 |
| **(g) TALLRec** | **Bao et al., RecSys 2023 — LLM as recommender** | **?** | **?** | N/A | **LLM CDR SOTA** |

**핵심 가설** (Codex 권장 반영, 외부 비교 강화):
1. **(c) > (a)·(b)·(f)**: Profile + Gate 학습 효과 (자기 검증)
2. **(c) > (d)**: Gate 자체의 효과 (BLOCK·PARTIAL 판단)
3. **(c) > (e1)·(e2)**: LLM 기반이 전통 CDR (고전·최신) 대비 우위
4. **(c) > (g)**: ★ **selective transfer가 monolithic LLM CDR 대비 우위** — 가장 중요한 비교
