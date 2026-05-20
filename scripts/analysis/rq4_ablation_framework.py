"""RQ4 추가 보강 — Framework 모듈 ablation (변형 A·B).

본 framework의 Profiler / Judge / Ranker 모듈을 단계적으로 제거하는 ablation:

  변형 A (Raw LLM)      : 영화 리뷰 raw text + 후보 50권 → LLM → Top-10
  변형 B (Profile만)    : Profile JSON + 후보 50권 → LLM → Top-10 (Judge·Ranker 없이)
  변형 C (본 연구)      : 기존 results/ablation_c_ours.json 활용

모델: GPT-4o-mini, GPT-4o
n=100, 본 연구 test fixture, 같은 후보 50권

사용법:
    export OPENAI_API_KEY=sk-...
    .venv_thesis/bin/pip install openai python-dotenv tiktoken

    # 변형 A × GPT-4o-mini
    .venv_thesis/bin/python scripts/analysis/rq4_ablation_framework.py \\
        --variant A --model gpt-4o-mini \\
        --output results/analysis/rq4_ablation_framework_A_gpt4omini.json

    # 변형 A × GPT-4o
    .venv_thesis/bin/python scripts/analysis/rq4_ablation_framework.py \\
        --variant A --model gpt-4o \\
        --output results/analysis/rq4_ablation_framework_A_gpt4o.json

    # 변형 B × GPT-4o-mini
    .venv_thesis/bin/python scripts/analysis/rq4_ablation_framework.py \\
        --variant B --model gpt-4o-mini \\
        --output results/analysis/rq4_ablation_framework_B_gpt4omini.json

    # 변형 B × GPT-4o
    .venv_thesis/bin/python scripts/analysis/rq4_ablation_framework.py \\
        --variant B --model gpt-4o \\
        --output results/analysis/rq4_ablation_framework_B_gpt4o.json

    # smoke test (n=3)
    .venv_thesis/bin/python scripts/analysis/rq4_ablation_framework.py \\
        --variant A --model gpt-4o-mini --limit 3
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from run_teacher import (
    format_candidate,
    sample_candidates,
    pick_gt,
    N_RECOMMENDATIONS,
)
from evaluate_judge import compute_per_user_metrics, aggregate_metrics

TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 2500
SEED = 42

MODEL_PRICING = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-2024-08-06": (2.50, 10.00),
}


# ============================================================
# Prompts
# ============================================================

SYSTEM_A_RAW_LLM = """You are a book recommender. A user has reviewed these movies. \
Recommend a Top-10 list of books from the candidates below that this user is likely to enjoy.

Output a single JSON object with this exact schema:
{
  "recommendations": [
    {"rank": 1, "item_id": "<exact parent_asin value as shown after 'item_id:' in candidate listing>",
     "title": "<book title>",
     "score": <0.0-1.0>, "reasoning": "<1-2 sentences>"},
    ...10 items total
  ]
}

STRICT RULES:
- item_id MUST be the actual parent_asin string (e.g., 'B07ABC123' or '0062407317'),
  NOT the candidate index like 'C1' or '32'.
- Each candidate is listed as: [C{idx}] item_id: <parent_asin> — use the <parent_asin> value.
- item_id MUST be one of the 50 candidates listed.
- All 10 item_ids must be distinct.
- Output ONLY the JSON, no prose."""


SYSTEM_B_PROFILE_ONLY = """You are a book recommender. A user's movie preference profile is \
provided in JSON format with 7 patterns (genre, narrative_complexity, pacing, quality_sensitivity, \
brand_loyalty, sensory_preference, emotional_resonance). Use this profile to recommend a Top-10 \
list of books from the candidates below.

Output a single JSON object with this exact schema:
{
  "recommendations": [
    {"rank": 1, "item_id": "<exact parent_asin value as shown after 'item_id:' in candidate listing>",
     "title": "<book title>",
     "score": <0.0-1.0>, "reasoning": "<1-2 sentences>"},
    ...10 items total
  ]
}

STRICT RULES:
- item_id MUST be the actual parent_asin string (e.g., 'B07ABC123' or '0062407317'),
  NOT the candidate index like 'C1' or '32'.
- Each candidate is listed as: [C{idx}] item_id: <parent_asin> — use the <parent_asin> value.
- item_id MUST be one of the 50 candidates listed.
- All 10 item_ids must be distinct.
- Do NOT make TRANSFER/PARTIAL/BLOCK decisions, only output the Top-10 directly from the Profile.
- Output ONLY the JSON, no prose."""


SYSTEM_D_PROFILE_JUDGE = """You are a book recommender. A user's movie preference profile is \
provided in JSON format with 7 patterns, along with TRANSFER/PARTIAL/BLOCK transfer decisions \
for each pattern made by an expert Cross-Domain Transfer Judge. Use BOTH the profile and the \
transfer decisions to recommend a Top-10 list of books from the candidates below.

How to use the transfer decisions:
- TRANSFER patterns: apply this preference directly to book recommendations.
- PARTIAL patterns: apply with medium translation (the pattern transfers partially with caveats).
- BLOCK patterns: do NOT use this pattern as a basis for any recommendation (it is medium-specific).

Output a single JSON object with this exact schema:
{
  "recommendations": [
    {"rank": 1, "item_id": "<exact parent_asin value as shown after 'item_id:' in candidate listing>",
     "title": "<book title>",
     "score": <0.0-1.0>, "reasoning": "<1-2 sentences explaining how TRANSFER/PARTIAL patterns drove this rec>"},
    ...10 items total
  ]
}

STRICT RULES:
- item_id MUST be the actual parent_asin string (e.g., 'B07ABC123' or '0062407317'),
  NOT the candidate index like 'C1' or '32'.
- Each candidate is listed as: [C{idx}] item_id: <parent_asin> — use the <parent_asin> value.
- item_id MUST be one of the 50 candidates listed.
- All 10 item_ids must be distinct.
- Recommendations must NOT be based on BLOCK-decision patterns.
- Output ONLY the JSON, no prose."""


SYSTEM_PROMPTS = {
    "A": SYSTEM_A_RAW_LLM,
    "B": SYSTEM_B_PROFILE_ONLY,
    "D": SYSTEM_D_PROFILE_JUDGE,
}


# ============================================================
# User Message Builders
# ============================================================

def build_user_message_raw_reviews(reviews_df: pd.DataFrame, candidates: list[dict]) -> str:
    """변형 A: raw 영화 리뷰 + 후보 50권."""
    rev_text = "\n".join(
        f"- {row.title}: {row.text[:300]}"
        for _, row in reviews_df.iterrows()
    )
    cand_text = "\n".join(format_candidate(c, idx + 1) for idx, c in enumerate(candidates))
    return (
        f"## User's Movie Reviews (n={len(reviews_df)})\n{rev_text}\n\n"
        f"## Book Candidates (n={len(candidates)})\n{cand_text}\n\n"
        f"## Task\nRecommend Top-10 books from the candidates above."
    )


def build_user_message_profile(profile_json: dict, candidates: list[dict]) -> str:
    """변형 B: Profile JSON + 후보 50권 (Judge·decisions 없이)."""
    profile_text = json.dumps(profile_json, ensure_ascii=False, indent=2)
    cand_text = "\n".join(format_candidate(c, idx + 1) for idx, c in enumerate(candidates))
    return (
        f"## User's 7-pattern Movie Preference Profile\n{profile_text}\n\n"
        f"## Book Candidates (n={len(candidates)})\n{cand_text}\n\n"
        f"## Task\nRecommend Top-10 books from the candidates above. "
        f"Use the Profile to infer the user's taste."
    )


def build_user_message_profile_judge(
    profile_json: dict, transfer_decisions: dict, candidates: list[dict]
) -> str:
    """변형 D: Profile + Judge transfer_decisions + 후보 50권."""
    profile_text = json.dumps(profile_json, ensure_ascii=False, indent=2)
    # Format decisions compactly
    decisions_summary = {}
    for pat, d in transfer_decisions.items():
        decisions_summary[pat] = {
            "decision": d.get("decision", "UNKNOWN"),
            "rationale": d.get("rationale", ""),
            "transferred_insight": d.get("transferred_insight"),
        }
    decisions_text = json.dumps(decisions_summary, ensure_ascii=False, indent=2)
    cand_text = "\n".join(format_candidate(c, idx + 1) for idx, c in enumerate(candidates))
    return (
        f"## User's 7-pattern Movie Preference Profile\n{profile_text}\n\n"
        f"## Transfer Judge Decisions (TRANSFER / PARTIAL / BLOCK per pattern)\n"
        f"{decisions_text}\n\n"
        f"## Book Candidates (n={len(candidates)})\n{cand_text}\n\n"
        f"## Task\nUsing BOTH the Profile and the Transfer Decisions, recommend Top-10 books "
        f"from the candidates above. Apply TRANSFER patterns directly, apply PARTIAL patterns "
        f"with medium translation, and do NOT use BLOCK patterns."
    )


def load_transfer_decisions(uid: str) -> dict | None:
    """본 연구 Judge가 출력한 transfer_decisions 로드 (ablation_c_ours.json output_json)."""
    cache_file = ROOT / "results/ablation_c_ours.json"
    if not hasattr(load_transfer_decisions, "_cache"):
        data = json.loads(cache_file.read_text())
        cache = {}
        for r in data["per_user"]:
            oj = r.get("output_json", {})
            if isinstance(oj, dict) and "transfer_decisions" in oj:
                cache[r["user_id"]] = oj["transfer_decisions"]
        load_transfer_decisions._cache = cache
    return load_transfer_decisions._cache.get(uid)


# ============================================================
# Output Parser
# ============================================================

def parse_top10_from_response(
    content: str, candidates: list[dict]
) -> list[str]:
    """LLM 응답에서 Top-10 parent_asin 추출 + 검증.

    Fallback: 만약 LLM이 candidate index (예: "32", "C32")를 출력하면
    candidates[idx-1].parent_asin으로 매핑.
    """
    candidate_ids = {c["parent_asin"] for c in candidates}

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if not m:
            return []
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return []

    recs = data.get("recommendations", [])
    top10 = []
    for r in recs:
        if not isinstance(r, dict):
            continue
        item_id = str(r.get("item_id", "")).strip()

        # Direct parent_asin match
        if item_id in candidate_ids and item_id not in top10:
            top10.append(item_id)
        else:
            # Fallback 1: "C{n}" or "{n}" → candidate index (1-based)
            idx_match = re.match(r"^C?(\d+)$", item_id)
            if idx_match:
                idx = int(idx_match.group(1)) - 1
                if 0 <= idx < len(candidates):
                    asin = candidates[idx]["parent_asin"]
                    if asin not in top10:
                        top10.append(asin)
        if len(top10) == N_RECOMMENDATIONS:
            break
    return top10


# ============================================================
# OpenAI Call
# ============================================================

def call_openai(client, model: str, system: str, user_msg: str, max_retries: int = 3):
    """OpenAI API 호출 + 재시도. 토큰 사용량 반환."""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user_msg}],
                temperature=TEMPERATURE,
                max_tokens=MAX_OUTPUT_TOKENS,
                response_format={"type": "json_object"},
                seed=SEED,
            )
            content = response.choices[0].message.content
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
            return content, usage
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  [retry {attempt+1}] {e} - waiting {wait}s")
                time.sleep(wait)
            else:
                raise


# ============================================================
# Main
# ============================================================

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--variant", required=True, choices=["A", "B", "D"])
    p.add_argument("--model", required=True,
                   choices=["gpt-4o-mini", "gpt-4o", "gpt-4o-2024-08-06"])
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--limit", type=int, default=0,
                   help="0 = all test users")
    p.add_argument("--test-fixture", type=Path,
                   default=ROOT / "eval_fixtures/test_users.json")
    p.add_argument("--gt-fixture", type=Path,
                   default=ROOT / "eval_fixtures/gt.json")
    p.add_argument("--candidates-dir", type=Path,
                   default=ROOT / "eval_fixtures/candidates")
    p.add_argument("--profiles-dir", type=Path,
                   default=ROOT / "profiler_outputs")
    p.add_argument("--movies-reviews", type=Path,
                   default=ROOT / "data/movies_reviews_filtered.parquet")
    args = p.parse_args()

    print("=" * 70)
    print(f"RQ4 추가 보강 — Framework Ablation")
    print(f"  변형: {args.variant}")
    print(f"  모델: {args.model}")
    print("=" * 70)

    # Load OpenAI
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)
    client = OpenAI(api_key=api_key)

    # Load fixture
    test_users = json.loads(args.test_fixture.read_text())
    gt_map = json.loads(args.gt_fixture.read_text())
    if args.limit > 0:
        test_users = test_users[: args.limit]
    print(f"  users: {len(test_users)}")

    # Load movies reviews (변형 A에 필요)
    movies = pd.read_parquet(
        args.movies_reviews,
        columns=["user_id", "timestamp", "title", "text", "rating"],
    )
    print(f"  movies reviews: {len(movies):,}\n")

    # Run inference
    system_prompt = SYSTEM_PROMPTS[args.variant]
    pricing = MODEL_PRICING[args.model]

    per_user_results = []
    total_input_tokens = 0
    total_output_tokens = 0
    t0 = time.time()

    for idx, uid in enumerate(test_users):
        # Load candidates
        cand_file = args.candidates_dir / f"user_{uid}.json"
        candidates = json.loads(cand_file.read_text())
        candidate_ids = {c["parent_asin"] for c in candidates}
        gt_id = gt_map[uid]["gt_id"] if isinstance(gt_map, dict) else \
                next(g["gt_id"] for g in gt_map if g["user_id"] == uid)

        # Build prompt based on variant
        if args.variant == "A":
            user_reviews = movies[movies["user_id"] == uid].sort_values("timestamp", ascending=False).head(30)
            user_msg = build_user_message_raw_reviews(user_reviews, candidates)
        elif args.variant == "B":
            profile_file = args.profiles_dir / f"user_{uid}.json"
            if not profile_file.exists():
                print(f"  [{idx+1}/{len(test_users)}] {uid} — profile 없음, skip")
                continue
            profile = json.loads(profile_file.read_text())
            user_msg = build_user_message_profile(profile, candidates)
        else:  # D — Profile + Judge decisions
            profile_file = args.profiles_dir / f"user_{uid}.json"
            if not profile_file.exists():
                print(f"  [{idx+1}/{len(test_users)}] {uid} — profile 없음, skip")
                continue
            profile = json.loads(profile_file.read_text())
            decisions = load_transfer_decisions(uid)
            if not decisions:
                print(f"  [{idx+1}/{len(test_users)}] {uid} — transfer_decisions 없음, skip")
                continue
            user_msg = build_user_message_profile_judge(profile, decisions, candidates)

        # Call OpenAI
        try:
            content, usage = call_openai(client, args.model, system_prompt, user_msg)
        except Exception as e:
            print(f"  [{idx+1}/{len(test_users)}] {uid} — API 실패: {e}")
            continue

        total_input_tokens += usage["input_tokens"]
        total_output_tokens += usage["output_tokens"]

        # Parse Top-10
        top10 = parse_top10_from_response(content, candidates)
        if len(top10) < N_RECOMMENDATIONS:
            print(f"  [{idx+1}/{len(test_users)}] {uid} — Top-10 부족 ({len(top10)}), pad with first remaining candidates")
            for c in candidates:
                if c["parent_asin"] not in top10:
                    top10.append(c["parent_asin"])
                if len(top10) == N_RECOMMENDATIONS:
                    break

        # Metrics
        metrics = compute_per_user_metrics(top10, gt_id)
        per_user_results.append({
            "user_id": uid,
            "gt_id": gt_id,
            "rec_ids": top10,
            "metrics": metrics,
        })

        if (idx + 1) % 10 == 0:
            elapsed = time.time() - t0
            print(f"  [{idx+1}/{len(test_users)}] elapsed {elapsed:.0f}s")

    elapsed = time.time() - t0
    summary = aggregate_metrics([r["metrics"] for r in per_user_results])

    # Cost
    cost_input = total_input_tokens / 1_000_000 * pricing[0]
    cost_output = total_output_tokens / 1_000_000 * pricing[1]
    total_cost = cost_input + cost_output

    print()
    print("=" * 70)
    print(f"결과")
    print("=" * 70)
    print(f"  변형: {args.variant} ({args.model})")
    print(f"  n: {len(per_user_results)}")
    print(f"  HR@10: {summary['HR@10']:.3f}")
    print(f"  NDCG@10: {summary['NDCG@10']:.4f}")
    print(f"  MRR: {summary['MRR']:.4f}")
    print(f"  토큰: input {total_input_tokens:,}  output {total_output_tokens:,}")
    print(f"  비용: ${total_cost:.4f}")
    print(f"  시간: {elapsed:.0f}s")

    # Save
    output = {
        "experiment": f"RQ4 framework ablation — variant {args.variant} × {args.model}",
        "variant": args.variant,
        "model": args.model,
        "n_evaluated": len(per_user_results),
        "summary": summary,
        "cost": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "cost_usd": total_cost,
        },
        "elapsed_seconds": elapsed,
        "per_user": per_user_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n저장: {args.output}")


if __name__ == "__main__":
    main()
