"""Phase 4 — Single LLM·Prompt-only·Raw Review·전통 CDR baseline 실행 (골격).

각 조건은 다른 추론 흐름:
  (a) Single LLM    — GPT-4o-mini 직접 (Profile 없음)
  (b) Prompt-only   — GPT-4o-mini + Profile (학습 없음)
  (e) Traditional CDR — EMCDR or CoNet
  (f) Raw Review    — Qwen3-14B (Profile 없이 학습)

사용법:
    python3 scripts/run_ablation.py --condition a_single --output results/ablation_a_single.json
    python3 scripts/run_ablation.py --condition b_prompt --output results/ablation_b_prompt.json
    python3 scripts/run_ablation.py --condition e_traditional --output results/ablation_e_traditional.json
    python3 scripts/run_ablation.py --condition f_raw --output results/ablation_f_raw.json

설계 참고: docs/phase4/Phase4_Evaluation_Plan.pdf §1, §3.2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


CONDITION_FLOWS = {
    "a_single": "GPT-4o-mini가 raw 영화 리뷰 30개를 직접 보고 Top-10 추천 (Profile 없음, 학습 없음)",
    "b_prompt": "GPT-4o-mini가 Profile JSON을 보고 transfer_decisions + Top-10 추천 (학습 없음)",
    "e_traditional": "EMCDR 또는 CoNet (matrix factorization 기반 cross-domain)",
    "f_raw": "Qwen3-14B를 raw 영화 리뷰로 학습 후 추천 (Profile 없음)",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", type=str, required=True,
                        choices=list(CONDITION_FLOWS.keys()))
    parser.add_argument("--test-users", type=Path, default=Path("data/test_users.parquet"))
    parser.add_argument("--profiles", type=Path, default=Path("profiler_outputs"),
                        help="(b) Prompt-only에서만 사용")
    parser.add_argument("--movies-reviews", type=Path,
                        default=Path("data/movies_reviews_filtered.parquet"))
    parser.add_argument("--books-reviews", type=Path,
                        default=Path("data/books_reviews_filtered.parquet"))
    parser.add_argument("--books-meta", type=Path,
                        default=Path("data/books_meta_filtered.parquet"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n-candidates", type=int, default=50)
    args = parser.parse_args()

    print(f"=== Phase 4 Ablation: {args.condition} ===")
    print(f"  설명: {CONDITION_FLOWS[args.condition]}")
    print()
    print("⚠ 이 스크립트는 골격. 각 condition별 구현 필요:")

    if args.condition == "a_single":
        print("""
  (a) Single LLM 구현:
    1. test_users 100명 로드
    2. 각 사용자별:
       - movies_reviews_filtered.parquet에서 영화 리뷰 30개 (GT 시점 이전)
       - books_meta에서 50권 후보 sample (seed=42, GT 포함)
       - GPT-4o-mini API call:
         system: "You are a book recommender..."
         user: "[영화 리뷰 30개] + [후보 50권] + 'Recommend Top-10'"
       - 출력 JSON 파싱 + 메트릭 계산
    3. results/ablation_a_single.json 저장
""")
    elif args.condition == "b_prompt":
        print("""
  (b) Prompt-only 구현:
    1. test_users 100명 로드
    2. 각 사용자별:
       - profiler_outputs/user_{uid}.json 로드
       - 후보 50권 sample
       - GPT-4o-mini API call (학습된 prompt + Profile + 후보)
         단, 본 연구의 train_judge.py와 다른 점:
           - 학습이 없으므로 transfer_decisions 일관성 ↓ 예상
           - assistant_only_loss 효과 없음
       - 출력 + 메트릭
    3. results/ablation_b_prompt.json 저장
""")
    elif args.condition == "e_traditional":
        print("""
  (e) Traditional CDR 구현:
    1. EMCDR 또는 CoNet 구현 — 가장 단순한 EMCDR 추천:
       - User-Movie rating matrix + User-Book rating matrix
       - Matrix factorization → user/item latent vector
       - Cross-domain mapping (mlp)
    2. 학습 + 평가 동일 데이터셋 사용 (train 578, test 100)
    3. results/ablation_e_traditional.json 저장
       (실제 구현은 https://github.com/Songweiping/EMCDR-pytorch 참고)
""")
    elif args.condition == "f_raw":
        print("""
  (f) Raw Review 구현:
    1. 학습 데이터 재구성:
       - 기존 teacher_train_main.jsonl의 system/user 메시지에서 Profile JSON 제거
       - 영화 리뷰 텍스트를 직접 user 메시지로
       - assistant 출력은 동일 (transfer_decisions + Top-10)
    2. Qwen3-14B QLoRA 재학습 (별도 adapter)
    3. test_users 100명에 대해 추론 + 메트릭
    4. results/ablation_f_raw.json 저장
""")

    print()
    print("TODO: 각 condition별 구현 후 결과 JSON 저장")
    print(f"      형식: docs/phase4/Phase4_Metrics.md §7 참조")


if __name__ == "__main__":
    main()
