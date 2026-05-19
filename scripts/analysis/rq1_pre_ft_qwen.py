"""RQ1 보강 — Base Qwen3-14B (pre-FT) vs Fine-tuned Qwen3-14B Transfer Judge 비교.

본 스크립트는 RunPod A100 GPU에서 실행합니다.

Base Qwen3-14B를 4-bit quantization으로 로드 → 100명 test fixture 대상으로
Zero-shot + Few-shot 두 가지 setting으로 transfer_decisions 생성.

비교:
  - Pre-FT zero-shot: base Qwen3-14B + Teacher prompt
  - Pre-FT few-shot:  base Qwen3-14B + Teacher prompt + 3 in-context 예시
  - Post-FT (이미 측정됨): fine-tuned Qwen3-14B QLoRA (results/ablation_c_ours.json)

평가 (Mac에서 다음 스크립트로):
  - Teacher decisions 대비 agreement (overall + per-pattern)
  - Macro-F1, per-class F1 (TRANSFER/PARTIAL/BLOCK)
  - JSON format success rate
  - 7-pattern completeness

사용법 (RunPod):
    cd /workspace/TransferJudge
    .venv_thesis/bin/python scripts/analysis/rq1_pre_ft_qwen.py \\
        --setting zero_shot \\
        --output results/analysis/rq1_pre_ft_qwen_zero_shot.json

    .venv_thesis/bin/python scripts/analysis/rq1_pre_ft_qwen.py \\
        --setting few_shot \\
        --output results/analysis/rq1_pre_ft_qwen_few_shot.json

요구사항:
    pip install transformers accelerate bitsandbytes pandas pyarrow
    HF_TOKEN environment variable (Qwen 다운로드)

GPU 메모리: 14B × 4bit ≈ 8GB. A100 40GB 이상 권장.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from run_teacher import format_candidate

MODEL_NAME = "Qwen/Qwen3-14B"
MAX_NEW_TOKENS = 2500

# Teacher SYSTEM_PROMPT (GT 힌트 부분 제거)
SYSTEM_PROMPT_NO_GT = """You are an expert Cross-Domain Transfer Judge. Your task is to decide \
how a user's Movies & TV preference patterns should transfer to Books recommendations, and \
produce a Top-10 ranked list of books.

## The 3-Level Transfer Gate

For each preference pattern in the profile, decide one of:

**TRANSFER**: Apply this pattern directly to Book recommendations.
- Use when: The pattern is about STORY/EXPERIENCE qualities that exist in both media.
- Examples: narrative_complexity, pacing_preference, philosophical themes, mood preferences.

**PARTIAL**: Apply with caveats — the pattern informs but doesn't dominate recommendations.
- Use when: The pattern is genre/topic-based and requires medium translation.
- Examples: movie sci-fi -> book sci-fi (different tropes), author-adjacent brand loyalty.

**BLOCK**: Do NOT transfer this pattern.
- Use when: The pattern is medium-specific or would cause negative transfer.
- Examples: brand_loyalty to actors/directors, quality_sensitivity to acting/cinematography,
  sensory_preference of MEDIUM-SPECIFIC sub-type (visual special effects, IMAX, action
  choreography, soundtrack).

## Output Requirements

For each pattern, produce: decision (TRANSFER/PARTIAL/BLOCK), rationale (2-3 sentences),
transferred_insight (string or null), confidence (0.0-1.0).

Then produce Top-10 book recommendations from the candidates listed in user message.

## STRICT Output Schema (JSON only)

{
  "transfer_decisions": {
    "<pattern_name>": {
      "decision": "TRANSFER|PARTIAL|BLOCK",
      "rationale": "<2-3 sentences>",
      "transferred_insight": "<string or null>",
      "confidence": <float>
    }
  },
  "recommendations": [
    {"rank": <1-10>, "item_id": "<parent_asin>", "title": "<book title>",
     "score": <float>, "applied_patterns": [...], "reasoning": "<text>"}
  ],
  "blocked_patterns_summary": "<brief note>",
  "overall_strategy": "<2-3 sentences>"
}

STRICT RULES:
- item_id MUST be from the 50 candidates listed.
- All 10 item_ids must be distinct.
- BLOCK patterns must not appear in any recommendation's applied_patterns.
- Output ONLY the JSON, no prose."""


def build_user_message(profile: dict, candidates: list) -> str:
    """Profile + 후보 50권으로 user message 구성 (Teacher와 동일)."""
    profile_text = json.dumps(profile, ensure_ascii=False, indent=2)
    cand_text = "\n\n".join(
        format_candidate(c, idx + 1) for idx, c in enumerate(candidates)
    )
    return (
        f"## User's 7-pattern Profile (extracted from Movies & TV reviews)\n\n"
        f"{profile_text}\n\n"
        f"## Book Candidates (n={len(candidates)})\n\n"
        f"{cand_text}\n\n"
        f"## Task\nFor each pattern in Profile, decide TRANSFER/PARTIAL/BLOCK. "
        f"Then produce Top-10 book recommendations from the candidates above. "
        f"Output JSON only."
    )


def load_fewshot_examples(train_jsonl: Path, n: int = 3) -> list:
    """SFT 학습 데이터에서 처음 n개 사용자의 messages 가져오기 (few-shot용)."""
    examples = []
    with open(train_jsonl) as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            sample = json.loads(line)
            messages = sample["messages"]
            # user message + assistant message 추출
            user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
            assistant_msg = next(
                (m["content"] for m in messages if m["role"] == "assistant"), ""
            )
            examples.append({"user": user_msg, "assistant": assistant_msg})
    return examples


def parse_decisions(content: str) -> dict | None:
    """모델 응답에서 transfer_decisions 추출."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return data


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--setting", required=True, choices=["zero_shot", "few_shot"],
        help="zero_shot or few_shot",
    )
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--limit", type=int, default=0, help="0 = all 100 users")
    p.add_argument("--n-fewshot", type=int, default=3)
    p.add_argument("--test-fixture", type=Path,
                   default=ROOT / "eval_fixtures/test_users.json")
    p.add_argument("--candidates-dir", type=Path,
                   default=ROOT / "eval_fixtures/candidates")
    p.add_argument("--profiles-dir", type=Path,
                   default=ROOT / "profiler_outputs")
    p.add_argument("--train-jsonl", type=Path,
                   default=ROOT / "data/teacher_train_main.jsonl")
    p.add_argument("--max-seq-length", type=int, default=12288)
    args = p.parse_args()

    print("=" * 70)
    print(f"RQ1 보강 — Base Qwen3-14B ({args.setting})")
    print("=" * 70)
    print()

    # Load model (4-bit quantization)
    print(f"Loading {MODEL_NAME} (4-bit)...")
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )
    model.eval()
    print(f"  Model loaded.")

    # Load fixture
    test_users = json.loads(args.test_fixture.read_text())
    if args.limit > 0:
        test_users = test_users[: args.limit]
    print(f"  test users: {len(test_users)}")

    # Few-shot examples (if needed)
    fewshot_examples = []
    if args.setting == "few_shot":
        fewshot_examples = load_fewshot_examples(args.train_jsonl, n=args.n_fewshot)
        print(f"  few-shot examples loaded: {len(fewshot_examples)}")

    # Inference loop
    results = []
    parse_success = 0
    t0 = time.time()

    for idx, uid in enumerate(test_users):
        profile_file = args.profiles_dir / f"user_{uid}.json"
        cand_file = args.candidates_dir / f"user_{uid}.json"
        if not profile_file.exists() or not cand_file.exists():
            print(f"  [{idx+1}/{len(test_users)}] {uid} — file missing, skip")
            continue
        profile = json.loads(profile_file.read_text())
        candidates = json.loads(cand_file.read_text())
        user_msg = build_user_message(profile, candidates)

        # Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT_NO_GT}]
        if args.setting == "few_shot":
            for ex in fewshot_examples:
                messages.append({"role": "user", "content": ex["user"]})
                messages.append({"role": "assistant", "content": ex["assistant"]})
        messages.append({"role": "user", "content": user_msg})

        # Apply chat template
        input_ids = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(model.device)

        if input_ids.shape[1] > args.max_seq_length:
            print(
                f"  [{idx+1}/{len(test_users)}] {uid} — context overflow "
                f"({input_ids.shape[1]} > {args.max_seq_length}), skip"
            )
            continue

        with torch.no_grad():
            output_ids = model.generate(
                input_ids,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                temperature=None,
                top_p=None,
                pad_token_id=tokenizer.eos_token_id,
            )

        response = tokenizer.decode(
            output_ids[0][input_ids.shape[1]:], skip_special_tokens=True
        )

        decisions = parse_decisions(response)
        if decisions is not None and "transfer_decisions" in decisions:
            parse_success += 1
            decision_pattern = {
                p: d.get("decision", "UNKNOWN")
                for p, d in decisions["transfer_decisions"].items()
            }
        else:
            decision_pattern = {}

        results.append(
            {
                "user_id": uid,
                "input_tokens": int(input_ids.shape[1]),
                "decisions_raw": decisions,
                "decision_pattern": decision_pattern,
                "response_preview": response[:500],
            }
        )

        if (idx + 1) % 10 == 0:
            elapsed = time.time() - t0
            print(
                f"  [{idx+1}/{len(test_users)}] elapsed {elapsed:.0f}s "
                f"parse_success={parse_success}"
            )

    elapsed = time.time() - t0
    print()
    print(f"Total elapsed: {elapsed:.0f}s")
    print(f"Parse success: {parse_success}/{len(results)} ({parse_success/len(results)*100:.1f}%)")

    # Save
    output = {
        "experiment": f"RQ1 보강 — Base Qwen3-14B {args.setting}",
        "model": MODEL_NAME,
        "setting": args.setting,
        "n_fewshot": args.n_fewshot if args.setting == "few_shot" else 0,
        "n_evaluated": len(results),
        "parse_success_count": parse_success,
        "elapsed_seconds": elapsed,
        "per_user": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n저장: {args.output}")


if __name__ == "__main__":
    main()
