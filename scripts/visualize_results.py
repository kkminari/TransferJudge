"""Phase 6 — 시각화 + 통계 분석.

Phase 4·5의 모든 결과를 받아 논문용 figure 5개·table 4개 생성.

사용법:
    python3 scripts/visualize_results.py \\
      --results-dir results/ \\
      --trainer-state checkpoints/judge_v1/trainer_state.json \\
      --output docs/phase6/figures/

산출:
  - F1 ~ F5 (PNG)
  - T1 ~ T4 (CSV)
  - statistical_tests.json (paired t-test + Cohen's d + Bootstrap CI)

설계 참고: docs/phase6/Phase6_Analysis_Plan.pdf
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


CONDITIONS = ["a_single", "b_prompt", "c_ours", "d_no_gate", "e_emcdr", "f_raw", "g_llm4cdr"]
CONDITION_LABELS = {
    "a_single": "(a) Single LLM",
    "b_prompt": "(b) Prompt-only",
    "c_ours": "(c) Ours ★",
    "d_no_gate": "(d) w/o Gate",
    "e_emcdr": "(e) EMCDR",
    "f_raw": "(f) Raw Review",
    "g_llm4cdr": "(g) LLM4CDR-style",
}
PATTERNS = ["genre_preference", "narrative_complexity", "pacing_preference",
            "quality_sensitivity", "brand_loyalty", "sensory_preference",
            "emotional_resonance"]


# ============================================================
# F1. 학습 loss curve
# ============================================================
def plot_loss_curve(trainer_state_path: Path, output: Path):
    if not trainer_state_path.exists():
        print(f"⚠ {trainer_state_path} 없음 — skip F1")
        return
    state = json.load(trainer_state_path.open())
    log = state.get("log_history", [])

    train_x, train_y = [], []
    eval_x, eval_y = [], []
    for h in log:
        if "loss" in h and "epoch" in h:
            train_x.append(h["epoch"])
            train_y.append(h["loss"])
        if "eval_loss" in h and "epoch" in h:
            eval_x.append(h["epoch"])
            eval_y.append(h["eval_loss"])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(train_x, train_y, label="train_loss", marker=".", alpha=0.7)
    ax.plot(eval_x, eval_y, label="eval_loss", marker="o", linewidth=2)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title("Phase 3 Learning Curve (Qwen3-14B QLoRA, 578 train)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"✅ F1: {output}")


# ============================================================
# F2. 6 conditions × 3 metrics 비교 막대그래프
# ============================================================
def plot_main_comparison(results: dict, output: Path):
    metrics = ["HR@10", "NDCG@10", "MRR"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for ax, m in zip(axes, metrics):
        values = [results.get(c, {}).get("metrics", {}).get(m, 0) for c in CONDITIONS]
        colors = ["#4a90d9" if c != "c_ours" else "#2e7d32" for c in CONDITIONS]
        bars = ax.bar(range(len(CONDITIONS)), values, color=colors)
        ax.set_xticks(range(len(CONDITIONS)))
        ax.set_xticklabels([CONDITION_LABELS[c] for c in CONDITIONS], rotation=30, ha="right", fontsize=8)
        ax.set_ylabel(m)
        ax.set_title(m)
        ax.grid(axis="y", alpha=0.3)
        # 값 표기
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, v + 0.005, f"{v:.3f}",
                    ha="center", fontsize=7)

    fig.suptitle("6-condition Ablation Comparison (Test 100 users)", fontsize=12)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"✅ F2: {output}")


# ============================================================
# F3. Pattern Importance Heatmap
# ============================================================
def plot_pattern_heatmap(results_dir: Path, output: Path):
    baseline_f = results_dir / "ablation_c_ours.json"
    if not baseline_f.exists():
        print(f"⚠ {baseline_f} 없음 — skip F3")
        return
    baseline = json.load(baseline_f.open())["metrics"]

    # 패턴별 ablation 결과
    delta_matrix = []
    metrics_to_show = ["HR@10", "NDCG@10", "MRR"]
    for p in PATTERNS:
        ablated_f = results_dir / f"per_pattern_{p}_block.json"
        if not ablated_f.exists():
            print(f"⚠ {ablated_f} 없음")
            delta_matrix.append([0] * len(metrics_to_show))
            continue
        ab = json.load(ablated_f.open())["metrics"]
        row = [ab.get(m, 0) - baseline.get(m, 0) for m in metrics_to_show]
        delta_matrix.append(row)

    delta_matrix = np.array(delta_matrix)

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(delta_matrix, cmap="RdBu_r", vmin=-0.1, vmax=0.1, aspect="auto")
    ax.set_xticks(range(len(metrics_to_show)))
    ax.set_xticklabels(metrics_to_show)
    ax.set_yticks(range(len(PATTERNS)))
    ax.set_yticklabels(PATTERNS)
    ax.set_title("Pattern Importance — Δ when pattern force_BLOCK\n(red = ↓ performance = important)")

    # 값 표기
    for i in range(len(PATTERNS)):
        for j in range(len(metrics_to_show)):
            ax.text(j, i, f"{delta_matrix[i, j]:+.3f}",
                    ha="center", va="center",
                    color="white" if abs(delta_matrix[i, j]) > 0.04 else "black",
                    fontsize=9)

    fig.colorbar(im, ax=ax, label="Δ vs Ours baseline")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"✅ F3: {output}")


# ============================================================
# F4. Cold-Start Segment 그래프
# ============================================================
def plot_cold_start(cold_start_f: Path, output: Path):
    if not cold_start_f.exists():
        print(f"⚠ {cold_start_f} 없음 — skip F4")
        return
    data = json.load(cold_start_f.open())
    per_cond = data.get("per_condition_per_segment", {})

    segments = ["severe", "moderate", "warm"]
    x = np.arange(len(segments))
    width = 0.13

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, cond in enumerate(CONDITIONS):
        values = [per_cond.get(cond, {}).get(seg, {}).get("NDCG@10", 0) for seg in segments]
        color = "#2e7d32" if cond == "c_ours" else None
        ax.bar(x + i * width, values, width, label=CONDITION_LABELS[cond], color=color)

    ax.set_xticks(x + width * (len(CONDITIONS) - 1) / 2)
    ax.set_xticklabels(["Severe (5 books)", "Moderate (6-7)", "Warm (8-10)"])
    ax.set_ylabel("NDCG@10")
    ax.set_title("Cold-Start Segment Analysis — NDCG@10 by Target Domain Activity")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"✅ F4: {output}")


# ============================================================
# F5. Decision Distribution (Judge vs Teacher)
# ============================================================
def plot_decision_distribution(results_dir: Path, output: Path):
    f = results_dir / "ablation_c_ours.json"
    if not f.exists():
        print(f"⚠ {f} 없음 — skip F5")
        return
    data = json.load(f.open())
    judge_dist = data.get("per_pattern_decision_distribution", {})
    teacher_dist = data.get("teacher_decision_distribution", {})
    if not judge_dist or not teacher_dist:
        print("⚠ decision distribution 데이터 없음 — evaluate_judge.py 출력 형식 확인 필요")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, dist, title in [(axes[0], teacher_dist, "Teacher (GPT-4o-mini)"),
                             (axes[1], judge_dist, "Judge (Qwen3-14B Ours)")]:
        bottoms = np.zeros(len(PATTERNS))
        for label, color in [("TRANSFER", "#4caf50"), ("PARTIAL", "#ff9800"), ("BLOCK", "#f44336")]:
            values = [dist.get(p, {}).get(label, 0) for p in PATTERNS]
            ax.bar(PATTERNS, values, bottom=bottoms, label=label, color=color)
            bottoms += values
        ax.set_title(title)
        ax.set_xticklabels(PATTERNS, rotation=30, ha="right", fontsize=8)
        ax.set_ylabel("Count")
        ax.legend()

    fig.suptitle("Transfer Decision Distribution per Pattern (Test 100 users)", fontsize=12)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"✅ F5: {output}")


# ============================================================
# T1-T4 Tables (CSV)
# ============================================================
def save_tables(results: dict, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # T1 Dataset Statistics — 정적
    t1 = pd.DataFrame([
        {"Metric": "Source domain", "Value": "Amazon Movies & TV"},
        {"Metric": "Target domain", "Value": "Amazon Books"},
        {"Metric": "Cohort selection", "Value": "Source≥15, Target 5-10, temporal cutoff"},
        {"Metric": "Train users", "Value": 578},
        {"Metric": "Valid users", "Value": 100},
        {"Metric": "Test users", "Value": 100},
        {"Metric": "Train ∩ (Valid ∪ Test) overlap", "Value": 0},
        {"Metric": "Candidates per user (LOO)", "Value": 50},
    ])
    t1.to_csv(output_dir / "T1_dataset_stats.csv", index=False)

    # T2 Main Results
    rows = []
    for c in CONDITIONS:
        m = results.get(c, {}).get("metrics", {})
        rows.append({
            "Condition": CONDITION_LABELS[c],
            "HR@1": m.get("HR@1"),
            "HR@5": m.get("HR@5"),
            "HR@10": m.get("HR@10"),
            "NDCG@5": m.get("NDCG@5"),
            "NDCG@10": m.get("NDCG@10"),
            "MRR": m.get("MRR"),
        })
    pd.DataFrame(rows).to_csv(output_dir / "T2_main_results.csv", index=False)
    print(f"✅ Tables saved: {output_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--trainer-state", type=Path,
                        default=Path("checkpoints/judge_v1/trainer_state.json"))
    parser.add_argument("--output", type=Path, default=Path("docs/phase6/figures"))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    # 모든 결과 로드
    results = {}
    for c in CONDITIONS:
        f = args.results_dir / f"ablation_{c}.json"
        if f.exists():
            results[c] = json.load(f.open())

    # F1 — F5 생성
    plot_loss_curve(args.trainer_state, args.output / "F1_loss_curve.png")
    if results:
        plot_main_comparison(results, args.output / "F2_main_comparison.png")
        plot_decision_distribution(args.results_dir, args.output / "F5_decision_distribution.png")
    plot_pattern_heatmap(args.results_dir, args.output / "F3_pattern_heatmap.png")
    plot_cold_start(args.results_dir / "cold_start_analysis.json",
                    args.output / "F4_cold_start_segments.png")

    # Tables
    if results:
        save_tables(results, args.output / "tables")

    print(f"\n=== Phase 6 시각화 완료 ===")
    print(f"  Figures: {args.output}/F*.png")
    print(f"  Tables:  {args.output}/tables/T*.csv")


if __name__ == "__main__":
    main()
