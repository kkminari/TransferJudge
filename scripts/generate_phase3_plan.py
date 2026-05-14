"""Phase 3 학습 계획 PDF 생성 — RunPod에서 바로 학습 시작 가능한 가이드.

산출: docs/phase3/Phase3_Training_Plan.pdf
참고: SOBA finetuning project FINETUNING_SETUP_GUIDE.md
"""
from __future__ import annotations

from pathlib import Path
import weasyprint

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "docs/phase3/Phase3_Training_Plan.pdf"


def main():
    html = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 2cm 1.8cm; @bottom-center { content: counter(page); font-size: 10px; color: #999; } }
  body { font-family: -apple-system, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif; font-size: 10pt; line-height: 1.55; color: #222; }
  h1 { text-align: center; font-size: 19pt; margin-bottom: 5px; color: #1a1a2e; }
  .subtitle { text-align: center; font-size: 10.5pt; color: #555; margin-bottom: 3px; }
  .author { text-align: center; font-size: 10pt; color: #777; margin-bottom: 22px; }
  h2 { font-size: 14pt; color: #16213e; border-bottom: 2.5px solid #4a90d9; padding-bottom: 4px; margin-top: 24px; }
  h3 { font-size: 11.5pt; color: #0f3460; margin-top: 14px; }
  table { width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 9.5pt; }
  th { background: #16213e; color: white; padding: 5px 8px; text-align: left; font-weight: 600; }
  td { padding: 5px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }
  tr:nth-child(even) td { background: #f8f9fa; }
  .pagebreak { page-break-before: always; }
  .callout { background: #f0f4f8; border-left: 4px solid #4a90d9; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }
  .callout-green { background: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }
  .callout-warn { background: #fff8e1; border-left: 4px solid #f5a623; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }
  .callout-red { background: #ffebee; border-left: 4px solid #c62828; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }
  code { background: #f0f4f8; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }
  pre { background: #1a1a2e; color: #e8e8e8; padding: 10px 14px; border-radius: 5px; font-size: 8.8pt; overflow-wrap: break-word; white-space: pre-wrap; word-wrap: break-word; line-height: 1.4; }
  .stat-card { display: inline-block; background: white; border: 1.5px solid #4a90d9; border-radius: 5px; padding: 8px 12px; margin: 4px; text-align: center; min-width: 120px; }
  .stat-card .num { font-size: 16pt; font-weight: 700; color: #16213e; }
  .stat-card .label { font-size: 8.5pt; color: #555; margin-top: 2px; }
  ol li { margin: 4px 0; }
</style>
</head>
<body>

<h1>Phase 3 학습 계획 — Qwen3-14B QLoRA</h1>
<p class="subtitle">TransferJudge · RunPod GPU 환경 학습 가이드</p>
<p class="author">2026.05.14 · 빅데이터학과 17기 곽민아</p>

<div class="callout-green">
<strong>한 줄 요약</strong><br>
Phase 2에서 생성한 578줄 학습 데이터로 Qwen3-14B 모델을 QLoRA 방식으로 파인튜닝.
RunPod A100 80GB 1대, 약 6~8시간, $3~$5 예상. 산출물은 약 50MB LoRA adapter.
</div>

<h2>0. 핵심 지표</h2>

<div>
  <div class="stat-card"><div class="num">578</div><div class="label">학습 데이터 (lines)</div></div>
  <div class="stat-card"><div class="num">14B</div><div class="label">모델 파라미터</div></div>
  <div class="stat-card"><div class="num">~0.3%</div><div class="label">실제 학습 (LoRA)</div></div>
  <div class="stat-card"><div class="num">~7h</div><div class="label">예상 시간</div></div>
  <div class="stat-card"><div class="num">$3~$5</div><div class="label">예상 비용</div></div>
</div>

<!-- ====== 1. 목적·배경 ====== -->
<h2>1. Phase 3의 목적과 위치</h2>

<table>
<tr><th>측면</th><th>내용</th></tr>
<tr><td>목적</td><td>Phase 2에서 GPT-4o-mini가 만든 시범 답안 578개를 <strong>Qwen3-14B Judge 모델이 따라 학습</strong>하도록 함</td></tr>
<tr><td>방식</td><td>지식 증류(Knowledge Distillation) → Teacher(GPT-4o-mini)의 추론 능력을 Student(Qwen3-14B)에게 이식</td></tr>
<tr><td>학습 후</td><td>Judge가 새 사용자의 Profile만 보고 transfer_decisions + Top-10 추천을 직접 생성 가능</td></tr>
<tr><td>왜 QLoRA?</td><td>14B 모델을 24~80GB GPU 1대로 학습 가능 (전체 FT 시 80GB+ 필요)</td></tr>
<tr><td>이후 단계</td><td>Phase 4 (Ablation 6 conditions) → Phase 5 (Per-Pattern 분석)</td></tr>
</table>

<!-- ====== 2. 학습 데이터 ====== -->
<h2>2. 학습 데이터 명세</h2>

<table>
<tr><th>항목</th><th>값</th></tr>
<tr><td>파일</td><td><code>data/teacher_train_main.jsonl</code></td></tr>
<tr><td>줄 수</td><td>578줄</td></tr>
<tr><td>포맷</td><td>OpenAI/Qwen chat format (system + user + assistant)</td></tr>
<tr><td>한 줄 평균 토큰</td><td>약 5,000 토큰 (입력 ~4,500 + 출력 ~500)</td></tr>
<tr><td>P95 토큰</td><td>~6,500</td></tr>
<tr><td>최대 토큰</td><td>~7,800 (max_seq_length 8192 안)</td></tr>
<tr><td>분할</td><td>학습 중 마지막 10% (58줄)를 valid로 자동 분리 (early stopping 트리거)</td></tr>
<tr><td>품질 보장</td><td>Codex 외부 리뷰 8개 결함 모두 수정 후 confirmed</td></tr>
</table>

<div class="callout">
<strong>train/valid 분리 메커니즘</strong>: 본 Phase에서 학습 monitoring용 valid는 train 데이터 마지막 10%를 자동 분리.
Phase 4 평가용 test 100명은 <strong>학습 데이터에 들어가지 않은 별도 holdout</strong> (Phase 2 split 재정의에서 보장).
</div>

<!-- ====== 3. RunPod 환경 셋업 ====== -->
<h2 class="pagebreak">3. RunPod 환경 셋업</h2>

<h3>3.1 인스턴스 선택</h3>

<table>
<tr><th>GPU</th><th>VRAM</th><th>시간당 요금</th><th>적합도</th></tr>
<tr><td><strong>A100 80GB</strong></td><td>80GB</td><td>~$1.5-2.0</td><td>✅ <strong>권장</strong> — 안전 마진</td></tr>
<tr><td>A100 40GB</td><td>40GB</td><td>~$1.0-1.3</td><td>가능 (배치=1 필수)</td></tr>
<tr><td>RTX 4090</td><td>24GB</td><td>~$0.5-0.8</td><td>가능 (max_seq_length 4096까지)</td></tr>
<tr><td>H100 80GB</td><td>80GB</td><td>~$2.5-4.0</td><td>가능 (속도 ↑ but cost 증가)</td></tr>
</table>

<h3>3.2 RunPod 템플릿</h3>

<table>
<tr><th>설정</th><th>값</th></tr>
<tr><td>Template</td><td>PyTorch 2.2 + CUDA 12.1</td></tr>
<tr><td>Disk</td><td>최소 100GB (모델 캐시 + 데이터)</td></tr>
<tr><td>Volume</td><td>50GB 권장 (체크포인트 영속화)</td></tr>
<tr><td>Container Start Command</td><td>(기본 jupyter 또는 SSH)</td></tr>
</table>

<h3>3.3 환경 변수</h3>

<pre>HF_TOKEN=hf_새토큰값             # https://huggingface.co/settings/tokens (read 권한)
WANDB_API_KEY=...                # 선택, monitoring용 (https://wandb.ai/settings)</pre>

<!-- ====== 4. 학습 명령어 (복붙 가능) ====== -->
<h2 class="pagebreak">4. 학습 실행 — 복붙 가능 명령어</h2>

<h3>4.1 환경 준비</h3>

<pre># SSH 접속 후 작업 디렉토리로 이동
cd /workspace   # 또는 /root

# 저장소 clone
git clone https://github.com/kkminari/TransferJudge.git
cd TransferJudge

# Python 의존성 설치 (~3-5분)
pip install -r requirements.txt

# HF 로그인 (token은 https://huggingface.co/settings/tokens 에서 발급)
export HF_TOKEN=hf_새토큰값
huggingface-cli login --token $HF_TOKEN

# WandB 로그인 (선택, monitoring용)
export WANDB_API_KEY=...
# 사용 안 할 경우 configs/judge_training.yaml의 report_to를 "none"으로 변경</pre>

<h3>4.2 books_meta 다운로드 (HF Hub)</h3>

<pre># 약 2.4GB · 5~10분
python3 scripts/download_data_runpod.py --repo kwaksuobusi/transferjudge-data

# 다운로드 확인
ls -lh data/books_meta_filtered.parquet
# 예상: 2.4GB</pre>

<h3>4.3 학습 시작</h3>

<pre># 백그라운드 실행 + 로그 저장
mkdir -p logs checkpoints

nohup python3 scripts/train_judge.py \\
  --config configs/judge_training.yaml \\
  > logs/train.log 2>&1 &

# PID 확인
echo "PID: $!"

# 진행 모니터링
tail -f logs/train.log</pre>

<h3>4.4 학습 종료 확인</h3>

<pre># 종료 감지
grep "학습 완료" logs/train.log

# 어댑터 크기 확인 (~50MB)
du -sh checkpoints/judge_v1/adapter/

# 최종 메트릭 확인
grep -E "train_loss|eval_loss" logs/train.log | tail -10</pre>

<!-- ====== 5. 하이퍼파라미터 설계 ====== -->
<h2 class="pagebreak">5. 하이퍼파라미터 설계 + 근거</h2>

<h3>5.1 LoRA 설정</h3>

<table>
<tr><th>파라미터</th><th>값</th><th>근거</th></tr>
<tr><td>r (rank)</td><td>16</td>
    <td>데이터 578건 (소~중규모) → 16이 적절 (가이드: 500~5,000건 = 16~32, 본 연구는 하한)</td></tr>
<tr><td>lora_alpha</td><td>32</td>
    <td>2 × r (스케일링 = alpha/r = 2.0, 표준)</td></tr>
<tr><td>lora_dropout</td><td>0.1</td>
    <td>소규모 데이터 → 과적합 방지 (SOBA의 0.05보다 강함)</td></tr>
<tr><td>target_modules</td><td>q/k/v/o/gate/up/down_proj</td>
    <td>Attention + MLP 전체 (Qwen3 표준)</td></tr>
<tr><td>학습 파라미터</td><td>~40M / 14B</td>
    <td>전체의 ~0.3%만 학습</td></tr>
</table>

<h3>5.2 학습 hyperparameter</h3>

<table>
<tr><th>파라미터</th><th>값</th><th>근거</th></tr>
<tr><td>num_train_epochs</td><td>5</td>
    <td>소규모 데이터 → 3~5 (early stopping으로 자동 종료 가능)</td></tr>
<tr><td>per_device_batch_size</td><td>1</td>
    <td>max_seq_length=8192 → VRAM 절약 필수</td></tr>
<tr><td>gradient_accumulation_steps</td><td>16</td>
    <td>실효 배치 = 1 × 16 = <strong>16</strong> (학습 안정성)</td></tr>
<tr><td>learning_rate</td><td>2.0e-4</td>
    <td>QLoRA 표준 (Full FT는 1e-5, LoRA는 1e-4 ~ 5e-4)</td></tr>
<tr><td>lr_scheduler</td><td>cosine</td>
    <td>후반부 안정 수렴</td></tr>
<tr><td>warmup_ratio</td><td>0.05</td>
    <td>전체 스텝의 5% 워밍업</td></tr>
<tr><td>optim</td><td>paged_adamw_8bit</td>
    <td>메모리 효율적 (QLoRA 표준)</td></tr>
<tr><td>bf16</td><td>true</td>
    <td>A100/H100 권장 (FP16보다 안정)</td></tr>
<tr><td>gradient_checkpointing</td><td>true</td>
    <td>메모리 절약 (느리지만 안전)</td></tr>
<tr><td>max_seq_length</td><td>8192</td>
    <td>P95 토큰 ~6,500 커버 (Phase 2 통계)</td></tr>
</table>

<h3>5.3 Early Stopping</h3>

<table>
<tr><th>설정</th><th>값</th></tr>
<tr><td>monitor</td><td>eval_loss</td></tr>
<tr><td>patience</td><td>2 epochs</td></tr>
<tr><td>최종 모델</td><td>load_best_model_at_end=true → 최저 eval_loss epoch 사용</td></tr>
</table>

<h3>5.4 예상 스텝·시간</h3>

<table>
<tr><th>항목</th><th>계산</th><th>값</th></tr>
<tr><td>총 스텝</td><td>578 × 5 epochs ÷ (1 × 16)</td><td>약 180 스텝</td></tr>
<tr><td>워밍업</td><td>180 × 0.05</td><td>9 스텝</td></tr>
<tr><td>스텝당 시간</td><td>A100 80GB 기준 추정</td><td>약 2~3분</td></tr>
<tr><td>총 학습 시간</td><td>180 스텝 × 2.5분</td><td>약 7~8시간</td></tr>
</table>

<!-- ====== 6. 모니터링 + 트러블슈팅 ====== -->
<h2 class="pagebreak">6. 모니터링 + 트러블슈팅</h2>

<h3>6.1 학습 중 모니터링</h3>

<table>
<tr><th>지표</th><th>정상 범위</th><th>이상 신호</th></tr>
<tr><td>train_loss</td><td>3.0 → 1.0 (감소)</td><td>NaN, ∞, 변화 없음</td></tr>
<tr><td>eval_loss</td><td>train_loss + 0~0.5</td><td>train보다 크게 높음 → 과적합</td></tr>
<tr><td>학습률</td><td>cosine 곡선 추종</td><td>0 또는 발산</td></tr>
<tr><td>GPU 사용률</td><td>90~99%</td><td>50% 이하 → 데이터 IO 병목</td></tr>
<tr><td>VRAM</td><td>40~60GB (80GB GPU)</td><td>OOM → batch_size 또는 max_seq_length 줄임</td></tr>
</table>

<h3>6.2 자주 나는 문제 + 해결</h3>

<table>
<tr><th>증상</th><th>원인</th><th>해결</th></tr>
<tr><td>OutOfMemoryError</td><td>VRAM 부족</td>
    <td>(1) <code>per_device_train_batch_size: 1</code> 확인<br>
        (2) <code>max_seq_length</code>를 4096으로 축소<br>
        (3) <code>gradient_checkpointing: true</code> 확인</td></tr>
<tr><td>NaN loss</td><td>FP 정밀도 문제</td>
    <td>(1) <code>bf16: true</code>인지 확인 (fp16 X)<br>
        (2) <code>learning_rate</code>를 5e-5로 낮춤</td></tr>
<tr><td>HF token 오류</td><td>인증 실패</td>
    <td><code>huggingface-cli login</code> 재실행. Qwen3-14B는 gated 모델일 수 있음 — 모델 페이지 동의 필요</td></tr>
<tr><td>Connection error</td><td>WandB·HF API 일시 장애</td>
    <td>(1) <code>report_to: "none"</code>으로 WandB 비활성화<br>
        (2) 30초 대기 후 재시도</td></tr>
<tr><td>학습 너무 느림</td><td>I/O 병목</td>
    <td>(1) <code>num_workers</code> 증가 (SFTConfig)<br>
        (2) 데이터셋을 미리 chat template 적용 후 캐시</td></tr>
<tr><td>RunPod 인스턴스 끊김</td><td>네트워크</td>
    <td>checkpoint가 매 epoch 저장됨 → 재시작 시 <code>resume_from_checkpoint=True</code></td></tr>
</table>

<h3>6.3 중단·재개</h3>

<pre># 중단 (Ctrl+C 또는 SIGTERM)
kill $(pgrep -f train_judge.py)

# 재개 (마지막 checkpoint부터)
python3 scripts/train_judge.py --config configs/judge_training.yaml
# (SFTTrainer가 output_dir의 checkpoint를 자동 감지하여 resume)</pre>

<!-- ====== 7. 학습 후 산출물 ====== -->
<h2 class="pagebreak">7. 학습 후 산출물 + 다음 단계</h2>

<h3>7.1 산출물 디렉토리 구조</h3>

<pre>checkpoints/judge_v1/
├── adapter/                          # ← LoRA 어댑터 (최종 산출, ~50MB)
│   ├── adapter_config.json
│   ├── adapter_model.safetensors
│   ├── tokenizer.json
│   └── tokenizer_config.json
├── checkpoint-36/                    # epoch 1
├── checkpoint-72/                    # epoch 2
├── checkpoint-108/                   # epoch 3 (best)
└── trainer_state.json                # 학습 메트릭 전체</pre>

<h3>7.2 GitHub 또는 HF Hub로 백업</h3>

<pre># 옵션 A: GitHub LFS (50MB는 무료 한도 내)
cd checkpoints/judge_v1/adapter
git lfs install
git lfs track "*.safetensors"
git add .gitattributes adapter_model.safetensors adapter_config.json tokenizer*
# (혹은 별도 모델 repo로)

# 옵션 B (권장): HuggingFace Hub
huggingface-cli upload kwaksuobusi/transferjudge-judge-v1 \\
  checkpoints/judge_v1/adapter --repo-type=model --private</pre>

<h3>7.3 다음 단계 (Phase 4·5)</h3>

<table>
<tr><th>Phase</th><th>내용</th><th>입력</th><th>비용·시간</th></tr>
<tr><td>4a</td><td>Ablation (c) Ours — 학습된 Judge로 test 100명 추천 평가</td>
    <td>checkpoints/judge_v1/adapter + test_users.parquet</td><td>$0.5~$1, 1-2h</td></tr>
<tr><td>4b</td><td>Ablation (a)(b)(d)(f) — 베이스라인 비교</td>
    <td>GPT-4o-mini / Claude / w/o Gate / Random</td><td>$2~$3, 2-3h</td></tr>
<tr><td>4c</td><td>Ablation (e) — 전통 CDR 베이스라인</td>
    <td>EMCDR/PTUPCDR/TrineCDR 등</td><td>$1, 2-3h</td></tr>
<tr><td>5a</td><td>Per-Pattern Ablation (7개 패턴 각각 BLOCK)</td>
    <td>Judge × 7 conditions</td><td>$2~$3, 3-4h</td></tr>
<tr><td>5b</td><td>Cold-Start segment 분석</td>
    <td>test set의 cold-start cohort 분석</td><td>$0, 1h</td></tr>
</table>

<h3>7.4 핵심 평가 지표 (Phase 4)</h3>

<table>
<tr><th>지표</th><th>설명</th><th>목표</th></tr>
<tr><td>Hit@10</td><td>Top-10 안에 GT 책 포함 비율</td><td>≥ 60% (Teacher 60.2% 비교 기준)</td></tr>
<tr><td>NDCG@10</td><td>순위 가중 평가</td><td>높을수록 좋음</td></tr>
<tr><td>MRR</td><td>Mean Reciprocal Rank</td><td>높을수록 좋음</td></tr>
<tr><td>Pattern Decision Accuracy</td><td>transfer_decisions가 Teacher와 일치하는 비율</td><td>≥ 80%</td></tr>
<tr><td>JSON 파싱 성공률</td><td>유효 JSON 출력 비율</td><td>≥ 95%</td></tr>
<tr><td>BLOCK leakage 0건</td><td>BLOCK 패턴이 추천 근거로 사용되지 않음</td><td>100% 통과</td></tr>
</table>

<!-- ====== 8. 일정 + 비용 ====== -->
<h2>8. 일정 + 비용 요약</h2>

<table>
<tr><th>단계</th><th>작업</th><th>예상 시간</th><th>예상 비용</th></tr>
<tr><td>0</td><td>RunPod 인스턴스 생성 + SSH 접속</td><td>10분</td><td>-</td></tr>
<tr><td>1</td><td>저장소 clone + 의존성 설치</td><td>5-10분</td><td>~$0.3 (GPU idle)</td></tr>
<tr><td>2</td><td>HF Hub에서 books_meta 다운로드</td><td>5-10분</td><td>~$0.3</td></tr>
<tr><td>3</td><td>학습 명령 실행 + 진행 모니터링</td><td>7-8시간</td><td><strong>$3~$5</strong></td></tr>
<tr><td>4</td><td>어댑터 검증 + HF Hub 업로드</td><td>30분</td><td>~$1</td></tr>
<tr><td><strong>Phase 3 총합</strong></td><td>-</td><td><strong>약 8-9시간</strong></td><td><strong>$5~$7</strong></td></tr>
</table>

<div class="callout-green">
<strong>한 번에 진행 가능</strong>: GPU instance 켜 둔 채 위 명령 순서대로 실행. 학습은 background로 돌리고 다른 일 하면 됨.
RunPod 무료 SSH·Jupyter 둘 다 사용 가능.
</div>

</body>
</html>
"""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    weasyprint.HTML(string=html).write_pdf(str(OUTPUT_PATH))
    print(f"✅ Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
