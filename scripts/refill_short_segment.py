"""short_segment 276명을 raw 데이터에서 새로 추출해 보충.

단계:
1. Raw HF cache에서 books/movies reviews 로드
2. Overlap 재계산 (Source ≥15, Target 5~10)
3. 기존 1,000명 제외
4. 각 후보 사용자에 대해 temporal cutoff 통과 여부 (GT 이전 영화 리뷰 ≥15) 계산
5. 276명 random sample (seed=2026)
6. 해당 사용자의 reviews를 기존 filtered parquet에 append
7. main_experiment_users.parquet 및 train/valid/test split 업데이트

사용법:
    python scripts/refill_short_segment.py
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# 보충 목표: short_segment 인원수만큼
SHORT_SEGMENT_PATH = ROOT / "profiler_outputs_short_segment.json"
SEED_SAMPLE = 2026  # 기존 1,000명 seed=42와 분리

# Phase 1 조건 (EDA에서 사용한 기준)
SOURCE_MIN = 15
TARGET_MIN = 5
TARGET_MAX = 10
MOVIES_TOP_K = 30  # 사용자별 최신 영화 리뷰 개수


def main():
    # ===== 1. Raw 데이터 로드 =====
    print("[1/7] Loading raw data from HF cache...")
    from datasets import load_dataset
    raw_books = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        "raw_review_Books",
        split="full",
        trust_remote_code=True,
    )
    raw_movies = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        "raw_review_Movies_and_TV",
        split="full",
        trust_remote_code=True,
    )

    print("[2/7] Converting to pandas (selecting essential columns)...")
    cols = ["user_id", "parent_asin", "rating", "timestamp", "title", "text"]
    books_pd = raw_books.select_columns(cols).to_pandas()
    movies_pd = raw_movies.select_columns(cols).to_pandas()
    print(f"  books rows: {len(books_pd):,}, movies rows: {len(movies_pd):,}")

    # ===== 2. Overlap 재계산 =====
    print("[3/7] Recomputing overlapping users (Source≥15, Target 5-10)...")
    movies_counts = movies_pd.groupby("user_id").size()
    books_counts = books_pd.groupby("user_id").size()
    qualified_movies = movies_counts[movies_counts >= SOURCE_MIN].index
    qualified_books = books_counts[(books_counts >= TARGET_MIN) & (books_counts <= TARGET_MAX)].index
    overlap_full = set(qualified_movies) & set(qualified_books)
    print(f"  overlap (Source≥{SOURCE_MIN}, Target {TARGET_MIN}-{TARGET_MAX}): {len(overlap_full):,}")

    # ===== 3. 기존 1,000명 제외 =====
    existing = set(pd.read_parquet(DATA / "main_experiment_users.parquet")["user_id"])
    remaining = overlap_full - existing
    print(f"  excluding existing 1,000 → remaining pool: {len(remaining):,}")

    # ===== 4. Temporal cutoff 통과 후보 계산 =====
    print("[4/7] Filtering temporal-cutoff-safe candidates...")
    # GT timestamp (rating>=4 max per user in books)
    pos = books_pd[books_pd["rating"] >= 4.0]
    gt_ts = pos.groupby("user_id")["timestamp"].max().to_dict()

    rem_movies = movies_pd[movies_pd["user_id"].isin(remaining)][["user_id", "timestamp"]]
    rem_movies = rem_movies.copy()
    rem_movies["gt_ts"] = rem_movies["user_id"].map(gt_ts)
    rem_movies["safe"] = rem_movies["gt_ts"].notna() & (rem_movies["timestamp"] < rem_movies["gt_ts"])
    safe_counts = rem_movies[rem_movies["safe"]].groupby("user_id").size()
    candidate_pool = safe_counts[safe_counts >= 15].index
    candidate_pool = set(candidate_pool) & remaining
    candidate_pool = [u for u in candidate_pool if u in gt_ts]  # GT 있어야
    print(f"  temporal-safe candidates (≥15 cutoff-passed movies + GT): {len(candidate_pool):,}")

    # ===== 5. 보충 인원 sample =====
    short_seg = json.loads(SHORT_SEGMENT_PATH.read_text())
    n_short = len(short_seg)
    print(f"\n[5/7] Sampling {n_short} replacement users (seed={SEED_SAMPLE})...")
    if len(candidate_pool) < n_short:
        raise SystemExit(
            f"❌ Insufficient candidates: need {n_short}, have {len(candidate_pool)}. "
            "Consider relaxing min_reviews."
        )
    rng = np.random.default_rng(SEED_SAMPLE)
    selected = list(rng.choice(list(candidate_pool), size=n_short, replace=False))
    print(f"  selected: {len(selected)} users")

    # 통계
    sel_movie_counts = movies_pd[movies_pd["user_id"].isin(selected)].groupby("user_id").size()
    sel_book_counts = books_pd[books_pd["user_id"].isin(selected)].groupby("user_id").size()
    sel_df = pd.DataFrame({
        "user_id": selected,
        "movie_count": [sel_movie_counts.get(u, 0) for u in selected],
        "book_count": [sel_book_counts.get(u, 0) for u in selected],
    })
    print(f"  movie_count mean={sel_df['movie_count'].mean():.1f}, "
          f"book_count mean={sel_df['book_count'].mean():.1f}")

    # ===== 6. Reviews append =====
    print("\n[6/7] Appending reviews to filtered parquet files...")
    # 새 사용자의 movies/books reviews 추출
    new_movies = movies_pd[movies_pd["user_id"].isin(selected)].copy()
    # Phase 1 방식과 동일하게 사용자별 최신 30개로 제한
    new_movies = (
        new_movies.sort_values(["user_id", "timestamp"], ascending=[True, False])
        .groupby("user_id")
        .head(MOVIES_TOP_K)
    )
    new_books = books_pd[books_pd["user_id"].isin(selected)].copy()
    print(f"  new movies reviews: {len(new_movies):,}, new books reviews: {len(new_books):,}")

    # datetime + token_count 컬럼 추가 (기존 schema 맞추기)
    new_movies["datetime"] = pd.to_datetime(new_movies["timestamp"], unit="ms")
    new_books["datetime"] = pd.to_datetime(new_books["timestamp"], unit="ms")
    new_movies["token_count"] = new_movies["text"].astype(str).str.split().str.len()
    new_books["token_count"] = new_books["text"].astype(str).str.split().str.len()

    # 기존 + 새 데이터 병합
    movies_old = pd.read_parquet(DATA / "movies_reviews_filtered.parquet")
    books_old = pd.read_parquet(DATA / "books_reviews_filtered.parquet")
    # 백업
    (DATA / "movies_reviews_filtered_v1.parquet").write_bytes(
        (DATA / "movies_reviews_filtered.parquet").read_bytes()
    )
    (DATA / "books_reviews_filtered_v1.parquet").write_bytes(
        (DATA / "books_reviews_filtered.parquet").read_bytes()
    )
    print(f"  backups saved: *_filtered_v1.parquet")

    # 컬럼 정렬 후 concat
    new_movies = new_movies[movies_old.columns]
    new_books = new_books[books_old.columns]
    movies_merged = pd.concat([movies_old, new_movies], ignore_index=True)
    books_merged = pd.concat([books_old, new_books], ignore_index=True)
    movies_merged.to_parquet(DATA / "movies_reviews_filtered.parquet", index=False)
    books_merged.to_parquet(DATA / "books_reviews_filtered.parquet", index=False)
    print(f"  movies_reviews_filtered.parquet: {len(movies_old):,} → {len(movies_merged):,}")
    print(f"  books_reviews_filtered.parquet:  {len(books_old):,} → {len(books_merged):,}")

    # ===== 7. main_experiment_users + split 업데이트 =====
    print("\n[7/7] Updating main_experiment_users + train/valid/test splits...")
    # 기존 split 유지하며 새 사용자만 추가 (8:1:1)
    n = len(selected)
    n_train = int(n * 0.8)
    n_valid = int(n * 0.1)
    # split을 위해 sel_df 셔플
    rng2 = np.random.default_rng(SEED_SAMPLE + 1)
    sel_df_shuf = sel_df.sample(frac=1, random_state=rng2.integers(0, 2**31)).reset_index(drop=True)

    new_train = sel_df_shuf.iloc[:n_train]
    new_valid = sel_df_shuf.iloc[n_train:n_train + n_valid]
    new_test = sel_df_shuf.iloc[n_train + n_valid:]
    print(f"  new split: train={len(new_train)}, valid={len(new_valid)}, test={len(new_test)}")

    # 백업 후 append
    for name, new_part in [("train_users", new_train), ("valid_users", new_valid), ("test_users", new_test)]:
        old = pd.read_parquet(DATA / f"{name}.parquet")
        (DATA / f"{name}_v1.parquet").write_bytes((DATA / f"{name}.parquet").read_bytes())
        merged = pd.concat([old, new_part], ignore_index=True)
        merged.to_parquet(DATA / f"{name}.parquet", index=False)
        print(f"  {name}.parquet: {len(old)} → {len(merged)}")

    # main_experiment_users 업데이트
    main_users = pd.concat([
        pd.read_parquet(DATA / "train_users.parquet"),
        pd.read_parquet(DATA / "valid_users.parquet"),
        pd.read_parquet(DATA / "test_users.parquet"),
    ], ignore_index=True)
    main_users.to_parquet(DATA / "main_experiment_users.parquet", index=False)
    print(f"  main_experiment_users.parquet: {len(main_users)} users total")

    print()
    print("✅ Refill complete. Now run:")
    print(f"   python3 scripts/run_profiler.py \\")
    print(f"     --users data/main_experiment_users.parquet \\")
    print(f"     --reviews data/movies_reviews_filtered.parquet \\")
    print(f"     --target-reviews data/books_reviews_filtered.parquet \\")
    print(f"     --output profiler_outputs/ \\")
    print(f"     --max-reviews 30 --min-reviews 15")
    print()
    print(f"   (Resume will auto-skip existing Profiles; only {n_short} new will be generated.)")


if __name__ == "__main__":
    main()
