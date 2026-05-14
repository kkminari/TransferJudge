"""Phase 6 결과 분석 + 시각화 계획 PDF.

산출: docs/phase6/Phase6_Analysis_Plan.pdf
"""
from pathlib import Path
import weasyprint

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "docs/phase6/Phase6_Analysis_Plan.pdf"


def main():
    html = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 2cm 1.8cm; @bottom-center { content: counter(page); font-size: 10px; color: #999; } }
  body { font-family: -apple-system, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif; font-size: 10pt; line-height: 1.55; color: #222; }
  h1 { text-align: center; font-size: 19pt; margin-bottom: 5px; color: #1a1a2e; }
  .subtitle { text-align: center; font-size: 10.5pt; color: #555; margin-bottom: 3px; }
  .author { text-align: center; font-size: 10pt; color: #777; margin-bottom: 22px; }
  h2 { font-size: 14pt; color: #16213e; border-bottom: 2.5px solid #4a90d9; padding-bottom: 4px; margin-top: 24px; }
  h3 { font-size: 11.5pt; color: #0f3460; margin-top: 14px; }
  table { width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 9.5pt; }
  th { background: #16213e; color: white; padding: 5px 8px; text-align: left; font-weight: 600; }
  td { padding: 5px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }
  tr:nth-child(even) td { background: #f8f9fa; }
  .pagebreak { page-break-before: always; }
  .callout { background: #f0f4f8; border-left: 4px solid #4a90d9; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }
  .callout-green { background: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }
  code { background: #f0f4f8; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }
  pre { background: #1a1a2e; color: #e8e8e8; padding: 10px 14px; border-radius: 5px; font-size: 8.8pt; }
</style>
</head>
<body>

<h1>Phase 6 결과 분석 + 시각화 계획</h1>
<p class="subtitle">TransferJudge · 통계 검증 + 논문용 figure·table 생성</p>
<p class="author">2026.05.14 · 빅데이터학과 17기 곽민아</p>

<div class="callout-green">
<strong>한 줄 요약</strong><br>
Phase 4·5에서 만들어진 모든 결과 파일을 통합 시각화하고 통계적 유의성 검증을 거쳐
논문 본문에 들어갈 5개 핵심 figure와 4개 table을 생성. 모든 분석은 Mac 로컬에서 진행 (추가 GPU 비용 없음).
</div>

<h2>1. 분석 대상 데이터</h2>

<table>
<tr><th>경로</th><th>내용</th><th>출처</th></tr>
<tr><td>results/ablation_*.json</td><td>6개 조건 평가 결과</td><td>Phase 4</td></tr>
<tr><td>results/per_pattern_*.json</td><td>7개 패턴 ablation 결과</td><td>Phase 5a</td></tr>
<tr><td>results/cold_start_analysis.json</td><td>3 segment × 6 조건</td><td>Phase 5b</td></tr>
<tr><td>results/per_user_predictions.jsonl</td><td>사용자별 추천 결과 (paired test용)</td><td>Phase 4</td></tr>
<tr><td>checkpoints/judge_v1/trainer_state.json</td><td>학습 loss 추이</td><td>Phase 3</td></tr>
</table>

<h2>2. 핵심 Figure 5개 (논문 본문용)</h2>

<table>
<tr><th>#</th><th>Figure</th><th>의미</th><th>도구</th></tr>
<tr><td>F1</td><td>학습 loss curve (train + eval, epoch별)</td>
    <td>학습이 정상 수렴했음을 증명</td><td>matplotlib</td></tr>
<tr><td>F2</td><td>6 conditions × 3 metrics 막대그래프 (HR@10, NDCG@10, MRR)</td>
    <td>Ours vs baseline 직관적 비교</td><td>matplotlib</td></tr>
<tr><td>F3</td><td>Pattern Importance Heatmap (7 × 3)</td>
    <td>brand_loyalty BLOCK 검증 가시화</td><td>seaborn heatmap</td></tr>
<tr><td>F4</td><td>Cold-Start Segment 그래프 (Severe/Moderate/Warm)</td>
    <td>cold-start 강건성 증명</td><td>matplotlib (clustered bar)</td></tr>
<tr><td>F5</td><td>Decision Distribution (Teacher vs Judge) — JSD 시각화</td>
    <td>Judge가 Teacher의 reasoning 패턴을 학습했음</td><td>matplotlib stacked bar</td></tr>
</table>

<h2>3. 논문 Table 4개</h2>

<table>
<tr><th>#</th><th>Table</th><th>내용</th></tr>
<tr><td>T1</td><td>Dataset Statistics</td>
    <td>1,000 cohort · 578 train · 100 valid · 100 test, leakage 0</td></tr>
<tr><td>T2</td><td>Main Results (6 conditions × metrics)</td>
    <td>HR@1, HR@5, HR@10, NDCG@5, NDCG@10, MRR + paired t-test 결과</td></tr>
<tr><td>T3</td><td>Per-Pattern Ablation (7 패턴)</td>
    <td>각 패턴 제거 시 ΔNDCG@10 + interpretation</td></tr>
<tr><td>T4</td><td>Cold-Start Segment Analysis</td>
    <td>6 conditions × 3 segments × NDCG@10</td></tr>
</table>

<h2 class="pagebreak">4. 통계 검증</h2>

<h3>4.1 Paired t-test</h3>

<table>
<tr><th>비교</th><th>가설</th></tr>
<tr><td>(c) vs (a)</td><td>NDCG@10 (c) > NDCG@10 (a), p < 0.05</td></tr>
<tr><td>(c) vs (b)</td><td>같음 (prompt-only 대비 학습 효과)</td></tr>
<tr><td>(c) vs (d)</td><td>Gate 효과 입증</td></tr>
<tr><td>(c) vs (f)</td><td>Profile 효과 입증</td></tr>
</table>

<h3>4.2 Effect Size (Cohen's d)</h3>

<table>
<tr><th>비교</th><th>목표 d</th><th>해석</th></tr>
<tr><td>(c) vs (a)</td><td>d ≥ 0.5</td><td>medium effect</td></tr>
<tr><td>(c) vs (b)</td><td>d ≥ 0.3</td><td>small-medium effect</td></tr>
<tr><td>(c) vs (e)</td><td>d ≥ 0.8</td><td>large effect (LLM vs 전통)</td></tr>
</table>

<h3>4.3 Bootstrap 95% Confidence Interval</h3>

<p>1,000회 bootstrap resampling으로 각 metric의 95% CI 계산 → 표에 ± 표기.</p>

<pre>예: NDCG@10 (c) Ours = 0.28 ± 0.02 (95% CI [0.26, 0.30])</pre>

<h2>5. Qualitative Analysis (정성 분석)</h2>

<h3>5.1 성공 사례 (Case Study)</h3>

<table>
<tr><th>분석 항목</th><th>방법</th></tr>
<tr><td>Ours가 정답 맞춘 사용자 3명</td><td>Profile 7-pattern + Judge transfer_decisions + 추천 근거 분석</td></tr>
<tr><td>Single LLM은 못 맞췄지만 Ours가 맞춘 사례</td><td>Gate의 명시적 효과 사례</td></tr>
<tr><td>brand_loyalty BLOCK의 효과 사례</td><td>Single LLM이 actor 이름 매칭으로 부정 추천한 사례</td></tr>
</table>

<h3>5.2 실패 사례 분석</h3>

<table>
<tr><th>분석 항목</th><th>방법</th></tr>
<tr><td>모든 조건이 못 맞춘 사용자</td><td>본 연구의 한계 영역 (Profile 신호 부족)</td></tr>
<tr><td>Ours만 못 맞춘 사용자</td><td>학습 데이터 분포 외 사례</td></tr>
</table>

<h2 class="pagebreak">6. 시각화 도구 (visualize_results.py)</h2>

<h3>6.1 사용법</h3>

<pre>python3 scripts/visualize_results.py \\
  --results-dir results/ \\
  --trainer-state checkpoints/judge_v1/trainer_state.json \\
  --output docs/phase6/figures/</pre>

<h3>6.2 생성 파일</h3>

<pre>docs/phase6/figures/
├── F1_loss_curve.png
├── F2_main_comparison.png
├── F3_pattern_heatmap.png
├── F4_cold_start_segments.png
├── F5_decision_distribution.png
└── tables/
    ├── T1_dataset_stats.csv
    ├── T2_main_results.csv
    ├── T3_pattern_ablation.csv
    └── T4_cold_start.csv</pre>

<h2>7. 일정 + 비용</h2>

<table>
<tr><th>단계</th><th>내용</th><th>시간</th><th>비용</th></tr>
<tr><td>6.1</td><td>모든 결과 파일 로드 + 통합 표</td><td>1h</td><td>0</td></tr>
<tr><td>6.2</td><td>5개 Figure 생성</td><td>2h</td><td>0</td></tr>
<tr><td>6.3</td><td>Paired t-test + Cohen's d + Bootstrap CI</td><td>2h</td><td>0</td></tr>
<tr><td>6.4</td><td>Case study 사용자 3-5명 선정 + 정성 분석</td><td>3h</td><td>0</td></tr>
<tr><td>6.5</td><td>결과 종합 보고서 PDF 생성</td><td>2h</td><td>0</td></tr>
<tr><td><strong>총</strong></td><td>—</td><td><strong>~10h (1.5일)</strong></td><td><strong>$0</strong></td></tr>
</table>

<div class="callout-green">
<strong>Phase 6 완료 시 → Phase 7 진입</strong>: 5 figure + 4 table 확보 → 논문 본문 작성.
</div>

</body>
</html>
"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    weasyprint.HTML(string=html).write_pdf(str(OUTPUT_PATH))
    print(f"✅ Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
