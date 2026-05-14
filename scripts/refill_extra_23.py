"""977명 → 1,000명 정확히 맞추기 위해 23명 추가 보충.

이번엔 사전 필터를 엄격화: 실제 run 조건(최신 30개 영화 중 GT 이전 ≥15)과 동일하게.

사용법:
    python scripts/refill_extra_23.py
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SEED_SAMPLE = 2027  # 이전 refill seed=2026과 분리
SOURCE_MIN = 15
TARGET_MIN = 5
TARGET_MAX = 10
MOVIES_TOP_K = 30
N_NEED = 23


def main():
    print("[1/6] Loading raw data from HF cache...")
    from datasets import load_dataset
    raw_books = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        "raw_review_Books", split="full", trust_remote_code=True,
    )
    raw_movies = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        "raw_review_Movies_and_TV", split="full", trust_remote_code=True,
    )

    print("[2/6] To pandas...")
    cols = ["user_id", "parent_asin", "rating", "timestamp", "title", "text"]
    books_pd = raw_books.select_columns(cols).to_pandas()
    movies_pd = raw_movies.select_columns(cols).to_pandas()

    # Existing
    existing = set(pd.read_parquet(DATA / "main_experiment_users.parquet")["user_id"])
    print(f"  existing users: {len(existing):,}")

    # Overlap (Source>=15, Target 5-10)
    print("[3/6] Recomputing overlap...")
    movies_counts = movies_pd.groupby("user_id").size()
    books_counts = books_pd.groupby("user_id").size()
    q_movies = movies_counts[movies_counts >= SOURCE_MIN].index
    q_books = books_counts[(books_counts >= TARGET_MIN) & (books_counts <= TARGET_MAX)].index
    overlap = (set(q_movies) & set(q_books)) - existing
    print(f"  overlap excluding existing: {len(overlap):,}")

    # GT timestamp
    pos = books_pd[books_pd["rating"] >= 4.0]
    gt_ts = pos.groupby("user_id")["timestamp"].max().to_dict()

    # ===== 엄격한 사전 필터 =====
    # 실제 run 조건과 동일: 사용자별 최신 30개 영화 중 GT 이전 ≥15
    print("[4/6] Strict pre-filter (top-30 movies, GT-pre ≥15)...")
    cand_movies = movies_pd[movies_pd["user_id"].isin(overlap)].copy()
    # 사용자별 최신순 정렬 후 head(30)
    cand_movies = cand_movies.sort_values(["user_id", "timestamp"], ascending=[True, False])
    cand_top30 = cand_movies.groupby("user_id", group_keys=False).head(MOVIES_TOP_K)
    cand_top30 = cand_top30.copy()
    cand_top30["gt_ts"] = cand_top30["user_id"].map(gt_ts)
    cand_top30["safe"] = cand_top30["gt_ts"].notna() & (cand_top30["timestamp"] < cand_top30["gt_ts"])
    safe_counts = cand_top30[cand_top30["safe"]].groupby("user_id").size()
    strict_pool = safe_counts[safe_counts >= 15].index
    strict_pool = [u for u in strict_pool if u in gt_ts]
    print(f"  strict-safe candidates: {len(strict_pool):,}")
    if len(strict_pool) < N_NEED:
        raise SystemExit(f"❌ Need {N_NEED}, have {len(strict_pool)}")

    # Sample
    rng = np.random.default_rng(SEED_SAMPLE)
    selected = list(rng.choice(strict_pool, size=N_NEED, replace=False))
    print(f"  selected: {len(selected)}")

    # Stats
    sel_book_counts = books_pd[books_pd["user_id"].isin(selected)].groupby("user_id").size()
    sel_df = pd.DataFrame({
        "user_id": selected,
        "movie_count": [int(safe_counts.get(u, 0)) for u in selected],
        "book_count": [int(sel_book_counts.get(u, 0)) for u in selected],
    })
    print(f"  movie(safe top30) mean={sel_df['movie_count'].mean():.1f}, "
          f"book mean={sel_df['book_count'].mean():.1f}")

    # Append reviews to filtered parquets
    print("[5/6] Appending reviews...")
    new_movies = movies_pd[movies_pd["user_id"].isin(selected)].copy()
    new_movies = (
        new_movies.sort_values(["user_id", "timestamp"], ascending=[True, False])
        .groupby("user_id").head(MOVIES_TOP_K)
    )
    new_books = books_pd[books_pd["user_id"].isin(selected)].copy()
    new_movies["datetime"] = pd.to_datetime(new_movies["timestamp"], unit="ms")
    new_books["datetime"] = pd.to_datetime(new_books["timestamp"], unit="ms")
    new_movies["token_count"] = new_movies["text"].astype(str).str.split().str.len()
    new_books["token_count"] = new_books["text"].astype(str).str.split().str.len()

    movies_old = pd.read_parquet(DATA / "movies_reviews_filtered.parquet")
    books_old = pd.read_parquet(DATA / "books_reviews_filtered.parquet")
    new_movies = new_movies[movies_old.columns]
    new_books = new_books[books_old.columns]
    pd.concat([movies_old, new_movies], ignore_index=True).to_parquet(
        DATA / "movies_reviews_filtered.parquet", index=False)
    pd.concat([books_old, new_books], ignore_index=True).to_parquet(
        DATA / "books_reviews_filtered.parquet", index=False)
    print(f"  movies: {len(movies_old):,} → {len(movies_old) + len(new_movies):,}")
    print(f"  books:  {len(books_old):,} → {len(books_old) + len(new_books):,}")

    # Update splits (8:1:1)
    print("[6/6] Updating splits...")
    rng2 = np.random.default_rng(SEED_SAMPLE + 1)
    sel_shuf = sel_df.sample(frac=1, random_state=rng2.integers(0, 2**31)).reset_index(drop=True)
    n = len(sel_shuf)
    n_train = int(n * 0.8); n_valid = int(n * 0.1)
    new_train = sel_shuf.iloc[:n_train]
    new_valid = sel_shuf.iloc[n_train:n_train + n_valid]
    new_test = sel_shuf.iloc[n_train + n_valid:]
    print(f"  split: train+{len(new_train)}, valid+{len(new_valid)}, test+{len(new_test)}")

    for name, part in [("train_users", new_train), ("valid_users", new_valid), ("test_users", new_test)]:
        old = pd.read_parquet(DATA / f"{name}.parquet")
        merged = pd.concat([old, part], ignore_index=True)
        merged.to_parquet(DATA / f"{name}.parquet", index=False)
        print(f"  {name}.parquet: {len(old)} → {len(merged)}")

    main_users = pd.concat([
        pd.read_parquet(DATA / "train_users.parquet"),
        pd.read_parquet(DATA / "valid_users.parquet"),
        pd.read_parquet(DATA / "test_users.parquet"),
    ], ignore_index=True)
    main_users.to_parquet(DATA / "main_experiment_users.parquet", index=False)
    print(f"  main_experiment_users.parquet: {len(main_users)} users total")
    print("\n✅ Extra 23 refill complete. Next: re-run profiler.")


if __name__ == "__main__":
    main()
