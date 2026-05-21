"""RQ4 Framework ablation × Qwen3-14B (base, 학습 전).

현재 RQ4 framework ablation은 변형 A·B·D를 GPT-4o-mini·GPT-4o로만 실행했음
(scripts/analysis/rq4_ablation_framework.py). 본 framework C는 Qwen3-14B QLoRA
+ Ranker 구조 → A·B·D vs C 비교에서 *모델 차이*(Qwen 14B vs GPT)와
*framework 효과*(모듈화·Ranker)가 혼재.

본 스크립트는 *동일 모델*(Qwen3-14B base, fine-tuning 전)로 A·B·D를
추가 측정하여 *공정 비교*를 구성한다.

  변형 A (Raw LLM)        : 영화 리뷰 raw + 후보 50권 → Qwen base → Top-10
  변형 B (Profile만)      : Profile JSON + 후보 50권 → Qwen base → Top-10
  변형 D (Profile+Judge)  : Profile + Judge decisions + 후보 50권 → Qwen base → Top-10

비교 대상:
  변형 C (본 연구)        : results/ablation_c_ours.json (Qwen3-14B QLoRA + Ranker)

사용법 (RunPod):
    cd /workspace/TransferJudge

    # 변형 A — 100명
    .venv_thesis/bin/python scripts/analysis/rq4_ablation_qwen_base.py \\
        --variant A \\
        --output results/analysis/rq4_ablation_A_qwen_base.json

    # 변형 B — 100명
    .venv_thesis/bin/python scripts/analysis/rq4_ablation_qwen_base.py \\
        --variant B \\
        --output results/analysis/rq4_ablation_B_qwen_base.json

    # 변형 D — 100명
    .venv_thesis/bin/python scripts/analysis/rq4_ablation_qwen_base.py \\
        --variant D \\
        --output results/analysis/rq4_ablation_D_qwen_base.json

    # smoke test (n=3, 모델 로딩·prompts·parsing 검증)
    .venv_thesis/bin/python scripts/analysis/rq4_ablation_qwen_base.py \\
        --variant A --limit 3 \\
        --output results/analysis/smoke_A_qwen.json

요구사항:
  - GPU: A100 40GB+ (Qwen 14B × 4-bit ≈ 8GB)
  - HF_TOKEN env (Qwen 다운로드)
  - eval_fixtures/, profiler_outputs/, results/ablation_c_ours.json
  - data/movies_reviews_filtered.parquet (변형 A 전용)

비용 추정 (RunPod A100-SXM4-80GB ~$2/h):
  - 변형 A: 100명, raw text 입력 (큼) → ~3.5h, ~$7
  - 변형 B: 100명, profile 압축 → ~3h, ~$6
  - 변형 D: 100명, profile + decisions → ~3.5h, ~$7
  - 합: ~10h, ~$20
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from run_teacher import N_RECOMMENDATIONS
from evaluate_judge import compute_per_user_metrics, aggregate_metrics

# RQ4 framework ablation의 prompts·user-message builders·parser 재사용
from analysis.rq4_ablation_framework import (
    SYSTEM_PROMPTS,
    build_user_message_raw_reviews,
    build_user_message_profile,
    build_user_message_profile_judge,
    load_transfer_decisions,
    parse_top10_from_response,
)

MODEL_NAME = "Qwen/Qwen3-14B"
MAX_NEW_TOKENS = 2500


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--variant", required=True, choices=["A", "B", "D"])
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--limit", type=int, default=0, help="0 = all test users")
    p.add_argument(
        "--test-fixture",
        type=Path,
        default=ROOT / "eval_fixtures/test_users.json",
    )
    p.add_argument(
        "--gt-fixture",
        type=Path,
        default=ROOT / "eval_fixtures/gt.json",
    )
    p.add_argument(
        "--candidates-dir",
        type=Path,
        default=ROOT / "eval_fixtures/candidates",
    )
    p.add_argument(
        "--profiles-dir",
        type=Path,
        default=ROOT / "profiler_outputs",
    )
    p.add_argument(
        "--movies-reviews",
        type=Path,
        default=ROOT / "data/movies_reviews_filtered.parquet",
    )
    p.add_argument("--max-seq-length", type=int, default=12288)
    args = p.parse_args()

    print("=" * 70)
    print(f"RQ4 framework ablation × Qwen3-14B (base, 학습 전)")
    print(f"  변형: {args.variant}")
    print(f"  출력: {args.output}")
    print("=" * 70)

    # ------------------------------------------------------------
    # Load model (4-bit quantization, deterministic generation)
    # ------------------------------------------------------------
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
    print("  Model loaded.\n")

    # ------------------------------------------------------------
    # Load fixture + GT + (optional) raw movie reviews
    # ------------------------------------------------------------
    test_users = json.loads(args.test_fixture.read_text())
    gt_map = json.loads(args.gt_fixture.read_text())
    if args.limit > 0:
        test_users = test_users[: args.limit]
    print(f"  users: {len(test_users)}")

    movies = None
    if args.variant == "A":
        movies = pd.read_parquet(
            args.movies_reviews,
            columns=["user_id", "timestamp", "title", "text", "rating"],
        )
        print(f"  movies reviews: {len(movies):,}")
    print()

    # ------------------------------------------------------------
    # Inference loop
    # ------------------------------------------------------------
    system_prompt = SYSTEM_PROMPTS[args.variant]
    per_user_results = []
    skipped = []
    t0 = time.time()

    for idx, uid in enumerate(test_users):
        cand_file = args.candidates_dir / f"user_{uid}.json"
        if not cand_file.exists():
            skipped.append({"user_id": uid, "reason": "candidates missing"})
            continue
        candidates = json.loads(cand_file.read_text())
        gt_id = (
            gt_map[uid]["gt_id"]
            if isinstance(gt_map, dict)
            else next(g["gt_id"] for g in gt_map if g["user_id"] == uid)
        )

        # Build user message per variant
        if args.variant == "A":
            user_reviews = (
                movies[movies["user_id"] == uid]
                .sort_values("timestamp", ascending=False)
                .head(30)
            )
            user_msg = build_user_message_raw_reviews(user_reviews, candidates)
        elif args.variant == "B":
            profile_file = args.profiles_dir / f"user_{uid}.json"
            if not profile_file.exists():
                skipped.append({"user_id": uid, "reason": "profile missing"})
                continue
            profile = json.loads(profile_file.read_text())
            user_msg = build_user_message_profile(profile, candidates)
        else:  # D
            profile_file = args.profiles_dir / f"user_{uid}.json"
            if not profile_file.exists():
                skipped.append({"user_id": uid, "reason": "profile missing"})
                continue
            profile = json.loads(profile_file.read_text())
            decisions = load_transfer_decisions(uid)
            if not decisions:
                skipped.append({"user_id": uid, "reason": "transfer_decisions missing"})
                continue
            user_msg = build_user_message_profile_judge(
                profile, decisions, candidates
            )

        # Chat template + tokenize
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]
        encoded = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            enable_thinking=False,
        )
        if hasattr(encoded, "input_ids") or (
            hasattr(encoded, "keys") and "input_ids" in encoded
        ):
            input_ids = encoded["input_ids"].to(model.device)
        else:
            input_ids = encoded.to(model.device)

        if input_ids.shape[1] > args.max_seq_length:
            print(
                f"  [{idx+1}/{len(test_users)}] {uid} — context overflow "
                f"({input_ids.shape[1]} > {args.max_seq_length}), skip"
            )
            skipped.append(
                {"user_id": uid, "reason": f"overflow {int(input_ids.shape[1])}"}
            )
            continue

        # Deterministic generation
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

        top10 = parse_top10_from_response(response, candidates)
        if len(top10) < N_RECOMMENDATIONS:
            print(
                f"  [{idx+1}/{len(test_users)}] {uid} — Top-10 부족 "
                f"({len(top10)}), pad with remaining candidates"
            )
            for c in candidates:
                if c["parent_asin"] not in top10:
                    top10.append(c["parent_asin"])
                if len(top10) == N_RECOMMENDATIONS:
                    break

        metrics = compute_per_user_metrics(top10, gt_id)
        per_user_results.append(
            {
                "user_id": uid,
                "gt_id": gt_id,
                "rec_ids": top10,
                "metrics": metrics,
                "input_tokens": int(input_ids.shape[1]),
                "response_preview": response[:300],
            }
        )

        if (idx + 1) % 5 == 0:
            elapsed = time.time() - t0
            n_done = len(per_user_results)
            rate = elapsed / max(n_done, 1)
            eta = rate * (len(test_users) - (idx + 1))
            print(
                f"  [{idx+1}/{len(test_users)}] elapsed {elapsed:.0f}s "
                f"({rate:.0f}s/user, ETA {eta:.0f}s)"
            )

    elapsed = time.time() - t0
    summary = aggregate_metrics([r["metrics"] for r in per_user_results])

    print()
    print("=" * 70)
    print(f"결과 — 변형 {args.variant} × Qwen3-14B base")
    print("=" * 70)
    print(f"  n_evaluated: {len(per_user_results)}")
    print(f"  n_skipped:   {len(skipped)}")
    print(f"  HR@10:       {summary['HR@10']:.3f}")
    print(f"  NDCG@10:     {summary['NDCG@10']:.4f}")
    print(f"  MRR:         {summary['MRR']:.4f}")
    print(f"  시간:         {elapsed:.0f}s ({elapsed/60:.1f}m)")

    output = {
        "experiment": (
            f"RQ4 framework ablation — variant {args.variant} "
            f"× Qwen3-14B (base, pre-FT)"
        ),
        "variant": args.variant,
        "model": MODEL_NAME,
        "quantization": "4-bit nf4",
        "temperature": 0.0,
        "n_evaluated": len(per_user_results),
        "n_skipped": len(skipped),
        "skipped": skipped,
        "summary": summary,
        "elapsed_seconds": elapsed,
        "per_user": per_user_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, ensure_ascii=False)
    )
    print(f"\n저장: {args.output}")


if __name__ == "__main__":
    main()
