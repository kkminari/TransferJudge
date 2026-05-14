# 🚀 TransferJudge 본 실험 — 진행 추적기

> **이 파일 하나로 본 실험을 처음부터 끝까지 진행 가능**
> 현재 위치 즉시 파악: `python3 scripts/check_main_progress.py`

---

# 🎯 지금 상황 (한눈에)  ※ 2026-05-14 업데이트

```
████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 5/14 단계 완료 (36%)
```

| 단계 | 상태 | 환경 |
|---|---|:---:|
| ✅ **0. 전제 조건 점검** | 완료 (2026-05-12) | 💻 Mac |
| ✅ **1. Profiler 본 실행 v1** | 완료 — temporal leakage 발견 후 폐기 | 💻 Mac |
| ✅ **1.v2 Profiler 재생성** | **완료 ★ 1,000명 Profile, $0.84, 5h 40m** | 💻 Mac |
| ✅ **2. Teacher Distillation** | **완료 ★ 578줄 (정합성 정리 후), $3.30, 9h 1m** | 💻 Mac |
| ✅ **2.5. GitHub + HF Hub 동기화** | **완료** [`kkminari/TransferJudge`](https://github.com/kkminari/TransferJudge) + `kwaksuobusi/transferjudge-data` | 🔄 |
| 🟡 **3. QLoRA 파인튜닝** | **← 지금 여기 (다음 작업)** | ☁️ RunPod |
| ⬜ 4a. Ablation (c) Ours | 대기 | ☁️ RunPod |
| ⬜ 4b. Ablation (a)(b)(d)(f) | 대기 | 💻 + ☁️ |
| ⬜ 4c. Ablation (e) 전통 CDR | 대기 | ☁️ RunPod |
| ⬜ 5a. Per-Pattern Ablation | 대기 | ☁️ RunPod |
| ⬜ 5b. Cold-Start 분석 | 대기 | 💻 Mac |
| ⬜ 6. 결과 분석 + 통계 | 대기 | 💻 Mac |
| ⬜ 7. 논문 초고 | 대기 | 💻 Mac |

**누적 비용**: **$4.32** (Phase 0~2.5) | **누적 시간**: **~17h** | **남은 예상**: ~$10~15 (Phase 3~5)

**Phase 2 최종 데이터** (Codex 외부 리뷰 1차·2차 반영, 8개 결함 모두 수정):
- 학습 데이터: **`data/teacher_train_main.jsonl` · 578줄**
- 분할: train 578 / valid 100 / test 100 — **train·valid·test 누수 0건**
- 정합성: out-of-candidate 0 · duplicate 0 · title exact mismatch 0 · BLOCK leakage 0 · GT title leakage 0 · 7-pattern 완전성 100%
- 정리 이력: orphan 1 제거, low-signal 23 제거, title 79 정규화

**다음 액션 (RunPod GPU 환경에서)**:
```bash
git clone https://github.com/kkminari/TransferJudge.git && cd TransferJudge
pip install -r requirements.txt
export HF_TOKEN=hf_새토큰   # https://huggingface.co/settings/tokens
huggingface-cli login --token $HF_TOKEN
python3 scripts/download_data_runpod.py --repo kwaksuobusi/transferjudge-data
nohup python3 scripts/train_judge.py \
  --training-data data/teacher_train_main.jsonl \
  --output checkpoints/judge_v1 > logs/train.log 2>&1 &
tail -f logs/train.log
```

---

# 🗺️ 환경별 작업 분담

| 환경 | 담당 Phase | 비용 |
|---|---|:---:|
| 💻 **Mac 로컬** (API만) | 0, 1, 2, 4b-i, 4b-ii, 5b, 6, 7 | API ~$6~9 |
| ☁️ **RunPod GPU** | 3, 4a, 4b-iii, 4b-iv, 4c, 5a | $20~40 (RTX 4090) |
| 🔄 **GitHub** | 2.5, 5b 동기화 | — |

---

# ✅ Phase 0 — 전제 조건 점검 (완료)

**완료일**: 2026-05-12

- [x] **0.1** `.env`에 `OPENAI_API_KEY` 존재
- [x] **0.2** 디스크 여유 ≥ 5GB
- [x] **0.3** Python 패키지 설치
- [x] **0.4** 데이터 파일 존재
- [x] **0.5** 사용자 수 확인 (Train 800, Valid 100, Test 100)
- [x] **0.6** GitHub 저장소 준비
- [x] **0.7** RunPod 계정 (Phase 3 진입 전 필요)

→ ✅ 모든 전제 조건 충족

---

# ✅ Phase 1 — Profiler 본 실행 1,000명 (완료)

**완료일**: 2026-05-12 (4시간 17분)
**환경**: 💻 Mac 로컬

## 📊 결과 요약
| 지표 | 결과 |
|---|---|
| 처리 사용자 | **1,000 / 1,000 (100%)** |
| 7-pattern 완전성 | **100%** |
| 실패 | **0건** |
| 평균 confidence | 0.647 |
| 빈 evidence | 3.1% (목표 ≤5%) |
| 총 비용 | **$0.83** (예상 $0.82와 일치) |
| 분할 일관성 | Train/Valid/Test mean 0.641~0.648 (완벽) |

## 🔍 핵심 발견
- **brand_loyalty 약한 신호 1,000명 규모 재검증**: avg_conf 0.455, 빈 evidence 14.4%, conf≤0.3 비율 50.3%
- → Pilot Study의 BLOCK 후보 가설이 1,000명에서도 일관됨

## 📋 작업 체크리스트 (모두 완료)
- [x] **1.1** Train 800명 Profiler 실행 ($0.660)
- [x] **1.2** Valid 100명 실행 ($0.083)
- [x] **1.3** Test 100명 실행 ($0.087)
- [x] **1.4** 출력 검증 (스크립트로 자동)
- [x] **1.5** Profile 품질 sample 검토 (3개 케이스 정성 검토)

## 📑 산출물
- `profiler_outputs/user_*.json` × 1,000
- `docs/phase1/Phase1_Profiler_Report.pdf` ← **상세 결과 보고서**
- `docs/phase1/Profiler_Process_Example.pdf` ← **작동 예시**
- `logs/phase1_full.log` ← 실행 로그

---

# 🟡 Phase 2 — Teacher Distillation (다음 작업)

**환경**: 💻 Mac 로컬 (OpenAI API)
**목표**: Train 800 + Valid 100명에 대해 GPT-4o-mini Teacher로 transfer_decisions + Top-10 recommendations 생성
**예상**: ~6시간, $2~3

## 📋 작업 체크리스트
- [ ] **2.1** Train 800명 Teacher 실행 → `data/teacher_train.jsonl`
- [ ] **2.2** Valid 100명 Teacher 실행 → `data/teacher_val.jsonl`
- [ ] **2.3** 출력 검증 (라인 수, 7-pattern 완전성)
- [ ] **2.4** BLOCK 누출 검사 (BLOCK 패턴이 applied_patterns에 포함됐는지)
- [ ] **2.5** GT 누출 검사 (rationale에 ground truth 언급)
- [ ] **2.6** 5명 sample 정성 검토 👤

## ▶️ 시작 명령
```bash
# 1. Train 800명 (~5h, $2.4)
python3 scripts/run_teacher.py \
  --users data/train_users.parquet \
  --profiles profiler_outputs/ \
  --output data/teacher_train.jsonl \
  --split train

# 2. Valid 100명 (~0.6h, $0.3)
python3 scripts/run_teacher.py \
  --users data/valid_users.parquet \
  --profiles profiler_outputs/ \
  --output data/teacher_val.jsonl \
  --split valid
```

## 🔁 재개 명령 (중단 시)
이미 처리된 user_id는 skip되도록 스크립트가 동작 — 위 명령 그대로 재실행

## ✅ 검증 명령
```bash
# 라인 수 확인 (기대: train 760~800, val 90~100)
wc -l data/teacher_train.jsonl data/teacher_val.jsonl

# 7-pattern 완전성 + BLOCK 누출 검사
python3 -c "
import json
ok, total, leak = 0, 0, 0
for line in open('data/teacher_train.jsonl'):
    d = json.loads(line); total += 1
    decisions = d.get('transfer_decisions', {})
    if len(decisions) == 7: ok += 1
    blocked = [p for p,v in decisions.items() if v.get('decision')=='BLOCK']
    if any(p in r.get('applied_patterns',[]) for r in d.get('recommendations',[]) for p in blocked):
        leak += 1
print(f'완전성: {ok}/{total}, BLOCK 누출: {leak}')
"
```

## 🎯 완료 기준
- [ ] teacher_train.jsonl: 760~800 lines (실패 ≤ 5%)
- [ ] teacher_val.jsonl: 90~100 lines
- [ ] 7-pattern 완전성 = 100%
- [ ] BLOCK 누출 0건
- [ ] GT 누출 0건

## ⚠️ 위험·대응
| 위험 | 대응 |
|---|---|
| BLOCK 누출 발생 | 해당 샘플 제외 또는 후처리 필터 |
| GT 누출 | 정규식 검출 후 제외 |
| Top-10 미달 | 후보 풀에서 추가 fill |

---

# ⬜ Phase 2.5 — GitHub Push & RunPod 동기화

**환경**: 💻 Mac → 🔄 GitHub → ☁️ RunPod
**목표**: Phase 1, 2 결과를 RunPod에 전달
**예상**: ~30분

## 📋 작업 체크리스트
- [ ] **2.5.1** `.gitignore` 최종 점검 (이미 완료 — 검증만)
- [ ] **2.5.2** 로컬에서 commit + GitHub push
- [ ] **2.5.3** HF Hub에 대용량 데이터 업로드 (`upload_data_to_hub.py`)
- [ ] **2.5.4** RunPod 인스턴스 생성 (RTX 4090, 24GB VRAM)
- [ ] **2.5.5** RunPod에서 git clone + 환경 설정
- [ ] **2.5.6** RunPod에서 HF Hub 데이터 다운로드 (`download_data_runpod.py`)
- [ ] **2.5.7** RunPod에서 진단 스크립트 실행 → Phase 1·2 ✅ 확인

## ▶️ 핵심 명령

### Mac에서 (한 번만)
```bash
# 1. HF Hub 로그인
huggingface-cli login

# 2. 대용량 데이터 업로드
python3 scripts/upload_data_to_hub.py \
  --repo USERNAME/transferjudge-data \
  --private

# 3. Git commit + push
git add profiler_outputs/ data/teacher_*.jsonl .gitignore docs/ scripts/ prompts/
git commit -m "Phase 1, 2 complete"
git push origin main
```

### RunPod에서
```bash
cd /workspace
git clone https://github.com/USERNAME/transferjudge.git
cd transferjudge
pip install -r requirements.txt  # (또는 개별 설치)
huggingface-cli login
python3 scripts/download_data_runpod.py --repo USERNAME/transferjudge-data
python3 scripts/check_main_progress.py  # Phase 1·2 ✅ 확인
```

---

# ⬜ Phase 3 — QLoRA 파인튜닝

**환경**: ☁️ RunPod GPU
**목표**: Qwen3-14B + QLoRA로 Teacher 출력 학습 → best checkpoint 확보
**예상**: ~12시간, $5~8 (RTX 4090)

## 📋 작업 체크리스트
- [ ] **3.1** 학습 설정 점검 (LoRA r=16, lr=2e-4, 3 epoch)
- [ ] **3.2** 학습 실행 (백그라운드)
- [ ] **3.3** Validation loss 곡선 확인
- [ ] **3.4** Best checkpoint 선택
- [ ] **3.5** Smoke test (10명 추론)
- [ ] **3.6** 학습 로그 검토 (overfitting 여부) 👤
- [ ] **3.7** (선택) HuggingFace Hub 백업

## ▶️ 시작 명령 (RunPod)
```bash
python3 scripts/train_judge_qlora.py \
  --train data/teacher_train.jsonl \
  --val data/teacher_val.jsonl \
  --base_model Qwen/Qwen3-14B-Instruct \
  --output_dir checkpoints/ \
  --lora_r 16 --lora_alpha 32 \
  --epochs 3 --batch_size 1 --grad_accum 8 \
  --learning_rate 2e-4 \
  --save_strategy epoch --eval_strategy epoch \
  --load_best_model_at_end
```

## 🔁 재개 명령
```bash
python3 scripts/train_judge_qlora.py \
  --resume_from_checkpoint $(ls -t checkpoints/judge_checkpoint_* | head -1)
```

## 🎯 완료 기준
- [ ] `checkpoints/judge_best/` 존재
- [ ] val_loss 감소 (best < initial)
- [ ] Smoke test 10명 ≥ 9건 유효 JSON

## ⚠️ 위험·대응
| 위험 | 대응 |
|---|---|
| OOM | `--grad_accum 16`, `--max_seq_len 2048` |
| Overfitting | epoch ↓ (3→2), early stopping |
| 학습 발산 | lr ↓ (2e-4 → 1e-4) |

---

# ⬜ Phase 4 — Ablation 6개 조건

## Phase 4a — (c) Ours (메인 결과)
**환경**: ☁️ RunPod | **시간**: ~2시간

- [ ] **4a.1** Test 100명에 대해 (c) 추론
- [ ] **4a.2** LOO 평가 (HR@1,5,10, NDCG@5,10, MRR)
- [ ] **4a.3** 결과 검토 (NDCG@10 ≥ 0.08 목표)

```bash
python3 scripts/evaluate.py --condition c_ours \
  --judge_ckpt checkpoints/judge_best/ \
  --test_users data/test_users.parquet \
  --profiles profiler_outputs/ \
  --output results/ablation_c_ours.json
```

## Phase 4b — 4개 Ablation
**시간**: 각 ~2시간

### 4b-i (a) Single LLM — 💻 Mac
- [ ] (a) Single LLM 실행 → `results/ablation_a_single.json`

### 4b-ii (b) Profiler-Judge Prompt-only — 💻 Mac
- [ ] (b) Prompt-only 실행 → `results/ablation_b_prompt.json`

### 4b-iii (d) w/o Gate — ☁️ RunPod
- [ ] (d) w/o Gate 실행 → `results/ablation_d_no_gate.json`

### 4b-iv (f) Raw Review — ☁️ RunPod
- [ ] (f) Raw Review 실행 → `results/ablation_f_raw.json`

## Phase 4c — (e) 전통 CDR
**환경**: ☁️ RunPod | **시간**: ~4시간

- [ ] **4c.1** EMCDR 또는 CoNet 구현 확보
- [ ] **4c.2** 동일 데이터로 학습
- [ ] **4c.3** 평가 실행

```bash
python3 scripts/train_eval_traditional_cdr.py --method emcdr \
  --output results/ablation_e.json
```

## 🎯 Phase 4 완료 기준
- [ ] 6개 결과 파일 모두 생성 (`results/ablation_*.json`)
- [ ] 동일 사용자 100명, 동일 후보 50개 (seed=42)

---

# ⬜ Phase 5 — 추가 Ablation

## Phase 5a — Per-Pattern Ablation
**환경**: ☁️ RunPod | **시간**: ~2시간

- [ ] **5a.1** 7개 패턴 각각 제거하며 (c) Ours 재평가
- [ ] **5a.2** 7×3 (패턴 × NDCG/HR/MRR) heatmap 생성

```bash
for p in genre_preference narrative_complexity pacing_preference \
         quality_sensitivity brand_loyalty sensory_preference emotional_resonance; do
  python3 scripts/evaluate.py --condition c_ours --ablate_pattern $p \
    --output results/per_pattern_${p}.json
done
```

## Phase 5b — RunPod → 로컬 동기화 + Cold-Start 분석
**환경**: ☁️ RunPod → 💻 Mac

- [ ] **5b.1** RunPod에서 결과 git push
- [ ] **5b.2** Mac에서 git pull
- [ ] **5b.3** Cold-Start segment 분석 (Severe/Moderate/Warm)
- [ ] **5b.4** RunPod 인스턴스 일시 정지 (비용 절감)

```bash
# RunPod에서: git push
git add results/ && git commit -m "Phase 3-5 results" && git push

# Mac에서: pull + 분석
git pull && python3 scripts/analyze_cold_start.py \
  --results "results/ablation_*.json" \
  --output results/cold_start_analysis.csv
```

---

# ⬜ Phase 6 — 결과 분석 + 통계

**환경**: 💻 Mac | **시간**: ~1주

- [ ] **6.1** 메인 결과표 생성 (조건 × 지표 + CI)
- [ ] **6.2** RQ별 가설 검증 (Wilcoxon signed-rank)
- [ ] **6.3** Per-pattern heatmap 최종화
- [ ] **6.4** Cold-Start 비교 차트
- [ ] **6.5** BLOCK 누출 정성 분석
- [ ] **6.6** 한계 + 향후 작업 정리
- [ ] **6.7** 분석 내러티브 작성 (`docs/Results_Analysis.md`)

## 📐 가설 검증 표 (작성용)
| 가설 | 비교 | 결과 | p-value | 통과 |
|---|---|:---:|:---:|:---:|
| H_main | (c) > (a) | ___ | ___ | ⬜ |
| H_gate | (c) > (d) | ___ | ___ | ⬜ |
| H_ft | (c) > (b) | ___ | ___ | ⬜ |
| H_struct | (c) > (f) | ___ | ___ | ⬜ |
| H_cold | Severe Cold-Start 우위 | ___ | ___ | ⬜ |

→ **5개 중 ≥3개 통과 시 contribution 입증**

---

# ⬜ Phase 7 — 논문 초고

**환경**: 💻 Mac | **시간**: ~1주

- [ ] **7.1** §1 Introduction
- [ ] **7.2** §2 Related Work
- [ ] **7.3** §3 Methodology (Profiler-Judge + Transfer Gate)
- [ ] **7.4** §4 Experiments (데이터, Pilot, Ablation 설계)
- [ ] **7.5** §5 Results
- [ ] **7.6** §6 Discussion
- [ ] **7.7** §7 Conclusion
- [ ] **7.8** 참고문헌 정리
- [ ] **7.9** 지도교수 1차 검토 받기

---

# 📐 사전 등록 가설 (Phase 6에서 검증)

| ID | 가설 | 비교 |
|:---:|---|---|
| **H_main** | Profiler-Judge (FT) > Single LLM | (c) vs (a) |
| **H_gate** | Gate ON > Gate OFF | (c) vs (d) |
| **H_ft** | FT > Prompt-only | (c) vs (b) |
| **H_struct** | 구조화 Profile > Raw Review | (c) vs (f) |
| **H_cold** | Severe Cold-Start 우위 | segment 비교 |

---

# 🗂️ 산출물 디렉토리 구조

```
.
├── profiler_outputs/         ✅ Phase 1 완료 (1,000개)
├── data/
│   ├── teacher_train.jsonl   ⬜ Phase 2 산출
│   ├── teacher_val.jsonl     ⬜ Phase 2 산출
│   ├── *_users.parquet       ✅ EDA 완료
│   └── *_meta_filtered.parquet ⛔ .gitignore (HF Hub 동기화)
├── checkpoints/              ⬜ Phase 3 산출 (RunPod 볼륨)
├── results/                  ⬜ Phase 4~5 산출
└── docs/
    ├── pilot/                ✅ Pilot Study 완료
    ├── overview/             ✅ Overview v6 완료
    ├── phase1/               ✅ Phase 1 보고서 완료
    ├── eda/                  ✅ EDA 보고서 완료
    └── plans/
        ├── MainExperiment_Tracker.md  ← 본 파일
        └── Results_Analysis.md         ⬜ Phase 6 산출
```

---

# 🆘 자주 쓰는 명령

```bash
# 1️⃣ 어디까지 됐는지 확인
python3 scripts/check_main_progress.py

# 2️⃣ 다음 작업 진입
# → 본 파일에서 "🟡" 표시된 Phase 섹션 찾기
# → ▶️ 시작 명령 실행

# 3️⃣ 작업 후 검증
# → 해당 Phase의 ✅ 검증 명령

# 4️⃣ 중단된 경우 재개
# → 해당 Phase의 🔁 재개 명령 (skip 로직 활용)
```

---

# 💰 비용·시간 누적 트래커

| 단계 | 시간 | 비용 | 누적 비용 |
|---|:---:|:---:|:---:|
| ✅ Phase 1 | 4h 17분 | $0.83 | **$0.83** |
| ⬜ Phase 2 | ~6h | $2~3 | ~$3~4 |
| ⬜ Phase 3 | ~12h GPU | $5~8 | ~$8~12 |
| ⬜ Phase 4a | ~2h GPU | $1 | ~$9~13 |
| ⬜ Phase 4b-i,ii | ~4h | $3~5 | ~$12~18 |
| ⬜ Phase 4b-iii,iv | ~4h GPU | $2 | ~$14~20 |
| ⬜ Phase 4c | ~4h GPU | $2 | ~$16~22 |
| ⬜ Phase 5a | ~2h GPU | $1 | ~$17~23 |
| ⬜ Phase 5b | ~1h | — | ~$17~23 |
| **총 예상** | ~40시간 | **~$17~23** | |

---

> **본 파일 사용 규칙**
> 1. Phase 완료 시 체크박스 `[ ]` → `[x]` 직접 변경 + 상단 진행률 표 갱신
> 2. 매번 작업 시작 전 `python3 scripts/check_main_progress.py` 실행
> 3. 어떤 Phase 어디서 시작해야 하는지 헷갈리면 "🟡 다음 작업" 표시된 Phase 찾기
> 4. 중단·재개 시 해당 Phase의 "🔁 재개 명령" 사용
