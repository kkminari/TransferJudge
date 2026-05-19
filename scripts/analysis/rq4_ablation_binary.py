"""RQ4 보강 — 옵션 C: 3단계 vs binary 결정 ablation (정확도 + 다양성).

3가지 변형:
  - three_level:           TRANSFER=1.0, PARTIAL=0.5, BLOCK=0.0  (본 연구)
  - binary_aggressive:     TRANSFER=1.0, PARTIAL=1.0, BLOCK=0.0  (PARTIAL → TRANSFER)
  - binary_conservative:   TRANSFER=1.0, PARTIAL=0.0, BLOCK=0.0  (PARTIAL → BLOCK)

각 변형에서 측정:
  - 정확도: HR@10, NDCG@10, MRR
  - 다양성: Novelty, ILD, Long-tail %

paired bootstrap 95% CI로 변형 간 비교.

실행:
    .venv_thesis/bin/python scripts/analysis/rq4_ablation_binary.py
출력:
    results/analysis/rq4_ablation_binary.json
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import transfer_ranker as tr
from transfer_ranker import (
    load_fixture,
    load_judge_decisions,
    compute_signals_per_user,
    eval_ranker,
    build_user_movie_text,
)

OUTPUT_PATH = ROOT / "results/analysis/rq4_ablation_binary.json"
ALPHA, BETA, GAMMA = 0.7, 0.3, 0.20
LONGTAIL_THR = 13.0  # rating_number 임계 (본 연구 표준)

VARIANTS = {
    "three_level": {"TRANSFER": 1.0, "PARTIAL": 0.5, "BLOCK": 0.0},
    "binary_aggressive": {"TRANSFER": 1.0, "PARTIAL": 1.0, "BLOCK": 0.0},
    "binary_conservative": {"TRANSFER": 1.0, "PARTIAL": 0.0, "BLOCK": 0.0},
}


def load_diversity_helpers():
    """analyze_novelty_serendipity.py 모듈을 동적 로드."""
    spec = importlib.util.spec_from_file_location(
        "ans", str(ROOT / "scripts/analyze_novelty_serendipity.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compute_diversity_per_user(per_user, book_meta, norm_pop, ans_mod):
    """ans_mod.compute_metrics_per_user 인터페이스에 맞춰 변환."""
    # ans_mod는 run = [{"user_id", "gt_id", "rec_ids"}, ...] 형태
    run = [
        {"user_id": r["user_id"], "gt_id": r["gt_id"], "rec_ids": r["rec_ids"]}
        for r in per_user
    ]
    return ans_mod.compute_metrics_per_user(run, book_meta, norm_pop)


def compute_longtail_pct(per_user, book_meta):
    pcts = []
    for r in per_user:
        recs = r["rec_ids"]
        if not recs:
            continue
        pops = [book_meta.get(rec, {}).get("rating_number", 0) or 0 for rec in recs]
        lt = sum(1 for p in pops if p <= LONGTAIL_THR)
        pcts.append(lt / len(recs))
    return float(np.mean(pcts)) if pcts else 0.0


def paired_bootstrap_ci(deltas, n_iter=10000, ci=0.95, seed=42):
    rng = np.random.default_rng(seed)
    n = len(deltas)
    boots = np.array(
        [rng.choice(deltas, size=n, replace=True).mean() for _ in range(n_iter)]
    )
    lo = float(np.quantile(boots, (1 - ci) / 2))
    hi = float(np.quantile(boots, 1 - (1 - ci) / 2))
    return float(np.mean(deltas)), lo, hi


def main() -> None:
    print("=" * 70)
    print("RQ4 옵션 C — 3단계 vs binary 결정 ablation (정확도 + 다양성)")
    print("=" * 70)
    print()

    # Load fixture + Judge + data
    users, gt_map = load_fixture()
    transfer_map = load_judge_decisions()
    movies = pd.read_parquet(
        ROOT / "data/movies_reviews_filtered.parquet",
        columns=["user_id", "timestamp", "title", "text", "rating"],
    )
    books_reviews = pd.read_parquet(
        ROOT / "data/books_reviews_filtered.parquet",
        columns=["user_id", "parent_asin", "timestamp"],
    )
    print(f"  users: {len(users)}, transfer decisions for {len(transfer_map)} users")

    # Diversity helpers
    print("Loading diversity helpers (book_meta, normalized popularity)...")
    ans_mod = load_diversity_helpers()
    book_meta = ans_mod.load_book_metadata()
    norm_pop = ans_mod.normalized_log_popularity(book_meta)
    print(f"  book_meta loaded: {len(book_meta):,}")

    from sentence_transformers import SentenceTransformer
    print("Loading sentence-transformers...")
    sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    print("  Loaded.\n")

    # Run each variant
    all_variants = {}
    per_user_by_variant = {}
    for variant_name, weights in VARIANTS.items():
        print(f"=== Variant: {variant_name} (weights={weights}) ===")
        t0 = time.time()
        tr.DECISION_WEIGHTS = weights

        signals = {}
        cands = {}
        for uid in users:
            c = json.load(open(ROOT / f"eval_fixtures/candidates/user_{uid}.json"))
            cands[uid] = c
            gt_id = gt_map[uid]["gt_id"]
            utext = build_user_movie_text(uid, gt_id, movies, books_reviews)
            pop, meta, transfer = compute_signals_per_user(
                uid, c, gt_id, utext, transfer_map, sentence_model
            )
            signals[uid] = {"pop": pop, "meta": meta, "transfer": transfer}

        summary, per_user = eval_ranker(
            ALPHA, BETA, GAMMA, users, gt_map, signals, cands
        )

        # Diversity metrics
        div_per_user = compute_diversity_per_user(per_user, book_meta, norm_pop, ans_mod)
        novelty = float(np.mean([x["novelty"] for x in div_per_user]))
        ild = float(np.mean([x["ILD"] for x in div_per_user]))
        lt_pct = compute_longtail_pct(per_user, book_meta)

        elapsed = time.time() - t0
        print(
            f"  → HR@10={summary['HR@10']:.3f}  NDCG@10={summary['NDCG@10']:.4f}  "
            f"MRR={summary['MRR']:.4f}"
        )
        print(
            f"    Novelty={novelty:.4f}  ILD={ild:.4f}  Long-tail%={lt_pct*100:.1f}%  "
            f"({elapsed:.0f}s)"
        )
        print()

        all_variants[variant_name] = {
            "weights": weights,
            "metrics": {
                "HR@10": summary["HR@10"],
                "NDCG@10": summary["NDCG@10"],
                "MRR": summary["MRR"],
                "Novelty": novelty,
                "ILD": ild,
                "LongTail_pct": lt_pct,
            },
        }
        per_user_by_variant[variant_name] = {
            "per_user_accuracy": per_user,
            "per_user_diversity": div_per_user,
        }

    # Paired bootstrap CI: three_level vs each binary variant
    print("=" * 70)
    print("Paired bootstrap 95% CI (3단계 vs binary 변형)")
    print("=" * 70)
    comparisons = {}
    base = per_user_by_variant["three_level"]
    base_acc_list = base["per_user_accuracy"]
    base_div_list = base["per_user_diversity"]
    base_acc = {r["user_id"]: r["metrics"] for r in base_acc_list}
    base_div = {
        base_acc_list[i]["user_id"]: base_div_list[i]
        for i in range(len(base_acc_list))
    }

    for variant in ["binary_aggressive", "binary_conservative"]:
        comp = per_user_by_variant[variant]
        comp_acc_list = comp["per_user_accuracy"]
        comp_div_list = comp["per_user_diversity"]
        comp_acc = {r["user_id"]: r["metrics"] for r in comp_acc_list}
        comp_div = {
            comp_acc_list[i]["user_id"]: comp_div_list[i]
            for i in range(len(comp_acc_list))
        }
        comparisons[f"three_level_vs_{variant}"] = {}

        # Accuracy
        for k in ["HR@10", "NDCG@10", "MRR"]:
            deltas = np.array(
                [base_acc[uid][k] - comp_acc[uid][k] for uid in base_acc]
            )
            mean, lo, hi = paired_bootstrap_ci(deltas)
            sig = "유의 우위" if lo > 0 else "유의 열위" if hi < 0 else "유의차 없음"
            comparisons[f"three_level_vs_{variant}"][k] = {
                "delta_mean": mean, "ci_lower": lo, "ci_upper": hi,
                "significance": sig,
            }
            print(
                f"  {variant} | {k}: Δ={mean:+.4f}  CI=[{lo:+.4f}, {hi:+.4f}]  ({sig})"
            )
        # Diversity
        for k_div in ["novelty", "ILD"]:
            deltas = np.array(
                [base_div[uid][k_div] - comp_div[uid][k_div] for uid in base_div]
            )
            mean, lo, hi = paired_bootstrap_ci(deltas)
            sig = "유의 우위" if lo > 0 else "유의 열위" if hi < 0 else "유의차 없음"
            comparisons[f"three_level_vs_{variant}"][k_div] = {
                "delta_mean": mean, "ci_lower": lo, "ci_upper": hi,
                "significance": sig,
            }
            print(
                f"  {variant} | {k_div}: Δ={mean:+.4f}  CI=[{lo:+.4f}, {hi:+.4f}]  ({sig})"
            )
        print()

    # Save
    result = {
        "experiment": "RQ4 옵션 C — 3단계 vs binary 결정 ablation (정확도 + 다양성)",
        "ranker_config": {"alpha": ALPHA, "beta": BETA, "gamma": GAMMA},
        "n_evaluated": len(users),
        "longtail_threshold": LONGTAIL_THR,
        "variants": all_variants,
        "comparisons": comparisons,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n저장: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
