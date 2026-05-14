"""Phase 3 — Qwen3-14B QLoRA 파인튜닝 (Judge 모델 학습).

학습 데이터: data/teacher_train_main.jsonl (578줄, chat format)
모델: Qwen/Qwen3-14B (4-bit quantization + LoRA adapter)
환경: RunPod A100 80GB 1대 (예상 6~8시간, $3~$5)

사용법 (RunPod):
    pip install -r requirements.txt
    python3 scripts/train_judge.py \\
        --training-data data/teacher_train_main.jsonl \\
        --valid-data data/valid_users.parquet \\
        --model Qwen/Qwen3-14B \\
        --output checkpoints/judge_v1 \\
        --batch-size 1 --grad-accum 16 --epochs 3 --lr 2e-4

설정 (논문 기준값):
    - LoRA: r=16, alpha=32, dropout=0.05
    - target_modules: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
    - max_seq_length: 8192 (Qwen3 컨텍스트 활용)
    - batch_size: 1 × grad_accum 16 = effective 16
    - learning_rate: 2e-4 (LoRA 표준)
    - warmup_ratio: 0.03
    - epochs: 3
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, prepare_model_for_kbit_training, get_peft_model
from trl import SFTTrainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


def load_training_data(path: Path) -> Dataset:
    """teacher_train_main.jsonl을 HF Dataset으로 로드."""
    records = []
    for line in open(path):
        d = json.loads(line)
        records.append(d)
    logging.info(f"Loaded {len(records)} training records from {path}")
    return Dataset.from_list(records)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--training-data", type=Path,
                   default=Path("data/teacher_train_main.jsonl"))
    p.add_argument("--model", default="Qwen/Qwen3-14B")
    p.add_argument("--output", type=Path, default=Path("checkpoints/judge_v1"))
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--grad-accum", type=int, default=16)
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--max-seq-length", type=int, default=8192)
    p.add_argument("--lora-r", type=int, default=16)
    p.add_argument("--lora-alpha", type=int, default=32)
    p.add_argument("--lora-dropout", type=float, default=0.05)
    p.add_argument("--warmup-ratio", type=float, default=0.03)
    p.add_argument("--save-steps", type=int, default=50)
    p.add_argument("--logging-steps", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    # ===== 1. Tokenizer =====
    logging.info(f"Loading tokenizer from {args.model}")
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ===== 2. Model with 4-bit quantization =====
    logging.info("Loading model with 4-bit quantization (QLoRA)")
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)

    # ===== 3. LoRA config =====
    lora = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    # ===== 4. Dataset =====
    dataset = load_training_data(args.training_data)

    # ===== 5. Training args =====
    training_args = TrainingArguments(
        output_dir=str(args.output),
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        warmup_ratio=args.warmup_ratio,
        lr_scheduler_type="cosine",
        bf16=True,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=3,
        seed=args.seed,
        report_to="none",  # wandb 사용 시 "wandb"로
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
    )

    # ===== 6. SFTTrainer =====
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        tokenizer=tokenizer,
        max_seq_length=args.max_seq_length,
        args=training_args,
        packing=False,
    )

    logging.info("=== Starting training ===")
    trainer.train()

    logging.info(f"=== Saving final adapter to {args.output} ===")
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    logging.info("✅ Training complete.")


if __name__ == "__main__":
    main()
