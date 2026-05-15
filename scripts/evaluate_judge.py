"""Phase 4 — 학습된 Judge로 test set 추천 + 평가.

사용법:
    # (c) Ours (with Gate)
    python3 scripts/evaluate_judge.py \\
      --condition c_ours \\
      --adapter checkpoints/judge_v1/adapter \\
      --test-users data/test_users.parquet \\
      --output results/ablation_c_ours.json

    # smoke (소수 사용자만)
    python3 scripts/evaluate_judge.py \\
      --condition c_ours \\
      --adapter checkpoints/judge_v1/adapter \\
      --output results/smoke.json \\
      --limit 3

지표:
  - HR@1/5/10, NDCG@5/10, MRR
  - JSONValid, SchemaComplete, CandMembership, BLOCKLeakage, NoDuplicates
  - Pattern Decision counts (TRANSFER/PARTIAL/BLOCK 분포)
  - Teacher와 PDA·JSD는 teacher_outputs/ 존재 시에만 (옵션)

설계 메모:
  - 입력 포맷은 run_teacher.to_sft_record()와 동일 (GT hint 제거 학습 포맷).
  - 후보 50권 샘플링은 run_teacher.sample_candidates(seed=42)와 동일 로직.
  - GT는 run_teacher.pick_gt() — books_reviews에서 rating>=4 최근.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from collections import Counter

import pandas as pd
import numpy as np

# Phase 2 helpers 재사용 (포맷·샘플링 동일성 보장)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_teacher import (
    SYSTEM_PROMPT,
    REQUIRED_CORE_PATTERNS,
    N_RECOMMENDATIONS,
    format_candidate,
    sample_candidates,
    pick_gt,
    to_sft_record,
)


# ============================================================
# 1. 메트릭 계산 — 골격 (학습 결과 들어오면 검증)
# ============================================================

def compute_hr_at_k(rec_ids: list[str], gt_id: str, k: int) -> int:
    """Top-k 안에 GT 있으면 1, 없으면 0."""
    return 1 if gt_id in rec_ids[:k] else 0


def compute_ndcg_at_k(rec_ids: list[str], gt_id: str, k: int) -> float:
    """NDCG@k — GT가 i-th position에 있으면 1/log2(i+1+1)."""
    for i, rid in enumerate(rec_ids[:k]):
        if rid == gt_id:
            return 1.0 / np.log2(i + 2)
    return 0.0


def compute_mrr(rec_ids: list[str], gt_id: str) -> float:
    for i, rid in enumerate(rec_ids):
        if rid == gt_id:
            return 1.0 / (i + 1)
    return 0.0


def compute_per_user_metrics(rec_ids: list[str], gt_id: str) -> dict:
    return {
        "HR@1": compute_hr_at_k(rec_ids, gt_id, 1),
        "HR@5": compute_hr_at_k(rec_ids, gt_id, 5),
        "HR@10": compute_hr_at_k(rec_ids, gt_id, 10),
        "NDCG@5": compute_ndcg_at_k(rec_ids, gt_id, 5),
        "NDCG@10": compute_ndcg_at_k(rec_ids, gt_id, 10),
        "MRR": compute_mrr(rec_ids, gt_id),
    }


def aggregate_metrics(per_user_results: list[dict]) -> dict:
    keys = ["HR@1", "HR@5", "HR@10", "NDCG@5", "NDCG@10", "MRR"]
    return {k: float(np.mean([r[k] for r in per_user_results])) for k in keys}


# ============================================================
# 2. 출력 품질 검증 (Phase 2 validate_teacher_trial과 동일)
# ============================================================

def validate_output(output_json: dict, candidate_ids: set[str], gt_id: str) -> dict:
    """JSON 출력의 품질 검증."""
    result = {
        "is_valid_json": True,
        "schema_complete": True,
        "all_in_candidates": True,
        "no_duplicates": True,
        "no_block_leakage": True,
    }

    if not isinstance(output_json, dict):
        result["is_valid_json"] = False
        return result

    td = output_json.get("transfer_decisions", {})
    PATTERNS = ["genre_preference", "narrative_complexity", "pacing_preference",
                "quality_sensitivity", "brand_loyalty", "sensory_preference",
                "emotional_resonance"]
    if not all(p in td for p in PATTERNS):
        result["schema_complete"] = False

    block_patterns = {p for p, info in td.items() if info.get("decision") == "BLOCK"}

    recs = output_json.get("recommendations", [])
    if len(recs) != 10:
        result["schema_complete"] = False

    rec_ids = []
    for r in recs:
        if not isinstance(r, dict):
            continue
        rid = str(r.get("item_id", ""))
        rec_ids.append(rid)
        if rid not in candidate_ids:
            result["all_in_candidates"] = False
        applied = set(r.get("applied_patterns", []))
        if applied & block_patterns:
            result["no_block_leakage"] = False

    if len(rec_ids) != len(set(rec_ids)):
        result["no_duplicates"] = False

    return result


# ============================================================
# 3. Pattern Decision Accuracy + JSD
# ============================================================

def compute_pattern_decision_accuracy(judge_td: dict, teacher_td: dict) -> float:
    """7개 패턴 중 Judge·Teacher decision이 일치하는 비율."""
    PATTERNS = ["genre_preference", "narrative_complexity", "pacing_preference",
                "quality_sensitivity", "brand_loyalty", "sensory_preference",
                "emotional_resonance"]
    matches = 0
    total = 0
    for p in PATTERNS:
        if p in judge_td and p in teacher_td:
            if judge_td[p].get("decision") == teacher_td[p].get("decision"):
                matches += 1
            total += 1
    return matches / total if total > 0 else 0.0


def jensen_shannon_divergence(p: dict, q: dict) -> float:
    """3-class (TRANSFER/PARTIAL/BLOCK) JSD."""
    labels = ["TRANSFER", "PARTIAL", "BLOCK"]
    p_vec = np.array([p.get(l, 0) for l in labels], dtype=float)
    q_vec = np.array([q.get(l, 0) for l in labels], dtype=float)
    p_vec /= p_vec.sum() if p_vec.sum() > 0 else 1
    q_vec /= q_vec.sum() if q_vec.sum() > 0 else 1
    m = 0.5 * (p_vec + q_vec)

    def _kl(a, b):
        mask = a > 0
        return float(np.sum(a[mask] * np.log2(a[mask] / b[mask])))

    return 0.5 * _kl(p_vec, m) + 0.5 * _kl(q_vec, m)


# ============================================================
# 4. Judge 모델 inference
# ============================================================

def load_judge_model(adapter_path: Path, base_model: str = "Qwen/Qwen3-14B"):
    """학습 시와 동일한 4bit 양자화로 base를 로드하고 LoRA adapter를 부착.

    Tokenizer는 adapter dir에서 로드 — chat_template은 학습용 generation 마커가
    포함되어 있지만 추론 시 add_generation_prompt=True 만 쓰면 무방.
    flash_attention_2가 설치돼 있으면 자동 사용 (~1.3x 가속), 아니면 sdpa.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel

    try:
        import flash_attn  # noqa: F401
        attn_impl = "flash_attention_2"
    except ImportError:
        attn_impl = "sdpa"
    print(f"  attn_implementation: {attn_impl}")

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    print(f"  Base model 로드: {base_model} (4bit)")
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation=attn_impl,
    )
    print(f"  LoRA adapter 부착: {adapter_path}")
    model = PeftModel.from_pretrained(base, str(adapter_path))
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(str(adapter_path), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer


_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```\s*$", flags=re.MULTILINE)


def _extract_json(text: str) -> dict | None:
    t = text.strip()
    t = _JSON_FENCE_RE.sub("", t).strip()
    # 가장 바깥쪽 중괄호 추출
    s = t.find("{")
    e = t.rfind("}")
    if s < 0 or e <= s:
        return None
    candidate = t[s : e + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def build_eval_messages(profiler_output: dict, candidates: list[dict],
                        disable_gate: bool = False) -> list[dict]:
    """학습 포맷과 동일한 (system + user) message 생성.

    Args:
        disable_gate: True면 (d) w/o Gate condition — user message에서
            'transfer_decisions' 지시 제거. 학습된 모델이 prompt 변경에 어떻게
            반응하는지 측정. 논문에서는 inference-time gate ablation으로 기술.
    """
    profile_json = json.dumps(profiler_output, ensure_ascii=False, indent=2)
    cand_lines = [format_candidate(c, i + 1) for i, c in enumerate(candidates)]

    if disable_gate:
        # (d) w/o Gate: transfer_decisions 출력 지시 제거
        user_msg = (
            "=== USER PROFILE ===\n"
            f"{profile_json}\n\n"
            "=== CANDIDATES (50 Books) ===\n\n"
            + "\n\n".join(cand_lines)
            + "\n\n"
            "=== INSTRUCTION ===\n\n"
            "Recommend Top-10 books from the candidates above. "
            "Use all preference patterns equally without explicit transferability classification.\n"
            "Output valid JSON following the schema."
        )
    else:
        # (c) Ours: 본 학습 포맷 그대로
        user_msg = (
            "=== USER PROFILE ===\n"
            f"{profile_json}\n\n"
            "=== CANDIDATES (50 Books) ===\n\n"
            + "\n\n".join(cand_lines)
            + "\n\n"
            "=== INSTRUCTION ===\n\n"
            "Produce transfer_decisions for all patterns in the Profile and recommend Top-10 books.\n"
            "Output valid JSON following the schema exactly."
        )
    system_training = SYSTEM_PROMPT.replace(
        "## Ground Truth Calibration (for training data quality)\n\n"
        "You will be given a GROUND_TRUTH_HINT: the item the user actually purchased and rated highly in Books.\n"
        "This hint is provided ONLY to help you calibrate your reasoning quality — if your pattern decisions\n"
        "are correct, your Top-10 should naturally include this item.\n\n"
        "STRICT RULES:\n"
        "- DO NOT mention the ground truth in your rationale, reasoning, or any output text.\n"
        "- DO NOT artificially boost the ground truth's score; reason naturally based on Profile.\n"
        "- If your honest reasoning does not place the ground truth in Top-10, revisit your decisions\n"
        "  (maybe a BLOCK should be PARTIAL, or vice versa).\n"
        "- The goal is a Student model that will NEVER see ground truth at inference time.\n\n",
        "",
    )
    return [
        {"role": "system", "content": system_training},
        {"role": "user", "content": user_msg},
    ]


def predict_for_user(model, tokenizer, messages: list[dict],
                     max_new_tokens: int = 2500) -> dict:
    """Judge inference + JSON 파싱.

    Returns: {"output_json": dict|None, "raw_text": str, "gen_tokens": int}
    """
    import torch
    encoded = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True,
    )
    input_ids = encoded["input_ids"].to(model.device)
    attention_mask = encoded.get("attention_mask")
    if attention_mask is None:
        attention_mask = torch.ones_like(input_ids)
    else:
        attention_mask = attention_mask.to(model.device)

    prompt_len = input_ids.shape[1]
    with torch.no_grad():
        out = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            num_beams=1,
            pad_token_id=tokenizer.pad_token_id,
            use_cache=True,
        )
    gen_ids = out[0][prompt_len:]
    raw_text = tokenizer.decode(gen_ids, skip_special_tokens=True)
    output_json = _extract_json(raw_text)
    return {
        "output_json": output_json,
        "raw_text": raw_text,
        "gen_tokens": int(len(gen_ids)),
        "prompt_tokens": int(prompt_len),
    }


# ============================================================
# 5. 추천 추출 + 메인 평가 루프
# ============================================================

def extract_rec_ids(output_json: dict | None, k: int = 10) -> list[str]:
    if not isinstance(output_json, dict):
        return []
    recs = output_json.get("recommendations", []) or []
    ids = []
    for r in recs[:k]:
        if isinstance(r, dict):
            rid = str(r.get("item_id", "")).strip()
            if rid:
                ids.append(rid)
    return ids


def decision_distribution(output_json: dict | None) -> Counter:
    counts: Counter = Counter()
    if not isinstance(output_json, dict):
        return counts
    td = output_json.get("transfer_decisions", {}) or {}
    for p, info in td.items():
        if isinstance(info, dict):
            d = info.get("decision")
            if d in {"TRANSFER", "PARTIAL", "BLOCK"}:
                counts[d] += 1
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", type=str, default="c_ours",
                        choices=["c_ours", "d_no_gate"])
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen3-14B")
    parser.add_argument("--test-users", type=Path, default=Path("data/test_users.parquet"))
    parser.add_argument("--profiles", type=Path, default=Path("profiler_outputs"))
    parser.add_argument("--books-meta", type=Path, default=Path("data/books_meta_filtered.parquet"))
    parser.add_argument("--books-reviews", type=Path, default=Path("data/books_reviews_filtered.parquet"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n-candidates", type=int, default=50)
    parser.add_argument("--limit", type=int, default=None,
                        help="처음 N명만 평가 (smoke test용)")
    parser.add_argument("--max-new-tokens", type=int, default=2500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--disable-gate", action="store_true",
                        help="(d) w/o Gate — Gate filtering 무시 (현 단계 unused)")
    args = parser.parse_args()

    print(f"=== Phase 4 Evaluation: {args.condition} ===")

    print(f"\n[1/4] 데이터 로드")
    test_users = pd.read_parquet(args.test_users)
    books_meta = pd.read_parquet(args.books_meta)
    books_reviews = pd.read_parquet(args.books_reviews)
    print(f"  test_users: {len(test_users)}")
    print(f"  books_meta: {len(books_meta):,}")
    print(f"  books_reviews: {len(books_reviews):,}")

    print(f"\n[2/4] Judge 모델 로드")
    model, tokenizer = load_judge_model(args.adapter, args.base_model)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    per_user_records: list[dict] = []
    metric_rows: list[dict] = []
    validation_rows: list[dict] = []
    decision_total: Counter = Counter()

    n_eval = len(test_users) if args.limit is None else min(args.limit, len(test_users))
    print(f"\n[3/4] 추론 시작 — {n_eval}명")
    t0 = time.time()

    for idx, row in enumerate(test_users.itertuples(index=False)):
        if idx >= n_eval:
            break
        user_id = getattr(row, "user_id")

        profile_path = args.profiles / f"user_{user_id}.json"
        if not profile_path.exists():
            print(f"  [{idx+1}/{n_eval}] {user_id}: skip (no profile)")
            continue
        profiler_output = json.loads(profile_path.read_text())

        user_books = books_reviews[books_reviews["user_id"] == user_id]
        gt_info = pick_gt(user_books)
        if gt_info is None:
            print(f"  [{idx+1}/{n_eval}] {user_id}: skip (no rating>=4 in target)")
            continue
        gt_id = str(gt_info["parent_asin"])

        try:
            candidates = sample_candidates(
                user_id=user_id,
                gt_item_id=gt_id,
                books_meta_df=books_meta,
                user_books_reviews=user_books,
                n_candidates=args.n_candidates,
                rng=rng,
            )
        except ValueError as e:
            print(f"  [{idx+1}/{n_eval}] {user_id}: skip ({e})")
            continue

        candidate_ids = {str(c.get("parent_asin", "")).strip() for c in candidates}
        candidate_ids.discard("")

        # condition 또는 --disable-gate 시 (d) w/o Gate
        disable_gate = (args.condition == "d_no_gate") or args.disable_gate
        messages = build_eval_messages(profiler_output, candidates, disable_gate=disable_gate)
        t_user = time.time()
        result = predict_for_user(model, tokenizer, messages,
                                  max_new_tokens=args.max_new_tokens)
        elapsed = time.time() - t_user

        output_json = result["output_json"]
        rec_ids = extract_rec_ids(output_json, k=10)

        val = validate_output(output_json or {}, candidate_ids, gt_id)
        if output_json is None:
            val["is_valid_json"] = False
        validation_rows.append({"user_id": user_id, **val})

        metrics = compute_per_user_metrics(rec_ids, gt_id)
        metric_rows.append({"user_id": user_id, **metrics})

        dist = decision_distribution(output_json)
        decision_total.update(dist)

        per_user_records.append({
            "user_id": user_id,
            "gt_id": gt_id,
            "rec_ids": rec_ids,
            "metrics": metrics,
            "validation": val,
            "decision_counts": dict(dist),
            "gen_tokens": result["gen_tokens"],
            "prompt_tokens": result["prompt_tokens"],
            "elapsed_s": round(elapsed, 1),
            "output_json": output_json,
            "raw_text_if_parse_failed": result["raw_text"] if output_json is None else None,
        })

        print(
            f"  [{idx+1}/{n_eval}] {user_id} "
            f"gt={'✓' if gt_id in rec_ids else '✗'} "
            f"HR@10={metrics['HR@10']} NDCG@10={metrics['NDCG@10']:.3f} "
            f"valid={val['is_valid_json'] and val['schema_complete']} "
            f"tokens={result['gen_tokens']} t={elapsed:.1f}s"
        )

    print(f"\n[4/4] 집계 + 저장 — 총 {len(metric_rows)}명 평가됨, {time.time()-t0:.0f}s 소요")

    aggregated = aggregate_metrics(metric_rows) if metric_rows else {}
    validation_summary = {}
    if validation_rows:
        keys = ["is_valid_json", "schema_complete", "all_in_candidates",
                "no_duplicates", "no_block_leakage"]
        validation_summary = {k: float(np.mean([r[k] for r in validation_rows])) for k in keys}

    summary = {
        "condition": args.condition,
        "adapter": str(args.adapter),
        "base_model": args.base_model,
        "n_evaluated": len(metric_rows),
        "metrics": aggregated,
        "validation_pass_rate": validation_summary,
        "decision_distribution_total": dict(decision_total),
        "params": {
            "n_candidates": args.n_candidates,
            "max_new_tokens": args.max_new_tokens,
            "seed": args.seed,
            "limit": args.limit,
        },
    }

    out = {
        "summary": summary,
        "per_user": per_user_records,
    }
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n📁 결과 저장: {args.output}")
    print(f"\n=== Summary ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
