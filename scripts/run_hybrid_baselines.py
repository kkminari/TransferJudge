"""Hybrid baseline (Codex 권장).

Popularity baseline이 너무 강해서 (c) Ours 단독으로 넘기 어려울 수 있음.
대신 'LLM/Gate 신호가 popularity 위에 얹었을 때 개선되는가'를 보여주는 것이
본 연구의 더 강한 주장이 될 수 있음.

Hybrid 4종:
  pop_x_meta_linear   : 0.5 * popularity_score + 0.5 * metadata_cos
  pop_x_hist_linear   : 0.5 * popularity_score + 0.5 * history_cos
  pop_rerank_by_hist  : popularity Top-20 → history_sim으로 재정렬 → Top-10
  hist_rerank_by_pop  : history_sim Top-20 → popularity로 재정렬 → Top-10

모두 eval_fixtures/ 사용 (frozen).
비용 $0, 시간 ~5분.

사용법:
    python3 scripts/run_hybrid_baselines.py
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


def normalize(values: np.ndarray) -> np.ndarray:
    """min-max scale to [0, 1]."""
    if values.size == 0:
        return values
    lo, hi = values.min(), values.max()
    if hi - lo < 1e-9:
        return np.zeros_like(values)
    return (values - lo) / (hi - lo)


def load_fixture():
    users = json.load(open(FIXTURE / "test_users.json"))
    gt_map = json.load(open(FIXTURE / "gt.json"))

    def load_cands(uid: str):
        return json.load(open(FIXTURE / f"candidates/user_{uid}.json"))

    return users, gt_map, load_cands


def compute_scores_per_user(uid, cands, gt_id, books, books_meta_map, sentence_model):
    """후보 50권 각각에 대해 popularity / metadata_sim / history_sim score 계산."""
    n = len(cands)
    pop_raw = np.array([c.get("rating_number") or 0 for c in cands], dtype=float)
    pop_score = normalize(pop_raw)

    # history sim
    user_books = books[(books["user_id"] == uid) & (books["parent_asin"] != gt_id)]
    if len(user_books) == 0:
        hist_score = np.zeros(n)
    else:
        history_texts = []
        for _, r in user_books.iterrows():
            meta = books_meta_map.get(r["parent_asin"])
            if meta is not None:
                history_texts.append(f"{meta.get('title','')}: {str(meta.get('features_text',''))[:300]}")
            else:
                history_texts.append(str(r.get("text", ""))[:300])
        book_texts = [f"{c['title']}: {c.get('features_text', '')[:300]}" for c in cands]
        history_emb = sentence_model.encode(history_texts, normalize_embeddings=True).mean(axis=0)
        history_emb = history_emb / (np.linalg.norm(history_emb) + 1e-9)
        book_embs = sentence_model.encode(book_texts, normalize_embeddings=True)
        sims = book_embs @ history_emb
        hist_score = normalize(sims)

    return pop_score, hist_score


def run_hybrid(users, gt_map, load_cands, books, books_meta_map, sentence_model,
               combine_fn, name: str) -> list[dict]:
    """공통 hybrid runner.

    combine_fn(pop_score, hist_score) → final_score (50 array)
    """
    results = []
    t0 = time.time()
    for idx, uid in enumerate(users):
        cands = load_cands(uid)
        gt_id = gt_map[uid]["gt_id"]
        pop_score, hist_score = compute_scores_per_user(
            uid, cands, gt_id, books, books_meta_map, sentence_model
        )
        final = combine_fn(pop_score, hist_score)
        top_idx = np.argsort(final)[::-1][:10]
        rec_ids = [cands[i]["parent_asin"] for i in top_idx]
        m = compute_per_user_metrics(rec_ids, gt_id)
        results.append({"user_id": uid, "gt_id": gt_id, "rec_ids": rec_ids, "metrics": m})
        if (idx + 1) % 25 == 0:
            print(f"    [{name}] {idx+1}/{len(users)} elapsed {time.time()-t0:.0f}s")
    return results


def hybrid_linear(alpha: float):
    """linear combination: alpha * pop + (1-alpha) * hist."""
    return lambda p, h: alpha * p + (1 - alpha) * h


def hybrid_rerank(primary: str, top_k: int = 20):
    """primary로 Top-K 선정 → 다른 score로 재정렬.

    primary == "pop" → pop Top-20 후 hist로 재정렬
    primary == "hist" → hist Top-20 후 pop으로 재정렬
    """
    def fn(pop_score, hist_score):
        if primary == "pop":
            sorted_idx = np.argsort(pop_score)[::-1]
            top_idx = sorted_idx[:top_k]
            rerank_score = hist_score
        else:
            sorted_idx = np.argsort(hist_score)[::-1]
            top_idx = sorted_idx[:top_k]
            rerank_score = pop_score
        # top_idx 안에서 재정렬, 나머지는 -inf
        final = np.full_like(pop_score, -np.inf)
        final[top_idx] = rerank_score[top_idx]
        return final
    return fn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    users, gt_map, load_cands = load_fixture()
    print(f"=== Hybrid Baselines ({len(users)} users) ===\n")

    # 데이터·모델 한 번만 로드
    print("Loading data + sentence-transformers...")
    books = pd.read_parquet(ROOT / "data/books_reviews_filtered.parquet")
    books_meta = pd.read_parquet(
        ROOT / "data/books_meta_filtered.parquet",
        columns=["parent_asin", "title", "features_text"],
    )
    books_meta_map = {r["parent_asin"]: r for _, r in books_meta.iterrows()}
    from sentence_transformers import SentenceTransformer
    sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    print("  Loaded.\n")

    hybrids = [
        ("pop_x_hist_linear_50",  hybrid_linear(alpha=0.5)),
        ("pop_x_hist_linear_30",  hybrid_linear(alpha=0.3)),   # hist에 더 가중
        ("pop_x_hist_linear_70",  hybrid_linear(alpha=0.7)),   # pop에 더 가중
        ("pop_rerank_by_hist",    hybrid_rerank("pop")),
        ("hist_rerank_by_pop",    hybrid_rerank("hist")),
    ]

    all_summaries = {}
    for name, combine_fn in hybrids:
        print(f"[{name}] 시작...")
        t0 = time.time()
        per_user = run_hybrid(users, gt_map, load_cands, books, books_meta_map,
                              sentence_model, combine_fn, name)
        summary = aggregate_metrics([r["metrics"] for r in per_user])
        elapsed = time.time() - t0

        out_file = args.output_dir / f"ablation_{name}.json"
        out_file.write_text(json.dumps({
            "summary": {
                "condition": name,
                "n_evaluated": len(per_user),
                "metrics": summary,
                "elapsed_s": round(elapsed, 1),
            },
            "per_user": per_user,
        }, indent=2, ensure_ascii=False))
        all_summaries[name] = summary
        print(f"[{name}] 완료 in {elapsed:.0f}s")
        print(f"  metrics: {summary}\n")

    # 종합 표
    print("\n=== Hybrid Baselines 종합 ===")
    print(f"{'Condition':<28} {'HR@10':<10} {'NDCG@10':<10} {'MRR':<10}")
    print("-" * 60)
    for name, s in all_summaries.items():
        print(f"{name:<28} {s['HR@10']:<10.4f} {s['NDCG@10']:<10.4f} {s['MRR']:<10.4f}")


if __name__ == "__main__":
    main()
