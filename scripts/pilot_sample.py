"""Pilot Study용 100명 샘플링 (Train 800명 中 12.5%).

절차:
  1. data/overlapping_users.parquet (1,000명) 로드
  2. seed=42로 shuffle 후 800/100/100 분할
  3. Train 800명 中 첫 100명을 Pilot 샘플로 선정 (deterministic)
  4. data/pilot_users.parquet 저장
  5. Source 리뷰 수 분포 검증 (전체 1,000명과 ±5% 이내)

사용법:
  python scripts/pilot_sample.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SEED = 42
N_TRAIN = 800
N_VALID = 100
N_TEST = 100
N_PILOT = 100


def main() -> None:
    print("[Loading] data/overlapping_users.parquet")
    users = pd.read_parquet(DATA / "overlapping_users.parquet")
    print(f"  total users: {len(users)}")

    # Deterministic shuffle
    rng = np.random.default_rng(SEED)
    indices = rng.permutation(len(users))
    users_shuffled = users.iloc[indices].reset_index(drop=True)

    # Split: 800 / 100 / 100
    train = users_shuffled.iloc[:N_TRAIN].copy()
    valid = users_shuffled.iloc[N_TRAIN:N_TRAIN + N_VALID].copy()
    test = users_shuffled.iloc[N_TRAIN + N_VALID:].copy()

    print(f"  split: train={len(train)} | valid={len(valid)} | test={len(test)}")

    # Pilot: first 100 of Train (deterministic given seed=42)
    pilot = train.iloc[:N_PILOT].copy()
    print(f"  pilot: {len(pilot)} (Train 첫 {N_PILOT}명)")

    # Save splits + pilot
    train.to_parquet(DATA / "train_users.parquet", index=False)
    valid.to_parquet(DATA / "valid_users.parquet", index=False)
    test.to_parquet(DATA / "test_users.parquet", index=False)
    pilot.to_parquet(DATA / "pilot_users.parquet", index=False)
    print(f"  saved: train_users.parquet, valid_users.parquet, test_users.parquet, pilot_users.parquet")

    # Verification: distribution comparison
    print("\n[Verification] Source(movie) 리뷰 수 분포 비교")
    print(f"  All 1,000명: mean={users['movie_count'].mean():.1f}, median={users['movie_count'].median():.0f}, P95={users['movie_count'].quantile(0.95):.0f}")
    print(f"  Train  800: mean={train['movie_count'].mean():.1f}, median={train['movie_count'].median():.0f}, P95={train['movie_count'].quantile(0.95):.0f}")
    print(f"  Pilot  100: mean={pilot['movie_count'].mean():.1f}, median={pilot['movie_count'].median():.0f}, P95={pilot['movie_count'].quantile(0.95):.0f}")

    pilot_mean_dev = abs(pilot["movie_count"].mean() - users["movie_count"].mean()) / users["movie_count"].mean() * 100
    print(f"  Pilot mean 편차: {pilot_mean_dev:.1f}% (목표: ≤5%)")
    if pilot_mean_dev <= 5.0:
        print("  ✅ 분포 유사성 검증 통과")
    else:
        print("  ⚠️ 분포 편차 5% 초과 — Pilot 샘플 재검토 필요할 수 있음")

    print("\n[Verification] Target(book) 리뷰 수 분포 비교")
    print(f"  All 1,000명: mean={users['book_count'].mean():.1f}, range=[{users['book_count'].min()}, {users['book_count'].max()}]")
    print(f"  Pilot  100: mean={pilot['book_count'].mean():.1f}, range=[{pilot['book_count'].min()}, {pilot['book_count'].max()}]")


if __name__ == "__main__":
    main()
