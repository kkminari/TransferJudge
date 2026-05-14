"""Pilot Study — 100명 비구조화 패턴 추출 (GPT-4o-mini API).

본 실험 Profiler와 차이:
  - Core Pattern 6개 사전 정보 미제공 (편향 방지)
  - 패턴 종류·이름·개수 자유 (5~15개 권장)
  - transferability_hint 없음 (사후 분석에서 도출)

사용법:
  # .env 파일에 OPENAI_API_KEY 입력 후
  python scripts/run_pilot.py --dry-run --n-users 3   # 프롬프트 검증
  python scripts/run_pilot.py --n-users 5             # 5명 시범 실행
  python scripts/run_pilot.py                         # 100명 전체 실행

출력:
  pilot_outputs/user_{id}.json × N
  pilot_outputs/run.log
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

ROOT = Path(__file__).resolve().parent.parent

# .env 로드 (python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

MODEL = "gpt-4o-mini"
TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 2000  # 비구조화이므로 본 실험 1500보다 약간 ↑
SEED = 42
PRICE_INPUT_PER_1M = 0.15
PRICE_OUTPUT_PER_1M = 0.60

REQUIRED_FIELDS_PATTERN = {"name", "description", "evidence", "confidence", "polarity"}
VALID_POLARITIES = {"positive", "negative", "mixed"}


# ========== 비구조화 프롬프트 ==========

SYSTEM_PROMPT = """You are an expert user preference analyst. Your task is to read a user's
Movies & TV reviews and extract the preference patterns you genuinely observe in the data.

## Important Rules

- Naming and number of patterns is up to YOU. Discover patterns naturally from the reviews.
- DO NOT use any predefined list of pattern types. Avoid generic catch-all categories.
- Pattern names must be snake_case (e.g., "narrative_complexity", "atmospheric_mood",
  "auteur_loyalty"). Be specific and descriptive.
- Each pattern must include:
  - name (snake_case)
  - description (1-2 sentences explaining what this pattern captures)
  - evidence (1-2 review quotes that directly support this pattern)
  - confidence (0.0-1.0): how strongly the data supports this pattern
  - polarity (positive | negative | mixed): whether the user likes, dislikes, or is mixed

## Quality Guidelines

- Aim for 5-15 patterns per user — extract what you genuinely observe.
- Avoid trivial patterns (e.g., "user_likes_movies", "watches_films" are too vague).
- Patterns should be ACTIONABLE for cross-domain recommendation
  (e.g., useful for recommending books to this user — think about what transfers vs what doesn't).
- Negative reviews (rating <= 2) are valuable — they reveal what the user DISLIKES.
- DO NOT invent preferences not supported by review text.
- Each pattern's evidence must directly quote or closely paraphrase actual review content.

## Output Schema (strict JSON)

{
  "user_id": "<string>",
  "patterns": [
    {
      "name": "<snake_case_name>",
      "description": "<1-2 sentences>",
      "evidence": ["<review quote 1>", "<review quote 2>"],
      "confidence": <float 0.0-1.0>,
      "polarity": "<positive|negative|mixed>"
    }
  ],
  "summary": "<2-3 sentence overall taste summary>"
}

Output ONLY the JSON object. No prose, no markdown fences.
"""


def build_user_message(user_id: str, reviews_df: pd.DataFrame) -> str:
    reviews_df = reviews_df.sort_values("timestamp", ascending=False)
    lines = [f"User ID: {user_id}", "", "=== Movies & TV Reviews (most recent first) ===", ""]
    for i, (_, row) in enumerate(reviews_df.iterrows(), start=1):
        rating = row.get("rating", "N/A")
        title = str(row.get("title", "")).strip() or "(no title)"
        text = str(row.get("text", "")).strip()
        lines.append(f'[Review {i}] Rating: {rating}/5.0 | Title: "{title}"')
        lines.append(f'"{text}"')
        lines.append("")
    lines.extend([
        "=== Instruction ===",
        "",
        f"Analyze the above {len(reviews_df)} reviews and extract the user's preference patterns.",
        "Discover patterns naturally — do not use any predefined list.",
        "Output valid JSON following the schema.",
    ])
    return "\n".join(lines)


# ========== 검증 ==========

@dataclass
class PilotValidation:
    is_valid: bool
    n_patterns: int = 0
    invalid_patterns: list[str] = field(default_factory=list)
    avg_confidence: float = 0.0
    polarity_distribution: dict[str, int] = field(default_factory=dict)


def validate_output(data: dict[str, Any]) -> PilotValidation:
    result = PilotValidation(is_valid=True)
    patterns = data.get("patterns", [])
    if not isinstance(patterns, list):
        result.is_valid = False
        return result
    result.n_patterns = len(patterns)
    if result.n_patterns < 1:
        result.is_valid = False
        return result

    confs, pols = [], []
    for i, p in enumerate(patterns):
        missing = REQUIRED_FIELDS_PATTERN - set(p.keys())
        if missing:
            result.invalid_patterns.append(f"#{i}: missing {missing}")
            continue
        try:
            conf = float(p.get("confidence", 0.0))
            confs.append(conf)
        except (TypeError, ValueError):
            result.invalid_patterns.append(f"#{i}: confidence not float")
        pol = p.get("polarity", "")
        if pol in VALID_POLARITIES:
            pols.append(pol)
        else:
            result.invalid_patterns.append(f"#{i}: polarity={pol}")

    if confs:
        result.avg_confidence = sum(confs) / len(confs)
    for pol in pols:
        result.polarity_distribution[pol] = result.polarity_distribution.get(pol, 0) + 1

    if not data.get("summary"):
        result.invalid_patterns.append("summary missing")

    if result.invalid_patterns:
        result.is_valid = False
    return result


# ========== API ==========

def call_pilot_api(client, user_id: str, user_message: str, max_retries: int = 3):
    usage = {"input_tokens": 0, "output_tokens": 0, "attempts": 0}
    for attempt in range(max_retries):
        usage["attempts"] += 1
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=TEMPERATURE + 0.1 * attempt,
                max_tokens=MAX_OUTPUT_TOKENS,
                seed=SEED,
                response_format={"type": "json_object"},
            )
            usage["input_tokens"] += resp.usage.prompt_tokens
            usage["output_tokens"] += resp.usage.completion_tokens
            data = json.loads(resp.choices[0].message.content)
            data.setdefault("user_id", user_id)
            val = validate_output(data)
            if val.is_valid:
                return data, usage, val
            logging.warning(f"[{user_id}] attempt {attempt+1} invalid: {val.invalid_patterns[:3]}")
        except json.JSONDecodeError as e:
            logging.warning(f"[{user_id}] attempt {attempt+1} JSON error: {e}")
        except Exception as e:
            logging.warning(f"[{user_id}] attempt {attempt+1} API error: {e}")
            time.sleep(2 ** attempt)
    return None, usage, None


# ========== Main ==========

def run(users_path: Path, reviews_path: Path, output_dir: Path,
        n_users: int, max_reviews: int, dry_run: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    users_df = pd.read_parquet(users_path)
    if n_users > 0:
        users_df = users_df.head(n_users).copy()
    logging.info(f"Target users: {len(users_df)}")

    reviews_df = pd.read_parquet(reviews_path)
    logging.info(f"Total reviews: {len(reviews_df):,}")

    client = None
    if not dry_run:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit(
                "❌ OPENAI_API_KEY 미설정. .env 파일에 키를 입력하거나 export로 설정하세요."
            )
        from openai import OpenAI
        client = OpenAI()

    total = {"input_tokens": 0, "output_tokens": 0, "success": 0, "failure": 0,
             "n_patterns_total": 0, "n_users_with_negative": 0}
    start = time.time()

    for idx, urow in enumerate(users_df.itertuples(index=False)):
        uid = urow.user_id
        out_path = output_dir / f"user_{uid}.json"
        if out_path.exists() and not dry_run:
            continue

        urev = reviews_df[reviews_df["user_id"] == uid].head(max_reviews)
        if len(urev) < 15:
            logging.warning(f"[{uid}] skip ({len(urev)} reviews < 15)")
            continue

        msg = build_user_message(uid, urev)

        if dry_run:
            print("=" * 60)
            print(f"[DRY RUN] {uid} ({len(urev)} reviews)")
            print(msg[:1500])
            if idx >= 1:
                print("\n(dry-run: first 2 users)")
                break
            continue

        out, usage, val = call_pilot_api(client, uid, msg)
        total["input_tokens"] += usage["input_tokens"]
        total["output_tokens"] += usage["output_tokens"]
        if out is not None and val is not None and val.is_valid:
            out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))
            total["success"] += 1
            total["n_patterns_total"] += val.n_patterns
            if val.polarity_distribution.get("negative", 0) > 0:
                total["n_users_with_negative"] += 1
        else:
            total["failure"] += 1

        if (idx + 1) % 10 == 0:
            elapsed = time.time() - start
            cost = (total["input_tokens"] / 1_000_000 * PRICE_INPUT_PER_1M
                    + total["output_tokens"] / 1_000_000 * PRICE_OUTPUT_PER_1M)
            avg_pat = total["n_patterns_total"] / max(total["success"], 1)
            logging.info(
                f"Progress {idx+1}/{len(users_df)} | "
                f"success={total['success']} fail={total['failure']} | "
                f"avg_patterns={avg_pat:.1f} negative_users={total['n_users_with_negative']} | "
                f"cost=${cost:.3f} | elapsed={elapsed:.0f}s"
            )

    cost = (total["input_tokens"] / 1_000_000 * PRICE_INPUT_PER_1M
            + total["output_tokens"] / 1_000_000 * PRICE_OUTPUT_PER_1M)
    avg_pat = total["n_patterns_total"] / max(total["success"], 1)
    logging.info(
        f"DONE | success={total['success']} fail={total['failure']} | "
        f"total_patterns={total['n_patterns_total']} (avg {avg_pat:.1f}/user) | "
        f"users_with_negative={total['n_users_with_negative']} | cost=${cost:.3f}"
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--users", type=Path, default=ROOT / "data" / "pilot_users.parquet")
    p.add_argument("--reviews", type=Path, default=ROOT / "data" / "movies_reviews_filtered.parquet")
    p.add_argument("--output", type=Path, default=ROOT / "pilot_outputs")
    p.add_argument("--n-users", type=int, default=0, help="0 = all")
    p.add_argument("--max-reviews", type=int, default=30)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    run(users_path=args.users, reviews_path=args.reviews, output_dir=args.output,
        n_users=args.n_users, max_reviews=args.max_reviews, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
