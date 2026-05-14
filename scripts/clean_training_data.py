"""학습 데이터 통합 정리 (Codex 2차 피드백 반영).

처리:
1. Orphan record 제거 (Profile/review 없는 user)
2. Low-signal record 제거 (core_patterns 중 ≥3개 unknown 또는 빈 evidence)
3. Title mismatch 정규화 (books_meta 기준으로 강제 통일)

사용법:
    python scripts/clean_training_data.py
"""
from __future__ import annotations

import json
import re
import glob
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SRC = DATA / "teacher_train_main.jsonl"
BACKUP = DATA / "teacher_train_main_pre_clean.jsonl"

CORE_PATTERNS = [
    "genre_preference", "narrative_complexity", "pacing_preference",
    "quality_sensitivity", "brand_loyalty", "sensory_preference",
    "emotional_resonance",
]
LOW_SIGNAL_THRESHOLD = 3  # unknown value가 ≥3개 OR empty evidence가 ≥3개


def extract_profile(content: str) -> dict | None:
    """user_msg 안의 Profile JSON을 brace balancer로 정확히 추출."""
    idx = content.find("=== USER PROFILE ===")
    if idx < 0:
        return None
    start = content.find("{", idx)
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(content)):
        c = content[i]
        if esc:
            esc = False
            continue
        if c == "\\":
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(content[start:i + 1])
                except Exception:
                    return None
    return None


def is_low_signal(user_msg_content: str) -> bool:
    """unknown value ≥ THRESHOLD OR empty evidence ≥ THRESHOLD 면 low-signal."""
    prof = extract_profile(user_msg_content)
    if prof is None:
        return True  # 파싱 실패 자체가 low-quality
    core = prof.get("core_patterns", {})
    n_unknown = 0
    n_empty_ev = 0
    for p in CORE_PATTERNS:
        info = core.get(p, {})
        val = str(info.get("value", "")).strip().lower()
        if val in ("", "unknown", "none", "n/a", "no signal"):
            n_unknown += 1
        ev = info.get("evidence", []) or []
        if not ev or all(not str(e).strip() for e in ev):
            n_empty_ev += 1
    return n_unknown >= LOW_SIGNAL_THRESHOLD or n_empty_ev >= LOW_SIGNAL_THRESHOLD


def get_uid(user_msg_content: str) -> str:
    m = re.search(r'"user_id":\s*"([A-Z0-9]+)"', user_msg_content)
    return m.group(1) if m else ""


def main():
    print("[1/6] Loading existing training data + sources...")
    lines = open(SRC).readlines()
    n_orig = len(lines)
    print(f"  Original records: {n_orig}")

    # 백업
    BACKUP.write_bytes(SRC.read_bytes())
    print(f"  Backup: {BACKUP.name}")

    # books_meta title 맵
    books_meta = pd.read_parquet(DATA / "books_meta_filtered.parquet",
                                  columns=["parent_asin", "title"])
    title_map = dict(zip(books_meta["parent_asin"], books_meta["title"]))

    # Profile 보유자 집합
    profile_uids = {Path(f).stem.replace("user_", "")
                    for f in glob.glob(str(ROOT / "profiler_outputs/*.json"))}
    print(f"  Profile owners: {len(profile_uids)}")

    # ===== Stage 1: orphan + low-signal 제거 =====
    print("\n[2/6] Stage 1 — remove orphan + low-signal records...")
    kept = []
    removed_orphan = 0
    removed_low = 0
    for line in lines:
        d = json.loads(line)
        user_msg = next(m for m in d["messages"] if m["role"] == "user")
        uid = get_uid(user_msg["content"])

        # orphan: Profile 없음
        if uid not in profile_uids:
            removed_orphan += 1
            print(f"  ORPHAN: {uid}")
            continue
        # low-signal
        if is_low_signal(user_msg["content"]):
            removed_low += 1
            continue
        kept.append(d)
    print(f"  removed orphan: {removed_orphan}")
    print(f"  removed low-signal: {removed_low}")
    print(f"  kept: {len(kept)} / {n_orig}")

    # ===== Stage 2: title mismatch 정규화 =====
    print("\n[3/6] Stage 2 — normalize recommendation titles to books_meta...")
    n_normalized = 0
    n_records_touched = 0
    for d in kept:
        asst_msg = next(m for m in d["messages"] if m["role"] == "assistant")
        try:
            out = json.loads(asst_msg["content"])
        except Exception:
            continue
        recs = out.get("recommendations", [])
        rec_changed = False
        for r in recs:
            if not isinstance(r, dict):
                continue
            rid = str(r.get("item_id", "")).strip()
            given = str(r.get("title", "")).strip()
            actual = title_map.get(rid, "").strip()
            if rid and actual and given and actual.lower()[:40] != given.lower()[:40]:
                r["title"] = actual
                n_normalized += 1
                rec_changed = True
        if rec_changed:
            n_records_touched += 1
            asst_msg["content"] = json.dumps(out, ensure_ascii=False)
    print(f"  recommendations normalized: {n_normalized}")
    print(f"  records touched: {n_records_touched}")

    # ===== Save cleaned =====
    print("\n[4/6] Saving cleaned training data...")
    SRC.write_text(
        "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in kept),
        encoding="utf-8",
    )
    print(f"  ✅ Saved: {SRC.name} ({len(kept)} lines)")

    # ===== Stage 3: split 재정의 =====
    print("\n[5/6] Stage 3 — redefine splits (train, valid 100, test 100)...")
    train_uids = set()
    for d in kept:
        user_msg = next(m for m in d["messages"] if m["role"] == "user")
        uid = get_uid(user_msg["content"])
        if uid:
            train_uids.add(uid)
    print(f"  train (학습 데이터): {len(train_uids)}")

    # 미사용 풀
    available = list(profile_uids - train_uids)
    print(f"  available pool: {len(available)}")
    import numpy as np
    rng = np.random.default_rng(2028)
    shuffled = rng.permutation(available)
    valid_uids = shuffled[:100].tolist()
    test_uids = shuffled[100:200].tolist()

    # 검증
    assert not set(train_uids) & set(valid_uids)
    assert not set(train_uids) & set(test_uids)
    assert not set(valid_uids) & set(test_uids)

    movies_reviews = pd.read_parquet(DATA / "movies_reviews_filtered.parquet",
                                      columns=["user_id"])
    books_reviews = pd.read_parquet(DATA / "books_reviews_filtered.parquet",
                                     columns=["user_id"])
    movie_counts = movies_reviews.groupby("user_id").size()
    book_counts = books_reviews.groupby("user_id").size()

    def make_df(uids):
        return pd.DataFrame({
            "user_id": list(uids),
            "movie_count": [int(movie_counts.get(u, 0)) for u in uids],
            "book_count": [int(book_counts.get(u, 0)) for u in uids],
        })

    train_df = make_df(sorted(train_uids))
    valid_df = make_df(valid_uids)
    test_df = make_df(test_uids)

    # 백업
    for name in ["train_users", "valid_users", "test_users", "main_experiment_users"]:
        src = DATA / f"{name}.parquet"
        dst = DATA / f"{name}_pre_clean.parquet"
        if src.exists() and not dst.exists():
            dst.write_bytes(src.read_bytes())

    train_df.to_parquet(DATA / "train_users.parquet", index=False)
    valid_df.to_parquet(DATA / "valid_users.parquet", index=False)
    test_df.to_parquet(DATA / "test_users.parquet", index=False)
    main_df = pd.concat([train_df, valid_df, test_df], ignore_index=True)
    main_df.to_parquet(DATA / "main_experiment_users.parquet", index=False)
    print(f"  train: {len(train_df)}, valid: {len(valid_df)}, test: {len(test_df)}")
    print(f"  main_experiment_users.parquet: {len(main_df)}")

    # ===== 최종 검증 =====
    print("\n[6/6] Final verification...")
    t = set(pd.read_parquet(DATA / "train_users.parquet")["user_id"])
    v = set(pd.read_parquet(DATA / "valid_users.parquet")["user_id"])
    e = set(pd.read_parquet(DATA / "test_users.parquet")["user_id"])
    print(f"  train ∩ valid = {len(t & v)}")
    print(f"  train ∩ test  = {len(t & e)}")
    print(f"  valid ∩ test  = {len(v & e)}")

    # title mismatch 재측정
    n_mm = 0
    new_lines = open(SRC).readlines()
    for line in new_lines:
        d = json.loads(line)
        asst = next(m for m in d["messages"] if m["role"] == "assistant")
        out = json.loads(asst["content"])
        recs = out.get("recommendations", [])
        for r in recs:
            if not isinstance(r, dict):
                continue
            rid = str(r.get("item_id", "")).strip()
            given = str(r.get("title", "")).strip()
            actual = title_map.get(rid, "").strip()
            if rid and actual and given:
                if actual.lower()[:40] != given.lower()[:40]:
                    n_mm += 1
    print(f"  title mismatch (post-clean): {n_mm}")

    print()
    print("=" * 60)
    print(f"SUMMARY: {n_orig} → {len(kept)} records")
    print(f"  -1 orphan, -{removed_low} low-signal, {n_normalized} titles normalized")
    print(f"  Final split: train {len(train_df)} / valid {len(valid_df)} / test {len(test_df)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
