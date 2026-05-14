"""Phase 5 — 최종 Top-N 패턴의 직교성 검증.

입력: data/pilot_patterns_canonical.parquet, data/pilot_pattern_frequency.parquet
절차:
  1. Top-N 패턴 선택 (CLI 인자, 기본 6)
  2. 각 패턴의 description 임베딩 (sentence-transformers)
  3. N×N cosine similarity matrix 계산
  4. Heatmap 시각화
  5. 모든 off-diagonal similarity ≤ 0.7 검증
  6. Movies/Books 도메인 적합성 평가 (description 키워드 기반 휴리스틱)

산출:
  - data/pilot_pattern_orthogonality.png
  - data/pilot_pattern_orthogonality.csv (similarity matrix)

사용법:
  python scripts/check_pattern_orthogonality.py --top-n 6
  python scripts/check_pattern_orthogonality.py --top-n 7
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EMBED_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.7

plt.rcParams["font.family"] = ["Apple SD Gothic Neo", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# Movies 한정 키워드 (BLOCK 후보 식별용)
MOVIES_ONLY_KEYWORDS = [
    "cinematograph", "visual", "imax", "soundtrack", "score",
    "acting", "actor", "actress", "director", "directorial",
    "scene", "shot", "camera", "frame", "screen",
    "season", "episode", "tv_show", "film", "movie",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-n", type=int, default=6, help="Number of top patterns to verify")
    args = parser.parse_args()

    print("[Loading]")
    df = pd.read_parquet(DATA / "pilot_patterns_canonical.parquet")
    freq = pd.read_parquet(DATA / "pilot_pattern_frequency.parquet")
    top = freq.head(args.top_n).copy()
    top_names = top["canonical_name"].tolist()
    print(f"  Top-{args.top_n} canonical: {top_names}")

    # 각 canonical 패턴의 가장 빈도 높은 description 1개 추출
    desc_map = {}
    for nm in top_names:
        sub = df[df["canonical_name"] == nm]
        if len(sub) == 0:
            desc_map[nm] = ""
            continue
        desc_map[nm] = sub["description"].iloc[0]

    # 임베딩
    print(f"\n[Embedding] {EMBED_MODEL}")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBED_MODEL)
    texts = [f"{nm.replace('_', ' ')}: {desc_map[nm]}" for nm in top_names]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    # cosine similarity
    sim = np.dot(embeddings, embeddings.T)
    print(f"\n[Cosine Similarity Matrix]")
    sim_df = pd.DataFrame(sim, index=top_names, columns=top_names)
    print(sim_df.round(3).to_string())

    # off-diagonal 분석
    mask = np.triu(np.ones_like(sim, dtype=bool), k=1)
    off_diag = sim[mask]
    max_sim = float(off_diag.max())
    mean_sim = float(off_diag.mean())
    print(f"\n[Off-diagonal Similarity Stats]")
    print(f"  max: {max_sim:.3f} (threshold: {SIMILARITY_THRESHOLD})")
    print(f"  mean: {mean_sim:.3f}")
    if max_sim <= SIMILARITY_THRESHOLD:
        print(f"  ✅ 직교성 검증 통과 (모든 쌍 ≤ {SIMILARITY_THRESHOLD})")
    else:
        # 가장 높은 쌍 찾기
        i, j = np.unravel_index(np.argmax(sim - np.eye(len(sim))), sim.shape)
        print(f"  ⚠️ 직교성 위반: '{top_names[i]}' vs '{top_names[j]}' = {sim[i,j]:.3f}")
        print("  → 두 패턴 병합 또는 한쪽 재정의 검토 필요")

    sim_df.to_csv(DATA / "pilot_pattern_orthogonality.csv")
    print(f"\n  saved: pilot_pattern_orthogonality.csv")

    # ============ Heatmap ============
    fig, ax = plt.subplots(figsize=(max(8, args.top_n * 1.0), max(6, args.top_n * 0.9)))
    im = ax.imshow(sim, cmap="RdYlGn_r", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(top_names)))
    ax.set_xticklabels(top_names, rotation=40, ha="right", fontsize=9)
    ax.set_yticks(range(len(top_names)))
    ax.set_yticklabels(top_names, fontsize=9)
    for i in range(len(top_names)):
        for j in range(len(top_names)):
            v = sim[i, j]
            color = "white" if v > 0.6 else "black"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8, color=color)
    plt.colorbar(im, ax=ax, shrink=0.8)
    title = (f"Pilot Top-{args.top_n} 패턴 직교성 (Cosine Similarity)\n"
             f"max={max_sim:.3f}, mean={mean_sim:.3f}, threshold={SIMILARITY_THRESHOLD} "
             f"({'✅ PASS' if max_sim <= SIMILARITY_THRESHOLD else '⚠️ VIOLATION'})")
    ax.set_title(title, fontsize=11, fontweight="bold")
    fig.tight_layout()
    out = DATA / "pilot_pattern_orthogonality.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved: pilot_pattern_orthogonality.png")

    # ============ Movies-only 패턴 식별 (BLOCK 후보) ============
    print(f"\n[Movies-only 패턴 식별 (Books 도메인 부적합 후보)]")
    for nm in top_names:
        desc_lower = desc_map[nm].lower() + " " + nm.lower()
        hits = [kw for kw in MOVIES_ONLY_KEYWORDS if kw in desc_lower]
        if hits:
            print(f"  ⚠️ {nm}: Movies-only 키워드 ({', '.join(hits[:3])}...) → BLOCK 후보")
        else:
            print(f"  ✅ {nm}: Movies/Books 양쪽 적용 가능 추정")

    # ============ 사용자 커버리지 재확인 ============
    print(f"\n[Top-{args.top_n} 패턴 사용자 커버리지]")
    n_total_users = df["user_id"].nunique()
    for nm in top_names:
        n = df[df["canonical_name"] == nm]["user_id"].nunique()
        pct = n / n_total_users * 100
        print(f"  {nm:35s} : {n:3d}/{n_total_users} ({pct:.0f}%)")

    # 모든 N개 패턴이 등장한 사용자 수
    user_pattern_set = df.groupby("user_id")["canonical_name"].apply(set)
    all_present = user_pattern_set.apply(lambda s: set(top_names).issubset(s)).sum()
    pct_all = all_present / n_total_users * 100
    print(f"\n  Top-{args.top_n} 모두 등장한 사용자: {all_present}/{n_total_users} ({pct_all:.0f}%) (이상적 ≥80%)")


if __name__ == "__main__":
    main()
