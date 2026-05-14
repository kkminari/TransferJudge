"""Step 2 — 사전 정의 7개 ↔ Pilot 391 canonical 패턴 임베딩 매칭.

자기참조 회피의 핵심 단계: 본 연구가 직접 매칭하지 않고 임베딩 cosine 유사도가 매칭.

산출:
  data/pilot_to_predefined_matching.csv   — 매칭 결과 (사전 정의 패턴 × Top-3 Pilot 매칭)
  data/pilot_to_predefined_matrix.csv     — 7 × N full similarity matrix

사용법:
  python scripts/match_pilot_to_predefined.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3
STRONG_MATCH = 0.7
MEDIUM_MATCH = 0.5
WEAK_MATCH = 0.3


# ============================================================
# 사전 정의 7개 패턴 (prompts/core_patterns_definition.md §1~7 영문 정의 기반)
# ============================================================

PREDEFINED_PATTERNS = {
    "genre_preference": {
        "definition": (
            "The user's preference for specific content genres or categories "
            "such as sci-fi, thriller, romance, biography. Includes both "
            "preferred genres (positive polarity) and disliked genres (negative polarity)."
        ),
        "academic_source": "NCF (He 2017), Amazon Reviews standard",
        "expected_pilot_match": "specific genre names dispersed (sci_fi_interest, humor_appreciation, suspense_intrigue)",
    },
    "narrative_complexity": {
        "definition": (
            "The user's preference for complex versus simple narrative structures, "
            "including multi-layered plots, non-linear timelines, unreliable narrators, "
            "and depth of character development."
        ),
        "academic_source": "LLM4CDR story attributes (WWW 2025), TALLRec attribute (RecSys 2023)",
        "expected_pilot_match": "character_depth, story_engagement, character_driven_narratives",
    },
    "pacing_preference": {
        "definition": (
            "The user's preference for narrative pacing, including fast-paced action "
            "and tension versus slow-burn, character-driven, contemplative storytelling."
        ),
        "academic_source": "TALLRec item attribute, movie/book review analysis standard",
        "expected_pilot_match": "narrative_pacing_issues, mixed_reaction_to_pacing, binge_watching",
    },
    "quality_sensitivity": {
        "definition": (
            "The user's sensitivity to production quality, technical execution, and overall craft. "
            "Includes attention to ratings, professional reviews, acting, direction, "
            "and other indicators of quality and craftsmanship."
        ),
        "academic_source": "Ricci et al. Recommender Systems Handbook (2015), rating sensitivity",
        "expected_pilot_match": "appreciation_for_performances, dislike_for_poor_execution, high_quality_production",
    },
    "brand_loyalty": {
        "definition": (
            "The user's loyalty to specific creators such as directors, actors, authors, "
            "franchises, series, or production brands. Includes both positive (favorite creators) "
            "and negative (avoided creators)."
        ),
        "academic_source": "Oliver (1999) Whence Consumer Loyalty?, marketing standard",
        "expected_pilot_match": "series_loyalty, disappointment_with_adaptations, mixed_feelings_on_remakes",
    },
    "sensory_preference": {
        "definition": (
            "The user's preference for sensory experiences in media, including visual spectacle, "
            "auditory immersion, action choreography, atmospheric mood, cinematography, "
            "and other medium-specific experiential qualities."
        ),
        "academic_source": "Movie medium-specific attribute (TALLRec, BLOCK candidate)",
        "expected_pilot_match": "visual_aesthetic_appreciation, appreciation_for_visual_beauty, cinematography",
    },
    "emotional_resonance": {
        "definition": (
            "The user's emphasis on emotional impact and resonance, "
            "whether the content evokes deep feelings, lasting memory, "
            "and personal meaning beyond mere entertainment."
        ),
        "academic_source": "Pilot Study derivation + affective response in recommendation",
        "expected_pilot_match": "emotional_resonance (direct match), emotional_impact",
    },
}


def main() -> None:
    print("[Loading]")
    canonical_df = pd.read_parquet(DATA / "pilot_patterns_canonical.parquet")
    print(f"  pilot canonical patterns (long-format): {len(canonical_df):,} rows")

    # canonical 패턴별로 description 1개 + 사용자 수 집계
    pilot_df = (
        canonical_df.groupby("canonical_name")
        .agg(
            n_users=("user_id", "nunique"),
            sample_desc=("description", lambda s: s.iloc[0]),
            avg_conf=("confidence", "mean"),
        )
        .reset_index()
        .sort_values("n_users", ascending=False)
    )
    print(f"  unique canonical: {len(pilot_df)}")

    # 임베딩 모델 로드
    print(f"\n[Embedding] {EMBED_MODEL}")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBED_MODEL)

    # 사전 정의 7개 임베딩 (이름 + 정의)
    predef_names = list(PREDEFINED_PATTERNS.keys())
    predef_texts = [
        f"{name.replace('_', ' ')}: {pat['definition']}"
        for name, pat in PREDEFINED_PATTERNS.items()
    ]
    predef_emb = model.encode(predef_texts, normalize_embeddings=True, show_progress_bar=False)

    # Pilot canonical 임베딩 (이름 + 샘플 설명)
    pilot_texts = (
        pilot_df["canonical_name"].str.replace("_", " ") + ": " + pilot_df["sample_desc"]
    ).tolist()
    print(f"  embedding {len(pilot_texts)} pilot patterns ...")
    pilot_emb = model.encode(pilot_texts, normalize_embeddings=True, show_progress_bar=True)

    # 7 × N 코사인 유사도 행렬
    sim_matrix = predef_emb @ pilot_emb.T  # normalize되어 있으므로 내적 = 코사인
    print(f"  similarity matrix: {sim_matrix.shape}")

    # full matrix 저장
    full_df = pd.DataFrame(
        sim_matrix,
        index=predef_names,
        columns=pilot_df["canonical_name"].tolist(),
    )
    full_df.to_csv(DATA / "pilot_to_predefined_matrix.csv")
    print(f"  saved: pilot_to_predefined_matrix.csv (full matrix)")

    # ============================================================
    # Top-K 매칭 추출
    # ============================================================
    rows = []
    for i, predef_name in enumerate(predef_names):
        sims = sim_matrix[i]
        # Top-K
        top_idx = np.argsort(-sims)[:TOP_K]
        for rank, idx in enumerate(top_idx, start=1):
            pilot_name = pilot_df.iloc[idx]["canonical_name"]
            sim = float(sims[idx])
            n_users = int(pilot_df.iloc[idx]["n_users"])
            avg_conf = float(pilot_df.iloc[idx]["avg_conf"])
            sample_desc = pilot_df.iloc[idx]["sample_desc"][:100]

            if sim >= STRONG_MATCH:
                strength = "STRONG"
            elif sim >= MEDIUM_MATCH:
                strength = "MEDIUM"
            elif sim >= WEAK_MATCH:
                strength = "WEAK"
            else:
                strength = "VERY_WEAK"

            rows.append({
                "predefined": predef_name,
                "rank": rank,
                "pilot_canonical": pilot_name,
                "similarity": round(sim, 4),
                "strength": strength,
                "pilot_n_users": n_users,
                "pilot_avg_conf": round(avg_conf, 3),
                "pilot_sample_desc": sample_desc,
            })

    matching_df = pd.DataFrame(rows)
    matching_df.to_csv(DATA / "pilot_to_predefined_matching.csv", index=False)
    print(f"  saved: pilot_to_predefined_matching.csv ({len(matching_df)} rows)")

    # ============================================================
    # 사용자에게 결과 출력
    # ============================================================
    print(f"\n{'='*72}")
    print(f"매칭 결과 (사전 정의 7개 × Top-{TOP_K})")
    print(f"{'='*72}\n")

    summary_rows = []
    for predef_name in predef_names:
        sub = matching_df[matching_df["predefined"] == predef_name]
        top1_sim = sub.iloc[0]["similarity"]
        top1_name = sub.iloc[0]["pilot_canonical"]
        top1_users = sub.iloc[0]["pilot_n_users"]
        top1_strength = sub.iloc[0]["strength"]

        # 강도 마크
        strength_mark = {
            "STRONG": "✅",
            "MEDIUM": "○",
            "WEAK": "△",
            "VERY_WEAK": "✗",
        }.get(top1_strength, "?")

        print(f"  {strength_mark} {predef_name:25s}")
        for _, row in sub.iterrows():
            mark = "  →" if row["rank"] == 1 else "   "
            print(
                f"    {mark} #{row['rank']} {row['pilot_canonical']:40s} "
                f"sim={row['similarity']:.3f} ({row['strength']:9s}) users={row['pilot_n_users']}"
            )
        print()

        summary_rows.append({
            "predefined": predef_name,
            "top1_pilot": top1_name,
            "top1_sim": top1_sim,
            "top1_strength": top1_strength,
            "top1_n_users": top1_users,
        })

    # ============================================================
    # H1 검증: 7개가 변형 형태로 발현 (sim ≥ 0.5)
    # ============================================================
    summary_df = pd.DataFrame(summary_rows)
    print(f"{'='*72}")
    print(f"가설 H1 검증: 사전 정의 7개가 Pilot에서 sim ≥ 0.5로 발현")
    print(f"{'='*72}")
    n_strong = (summary_df["top1_sim"] >= STRONG_MATCH).sum()
    n_medium = ((summary_df["top1_sim"] >= MEDIUM_MATCH) & (summary_df["top1_sim"] < STRONG_MATCH)).sum()
    n_weak = ((summary_df["top1_sim"] >= WEAK_MATCH) & (summary_df["top1_sim"] < MEDIUM_MATCH)).sum()
    n_very_weak = (summary_df["top1_sim"] < WEAK_MATCH).sum()
    n_passed = n_strong + n_medium

    print(f"  STRONG (≥{STRONG_MATCH}): {n_strong}/7")
    print(f"  MEDIUM ({MEDIUM_MATCH}~{STRONG_MATCH}): {n_medium}/7")
    print(f"  WEAK ({WEAK_MATCH}~{MEDIUM_MATCH}): {n_weak}/7")
    print(f"  VERY_WEAK (<{WEAK_MATCH}): {n_very_weak}/7")
    print(f"  → H1 통과 (≥{MEDIUM_MATCH}): {n_passed}/7 ({n_passed/7*100:.0f}%)")

    # H5 검증: emotional_resonance 직접 매칭
    er_top1 = summary_df[summary_df["predefined"] == "emotional_resonance"].iloc[0]
    print(f"\n  H5 검증: emotional_resonance 직접 매칭 sim ≥ 0.9")
    print(f"    → top-1: {er_top1['top1_pilot']} (sim={er_top1['top1_sim']:.3f}) "
          f"{'✅ 통과' if er_top1['top1_sim'] >= 0.9 else '⚠️ 미달'}")


if __name__ == "__main__":
    main()
