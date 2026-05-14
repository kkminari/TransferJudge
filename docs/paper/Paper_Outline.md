# 논문 골격 — TransferJudge

> 빅데이터학과 17기 곽민아 석사학위논문
> 작성: 2026.05.14 (Phase 3 학습 중 작성, Phase 4·5 결과 들어오면 채움)

---

## 가제 (Working Title)

> **TransferJudge: A Profiler-Judge LLM-Based Framework for Selective Transfer in Cross-Domain Recommendation**

대안 1: "Selective Transfer in Cross-Domain Recommendation via LLM-Based Profile and Gate"
대안 2: "Beyond Universal Transfer: A Pattern-Level Transfer Gate for Cold-Start CDR"

---

## Abstract (초안, 250 단어 목표)

**Motivation (35단어)**
Cross-domain recommendation (CDR) is critical for cold-start scenarios, but conventional approaches assume that all user preferences transfer uniformly across domains. This assumption fails when domain-specific patterns (e.g., actor loyalty in movies) cause negative transfer to other domains (e.g., books).

**Problem (40단어)**
Existing LLM-based CDR methods generate recommendations either from raw reviews (losing structure) or from monolithic prompts (mixing transferable and non-transferable signals). Neither explicitly identifies which preference patterns should transfer.

**Method (60단어)**
We propose TransferJudge, a Profiler-Judge framework that (1) extracts 7 structured preference patterns from source-domain reviews via a frozen LLM (Profiler), and (2) trains a small Judge model (Qwen3-14B QLoRA) to apply a 3-level transfer gate (TRANSFER / PARTIAL / BLOCK) per pattern before generating recommendations. Training uses GPT-4o-mini as Teacher to produce 578 high-quality decisions for selective distillation.

**Experiments (60단어)**
Evaluated on Amazon Movies → Books cold-start scenario (100 test users, 50 candidates each), TransferJudge achieves HR@10 of XX% and NDCG@10 of XX, surpassing single-LLM (X), prompt-only (X), no-gate (X), and traditional CDR (X) baselines by margins of XX–XX percentage points. Pattern-level ablation confirms that blocking brand_loyalty is essential while atmosphere-type sensory signals successfully transfer.

**Contribution (55단어)**
This work demonstrates that (i) selective transfer outperforms uniform transfer in cross-domain recommendation, (ii) LLMs can be guided to identify medium-specific patterns through few-shot distillation, and (iii) a 14B parameter model with 578 training examples suffices to internalize this transfer gating—a practical solution for resource-constrained CDR research.

---

## 1. Introduction (~2-3 pages)

### 1.1 Background
- Cross-domain recommendation의 필요성 (cold-start 완화)
- 기존 접근의 두 흐름: matrix factorization (collaborative) / LLM-based
- 두 흐름 모두 "모든 사용자 신호가 다 전이 가능하다"는 암묵적 가정

### 1.2 Motivating Example
- 사례: "Christopher Nolan 영화 좋아함" → "Nolan에 관한 책"으로 변환 시도 시 부정 효과 (Nolan은 감독, author 없음)
- 다른 사례: "감성적·따뜻한 영화 분위기 선호" → 책에도 적용 가능
- 두 사례의 차이: **medium-specific vs medium-agnostic**

### 1.3 Research Questions

- **RQ1**: 구조화된 Profile이 raw review와 **전통 CDR (EMCDR, PTUPCDR)** 보다 추천을 개선하는가?
- **RQ2**: Transfer Gate (TRANSFER/PARTIAL/BLOCK)가 실제로 성능에 기여하는가?
- **RQ3**: Profiler-Judge 분리 + Judge 파인튜닝이 prompt-only, single LLM, **기존 LLM CDR (TALLRec)** 보다 나은가?

(외부 검토 반영: 단순 self-ablation을 넘어 전통 CDR 2종 + LLM CDR 1종을 baseline으로 포함하여
"본 연구만의 selective transfer가 monolithic 접근들과 어떻게 다른가"를 직접 검증)

### 1.4 Contributions (Bullet Points)
1. **개념적**: Selective transfer 패러다임 제시 — 모든 신호가 전이 가능한 것이 아니다
2. **방법론적**: Profiler-Judge 2단계 구조 + 3-level Transfer Gate
3. **실험적**: Amazon Movies→Books에서 6 conditions ablation으로 효과 입증
4. **재현 가능성**: 1,000명 cohort + 578줄 SFT 데이터로 14B 모델 학습 가능

---

## 2. Related Work (~3-4 pages)

### 2.1 Cross-Domain Recommendation

**Traditional (collaborative filtering 기반)**:
- **EMCDR (Man et al., IJCAI 2017)** — embedding mapping + MLP cross-domain transfer
  → 본 연구 (e1) baseline
- CoNet (Hu et al., 2018) — cross-domain neural network
- **PTUPCDR (Zhu et al., WSDM 2022)** — personalized transfer + meta-learning, SOTA
  → 본 연구 (e2) baseline
- BiTGCF (Liu et al., 2020) — bidirectional transfer GCN
- Limitation: latent feature 전이 가정, **패턴별 선택성 부재**

**LLM-based (최근 흐름)**:
- **TALLRec (Bao et al., RecSys 2023)** — LLM as recommender via instruction SFT, 가장 인용 많은 LLM CDR
  → 본 연구 (g) baseline ★
- LLM4CDR (Zhang et al., 2024) — LLM for CDR with prompt engineering
- TrineCDR (Liu et al., 2024) — knowledge distillation for CDR (본 연구와 동일 접근이나 monolithic)
- Limitation: 단일 prompt에 모든 신호 통합, **transfer 가능성을 명시적으로 모델링하지 않음**

**본 연구 차별성**:
| 측면 | Traditional CDR | LLM CDR (TALLRec 등) | **TransferJudge (Ours)** |
|------|----------------|---------------------|-------------------------|
| Source 신호 처리 | latent vector | raw review/instruction | **structured 7-pattern profile** |
| Transfer 결정 | implicit (mapping function) | implicit (LLM 내부) | **explicit per-pattern gate** |
| 부정 전이 차단 | 불가 | 불가 | **명시적 BLOCK 판정** |
| Cold-start 적합도 | 제한적 (latent 학습 필요) | 가능 | **검증된 강건성** |

### 2.2 LLM Knowledge Distillation
- Self-distillation (Hinton et al., 2015)
- Teacher-Student frameworks for SFT (Wang et al., 2022)
- 본 연구: GPT-4o-mini → Qwen3-14B QLoRA, 578 examples

### 2.3 Cold-Start Recommendation
- Content-based hybrid
- Meta-learning approaches (MAMO)
- 본 연구: cohort 정의 (Target 5~10) + temporal cutoff

### 2.4 User Preference Modeling
- Implicit vs explicit feedback
- Multi-faceted preference (Adomavicius et al., 2022)
- 본 연구의 7-pattern 정의 근거 (Pilot Study에서 학술 표준 6 + 1 추출)

---

## 3. Method (~5-6 pages)

### 3.1 Problem Formulation
- Source domain $D_s$ (Movies), Target domain $D_t$ (Books)
- User $u$ has reviews $R^s_u$ in source, $R^t_u$ in target (small)
- Goal: predict next item $i \in I_t$ for user $u$ given $R^s_u + R^t_u$ partial

### 3.2 Profiler (Frozen LLM)
- Input: $R^s_u$ (영화 리뷰 30개, temporal cutoff)
- Output: $P_u$ = 7-pattern JSON
  - 각 pattern: {value, evidence, confidence, polarity, transferability_hint}
- Implementation: GPT-4o-mini, temperature 0.0, seed 42

### 3.3 The 7 Core Preference Patterns
| Pattern | 정의 | 학술 근거 |
|---------|------|-----------|
| genre_preference | 장르 선호 | Adomavicius (taxonomic) |
| narrative_complexity | 서사 복잡도 | Thet (text analytics) |
| pacing_preference | 전개 속도 | Liu (sequence) |
| quality_sensitivity | 퀄리티 민감도 | Hu & Liu (sentiment) |
| brand_loyalty | 브랜드 충성도 | Sun (brand) |
| sensory_preference | 감각·분위기 (subtypes: visual / atmosphere) | Suh (multimedia) |
| emotional_resonance | 감정 공명 | Liu (emotion) |

### 3.4 Teacher: Synthetic Label Generation
- Input: Profile + 50 candidate books + GT hint
- Output: transfer_decisions (per-pattern TRANSFER/PARTIAL/BLOCK) + Top-10 recommendations
- Filter: Only records where GT appears in Top-10 are retained (quality control)
- Result: 578 high-quality records

### 3.5 Judge: Qwen3-14B QLoRA
- Architecture: Qwen3-14B + LoRA (r=16, target 7 modules)
- Training: SFT with assistant_only_loss=True
- Quantization: 4-bit NF4 + bfloat16 compute
- Effective batch size: 1 × 16 = 16
- Loss: cross-entropy on assistant tokens only

### 3.6 Inference: Transfer Gate Application
1. Receive Profile (no GT hint)
2. For each pattern, decide TRANSFER / PARTIAL / BLOCK
3. Generate Top-10 using only TRANSFER and PARTIAL patterns as `applied_patterns`
4. BLOCK patterns must not influence any recommendation

---

## 4. Experimental Setup (~3-4 pages)

### 4.1 Dataset
- Source: Amazon Reviews 2023 — Movies & TV
- Target: Amazon Reviews 2023 — Books
- Cohort selection: Source ≥ 15 reviews, Target 5~10 reviews → 1,000 users (cold-start)
- Temporal cutoff: source reviews must precede the GT timestamp
- Splits: train 578 / valid 100 / test 100 (no user overlap)
- Dataset statistics in Table 1

### 4.2 Evaluation Protocol
- Leave-One-Out (LOO): GT is the most recent target item with rating ≥ 4
- For each user, sample 50 candidates (1 GT + 49 random)
- Metrics: HR@1, HR@5, HR@10, NDCG@5, NDCG@10, MRR
- Plus: JSONValid, SchemaComplete, CandMembership, BLOCKLeakage, PDA, Decision JSD

### 4.3 Baselines (8 Conditions)

**자기 검증용 (4개)**:
- (a) Single LLM — GPT-4o-mini, raw review → Top-10, zero-shot
- (b) Profiler-Judge Prompt-only — GPT-4o-mini, Profile + no gate, zero-shot
- (c) **Ours** ★ — Qwen3-14B QLoRA, Profile + Gate + 578-shot training
- (d) w/o Gate — Qwen3-14B QLoRA, Profile but gate disabled
- (f) Raw Review — Qwen3-14B trained on raw reviews, no Profile

**외부 baseline (3개)** — Codex 권장 반영:
- (e1) **EMCDR (Man et al., IJCAI 2017)** — 고전 cross-domain matrix factorization
- (e2) **PTUPCDR (Zhu et al., WSDM 2022)** — 최신 personalized transfer + meta-learning
- (g) **TALLRec (Bao et al., RecSys 2023)** — LLM as recommender via instruction SFT (가장 인용 많은 LLM CDR)

8개 모두 동일한 Test 100명, 동일한 후보 50권 (seed=42)에서 평가하여 공정 비교.

### 4.4 Implementation Details
- Profiler: GPT-4o-mini, temp 0.0, seed 42
- Teacher: GPT-4o-mini, temp 0.0, seed 42, with GT hint
- Judge: Qwen3-14B, QLoRA r=16, lr 2e-4, 5 epochs, early stop patience 2
- Hardware: 1×A100 80GB (RunPod), training ~7 hours
- Cost: ~$5 GPU + ~$5 OpenAI API = ~$10 total

---

## 5. Results (~4-5 pages)

### 5.1 Main Results (Table 2)
- 6 conditions × 6 metrics
- (c) Ours achieves the best on HR@10 and NDCG@10
- Paired t-test (c) vs (a): p < 0.05
- Cohen's d (c) vs (a): d > 0.5

### 5.2 Per-Pattern Ablation (Figure 3, Table 3)
- brand_loyalty ablation: Δ ≈ 0 (already blocked in Ours)
- brand_loyalty force_transfer: ΔNDCG < 0 (negative transfer demonstrated)
- sensory_preference: subtype 분리 효과
- Top important: genre_preference, emotional_resonance

### 5.3 Cold-Start Robustness (Figure 4, Table 4)
- Severe segment (Target 5권): Ours NDCG > 0.85 × Warm NDCG
- 전통 CDR (e): Severe에서 매우 저조
- Ours가 cold-start에 강건함 입증

### 5.4 Transfer Gate Effectiveness (Figure 5)
- (c) Ours vs (d) w/o Gate: NDCG 차이 = Gate 자체의 효과
- Decision distribution (Judge vs Teacher) JSD < 0.05

### 5.5 Qualitative Analysis (Section 5.5)
- Case 1: Drama lover + emotional resonance → memoir 추천 성공
- Case 2: Action film fan + brand_loyalty BLOCK → 책 형식 thriller 추천 (배우 책 X)
- Case 3: 실패 사례 (Profile 신호 부족)

---

## 6. Discussion (~2-3 pages)

### 6.1 Why Selective Transfer Works
- 인터프리테이션: Gate가 explicit reasoning을 강제
- Reasoning chain이 black-box LLM보다 통제 가능

### 6.2 Why 578 examples is enough
- LoRA의 효율성
- High-quality > quantity (Teacher quality filter 효과)

### 6.3 Limitations
- Domain: Movies → Books만 검증. 다른 cross-domain (Music → Movies 등) 추가 필요
- Cohort: 1,000명 random sample. 더 대규모 cohort에서 결과 확인 필요
- Profile 신호 부족 사용자 (~30%): Profile만으로 추천 어려운 한계

### 6.4 Future Work
- Multi-domain extension (3+ domains)
- Online learning / continual update
- Other domains: e-commerce, entertainment

---

## 7. Conclusion (~1 page)

본 연구는 cross-domain recommendation에서 모든 사용자 신호가 균일하게 전이 가능하다는 기존 가정을 부정하고,
선택적 전이(selective transfer)를 명시적으로 학습한 Judge 모델이 더 나은 cold-start 성능을 달성함을 보였다.
578줄의 distilled 학습 데이터와 14B 모델만으로 6개 baseline을 모두 outperform하는 결과는
LLM 기반 추천 시스템 연구의 새로운 방향을 제시한다.

---

## References (학술적 인용)

### 학술 표준 — 본 연구 직접 인용
- Bao, K., et al. (2023). TALLRec. RecSys.
- Hinton, G., et al. (2015). Distilling the Knowledge in a Neural Network.
- Hu, G., et al. (2018). CoNet. CIKM.
- Liu, J., et al. (2024). TrineCDR.
- Man, T., et al. (2017). EMCDR. IJCAI.
- McAuley, J., et al. (2023). Amazon Reviews 2023 Dataset.
- Zhang, S., et al. (2024). LLM4CDR.
- Zhu, Y., et al. (2022). PTUPCDR.

### Pilot Study 인용 (Pattern 정의 근거)
- Adomavicius, G., et al. (2022). Multi-criteria recommender systems.
- Hu, M., & Liu, B. (2004). Mining and summarizing customer reviews.
- Liu, B. (2012). Sentiment Analysis and Opinion Mining.
- Sun, J., et al. (2017). Brand loyalty in recommender systems.
- Suh, B., et al. (2020). Multimedia recommendation.
- Thet, T. T., et al. (2010). Aspect-based sentiment analysis.

### 부록 / Limitation 인용
- Wang, J., et al. (2022). Noisy label learning.
- Mehrabi, N., et al. (2021). Survey on bias and fairness in ML.

---

## 부록 (Appendices)

### A. Pilot Study Report (별도 PDF 첨부)
- 100명 표본 EDA → 7 pattern 도출 과정
- HDBSCAN 클러스터링 결과
- TransferJudge_Pilot_Report.pdf 참조

### B. Phase별 실험 보고서
- Phase 1 Profiler Report (docs/phase1/)
- Phase 2 Final Report (docs/phase2/)
- Phase 2 Data Lineage (docs/phase2/)
- Phase 2 Defect Analysis (docs/phase2/) — 외부 리뷰 + 수정 이력

### C. Hyperparameter Details
- LoRA r=16, alpha=32, dropout=0.1
- max_seq_length=12288 (실측 최대 11,194 커버)
- assistant_only_loss=True
- 자세한 근거: docs/phase3/Phase3_Hyperparam_Notes.md

### D. Reproducibility Checklist
- Code: github.com/kkminari/TransferJudge
- Data: HuggingFace kwaksuobusi/transferjudge-data
- Adapter: HuggingFace kwaksuobusi/transferjudge-judge-v1
- Seeds: 42 (sampling), 2027/2028 (refill·holdout), 42 (training)

### E. Cost Breakdown
- Phase 1·2 (OpenAI API): $4.32
- Phase 3 (RunPod A100 8h): $12-16
- Phase 4·5 (mixed): $11-17
- Total: ~$28-37
