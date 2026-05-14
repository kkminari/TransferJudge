"""Split 재정의 — data leakage 제거.

규칙:
1. 학습 데이터(teacher_train_main.jsonl) 602 user → 전부 train으로 재분류
2. Profile 보유 1,000명 - 602명 = 398명 미사용 풀
3. 그 중 random sample → valid 100 / test 100 (seed=2028)
4. 기존 train/valid/test parquet 백업 (_pre_leakfix) 후 재생성

검증:
- train ∩ (valid ∪ test) = ∅
- 모두 Profile 보유

사용법:
    python scripts/redefine_splits.py
"""
from __future__ import annotations

import json
import re
import glob
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SEED_HOLDOUT = 2028
N_VALID = 100
N_TEST = 100


def main():
    # 1. 학습 데이터 user_id 추출
    print("[1/5] Extracting user IDs from training data...")
    lines = open(DATA / "teacher_train_main.jsonl").readlines()
    train_uids = set()
    for line in lines:
        d = json.loads(line)
        user_msg = next(m for m in d["messages"] if m["role"] == "user")
        m = re.search(r'"user_id":\s*"([A-Z0-9]+)"', user_msg["content"])
        if m:
            train_uids.add(m.group(1))
    print(f"  Training records: {len(lines)}, unique users: {len(train_uids)}")

    # 2. Profile 보유 사용자 전체
    print("[2/5] Loading Profile owners...")
    profile_uids = set()
    for f in glob.glob(str(ROOT / "profiler_outputs/*.json")):
        uid = Path(f).stem.replace("user_", "")
        profile_uids.add(uid)
    print(f"  Profile owners: {len(profile_uids)}")

    # 3. 미사용 풀 = Profile 보유 - 학습 데이터
    available = list(profile_uids - train_uids)
    print(f"\n[3/5] Available holdout pool: {len(available)}")
    if len(available) < N_VALID + N_TEST:
        raise SystemExit(f"❌ Need {N_VALID + N_TEST}, have {len(available)}")

    # 4. Random sample
    rng = np.random.default_rng(SEED_HOLDOUT)
    shuffled = rng.permutation(available)
    valid_uids = shuffled[:N_VALID].tolist()
    test_uids = shuffled[N_VALID:N_VALID + N_TEST].tolist()
    print(f"  valid: {len(valid_uids)}, test: {len(test_uids)}")

    # 검증: 누수 없는지
    assert not set(train_uids) & set(valid_uids), "train-valid leakage!"
    assert not set(train_uids) & set(test_uids), "train-test leakage!"
    assert not set(valid_uids) & set(test_uids), "valid-test overlap!"
    print("  ✅ no leakage")

    # 5. 백업 후 새 parquet 생성
    print("\n[4/5] Backup + regenerate split parquets...")
    movies_reviews = pd.read_parquet(DATA / "movies_reviews_filtered.parquet", columns=["user_id"])
    books_reviews = pd.read_parquet(DATA / "books_reviews_filtered.parquet", columns=["user_id"])
    movie_counts = movies_reviews.groupby("user_id").size()
    book_counts = books_reviews.groupby("user_id").size()

    def make_df(uids: list) -> pd.DataFrame:
        return pd.DataFrame({
            "user_id": uids,
            "movie_count": [int(movie_counts.get(u, 0)) for u in uids],
            "book_count": [int(book_counts.get(u, 0)) for u in uids],
        })

    train_df = make_df(sorted(train_uids))
    valid_df = make_df(valid_uids)
    test_df = make_df(test_uids)

    # 백업
    for name in ["train_users", "valid_users", "test_users"]:
        src = DATA / f"{name}.parquet"
        if src.exists():
            dst = DATA / f"{name}_pre_leakfix.parquet"
            dst.write_bytes(src.read_bytes())
            print(f"  backup: {dst.name}")

    train_df.to_parquet(DATA / "train_users.parquet", index=False)
    valid_df.to_parquet(DATA / "valid_users.parquet", index=False)
    test_df.to_parquet(DATA / "test_users.parquet", index=False)
    print(f"  train_users.parquet: {len(train_df)}")
    print(f"  valid_users.parquet: {len(valid_df)}")
    print(f"  test_users.parquet:  {len(test_df)}")

    # main_experiment_users 업데이트
    main_df = pd.concat([train_df, valid_df, test_df], ignore_index=True)
    (DATA / "main_experiment_users_pre_leakfix.parquet").write_bytes(
        (DATA / "main_experiment_users.parquet").read_bytes()
    )
    main_df.to_parquet(DATA / "main_experiment_users.parquet", index=False)
    print(f"  main_experiment_users.parquet: {len(main_df)} (= {len(train_df)} + {len(valid_df)} + {len(test_df)})")

    # 6. Verification
    print("\n[5/5] Final verification...")
    t = set(pd.read_parquet(DATA / "train_users.parquet")["user_id"])
    v = set(pd.read_parquet(DATA / "valid_users.parquet")["user_id"])
    e = set(pd.read_parquet(DATA / "test_users.parquet")["user_id"])
    print(f"  train ∩ valid: {len(t & v)} (must be 0)")
    print(f"  train ∩ test:  {len(t & e)} (must be 0)")
    print(f"  valid ∩ test:  {len(v & e)} (must be 0)")
    print(f"  train ⊆ training_data: {len(t - train_uids) == 0}")
    print()
    print("✅ Split redefined. data leakage = 0.")


if __name__ == "__main__":
    main()
