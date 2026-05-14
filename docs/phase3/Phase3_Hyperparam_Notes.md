# Phase 3 Hyperparameter 노트

> Phase 3 학습 하이퍼파라미터의 **선택 근거 + 변경 시 가이드라인**
> 참고: SOBA finetuning project (Qwen3-14B QLoRA 동일 베이스)

---

## 1. 데이터 규모 분류

| 규모 | 데이터 건수 | LoRA r | dropout | epochs |
|------|-----------|--------|---------|--------|
| 소규모 | < 500 | 8 | 0.15 | 5-8 |
| **소~중규모** | **500-5,000** | **16~32** | **0.05~0.10** | **3-5** |
| 중규모 | 5,000-20,000 | 32-64 | 0.05 | 2-3 |
| 대규모 | > 20,000 | 64-128 | 0.05 | 1-2 |

**본 연구 = 578건 (소~중규모 하한)**:
- r=16, alpha=32, dropout=0.10, epochs=5 → 가이드 정확히 일치

---

## 2. LoRA 파라미터 선택 근거

### r (rank)
- 본 연구 **r=16** 채택
- 이유: 데이터 578건 (가이드 하한). r=32는 과적합 위험. r=8은 표현력 부족
- **변경 시**: 데이터가 1,000건 이상이면 r=32로 ↑ 고려

### lora_alpha
- 본 연구 **alpha=32** (= 2 × r)
- 이유: 표준 비율. 스케일 = alpha/r = 2.0
- **변경 시**: alpha를 r과 동일(=1.0) → 안전 / 4 × r(=4.0) → 강한 학습

### lora_dropout
- 본 연구 **dropout=0.10**
- 이유: 소규모 데이터 → 과적합 방지. SOBA(7,800건)의 0.05보다 강함
- **변경 시**:
  - 학습 후 train_loss << eval_loss (과적합) → 0.15로 ↑
  - 학습 부족 (loss 안 떨어짐) → 0.05로 ↓

### target_modules
- 본 연구 **q/k/v/o/gate/up/down_proj 7개 모두**
- 이유: Qwen3 표준. attention만 (q/k/v/o)는 성능 낮음
- **변경 시**: MLP 제외 시 학습 파라미터 ~40%로 감소 (속도 ↑, 성능 ↓)

---

## 3. 학습 hyperparameter 선택 근거

### num_train_epochs
- 본 연구 **5 epochs**
- 이유: Early stopping (patience=2)로 자동 종료. 보통 3 epoch에서 best
- **변경 시**: 학습이 너무 빨리 끝나면 (1 epoch만에 best) → 10으로 ↑

### batch_size + gradient_accumulation
- 본 연구 **per_device=1 × grad_accum=16 = 실효 16**
- 이유: max_seq_length=8192이라 batch=1 강제. A100 80GB도 batch=2 위험
- **변경 시**:
  - VRAM 여유 시 batch=2, grad_accum=8 (실효 16 유지)
  - max_seq_length=4096으로 줄이면 batch=4도 가능

### learning_rate
- 본 연구 **2.0e-4**
- 이유: QLoRA 표준값 (Full FT는 1e-5~5e-5, LoRA는 1e-4~5e-4)
- **변경 시**:
  - NaN loss → 5e-5로 ↓
  - 학습 너무 느림 → 5e-4로 ↑ (위험, warmup 필요)

### lr_scheduler
- 본 연구 **cosine**
- 이유: 후반부 안정 수렴. linear는 마지막에 lr=0이라 미세 조정 약함
- **변경 시**: constant_with_warmup이 더 단순 (epoch 적을 때)

### warmup_ratio
- 본 연구 **0.05** (전체 스텝의 5%)
- 이유: 표준. 초기 불안정성 방지
- **변경 시**: epoch 많으면 0.03, 적으면 0.1

### optim
- 본 연구 **paged_adamw_8bit**
- 이유: QLoRA 표준. AdamW + 8bit + paged memory (대용량 모델에 효율적)
- **변경 시**: 표준 AdamW (32bit)는 VRAM 추가 2-3GB 필요

### bf16 vs fp16
- 본 연구 **bf16: true, fp16: false**
- 이유: A100/H100은 bfloat16 네이티브 지원. fp16보다 안정 (NaN 위험 ↓)
- **변경 시**: V100/T4 등 구형 GPU는 fp16: true 사용

### gradient_checkpointing
- 본 연구 **true**
- 이유: 메모리 절약 (~20% 추가 여유). 속도 ~20% 감소
- **변경 시**: VRAM 충분하면 false → 학습 속도 ↑

### max_seq_length
- 본 연구 **8192**
- 이유: Phase 2 토큰 통계 P95 ~6,500, max ~7,800 → 8192가 안전 마진
- **변경 시**:
  - 4096: 일부 record 잘림 (~5%), VRAM 절약
  - 16384: 거의 모든 record 안전, but VRAM ↑↑

---

## 4. Early Stopping 설정

- **monitor**: eval_loss (낮을수록 좋음)
- **patience**: 2 epochs
- **load_best_model_at_end**: true → 최저 eval_loss epoch 사용
- **save_strategy**: epoch (매 epoch checkpoint 저장)
- **save_total_limit**: 3 (디스크 절약)

---

## 5. 예상 학습 곡선

| Epoch | train_loss | eval_loss | 비고 |
|-------|-----------|-----------|------|
| 1 | ~3.0 → ~1.8 | ~2.5 → ~2.0 | 빠른 감소 |
| 2 | ~1.8 → ~1.2 | ~2.0 → ~1.7 | 안정 학습 |
| 3 | ~1.2 → ~1.0 | ~1.7 → ~1.6 | **best 후보** |
| 4 | ~1.0 → ~0.9 | ~1.6 → ~1.65 | 과적합 시작 |
| 5 | ~0.9 → ~0.85 | ~1.65 → ~1.7 | early stop 발동 |

**예상 최종**:
- best eval_loss: ~1.6 (epoch 3)
- final adapter는 epoch 3 모델 자동 채택

---

## 6. 비교 — SOBA 프로젝트 hyperparameter

| 파라미터 | SOBA (7,800건) | TransferJudge (578건) | 차이 이유 |
|---------|---------------|---------------------|-----------|
| LoRA r | 32 | 16 | 데이터 규모 |
| dropout | 0.05 | 0.10 | 과적합 방지 강화 |
| epochs | 3 | 5 | early stop 활용 |
| batch_size | 4 | 1 | max_seq_length 차이 (768 vs 8192) |
| grad_accum | 2 | 16 | 실효 배치 동일 (8 vs 16) |
| max_seq_length | 768 | 8192 | 챗봇 vs 추천 시스템 |
| lr | 2e-4 | 2e-4 | 동일 |
| optim | paged_adamw_8bit | paged_adamw_8bit | 동일 |
| bf16 | true | true | 동일 |

---

## 7. Best Practice 체크리스트

학습 시작 전:

- [ ] `configs/judge_training.yaml`의 `report_to`: wandb 사용 여부 결정
- [ ] `model.name`이 정확한 모델인지 확인 (`Qwen/Qwen3-14B`)
- [ ] `data.train_path`가 실제 존재하는지 확인
- [ ] `output.adapter_dir`로 사용할 디스크 공간 확보 (>50MB)
- [ ] HF token이 Qwen3-14B 모델 접근 권한 있는지 (gated일 수 있음)

학습 중:

- [ ] 첫 10분 안에 loss가 감소하는지 확인
- [ ] eval_loss가 train_loss 대비 2배 이상 크면 → 과적합 의심
- [ ] GPU 사용률 90% 이상인지 확인 (낮으면 I/O 병목)

학습 후:

- [ ] best_eval_loss가 합리적 (e.g., < 2.0)
- [ ] 어댑터 파일 정상 (`adapter_model.safetensors` 존재)
- [ ] 추론 테스트로 출력 형식 확인
- [ ] HF Hub에 백업 (RunPod 인스턴스 종료 대비)
