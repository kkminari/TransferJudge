"""Teacher Distillation — Profiler Output + Candidates → TRANSFER/PARTIAL/BLOCK 판정 + Top-10.

생성된 데이터는 Qwen3-14B QLoRA 파인튜닝(SFT)의 학습 데이터가 됨.

사용법:
    python scripts/run_teacher.py \\
        --profiler-dir profiler_outputs/ \\
        --users data/overlapping_users.parquet \\
        --books-reviews data/books_reviews_filtered.parquet \\
        --books-meta data/books_meta_filtered.parquet \\
        --output teacher_outputs/ \\
        --training-data data/train.jsonl \\
        --n-candidates 50 \\
        --dry-run

요구사항:
    pip install openai tiktoken pandas pyarrow
    export OPENAI_API_KEY="sk-..."
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# .env 자동 로드 (OPENAI_API_KEY 등)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ========== 설정 ==========

MODEL = "gpt-4o-mini"
TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 2500
SEED = 42
PRICE_INPUT_PER_1M = 0.15
PRICE_OUTPUT_PER_1M = 0.60

REQUIRED_CORE_PATTERNS = [
    "genre_preference",
    "narrative_complexity",
    "pacing_preference",
    "quality_sensitivity",
    "brand_loyalty",
    "sensory_preference",
    "emotional_resonance",
]
VALID_DECISIONS = {"TRANSFER", "PARTIAL", "BLOCK"}
N_RECOMMENDATIONS = 10


# ========== Prompt 정의 ==========

SYSTEM_PROMPT = """You are an expert Cross-Domain Transfer Judge. Your task is to decide how a user's
Movies & TV preference patterns should transfer to Books recommendations, and produce
a Top-10 ranked list of books.

You are generating TRAINING DATA for a student model. Your reasoning quality matters.

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
  sensory_preference of the MEDIUM-SPECIFIC sub-type (visual special effects, IMAX, action
  choreography, soundtrack, explosions).

## Important — sensory_preference is NOT always BLOCK

sensory_preference has TWO sub-types:
- (a) MEDIUM-SPECIFIC (visual spectacle, soundtrack, action choreography) → BLOCK.
- (b) MEDIUM-AGNOSTIC (atmosphere, mood, imagery/descriptive writing, "immersive", "cozy",
      "haunting", "uplifting") → TRANSFER or PARTIAL. Books achieve these through prose.

Read the "value" and "evidence" of sensory_preference in the Profile carefully. If the user
values atmosphere/imagery/tone, do NOT auto-BLOCK; recommend books with vivid prose or
matching atmosphere instead.

## Ground Truth Calibration (for training data quality)

You will be given a GROUND_TRUTH_HINT: the item the user actually purchased and rated highly in Books.
This hint is provided ONLY to help you calibrate your reasoning quality — if your pattern decisions
are correct, your Top-10 should naturally include this item.

STRICT RULES:
- DO NOT mention the ground truth in your rationale, reasoning, or any output text.
- DO NOT artificially boost the ground truth's score; reason naturally based on Profile.
- If your honest reasoning does not place the ground truth in Top-10, revisit your decisions
  (maybe a BLOCK should be PARTIAL, or vice versa).
- The goal is a Student model that will NEVER see ground truth at inference time.

## Output Requirements

For each pattern in the Profile (both core_patterns and additional_patterns), produce:
- decision: TRANSFER | PARTIAL | BLOCK
- rationale: 2-3 sentences explaining why (NO ground truth references)
- transferred_insight: What Books-domain preference this implies (null if BLOCK)
- confidence: 0.0-1.0

Then produce Top-10 book recommendations from the candidates:
- Use ONLY TRANSFER and PARTIAL patterns (BLOCK patterns must not drive any recommendation)
- Each recommendation: rank, item_id (parent_asin), title, score (0.0-1.0), applied_patterns, reasoning
- "applied_patterns" lists which patterns support this rec (must not include BLOCK patterns)
- "reasoning": 2-3 sentences (NO ground truth references)

## STRICT Recommendation Constraints (validation will reject violations)

- You MUST select Top-10 from the 50 candidates listed in the user message.
- "item_id" MUST be exactly the parent_asin shown after "item_id:" for the candidate.
  Do NOT use the candidate index (e.g. "C3"). Do NOT invent or guess item_ids.
- "title" MUST exactly match the title shown in the candidate list for that item_id.
- All 10 item_ids in recommendations MUST be distinct (no duplicates).
- "rank" must be in 1..10. "score" must be in [0.0, 1.0].

## Output Schema (strict JSON)

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
    {
      "rank": <1-10>,
      "item_id": "<parent_asin>",
      "title": "<book title>",
      "score": <float 0.0-1.0>,
      "applied_patterns": ["<pattern_name>", ...],
      "reasoning": "<2-3 sentences>"
    }
  ],
  "blocked_patterns_summary": "<brief note>",
  "overall_strategy": "<2-3 sentences>"
}

Output ONLY the JSON object. No prose, no markdown fences.

## Few-Shot Example 1 — TRANSFER-heavy case

Input (abbreviated):
Profile: User prefers complex narratives, slow pacing, philosophical themes; loyal to Christopher Nolan; loves IMAX cinematography.
Candidates include "Cloud Atlas" by David Mitchell.
GROUND_TRUTH_HINT: item_id=B002, title="Cloud Atlas"

Output:
{
  "transfer_decisions": {
    "genre_preference": {"decision": "PARTIAL", "rationale": "User enjoys thought-provoking sci-fi films; this taste partially transfers to speculative fiction novels but book tropes differ from film tropes.", "transferred_insight": "Prefer literary speculative fiction and philosophical sci-fi novels", "confidence": 0.75},
    "narrative_complexity": {"decision": "TRANSFER", "rationale": "Preference for multi-layered, non-linear storytelling is medium-agnostic and directly applies to books with complex structures.", "transferred_insight": "Prefer novels with multiple timelines, nested narratives, unreliable narrators", "confidence": 0.90},
    "pacing_preference": {"decision": "TRANSFER", "rationale": "Slow-burn preference transfers directly to character-driven literary novels.", "transferred_insight": "Prefer slow-burn, character-driven literary novels", "confidence": 0.85},
    "quality_sensitivity": {"decision": "PARTIAL", "rationale": "Quality sensitivity to direction/acting does not apply to books, but overall rating sensitivity does. Use average_rating as proxy.", "transferred_insight": "Prioritize highly-rated books over obscure titles", "confidence": 0.70},
    "brand_loyalty": {"decision": "BLOCK", "rationale": "Nolan is a film director; there is no direct author equivalent and recommending based on directors would cause negative transfer.", "transferred_insight": null, "confidence": 0.95},
    "sensory_preference": {"decision": "BLOCK", "rationale": "IMAX cinematography is film-specific. Books do not provide visual spectacle, so this pattern does not apply.", "transferred_insight": null, "confidence": 0.95},
    "emotional_resonance": {"decision": "TRANSFER", "rationale": "User values content that 'stays with them' and provokes deep feelings. This pattern is medium-agnostic and directly applies to literary fiction with emotional depth.", "transferred_insight": "Prefer emotionally resonant literary fiction with lasting impact", "confidence": 0.85}
  },
  "recommendations": [
    {"rank": 1, "item_id": "B002", "title": "Cloud Atlas", "score": 0.92, "applied_patterns": ["narrative_complexity", "pacing_preference", "quality_sensitivity", "emotional_resonance"], "reasoning": "Six nested timelines and philosophical themes match the user's taste for complex, multi-layered storytelling. Slow, contemplative pacing and emotional depth align with their preferences."}
  ],
  "blocked_patterns_summary": "brand_loyalty (Nolan as director) and sensory_preference (IMAX) are film-specific and were blocked to avoid negative transfer.",
  "overall_strategy": "Leveraged the user's transferable preferences (complex narratives, slow pacing, quality sensitivity) while blocking film-specific signals (director loyalty, visual spectacle)."
}

## Few-Shot Example 2 — BLOCK-heavy case

Input (abbreviated):
Profile: Fast-paced action fan; Jason Statham loyalty; loves action choreography and explosions.
Candidates: mostly novels, some bios.
GROUND_TRUTH_HINT: item_id=B045, title="Thriller: Short Stories by Lee Child"

Output:
{
  "transfer_decisions": {
    "genre_preference": {"decision": "PARTIAL", "rationale": "User's action-film preference partially transfers to thriller and action novels, but the visual/explosive aspect does not exist in books. Focus on high-tension plot genres.", "transferred_insight": "Prefer thriller, crime, and action-oriented fiction", "confidence": 0.70},
    "narrative_complexity": {"decision": "TRANSFER", "rationale": "Preference for simple linear narratives applies directly. Recommend straightforward plots, avoid literary experiments.", "transferred_insight": "Prefer linear, plot-driven narratives over complex structures", "confidence": 0.80},
    "pacing_preference": {"decision": "TRANSFER", "rationale": "Fast-paced preference transfers directly to page-turner thrillers and action novels.", "transferred_insight": "Prefer fast-paced page-turners with constant tension", "confidence": 0.90},
    "quality_sensitivity": {"decision": "BLOCK", "rationale": "No strong quality sensitivity evidence in profile; book rating not a strong signal here.", "transferred_insight": null, "confidence": 0.60},
    "brand_loyalty": {"decision": "BLOCK", "rationale": "Jason Statham is an actor, not an author. Recommending Statham biographies would exploit a superficial name match and represent negative transfer from acting loyalty.", "transferred_insight": null, "confidence": 0.95},
    "sensory_preference": {"decision": "BLOCK", "rationale": "Action choreography and explosions do not exist in books. This pattern is film-specific.", "transferred_insight": null, "confidence": 0.95},
    "emotional_resonance": {"decision": "BLOCK", "rationale": "User shows weak emotional engagement signals (focus on action/spectacle). Confidence too low to drive recommendations.", "transferred_insight": null, "confidence": 0.40}
  },
  "recommendations": [
    {"rank": 1, "item_id": "B045", "title": "Thriller: Short Stories by Lee Child", "score": 0.88, "applied_patterns": ["genre_preference", "narrative_complexity", "pacing_preference"], "reasoning": "Thriller genre matches the user's action/tension preference. Linear, plot-driven stories align with preference for simple narratives. Short stories format supports fast-paced consumption."}
  ],
  "blocked_patterns_summary": "Actor loyalty (Statham) and film-specific sensory preferences were blocked. Quality_sensitivity also blocked due to weak evidence.",
  "overall_strategy": "Focused on transferable plot qualities while blocking actor-based and visual-spectacle signals that would drive negative transfer."
}

## Few-Shot Example 3 — PARTIAL-mixed case

Input (abbreviated):
Profile: Mixed tastes; drama preferred, rom-com disliked; moderate complexity; no strong brand loyalty.
GROUND_TRUTH_HINT: item_id=B078, title="Little Fires Everywhere"

Output:
{
  "transfer_decisions": {
    "genre_preference": {"decision": "PARTIAL", "rationale": "Drama preference transfers well to literary and family-drama novels; dislike of rom-com translates to avoiding romance genre books.", "transferred_insight": "Prefer literary and family-drama novels; avoid romance-dominant books", "confidence": 0.75},
    "narrative_complexity": {"decision": "PARTIAL", "rationale": "Moderate complexity preference suggests neither overly literary nor purely formulaic. Recommend accessible but well-crafted books.", "transferred_insight": "Prefer accessible yet well-crafted narratives", "confidence": 0.60},
    "pacing_preference": {"decision": "PARTIAL", "rationale": "No strong pacing signal; defaults to moderately-paced narratives.", "transferred_insight": "No strong pacing constraint", "confidence": 0.40},
    "quality_sensitivity": {"decision": "PARTIAL", "rationale": "Moderate quality sensitivity applies; use average_rating as a soft signal.", "transferred_insight": "Moderate rating preference", "confidence": 0.55},
    "brand_loyalty": {"decision": "BLOCK", "rationale": "No clear creator loyalty pattern evident. Confidence too low to drive recommendations.", "transferred_insight": null, "confidence": 0.30},
    "sensory_preference": {"decision": "BLOCK", "rationale": "Sensory preferences for film media do not apply to books.", "transferred_insight": null, "confidence": 0.90},
    "emotional_resonance": {"decision": "PARTIAL", "rationale": "User responds to drama with moderate emotional engagement. Recommend books with emotional depth but not overly heavy.", "transferred_insight": "Moderate emotional resonance — family/relationship drama with depth", "confidence": 0.65}
  },
  "recommendations": [
    {"rank": 1, "item_id": "B078", "title": "Little Fires Everywhere", "score": 0.80, "applied_patterns": ["genre_preference", "narrative_complexity", "quality_sensitivity", "emotional_resonance"], "reasoning": "Family-drama novel matches the user's drama preference while avoiding romance-dominant content. Accessible literary style fits moderate complexity. Emotional depth aligns with the user's drama appreciation."}
  ],
  "blocked_patterns_summary": "brand_loyalty blocked due to weak signal. sensory_preference blocked as medium-specific.",
  "overall_strategy": "Applied PARTIAL decisions across most patterns to avoid overfitting to weak signals. Relied on genre preference polarity as the strongest guide."
}

END OF SYSTEM PROMPT.
"""


# ========== 후보 생성 ==========

def format_candidate(item_row: dict, idx: int) -> str:
    """후보 아이템 한 개를 프롬프트 문자열로 변환."""
    title = str(item_row.get("title", "")).strip() or "(unknown)"
    author = str(item_row.get("author_name", "")).strip() or "(unknown)"
    cats = item_row.get("categories", [])
    if isinstance(cats, (list, np.ndarray)):
        cats_str = " > ".join([str(c) for c in cats[:3]])
    else:
        cats_str = str(cats)
    avg_rating = item_row.get("average_rating", "N/A")
    synopsis = str(item_row.get("features_text", "")).strip()
    if synopsis:
        words = synopsis.split()[:40]
        synopsis = " ".join(words)
        if len(synopsis) > 300:
            synopsis = synopsis[:300]
    else:
        synopsis = "(no synopsis available)"

    return (
        f"[C{idx}] item_id: {item_row.get('parent_asin', '')}\n"
        f"      title: {title}\n"
        f"      author: {author}\n"
        f"      categories: {cats_str}\n"
        f"      average_rating: {avg_rating}\n"
        f"      synopsis: {synopsis}"
    )


def build_user_message(
    profiler_output: dict,
    candidates: list[dict],
    gt_item_id: str,
    gt_title: str,
) -> str:
    profile_json = json.dumps(profiler_output, ensure_ascii=False, indent=2)
    cand_lines = [format_candidate(c, i + 1) for i, c in enumerate(candidates)]
    allowed_ids = [str(c.get("parent_asin", "")).strip() for c in candidates]
    allowed_id_block = "\n".join(
        f"  - {cid}: {str(c.get('title',''))[:80]}"
        for cid, c in zip(allowed_ids, candidates)
    )
    return (
        "=== USER PROFILE ===\n"
        f"{profile_json}\n\n"
        "=== CANDIDATES (50 Books) ===\n\n"
        + "\n\n".join(cand_lines)
        + "\n\n"
        "=== GROUND TRUTH HINT (for training data calibration only) ===\n"
        f"item_id: {gt_item_id}\n"
        f"title: {gt_title}\n\n"
        "Reminder: Do NOT reference the ground truth in your output. Reason naturally based on\n"
        "the Profile; the ground truth is used only to verify your Top-10 quality.\n\n"
        "=== ALLOWED_ITEM_IDS (you MUST pick Top-10 from this exact list of 50) ===\n"
        f"{allowed_id_block}\n\n"
        "Self-check BEFORE outputting:\n"
        "  (1) Every recommendation.item_id appears verbatim in the ALLOWED_ITEM_IDS list above.\n"
        "  (2) All 10 item_ids are distinct.\n"
        "  (3) Each recommendation.title matches the title shown for that item_id above.\n"
        "If any check fails, FIX YOUR OUTPUT before returning. Do NOT invent item_ids.\n\n"
        "=== INSTRUCTION ===\n\n"
        "Produce transfer_decisions for all patterns in the Profile and recommend Top-10 books.\n"
        "Output valid JSON following the schema exactly."
    )


# ========== 출력 검증 ==========

@dataclass
class TeacherValidation:
    is_valid: bool
    missing_patterns: list[str] = field(default_factory=list)
    invalid_fields: list[str] = field(default_factory=list)
    block_leakage: list[str] = field(default_factory=list)
    out_of_candidate: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    title_mismatch: list[str] = field(default_factory=list)
    rank_out_of_range: list[int] = field(default_factory=list)
    score_out_of_range: list[float] = field(default_factory=list)
    gt_in_top10: bool = False
    gt_leaked_in_text: bool = False
    rec_count: int = 0


def validate_teacher_output(
    data: dict[str, Any],
    expected_patterns: list[str],
    gt_item_id: str,
    gt_title: str,
    candidate_ids: set[str],
    candidate_title_map: dict[str, str],
) -> TeacherValidation:
    """Teacher 출력 검증 (강화판):
    schema + BLOCK leakage + GT Top-10 + GT 텍스트 누출
    + candidate membership + duplicate + title mismatch + rank/score range.
    """
    result = TeacherValidation(is_valid=True)

    td = data.get("transfer_decisions", {})
    block_patterns = set()
    for pname in expected_patterns:
        if pname not in td:
            result.missing_patterns.append(pname)
            result.is_valid = False
            continue
        decision = td[pname].get("decision")
        if decision not in VALID_DECISIONS:
            result.invalid_fields.append(f"{pname}.decision={decision}")
            result.is_valid = False
        if decision == "BLOCK":
            block_patterns.add(pname)

    recs = data.get("recommendations", [])
    result.rec_count = len(recs)
    if result.rec_count != N_RECOMMENDATIONS:
        result.invalid_fields.append(f"recommendations count={result.rec_count}")
        result.is_valid = False

    seen_ids = []
    rec_item_ids = set()
    for rec in recs:
        iid = str(rec.get("item_id", "")).strip()
        rec_item_ids.add(iid)
        seen_ids.append(iid)

        # [신규] candidate membership
        if iid and iid not in candidate_ids:
            result.out_of_candidate.append(iid)
            result.is_valid = False

        # [신규] title mismatch
        given_title = str(rec.get("title", "")).strip()
        if iid in candidate_title_map and given_title:
            actual = candidate_title_map[iid].strip().lower()[:40]
            given = given_title.lower()[:40]
            if actual and given and actual != given:
                result.title_mismatch.append(f"{iid}: '{given}' != '{actual}'")
                result.is_valid = False

        # [신규] rank/score range
        rank = rec.get("rank")
        if rank is not None and not (1 <= rank <= N_RECOMMENDATIONS):
            result.rank_out_of_range.append(rank)
            result.is_valid = False
        score = rec.get("score")
        if score is not None:
            try:
                if not (0.0 <= float(score) <= 1.0):
                    result.score_out_of_range.append(score)
                    result.is_valid = False
            except (TypeError, ValueError):
                result.score_out_of_range.append(score)
                result.is_valid = False

        # BLOCK leakage (기존)
        applied = set(rec.get("applied_patterns", []))
        leak = applied & block_patterns
        if leak:
            result.block_leakage.append(f"rank {rec.get('rank')}: {leak}")
            result.is_valid = False

    # [신규] duplicate detection
    non_empty = [x for x in seen_ids if x]
    dup_set = {x for x in non_empty if non_empty.count(x) > 1}
    if dup_set:
        result.duplicates = sorted(dup_set)
        result.is_valid = False

    result.gt_in_top10 = gt_item_id in rec_item_ids

    full_text_fields = []
    for pname, pd_ in td.items():
        full_text_fields.append(str(pd_.get("rationale", "")))
    for rec in recs:
        full_text_fields.append(str(rec.get("reasoning", "")))
    full_text = " ".join(full_text_fields).lower()
    gt_title_lower = gt_title.lower()
    if gt_title_lower and len(gt_title_lower) > 5 and gt_title_lower in full_text:
        result.gt_leaked_in_text = True

    return result


# ========== 후보 샘플링 ==========

def sample_candidates(
    user_id: str,
    gt_item_id: str,
    books_meta_df: pd.DataFrame,
    user_books_reviews: pd.DataFrame,
    n_candidates: int,
    rng: np.random.Generator,
) -> list[dict]:
    """GT 1개 + Negative (n-1)개 = n개 후보 구성. 순서는 shuffle."""
    user_purchased = set(user_books_reviews["parent_asin"].unique())

    gt_row = books_meta_df[books_meta_df["parent_asin"] == gt_item_id]
    if gt_row.empty:
        raise ValueError(f"[{user_id}] GT item {gt_item_id} not in books_meta")
    gt_dict = gt_row.iloc[0].to_dict()

    available = books_meta_df[~books_meta_df["parent_asin"].isin(user_purchased)]
    neg_sample = available.sample(n=n_candidates - 1, random_state=rng.integers(0, 2**31))
    neg_dicts = neg_sample.to_dict(orient="records")

    candidates = [gt_dict] + neg_dicts
    rng.shuffle(candidates)
    return candidates


# ========== GT 결정 (rating≥4 중 가장 최근) ==========

def pick_gt(user_books_reviews: pd.DataFrame) -> dict | None:
    pos = user_books_reviews[user_books_reviews["rating"] >= 4.0]
    if pos.empty:
        return None
    latest = pos.sort_values("timestamp", ascending=False).iloc[0]
    return {"parent_asin": latest["parent_asin"], "rating": latest["rating"]}


# ========== API 호출 ==========

def call_teacher_api(
    client,
    user_id: str,
    user_message: str,
    expected_patterns: list[str],
    gt_item_id: str,
    gt_title: str,
    candidate_ids: set[str],
    candidate_title_map: dict[str, str],
    max_retries: int = 3,
) -> tuple[dict | None, dict, TeacherValidation | None]:
    usage = {"input_tokens": 0, "output_tokens": 0, "attempts": 0}
    last_val = None

    for attempt in range(max_retries):
        usage["attempts"] += 1
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
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
            data = json.loads(content)

            val = validate_teacher_output(
                data, expected_patterns, gt_item_id, gt_title,
                candidate_ids=candidate_ids,
                candidate_title_map=candidate_title_map,
            )
            last_val = val
            if val.is_valid and not val.gt_leaked_in_text:
                return data, usage, val

            logging.warning(
                f"[{user_id}] Attempt {attempt+1}: valid={val.is_valid} "
                f"gt_top10={val.gt_in_top10} gt_leaked={val.gt_leaked_in_text} "
                f"missing={val.missing_patterns[:3]} leakage={val.block_leakage[:2]} "
                f"out_of_cand={len(val.out_of_candidate)} dup={len(val.duplicates)} "
                f"title_mm={len(val.title_mismatch)}"
            )
        except json.JSONDecodeError as e:
            logging.warning(f"[{user_id}] Attempt {attempt+1} JSON error: {e}")
        except Exception as e:
            logging.warning(f"[{user_id}] Attempt {attempt+1} API error: {e}")
            time.sleep(2 ** attempt)

    return None, usage, last_val


# ========== 학습 데이터 변환 ==========

def to_sft_record(
    profiler_output: dict,
    candidates: list[dict],
    teacher_output: dict,
) -> dict:
    """학습용 SFT 레코드 생성. GT hint 제거된 user_message 사용."""
    profile_json = json.dumps(profiler_output, ensure_ascii=False, indent=2)
    cand_lines = [format_candidate(c, i + 1) for i, c in enumerate(candidates)]
    user_msg_training = (
        "=== USER PROFILE ===\n"
        f"{profile_json}\n\n"
        "=== CANDIDATES (50 Books) ===\n\n"
        + "\n\n".join(cand_lines)
        + "\n\n"
        "=== INSTRUCTION ===\n\n"
        "Produce transfer_decisions for all patterns in the Profile and recommend Top-10 books.\n"
        "Output valid JSON following the schema exactly."
    )

    # System prompt also needs GT-related lines removed for student training
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

    return {
        "messages": [
            {"role": "system", "content": system_training},
            {"role": "user", "content": user_msg_training},
            {"role": "assistant", "content": json.dumps(teacher_output, ensure_ascii=False)},
        ]
    }


# ========== Main Loop ==========

def run(
    profiler_dir: Path,
    users_path: Path,
    books_reviews_path: Path,
    books_meta_path: Path,
    output_dir: Path,
    training_data_path: Path,
    n_candidates: int,
    dry_run: bool = False,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    training_data_path.parent.mkdir(parents=True, exist_ok=True)

    logging.info("Loading data...")
    users_df = pd.read_parquet(users_path)
    books_reviews = pd.read_parquet(books_reviews_path)
    books_meta = pd.read_parquet(books_meta_path)
    logging.info(
        f"users={len(users_df)}, books_reviews={len(books_reviews):,}, books_meta={len(books_meta):,}"
    )

    rng = np.random.default_rng(SEED)

    client = None
    if not dry_run:
        try:
            from openai import OpenAI
            client = OpenAI(timeout=60.0, max_retries=2)
        except ImportError:
            raise SystemExit("Install openai: pip install openai")

    total_usage = {
        "input_tokens": 0, "output_tokens": 0,
        "success": 0, "failure": 0, "gt_in_top10": 0, "skipped": 0,
    }
    start = time.time()

    training_fp = None if dry_run else training_data_path.open("a", encoding="utf-8")

    try:
        for idx, user_row in enumerate(users_df.itertuples(index=False)):
            user_id = getattr(user_row, "user_id")

            profiler_path = profiler_dir / f"user_{user_id}.json"
            if not profiler_path.exists():
                logging.debug(f"[{user_id}] skip (no profiler output)")
                total_usage["skipped"] += 1
                continue

            teacher_path = output_dir / f"user_{user_id}.json"
            if teacher_path.exists() and not dry_run:
                logging.debug(f"[{user_id}] skip (already done)")
                continue

            profiler_output = json.loads(profiler_path.read_text())

            user_books = books_reviews[books_reviews["user_id"] == user_id]
            gt_info = pick_gt(user_books)
            if gt_info is None:
                logging.warning(f"[{user_id}] skip (no rating>=4 in target)")
                total_usage["skipped"] += 1
                continue

            gt_input_books = user_books[user_books["parent_asin"] != gt_info["parent_asin"]]
            try:
                candidates = sample_candidates(
                    user_id=user_id,
                    gt_item_id=gt_info["parent_asin"],
                    books_meta_df=books_meta,
                    user_books_reviews=user_books,
                    n_candidates=n_candidates,
                    rng=rng,
                )
            except ValueError as e:
                logging.warning(f"[{user_id}] skip: {e}")
                total_usage["skipped"] += 1
                continue

            gt_title_row = books_meta[books_meta["parent_asin"] == gt_info["parent_asin"]]
            gt_title = str(gt_title_row.iloc[0]["title"]) if not gt_title_row.empty else ""

            # 후보 ID·title 맵 (검증용)
            candidate_ids = {str(c.get("parent_asin", "")).strip() for c in candidates}
            candidate_ids.discard("")
            candidate_title_map = {
                str(c.get("parent_asin", "")).strip(): str(c.get("title", "")).strip()
                for c in candidates
                if str(c.get("parent_asin", "")).strip()
            }

            user_message = build_user_message(
                profiler_output=profiler_output,
                candidates=candidates,
                gt_item_id=gt_info["parent_asin"],
                gt_title=gt_title,
            )

            expected_patterns = list(profiler_output.get("core_patterns", {}).keys())
            for add_p in profiler_output.get("additional_patterns", []):
                name = add_p.get("name")
                if name:
                    expected_patterns.append(name)

            if dry_run:
                print("=" * 60)
                print(f"[DRY RUN] user_id={user_id}")
                print(f"  profiler patterns: {expected_patterns}")
                print(f"  GT: {gt_info['parent_asin']} ('{gt_title[:50]}')")
                print(f"  candidates: {len(candidates)}")
                print(f"  message preview (first 1500 chars):")
                print("-" * 60)
                print(user_message[:1500])
                print("..." if len(user_message) > 1500 else "")
                if idx >= 1:
                    print("\n(dry-run: showing first 2 users only)")
                    break
                continue

            output, usage, val = call_teacher_api(
                client=client,
                user_id=user_id,
                user_message=user_message,
                expected_patterns=expected_patterns,
                gt_item_id=gt_info["parent_asin"],
                gt_title=gt_title,
                candidate_ids=candidate_ids,
                candidate_title_map=candidate_title_map,
            )
            total_usage["input_tokens"] += usage["input_tokens"]
            total_usage["output_tokens"] += usage["output_tokens"]

            if output is not None and val is not None and val.is_valid and not val.gt_leaked_in_text:
                teacher_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
                if val.gt_in_top10:
                    total_usage["gt_in_top10"] += 1
                    sft_record = to_sft_record(profiler_output, candidates, output)
                    training_fp.write(json.dumps(sft_record, ensure_ascii=False) + "\n")
                    total_usage["success"] += 1
                else:
                    logging.info(f"[{user_id}] valid but GT not in Top-10 -> excluded from training")
                    total_usage["failure"] += 1
            else:
                total_usage["failure"] += 1

            if (idx + 1) % 25 == 0:
                elapsed = time.time() - start
                cost = (
                    total_usage["input_tokens"] / 1_000_000 * PRICE_INPUT_PER_1M
                    + total_usage["output_tokens"] / 1_000_000 * PRICE_OUTPUT_PER_1M
                )
                logging.info(
                    f"Progress {idx+1}/{len(users_df)} | "
                    f"success={total_usage['success']} gt_top10={total_usage['gt_in_top10']} "
                    f"fail={total_usage['failure']} skip={total_usage['skipped']} | "
                    f"cost=${cost:.3f} | elapsed={elapsed:.0f}s"
                )
    finally:
        if training_fp is not None:
            training_fp.close()

    cost = (
        total_usage["input_tokens"] / 1_000_000 * PRICE_INPUT_PER_1M
        + total_usage["output_tokens"] / 1_000_000 * PRICE_OUTPUT_PER_1M
    )
    logging.info(
        f"DONE | success={total_usage['success']} gt_top10={total_usage['gt_in_top10']} "
        f"fail={total_usage['failure']} skip={total_usage['skipped']} | total_cost=${cost:.3f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiler-dir", type=Path, required=True)
    parser.add_argument("--users", type=Path, required=True)
    parser.add_argument("--books-reviews", type=Path, required=True)
    parser.add_argument("--books-meta", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("teacher_outputs"))
    parser.add_argument("--training-data", type=Path, default=Path("data/train.jsonl"))
    parser.add_argument("--n-candidates", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    run(
        profiler_dir=args.profiler_dir,
        users_path=args.users,
        books_reviews_path=args.books_reviews,
        books_meta_path=args.books_meta,
        output_dir=args.output,
        training_data_path=args.training_data,
        n_candidates=args.n_candidates,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
