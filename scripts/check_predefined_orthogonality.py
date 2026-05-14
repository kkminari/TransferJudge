"""Step 4 — 사전 정의 7개 패턴의 직교성 검증.

본 스크립트는 사전 정의된 7개 패턴(prompts/core_patterns_definition.md §1~7)의
영문 정의 텍스트를 임베딩하고, 7×7 cosine similarity matrix를 계산한다.
모든 off-diagonal pair가 ≤ 0.7이어야 통과 (직교성).

산출:
  data/pilot_pattern_orthogonality.png  (Heatmap)
  data/pilot_pattern_orthogonality.csv  (Similarity matrix)

사용법:
  python scripts/check_predefined_orthogonality.py
"""
from __future__ import annotations

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

# ============================================================
# 사전 정의 7개 (match_pilot_to_predefined.py와 동일)
# ============================================================

PREDEFINED_PATTERNS = {
    "genre_preference": (
        "The user's preference for specific content genres or categories "
        "such as sci-fi, thriller, romance, biography. Includes both "
        "preferred genres (positive polarity) and disliked genres (negative polarity)."
    ),
    "narrative_complexity": (
        "The user's preference for complex versus simple narrative structures, "
        "including multi-layered plots, non-linear timelines, unreliable narrators, "
        "and depth of character development."
    ),
    "pacing_preference": (
        "The user's preference for narrative pacing, including fast-paced action "
        "and tension versus slow-burn, character-driven, contemplative storytelling."
    ),
    "quality_sensitivity": (
        "The user's sensitivity to production quality, technical execution, and overall craft. "
        "Includes attention to ratings, professional reviews, acting, direction, "
        "and other indicators of quality and craftsmanship."
    ),
    "brand_loyalty": (
        "The user's loyalty to specific creators such as directors, actors, authors, "
        "franchises, series, or production brands. Includes both positive (favorite creators) "
        "and negative (avoided creators)."
    ),
    "sensory_preference": (
        "The user's preference for sensory experiences in media, including visual spectacle, "
        "auditory immersion, action choreography, atmospheric mood, cinematography, "
        "and other medium-specific experiential qualities."
    ),
    "emotional_resonance": (
        "The user's emphasis on emotional impact and resonance, "
        "whether the content evokes deep feelings, lasting memory, "
        "and personal meaning beyond mere entertainment."
    ),
}

# Movies-only 키워드 (도메인 적합성 검증용)
MOVIES_ONLY_KEYWORDS = [
    "cinematograph", "visual_spectacle", "imax", "soundtrack", "score",
    "acting", "actor", "director", "scene", "camera", "frame",
    "season", "episode", "tv_show", "film", "movie",
    "cast", "performance",
]


def main() -> None:
    print("[Loading sentence-transformers]")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBED_MODEL)

    names = list(PREDEFINED_PATTERNS.keys())
    texts = [
        f"{name.replace('_', ' ')}: {definition}"
        for name, definition in PREDEFINED_PATTERNS.items()
    ]

    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    sim = embeddings @ embeddings.T  # 7 × 7
    print(f"  similarity matrix: {sim.shape}")

    sim_df = pd.DataFrame(sim, index=names, columns=names)
    sim_df.to_csv(DATA / "pilot_pattern_orthogonality.csv")
    print(f"  saved: pilot_pattern_orthogonality.csv\n")

    # ============================================================
    # Off-diagonal 통계
    # ============================================================
    mask = np.triu(np.ones_like(sim, dtype=bool), k=1)
    off = sim[mask]
    print(f"[Off-diagonal Similarity Stats]")
    print(f"  쌍 개수: {len(off)}")
    print(f"  max:  {off.max():.3f}")
    print(f"  mean: {off.mean():.3f}")
    print(f"  min:  {off.min():.3f}")
    print(f"  threshold: {SIMILARITY_THRESHOLD}")

    n_violation = int((off > SIMILARITY_THRESHOLD).sum())
    if n_violation == 0:
        print(f"  ✅ 직교성 검증 통과 — 모든 쌍 ≤ {SIMILARITY_THRESHOLD}")
    else:
        print(f"  ⚠️ 직교성 위반 {n_violation}쌍")

    # ============================================================
    # 위반 쌍 출력
    # ============================================================
    violations = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if sim[i, j] > SIMILARITY_THRESHOLD:
                violations.append((names[i], names[j], float(sim[i, j])))

    if violations:
        print(f"\n[Violation Pairs]")
        for a, b, v in violations:
            print(f"  ⚠️ {a} ↔ {b}: {v:.3f}")

    # ============================================================
    # 가장 가까운 쌍 (가장 위험)
    # ============================================================
    print(f"\n[Top-5 가장 가까운 쌍 (잠재적 중복)]")
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pairs.append((names[i], names[j], float(sim[i, j])))
    pairs.sort(key=lambda x: -x[2])
    for a, b, v in pairs[:5]:
        warn = "⚠️" if v > SIMILARITY_THRESHOLD else "○ " if v > 0.55 else "✅"
        print(f"  {warn} {a:25s} ↔ {b:25s}: {v:.3f}")

    # ============================================================
    # Movies-only 도메인 적합성 검증
    # ============================================================
    print(f"\n[Movies-only 키워드 자동 검출 (BLOCK 후보 식별)]")
    for name, defn in PREDEFINED_PATTERNS.items():
        text = (name + " " + defn).lower()
        hits = [kw for kw in MOVIES_ONLY_KEYWORDS if kw in text]
        if hits:
            print(f"  ⚠️ {name:25s}  Movies-only 키워드 {len(hits)}개: {', '.join(hits[:5])}")
        else:
            print(f"  ✅ {name:25s}  Movies/Books 양쪽 적용 가능")

    # ============================================================
    # Heatmap 시각화
    # ============================================================
    fig, ax = plt.subplots(figsize=(9, 7.5))
    im = ax.imshow(sim, cmap="RdYlGn_r", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=40, ha="right", fontsize=9)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    for i in range(len(names)):
        for j in range(len(names)):
            v = sim[i, j]
            color = "white" if v > 0.6 else "black"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8, color=color)
    plt.colorbar(im, ax=ax, shrink=0.8)
    title = (
        f"Pilot Step 4 — 사전 정의 7개 패턴 직교성\n"
        f"max off-diag = {off.max():.3f}, mean = {off.mean():.3f}, threshold = {SIMILARITY_THRESHOLD}\n"
        f"({'✅ PASS — 모든 쌍 ≤ ' + str(SIMILARITY_THRESHOLD) if n_violation == 0 else f'⚠️ {n_violation} VIOLATION'})"
    )
    ax.set_title(title, fontsize=11, fontweight="bold")
    fig.tight_layout()
    out = DATA / "pilot_pattern_orthogonality.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  saved: {out}")

    # ============================================================
    # H3, H4 검증
    # ============================================================
    print(f"\n{'='*72}")
    print(f"가설 H3, H4 검증")
    print(f"{'='*72}")
    h3_pass = n_violation == 0
    print(f"  H3 (직교성 ≤ {SIMILARITY_THRESHOLD}): {'✅ 통과' if h3_pass else '⚠️ 미달'}")

    # H4: sensory_preference의 Movies-only 키워드 검출
    sensory_text = ("sensory_preference " + PREDEFINED_PATTERNS["sensory_preference"]).lower()
    sensory_hits = sum(1 for kw in MOVIES_ONLY_KEYWORDS if kw in sensory_text)
    h4_pass = sensory_hits >= 1
    print(f"  H4 (sensory_preference Movies-only 검출): {'✅ 통과' if h4_pass else '⚠️ 미달'} "
          f"(검출 키워드 {sensory_hits}개)")


if __name__ == "__main__":
    main()
