"""EDA 추가 검증 분석 (계획서 vs EDA 보고서 GAP 보완).

검증 항목:
  GAP-2: 사용자별 평점 다양성 분포 (Profiler의 negative polarity 추출 가능성)
  GAP-1: Source-Target 카테고리 상관 (CDR 핵심 가정의 데이터 근거)
  GAP-4: GT vs Negative 후보 분포 비교 (평가 공정성)

산출물:
  data/eda_rating_diversity.png
  data/eda_cross_domain_categories.png
  data/eda_gt_vs_negative.png

사용법:
  python scripts/analyze_eda_gaps.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SEED = 42

# 한글 폰트 (mac)
plt.rcParams["font.family"] = ["Apple SD Gothic Neo", "Noto Sans KR", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# 데이터 로딩
# ============================================================

def load_data():
    print("[Loading] parquet files ...")
    users = pd.read_parquet(DATA / "overlapping_users.parquet")
    movies_rev = pd.read_parquet(DATA / "movies_reviews_filtered.parquet")
    books_rev = pd.read_parquet(DATA / "books_reviews_filtered.parquet")
    movies_meta = pd.read_parquet(DATA / "movies_meta_filtered.parquet")
    books_meta = pd.read_parquet(DATA / "books_meta_filtered.parquet")

    user_ids = set(users["user_id"])
    movies_rev = movies_rev[movies_rev["user_id"].isin(user_ids)].copy()
    books_rev = books_rev[books_rev["user_id"].isin(user_ids)].copy()

    print(f"  users={len(users):,} | movies_rev={len(movies_rev):,} | books_rev={len(books_rev):,}")
    print(f"  movies_meta={len(movies_meta):,} | books_meta={len(books_meta):,}")
    return users, movies_rev, books_rev, movies_meta, books_meta


# ============================================================
# GAP-2: 사용자별 평점 다양성
# ============================================================

def analyze_rating_diversity(users: pd.DataFrame, movies_rev: pd.DataFrame) -> dict:
    print("\n[GAP-2] 사용자별 평점 다양성 분석")
    grouped = movies_rev.groupby("user_id")["rating"]

    user_stats = pd.DataFrame({
        "n_reviews": grouped.count(),
        "rating_mean": grouped.mean(),
        "rating_std": grouped.std().fillna(0),
        "has_low_rating_le2": grouped.apply(lambda s: int((s <= 2).any())),
        "has_low_rating_le3": grouped.apply(lambda s: int((s <= 3).any())),
        "frac_le2": grouped.apply(lambda s: float((s <= 2).mean())),
        "frac_le3": grouped.apply(lambda s: float((s <= 3).mean())),
    })

    summary = {
        "n_users": len(user_stats),
        "rating_std_mean": float(user_stats["rating_std"].mean()),
        "rating_std_p25": float(user_stats["rating_std"].quantile(0.25)),
        "rating_std_p75": float(user_stats["rating_std"].quantile(0.75)),
        "pct_users_with_rating_le2": float(user_stats["has_low_rating_le2"].mean()) * 100,
        "pct_users_with_rating_le3": float(user_stats["has_low_rating_le3"].mean()) * 100,
        "frac_le2_mean": float(user_stats["frac_le2"].mean()) * 100,
        "frac_le3_mean": float(user_stats["frac_le3"].mean()) * 100,
    }
    print(f"  사용자 수: {summary['n_users']}")
    print(f"  Source 평점 std 평균: {summary['rating_std_mean']:.2f} (P25 {summary['rating_std_p25']:.2f} - P75 {summary['rating_std_p75']:.2f})")
    print(f"  rating <= 2 보유 사용자 비율: {summary['pct_users_with_rating_le2']:.1f}%")
    print(f"  rating <= 3 보유 사용자 비율: {summary['pct_users_with_rating_le3']:.1f}%")
    print(f"  평균 사용자의 rating <= 2 비중: {summary['frac_le2_mean']:.1f}%")
    print(f"  평균 사용자의 rating <= 3 비중: {summary['frac_le3_mean']:.1f}%")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    axes[0].hist(user_stats["rating_std"], bins=30, color="#4a90d9", edgecolor="white")
    axes[0].axvline(user_stats["rating_std"].mean(), color="red", linestyle="--", label=f"mean={summary['rating_std_mean']:.2f}")
    axes[0].set_title("(a) 사용자별 Source 평점 표준편차")
    axes[0].set_xlabel("rating std (사용자 단위)")
    axes[0].set_ylabel("사용자 수")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    counts = [
        (user_stats["has_low_rating_le2"] == 1).sum(),
        (user_stats["has_low_rating_le3"] == 1).sum(),
        len(user_stats),
    ]
    labels = ["≤2점 1개+", "≤3점 1개+", "전체 사용자"]
    bars = axes[1].bar(labels, counts, color=["#e94560", "#f5a623", "#4a90d9"])
    axes[1].set_title("(b) 비선호 신호 보유 사용자 수")
    axes[1].set_ylabel("사용자 수")
    for b, v in zip(bars, counts):
        pct = v / len(user_stats) * 100
        axes[1].text(b.get_x() + b.get_width() / 2, v + 5, f"{v}\n({pct:.1f}%)", ha="center", fontsize=9)
    axes[1].grid(alpha=0.3, axis="y")

    axes[2].hist(user_stats["frac_le3"] * 100, bins=30, color="#2f9a53", edgecolor="white")
    axes[2].axvline(summary["frac_le3_mean"], color="red", linestyle="--", label=f"mean={summary['frac_le3_mean']:.1f}%")
    axes[2].set_title("(c) 사용자별 ≤3점 비중 분포")
    axes[2].set_xlabel("rating ≤ 3 리뷰의 비중 (%)")
    axes[2].set_ylabel("사용자 수")
    axes[2].legend()
    axes[2].grid(alpha=0.3)

    fig.suptitle("GAP-2 · Source 평점 다양성 (Profiler의 negative polarity 추출 가능성)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    out = DATA / "eda_rating_diversity.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved: {out}")
    return summary


# ============================================================
# GAP-1: Source-Target 카테고리 상관
# ============================================================

def _extract_top_category(cats, exclude=("Books", "Movies & TV", "Prime Video")) -> str:
    """카테고리 배열에서 가장 의미 있는 첫 번째 장르 추출."""
    if cats is None:
        return ""
    if isinstance(cats, np.ndarray):
        cats = cats.tolist()
    if not isinstance(cats, list) or len(cats) == 0:
        return ""
    for c in cats:
        if c and c not in exclude:
            return str(c)
    return ""


def analyze_cross_domain_categories(users, movies_rev, books_rev, movies_meta, books_meta) -> dict:
    print("\n[GAP-1] Source-Target 카테고리 상관 분석")

    movies_meta = movies_meta.copy()
    books_meta = books_meta.copy()
    movies_meta["genre"] = movies_meta["categories"].apply(_extract_top_category)
    books_meta["genre"] = books_meta["categories"].apply(_extract_top_category)

    movies_rev_g = movies_rev.merge(movies_meta[["parent_asin", "genre"]], on="parent_asin", how="left")
    books_rev_g = books_rev.merge(books_meta[["parent_asin", "genre"]], on="parent_asin", how="left")

    movies_rev_g = movies_rev_g[movies_rev_g["genre"].astype(str).str.len() > 0]
    books_rev_g = books_rev_g[books_rev_g["genre"].astype(str).str.len() > 0]

    movies_top = (
        movies_rev_g.groupby(["user_id", "genre"]).size()
        .reset_index(name="n").sort_values(["user_id", "n"], ascending=[True, False])
        .drop_duplicates("user_id", keep="first")
        .rename(columns={"genre": "movies_top_genre"})[["user_id", "movies_top_genre"]]
    )
    books_top = (
        books_rev_g.groupby(["user_id", "genre"]).size()
        .reset_index(name="n").sort_values(["user_id", "n"], ascending=[True, False])
        .drop_duplicates("user_id", keep="first")
        .rename(columns={"genre": "books_top_genre"})[["user_id", "books_top_genre"]]
    )

    pairs = movies_top.merge(books_top, on="user_id", how="inner")
    print(f"  매핑 가능 사용자: {len(pairs):,}/{len(users):,}")

    movies_top_genres = pairs["movies_top_genre"].value_counts().head(10).index.tolist()
    books_top_genres = pairs["books_top_genre"].value_counts().head(10).index.tolist()
    pairs_top = pairs[
        pairs["movies_top_genre"].isin(movies_top_genres)
        & pairs["books_top_genre"].isin(books_top_genres)
    ]

    cross_tab = pd.crosstab(pairs_top["movies_top_genre"], pairs_top["books_top_genre"])
    cross_tab = cross_tab.reindex(index=movies_top_genres, columns=books_top_genres, fill_value=0)
    cross_norm = cross_tab.div(cross_tab.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))

    im0 = axes[0].imshow(cross_tab.values, cmap="Blues", aspect="auto")
    axes[0].set_xticks(range(len(books_top_genres)))
    axes[0].set_xticklabels(books_top_genres, rotation=40, ha="right", fontsize=8)
    axes[0].set_yticks(range(len(movies_top_genres)))
    axes[0].set_yticklabels(movies_top_genres, fontsize=8)
    axes[0].set_title("(a) 사용자 수 (절대값)")
    axes[0].set_xlabel("Books top-genre")
    axes[0].set_ylabel("Movies top-genre")
    for i in range(cross_tab.shape[0]):
        for j in range(cross_tab.shape[1]):
            v = cross_tab.values[i, j]
            if v > 0:
                axes[0].text(j, i, str(v), ha="center", va="center", fontsize=7,
                             color="white" if v > cross_tab.values.max() * 0.5 else "black")
    plt.colorbar(im0, ax=axes[0], shrink=0.8)

    im1 = axes[1].imshow(cross_norm.values, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)
    axes[1].set_xticks(range(len(books_top_genres)))
    axes[1].set_xticklabels(books_top_genres, rotation=40, ha="right", fontsize=8)
    axes[1].set_yticks(range(len(movies_top_genres)))
    axes[1].set_yticklabels(movies_top_genres, fontsize=8)
    axes[1].set_title("(b) 행 정규화 (Movies 장르 → Books 장르 조건부 확률)")
    axes[1].set_xlabel("Books top-genre")
    for i in range(cross_norm.shape[0]):
        for j in range(cross_norm.shape[1]):
            v = cross_norm.values[i, j]
            if v >= 0.05:
                axes[1].text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                             color="white" if v > 0.5 else "black")
    plt.colorbar(im1, ax=axes[1], shrink=0.8)

    fig.suptitle("GAP-1 · Source(Movies) ↔ Target(Books) Top-Genre 매핑", fontsize=12, fontweight="bold")
    fig.tight_layout()
    out = DATA / "eda_cross_domain_categories.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved: {out}")

    diag_match = 0
    overlap_pairs = 0
    for g in movies_top_genres:
        if g in cross_norm.columns:
            overlap_pairs += int(cross_tab.loc[g, g])
            diag_match += 1
    same_name_total = sum(int(cross_tab.loc[g, g]) for g in movies_top_genres if g in cross_tab.columns)

    movies_to_books_top1 = {}
    for g in movies_top_genres:
        if g in cross_tab.index:
            row = cross_tab.loc[g]
            if row.sum() > 0:
                top_book = row.idxmax()
                top_n = int(row.max())
                movies_to_books_top1[g] = (top_book, top_n, int(row.sum()))

    print(f"  매핑된 사용자 (Top10×Top10): {int(cross_tab.values.sum())}")
    print(f"  동일 명칭 직접 매칭 (예: Sci-Fi→Sci-Fi): {same_name_total}")
    print("  Movies 장르별 가장 많이 매핑되는 Books 장르 Top 1:")
    for mg, (bg, n, total) in movies_to_books_top1.items():
        pct = n / total * 100 if total else 0
        print(f"    {mg:30s} → {bg:35s}  ({n}/{total}, {pct:.1f}%)")

    return {
        "n_pairs_total": int(len(pairs)),
        "n_pairs_top10x10": int(cross_tab.values.sum()),
        "same_name_match": int(same_name_total),
        "movies_to_books_top1": movies_to_books_top1,
        "movies_top_genres": movies_top_genres,
        "books_top_genres": books_top_genres,
    }


# ============================================================
# GAP-4: GT vs Negative 분포 비교
# ============================================================

def analyze_gt_vs_negative(users, books_rev, books_meta, n_negatives=49) -> dict:
    print("\n[GAP-4] GT vs Negative 후보 분포 비교")

    pos = books_rev[books_rev["rating"] >= 4].copy()
    pos = pos.sort_values("timestamp", ascending=False).drop_duplicates("user_id", keep="first")
    user_gt = users.merge(pos[["user_id", "parent_asin", "rating"]], on="user_id", how="inner")
    print(f"  GT 확보 사용자: {len(user_gt):,}/{len(users):,}")

    user_purchased = books_rev.groupby("user_id")["parent_asin"].apply(set).to_dict()

    rng = np.random.default_rng(SEED)
    candidate_ids = books_meta["parent_asin"].values

    gt_records = []
    neg_records = []
    for _, row in user_gt.iterrows():
        uid = row["user_id"]
        gt_id = row["parent_asin"]
        gt_records.append(gt_id)

        purchased = user_purchased.get(uid, set())
        attempts = 0
        chosen = []
        while len(chosen) < n_negatives and attempts < n_negatives * 3:
            sample = rng.choice(candidate_ids, size=n_negatives, replace=False)
            for s in sample:
                if s not in purchased and s != gt_id and s not in chosen:
                    chosen.append(s)
                    if len(chosen) >= n_negatives:
                        break
            attempts += 1
        neg_records.extend(chosen[:n_negatives])

    gt_meta = books_meta[books_meta["parent_asin"].isin(gt_records)].copy()
    neg_meta = books_meta[books_meta["parent_asin"].isin(neg_records)].copy()
    gt_meta["genre"] = gt_meta["categories"].apply(_extract_top_category)
    neg_meta["genre"] = neg_meta["categories"].apply(_extract_top_category)
    gt_meta = gt_meta[gt_meta["genre"].astype(str).str.len() > 0]
    neg_meta = neg_meta[neg_meta["genre"].astype(str).str.len() > 0]

    print(f"  GT 카테고리 추출: {len(gt_meta):,} | Negative 카테고리 추출: {len(neg_meta):,}")

    top_genres = (gt_meta["genre"].value_counts().head(10).index.tolist())
    gt_genre_dist = gt_meta["genre"].value_counts(normalize=True).reindex(top_genres, fill_value=0)
    neg_genre_dist = neg_meta["genre"].value_counts(normalize=True).reindex(top_genres, fill_value=0)

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

    x = np.arange(len(top_genres))
    width = 0.4
    axes[0].bar(x - width / 2, gt_genre_dist.values * 100, width, label=f"GT (n={len(gt_meta)})", color="#2f9a53")
    axes[0].bar(x + width / 2, neg_genre_dist.values * 100, width, label=f"Negative (n={len(neg_meta):,})", color="#e94560")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(top_genres, rotation=40, ha="right", fontsize=8)
    axes[0].set_ylabel("비율 (%)")
    axes[0].set_title("(a) Top-10 Books 장르 분포 비교 (GT vs Negative)")
    axes[0].legend()
    axes[0].grid(alpha=0.3, axis="y")

    bins = np.arange(0, 5.25, 0.25)
    axes[1].hist(gt_meta["average_rating"].dropna(), bins=bins, alpha=0.6,
                 label=f"GT (mean={gt_meta['average_rating'].mean():.2f})",
                 color="#2f9a53", density=True)
    axes[1].hist(neg_meta["average_rating"].dropna(), bins=bins, alpha=0.6,
                 label=f"Negative (mean={neg_meta['average_rating'].mean():.2f})",
                 color="#e94560", density=True)
    axes[1].set_xlabel("aitem average_rating")
    axes[1].set_ylabel("density")
    axes[1].set_title("(b) 아이템 평균 평점 분포 비교")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    fig.suptitle("GAP-4 · GT 1,000개 vs Negative ~49,000개 분포 비교 (평가 공정성)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    out = DATA / "eda_gt_vs_negative.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved: {out}")

    try:
        from scipy.stats import ks_2samp
        ks_rating = ks_2samp(gt_meta["average_rating"].dropna(),
                              neg_meta["average_rating"].dropna())
        ks_stat = float(ks_rating.statistic)
        ks_pvalue = float(ks_rating.pvalue)
        print(f"  KS test (rating): statistic={ks_stat:.3f}, p-value={ks_pvalue:.3e}")
    except Exception as e:
        ks_stat, ks_pvalue = None, None
        print(f"  KS test 생략: {e}")

    summary = {
        "n_gt": int(len(gt_meta)),
        "n_negative": int(len(neg_meta)),
        "gt_rating_mean": float(gt_meta["average_rating"].mean()),
        "neg_rating_mean": float(neg_meta["average_rating"].mean()),
        "rating_diff": float(gt_meta["average_rating"].mean() - neg_meta["average_rating"].mean()),
        "ks_statistic": ks_stat,
        "ks_pvalue": ks_pvalue,
        "top_genres": top_genres,
        "gt_genre_pct": [float(v * 100) for v in gt_genre_dist.values],
        "neg_genre_pct": [float(v * 100) for v in neg_genre_dist.values],
    }
    print(f"  GT 평균 평점: {summary['gt_rating_mean']:.2f} | Negative 평균: {summary['neg_rating_mean']:.2f} (차이 {summary['rating_diff']:+.2f})")
    return summary


# ============================================================
# Main
# ============================================================

def main():
    users, movies_rev, books_rev, movies_meta, books_meta = load_data()
    s2 = analyze_rating_diversity(users, movies_rev)
    s1 = analyze_cross_domain_categories(users, movies_rev, books_rev, movies_meta, books_meta)
    s4 = analyze_gt_vs_negative(users, books_rev, books_meta)

    print("\n" + "=" * 60)
    print("[Summary]")
    print(f"  GAP-2 평점 다양성: ≤2점 보유 {s2['pct_users_with_rating_le2']:.1f}%, std mean {s2['rating_std_mean']:.2f}")
    print(f"  GAP-1 카테고리 매핑: {s1['n_pairs_total']:,}쌍, 동일명 매칭 {s1['same_name_match']}건")
    print(f"  GAP-4 GT vs Neg: 평점 차이 {s4['rating_diff']:+.2f}, KS stat={s4['ks_statistic']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
