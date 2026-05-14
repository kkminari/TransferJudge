"""teacher_train_main.jsonl의 system prompt에서 GT 관련 잔재 제거.

대상:
1. few-shot example 안의 'GROUND_TRUTH_HINT: ...' 라인 → 라인 자체 제거
2. instruction 안의 '(NO ground truth references)' 문구 → 'in your own words' 등으로 대체
3. 학습 record의 user/assistant 메시지는 건드리지 않음 (이미 정리됨)

사용법:
    python scripts/strip_gt_residue.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/teacher_train_main.jsonl"


def clean_system(content: str) -> str:
    # 1. GROUND_TRUTH_HINT 라인 제거 (한 줄 통째로)
    content = re.sub(r"^.*GROUND_TRUTH_HINT.*$\n?", "", content, flags=re.MULTILINE)
    # 2. "(NO ground truth references)" → 제거
    content = re.sub(r"\s*\(NO ground truth references\)", "", content)
    # 3. 연속 빈 줄 정리
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content


def main():
    lines = open(SRC).readlines()
    n_lines = len(lines)
    print(f"Processing {n_lines} records...")

    cleaned_lines = []
    n_changed = 0
    sample_before = None
    sample_after = None

    for i, line in enumerate(lines):
        d = json.loads(line)
        new_messages = []
        changed = False
        for m in d["messages"]:
            if m["role"] == "system":
                original = m["content"]
                cleaned = clean_system(original)
                if cleaned != original:
                    changed = True
                    if sample_before is None:
                        # 변경 부분 일부 저장
                        sample_before_count = original.count("GROUND_TRUTH_HINT") + original.count("(NO ground truth references)")
                        sample_after_count = cleaned.count("GROUND_TRUTH_HINT") + cleaned.count("(NO ground truth references)")
                        sample_before = sample_before_count
                        sample_after = sample_after_count
                new_messages.append({"role": "system", "content": cleaned})
            else:
                new_messages.append(m)
        if changed:
            n_changed += 1
        d["messages"] = new_messages
        cleaned_lines.append(json.dumps(d, ensure_ascii=False) + "\n")

    print(f"Records modified: {n_changed} / {n_lines}")
    print(f"Sample GT mention count: before={sample_before}, after={sample_after}")

    # 덮어쓰기
    SRC.write_text("".join(cleaned_lines), encoding="utf-8")
    print(f"\n✅ Saved: {SRC}")

    # 검증
    d_chk = json.loads(open(SRC).readlines()[0])
    sys_chk = next(m for m in d_chk["messages"] if m["role"] == "system")["content"]
    print(f"\n=== Verification (record 0) ===")
    print(f"  GROUND_TRUTH_HINT in system: {sys_chk.count('GROUND_TRUTH_HINT')}")
    print(f"  ground truth in system:      {sys_chk.lower().count('ground truth')}")
    print(f"  system prompt size:          {len(sys_chk)} chars")


if __name__ == "__main__":
    main()
