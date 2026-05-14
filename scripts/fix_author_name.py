"""books_meta_filtered.parquet의 author_name을 raw HF 데이터셋에서 재파싱.

원인: 기존 EDA 노트북의 extract_author 함수가 raw 'author' 컬럼이 dict가 아닌 다른 형태로
저장된 경우 빈 문자열을 반환. 본 스크립트는 raw books meta에서 직접 author.name을 추출해
filtered parquet에 병합·저장.

사용법:
    python scripts/fix_author_name.py
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FILTERED = ROOT / "data/books_meta_filtered.parquet"
BACKUP = ROOT / "data/books_meta_filtered_v1_noauthor.parquet"


def extract_author_name(val) -> str:
    """raw 'author' 필드에서 name 추출. dict, str(dict), None 모두 대응."""
    if val is None:
        return ""
    if isinstance(val, dict):
        return str(val.get("name", "")).strip()
    if isinstance(val, str):
        s = val.strip()
        if not s or s.lower() == "none":
            return ""
        # "{'name': 'X', ...}" 형태로 들어온 경우
        if s.startswith("{") and "name" in s:
            try:
                import ast
                d = ast.literal_eval(s)
                if isinstance(d, dict):
                    return str(d.get("name", "")).strip()
            except (ValueError, SyntaxError):
                pass
        return ""
    return ""


def main():
    print(f"[1/4] Loading raw books meta from HF cache...")
    from datasets import load_dataset
    raw = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        "raw_meta_Books",
        split="full",
        trust_remote_code=True,
    )
    print(f"  raw rows: {len(raw):,}")

    print(f"[2/4] Extracting author names...")
    # parent_asin + author만 추출
    raw_pd = raw.select_columns(["parent_asin", "author"]).to_pandas()
    raw_pd["author_name_v2"] = raw_pd["author"].apply(extract_author_name)
    nonempty = (raw_pd["author_name_v2"].str.strip() != "").sum()
    print(f"  parsed non-empty: {nonempty:,} / {len(raw_pd):,} ({nonempty/len(raw_pd)*100:.1f}%)")

    print(f"[3/4] Merging into filtered parquet...")
    filt = pd.read_parquet(FILTERED)
    print(f"  filtered rows: {len(filt):,}, current non-empty author_name: "
          f"{(filt['author_name'].astype(str).str.strip() != '').sum():,}")

    # 백업
    if not BACKUP.exists():
        filt.to_parquet(BACKUP, index=False)
        print(f"  backup saved: {BACKUP.name}")

    # 병합
    merged = filt.merge(
        raw_pd[["parent_asin", "author_name_v2"]],
        on="parent_asin", how="left",
    )
    merged["author_name"] = merged["author_name_v2"].fillna("").astype(str)
    merged = merged.drop(columns=["author_name_v2"])

    new_nonempty = (merged["author_name"].str.strip() != "").sum()
    print(f"  new non-empty author_name: {new_nonempty:,} / {len(merged):,} "
          f"({new_nonempty/len(merged)*100:.1f}%)")

    print(f"[4/4] Saving updated parquet...")
    merged.to_parquet(FILTERED, index=False)
    print(f"  ✅ Saved: {FILTERED}")
    print()
    print("Sample non-empty author rows:")
    sample = merged[merged["author_name"].str.strip() != ""].head(5)
    for _, r in sample.iterrows():
        print(f"  - {r['parent_asin']}: '{r['author_name']}'  ({str(r['title'])[:40]})")


if __name__ == "__main__":
    main()
