"""학습된 LoRA 어댑터를 HuggingFace Hub에 업로드 (RunPod에서 실행).

학습 종료 후 checkpoints/judge_v1/adapter/를 HF Hub private model repo로 백업.
RunPod 인스턴스 종료 후에도 어댑터를 로컬·다른 환경에서 다시 받아 평가 가능.

사용법:
    export HF_TOKEN=hf_...
    python3 scripts/upload_adapter_to_hub.py
    # 또는
    python3 scripts/upload_adapter_to_hub.py \\
        --adapter-dir checkpoints/judge_v1/adapter \\
        --repo kwaksuobusi/transferjudge-judge-v1
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter-dir", type=Path,
                        default=Path("checkpoints/judge_v1/adapter"),
                        help="업로드할 어댑터 디렉토리")
    parser.add_argument("--repo", type=str,
                        default="kwaksuobusi/transferjudge-judge-v1",
                        help="HF Hub repo (username/repo_name)")
    parser.add_argument("--private", action="store_true", default=True)
    parser.add_argument("--public", dest="private", action="store_false",
                        help="public repo (기본은 private)")
    args = parser.parse_args()

    if not args.adapter_dir.exists():
        print(f"❌ 어댑터 디렉토리 없음: {args.adapter_dir}")
        print(f"   먼저 train_judge.py 학습을 완료하세요.")
        sys.exit(1)

    try:
        from huggingface_hub import HfApi, create_repo, upload_folder
    except ImportError:
        print("❌ huggingface_hub 패키지 필요 — pip install huggingface_hub")
        sys.exit(1)

    # 어댑터 파일 확인
    print(f"\n📦 어댑터 업로드 대상: {args.adapter_dir}")
    files = list(args.adapter_dir.rglob("*"))
    files = [f for f in files if f.is_file()]
    total_mb = sum(f.stat().st_size for f in files) / 1e6
    for f in files:
        size_mb = f.stat().st_size / 1e6
        print(f"  {f.relative_to(args.adapter_dir)}  ({size_mb:.1f} MB)")
    print(f"\n총 크기: {total_mb:.1f} MB")
    print(f"대상 repo: {args.repo} (private={args.private})")

    # Repo 생성 (이미 있어도 무시)
    api = HfApi()
    create_repo(
        repo_id=args.repo,
        repo_type="model",
        private=args.private,
        exist_ok=True,
    )
    print(f"✅ Repo 준비됨: {args.repo}")

    # 폴더 통째로 업로드
    print(f"\n📤 업로드 중...")
    upload_folder(
        folder_path=str(args.adapter_dir),
        repo_id=args.repo,
        repo_type="model",
        commit_message="Upload LoRA adapter (Phase 3 학습 결과)",
    )
    print(f"\n🎉 업로드 완료!")
    print(f"   https://huggingface.co/{args.repo}")
    print(f"\n다음 단계 (로컬 Mac에서):")
    print(f"   python3 scripts/download_adapter_from_hub.py --repo {args.repo}")


if __name__ == "__main__":
    main()
