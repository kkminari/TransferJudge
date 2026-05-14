"""Phase 5b — Cold-Start Segment 분석.

Phase 4의 6개 조건 결과를 test 사용자별 Books 활동량으로 segment 나눠
Severe/Moderate/Warm 비교.

사용법:
    python3 scripts/cold_start_analysis.py \\
      --results-dir results/ \\
      --test-users data/test_users.parquet \\
      --output results/cold_start_analysis.json

설계 참고: docs/phase5/Phase5_Ablation_Plan.pdf §2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np


SEGMENT_DEF = {
    "severe": (5, 5),     # books_count == 5
    "moderate": (6, 7),   # 6~7
    "warm": (8, 10),      # 8~10
}


def classify_segment(book_count: int) -> str:
    for seg, (lo, hi) in SEGMENT_DEF.items():
        if lo <= book_count <= hi:
            return seg
    return "unknown"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--test-users", type=Path, default=Path("data/test_users.parquet"))
    parser.add_argument("--output", type=Path, default=Path("results/cold_start_analysis.json"))
    args = parser.parse_args()

    # Test users + segment 할당
    test_df = pd.read_parquet(args.test_users)
    test_df["segment"] = test_df["book_count"].apply(classify_segment)
    print(f"Test segment 분포:")
    print(test_df["segment"].value_counts())
    print()

    # 각 ablation 결과 파일 로드
    conditions = ["a_single", "b_prompt", "c_ours", "d_no_gate", "e_traditional", "f_raw"]
    all_results = {}

    for cond in conditions:
        f = args.results_dir / f"ablation_{cond}.json"
        if not f.exists():
            print(f"⚠ {f} 없음 — skip (해당 조건 아직 미실행)")
            continue
        data = json.load(f.open())
        all_results[cond] = data

    if not all_results:
        print("❌ 결과 파일이 없습니다. Phase 4 실행 후 다시 시도하세요.")
        return

    # Per-user predictions 로드 (segment별 metric 계산용)
    pred_f = args.results_dir / "per_user_predictions.jsonl"
    if not pred_f.exists():
        print(f"⚠ {pred_f} 없음 — 본격 분석 불가. evaluate_judge.py 출력 형식 확인 필요.")
        print("  형식: {user_id, condition, rec_ids, gt_id, HR@10, NDCG@10, ...}")
        return

    per_user = []
    for line in pred_f.open():
        per_user.append(json.loads(line))
    per_user_df = pd.DataFrame(per_user)
    per_user_df = per_user_df.merge(test_df[["user_id", "segment"]], on="user_id")

    # Condition × Segment 집계
    print("\n=== Cold-Start Segment 분석 결과 ===")
    summary = {}
    for cond in all_results:
        cond_df = per_user_df[per_user_df["condition"] == cond]
        summary[cond] = {}
        for seg in ["severe", "moderate", "warm"]:
            seg_df = cond_df[cond_df["segment"] == seg]
            if len(seg_df) == 0:
                continue
            summary[cond][seg] = {
                "n": int(len(seg_df)),
                "HR@10": float(seg_df["HR@10"].mean()),
                "NDCG@10": float(seg_df["NDCG@10"].mean()),
                "MRR": float(seg_df["MRR"].mean()),
            }
        # Severe/Warm ratio
        sev = summary[cond].get("severe", {})
        warm = summary[cond].get("warm", {})
        if sev and warm and warm.get("NDCG@10", 0) > 0:
            summary[cond]["severe_warm_ratio"] = sev["NDCG@10"] / warm["NDCG@10"]

    # 출력
    output = {
        "segment_definition": {k: f"{v[0]}-{v[1]} books" for k, v in SEGMENT_DEF.items()},
        "test_segment_distribution": test_df["segment"].value_counts().to_dict(),
        "per_condition_per_segment": summary,
    }
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n✅ Saved: {args.output}")

    # 콘솔 표 출력
    print("\n" + "=" * 70)
    print(f"{'Condition':<20} {'Severe (n)':<15} {'Moderate (n)':<15} {'Warm (n)':<15} {'S/W':<10}")
    print("-" * 70)
    for cond, segs in summary.items():
        sev = segs.get("severe", {})
        mod = segs.get("moderate", {})
        warm = segs.get("warm", {})
        sw = segs.get("severe_warm_ratio", "-")
        sw_str = f"{sw:.2f}" if isinstance(sw, (int, float)) else sw
        print(f"{cond:<20} "
              f"{sev.get('NDCG@10', '-'):<10.3f} ({sev.get('n', '-')})  "
              f"{mod.get('NDCG@10', '-'):<10.3f} ({mod.get('n', '-')})  "
              f"{warm.get('NDCG@10', '-'):<10.3f} ({warm.get('n', '-')})  "
              f"{sw_str:<10}")


if __name__ == "__main__":
    main()
