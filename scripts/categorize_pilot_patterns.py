"""Step 3 — Pilot 391 canonical 패턴을 4 카테고리로 자동 분류.

카테고리:
  1. 매체-종속 (medium_specific): Movies-only 키워드 보유
  2. 메타 정보 (meta): 패턴이 아닌 표현 (recommendation, rating 자체 등)
  3. Cross-Domain 적합 (cdr_relevant): 사전 정의 7개와 sim ≥ 0.5
  4. 표층 신호 (surface): 위 3개에 안 들어가는 표층 감정·장르

산출:
  data/pilot_pattern_categories.csv
  data/pilot_categories_summary.png

사용법:
  python scripts/categorize_pilot_patterns.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

plt.rcParams["font.family"] = ["Apple SD Gothic Neo", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ============================================================
# 카테고리 분류 키워드
# ============================================================

# Movies-only 키워드 (매체-종속 식별)
MEDIUM_SPECIFIC_KEYWORDS = [
    # 영상 관련
    "cinematograph", "visual", "imax", "screen", "frame", "shot", "camera",
    "scene", "season", "episode", "episodic",
    "tv_show", "tv_series", "film", "movie", "movies", "filmmaking",
    # 음향
    "soundtrack", "score", "audio", "sound_design", "music_score",
    # 배우·연기
    "acting", "actor", "actress", "performance", "performances",
    "director", "directorial", "cast",
    # 영화 특화 장르 표현
    "musical", "documentar", "remake", "sequel", "franchise",
    "binge", "binge_watching", "rewatch", "re_watch", "re_watchability",
    # 영상 특화 액션
    "action_choreograph", "fight_scene",
    # DVD·Blu-ray
    "dvd", "bluray", "blu_ray",
    # 자막
    "subtitle",
]

# 메타 정보 (패턴이 아닌 표현)
META_KEYWORDS = [
    "recommendation", "high_recommend", "low_recommend",
    "value_for_money", "purchase_satisfaction", "consumer",
    "rating", "high_rating", "low_rating", "average_rating",
    "consistency_in_rating", "consistent_rating",
    "review_style", "writing_style_review", "text_length",
    "overall_satisfaction", "user_engagement", "reception",
]

CDR_THRESHOLD = 0.5  # sim ≥ 0.5 → Cross-Domain 적합


def categorize_pattern(name: str, description: str, max_sim_to_predef: float) -> str:
    """우선순위: medium-specific > meta > cdr_relevant > surface."""
    text = (name + " " + description).lower()

    # 1. 매체-종속 검사 (가장 우선)
    for kw in MEDIUM_SPECIFIC_KEYWORDS:
        if kw in text:
            return "medium_specific"

    # 2. 메타 정보 검사
    for kw in META_KEYWORDS:
        if kw in text:
            return "meta"

    # 3. Cross-Domain 적합 검사
    if max_sim_to_predef >= CDR_THRESHOLD:
        return "cdr_relevant"

    # 4. 그 외 표층 신호
    return "surface"


def main() -> None:
    print("[Loading]")
    canonical_df = pd.read_parquet(DATA / "pilot_patterns_canonical.parquet")
    matrix_df = pd.read_csv(DATA / "pilot_to_predefined_matrix.csv", index_col=0)
    print(f"  canonical_df: {len(canonical_df):,} rows")
    print(f"  similarity matrix: {matrix_df.shape}")

    # canonical 패턴별로 max similarity 계산
    pilot_df = (
        canonical_df.groupby("canonical_name")
        .agg(
            n_users=("user_id", "nunique"),
            sample_desc=("description", lambda s: s.iloc[0]),
            avg_conf=("confidence", "mean"),
            polarity_neg=("polarity", lambda s: int((s == "negative").sum())),
            polarity_pos=("polarity", lambda s: int((s == "positive").sum())),
        )
        .reset_index()
    )
    print(f"  unique pilot canonical: {len(pilot_df)}")

    # max similarity to any predefined
    max_sims = matrix_df.max(axis=0)
    best_match = matrix_df.idxmax(axis=0)

    pilot_df["max_sim_to_predef"] = pilot_df["canonical_name"].map(max_sims)
    pilot_df["best_predef_match"] = pilot_df["canonical_name"].map(best_match)

    # 카테고리 자동 분류
    pilot_df["category"] = pilot_df.apply(
        lambda r: categorize_pattern(
            r["canonical_name"],
            r["sample_desc"],
            r["max_sim_to_predef"],
        ),
        axis=1,
    )

    pilot_df.to_csv(DATA / "pilot_pattern_categories.csv", index=False)
    print(f"  saved: pilot_pattern_categories.csv ({len(pilot_df)} rows)")

    # ============================================================
    # 카테고리별 통계
    # ============================================================
    print(f"\n{'='*72}")
    print(f"4 카테고리 분류 결과")
    print(f"{'='*72}")

    cat_stats = (
        pilot_df.groupby("category")
        .agg(
            n_patterns=("canonical_name", "size"),
            n_users_total=("n_users", "sum"),
            avg_sim_to_predef=("max_sim_to_predef", "mean"),
        )
        .reset_index()
    )

    total_patterns = len(pilot_df)
    cat_stats["pct_patterns"] = (cat_stats["n_patterns"] / total_patterns * 100).round(1)

    cat_order = ["cdr_relevant", "surface", "medium_specific", "meta"]
    cat_stats["sort_key"] = cat_stats["category"].map({c: i for i, c in enumerate(cat_order)})
    cat_stats = cat_stats.sort_values("sort_key").drop("sort_key", axis=1)

    print(cat_stats.to_string(index=False))

    # ============================================================
    # 카테고리별 대표 패턴
    # ============================================================
    print(f"\n{'='*72}")
    print(f"카테고리별 대표 패턴 Top-5 (사용자 수 기준)")
    print(f"{'='*72}")
    for cat in cat_order:
        sub = pilot_df[pilot_df["category"] == cat].sort_values("n_users", ascending=False).head(5)
        if len(sub) == 0:
            continue
        print(f"\n  [{cat}]")
        for _, r in sub.iterrows():
            print(
                f"    • {r['canonical_name']:40s} "
                f"users={r['n_users']:3d}  sim={r['max_sim_to_predef']:.3f}  "
                f"→ {r['best_predef_match']}"
            )

    # ============================================================
    # H2 검증: 자유 추출의 한계 (≥60% 비-CDR-적합)
    # ============================================================
    n_cdr = int((pilot_df["category"] == "cdr_relevant").sum())
    n_surface = int((pilot_df["category"] == "surface").sum())
    n_medium = int((pilot_df["category"] == "medium_specific").sum())
    n_meta = int((pilot_df["category"] == "meta").sum())
    pct_non_cdr = (n_surface + n_medium + n_meta) / total_patterns * 100

    print(f"\n{'='*72}")
    print(f"가설 H2 검증: 자유 추출의 한계 (≥60% 비-CDR-적합)")
    print(f"{'='*72}")
    print(f"  CDR 적합 (사전 정의 7개와 매칭): {n_cdr}/{total_patterns} ({n_cdr/total_patterns*100:.1f}%)")
    print(f"  표층 신호: {n_surface}/{total_patterns} ({n_surface/total_patterns*100:.1f}%)")
    print(f"  매체-종속: {n_medium}/{total_patterns} ({n_medium/total_patterns*100:.1f}%)")
    print(f"  메타 정보: {n_meta}/{total_patterns} ({n_meta/total_patterns*100:.1f}%)")
    print(f"  비-CDR-적합 합계: {pct_non_cdr:.1f}% {'✅ H2 통과' if pct_non_cdr >= 60 else '⚠️ H2 미달'}")

    # ============================================================
    # 시각화: 카테고리별 막대 그래프
    # ============================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # (a) 패턴 수 분포
    cat_labels_kr = {
        "cdr_relevant": "CDR 적합\n(사전 7개 매칭)",
        "surface": "표층 신호",
        "medium_specific": "매체-종속\n(Movies-only)",
        "meta": "메타 정보",
    }
    colors = {
        "cdr_relevant": "#2f9a53",
        "surface": "#6b7cb5",
        "medium_specific": "#e94560",
        "meta": "#f5a623",
    }

    cats = cat_stats["category"].tolist()
    counts = cat_stats["n_patterns"].tolist()
    pcts = cat_stats["pct_patterns"].tolist()
    bar_colors = [colors[c] for c in cats]
    labels = [cat_labels_kr[c] for c in cats]

    bars = axes[0].bar(labels, counts, color=bar_colors, alpha=0.85)
    axes[0].set_ylabel("Canonical 패턴 수")
    axes[0].set_title(
        f"(a) 391개 Pilot 패턴 카테고리 분포\n"
        f"비-CDR-적합 합계: {pct_non_cdr:.1f}%",
        fontsize=11, fontweight="bold",
    )
    for b, c, p in zip(bars, counts, pcts):
        axes[0].text(b.get_x() + b.get_width() / 2, c + 5,
                     f"{c}\n({p:.1f}%)", ha="center", fontsize=9)
    axes[0].grid(alpha=0.3, axis="y")

    # (b) 사용자 커버리지 (총 사용자 수 = patterns × users)
    user_totals = cat_stats["n_users_total"].tolist()
    bars2 = axes[1].bar(labels, user_totals, color=bar_colors, alpha=0.85)
    axes[1].set_ylabel("사용자 수 합계 (각 패턴이 등장한 사용자 수의 합)")
    axes[1].set_title("(b) 카테고리별 사용자 커버리지", fontsize=11, fontweight="bold")
    for b, c in zip(bars2, user_totals):
        axes[1].text(b.get_x() + b.get_width() / 2, c + 5, str(c), ha="center", fontsize=9)
    axes[1].grid(alpha=0.3, axis="y")

    fig.suptitle(
        "Pilot Step 3 · 자유 추출 결과의 4 카테고리 분류 (자기참조 회피)",
        fontsize=12, fontweight="bold", y=1.02,
    )
    fig.tight_layout()
    out = DATA / "pilot_categories_summary.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  saved: {out}")


if __name__ == "__main__":
    main()
