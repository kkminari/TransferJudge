"""Phase 4 — Canonical 패턴 빈도 분석 + Top-N elbow point 탐지.

입력: data/pilot_patterns_canonical.parquet (Phase 3 산출)
절차:
  1. Canonical 패턴별 사용자 커버리지 집계
  2. Pareto chart 생성 (빈도 + 누적 커버리지)
  3. Elbow point 자동 탐지 (kneed library)
  4. 현재 6개 (genre/narrative/pacing/quality/brand/sensory)와 매핑
  5. 산출:
     - data/pilot_pattern_frequency.parquet
     - data/pilot_pattern_frequency.png
     - data/pilot_top_n_mapping.csv (현재 6개와 비교)

사용법:
  python scripts/analyze_pattern_frequency.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# 현재 가정 6개 (실험 계획서)
CURRENT_SIX = [
    "genre_preference",
    "narrative_complexity",
    "pacing_preference",
    "quality_sensitivity",
    "brand_loyalty",
    "sensory_preference",
]

plt.rcParams["font.family"] = ["Apple SD Gothic Neo", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def main() -> None:
    print("[Loading] pilot_patterns_canonical.parquet")
    df = pd.read_parquet(DATA / "pilot_patterns_canonical.parquet")
    print(f"  rows: {len(df):,} | unique canonical: {df['canonical_name'].nunique()} | users: {df['user_id'].nunique()}")

    # 빈도 집계
    freq = (
        df.groupby("canonical_name")
        .agg(
            n_users=("user_id", "nunique"),
            n_total=("canonical_name", "size"),
            avg_conf=("confidence", "mean"),
            n_positive=("polarity", lambda s: int((s == "positive").sum())),
            n_negative=("polarity", lambda s: int((s == "negative").sum())),
            n_mixed=("polarity", lambda s: int((s == "mixed").sum())),
        )
        .sort_values("n_users", ascending=False)
        .reset_index()
    )
    freq["coverage_pct"] = freq["n_users"] / df["user_id"].nunique() * 100
    freq.to_parquet(DATA / "pilot_pattern_frequency.parquet", index=False)
    print(f"  saved: pilot_pattern_frequency.parquet ({len(freq)} canonical patterns)")

    # Top 30 출력
    print(f"\n[Top-30 canonical patterns]")
    print(freq[["canonical_name", "n_users", "coverage_pct", "avg_conf",
                "n_positive", "n_negative", "n_mixed"]].head(30).to_string(index=False))

    # ============ Pareto chart ============
    top_n_show = 25
    top = freq.head(top_n_show)
    cumulative_pct = (top["n_users"].cumsum() / freq["n_users"].sum() * 100).values

    fig, ax1 = plt.subplots(figsize=(13, 6))
    bars = ax1.bar(range(len(top)), top["n_users"], color="#4a90d9", alpha=0.85)
    ax1.set_xticks(range(len(top)))
    ax1.set_xticklabels(top["canonical_name"].str.replace("_", " "),
                        rotation=45, ha="right", fontsize=8)
    ax1.set_ylabel("등장 사용자 수 (n=100)", color="#4a90d9")
    ax1.tick_params(axis="y", labelcolor="#4a90d9")
    ax1.set_ylim(0, top["n_users"].max() * 1.1)
    ax1.grid(alpha=0.3, axis="y")

    # 커버리지 라인 (cumulative %)
    ax2 = ax1.twinx()
    ax2.plot(range(len(top)), cumulative_pct, "o-", color="#e94560", linewidth=2)
    ax2.set_ylabel("누적 커버리지 (% of total occurrences)", color="#e94560")
    ax2.tick_params(axis="y", labelcolor="#e94560")
    ax2.set_ylim(0, 100)

    # ============ Elbow detection ============
    elbow_n = None
    try:
        from kneed import KneeLocator

        x = np.arange(1, len(top) + 1)
        y = top["n_users"].values
        kl = KneeLocator(x, y, curve="convex", direction="decreasing", S=1.0)
        if kl.knee is not None:
            elbow_n = int(kl.knee)
            ax1.axvline(elbow_n - 1, color="#2e7d32", linestyle="--", linewidth=2,
                        label=f"Elbow at N={elbow_n}")
            ax1.legend(loc="upper right")
            print(f"\n[Elbow] kneed detected N={elbow_n}")
    except Exception as e:
        print(f"  Elbow detection 실패: {e}")

    plt.title(f"GAP-Pilot · Canonical 패턴 빈도 분포 (Top-{top_n_show})\n"
              f"등장 사용자 수 (막대) + 누적 커버리지 (선){'  ·  Elbow N=' + str(elbow_n) if elbow_n else ''}",
              fontsize=11, fontweight="bold")
    fig.tight_layout()
    out = DATA / "pilot_pattern_frequency.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved: pilot_pattern_frequency.png")

    # ============ Top-N 컷오프 검증 ============
    candidates = sorted(set([5, 6, 7, 8, elbow_n]) - {None})
    print(f"\n[Top-N 컷오프 후보 검증]")
    for n in candidates:
        if n <= len(freq):
            top_n_users = freq.head(n)["n_users"].sum()
            total_users = freq["n_users"].sum()
            cov = top_n_users / total_users * 100
            last = freq.iloc[n - 1]["n_users"]
            next_one = freq.iloc[n]["n_users"] if n < len(freq) else 0
            drop_pct = (last - next_one) / last * 100 if last else 0
            mark = "★" if n == elbow_n else " "
            print(f"  {mark} Top-{n}: 마지막 패턴 user={last}, "
                  f"다음 user={next_one} (drop {drop_pct:.0f}%), "
                  f"누적 커버리지 {cov:.1f}%")

    # ============ 현재 6개와 매핑 ============
    print(f"\n[현재 6개 (계획서) vs Top-N 매핑]")
    mapping_rows = []
    for current in CURRENT_SIX:
        # canonical에서 정확 일치
        exact = freq[freq["canonical_name"] == current]
        if len(exact) > 0:
            r = exact.iloc[0]
            mapping_rows.append({
                "current": current, "match_type": "EXACT",
                "matched_canonical": current,
                "n_users": r["n_users"], "coverage_pct": r["coverage_pct"],
            })
            print(f"  ✅ EXACT: {current:25s} → {current:25s} (users={r['n_users']}, {r['coverage_pct']:.0f}%)")
            continue
        # 부분 일치 (canonical에 current의 키워드 포함)
        keyword = current.replace("_preference", "").replace("_", " ").split()[0]
        partial = freq[freq["canonical_name"].str.contains(keyword, na=False)]
        if len(partial) > 0:
            r = partial.iloc[0]
            mapping_rows.append({
                "current": current, "match_type": "PARTIAL",
                "matched_canonical": r["canonical_name"],
                "n_users": r["n_users"], "coverage_pct": r["coverage_pct"],
            })
            print(f"  △ PARTIAL: {current:25s} → {r['canonical_name']:30s} (keyword '{keyword}', users={r['n_users']})")
        else:
            mapping_rows.append({
                "current": current, "match_type": "MISSING",
                "matched_canonical": "",
                "n_users": 0, "coverage_pct": 0.0,
            })
            print(f"  ❌ MISSING: {current:25s} (직접·부분 매칭 모두 없음)")

    pd.DataFrame(mapping_rows).to_csv(DATA / "pilot_top_n_mapping.csv", index=False)
    print(f"  saved: pilot_top_n_mapping.csv")

    # 요약
    n_exact = sum(1 for m in mapping_rows if m["match_type"] == "EXACT")
    n_partial = sum(1 for m in mapping_rows if m["match_type"] == "PARTIAL")
    n_missing = sum(1 for m in mapping_rows if m["match_type"] == "MISSING")
    print(f"\n[Summary]")
    print(f"  현재 6개 → EXACT {n_exact} | PARTIAL {n_partial} | MISSING {n_missing}")
    if elbow_n:
        new_in_top = freq.head(elbow_n)["canonical_name"].tolist()
        new_only = [n for n in new_in_top if n not in CURRENT_SIX]
        print(f"  Top-{elbow_n} 中 신규 도출 패턴: {len(new_only)}개")
        for nm in new_only[:10]:
            r = freq[freq["canonical_name"] == nm].iloc[0]
            print(f"    • {nm} (users={r['n_users']}, conf={r['avg_conf']:.2f})")


if __name__ == "__main__":
    main()
