"""RQ1 보강 — Pre-FT vs Post-FT decision agreement 비교 분석.

본 스크립트는 RunPod에서 생성된 pre-FT 결과를 받아 Mac에서 분석.

입력:
  - results/analysis/rq1_pre_ft_qwen_zero_shot.json  (RunPod 결과)
  - results/analysis/rq1_pre_ft_qwen_few_shot.json   (RunPod 결과)
  - teacher_outputs/user_{uid}.json                  (Teacher decisions, GT 정답 라벨)
  - results/ablation_c_ours.json                     (Post-FT Student decisions, 본 연구)

출력:
  - results/analysis/rq1_compare_pre_post_ft.json
  - Overall accuracy / Macro-F1 / per-class F1 (TRANSFER/PARTIAL/BLOCK)
  - Confusion matrix
  - JSON format success rate
  - 7-pattern completeness

실행:
    .venv_thesis/bin/python scripts/analysis/rq1_compare_pre_post_ft.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = ROOT / "results/analysis/rq1_compare_pre_post_ft.json"

PATTERNS = [
    "genre_preference",
    "narrative_complexity",
    "pacing_preference",
    "quality_sensitivity",
    "brand_loyalty",
    "sensory_preference",
    "emotional_resonance",
]
LABELS = ["TRANSFER", "PARTIAL", "BLOCK"]


def load_pre_ft(path: Path) -> dict:
    """RunPod 출력 → user_id → pattern → decision."""
    out = {}
    if not path.exists():
        return out
    data = json.loads(path.read_text())
    for r in data.get("per_user", []):
        out[r["user_id"]] = r.get("decision_pattern", {})
    return out


def load_teacher_decisions() -> dict:
    """Teacher 결정 (정답 라벨)."""
    teacher_dir = ROOT / "teacher_outputs"
    out = {}
    for f in teacher_dir.glob("user_*.json"):
        uid = f.stem.replace("user_", "")
        try:
            d = json.loads(f.read_text())
            td = d.get("transfer_decisions", {})
            out[uid] = {p: td[p]["decision"] for p in PATTERNS if p in td}
        except Exception:
            pass
    return out


def load_post_ft() -> dict:
    """본 연구 fine-tuned Student decisions."""
    path = ROOT / "results/ablation_c_ours.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    out = {}
    for r in data.get("per_user", []):
        uid = r["user_id"]
        td = r.get("transfer_decisions", {})
        out[uid] = {p: td[p]["decision"] for p in PATTERNS if p in td}
    return out


def compute_metrics(pred: dict, gold: dict, label_name: str) -> dict:
    """pred·gold: {uid: {pattern: decision}}. Teacher 정답 대비 metrics."""
    y_true, y_pred = [], []
    fmt_success = 0
    n_total = 0
    completeness_counts = []
    for uid, gold_dec in gold.items():
        if uid not in pred:
            continue
        pred_dec = pred[uid]
        if pred_dec:
            fmt_success += 1
        completeness = sum(1 for p in PATTERNS if p in pred_dec) / len(PATTERNS)
        completeness_counts.append(completeness)
        for p in PATTERNS:
            if p in gold_dec and p in pred_dec:
                y_true.append(gold_dec[p])
                y_pred.append(pred_dec[p])
                n_total += 1

    if not y_true:
        return {"error": "no overlapping users with decisions"}

    report = classification_report(
        y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=LABELS).tolist()

    return {
        "label": label_name,
        "n_users_with_decisions": fmt_success,
        "n_decisions_compared": n_total,
        "format_success_rate": fmt_success / max(len(gold), 1),
        "7pattern_completeness_mean": float(np.mean(completeness_counts))
        if completeness_counts
        else 0.0,
        "overall_accuracy": report["accuracy"],
        "macro_f1": report["macro avg"]["f1-score"],
        "weighted_f1": report["weighted avg"]["f1-score"],
        "per_class": {
            lbl: {
                "precision": report.get(lbl, {}).get("precision", 0),
                "recall": report.get(lbl, {}).get("recall", 0),
                "f1": report.get(lbl, {}).get("f1-score", 0),
                "support": report.get(lbl, {}).get("support", 0),
            }
            for lbl in LABELS
        },
        "confusion_matrix": {
            "rows_true": LABELS,
            "cols_pred": LABELS,
            "matrix": cm,
        },
    }


def main() -> None:
    print("=" * 70)
    print("RQ1 보강 — Pre-FT vs Post-FT vs Teacher 비교")
    print("=" * 70)

    teacher = load_teacher_decisions()
    print(f"\nTeacher users: {len(teacher)}")

    pre_ft_zs = load_pre_ft(ROOT / "results/analysis/rq1_pre_ft_qwen_zero_shot.json")
    pre_ft_fs = load_pre_ft(ROOT / "results/analysis/rq1_pre_ft_qwen_few_shot.json")
    post_ft = load_post_ft()
    print(
        f"Pre-FT zero-shot: {len(pre_ft_zs)}\n"
        f"Pre-FT few-shot: {len(pre_ft_fs)}\n"
        f"Post-FT (본 연구): {len(post_ft)}"
    )

    result = {
        "comparison": "Pre-FT vs Post-FT Qwen3-14B, Teacher decisions as gold",
        "labels": LABELS,
        "patterns": PATTERNS,
    }

    for name, pred in [
        ("pre_ft_zero_shot", pre_ft_zs),
        ("pre_ft_few_shot", pre_ft_fs),
        ("post_ft_ours", post_ft),
    ]:
        if not pred:
            print(f"\n[skip] {name}: 결과 파일 없음")
            continue
        metrics = compute_metrics(pred, teacher, name)
        result[name] = metrics

        print(f"\n=== {name} ===")
        if "error" in metrics:
            print(f"  {metrics['error']}")
            continue
        print(f"  format success: {metrics['format_success_rate']*100:.1f}%")
        print(f"  7-pattern completeness: {metrics['7pattern_completeness_mean']*100:.1f}%")
        print(f"  overall accuracy: {metrics['overall_accuracy']*100:.1f}%")
        print(f"  macro-F1: {metrics['macro_f1']:.3f}")
        for lbl in LABELS:
            pc = metrics["per_class"][lbl]
            print(
                f"  {lbl}: precision={pc['precision']:.3f}  "
                f"recall={pc['recall']:.3f}  F1={pc['f1']:.3f}  n={pc['support']}"
            )

    # 비교 표 (overall accuracy 차이)
    if "pre_ft_zero_shot" in result and "post_ft_ours" in result:
        delta = (
            result["post_ft_ours"]["overall_accuracy"]
            - result["pre_ft_zero_shot"]["overall_accuracy"]
        )
        result["comparison_summary"] = {
            "post_ft_vs_pre_ft_zero_shot_delta": delta,
            "interpretation": (
                f"Post-FT가 Pre-FT zero-shot 대비 overall accuracy "
                f"{'유의' if abs(delta) > 0.05 else '미미'} 차이 ({delta:+.3f})"
            ),
        }
        print(f"\n=== 종합 ===")
        print(f"  Post-FT vs Pre-FT zero-shot: Δ accuracy = {delta:+.3f}")

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n저장: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
