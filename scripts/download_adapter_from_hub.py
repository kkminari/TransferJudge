"""HF Hub에서 학습된 LoRA 어댑터 다운로드 (로컬·다른 환경에서 실행).

RunPod에서 학습한 어댑터를 로컬 Mac으로 가져와 Phase 4 평가에 사용.

사용법:
    export HF_TOKEN=hf_...
    python3 scripts/download_adapter_from_hub.py
    # 또는
    python3 scripts/download_adapter_from_hub.py \\
        --repo kwaksuobusi/transferjudge-judge-v1 \\
        --output checkpoints/judge_v1/adapter
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=str,
                        default="kwaksuobusi/transferjudge-judge-v1",
                        help="HF Hub repo (username/repo_name)")
    parser.add_argument("--output", type=Path,
                        default=Path("checkpoints/judge_v1/adapter"),
                        help="다운로드 받을 로컬 경로")
    args = parser.parse_args()

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("❌ huggingface_hub 패키지 필요 — pip install huggingface_hub")
        sys.exit(1)

    args.output.mkdir(parents=True, exist_ok=True)

    print(f"\n📥 어댑터 다운로드: {args.repo} → {args.output}")
    snapshot_download(
        repo_id=args.repo,
        repo_type="model",
        local_dir=str(args.output),
        local_dir_use_symlinks=False,  # 실제 파일 복사
    )
    files = list(args.output.rglob("*"))
    files = [f for f in files if f.is_file()]
    total_mb = sum(f.stat().st_size for f in files) / 1e6
    print(f"\n✅ 다운로드 완료 ({total_mb:.1f} MB)")
    for f in files:
        size_mb = f.stat().st_size / 1e6
        print(f"  {f.relative_to(args.output)}  ({size_mb:.1f} MB)")
    print(f"\n다음 단계: Phase 4 evaluate_judge.py 실행")


if __name__ == "__main__":
    main()
