"""Pilot Study 옵션 A 진행 상황 자동 진단.

언제든지 다음 명령으로 현재 어디까지 진행했는지 확인:
  python scripts/check_pilot_progress.py

산출물 파일의 존재 여부와 크기를 기반으로 각 Step의 완료 상태를 자동 판정.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 색상 ANSI
G = "\033[92m"  # green
Y = "\033[93m"  # yellow
R = "\033[91m"  # red
B = "\033[94m"  # blue
GR = "\033[90m"  # gray
RST = "\033[0m"
BOLD = "\033[1m"


def check(path: Path, min_size: int = 1) -> tuple[bool, str]:
    if not path.exists():
        return False, "파일 없음"
    size = path.stat().st_size
    if size < min_size:
        return False, f"파일 비어 있음 ({size}B)"
    if size < 1024:
        return True, f"{size}B"
    if size < 1024 * 1024:
        return True, f"{size/1024:.1f}KB"
    return True, f"{size/1024/1024:.1f}MB"


# 각 단계의 정의: (step_id, name, [(label, path, min_size)])
STEPS = [
    (
        "Pilot Phase 1~4 (이미 완료)",
        "기존 Pilot Study 인프라",
        [
            ("Pilot 100명 출력", ROOT / "pilot_outputs", 100),
            ("Raw 패턴 수집", ROOT / "data" / "pilot_patterns_raw.parquet", 1024),
            ("Canonical 패턴", ROOT / "data" / "pilot_patterns_canonical.parquet", 1024),
            ("빈도 분석 그래프", ROOT / "data" / "pilot_pattern_frequency.png", 10240),
        ],
    ),
    (
        "Step 1",
        "7개 패턴 정의서 (학술 인용)",
        [
            ("정의서 마크다운", ROOT / "prompts" / "core_patterns_definition.md", 2048),
        ],
    ),
    (
        "Step 2",
        "Pilot 자동 매칭 (임베딩)",
        [
            ("매칭 스크립트", ROOT / "scripts" / "match_pilot_to_predefined.py", 1024),
            ("매칭 결과 CSV", ROOT / "data" / "pilot_to_predefined_matching.csv", 256),
        ],
    ),
    (
        "Step 3",
        "자유 추출 한계 분석",
        [
            ("분류 스크립트", ROOT / "scripts" / "categorize_pilot_patterns.py", 1024),
            ("카테고리 분류 CSV", ROOT / "data" / "pilot_pattern_categories.csv", 256),
        ],
    ),
    (
        "Step 4",
        "7개 직교성 검증",
        [
            ("직교성 스크립트", ROOT / "scripts" / "check_pattern_orthogonality.py", 1024),
            ("직교성 heatmap", ROOT / "data" / "pilot_pattern_orthogonality.png", 10240),
            ("직교성 CSV", ROOT / "data" / "pilot_pattern_orthogonality.csv", 256),
        ],
    ),
    (
        "Step 5",
        "채택 결정표 + Pilot 보고서",
        [
            ("통합 스크립트", ROOT / "scripts" / "integrate_pilot_evaluation.py", 1024),
            ("Pilot 보고서", ROOT / "docs" / "Pilot_Study_Report.md", 2048),
        ],
    ),
    (
        "Phase 6",
        "문서·코드 동기화 (실험 계획·프롬프트·PDF)",
        [
            # 동기화는 기존 파일을 수정하는 것이므로 직접 검증 어려움
            # 대신 Pilot Report에서 "동기화 완료" 마크 또는 별도 마커 파일
            ("동기화 완료 마커", ROOT / "data" / "pilot_phase6_done.marker", 1),
        ],
    ),
]


# 다음 명령 추천 매핑
NEXT_CMD = {
    "Step 1": '사용자에게 "Step 1 시작" 또는 "go" 신호 주기 → AI가 정의서 작성',
    "Step 2": "python scripts/match_pilot_to_predefined.py",
    "Step 3": "python scripts/categorize_pilot_patterns.py",
    "Step 4": "python scripts/check_pattern_orthogonality.py --top-n 7",
    "Step 5": "python scripts/integrate_pilot_evaluation.py",
    "Phase 6": '사용자 승인 후 AI가 "Phase 6 진행" 명령으로 6개 파일 동기화',
}


def step_status(items: list) -> str:
    n_total = len(items)
    n_ok = sum(1 for ok, _ in items if ok)
    if n_ok == 0:
        return "PENDING"
    if n_ok < n_total:
        return "PARTIAL"
    return "COMPLETED"


def main() -> None:
    print(f"\n{BOLD}{B}═══ Pilot Study 옵션 A 진행 진단 ═══{RST}\n")
    print(f"  작업 위치: {ROOT}\n")

    next_action = None

    for idx, (step_id, name, items) in enumerate(STEPS):
        # pilot_outputs 디렉토리 특수 처리
        results = []
        for label, path, min_size in items:
            if path.is_dir() if path.exists() else False:
                count = len(list(path.glob("user_*.json")))
                ok = count >= min_size
                detail = f"{count} files" + (f" (≥{min_size} 필요)" if not ok else "")
                results.append((ok, detail))
            else:
                ok, detail = check(path, min_size)
                results.append((ok, detail))

        status = step_status(results)
        if status == "COMPLETED":
            head = f"{G}✅ {step_id}{RST} — {name}"
        elif status == "PARTIAL":
            head = f"{Y}🟡 {step_id}{RST} — {name} (부분 진행)"
        else:
            head = f"{GR}⬜ {step_id}{RST} — {name}"
            if next_action is None and step_id != "Pilot Phase 1~4 (이미 완료)":
                next_action = step_id

        print(f"  {head}")

        for (label, path, min_size), (ok, detail) in zip(items, results):
            mark = f"{G}✅{RST}" if ok else f"{R}❌{RST}"
            rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
            print(f"     {mark} {label:25s} {GR}{rel}{RST}  {GR}({detail}){RST}")

    print()
    if next_action:
        cmd = NEXT_CMD.get(next_action, "확인 필요")
        print(f"{BOLD}{B}▶ 다음 단계: {next_action}{RST}")
        print(f"  {Y}추천 명령:{RST} {cmd}\n")
    else:
        print(f"{BOLD}{G}🎉 모든 단계 완료!{RST}\n")

    # 추적 마크다운 위치 안내
    tracker = ROOT / "docs" / "Pilot_OptionA_Tracker.md"
    if tracker.exists():
        print(f"{GR}  상세 추적 문서: {tracker.relative_to(ROOT)}{RST}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{R}진단 실패: {e}{RST}", file=sys.stderr)
        sys.exit(1)
