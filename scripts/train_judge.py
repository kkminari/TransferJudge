"""TransferJudge — Phase 3 Judge 모델 QLoRA 파인튜닝.

Qwen3-14B 모델을 QLoRA 방식으로 파인튜닝.
학습 데이터: data/teacher_train_main.jsonl (578줄, chat format).

실행 (RunPod):
    python3 scripts/train_judge.py
    python3 scripts/train_judge.py --config configs/judge_training.yaml

설계 참고: SOBA finetuning project (Qwen3-14B QLoRA 동일 구조).
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

import random

import torch
import yaml
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    EarlyStoppingCallback,
)
from transformers.trainer_utils import get_last_checkpoint
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTConfig, SFTTrainer


# ============================================================
# 1. 설정 로드
# ============================================================

def load_config(config_path: str | None = None) -> dict:
    if config_path is None:
        config_path = Path(__file__).parent.parent / "configs" / "judge_training.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    print(f"설정 로드: {config_path}")
    print(f"  모델: {config['model']['name']}")
    print(f"  LoRA r: {config['lora']['r']}")
    print(f"  Epochs: {config['training']['num_train_epochs']}")
    print(f"  max_seq_length: {config['model']['max_seq_length']}")
    return config


# ============================================================
# 2. 데이터 로드 + train/valid 분리
# ============================================================

def load_jsonl(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def load_dataset_from_jsonl(config: dict) -> tuple[Dataset, Dataset]:
    """teacher_train_main.jsonl을 로드하고 train/valid로 분리.

    seed 고정 shuffle 후 마지막 N% 분리 (분포 치우침 방지).
    여기서 분리하는 valid는 학습 중 monitoring용 (early stopping 트리거).
    Phase 4 평가용 test 100명은 Phase 2 split 재정의에서 별도 holdout으로 분리됨.
    """
    train_path = Path(config["data"]["train_path"])
    all_records = load_jsonl(train_path)

    # ★ seed shuffle 후 split (Codex 피드백 반영)
    ratio = float(config["data"]["val_ratio_from_train"])
    seed = int(config["data"].get("val_split_seed", 42))
    rng = random.Random(seed)
    shuffled = list(all_records)
    rng.shuffle(shuffled)
    n_val = int(len(shuffled) * ratio)
    val_records = shuffled[-n_val:]
    train_records = shuffled[:-n_val]

    print(f"\n데이터 로드: {train_path}")
    print(f"  train: {len(train_records)}줄, val: {len(val_records)}줄 "
          f"(총 {len(all_records)}줄, shuffle seed={seed})")

    return Dataset.from_list(train_records), Dataset.from_list(val_records)


def measure_token_lengths(dataset: Dataset, tokenizer, n_sample: int = 50) -> tuple[float, int]:
    """messages를 tokenize한 토큰 길이 통계 (max_seq_length 검증용)."""
    sample_lengths = []
    for i in range(min(n_sample, len(dataset))):
        messages = dataset[i]["messages"]
        ids = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=False,
        )
        sample_lengths.append(len(ids))
    avg_len = sum(sample_lengths) / len(sample_lengths)
    max_len = max(sample_lengths)
    return avg_len, max_len


# ============================================================
# 3. 모델 로드 (QLoRA)
# ============================================================

_QWEN3_ASSISTANT_BLOCK_ORIGINAL = """{%- elif message.role == "assistant" %}
        {%- set reasoning_content = '' %}
        {%- if message.reasoning_content is string %}
            {%- set reasoning_content = message.reasoning_content %}
        {%- else %}
            {%- if '</think>' in content %}
                {%- set reasoning_content = content.split('</think>')[0].rstrip('\\n').split('<think>')[-1].lstrip('\\n') %}
                {%- set content = content.split('</think>')[-1].lstrip('\\n') %}
            {%- endif %}
        {%- endif %}
        {%- if loop.index0 > ns.last_query_index %}
            {%- if loop.last or (not loop.last and reasoning_content) %}
                {{- '<|im_start|>' + message.role + '\\n<think>\\n' + reasoning_content.strip('\\n') + '\\n</think>\\n\\n' + content.lstrip('\\n') }}
            {%- else %}
                {{- '<|im_start|>' + message.role + '\\n' + content }}
            {%- endif %}
        {%- else %}
            {{- '<|im_start|>' + message.role + '\\n' + content }}
        {%- endif %}
        {%- if message.tool_calls %}
            {%- for tool_call in message.tool_calls %}
                {%- if (loop.first and content) or (not loop.first) %}
                    {{- '\\n' }}
                {%- endif %}
                {%- if tool_call.function %}
                    {%- set tool_call = tool_call.function %}
                {%- endif %}
                {{- '<tool_call>\\n{"name": "' }}
                {{- tool_call.name }}
                {{- '", "arguments": ' }}
                {%- if tool_call.arguments is string %}
                    {{- tool_call.arguments }}
                {%- else %}
                    {{- tool_call.arguments | tojson }}
                {%- endif %}
                {{- '}\\n</tool_call>' }}
            {%- endfor %}
        {%- endif %}
        {{- '<|im_end|>\\n' }}"""

_QWEN3_ASSISTANT_BLOCK_PATCHED = """{%- elif message.role == "assistant" %}
        {%- set reasoning_content = '' %}
        {%- if message.reasoning_content is string %}
            {%- set reasoning_content = message.reasoning_content %}
        {%- else %}
            {%- if '</think>' in content %}
                {%- set reasoning_content = content.split('</think>')[0].rstrip('\\n').split('<think>')[-1].lstrip('\\n') %}
                {%- set content = content.split('</think>')[-1].lstrip('\\n') %}
            {%- endif %}
        {%- endif %}
        {{- '<|im_start|>' + message.role + '\\n' }}
        {% generation %}
        {%- if loop.index0 > ns.last_query_index %}
            {%- if loop.last or (not loop.last and reasoning_content) %}
                {{- '<think>\\n' + reasoning_content.strip('\\n') + '\\n</think>\\n\\n' + content.lstrip('\\n') }}
            {%- else %}
                {{- content }}
            {%- endif %}
        {%- else %}
            {{- content }}
        {%- endif %}
        {%- if message.tool_calls %}
            {%- for tool_call in message.tool_calls %}
                {%- if (loop.first and content) or (not loop.first) %}
                    {{- '\\n' }}
                {%- endif %}
                {%- if tool_call.function %}
                    {%- set tool_call = tool_call.function %}
                {%- endif %}
                {{- '<tool_call>\\n{"name": "' }}
                {{- tool_call.name }}
                {{- '", "arguments": ' }}
                {%- if tool_call.arguments is string %}
                    {{- tool_call.arguments }}
                {%- else %}
                    {{- tool_call.arguments | tojson }}
                {%- endif %}
                {{- '}\\n</tool_call>' }}
            {%- endfor %}
        {%- endif %}
        {{- '<|im_end|>\\n' }}
        {% endgeneration %}"""


def _patch_chat_template_for_generation(tokenizer):
    """Qwen3 chat template에 ``{% generation %}`` 마커를 주입.

    TRL ``assistant_only_loss=True``는 ``apply_chat_template(return_assistant_tokens_mask=True)``
    가 마스크를 반환해야 동작하고, 그 마스크는 템플릿이 ``{% generation %}``/``{% endgeneration %}``
    로 assistant 응답 영역을 표시해야 생성됨. Qwen3 기본 템플릿은 이 마커가 없어
    학습 시 ``RuntimeError: at least one example has no assistant tokens`` 가 발생함.

    원본 assistant 블록의 prefix ``<|im_start|>assistant\\n`` 출력을 분리하고 그 뒤로
    ``{% generation %}`` 을 열어 content와 tool_calls, 닫는 ``<|im_end|>\\n`` 까지
    전부 포함시킴. system/user/tool 분기는 그대로 보존. 본 함수는 학습 토크나이저에만 적용;
    Phase 4 추론은 원본 템플릿 사용 권장 (이 패치를 호출하지 않으면 됨).
    """
    ct = tokenizer.chat_template
    if ct is None or "{% generation %}" in ct:
        return tokenizer

    if _QWEN3_ASSISTANT_BLOCK_ORIGINAL not in ct:
        raise RuntimeError(
            "chat_template 패치 실패 — assistant 블록 원본 시그니처가 일치하지 않음. "
            "Qwen3 템플릿 버전이 바뀌었거나 다른 모델일 수 있음."
        )
    tokenizer.chat_template = ct.replace(
        _QWEN3_ASSISTANT_BLOCK_ORIGINAL,
        _QWEN3_ASSISTANT_BLOCK_PATCHED,
        1,
    )
    return tokenizer


def load_model_and_tokenizer(config: dict):
    model_name = config["model"]["name"]
    quant_cfg = config["quantization"]
    print(f"\n모델 로드: {model_name}")

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        print(f"  pad_token 설정: {tokenizer.pad_token}")

    _patch_chat_template_for_generation(tokenizer)
    print("  chat_template: {% generation %} 마커 주입 완료 (assistant_only_loss 활성화 위함)")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=quant_cfg["load_in_4bit"],
        bnb_4bit_quant_type=quant_cfg["bnb_4bit_quant_type"],
        bnb_4bit_compute_dtype=getattr(torch, quant_cfg["bnb_4bit_compute_dtype"]),
        bnb_4bit_use_double_quant=quant_cfg["bnb_4bit_use_double_quant"],
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="sdpa",
    )
    model = prepare_model_for_kbit_training(model)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"  총 파라미터: {total_params / 1e9:.1f}B")
    return model, tokenizer


# ============================================================
# 4. LoRA 어댑터 부착
# ============================================================

def apply_lora(model, config: dict):
    lora_cfg = config["lora"]
    lora_config = LoraConfig(
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"],
        lora_dropout=lora_cfg["lora_dropout"],
        target_modules=lora_cfg["target_modules"],
        bias=lora_cfg["bias"],
        task_type=lora_cfg["task_type"],
    )
    model = get_peft_model(model, lora_config)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    pct = trainable / total * 100
    print(f"\nLoRA 적용: r={lora_cfg['r']}, alpha={lora_cfg['lora_alpha']}, dropout={lora_cfg['lora_dropout']}")
    print(f"  학습 파라미터: {trainable / 1e6:.1f}M / {total / 1e6:.0f}M ({pct:.2f}%)")
    return model


# ============================================================
# 5. 학습 실행
# ============================================================

def train(config: dict):
    # --- 런타임 환경 출력 (Codex 권장: 버전 조합 검증) ---
    try:
        import transformers as _hf, trl as _trl, peft as _peft
        print(f"\n[환경] transformers={_hf.__version__}, trl={_trl.__version__}, peft={_peft.__version__}")
        # Qwen3 권장 최소 버전 체크
        hf_v = tuple(int(x) for x in _hf.__version__.split(".")[:2])
        if hf_v < (4, 46):
            print(f"  ⚠ transformers < 4.46 — Qwen3 chat template 이슈 가능")
    except Exception as e:
        print(f"  ⚠ 버전 출력 실패: {e}")

    # --- WandB (선택) ---
    use_wandb = config["training"].get("report_to") == "wandb"
    if use_wandb:
        try:
            import wandb
            wandb.init(
                project=config["wandb"]["project"],
                name=config["wandb"]["run_name"],
                config=config,
            )
            print(f"\nWandB: {config['wandb']['project']} / {config['wandb']['run_name']}")
        except Exception as e:
            print(f"WandB 초기화 실패 ({e}) → report_to='none'으로 진행")
            config["training"]["report_to"] = "none"
            use_wandb = False

    # --- 데이터 로드 ---
    train_dataset, val_dataset = load_dataset_from_jsonl(config)

    # --- 모델 + 토크나이저 ---
    model, tokenizer = load_model_and_tokenizer(config)

    # --- LoRA ---
    model = apply_lora(model, config)

    # --- Chat template 적용 ---
    # ★ Codex P1 반영: messages 컬럼을 그대로 유지하여 TRL이 conversational dataset으로 인식.
    # 사전에 text로 변환하면 assistant mask가 생성되지 않아 prompt까지 loss 계산됨.
    # SFTTrainer가 내부에서 tokenizer.apply_chat_template + assistant_only_loss mask를 자동 적용.
    print("\nConversational format 유지 (messages 컬럼) — TRL이 chat template + assistant mask 자동 처리")

    # --- 토큰 길이 검증 (messages 기반) ---
    avg_len, max_len = measure_token_lengths(train_dataset, tokenizer, n_sample=50)
    max_seq = config["model"]["max_seq_length"]
    print(f"\n토큰 길이 (샘플 50건):")
    print(f"  평균: {avg_len:.0f}, 최대: {max_len}, max_seq_length: {max_seq}")
    if max_len > max_seq:
        print(f"  ⚠ 일부 샘플이 max_seq_length 초과 → 잘림 가능")

    # --- 학습 설정 ---
    train_cfg = config["training"]
    output_cfg = config["output"]
    total_steps = (
        len(train_dataset)
        // train_cfg["per_device_train_batch_size"]
        // train_cfg["gradient_accumulation_steps"]
        * train_cfg["num_train_epochs"]
    )
    warmup_steps = int(total_steps * train_cfg["warmup_ratio"])

    # ★ Codex P1 반영: dataset_text_field 제거 → TRL이 messages를 conversational dataset으로 처리
    # ★ assistant_only_loss=True: assistant 토큰만 loss 계산 (TRL>=0.13)
    sft_kwargs = dict(
        output_dir=output_cfg["output_dir"],
        num_train_epochs=train_cfg["num_train_epochs"],
        per_device_train_batch_size=train_cfg["per_device_train_batch_size"],
        per_device_eval_batch_size=train_cfg["per_device_eval_batch_size"],
        gradient_accumulation_steps=train_cfg["gradient_accumulation_steps"],
        learning_rate=train_cfg["learning_rate"],
        lr_scheduler_type=train_cfg["lr_scheduler_type"],
        warmup_steps=warmup_steps,
        optim=train_cfg["optim"],
        fp16=train_cfg["fp16"],
        bf16=train_cfg["bf16"],
        gradient_checkpointing=train_cfg.get("gradient_checkpointing", True),
        logging_steps=train_cfg["logging_steps"],
        eval_strategy=train_cfg["eval_strategy"],
        save_strategy=train_cfg["save_strategy"],
        save_total_limit=train_cfg.get("save_total_limit", 3),
        load_best_model_at_end=train_cfg["load_best_model_at_end"],
        metric_for_best_model=train_cfg["metric_for_best_model"],
        greater_is_better=train_cfg["greater_is_better"],
        report_to=train_cfg["report_to"],
        seed=train_cfg.get("seed", 42),
        # dataset_text_field 제거 — messages 컬럼이 있으면 TRL이 자동으로 conversational 처리
        max_length=config["model"]["max_seq_length"],
    )
    # smoke test 시 강제 종료 step
    if train_cfg.get("_max_steps_override"):
        sft_kwargs["max_steps"] = int(train_cfg["_max_steps_override"])
        print(f"  🧪 smoke test: max_steps={sft_kwargs['max_steps']}")
    # ★ assistant_only_loss: 논문용 학습이라 hard fail (조용한 prompt 학습 방지)
    if train_cfg.get("assistant_only_loss"):
        try:
            sft_config = SFTConfig(**sft_kwargs, assistant_only_loss=True)
            print("  ✅ assistant_only_loss=True (prompt 토큰은 loss에서 제외)")
        except TypeError as e:
            raise RuntimeError(
                "현재 TRL 버전이 assistant_only_loss를 지원하지 않습니다. "
                "본 연구는 prompt 토큰이 loss에 포함되면 학습 품질이 보장되지 않습니다.\n"
                "조치: pip install -U 'trl>=0.13' 또는 최신 trl 설치 후 재실행.\n"
                f"원인: {e}"
            )
    else:
        sft_config = SFTConfig(**sft_kwargs)
        print("  ⚠ assistant_only_loss 미설정 — prompt 토큰까지 loss에 포함됨 (config 확인 권장)")

    print(f"\n학습 설정:")
    print(f"  실효 배치: {train_cfg['per_device_train_batch_size']} × {train_cfg['gradient_accumulation_steps']} = {train_cfg['per_device_train_batch_size'] * train_cfg['gradient_accumulation_steps']}")
    print(f"  총 스텝: ~{total_steps}, 워밍업: {warmup_steps}")

    # --- Trainer ---
    is_smoke = bool(train_cfg.get("_max_steps_override"))
    callbacks = []
    if not is_smoke:
        patience = config.get("early_stopping", {}).get("patience", 2)
        callbacks.append(EarlyStoppingCallback(early_stopping_patience=patience))

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_dataset,
        eval_dataset=None if is_smoke else val_dataset,
        processing_class=tokenizer,
        callbacks=callbacks,
    )

    # ★ resume_from_checkpoint: output_dir에 이전 checkpoint 있으면 자동 이어서
    resume_ckpt = None
    output_dir = Path(output_cfg["output_dir"])
    if output_dir.exists():
        last = get_last_checkpoint(str(output_dir))
        if last is not None:
            resume_ckpt = last
            print(f"\n🔄 Resume detected: {last}")

    print("\n" + "=" * 60)
    print("학습 시작!" if resume_ckpt is None else f"학습 재개! (from {resume_ckpt})")
    print("=" * 60)
    trainer.train(resume_from_checkpoint=resume_ckpt)

    # --- 어댑터 저장 ---
    adapter_dir = output_cfg["adapter_dir"]
    Path(adapter_dir).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    print(f"\n어댑터 저장: {adapter_dir}")

    adapter_size = sum(f.stat().st_size for f in Path(adapter_dir).rglob("*") if f.is_file())
    print(f"어댑터 크기: {adapter_size / 1e6:.1f}MB")

    # --- 최종 메트릭 ---
    final_metrics = trainer.state.log_history
    train_losses = [h["loss"] for h in final_metrics if "loss" in h]
    eval_losses = [h["eval_loss"] for h in final_metrics if "eval_loss" in h]
    print(f"\n최종 메트릭:")
    if train_losses:
        print(f"  train_loss (last): {train_losses[-1]:.4f}")
    if eval_losses:
        print(f"  eval_loss  (last): {eval_losses[-1]:.4f} (best: {min(eval_losses):.4f})")

    if use_wandb:
        import wandb
        wandb.finish()
    print("\n학습 완료!")


# ============================================================
# 메인
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TransferJudge Phase 3 QLoRA 파인튜닝")
    parser.add_argument("--config", type=str, default=None,
                        help="설정 파일 경로 (기본: configs/judge_training.yaml)")
    parser.add_argument("--smoke-test", action="store_true",
                        help="2 step만 학습해 파이프라인 검증 (RunPod 첫 실행 권장)")
    args = parser.parse_args()

    config = load_config(args.config)

    # ★ Codex P2 반영: smoke test — 의존성·API 조합·assistant_only_loss 작동 확인
    if args.smoke_test:
        print("\n" + "=" * 60)
        print("🧪 SMOKE TEST MODE — 2 step만 학습해 파이프라인 검증")
        print("=" * 60)
        config["training"]["num_train_epochs"] = 1
        config["training"]["save_strategy"] = "no"
        config["training"]["eval_strategy"] = "no"
        config["training"]["load_best_model_at_end"] = False
        config["training"]["logging_steps"] = 1
        config["training"]["report_to"] = "none"
        config["training"]["_max_steps_override"] = 2
        # ★ smoke test 결과를 본 학습 dir과 분리 — 충돌 방지
        config["output"]["output_dir"] = "checkpoints/_smoke_test"
        config["output"]["adapter_dir"] = "checkpoints/_smoke_test/adapter"
        print(f"  smoke output_dir: {config['output']['output_dir']}")
        print(f"  (본 학습은 'checkpoints/judge_v1'를 사용 — 충돌 없음)")

    train(config)
