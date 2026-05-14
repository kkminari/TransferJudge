"""Phase 4 — 학습된 Judge로 test set 추천 + 평가 (골격).

사용법:
    # (c) Ours
    python3 scripts/evaluate_judge.py \\
      --condition c_ours \\
      --adapter checkpoints/judge_v1/adapter \\
      --test-users data/test_users.parquet \\
      --output results/ablation_c_ours.json

    # (d) w/o Gate
    python3 scripts/evaluate_judge.py \\
      --condition d_no_gate \\
      --adapter checkpoints/judge_v1/adapter \\
      --disable-gate \\
      --output results/ablation_d_no_gate.json

평가 지표 (자세히: docs/phase4/Phase4_Metrics.md):
  - HR@1, @5, @10
  - NDCG@5, @10
  - MRR
  - JSONValid, SchemaComplete, CandMembership, BLOCKLeakage
  - Pattern Decision Accuracy (PDA)
  - Decision JSD vs Teacher
  - BrandLoyaltyBLOCK, SensoryTRANSFER

TODO (Phase 3 학습 완료 후 채울 부분):
  1. load_judge_model() — PEFT adapter merge + inference 셋업
  2. build_user_prompt() — Phase 2 train_judge 입력과 동일 형식 (Profile + 50 candidates)
  3. predict_for_user() — Judge 추론 + JSON 파싱
  4. compute_metrics() — 위 모든 지표 계산
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from collections import Counter

import pandas as pd
import numpy as np


# ============================================================
# 1. 메트릭 계산 — 골격 (학습 결과 들어오면 검증)
# ============================================================

def compute_hr_at_k(rec_ids: list[str], gt_id: str, k: int) -> int:
    """Top-k 안에 GT 있으면 1, 없으면 0."""
    return 1 if gt_id in rec_ids[:k] else 0


def compute_ndcg_at_k(rec_ids: list[str], gt_id: str, k: int) -> float:
    """NDCG@k — GT가 i-th position에 있으면 1/log2(i+1+1)."""
    for i, rid in enumerate(rec_ids[:k]):
        if rid == gt_id:
            return 1.0 / np.log2(i + 2)
    return 0.0


def compute_mrr(rec_ids: list[str], gt_id: str) -> float:
    for i, rid in enumerate(rec_ids):
        if rid == gt_id:
            return 1.0 / (i + 1)
    return 0.0


def compute_per_user_metrics(rec_ids: list[str], gt_id: str) -> dict:
    return {
        "HR@1": compute_hr_at_k(rec_ids, gt_id, 1),
        "HR@5": compute_hr_at_k(rec_ids, gt_id, 5),
        "HR@10": compute_hr_at_k(rec_ids, gt_id, 10),
        "NDCG@5": compute_ndcg_at_k(rec_ids, gt_id, 5),
        "NDCG@10": compute_ndcg_at_k(rec_ids, gt_id, 10),
        "MRR": compute_mrr(rec_ids, gt_id),
    }


def aggregate_metrics(per_user_results: list[dict]) -> dict:
    keys = ["HR@1", "HR@5", "HR@10", "NDCG@5", "NDCG@10", "MRR"]
    return {k: float(np.mean([r[k] for r in per_user_results])) for k in keys}


# ============================================================
# 2. 출력 품질 검증 (Phase 2 validate_teacher_trial과 동일)
# ============================================================

def validate_output(output_json: dict, candidate_ids: set[str], gt_id: str) -> dict:
    """JSON 출력의 품질 검증."""
    result = {
        "is_valid_json": True,
        "schema_complete": True,
        "all_in_candidates": True,
        "no_duplicates": True,
        "no_block_leakage": True,
    }

    if not isinstance(output_json, dict):
        result["is_valid_json"] = False
        return result

    td = output_json.get("transfer_decisions", {})
    PATTERNS = ["genre_preference", "narrative_complexity", "pacing_preference",
                "quality_sensitivity", "brand_loyalty", "sensory_preference",
                "emotional_resonance"]
    if not all(p in td for p in PATTERNS):
        result["schema_complete"] = False

    block_patterns = {p for p, info in td.items() if info.get("decision") == "BLOCK"}

    recs = output_json.get("recommendations", [])
    if len(recs) != 10:
        result["schema_complete"] = False

    rec_ids = []
    for r in recs:
        if not isinstance(r, dict):
            continue
        rid = str(r.get("item_id", ""))
        rec_ids.append(rid)
        if rid not in candidate_ids:
            result["all_in_candidates"] = False
        applied = set(r.get("applied_patterns", []))
        if applied & block_patterns:
            result["no_block_leakage"] = False

    if len(rec_ids) != len(set(rec_ids)):
        result["no_duplicates"] = False

    return result


# ============================================================
# 3. Pattern Decision Accuracy + JSD
# ============================================================

def compute_pattern_decision_accuracy(judge_td: dict, teacher_td: dict) -> float:
    """7개 패턴 중 Judge·Teacher decision이 일치하는 비율."""
    PATTERNS = ["genre_preference", "narrative_complexity", "pacing_preference",
                "quality_sensitivity", "brand_loyalty", "sensory_preference",
                "emotional_resonance"]
    matches = 0
    total = 0
    for p in PATTERNS:
        if p in judge_td and p in teacher_td:
            if judge_td[p].get("decision") == teacher_td[p].get("decision"):
                matches += 1
            total += 1
    return matches / total if total > 0 else 0.0


def jensen_shannon_divergence(p: dict, q: dict) -> float:
    """3-class (TRANSFER/PARTIAL/BLOCK) JSD."""
    labels = ["TRANSFER", "PARTIAL", "BLOCK"]
    p_vec = np.array([p.get(l, 0) for l in labels], dtype=float)
    q_vec = np.array([q.get(l, 0) for l in labels], dtype=float)
    p_vec /= p_vec.sum() if p_vec.sum() > 0 else 1
    q_vec /= q_vec.sum() if q_vec.sum() > 0 else 1
    m = 0.5 * (p_vec + q_vec)

    def _kl(a, b):
        mask = a > 0
        return float(np.sum(a[mask] * np.log2(a[mask] / b[mask])))

    return 0.5 * _kl(p_vec, m) + 0.5 * _kl(q_vec, m)


# ============================================================
# 4. Judge 모델 inference (TODO: Phase 3 후 채움)
# ============================================================

def load_judge_model(adapter_path: Path, base_model: str = "Qwen/Qwen3-14B"):
    """LoRA adapter를 base에 merge하여 inference-ready 모델 로드.

    Returns: (model, tokenizer)
    """
    raise NotImplementedError(
        "Phase 3 학습 완료 후 구현. PEFT model.from_pretrained() 활용."
    )


def predict_for_user(model, tokenizer, profile: dict, candidates: list[dict],
                     gt_id: str, max_new_tokens: int = 2500) -> dict:
    """한 사용자에 대해 Judge inference + JSON 파싱.

    Returns: {"output_json": dict, "raw_text": str}
    """
    raise NotImplementedError(
        "Phase 3 학습 완료 후 구현. tokenizer.apply_chat_template + model.generate."
    )


# ============================================================
# 5. 메인 — Phase 3 학습 완료 후 채울 부분 표시
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", type=str, required=True,
                        choices=["c_ours", "d_no_gate"])
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--test-users", type=Path, default=Path("data/test_users.parquet"))
    parser.add_argument("--profiles", type=Path, default=Path("profiler_outputs"))
    parser.add_argument("--books-meta", type=Path, default=Path("data/books_meta_filtered.parquet"))
    parser.add_argument("--books-reviews", type=Path, default=Path("data/books_reviews_filtered.parquet"))
    parser.add_argument("--teacher-outputs", type=Path, default=Path("teacher_outputs"),
                        help="Teacher 추천 비교용 (PDA 계산에 사용)")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--disable-gate", action="store_true",
                        help="(d) w/o Gate condition")
    parser.add_argument("--n-candidates", type=int, default=50)
    args = parser.parse_args()

    print(f"=== Phase 4 Evaluation: {args.condition} ===")
    print("⚠ 이 스크립트는 Phase 3 학습 완료 후 NotImplementedError 부분을 채워야 동작.")
    print("  현재는 메트릭 계산·검증 로직만 골격으로 작성됨.")
    print("  학습 종료 후 evaluate_judge_impl.py에 inference 구현 추가 예정.")

    # TODO: Phase 3 학습 완료 시 실제 inference 구현
    # 1. test_users 로드
    # 2. 각 사용자별:
    #    - Profile 로드 (profiler_outputs/user_{uid}.json)
    #    - GT 추출 (books_reviews_filtered.parquet의 rating>=4 최근)
    #    - 후보 50권 sample (seed=42)
    #    - Judge inference (predict_for_user)
    #    - 출력 검증 (validate_output)
    #    - per-user metric (compute_per_user_metrics)
    # 3. aggregate_metrics로 집계
    # 4. PDA + JSD + 패턴별 분포 계산
    # 5. results JSON 저장


if __name__ == "__main__":
    main()
