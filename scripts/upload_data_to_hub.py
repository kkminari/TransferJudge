"""HuggingFace Hub에 대용량 데이터 파일 업로드 (Mac 로컬에서 실행).

GitHub에 push할 수 없는 대용량 파일들을 HF Hub private repo에 업로드한다.
업로드 후 RunPod에서 `download_data_runpod.py`로 다운로드 가능.

대상 파일 (~2.5GB):
  - data/books_meta_filtered.parquet  (2.4GB)
  - data/movies_meta_filtered.parquet (51MB)

사전 준비:
  1. HuggingFace 계정 (https://huggingface.co)
  2. Access Token 발급 (https://huggingface.co/settings/tokens, "write" 권한)
  3. CLI 로그인:
        huggingface-cli login
     또는 환경 변수:
        export HF_TOKEN=hf_...

사용법:
  python3 scripts/upload_data_to_hub.py --repo USERNAME/transferjudge-data
  # private repo로 생성:
  python3 scripts/upload_data_to_hub.py --repo USERNAME/transferjudge-data --private
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 업로드할 파일 목록
TARGET_FILES = [
    "data/books_meta_filtered.parquet",
    "data/movies_meta_filtered.parquet",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="HF Hub에 대용량 데이터 업로드")
    parser.add_argument(
        "--repo",
        required=True,
        help="HF Hub repo ID (예: USERNAME/transferjudge-data)",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Private repo로 생성 (권장)",
    )
    parser.add_argument(
        "--repo_type",
        default="dataset",
        choices=["dataset", "model"],
        help="Repo 타입 (기본: dataset)",
    )
    args = parser.parse_args()

    # 의존성 확인
    try:
        from huggingface_hub import HfApi, create_repo, upload_file
    except ImportError:
        print("❌ huggingface_hub 패키지가 필요합니다.")
        print("   설치: pip install huggingface_hub")
        sys.exit(1)

    # 파일 존재 확인
    print("\n📦 업로드 대상 파일 확인:")
    missing = []
    total_size = 0
    for rel_path in TARGET_FILES:
        full_path = ROOT / rel_path
        if not full_path.exists():
            missing.append(rel_path)
            print(f"  ❌ {rel_path} — 파일 없음")
        else:
            size_mb = full_path.stat().st_size / 1e6
            total_size += size_mb
            print(f"  ✅ {rel_path} ({size_mb:.1f} MB)")

    if missing:
        print(f"\n❌ {len(missing)}개 파일이 누락되었습니다. 업로드 중단.")
        sys.exit(1)

    print(f"\n총 업로드 크기: {total_size:.1f} MB")
    print(f"Repo: {args.repo} (private={args.private}, type={args.repo_type})")

    # 사용자 확인
    confirm = input("\n계속 진행하시겠습니까? [y/N]: ").strip().lower()
    if confirm != "y":
        print("취소됨.")
        sys.exit(0)

    # Repo 생성 (이미 있어도 무시)
    api = HfApi()
    try:
        create_repo(
            repo_id=args.repo,
            repo_type=args.repo_type,
            private=args.private,
            exist_ok=True,
        )
        print(f"\n✅ Repo 준비됨: {args.repo}")
    except Exception as e:
        print(f"\n❌ Repo 생성 실패: {e}")
        sys.exit(1)

    # 파일 업로드
    print("\n📤 업로드 시작...")
    for rel_path in TARGET_FILES:
        full_path = ROOT / rel_path
        print(f"\n  업로드 중: {rel_path} ...")
        try:
            upload_file(
                path_or_fileobj=str(full_path),
                path_in_repo=rel_path,
                repo_id=args.repo,
                repo_type=args.repo_type,
            )
            print(f"  ✅ 완료: {rel_path}")
        except Exception as e:
            print(f"  ❌ 실패: {e}")
            sys.exit(1)

    print(f"\n🎉 모든 파일 업로드 완료!")
    print(f"\n다음 단계 (RunPod에서):")
    print(f"  python3 scripts/download_data_runpod.py --repo {args.repo}")


if __name__ == "__main__":
    main()
