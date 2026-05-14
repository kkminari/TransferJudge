"""Pilot 패턴 의미적 정규화 (임베딩 기반 클러스터링).

입력: data/pilot_patterns_normalized.parquet (표면 정규화 후)
절차:
  1. unique 패턴별 (name + description) 임베딩 (sentence-transformers)
  2. HDBSCAN 클러스터링 (cosine, min_cluster_size=3)
  3. 클러스터별 대표 이름 자동 제안 (가장 빈도 높은 멤버)
  4. 노이즈(label=-1)는 individual cluster로 처리
  5. 산출:
     - data/pilot_clusters.parquet (모든 패턴별 cluster_id)
     - data/pilot_clusters_for_review.csv (수동 검토용)
     - data/pilot_patterns_canonical.parquet (canonical_name 부여 후 long-format)

사용법:
  python scripts/normalize_patterns.py
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

MIN_CLUSTER_SIZE = 3
EMBED_MODEL = "all-MiniLM-L6-v2"


def main() -> None:
    print("[Loading] pilot_patterns_normalized.parquet")
    df = pd.read_parquet(DATA / "pilot_patterns_normalized.parquet")
    print(f"  rows: {len(df):,} | unique name_norm: {df['name_norm'].nunique()}")

    # unique (name_norm, sample description) 추출 — 가장 자주 등장하는 description 1개를 대표로
    unique_df = (
        df.groupby("name_norm")
        .agg(
            sample_desc=("description", lambda s: s.iloc[0]),
            n_users=("user_id", "nunique"),
            n_rows=("name_norm", "size"),
            avg_conf=("confidence", "mean"),
        )
        .reset_index()
        .sort_values("n_users", ascending=False)
        .reset_index(drop=True)
    )
    print(f"  unique patterns to embed: {len(unique_df)}")

    # 임베딩
    print(f"\n[Embedding] {EMBED_MODEL}")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBED_MODEL)
    texts = (unique_df["name_norm"].str.replace("_", " ") + ": " + unique_df["sample_desc"]).tolist()
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    print(f"  embedding shape: {embeddings.shape}")

    # HDBSCAN 클러스터링
    print(f"\n[Clustering] HDBSCAN (min_cluster_size={MIN_CLUSTER_SIZE}, metric=cosine via euclidean on normalized)")
    import hdbscan

    # cosine 거리는 normalized 벡터의 euclidean ** 2 / 2와 비례 → euclidean 직접 사용
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=1,
        cluster_selection_epsilon=0.15,
        metric="euclidean",
    )
    labels = clusterer.fit_predict(embeddings)

    n_clusters = len(set(labels) - {-1})
    n_noise = int((labels == -1).sum())
    print(f"  clusters: {n_clusters} | noise: {n_noise} ({n_noise/len(labels)*100:.1f}%)")

    unique_df["cluster_id"] = labels

    # 노이즈는 개별 클러스터로 (cluster_id에 더 큰 음수 부여)
    next_id = max(n_clusters, 1)
    for idx in unique_df.index[unique_df["cluster_id"] == -1]:
        unique_df.at[idx, "cluster_id"] = next_id
        next_id += 1

    # 클러스터별 대표 이름 = 가장 빈도(n_users) 높은 멤버
    cluster_repr = (
        unique_df.sort_values(["cluster_id", "n_users"], ascending=[True, False])
        .drop_duplicates("cluster_id", keep="first")
        .set_index("cluster_id")["name_norm"]
        .to_dict()
    )
    unique_df["canonical_name"] = unique_df["cluster_id"].map(cluster_repr)

    # 클러스터 통계
    cluster_stats = (
        unique_df.groupby("cluster_id")
        .agg(
            canonical=("canonical_name", "first"),
            n_members=("name_norm", "size"),
            members_sample=("name_norm", lambda s: " | ".join(s.head(8).tolist())),
            n_users_total=("n_users", "sum"),
            avg_conf_mean=("avg_conf", "mean"),
        )
        .sort_values("n_users_total", ascending=False)
        .reset_index()
    )

    # 검토용 CSV
    review_path = DATA / "pilot_clusters_for_review.csv"
    cluster_stats.to_csv(review_path, index=False)
    print(f"\n  saved: pilot_clusters_for_review.csv ({len(cluster_stats)} clusters)")

    # 모든 unique 패턴별 cluster_id 저장
    unique_df.to_parquet(DATA / "pilot_clusters.parquet", index=False)
    print(f"  saved: pilot_clusters.parquet (unique 패턴별 cluster_id)")

    # 원래 long-format에 canonical_name join
    name_to_canonical = unique_df.set_index("name_norm")["canonical_name"].to_dict()
    df["canonical_name"] = df["name_norm"].map(name_to_canonical)
    df.to_parquet(DATA / "pilot_patterns_canonical.parquet", index=False)
    print(f"  saved: pilot_patterns_canonical.parquet (long-format with canonical_name)")

    # Top 클러스터 출력
    print(f"\n[Top-25 clusters by total user coverage]")
    cols = ["canonical", "n_members", "n_users_total", "avg_conf_mean", "members_sample"]
    print(cluster_stats[cols].head(25).to_string(index=False))

    # Long-tail 통계 (canonical 기준)
    canonical_freq = (
        df.groupby("canonical_name")["user_id"].nunique().sort_values(ascending=False)
    )
    print(f"\n[Long-tail check (canonical 기준)]")
    print(f"  canonical patterns covering >= 50 users: {(canonical_freq >= 50).sum()}")
    print(f"  canonical patterns covering >= 30 users: {(canonical_freq >= 30).sum()}")
    print(f"  canonical patterns covering >= 10 users: {(canonical_freq >= 10).sum()}")
    print(f"  canonical patterns covering >=  5 users: {(canonical_freq >= 5).sum()}")
    print(f"  canonical patterns total (non-noise threshold {MIN_CLUSTER_SIZE}): {len(canonical_freq)}")


if __name__ == "__main__":
    main()
