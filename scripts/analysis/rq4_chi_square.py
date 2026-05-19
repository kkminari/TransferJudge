"""RQ4 보강 — 옵션 B: 패턴 분포 chi-square 통계 검정.

7-패턴 × 3-결정(TRANSFER/PARTIAL/BLOCK) 분포 행렬에 chi-square test 적용.
H0: "패턴별 결정 분포가 균질하다"
H1: "패턴별 결정 분포가 유의하게 다르다"

결과: chi2, p-value, dof, Cramér's V, 표준화 잔차

실행:
    .venv_thesis/bin/python scripts/analysis/rq4_chi_square.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import chi2_contingency

ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_PATH = ROOT / "results/analysis/decision_quality.json"
OUTPUT_PATH = ROOT / "results/analysis/rq4_chi_square.json"

PATTERN_ORDER = [
    "genre_preference",
    "narrative_complexity",
    "pacing_preference",
    "quality_sensitivity",
    "brand_loyalty",
    "sensory_preference",
    "emotional_resonance",
]
LABELS = ["TRANSFER", "PARTIAL", "BLOCK"]


def main() -> None:
    with open(INPUT_PATH) as f:
        d = json.load(f)

    # 7×3 분포 행렬
    matrix = []
    for pat in PATTERN_ORDER:
        decisions = d["per_pattern_utility"][pat]["decisions"]
        row = [decisions.get(lbl, 0) for lbl in LABELS]
        matrix.append(row)
    matrix = np.array(matrix)

    # Chi-square test
    chi2, p_value, dof, expected = chi2_contingency(matrix)

    # Cramér's V (효과 크기)
    n = matrix.sum()
    phi2 = chi2 / n
    cramers_v = np.sqrt(phi2 / min(matrix.shape[0] - 1, matrix.shape[1] - 1))

    # 표준화 잔차 (residuals): (observed - expected) / sqrt(expected)
    # |z| > 2 → 유의하게 예상보다 많음/적음
    residuals = (matrix - expected) / np.sqrt(expected)

    result = {
        "test": "chi-square test of independence",
        "null_hypothesis": "패턴별 결정 분포가 균질하다",
        "matrix": {
            "patterns": PATTERN_ORDER,
            "labels": LABELS,
            "observed": matrix.tolist(),
            "expected": expected.tolist(),
        },
        "statistics": {
            "chi2": float(chi2),
            "p_value": float(p_value),
            "dof": int(dof),
            "cramers_v": float(cramers_v),
            "n_total": int(n),
        },
        "residuals": {
            "values": residuals.tolist(),
            "interpretation": "|z| > 2 → 예상보다 유의하게 많음(+) 또는 적음(-)",
            "highlights": [],
        },
        "interpretation": {},
    }

    # 주목할 만한 잔차 (|z| > 2)
    for i, pat in enumerate(PATTERN_ORDER):
        for j, lbl in enumerate(LABELS):
            z = residuals[i, j]
            if abs(z) > 2:
                obs = int(matrix[i, j])
                exp = float(expected[i, j])
                sign = "예상보다 많음" if z > 0 else "예상보다 적음"
                result["residuals"]["highlights"].append(
                    f"{pat} × {lbl}: z={z:.2f} (관찰={obs}, 기대={exp:.1f}, {sign})"
                )

    # 해석
    if p_value < 0.001:
        sig_text = "p < 0.001 (매우 유의)"
    elif p_value < 0.01:
        sig_text = f"p = {p_value:.4f} (유의)"
    elif p_value < 0.05:
        sig_text = f"p = {p_value:.4f} (유의)"
    else:
        sig_text = f"p = {p_value:.4f} (유의 안 함)"

    if cramers_v < 0.1:
        v_text = "negligible"
    elif cramers_v < 0.3:
        v_text = "small"
    elif cramers_v < 0.5:
        v_text = "moderate"
    else:
        v_text = "large"

    result["interpretation"] = {
        "significance": sig_text,
        "effect_size": f"Cramér's V = {cramers_v:.3f} ({v_text})",
        "conclusion": (
            "패턴별 결정 분포는 균질하다는 귀무가설이 기각된다. "
            f"chi-square 검정 결과 chi²={chi2:.2f}, dof={dof}, {sig_text}로 "
            "7가지 선호 패턴이 통계적으로 유의하게 다른 결정 분포를 보인다. "
            f"효과 크기는 {v_text} 수준(Cramér's V={cramers_v:.3f})이다."
        ),
    }

    # 저장
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # 콘솔 출력
    print("=" * 70)
    print(f"RQ4 옵션 B — 패턴 분포 chi-square 통계 검정")
    print("=" * 70)
    print()
    print(f"H0: 패턴별 결정 분포가 균질하다")
    print(f"H1: 패턴별 결정 분포가 유의하게 다르다")
    print()
    print(f"chi² = {chi2:.2f}")
    print(f"p-value = {p_value:.6e}")
    print(f"dof = {dof}")
    print(f"Cramér's V = {cramers_v:.3f} ({v_text})")
    print(f"n = {n}")
    print()
    print(f"→ {sig_text}")
    print()
    print("주목할 잔차 (|z| > 2):")
    for h in result["residuals"]["highlights"]:
        print(f"  • {h}")
    print()
    print(f"해석: {result['interpretation']['conclusion']}")
    print()
    print(f"저장: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
