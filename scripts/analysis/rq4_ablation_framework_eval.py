"""RQ4 framework ablation 종합 분석 — paired bootstrap 95% CI vs 본 연구 C.

입력:
  - results/analysis/rq4_ablation_framework_{A|B}_{gpt4o|gpt4omini}.json (4개 변형)
  - results/ablation_c_ours.json (본 연구 C)

출력:
  - results/analysis/rq4_ablation_framework_summary.json
  - 콘솔: 변형별 vs C 비교 + paired bootstrap 95% CI
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = ROOT / "results/analysis/rq4_ablation_framework_summary.json"

VARIANTS = [
    ("A_gpt4omini", "A. Raw 리뷰 × gpt-4o-mini"),
    ("A_gpt4o", "A. Raw 리뷰 × gpt-4o"),
    ("B_gpt4omini", "B. Profile만 × gpt-4o-mini"),
    ("B_gpt4o", "B. Profile만 × gpt-4o"),
    ("D_gpt4omini", "D. Profile + Judge decisions × gpt-4o-mini"),
    ("D_gpt4o", "D. Profile + Judge decisions × gpt-4o"),
]

METRICS = ["HR@10", "NDCG@10", "MRR"]


def load_results(path: Path) -> dict:
    """JSON 결과 → {user_id: metrics}."""
    data = json.loads(path.read_text())
    return {r["user_id"]: r["metrics"] for r in data["per_user"]}


def paired_bootstrap_ci(deltas, n_iter=10000, ci=0.95, seed=42):
    rng = np.random.default_rng(seed)
    n = len(deltas)
    boots = np.array(
        [rng.choice(deltas, size=n, replace=True).mean() for _ in range(n_iter)]
    )
    lo = float(np.quantile(boots, (1 - ci) / 2))
    hi = float(np.quantile(boots, 1 - (1 - ci) / 2))
    return float(np.mean(deltas)), lo, hi


def main():
    print("=" * 78)
    print("RQ4 framework ablation — paired bootstrap 95% CI (vs 본 연구 C)")
    print("=" * 78)
    print()

    # Load C (본 연구 TransferJudge γ=0.20 — Profile→Judge→Ranker)
    # ablation_c_ours.json은 LLM-direct(Qwen3-14B 직접 출력)이므로 X
    # 실제 본 연구는 gamma_sweep/ranker_g0.20.json (transfer-aware ranker)
    c_path = ROOT / "results/gamma_sweep/ranker_g0.20.json"
    c_results = load_results(c_path)
    print(f"C (TransferJudge γ=0.20, Profile→Judge→Ranker): {len(c_results)} users")

    # Load each variant
    summary = {
        "experiment": "RQ4 Framework Ablation — vs 본 연구 C",
        "n_users": len(c_results),
        "variants": {},
        "comparisons": {},
    }

    for vname, vlabel in VARIANTS:
        path = ROOT / f"results/analysis/rq4_ablation_framework_{vname}.json"
        v_data = json.loads(path.read_text())
        v_results = load_results(path)
        summary["variants"][vname] = {
            "label": vlabel,
            "n": v_data["n_evaluated"],
            "metrics": v_data["summary"],
            "cost_usd": v_data["cost"]["cost_usd"],
        }

        # paired bootstrap CI: C - variant (양수 = C 우위)
        print(f"\n=== C vs {vlabel} ===")
        comp = {}
        for metric in METRICS:
            common = set(c_results.keys()) & set(v_results.keys())
            deltas = np.array(
                [c_results[u][metric] - v_results[u][metric] for u in sorted(common)]
            )
            mean, lo, hi = paired_bootstrap_ci(deltas)
            sig = "유의 우위" if lo > 0 else "유의 열위" if hi < 0 else "유의차 없음"
            comp[metric] = {
                "delta_mean": mean, "ci_lower": lo, "ci_upper": hi,
                "significance": sig,
                "n_compared": len(deltas),
            }
            print(
                f"  {metric}: Δ={mean:+.4f}  CI=[{lo:+.4f}, {hi:+.4f}]  ({sig})"
            )
        summary["comparisons"][f"C_vs_{vname}"] = comp

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n저장: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
