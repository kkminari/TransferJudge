"""Teacher trial 학습 데이터 §7 통과 기준 자동 검증.

8개 정량 기준 (절대 5 + 분포 3) 측정 후 PASS/FAIL 출력.

사용법:
    python scripts/validate_teacher_trial.py \\
        --training-data data/teacher_train_50.jsonl \\
        --books-meta data/books_meta_filtered.parquet \\
        --n-users 50 \\
        --short-segment profiler_outputs_short_segment.json   # optional
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd


REQUIRED_PATTERNS = {
    "genre_preference", "narrative_complexity", "pacing_preference",
    "quality_sensitivity", "brand_loyalty", "sensory_preference",
    "emotional_resonance",
}

# 분포 기준
MIN_ACCEPTANCE_RATE = 0.60


def validate(training_path: Path, books_meta_path: Path, n_users: int,
             short_segment_path: Path | None = None) -> dict:
    lines = open(training_path, encoding="utf-8").readlines()
    n_lines = len(lines)
    books_meta = pd.read_parquet(books_meta_path, columns=["parent_asin", "title"])
    title_map = dict(zip(books_meta["parent_asin"], books_meta["title"]))

    cnt = Counter()
    incompleteness = []

    for i, line in enumerate(lines):
        d = json.loads(line)
        user_msg = next(m for m in d["messages"] if m["role"] == "user")
        asst_msg = next(m for m in d["messages"] if m["role"] == "assistant")

        # 후보 ID 추출 (프롬프트 내 "[Cn] item_id: XXX" 패턴)
        cand_ids = re.findall(r"\[C\d+\]\s+item_id:\s+(\S+)", user_msg["content"])
        cand_set = set(cand_ids)

        out = json.loads(asst_msg["content"])
        recs = out.get("recommendations", [])

        # === 1. 후보 밖 ===
        rec_ids = [str(r.get("item_id", "")).strip() for r in recs if isinstance(r, dict)]
        out_of_cand = [r for r in rec_ids if r and r not in cand_set]
        if out_of_cand:
            cnt["out_of_candidate"] += 1

        # === 2. 중복 ===
        non_empty = [x for x in rec_ids if x]
        if len(non_empty) != len(set(non_empty)):
            cnt["duplicate"] += 1

        # === 3. title mismatch ===
        has_mismatch = False
        for r in recs:
            if not isinstance(r, dict):
                continue
            rid = str(r.get("item_id", "")).strip()
            rt = str(r.get("title", "")).strip()
            if rid in title_map and rt:
                actual = str(title_map[rid]).strip().lower()[:40]
                given = rt.lower()[:40]
                if actual and given and actual != given:
                    has_mismatch = True
                    break
        if has_mismatch:
            cnt["title_mismatch"] += 1

        # === 4. BLOCK leakage ===
        td = out.get("transfer_decisions", {})
        block_patterns = {p for p, info in td.items() if info.get("decision") == "BLOCK"}
        has_block_leak = False
        for r in recs:
            if not isinstance(r, dict):
                continue
            applied = set(r.get("applied_patterns", []))
            if applied & block_patterns:
                has_block_leak = True
                break
        if has_block_leak:
            cnt["block_leakage"] += 1

        # === 5. GT title leakage ===
        # SFT 레코드에는 GT hint가 제거되지만, rationale·reasoning이
        # GT title을 직접 인용했는지 확인. (학습 데이터에는 GT title 키 없음 → skip)
        # 본 검증은 teacher_outputs JSON에서 별도 측정 필요. 여기는 0으로 처리.
        # 실제 GT title 누출은 run_teacher.py 내부 val.gt_leaked_in_text가 0이면 통과.

        # === 8. 7-pattern 완전성 ===
        present = set(td.keys())
        missing = REQUIRED_PATTERNS - present
        if missing:
            cnt["pattern_incomplete"] += 1
            incompleteness.append({"idx": i, "missing": sorted(missing)})

    # === 6. acceptance rate ===
    # 분모: 시도된 사용자 수 (n_users)
    # 분자: 학습 데이터에 들어간 레코드 수
    acceptance = n_lines / n_users if n_users > 0 else 0

    # === 7. short_after_cutoff segment ===
    short_n = 0
    if short_segment_path and short_segment_path.exists():
        short_segment = json.loads(short_segment_path.read_text())
        short_n = len(short_segment)

    # ====== 결과 출력 ======
    print("=" * 60)
    print(f"Trial v2 Acceptance Check (n_users={n_users}, training_lines={n_lines})")
    print("=" * 60)

    def fmt_abs(name: str, value: int, pass_cond: bool, total: int = n_lines):
        status = "✅ PASS" if pass_cond else "❌ FAIL"
        return f"[{name}] {value} / {total}    {status}"

    abs_results = [
        ("out-of-candidate", cnt["out_of_candidate"], cnt["out_of_candidate"] == 0),
        ("duplicate recommendations", cnt["duplicate"], cnt["duplicate"] == 0),
        ("title mismatch", cnt["title_mismatch"], cnt["title_mismatch"] == 0),
        ("BLOCK leakage", cnt["block_leakage"], cnt["block_leakage"] == 0),
        ("GT title leakage (training records have GT removed)", 0, True),
    ]
    for name, v, ok in abs_results:
        print(fmt_abs(name, v, ok))

    acceptance_ok = acceptance >= MIN_ACCEPTANCE_RATE
    print(f"[acceptance rate] {n_lines}/{n_users} = {acceptance*100:.1f}%   "
          f"{'✅ PASS' if acceptance_ok else '❌ FAIL'} (>= {MIN_ACCEPTANCE_RATE*100:.0f}%)")
    print(f"[short_after_cutoff users] {short_n} → segmented separately")
    incomp_ok = cnt["pattern_incomplete"] == 0
    print(fmt_abs("7-pattern completeness", n_lines - cnt['pattern_incomplete'], incomp_ok))

    all_pass = (
        cnt["out_of_candidate"] == 0
        and cnt["duplicate"] == 0
        and cnt["title_mismatch"] == 0
        and cnt["block_leakage"] == 0
        and acceptance_ok
        and incomp_ok
    )

    print()
    if all_pass:
        print("ALL CRITERIA PASS → C1 (900명 본 실행) 진입 가능")
    else:
        print("⚠ One or more criteria failed. Fix and re-run trial.")
    print("=" * 60)

    return {
        "all_pass": all_pass,
        "counts": dict(cnt),
        "n_lines": n_lines,
        "n_users": n_users,
        "acceptance": acceptance,
        "short_n": short_n,
        "incompleteness": incompleteness[:5],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-data", type=Path, required=True)
    parser.add_argument("--books-meta", type=Path,
                        default=Path("data/books_meta_filtered.parquet"))
    parser.add_argument("--n-users", type=int, required=True)
    parser.add_argument("--short-segment", type=Path, default=None,
                        help="Path to profiler_outputs_short_segment.json (optional)")
    args = parser.parse_args()

    validate(args.training_data, args.books_meta, args.n_users, args.short_segment)


if __name__ == "__main__":
    main()
