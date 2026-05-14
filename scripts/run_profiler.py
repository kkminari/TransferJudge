"""Profiler — Source 리뷰에서 7개 Core Pattern 추출 (temporal-cutoff 적용).

각 사용자의 GT(Books 도메인 rating≥4 최근) timestamp를 사전 계산하고,
Source(Movies) 리뷰 중 GT 이전 시점만 입력으로 사용.

사용법:
    python scripts/run_profiler.py \\
        --users data/overlapping_users.parquet \\
        --reviews data/movies_reviews_filtered.parquet \\
        --target-reviews data/books_reviews_filtered.parquet \\
        --output profiler_outputs/ \\
        --n-users 1000 \\
        --max-reviews 30 \\
        --min-reviews 15 \\
        --dry-run

요구사항:
    pip install openai tiktoken pandas pyarrow
    export OPENAI_API_KEY="sk-..."
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

# .env 자동 로드 (OPENAI_API_KEY 등)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv 없으면 환경변수 그대로 사용


# ========== 설정 ==========

MODEL = "gpt-4o-mini"
TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 2000  # 7개 core + 3 additional + summary 안전 마진 (원 1500에서 상향)
SEED = 42
PRICE_INPUT_PER_1M = 0.15  # USD
PRICE_OUTPUT_PER_1M = 0.60  # USD

REQUIRED_CORE_PATTERNS = [
    "genre_preference",
    "narrative_complexity",
    "pacing_preference",
    "quality_sensitivity",
    "brand_loyalty",
    "sensory_preference",
    "emotional_resonance",
]

REQUIRED_PATTERN_KEYS = {
    "value",
    "evidence",
    "confidence",
    "polarity",
    "transferability_hint",
}

VALID_POLARITIES = {"positive", "negative", "mixed"}
VALID_TRANSFERABILITIES = {"high", "medium", "low"}


# ========== Prompt 정의 ==========

SYSTEM_PROMPT = """You are an expert user preference analyst specializing in cross-domain recommendation.
Your task is to extract structured preference patterns from a user's Movies & TV reviews
that will later be used to recommend books to this user.

## Core Patterns to Extract (MANDATORY)

For each user, you MUST analyze the following 7 core patterns:

1. genre_preference — Preferred genres/categories (e.g., sci-fi, thriller, drama, romance).
   Report BOTH preferred and disliked genres if evidence exists.

2. narrative_complexity — Preference for narrative complexity.
   "complex" = multi-layered plots, non-linear timelines, unreliable narrators.
   "simple" = linear, straightforward storytelling.

3. pacing_preference — Preference for pacing.
   "fast" = action-heavy, quick scene transitions, high-tension.
   "slow" = character-driven, contemplative, slow-burn.

4. quality_sensitivity — How much the user cares about production quality.
   "high" = frequently mentions direction, acting, cinematography quality.
   "low" = focuses on story/entertainment regardless of production polish.

5. brand_loyalty — Loyalty to specific creators.
   Identify mentions of favorite directors, actors, franchises, series.
   Note: If no such loyalty is evident, mark confidence as low.

6. sensory_preference — Preference for sensory experience. Distinguish TWO sub-types:
   (a) MEDIUM-SPECIFIC sensory (BLOCK-leaning for books): visual spectacle (special effects,
       animation, action choreography), sound (soundtrack, IMAX audio), explosions, fight scenes.
       These do not exist in books.
   (b) MEDIUM-AGNOSTIC sensory (TRANSFERABLE to books): atmosphere/mood (e.g. "felt immersive",
       "haunting tone"), imagery/visual writing (e.g. "scenes felt vivid"), tactile/emotional
       texture (e.g. "uplifting", "cozy", "intimate"). These describe how the experience FEELS
       and can apply to books through prose and descriptive writing.
   In "value" and "evidence", be explicit about which sub-type the user prefers; the downstream
   Transfer Judge uses this to decide TRANSFER vs BLOCK.

7. emotional_resonance — Emphasis on emotional impact and resonance.
   "high" = content evokes deep feelings, lasting memory, personal meaning ("brought tears", "stayed with me").
   "low" = focuses on entertainment without strong emotional engagement.

## Output Requirements

- Output MUST be a single valid JSON object following the schema below.
- Each core pattern must include: value, evidence, confidence, polarity, transferability_hint.
- "evidence" must quote or closely paraphrase specific review text (max 2 citations per pattern).
- "confidence" in [0.0, 1.0]: 1.0 if strongly supported by multiple reviews, 0.2 if weakly hinted.
- "polarity" in {"positive", "negative", "mixed"}: whether the user likes, dislikes, or has mixed feelings.
- "transferability_hint" in {"high", "medium", "low"}: initial estimate of how well this pattern
  transfers to the Books domain. This is a HINT only; the downstream Transfer Judge makes the final decision.
- You MAY add up to 3 additional_patterns that are strongly evidenced but not in the core 7.
- "summary" must be 2-3 sentences capturing the user's overall taste.

## Evidence Grounding Rules

- DO NOT invent preferences not supported by review text.
- If evidence is weak or absent for a core pattern, set confidence <= 0.3 and polarity to "mixed".
- Negative reviews (rating <= 2) are VALUABLE — they reveal what the user DISLIKES.
- If the user gave a low rating citing specific reasons (e.g., "too slow"), this reveals pacing_preference.

## Output Schema (strict JSON)

{
  "user_id": "<string>",
  "core_patterns": {
    "genre_preference":       {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "narrative_complexity":   {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "pacing_preference":      {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "quality_sensitivity":    {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "brand_loyalty":          {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "sensory_preference":     {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "emotional_resonance":    {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"}
  },
  "additional_patterns": [
    {"name": "<snake_case_name>", "value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"}
  ],
  "summary": "<2-3 sentence overall taste summary>"
}

Output ONLY the JSON object, no prose, no markdown fences.
"""


def build_user_message(user_id: str, reviews_df: pd.DataFrame) -> str:
    """최신순 정렬된 리뷰로 User Message 구성."""
    reviews_df = reviews_df.sort_values("timestamp", ascending=False)
    lines = [f"User ID: {user_id}", "", "=== Source Domain (Movies & TV) Reviews ===", ""]
    for i, (_, row) in enumerate(reviews_df.iterrows(), start=1):
        rating = row.get("rating", "N/A")
        title = str(row.get("title", "")).strip() or "(no title)"
        text = str(row.get("text", "")).strip()
        lines.append(f"[Review {i}] Rating: {rating}/5.0 | Title: \"{title}\"")
        lines.append(f'"{text}"')
        lines.append("")
    lines.extend([
        "=== Instruction ===",
        "",
        f"Analyze the above {len(reviews_df)} reviews and extract the user's preference patterns following the schema.",
        "Output valid JSON only.",
    ])
    return "\n".join(lines)


# ========== 출력 검증 ==========

@dataclass
class ValidationResult:
    is_valid: bool
    missing_patterns: list[str] = field(default_factory=list)
    invalid_fields: list[str] = field(default_factory=list)
    low_confidence_count: int = 0
    avg_confidence: float = 0.0


def validate_output(data: dict[str, Any]) -> ValidationResult:
    """출력 JSON의 스키마·완전성 검증."""
    result = ValidationResult(is_valid=True)

    if "core_patterns" not in data:
        result.is_valid = False
        result.missing_patterns = REQUIRED_CORE_PATTERNS
        return result

    core = data["core_patterns"]
    confidences = []

    for pattern_name in REQUIRED_CORE_PATTERNS:
        if pattern_name not in core:
            result.missing_patterns.append(pattern_name)
            result.is_valid = False
            continue

        pattern = core[pattern_name]
        missing_keys = REQUIRED_PATTERN_KEYS - set(pattern.keys())
        if missing_keys:
            result.invalid_fields.append(f"{pattern_name} missing {missing_keys}")
            result.is_valid = False
            continue

        conf = pattern.get("confidence", 0.0)
        try:
            conf = float(conf)
            confidences.append(conf)
            if conf < 0.3:
                result.low_confidence_count += 1
        except (TypeError, ValueError):
            result.invalid_fields.append(f"{pattern_name}.confidence not float")
            result.is_valid = False

        pol = pattern.get("polarity", "")
        if pol not in VALID_POLARITIES:
            result.invalid_fields.append(f"{pattern_name}.polarity={pol}")
            result.is_valid = False

        tr = pattern.get("transferability_hint", "")
        if tr not in VALID_TRANSFERABILITIES:
            result.invalid_fields.append(f"{pattern_name}.transferability_hint={tr}")
            result.is_valid = False

    if confidences:
        result.avg_confidence = sum(confidences) / len(confidences)

    if "summary" not in data or not str(data.get("summary", "")).strip():
        result.invalid_fields.append("summary missing")
        result.is_valid = False

    return result


# ========== API 호출 ==========

def call_profiler_api(
    client,
    user_id: str,
    user_message: str,
    max_retries: int = 3,
) -> tuple[dict[str, Any] | None, dict[str, int]]:
    """재시도 로직 포함 API 호출. (output_json, usage_stats) 반환."""
    usage = {"input_tokens": 0, "output_tokens": 0, "attempts": 0}
    last_error = None

    for attempt in range(max_retries):
        usage["attempts"] += 1
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=TEMPERATURE + (0.1 * attempt),  # 재시도 시 미세 온도 상승
                max_tokens=MAX_OUTPUT_TOKENS,
                seed=SEED,
                response_format={"type": "json_object"},
            )
            usage["input_tokens"] += response.usage.prompt_tokens
            usage["output_tokens"] += response.usage.completion_tokens

            content = response.choices[0].message.content
            data = json.loads(content)
            data.setdefault("user_id", user_id)

            val = validate_output(data)
            if val.is_valid:
                return data, usage

            logging.warning(
                f"[{user_id}] Attempt {attempt+1} validation failed: "
                f"missing={val.missing_patterns}, invalid={val.invalid_fields[:3]}"
            )
            last_error = f"validation failed: {val.missing_patterns[:3]}{val.invalid_fields[:3]}"
        except json.JSONDecodeError as e:
            last_error = f"json decode: {e}"
            logging.warning(f"[{user_id}] Attempt {attempt+1} JSON error: {e}")
        except Exception as e:
            last_error = f"api error: {e}"
            logging.warning(f"[{user_id}] Attempt {attempt+1} API error: {e}")
            time.sleep(2 ** attempt)  # exponential backoff

    logging.error(f"[{user_id}] All {max_retries} attempts failed: {last_error}")
    return None, usage


# ========== Main Loop ==========

def compute_gt_timestamps(target_reviews_df: pd.DataFrame) -> dict[str, int]:
    """각 사용자별 GT timestamp 사전 계산 (Books rating≥4 중 가장 최근)."""
    pos = target_reviews_df[target_reviews_df["rating"] >= 4.0]
    gt_ts = pos.groupby("user_id")["timestamp"].max().to_dict()
    return gt_ts


def run(
    users_path: Path,
    reviews_path: Path,
    target_reviews_path: Path,
    output_dir: Path,
    n_users: int,
    max_reviews: int,
    min_reviews: int,
    dry_run: bool = False,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.info(f"Loading users from {users_path}")
    users_df = pd.read_parquet(users_path)
    if n_users > 0:
        users_df = users_df.sample(n=min(n_users, len(users_df)), random_state=SEED)
    logging.info(f"Target users: {len(users_df)}")

    logging.info(f"Loading source reviews from {reviews_path}")
    reviews_df = pd.read_parquet(reviews_path)
    logging.info(f"Total source reviews: {len(reviews_df):,}")

    logging.info(f"Loading target reviews from {target_reviews_path} (for GT timestamp)")
    target_reviews_df = pd.read_parquet(target_reviews_path)
    gt_ts_map = compute_gt_timestamps(target_reviews_df)
    logging.info(f"GT timestamps computed for {len(gt_ts_map):,} users")
    del target_reviews_df

    client = None
    if not dry_run:
        try:
            from openai import OpenAI
            client = OpenAI(timeout=60.0, max_retries=2)
        except ImportError:
            raise SystemExit("Install openai: pip install openai")

    total_usage = {
        "input_tokens": 0, "output_tokens": 0,
        "success": 0, "failure": 0,
        "no_gt": 0, "short_after_cutoff": 0,
    }
    short_segment = []  # cutoff 후 <min_reviews 사용자 기록
    start = time.time()

    for idx, user_row in enumerate(users_df.itertuples(index=False)):
        user_id = getattr(user_row, "user_id")
        out_path = output_dir / f"user_{user_id}.json"
        if out_path.exists():
            logging.debug(f"[{user_id}] skip (already done)")
            continue

        # GT timestamp 확보 (없으면 skip — 본 실험 대상 아님)
        gt_ts = gt_ts_map.get(user_id)
        if gt_ts is None:
            logging.warning(f"[{user_id}] skip (no GT in target domain)")
            total_usage["no_gt"] += 1
            continue

        # Temporal cutoff: GT 이전 영화 리뷰만, 최신순 max_reviews개
        user_all = reviews_df[reviews_df["user_id"] == user_id]
        user_cutoff = user_all[user_all["timestamp"] < gt_ts]
        user_reviews = user_cutoff.sort_values("timestamp", ascending=False).head(max_reviews)

        if len(user_reviews) < min_reviews:
            logging.warning(
                f"[{user_id}] skip (after cutoff {len(user_reviews)} reviews, <{min_reviews}) "
                f"[total={len(user_all)}, cutoff_loss={len(user_all) - len(user_cutoff)}]"
            )
            total_usage["short_after_cutoff"] += 1
            short_segment.append({
                "user_id": user_id,
                "total_reviews": int(len(user_all)),
                "after_cutoff": int(len(user_reviews)),
                "lost_to_cutoff": int(len(user_all) - len(user_cutoff)),
                "gt_ts": int(gt_ts),
            })
            continue

        user_message = build_user_message(user_id, user_reviews)

        if dry_run:
            print("=" * 60)
            print(f"[DRY RUN] user_id={user_id}, reviews={len(user_reviews)}")
            print("-" * 60)
            print(user_message[:2000])
            print("..." if len(user_message) > 2000 else "")
            if idx >= 2:
                print("\n(dry-run: showing first 3 users only)")
                break
            continue

        output, usage = call_profiler_api(client, user_id, user_message)
        total_usage["input_tokens"] += usage["input_tokens"]
        total_usage["output_tokens"] += usage["output_tokens"]

        if output is not None:
            out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
            total_usage["success"] += 1
        else:
            total_usage["failure"] += 1

        if (idx + 1) % 50 == 0:
            elapsed = time.time() - start
            cost = (
                total_usage["input_tokens"] / 1_000_000 * PRICE_INPUT_PER_1M
                + total_usage["output_tokens"] / 1_000_000 * PRICE_OUTPUT_PER_1M
            )
            logging.info(
                f"Progress {idx+1}/{len(users_df)} | "
                f"success={total_usage['success']} fail={total_usage['failure']} | "
                f"in={total_usage['input_tokens']:,} out={total_usage['output_tokens']:,} | "
                f"cost=${cost:.3f} | elapsed={elapsed:.0f}s"
            )

    cost = (
        total_usage["input_tokens"] / 1_000_000 * PRICE_INPUT_PER_1M
        + total_usage["output_tokens"] / 1_000_000 * PRICE_OUTPUT_PER_1M
    )
    logging.info(
        f"DONE | success={total_usage['success']} fail={total_usage['failure']} "
        f"no_gt={total_usage['no_gt']} short_after_cutoff={total_usage['short_after_cutoff']} | "
        f"total_cost=${cost:.3f}"
    )

    # cutoff 후 부족한 사용자 segment 기록
    if short_segment and not dry_run:
        seg_path = output_dir.parent / f"{output_dir.name}_short_segment.json"
        seg_path.write_text(json.dumps(short_segment, indent=2, ensure_ascii=False))
        logging.info(f"Short-after-cutoff segment saved: {seg_path} (n={len(short_segment)})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True,
                        help="Source domain reviews (e.g. movies)")
    parser.add_argument("--target-reviews", type=Path, required=True,
                        help="Target domain reviews for GT timestamp lookup (e.g. books)")
    parser.add_argument("--output", type=Path, default=Path("profiler_outputs"))
    parser.add_argument("--n-users", type=int, default=0, help="0 = all")
    parser.add_argument("--max-reviews", type=int, default=30)
    parser.add_argument("--min-reviews", type=int, default=15,
                        help="Minimum reviews after temporal cutoff to include user")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    run(
        users_path=args.users,
        reviews_path=args.reviews,
        target_reviews_path=args.target_reviews,
        output_dir=args.output,
        n_users=args.n_users,
        max_reviews=args.max_reviews,
        min_reviews=args.min_reviews,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
