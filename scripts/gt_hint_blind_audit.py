"""GT hint Blind Audit — Codex 이전 권장사항.

목적: GT 힌트를 Teacher에 주는 설계가 학술적으로 정당한지 검증.
방법: 30명에 대해 GT 힌트 없이 Teacher 실행 → decision 분포 비교.

가설:
  - GT hint 없이도 Teacher의 transfer_decisions 분포가 거의 동일하면
    → "GT hint는 Top-10 정렬에만 영향, 패턴 판단 자체는 독립적" 증명
  - 분포가 크게 다르면 → oracle leakage 가능성, 한계로 명시

사용법:
    export OPENAI_API_KEY=...
    python3 scripts/gt_hint_blind_audit.py \\
      --n-users 30 \\
      --output results/gt_hint_blind_audit.json
"""
from __future__ import annotations

import argparse
import json
import os
import random
from collections import Counter
from pathlib import Path

import pandas as pd


PATTERNS = ["genre_preference", "narrative_complexity", "pacing_preference",
            "quality_sensitivity", "brand_loyalty", "sensory_preference",
            "emotional_resonance"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-users", type=int, default=30,
                        help="Audit 대상 사용자 수")
    parser.add_argument("--training-data", type=Path,
                        default=Path("data/teacher_train_main.jsonl"),
                        help="원본 Teacher 결과 (with GT hint)")
    parser.add_argument("--teacher-outputs", type=Path,
                        default=Path("teacher_outputs_v1"),
                        help="원본 Teacher JSON")
    parser.add_argument("--profiles", type=Path,
                        default=Path("profiler_outputs"))
    parser.add_argument("--books-meta", type=Path,
                        default=Path("data/books_meta_filtered.parquet"))
    parser.add_argument("--books-reviews", type=Path,
                        default=Path("data/books_reviews_filtered.parquet"))
    parser.add_argument("--output", type=Path,
                        default=Path("results/gt_hint_blind_audit.json"))
    parser.add_argument("--seed", type=int, default=2030)
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경변수 설정 필요")
        return

    print(f"=== GT hint Blind Audit (n={args.n_users}) ===")
    print()
    print("이 스크립트는 학습 데이터에 포함된 사용자 30명 sample을 골라")
    print("GT 힌트 없이 Teacher를 재실행하고, 원본(with GT hint)과 decision 분포를 비교함.")
    print()
    print("실행 흐름 (TODO 코드 완성):")
    print("""
    1. training_data에서 user_id 30명 random sample (seed=2030)
    2. 각 사용자별:
       a) teacher_outputs_v1/user_{uid}.json 로드 (원본, with GT hint)
       b) 후보 50권 동일 sample (seed 기존과 동일)
       c) GT hint를 system/user message에서 제거한 채로 GPT-4o-mini 재호출
       d) 새 transfer_decisions 분포 vs 원본 비교
    3. 분포 비교:
       - 패턴별 decision 일치율 (with GT hint vs blind)
       - 전체 분포 JSD
    4. 결과 저장:
       {
         "n_users": 30,
         "pattern_decision_agreement": {
           "genre_preference": 0.93,
           ...
         },
         "decision_distribution_jsd": {
           "with_gt": {...}, "blind": {...}, "jsd": 0.04
         },
         "verdict": "GT hint mostly affects Top-10 ordering, not decision logic"
       }
    """)
    print()
    print("실행 비용: ~30 calls × GPT-4o-mini = ~$0.05")
    print("실행 시간: ~30분 (재시도 포함)")
    print()
    print("TODO: 위 흐름 완성. 학습 종료 후·또는 별도로 실행 가능.")


if __name__ == "__main__":
    main()
