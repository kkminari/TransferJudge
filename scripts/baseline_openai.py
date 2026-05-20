"""Phase 4 — OpenAI API 기반 baseline (a)(b)(g) 통합 실행.

세 조건 모두 GPT-4o-mini API로 추론하며 입력 구성만 다름:
  (a) Single LLM   : raw 영화 리뷰 + 후보 50권 → Top-10 (Profile 없음, CDR 명시 없음)
  (b) Prompt-only  : Profile JSON + 후보 50권 → transfer_decisions + Top-10 (학습 없음)
  (g) LLM4CDR-style: raw 영화 리뷰 + 후보 50권 → cross-domain transfer prompt → Top-10

사용법:
    export OPENAI_API_KEY=sk-...
    python3 scripts/baseline_openai.py --condition a_single --limit 3
    python3 scripts/baseline_openai.py --condition b_prompt --output results/ablation_b_prompt.json
    python3 scripts/baseline_openai.py --condition g_llm4cdr --limit 3

100명 전체 실행 (기본):
    python3 scripts/baseline_openai.py --condition a_single
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd

# .env 자동 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# Phase 2/4 헬퍼 재사용 (입력 포맷·sampling·메트릭 일관성)
from run_teacher import (
    REQUIRED_CORE_PATTERNS,
    N_RECOMMENDATIONS,
    format_candidate,
    sample_candidates,
    pick_gt,
)
from evaluate_judge import (
    compute_per_user_metrics,
    aggregate_metrics,
    validate_output,
)


MODEL = "gpt-4o-mini"
TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 2500
SEED = 42
PRICE_INPUT_PER_1M = 0.15
PRICE_OUTPUT_PER_1M = 0.60

# Model pricing per 1M tokens (input, output)
MODEL_PRICING = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-2024-08-06": (2.50, 10.00),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
}


# ============================================================
# Prompt 구성 — Condition별
# ============================================================

SYSTEM_A_SINGLE = """You are a book recommender. A user has reviewed these movies. \
Recommend a Top-10 list of books from the candidates below.

Output a single JSON object with this exact schema:
{
  "recommendations": [
    {"rank": 1, "item_id": "<parent_asin from candidates>", "title": "<book title>",
     "score": <0.0-1.0>, "reasoning": "<1-2 sentences>"},
    ...10 items total
  ]
}

STRICT RULES:
- item_id MUST be from the 50 candidates listed.
- All 10 item_ids must be distinct.
- Output ONLY the JSON, no prose."""


SYSTEM_B_PROMPT = """You are an expert Cross-Domain Transfer Judge. Given a user's preference \
profile extracted from Movies & TV reviews, decide for each pattern whether it should TRANSFER, \
PARTIAL-transfer, or BLOCK to the Books domain, then recommend Top-10 books from the candidates.

For each pattern in the Profile:
- TRANSFER: directly apply (medium-agnostic)
- PARTIAL: apply with caveats (e.g., genre mapping)
- BLOCK: medium-specific, do not transfer

Output JSON:
{
  "transfer_decisions": {
    "<pattern_name>": {
      "decision": "TRANSFER|PARTIAL|BLOCK",
      "rationale": "<1-2 sentences>",
      "transferred_insight": "<string or null>",
      "confidence": <0.0-1.0>
    }
  },
  "recommendations": [
    {"rank": 1, "item_id": "<parent_asin>", "title": "<book title>",
     "score": <0.0-1.0>, "applied_patterns": ["<pattern>", ...],
     "reasoning": "<1-2 sentences>"},
    ...10 items
  ]
}

STRICT:
- item_id MUST be from the 50 candidates.
- All 10 distinct.
- BLOCK patterns must NOT appear in any applied_patterns.
- Output JSON only."""


SYSTEM_G_LLM4CDR = """You are a cross-domain recommender. The user has source-domain (Movies & TV) \
activity below. Your task: transfer this preference to the target domain (Books) and recommend \
Top-10 books from the candidates.

This is a single-LLM cross-domain recommendation setup with no explicit preference structure \
extraction or transfer gating.

Output JSON:
{
  "recommendations": [
    {"rank": 1, "item_id": "<parent_asin>", "title": "<title>",
     "score": <0.0-1.0>, "reasoning": "<1-2 sentences>"},
    ...10 items
  ]
}

STRICT:
- item_id MUST be from the 50 candidates.
- All 10 distinct.
- Output JSON only."""


SYSTEMS = {
    "a_single": SYSTEM_A_SINGLE,
    "b_prompt": SYSTEM_B_PROMPT,
    "g_llm4cdr": SYSTEM_G_LLM4CDR,
}


def build_user_message_raw_reviews(reviews_df: pd.DataFrame, candidates: list[dict],
                                    cross_domain_hint: bool = False) -> str:
    """raw 영화 리뷰 기반 user message — (a) 및 (g) 공통."""
    lines = ["=== USER'S MOVIES & TV REVIEWS ==="]
    for _, row in reviews_df.iterrows():
        title = str(row.get("title", "")).strip()[:80]
        text = str(row.get("text", "")).strip()
        if len(text) > 500:
            text = text[:500] + "..."
        rating = row.get("rating", "")
        lines.append(f"[★{rating}] {title}: \"{text}\"")
    lines.append("")
    lines.append("=== CANDIDATES (50 Books) ===")
    cand_lines = [format_candidate(c, i + 1) for i, c in enumerate(candidates)]
    lines.append("\n\n".join(cand_lines))
    lines.append("")
    # ALLOWED_IDS 블록 (환각 방지 — Phase 2 효과 확인)
    lines.append("=== ALLOWED_ITEM_IDS (you MUST pick from this list) ===")
    for c in candidates:
        rid = str(c.get("parent_asin", "")).strip()
        title = str(c.get("title", ""))[:60]
        lines.append(f"  - {rid}: {title}")
    lines.append("")
    if cross_domain_hint:
        lines.append("=== INSTRUCTION ===")
        lines.append("Use the user's Movies preferences to infer Books recommendations. "
                     "Apply your judgement about which signals transfer across domains.")
    else:
        lines.append("=== INSTRUCTION ===")
        lines.append("Recommend Top-10 books from the candidates. Output JSON only.")
    return "\n".join(lines)


def build_user_message_profile(profile: dict, candidates: list[dict]) -> str:
    """Profile JSON 기반 user message — (b)."""
    profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
    cand_lines = [format_candidate(c, i + 1) for i, c in enumerate(candidates)]
    lines = [
        "=== USER PROFILE ===",
        profile_json,
        "",
        "=== CANDIDATES (50 Books) ===",
        "\n\n".join(cand_lines),
        "",
        "=== ALLOWED_ITEM_IDS ===",
    ]
    for c in candidates:
        rid = str(c.get("parent_asin", "")).strip()
        title = str(c.get("title", ""))[:60]
        lines.append(f"  - {rid}: {title}")
    lines.extend([
        "",
        "=== INSTRUCTION ===",
        "Produce transfer_decisions for all 7 patterns in the Profile and recommend Top-10 books.",
    ])
    return "\n".join(lines)


# ============================================================
# OpenAI API call wrapper
# ============================================================

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```\s*$", flags=re.MULTILINE)


def _extract_json(text: str) -> dict | None:
    text = _JSON_FENCE_RE.sub("", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # try to find first { ... } block
        start = text.find("{")
        if start < 0:
            return None
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            c = text[i]
            if esc:
                esc = False
                continue
            if c == "\\":
                esc = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except Exception:
                        return None
        return None


def call_openai(client, system_prompt: str, user_message: str, max_retries: int = 3):
    """OpenAI API 호출 with JSON 강제 + retry."""
    last_error = None
    usage = {"input_tokens": 0, "output_tokens": 0, "attempts": 0}
    for attempt in range(max_retries):
        usage["attempts"] += 1
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=TEMPERATURE + (0.1 * attempt),
                max_tokens=MAX_OUTPUT_TOKENS,
                seed=SEED,
                response_format={"type": "json_object"},
            )
            usage["input_tokens"] += response.usage.prompt_tokens
            usage["output_tokens"] += response.usage.completion_tokens
            content = response.choices[0].message.content
            data = _extract_json(content)
            if data is None:
                last_error = f"JSON parse failed at attempt {attempt+1}"
                continue
            return data, usage, None
        except Exception as e:
            last_error = str(e)
            time.sleep(2 ** attempt)
    return None, usage, last_error


# ============================================================
# 메인
# ============================================================

def main():
    global MODEL, PRICE_INPUT_PER_1M, PRICE_OUTPUT_PER_1M
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", required=True, choices=["a_single", "b_prompt", "g_llm4cdr"])
    parser.add_argument("--test-users", type=Path, default=Path("data/test_users.parquet"))
    parser.add_argument("--profiles", type=Path, default=Path("profiler_outputs"))
    parser.add_argument("--movies-reviews", type=Path,
                        default=Path("data/movies_reviews_filtered.parquet"))
    parser.add_argument("--books-reviews", type=Path,
                        default=Path("data/books_reviews_filtered.parquet"))
    parser.add_argument("--books-meta", type=Path,
                        default=Path("data/books_meta_filtered.parquet"))
    parser.add_argument("--output", type=Path, default=None,
                        help="기본: results/ablation_{condition}.json")
    parser.add_argument("--n-candidates", type=int, default=50)
    parser.add_argument("--limit", type=int, default=0, help="0 = 전체, >0 = smoke")
    parser.add_argument("--fixture-dir", type=Path, default=None,
                        help="평가 fixture 디렉토리 (eval_fixtures/). 권장: baseline과 동일 조건 보장.")
    parser.add_argument("--model", type=str, default=None,
                        help=f"OpenAI 모델 (기본: {MODEL}). 예: gpt-4o, gpt-4o-mini")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경변수 필요")
        sys.exit(1)

    # Override model from CLI
    if args.model:
        MODEL = args.model
        if MODEL in MODEL_PRICING:
            PRICE_INPUT_PER_1M, PRICE_OUTPUT_PER_1M = MODEL_PRICING[MODEL]
        else:
            print(f"⚠ Warning: {MODEL} pricing unknown, using gpt-4o-mini rates")

    output_path = args.output or Path(f"results/ablation_{args.condition}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== Phase 4 Baseline: {args.condition} ===")
    print(f"  Model: {MODEL}  (${PRICE_INPUT_PER_1M}/M in, ${PRICE_OUTPUT_PER_1M}/M out)")
    print(f"  Output: {output_path}")

    # 데이터 로드
    print("\nLoading data...")
    use_fixture = args.fixture_dir is not None and args.fixture_dir.exists()
    fixture_data = None
    if use_fixture:
        print(f"  ★ FIXTURE 모드: {args.fixture_dir}")
        fixture_data = {
            "users": json.load((args.fixture_dir / "test_users.json").open()),
            "gt": json.load((args.fixture_dir / "gt.json").open()),
            "cand_dir": args.fixture_dir / "candidates",
        }
        test_users = pd.DataFrame({"user_id": fixture_data["users"]})
    else:
        test_users = pd.read_parquet(args.test_users)
    if args.limit > 0:
        test_users = test_users.head(args.limit)
        print(f"  ⚠ SMOKE: limit={args.limit}")
    print(f"  test users: {len(test_users)}")

    movies = pd.read_parquet(args.movies_reviews)
    books = pd.read_parquet(args.books_reviews)
    books_meta = pd.read_parquet(args.books_meta) if not use_fixture else None

    from openai import OpenAI
    client = OpenAI(timeout=120.0, max_retries=2)

    # 실행
    per_user_results = []
    val_counts = Counter()
    total_usage = {"input_tokens": 0, "output_tokens": 0, "attempts": 0,
                   "success": 0, "fail": 0}
    decision_dist = Counter()
    rng = np.random.default_rng(SEED)
    start_time = time.time()

    for idx, user_row in enumerate(test_users.itertuples(index=False)):
        user_id = getattr(user_row, "user_id")
        user_start = time.time()

        # GT & candidates: fixture 우선
        if use_fixture:
            gt_entry = fixture_data["gt"].get(user_id)
            if gt_entry is None:
                print(f"  [{idx+1}/{len(test_users)}] {user_id}: not in fixture, skip")
                total_usage["fail"] += 1
                continue
            gt_id = str(gt_entry["gt_id"])
            cand_file = fixture_data["cand_dir"] / f"user_{user_id}.json"
            if not cand_file.exists():
                print(f"  [{idx+1}/{len(test_users)}] {user_id}: no candidate file")
                total_usage["fail"] += 1
                continue
            candidates = json.load(cand_file.open())
            user_books = books[books["user_id"] == user_id]  # GT timestamp용
        else:
            user_books = books[books["user_id"] == user_id]
            gt_info = pick_gt(user_books)
            if gt_info is None:
                print(f"  [{idx+1}/{len(test_users)}] {user_id}: no GT, skip")
                total_usage["fail"] += 1
                continue
            gt_id = gt_info["parent_asin"]
            try:
                candidates = sample_candidates(
                    user_id=user_id, gt_item_id=gt_id,
                    books_meta_df=books_meta,
                    user_books_reviews=user_books,
                    n_candidates=args.n_candidates, rng=rng,
                )
            except ValueError as e:
                print(f"  [{idx+1}/{len(test_users)}] {user_id}: candidate err: {e}")
                total_usage["fail"] += 1
                continue
        cand_set = {str(c.get("parent_asin", "")).strip() for c in candidates}

        # User message 구성 (조건별)
        if args.condition == "b_prompt":
            profile_file = args.profiles / f"user_{user_id}.json"
            if not profile_file.exists():
                print(f"  [{idx+1}/{len(test_users)}] {user_id}: no profile, skip")
                total_usage["fail"] += 1
                continue
            profile = json.loads(profile_file.read_text())
            user_msg = build_user_message_profile(profile, candidates)
        else:
            # (a)와 (g): raw 영화 리뷰 + temporal cutoff
            gt_ts = user_books[user_books["parent_asin"] == gt_id]["timestamp"].iloc[0]
            user_movies = movies[(movies["user_id"] == user_id) &
                                 (movies["timestamp"] < gt_ts)]
            user_movies = user_movies.sort_values("timestamp", ascending=False).head(30)
            if len(user_movies) < 5:
                print(f"  [{idx+1}/{len(test_users)}] {user_id}: <5 movies after cutoff, skip")
                total_usage["fail"] += 1
                continue
            user_msg = build_user_message_raw_reviews(
                user_movies, candidates,
                cross_domain_hint=(args.condition == "g_llm4cdr"),
            )

        # API call
        system_prompt = SYSTEMS[args.condition]
        output, usage, error = call_openai(client, system_prompt, user_msg)
        total_usage["input_tokens"] += usage["input_tokens"]
        total_usage["output_tokens"] += usage["output_tokens"]
        total_usage["attempts"] += usage["attempts"]

        if output is None:
            print(f"  [{idx+1}/{len(test_users)}] {user_id}: API fail ({error})")
            total_usage["fail"] += 1
            continue

        # 검증 + 메트릭
        validation = validate_output(output, cand_set, gt_id)
        rec_ids = [str(r.get("item_id", "")) for r in output.get("recommendations", [])
                   if isinstance(r, dict)]
        metrics = compute_per_user_metrics(rec_ids, gt_id)
        for k, v in validation.items():
            val_counts[k] += int(bool(v))

        # decision 분포 (b만)
        td = output.get("transfer_decisions", {})
        if isinstance(td, dict):
            for p, info in td.items():
                if isinstance(info, dict):
                    decision_dist[info.get("decision", "?")] += 1

        per_user_results.append({
            "user_id": user_id,
            "gt_id": gt_id,
            "rec_ids": rec_ids[:10],
            "metrics": metrics,
            "validation": validation,
            "decision_counts": {k: sum(1 for p, info in td.items()
                                       if isinstance(info, dict) and info.get("decision") == k)
                                for k in ["TRANSFER", "PARTIAL", "BLOCK"]} if td else {},
            "tokens": usage,
            "elapsed_s": round(time.time() - user_start, 1),
        })
        total_usage["success"] += 1

        elapsed_total = time.time() - start_time
        cost = (total_usage["input_tokens"] / 1e6 * PRICE_INPUT_PER_1M
                + total_usage["output_tokens"] / 1e6 * PRICE_OUTPUT_PER_1M)
        print(f"  [{idx+1}/{len(test_users)}] {user_id[:15]}: "
              f"HR@10={metrics['HR@10']} NDCG@10={metrics['NDCG@10']:.3f} "
              f"({usage['attempts']} try, ${cost:.3f} so far, {elapsed_total:.0f}s)")

    # 집계 — per_user의 'metrics' 필드만 추출해 aggregate_metrics에 전달
    summary_metrics = (aggregate_metrics([r["metrics"] for r in per_user_results])
                       if per_user_results else {})
    val_pass_rate = {k: val_counts[k] / max(1, len(per_user_results))
                     for k in ["is_valid_json", "schema_complete", "all_in_candidates",
                                "no_duplicates", "no_block_leakage"]}
    cost = (total_usage["input_tokens"] / 1e6 * PRICE_INPUT_PER_1M
            + total_usage["output_tokens"] / 1e6 * PRICE_OUTPUT_PER_1M)

    summary = {
        "condition": args.condition,
        "model": MODEL,
        "n_evaluated": len(per_user_results),
        "n_failed": total_usage["fail"],
        "metrics": summary_metrics,
        "validation_pass_rate": val_pass_rate,
        "decision_distribution_total": dict(decision_dist),
        "tokens": {
            "input": total_usage["input_tokens"],
            "output": total_usage["output_tokens"],
            "attempts": total_usage["attempts"],
        },
        "cost_usd": round(cost, 4),
        "elapsed_s": round(time.time() - start_time, 1),
        "params": {
            "n_candidates": args.n_candidates,
            "max_new_tokens": MAX_OUTPUT_TOKENS,
            "seed": SEED,
            "limit": args.limit,
        },
    }

    output_path.write_text(json.dumps({"summary": summary, "per_user": per_user_results},
                                       indent=2, ensure_ascii=False))
    print(f"\n=== {args.condition} 완료 ===")
    print(f"  success: {len(per_user_results)} / {len(test_users)}")
    print(f"  metrics: {summary_metrics}")
    print(f"  cost: ${cost:.4f}")
    print(f"  saved: {output_path}")


if __name__ == "__main__":
    main()
