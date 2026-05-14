# Phase 3 RunPod Quickstart — 복붙용 명령어 모음

> **이 파일을 RunPod 터미널에 직접 복붙해 진행**
> 자세한 설명·근거는 `Phase3_Training_Plan.pdf` 참조

---

## ⚡ 0. 빠른 흐름 (요약)

```
RunPod A100 80GB 인스턴스 → clone → install → HF token → download → train → upload
                    10분        5분    3분      10분     5분    7-8h    5분
```

총 ~9시간, ~$5

---

## 1. RunPod 인스턴스 설정

| 항목 | 권장값 |
|------|--------|
| GPU | A100 80GB (또는 H100 80GB) |
| Template | PyTorch 2.2 + CUDA 12.1 |
| Container Disk | 100GB |
| Volume Disk | 50GB (checkpoint 영속화) |

---

## 2. SSH 접속 후 환경 셋업

```bash
# 작업 디렉토리
cd /workspace

# 저장소 clone
git clone https://github.com/kkminari/TransferJudge.git
cd TransferJudge

# 의존성 설치 (~3-5분)
pip install -r requirements.txt

# HF Token (https://huggingface.co/settings/tokens 에서 발급, read 권한)
export HF_TOKEN=hf_새토큰값
huggingface-cli login --token $HF_TOKEN

# (선택) WandB — 기본은 OFF (config에 report_to: "none")
# 모니터링 원하면 config 수정 후:
#   sed -i 's/report_to: "none"/report_to: "wandb"/' configs/judge_training.yaml
#   export WANDB_API_KEY=...
#   wandb login $WANDB_API_KEY
```

---

## 3. books_meta 다운로드 (2.4GB)

```bash
python3 scripts/download_data_runpod.py --repo kwaksuobusi/transferjudge-data

# 다운로드 확인
ls -lh data/books_meta_filtered.parquet
# 예상: 2.4GB
```

---

## 4. 학습 시작 (백그라운드)

```bash
# 로그 디렉토리 생성
mkdir -p logs checkpoints

# 학습 실행 (nohup background)
nohup python3 scripts/train_judge.py \
  --config configs/judge_training.yaml \
  > logs/train.log 2>&1 &

# PID 확인
echo "PID: $!"

# 진행 monitoring (Ctrl+C로 빠져나와도 학습은 계속)
tail -f logs/train.log
```

---

## 5. 학습 중 상태 확인

```bash
# 프로세스 살아있는지
ps aux | grep train_judge | grep -v grep

# 최근 loss
grep -E "loss|eval_loss" logs/train.log | tail -10

# GPU 사용률 (별도 터미널)
watch -n 2 nvidia-smi

# 디스크 사용량
du -sh checkpoints/
```

---

## 6. 학습 종료 후

```bash
# 완료 확인
grep "학습 완료" logs/train.log

# 어댑터 크기 확인 (~50MB)
du -sh checkpoints/judge_v1/adapter/

# HF Hub로 어댑터 백업 (권장)
huggingface-cli upload kwaksuobusi/transferjudge-judge-v1 \
  checkpoints/judge_v1/adapter \
  --repo-type=model --private
```

---

## 7. 트러블슈팅 (자주 발생)

### OOM (Out of Memory)
```bash
# configs/judge_training.yaml 수정:
#   model.max_seq_length: 8192 → 4096
#   training.per_device_train_batch_size: 1 (이미 최소)
#   training.gradient_checkpointing: true (이미 활성)
```

### Qwen3-14B gated 모델 오류
```bash
# https://huggingface.co/Qwen/Qwen3-14B 페이지에서 License Agreement 수락 필요
# 그 후 huggingface-cli login 재실행
```

### NaN loss
```bash
# configs/judge_training.yaml 수정:
#   training.learning_rate: 2.0e-4 → 5.0e-5
#   training.bf16: true (fp16: false 확인)
```

### Connection error (HF/WandB)
```bash
# WandB 비활성화
sed -i 's/report_to: "wandb"/report_to: "none"/' configs/judge_training.yaml

# 또는 환경변수
export WANDB_MODE=offline
```

### 학습 중단 후 재개
```bash
# train_judge.py가 output_dir의 최신 checkpoint를 자동 감지 + resume_from_checkpoint로 이어감
python3 scripts/train_judge.py --config configs/judge_training.yaml
# 로그에 "🔄 Resume detected: checkpoint-XXX" 출력 확인
```

---

## 8. 학습 결과 검증 (Phase 4 진입 전)

```bash
# 1) eval_loss 추이 확인
python3 -c "
import json
with open('checkpoints/judge_v1/trainer_state.json') as f:
    state = json.load(f)
losses = [(h['epoch'], h.get('eval_loss')) for h in state['log_history'] if 'eval_loss' in h]
for e, l in losses:
    print(f'epoch {e}: eval_loss={l:.4f}')
"

# 2) 한 사용자에 대해 추론 테스트 (선택)
python3 -c "
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
tok = AutoTokenizer.from_pretrained('checkpoints/judge_v1/adapter')
base = AutoModelForCausalLM.from_pretrained('Qwen/Qwen3-14B', torch_dtype=torch.bfloat16, device_map='auto')
model = PeftModel.from_pretrained(base, 'checkpoints/judge_v1/adapter')
print('✅ Adapter 로드 성공')
"
```

---

## 9. RunPod 종료 시 (비용 절감)

```bash
# 1) 어댑터를 HF Hub에 백업 (위 §6)
# 2) 로그 GitHub에 commit
git add logs/train.log checkpoints/judge_v1/trainer_state.json
git commit -m "Phase 3 학습 완료 로그"
git push origin main

# 3) RunPod 인스턴스 STOP (콘솔에서)
# Volume에 어댑터 남아있으므로 다음에 켤 때 재사용 가능
```
