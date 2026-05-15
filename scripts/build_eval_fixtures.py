"""Tier 1 — 평가 fixture 고정 (Codex 권장).

test 100명에 대해 candidates 50권 + GT를 한 번 산출하고 JSON으로 저장.
이후 모든 baseline·모델은 이 fixture를 사용하여 동일 조건 비교 보장.

사용법:
    python3 scripts/build_eval_fixtures.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT / "scripts"))
from run_teacher import sample_candidates, pick_gt

SEED = 42


def main():
    out_dir = ROOT / "eval_fixtures"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "candidates").mkdir(parents=True, exist_ok=True)

    print("=== Tier 1: Eval Fixture 고정 ===")
    print(f"Output: {out_dir}")

    # 데이터 로드
    test_users = pd.read_parquet(ROOT / "data/test_users.parquet")
    books = pd.read_parquet(ROOT / "data/books_reviews_filtered.parquet")
    books_meta = pd.read_parquet(ROOT / "data/books_meta_filtered.parquet")

    print(f"test_users: {len(test_users)}")
    print(f"books reviews: {len(books):,}")
    print(f"books meta: {len(books_meta):,}")
    print()

    rng = np.random.default_rng(SEED)
    n_failed = 0
    fixture_users = []
    gt_map = {}

    for idx, user_row in enumerate(test_users.itertuples(index=False)):
        uid = getattr(user_row, "user_id")

        # GT
        user_books = books[books["user_id"] == uid]
        gt_info = pick_gt(user_books)
        if gt_info is None:
            print(f"  [{idx+1}/{len(test_users)}] {uid}: no GT, SKIP")
            n_failed += 1
            continue
        gt_id = str(gt_info["parent_asin"])

        # Candidates
        try:
            candidates = sample_candidates(
                user_id=uid, gt_item_id=gt_id,
                books_meta_df=books_meta,
                user_books_reviews=user_books,
                n_candidates=50, rng=rng,
            )
        except ValueError as e:
            print(f"  [{idx+1}/{len(test_users)}] {uid}: candidate err: {e}")
            n_failed += 1
            continue

        cand_list = []
        for c in candidates:
            cand_list.append({
                "parent_asin": str(c.get("parent_asin", "")).strip(),
                "title": str(c.get("title", "")).strip(),
                "author_name": str(c.get("author_name", "")).strip(),
                "categories": list(c.get("categories", [])) if c.get("categories") is not None else [],
                "average_rating": float(c["average_rating"]) if c.get("average_rating") is not None else None,
                "rating_number": int(c["rating_number"]) if c.get("rating_number") is not None else None,
                "features_text": str(c.get("features_text", "") or "")[:1000],
            })

        # 사용자별 candidates 저장
        cand_file = out_dir / "candidates" / f"user_{uid}.json"
        cand_file.write_text(json.dumps(cand_list, ensure_ascii=False, indent=2))

        fixture_users.append(uid)
        gt_map[uid] = {
            "gt_id": gt_id,
            "gt_rating": float(gt_info["rating"]),
            "n_candidates": len(cand_list),
        }

        if (idx + 1) % 20 == 0:
            print(f"  [{idx+1}/{len(test_users)}] processed...")

    # users.json + gt.json
    (out_dir / "test_users.json").write_text(
        json.dumps(fixture_users, ensure_ascii=False, indent=2)
    )
    (out_dir / "gt.json").write_text(
        json.dumps(gt_map, ensure_ascii=False, indent=2)
    )

    # README
    readme = f"""# Evaluation Fixtures (FROZEN)

생성 시점: {time.strftime('%Y-%m-%d %H:%M:%S')}
SEED: {SEED} (sample_candidates)

## 파일 구조
- `test_users.json` — 평가 대상 user_id {len(fixture_users)}개 (frozen)
- `gt.json` — user_id → gt_id 매핑 (frozen)
- `candidates/user_<id>.json` — 사용자별 50권 후보 (frozen)

## 사용 방법
모든 baseline / model 평가는 이 fixture를 사용해야 함:
```python
import json
from pathlib import Path
FIXTURE = Path("eval_fixtures")
users = json.load(open(FIXTURE / "test_users.json"))
gt_map = json.load(open(FIXTURE / "gt.json"))
for uid in users:
    candidates = json.load(open(FIXTURE / f"candidates/user_{{uid}}.json"))
    gt_id = gt_map[uid]["gt_id"]
    # ... model 추론 ...
```

## 통계
- 평가 대상: {len(fixture_users)} 명
- GT 없는 사용자 (skip): {n_failed} 명
- 사용자별 후보: 50권 (GT 1 + Negative 49, shuffle)

## 주의
**절대 이 파일들을 수정하지 말 것.**
모델·baseline 비교의 공정성은 이 fixture가 frozen 상태일 때만 보장됨.
"""
    (out_dir / "README.md").write_text(readme)

    print(f"\n=== 완료 ===")
    print(f"  fixture users: {len(fixture_users)}")
    print(f"  skipped: {n_failed}")
    print(f"  candidates dir: {out_dir / 'candidates'}")
    print(f"  files: test_users.json, gt.json, candidates/*.json, README.md")


if __name__ == "__main__":
    main()
