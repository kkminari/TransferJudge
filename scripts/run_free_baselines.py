"""Tier 2 — 5개 무료 baseline (Codex 권장).

모두 eval_fixtures/를 사용하여 동일 조건 평가.
비용 $0, GPU 불필요.

Baselines:
  random      : 50개 후보에서 무작위 10개 (seed 고정)
  cand_order  : 후보 순서 그대로 첫 10개 (no model)
  popularity  : books_reviews에서 review_count 많은 책 우선
  metadata_sim: 사용자 영화 리뷰 ↔ 책 메타데이터 임베딩 cosine
  history_sim : 사용자 books 평가 ↔ 후보 책 메타데이터 임베딩 cosine

사용법:
    python3 scripts/run_free_baselines.py --baseline random
    python3 scripts/run_free_baselines.py --baseline all
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "eval_fixtures"

sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_judge import compute_per_user_metrics, aggregate_metrics


SEED = 42
BASELINES = ["random", "cand_order", "popularity", "metadata_sim", "history_sim"]


def load_fixture():
    users = json.load(open(FIXTURE / "test_users.json"))
    gt_map = json.load(open(FIXTURE / "gt.json"))

    def load_cands(uid: str):
        return json.load(open(FIXTURE / f"candidates/user_{uid}.json"))

    return users, gt_map, load_cands


# ============================================================
# Baseline 1: Random
# ============================================================
def baseline_random(users, gt_map, load_cands) -> list[dict]:
    rng = np.random.default_rng(SEED)
    results = []
    for uid in users:
        cands = load_cands(uid)
        gt_id = gt_map[uid]["gt_id"]
        # Shuffle indices and take top 10
        indices = rng.permutation(len(cands))[:10]
        rec_ids = [cands[i]["parent_asin"] for i in indices]
        m = compute_per_user_metrics(rec_ids, gt_id)
        results.append({"user_id": uid, "gt_id": gt_id, "rec_ids": rec_ids, "metrics": m})
    return results


# ============================================================
# Baseline 2: Candidate Order
# ============================================================
def baseline_cand_order(users, gt_map, load_cands) -> list[dict]:
    """후보 입력 순서 그대로 첫 10개. 모델 없는 simplest baseline."""
    results = []
    for uid in users:
        cands = load_cands(uid)
        gt_id = gt_map[uid]["gt_id"]
        rec_ids = [c["parent_asin"] for c in cands[:10]]
        m = compute_per_user_metrics(rec_ids, gt_id)
        results.append({"user_id": uid, "gt_id": gt_id, "rec_ids": rec_ids, "metrics": m})
    return results


# ============================================================
# Baseline 3: Popularity
# ============================================================
def baseline_popularity(users, gt_map, load_cands) -> list[dict]:
    """rating_number(인기) 기준 내림차순. fixture에 이미 있음."""
    results = []
    for uid in users:
        cands = load_cands(uid)
        gt_id = gt_map[uid]["gt_id"]
        # rating_number는 리뷰 수 → 인기도
        ranked = sorted(cands, key=lambda c: c.get("rating_number") or 0, reverse=True)
        rec_ids = [c["parent_asin"] for c in ranked[:10]]
        m = compute_per_user_metrics(rec_ids, gt_id)
        results.append({"user_id": uid, "gt_id": gt_id, "rec_ids": rec_ids, "metrics": m})
    return results


# ============================================================
# Baseline 4: Metadata Similarity (sentence-transformers)
# ============================================================
def baseline_metadata_sim(users, gt_map, load_cands) -> list[dict]:
    """사용자 영화 리뷰 텍스트 ↔ 책 메타데이터 (title + features_text) 임베딩 코사인."""
    print("  Loading sentence-transformers...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")

    movies = pd.read_parquet(ROOT / "data/movies_reviews_filtered.parquet",
                              columns=["user_id", "timestamp", "title", "text", "rating"])
    books_reviews = pd.read_parquet(ROOT / "data/books_reviews_filtered.parquet",
                                     columns=["user_id", "parent_asin", "timestamp"])

    results = []
    t0 = time.time()
    for idx, uid in enumerate(users):
        cands = load_cands(uid)
        gt_id = gt_map[uid]["gt_id"]

        # 사용자 영화 텍스트 (GT 이전, 최신 30개)
        gt_ts = books_reviews[(books_reviews["user_id"] == uid) &
                              (books_reviews["parent_asin"] == gt_id)]["timestamp"]
        if len(gt_ts) == 0:
            results.append({"user_id": uid, "gt_id": gt_id, "rec_ids": [], "metrics": {
                "HR@1": 0, "HR@5": 0, "HR@10": 0, "NDCG@5": 0.0, "NDCG@10": 0.0, "MRR": 0.0,
            }})
            continue
        gt_ts = gt_ts.iloc[0]
        user_movies = movies[(movies["user_id"] == uid) &
                              (movies["timestamp"] < gt_ts)]
        user_movies = user_movies.sort_values("timestamp", ascending=False).head(30)

        # 영화 리뷰 텍스트 합치기
        user_text = " ".join([f"{r['title']}: {r['text'][:200]}"
                              for _, r in user_movies.iterrows()])

        # 후보 책 메타데이터 텍스트
        book_texts = [f"{c['title']}: {c.get('features_text', '')[:300]}" for c in cands]

        # 임베딩 + 코사인
        user_emb = model.encode([user_text], normalize_embeddings=True)[0]
        book_embs = model.encode(book_texts, normalize_embeddings=True)
        sims = book_embs @ user_emb
        top_indices = np.argsort(sims)[::-1][:10]
        rec_ids = [cands[i]["parent_asin"] for i in top_indices]

        m = compute_per_user_metrics(rec_ids, gt_id)
        results.append({"user_id": uid, "gt_id": gt_id, "rec_ids": rec_ids, "metrics": m})

        if (idx + 1) % 20 == 0:
            elapsed = time.time() - t0
            print(f"    [{idx+1}/{len(users)}] elapsed {elapsed:.0f}s")

    return results


# ============================================================
# Baseline 5: History Similarity
# ============================================================
def baseline_history_sim(users, gt_map, load_cands) -> list[dict]:
    """사용자의 books 활동 (GT 제외)과 후보 책 메타데이터 임베딩 코사인."""
    print("  Loading sentence-transformers...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")

    books = pd.read_parquet(ROOT / "data/books_reviews_filtered.parquet")
    books_meta = pd.read_parquet(
        ROOT / "data/books_meta_filtered.parquet",
        columns=["parent_asin", "title", "features_text"],
    )
    title_map = {r["parent_asin"]: r for _, r in books_meta.iterrows()}

    results = []
    t0 = time.time()
    for idx, uid in enumerate(users):
        cands = load_cands(uid)
        gt_id = gt_map[uid]["gt_id"]

        # 사용자의 books 활동 (GT 제외)
        user_books = books[(books["user_id"] == uid) &
                            (books["parent_asin"] != gt_id)]
        if len(user_books) == 0:
            # GT 외 책 없으면 candidate-order로 fallback
            rec_ids = [c["parent_asin"] for c in cands[:10]]
            m = compute_per_user_metrics(rec_ids, gt_id)
            results.append({"user_id": uid, "gt_id": gt_id, "rec_ids": rec_ids, "metrics": m})
            continue

        # 사용자 books 텍스트
        history_texts = []
        for _, r in user_books.iterrows():
            meta = title_map.get(r["parent_asin"])
            if meta is not None:
                history_texts.append(f"{meta.get('title','')}: {str(meta.get('features_text',''))[:300]}")
            else:
                history_texts.append(str(r.get("text", ""))[:300])

        # 후보 책 텍스트
        book_texts = [f"{c['title']}: {c.get('features_text', '')[:300]}" for c in cands]

        # 평균 임베딩 (사용자 history) ↔ 후보 책 임베딩
        history_emb = model.encode(history_texts, normalize_embeddings=True).mean(axis=0)
        history_emb = history_emb / (np.linalg.norm(history_emb) + 1e-9)
        book_embs = model.encode(book_texts, normalize_embeddings=True)
        sims = book_embs @ history_emb
        top_indices = np.argsort(sims)[::-1][:10]
        rec_ids = [cands[i]["parent_asin"] for i in top_indices]

        m = compute_per_user_metrics(rec_ids, gt_id)
        results.append({"user_id": uid, "gt_id": gt_id, "rec_ids": rec_ids, "metrics": m})

        if (idx + 1) % 20 == 0:
            elapsed = time.time() - t0
            print(f"    [{idx+1}/{len(users)}] elapsed {elapsed:.0f}s")

    return results


BASELINE_FN = {
    "random": baseline_random,
    "cand_order": baseline_cand_order,
    "popularity": baseline_popularity,
    "metadata_sim": baseline_metadata_sim,
    "history_sim": baseline_history_sim,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", choices=BASELINES + ["all"], default="all")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    users, gt_map, load_cands = load_fixture()
    print(f"=== Tier 2: Free Baselines ===")
    print(f"  fixture users: {len(users)}")
    print()

    to_run = BASELINES if args.baseline == "all" else [args.baseline]
    for bl in to_run:
        t0 = time.time()
        print(f"\n[{bl}] 시작...")
        per_user = BASELINE_FN[bl](users, gt_map, load_cands)
        summary = aggregate_metrics([r["metrics"] for r in per_user]) if per_user else {}
        elapsed = time.time() - t0

        out_file = args.output_dir / f"ablation_{bl}.json"
        out_file.write_text(json.dumps({
            "summary": {
                "condition": bl,
                "n_evaluated": len(per_user),
                "metrics": summary,
                "elapsed_s": round(elapsed, 1),
            },
            "per_user": per_user,
        }, indent=2, ensure_ascii=False))

        print(f"[{bl}] 완료 in {elapsed:.0f}s")
        print(f"  metrics: {summary}")
        print(f"  saved: {out_file}")


if __name__ == "__main__":
    main()
