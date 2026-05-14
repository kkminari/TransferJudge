"""Phase 5a — Per-Pattern Ablation (골격).

7개 패턴 각각을 강제 BLOCK 또는 강제 TRANSFER로 만들어 Judge 추론.
목적: 패턴별 중요도 + negative transfer 검증.

사용법:
    # 7개 패턴 각각 force_block
    for p in genre_preference narrative_complexity pacing_preference \\
             quality_sensitivity brand_loyalty sensory_preference \\
             emotional_resonance; do
        python3 scripts/per_pattern_ablation.py \\
          --adapter checkpoints/judge_v1/adapter \\
          --ablate-pattern $p --mode force_block \\
          --output results/per_pattern_${p}_block.json
    done

    # brand_loyalty 강제 TRANSFER (negative transfer 검증)
    python3 scripts/per_pattern_ablation.py \\
      --adapter checkpoints/judge_v1/adapter \\
      --ablate-pattern brand_loyalty --mode force_transfer \\
      --output results/per_pattern_brand_force_transfer.json

설계 참고: docs/phase5/Phase5_Ablation_Plan.pdf §1
"""
from __future__ import annotations

import argparse
from pathlib import Path


PATTERNS = ["genre_preference", "narrative_complexity", "pacing_preference",
            "quality_sensitivity", "brand_loyalty", "sensory_preference",
            "emotional_resonance"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--ablate-pattern", type=str, required=True, choices=PATTERNS)
    parser.add_argument("--mode", type=str, default="force_block",
                        choices=["force_block", "force_transfer"])
    parser.add_argument("--test-users", type=Path, default=Path("data/test_users.parquet"))
    parser.add_argument("--profiles", type=Path, default=Path("profiler_outputs"))
    parser.add_argument("--books-meta", type=Path, default=Path("data/books_meta_filtered.parquet"))
    parser.add_argument("--books-reviews", type=Path, default=Path("data/books_reviews_filtered.parquet"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    print(f"=== Per-Pattern Ablation: {args.ablate_pattern} ({args.mode}) ===")
    print()
    print("구현 방식 (Phase 3 학습 완료 후 채움):")
    print(f"""
    1. Judge inference 시 system prompt에 다음 지시 추가:
       'For the pattern "{args.ablate_pattern}", you MUST set its decision to
        "{args.mode.replace('force_', '').upper()}", regardless of Profile evidence.'

    2. 또는 inference 후 post-process:
       - generated_output['transfer_decisions']['{args.ablate_pattern}']['decision']을
         "{args.mode.replace('force_', '').upper()}"로 강제 override
       - 만약 BLOCK으로 override되면 추천 재계산 (해당 패턴을 applied_patterns에서 제거)
       - TRANSFER로 override되면 해당 패턴이 추천에 영향 주도록 prompt-side에서 활성화

    3. evaluate_judge.py와 동일한 메트릭 계산
       (HR@k, NDCG@k, MRR, JSONValid 등)

    4. results/per_pattern_{args.ablate_pattern}_{args.mode}.json 형식 저장:
       {{
         "condition": "per_pattern_{args.ablate_pattern}_{args.mode}",
         "n_users": 100,
         "metrics": {{...}},
         "delta_vs_baseline": {{
           "HR@10": -0.02,
           "NDCG@10": -0.03,
           ...
         }}
       }}
    """)
    print()
    print("TODO: evaluate_judge.py 완성 후 본 스크립트의 inference 부분 공유 구조로 구현")


if __name__ == "__main__":
    main()
