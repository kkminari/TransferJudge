"""Pilot 출력에서 모든 raw 패턴 수집 + 1차 표면 정규화.

절차:
  1. pilot_outputs/*.json 모두 로드
  2. patterns 배열 펼쳐서 long-format DataFrame 생성
  3. 표면 정규화: snake_case·lowercase·접미사 통일
  4. 산출:
     - data/pilot_patterns_raw.parquet
     - data/pilot_patterns_normalized.parquet

사용법:
  python scripts/collect_patterns.py
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PILOT_OUT = ROOT / "pilot_outputs"


def normalize_name(name: str) -> str:
    """패턴 이름 표면 정규화."""
    if not name:
        return ""
    s = str(name).strip()
    s = re.sub(r"[\s\-]+", "_", s)              # 공백·하이픈 → _
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)         # 영숫자·_만 유지
    s = re.sub(r"_+", "_", s).strip("_").lower()

    # 의미 없는 접미사 통일
    suffixes = ["_pref", "_prefs", "_preferences", "_preference",
                "_taste", "_tastes",
                "_inclination", "_tendency"]
    for suf in suffixes:
        if s.endswith(suf):
            s = s[: -len(suf)] + "_preference"
            break

    # 접두 통일 (간헐적 등장)
    prefixes = ["user_", "viewer_", "the_user_", "users_"]
    for pre in prefixes:
        if s.startswith(pre):
            s = s[len(pre):]
            break

    return s


def main() -> None:
    files = sorted(PILOT_OUT.glob("user_*.json"))
    print(f"[Loading] {len(files)} pilot output files")

    rows = []
    for fp in files:
        try:
            data = json.loads(fp.read_text())
        except Exception as e:
            print(f"  skip {fp.name}: {e}")
            continue
        uid = data.get("user_id", fp.stem.replace("user_", ""))
        for p in data.get("patterns", []):
            rows.append({
                "user_id": uid,
                "name_raw": str(p.get("name", "")),
                "description": str(p.get("description", "")),
                "evidence": p.get("evidence", []),
                "confidence": float(p.get("confidence", 0.0)),
                "polarity": str(p.get("polarity", "")),
            })

    df = pd.DataFrame(rows)
    print(f"[Stats] total raw rows: {len(df):,} | unique users: {df['user_id'].nunique()}")
    print(f"[Stats] unique raw names: {df['name_raw'].nunique():,}")

    df.to_parquet(DATA / "pilot_patterns_raw.parquet", index=False)
    print(f"  saved: pilot_patterns_raw.parquet")

    # 1차 표면 정규화
    df["name_norm"] = df["name_raw"].apply(normalize_name)
    df = df[df["name_norm"].astype(str).str.len() > 0].copy()

    n_unique_norm = df["name_norm"].nunique()
    print(f"[Stats] after surface normalize: unique names {df['name_raw'].nunique()} → {n_unique_norm}")

    df.to_parquet(DATA / "pilot_patterns_normalized.parquet", index=False)
    print(f"  saved: pilot_patterns_normalized.parquet")

    # 빈도 통계
    name_counts = df.groupby("name_norm").agg(
        n_users=("user_id", "nunique"),
        n_total=("name_norm", "size"),
        avg_conf=("confidence", "mean"),
    ).sort_values("n_users", ascending=False)
    print(f"\n[Top-30 normalized names by user coverage]")
    print(name_counts.head(30).to_string())

    print(f"\n[Long-tail check]")
    print(f"  patterns covering >= 50 users: {(name_counts['n_users'] >= 50).sum()}")
    print(f"  patterns covering >= 30 users: {(name_counts['n_users'] >= 30).sum()}")
    print(f"  patterns covering >= 10 users: {(name_counts['n_users'] >= 10).sum()}")
    print(f"  patterns covering >=  5 users: {(name_counts['n_users'] >= 5).sum()}")
    print(f"  patterns covering   1 user only: {(name_counts['n_users'] == 1).sum()}")

    name_counts.to_parquet(DATA / "pilot_patterns_freq_surface.parquet")
    print(f"  saved: pilot_patterns_freq_surface.parquet")


if __name__ == "__main__":
    main()
