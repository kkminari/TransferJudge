"""RunPod 환경에서 HuggingFace Hub로부터 대용량 데이터 다운로드.

GitHub에 push되지 않은 대용량 파일들을 HF Hub private repo에서 받는다.
Mac에서 사전에 `upload_data_to_hub.py`로 업로드해두었어야 한다.

대상 파일 (~2.5GB):
  - data/books_meta_filtered.parquet  (2.4GB)
  - data/movies_meta_filtered.parquet (51MB)

사전 준비:
  1. HuggingFace 계정 + Access Token (Mac과 동일)
  2. RunPod에서 로그인:
        huggingface-cli login
     또는:
        export HF_TOKEN=hf_...

사용법 (RunPod 터미널):
  cd /workspace/transferjudge
  python3 scripts/download_data_runpod.py --repo USERNAME/transferjudge-data
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGET_FILES = [
    "data/books_meta_filtered.parquet",
    "data/movies_meta_filtered.parquet",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="HF Hub에서 대용량 데이터 다운로드")
    parser.add_argument(
        "--repo",
        required=True,
        help="HF Hub repo ID (예: USERNAME/transferjudge-data)",
    )
    parser.add_argument(
        "--repo_type",
        default="dataset",
        choices=["dataset", "model"],
        help="Repo 타입 (Mac에서 업로드한 것과 동일)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="이미 존재하는 파일도 다시 다운로드",
    )
    args = parser.parse_args()

    # 의존성 확인
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("❌ huggingface_hub 패키지가 필요합니다.")
        print("   설치: pip install huggingface_hub")
        sys.exit(1)

    print(f"\n📥 HF Hub에서 다운로드: {args.repo}")
    print(f"   대상 파일: {len(TARGET_FILES)}개\n")

    # data/ 디렉토리 생성
    (ROOT / "data").mkdir(exist_ok=True)

    success = 0
    for rel_path in TARGET_FILES:
        full_path = ROOT / rel_path

        # 이미 존재하면 skip (--force 없으면)
        if full_path.exists() and not args.force:
            size_mb = full_path.stat().st_size / 1e6
            print(f"  ⏭️  스킵: {rel_path} ({size_mb:.1f} MB, 이미 존재)")
            success += 1
            continue

        print(f"  다운로드: {rel_path} ...")
        try:
            downloaded = hf_hub_download(
                repo_id=args.repo,
                filename=rel_path,
                repo_type=args.repo_type,
                local_dir=str(ROOT),
                local_dir_use_symlinks=False,
            )
            size_mb = Path(downloaded).stat().st_size / 1e6
            print(f"  ✅ 완료: {rel_path} ({size_mb:.1f} MB)")
            success += 1
        except Exception as e:
            print(f"  ❌ 실패: {rel_path}\n     {e}")

    print(f"\n결과: {success}/{len(TARGET_FILES)} 파일 다운로드 완료")

    if success == len(TARGET_FILES):
        print(f"\n🎉 모든 데이터 준비 완료!")
        print(f"\n다음 단계:")
        print(f"  python3 scripts/check_main_progress.py  # 환경 확인")
        print(f"  # Phase 3 진입 가능")
    else:
        print(f"\n⚠️ 일부 다운로드 실패. 다음을 확인하세요:")
        print(f"  1. HF Token이 올바르게 설정되었는지 (huggingface-cli login)")
        print(f"  2. Repo가 존재하고 접근 권한이 있는지")
        print(f"  3. Mac에서 upload_data_to_hub.py가 완료되었는지")
        sys.exit(1)


if __name__ == "__main__":
    main()
