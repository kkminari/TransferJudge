"""RQ4 ablation chain — A → B → D → C 단계적 비교 + paired bootstrap CI.

각 비교가 측정하는 것:
  A vs B: Profiler 효과 (raw vs 구조화)
  B vs D: Judge decisions 효과 (LLM이 decisions를 활용하는가)
  D vs C: Ranker 분리 효과 (같은 decisions를 LLM vs Ranker가 사용)
  A·B·D vs C: Framework 전체 효과

출력: results/analysis/rq4_ablation_chain_summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT = ROOT / "results/analysis/rq4_ablation_chain_summary.json"

METRICS = ["HR@10", "NDCG@10", "MRR"]


def load_results(path: Path) -> dict:
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


def compare(name_a, name_b, results_a, results_b):
    """results_a - results_b: 양수면 a가 우위."""
    out = {}
    common = sorted(set(results_a.keys()) & set(results_b.keys()))
    for metric in METRICS:
        deltas = np.array(
            [results_a[u][metric] - results_b[u][metric] for u in common]
        )
        mean, lo, hi = paired_bootstrap_ci(deltas)
        sig = "유의 우위" if lo > 0 else "유의 열위" if hi < 0 else "유의차 없음"
        out[metric] = {
            "delta_mean": mean,
            "ci_lower": lo,
            "ci_upper": hi,
            "significance": sig,
            "n_compared": len(deltas),
        }
    return out


def main():
    # Load all 7 results
    paths = {
        "A_4omini": ROOT / "results/analysis/rq4_ablation_framework_A_gpt4omini.json",
        "A_4o": ROOT / "results/analysis/rq4_ablation_framework_A_gpt4o.json",
        "B_4omini": ROOT / "results/analysis/rq4_ablation_framework_B_gpt4omini.json",
        "B_4o": ROOT / "results/analysis/rq4_ablation_framework_B_gpt4o.json",
        "D_4omini": ROOT / "results/analysis/rq4_ablation_framework_D_gpt4omini.json",
        "D_4o": ROOT / "results/analysis/rq4_ablation_framework_D_gpt4o.json",
        "C": ROOT / "results/gamma_sweep/ranker_g0.20.json",
    }
    results = {k: load_results(v) for k, v in paths.items()}
    print(f"All loaded: {[(k, len(v)) for k, v in results.items()]}\n")

    print("=" * 80)
    print("RQ4 Ablation Chain — paired bootstrap 95% CI")
    print("=" * 80)
    print()

    summary = {"comparisons": {}}

    # 1) A vs B (Profiler effect) — pair 같은 모델끼리
    print("=== 1) Profiler 효과 (A vs B, 같은 LLM) ===")
    for llm in ["4omini", "4o"]:
        cmp = compare(f"B_{llm}", f"A_{llm}", results[f"B_{llm}"], results[f"A_{llm}"])
        summary["comparisons"][f"profiler_effect_{llm}"] = cmp
        print(f"  B vs A ({llm}):")
        for m in METRICS:
            c = cmp[m]
            print(f"    {m}: Δ={c['delta_mean']:+.4f}  CI=[{c['ci_lower']:+.4f}, {c['ci_upper']:+.4f}]  ({c['significance']})")

    # 2) B vs D (Judge decisions effect) — 같은 LLM
    print("\n=== 2) Judge decisions 효과 (D vs B, 같은 LLM) ===")
    for llm in ["4omini", "4o"]:
        cmp = compare(f"D_{llm}", f"B_{llm}", results[f"D_{llm}"], results[f"B_{llm}"])
        summary["comparisons"][f"judge_effect_{llm}"] = cmp
        print(f"  D vs B ({llm}):")
        for m in METRICS:
            c = cmp[m]
            print(f"    {m}: Δ={c['delta_mean']:+.4f}  CI=[{c['ci_lower']:+.4f}, {c['ci_upper']:+.4f}]  ({c['significance']})")

    # 3) D vs C (Ranker effect) — D가 LLM에게 decisions를 줬을 때 vs Ranker가 동일 decisions로 점수화
    print("\n=== 3) Ranker 분리 효과 (C vs D, 같은 정보 LLM vs Ranker) ===")
    for llm in ["4omini", "4o"]:
        cmp = compare("C", f"D_{llm}", results["C"], results[f"D_{llm}"])
        summary["comparisons"][f"ranker_effect_vs_D_{llm}"] = cmp
        print(f"  C vs D × {llm}:")
        for m in METRICS:
            c = cmp[m]
            print(f"    {m}: Δ={c['delta_mean']:+.4f}  CI=[{c['ci_lower']:+.4f}, {c['ci_upper']:+.4f}]  ({c['significance']})")

    # 4) Framework 전체 효과 (C vs each LLM-direct variant)
    print("\n=== 4) Framework 전체 효과 (C vs A/B/D × 2 LLM) ===")
    for v in ["A_4omini", "A_4o", "B_4omini", "B_4o", "D_4omini", "D_4o"]:
        cmp = compare("C", v, results["C"], results[v])
        summary["comparisons"][f"framework_vs_{v}"] = cmp
        print(f"  C vs {v}:")
        for m in METRICS:
            c = cmp[m]
            sig_mark = "★" if c["ci_lower"] > 0 else ""
            print(f"    {m}: Δ={c['delta_mean']:+.4f}  CI=[{c['ci_lower']:+.4f}, {c['ci_upper']:+.4f}]  ({c['significance']}) {sig_mark}")

    # Save
    summary["raw_results"] = {
        k: {"n": len(v), "mean_metrics": {
            m: float(np.mean([v[u][m] for u in v])) for m in METRICS
        }} for k, v in results.items()
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n저장: {OUTPUT}")


if __name__ == "__main__":
    main()
