"""Phase 5 Per-Pattern Ablation + Cold-Start 분석 계획 PDF.

산출: docs/phase5/Phase5_Ablation_Plan.pdf
"""
from pathlib import Path
import weasyprint

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "docs/phase5/Phase5_Ablation_Plan.pdf"


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
  .highlight-row td { background: #fff8e1 !important; font-weight: 600; }
  .pagebreak { page-break-before: always; }
  .callout { background: #f0f4f8; border-left: 4px solid #4a90d9; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }
  .callout-green { background: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }
  code { background: #f0f4f8; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }
  pre { background: #1a1a2e; color: #e8e8e8; padding: 10px 14px; border-radius: 5px; font-size: 8.8pt; overflow-wrap: break-word; white-space: pre-wrap; word-wrap: break-word; line-height: 1.4; }
</style>
</head>
<body>

<h1>Phase 5 Per-Pattern Ablation + Cold-Start 분석</h1>
<p class="subtitle">TransferJudge · 패턴별 중요도 측정 + Segment별 성능</p>
<p class="author">2026.05.14 · 빅데이터학과 17기 곽민아</p>

<div class="callout-green">
<strong>한 줄 요약</strong><br>
Phase 4의 메인 결과 (c) Ours를 토대로 (1) 7개 패턴 각각을 강제 BLOCK 시 성능 변화를 측정하고
(2) Test 100명을 Cold-Start severity로 segment 나눠서 본 연구의 cold-start 강건성을 정량화.
이 결과가 본 연구의 핵심 가설(<em>"모든 취향이 전이 가능한 것이 아니다"</em>)을 정성적·정량적으로 증명.
</div>

<h2>Phase 5a: Per-Pattern Ablation</h2>

<h3>1.1 목적</h3>

<p>본 연구 주장: "모든 사용자 취향이 cross-domain 전이 가능한 것이 아니다.
brand_loyalty 같은 medium-specific 패턴은 BLOCK해야 정답."</p>

<p>이를 정량 검증하려면 각 패턴이 추천 성능에 얼마나 기여하는지 측정해야 함.
방법: 학습된 Judge를 inference 시점에 강제로 특정 패턴을 BLOCK 처리하고 성능 비교.</p>

<h3>1.2 실험 설계</h3>

<table>
<tr><th>조건</th><th>제거 패턴</th><th>예상 성능</th><th>해석</th></tr>
<tr><td>Full Ours</td><td>없음 (모든 7 패턴 학습된 대로)</td><td>baseline (NDCG@10 ~0.28)</td><td>본 연구 메인 결과</td></tr>
<tr><td>w/o genre_preference</td><td>genre_preference 강제 BLOCK</td><td>NDCG↓↓</td><td>장르는 핵심 신호</td></tr>
<tr><td>w/o narrative_complexity</td><td>narrative_complexity 강제 BLOCK</td><td>NDCG↓</td><td>중요</td></tr>
<tr><td>w/o pacing_preference</td><td>pacing_preference 강제 BLOCK</td><td>NDCG↓</td><td>중요</td></tr>
<tr><td>w/o quality_sensitivity</td><td>quality_sensitivity 강제 BLOCK</td><td>NDCG ≈ 동일</td><td>중간 영향</td></tr>
<tr class="highlight-row"><td>w/o brand_loyalty (이미 BLOCK)</td><td>—</td><td>NDCG ≈ 동일</td><td>학습 가설 검증</td></tr>
<tr><td>w/o sensory_preference</td><td>sensory_preference 강제 BLOCK</td><td>NDCG↓ (atmosphere 신호 손실)</td><td>subtype 분리 효과</td></tr>
<tr><td>w/o emotional_resonance</td><td>emotional_resonance 강제 BLOCK</td><td>NDCG↓↓</td><td>강한 전이 신호 손실</td></tr>
</table>

<h3>1.3 추가 실험: Negative Transfer Detection</h3>

<p>특정 패턴을 강제 TRANSFER로 했을 때 성능이 떨어지면, 그 패턴은 BLOCK이 정답이라는 증거:</p>

<table>
<tr><th>조건</th><th>해석</th></tr>
<tr><td>brand_loyalty 강제 TRANSFER</td><td>NDCG↓ 예상 (negative transfer)</td></tr>
<tr><td>sensory_preference 강제 TRANSFER (전부)</td><td>visual spectacle 잘못 적용 시 NDCG↓</td></tr>
</table>

<h3>1.4 실행 흐름</h3>

<pre>for pattern in genre_preference narrative_complexity pacing_preference \\
               quality_sensitivity brand_loyalty sensory_preference \\
               emotional_resonance; do
    python3 scripts/per_pattern_ablation.py \\
      --adapter checkpoints/judge_v1/adapter \\
      --ablate-pattern $pattern \\
      --mode force_block \\
      --output results/per_pattern_${pattern}_block.json
done

# Negative transfer test (선택 2개)
python3 scripts/per_pattern_ablation.py \\
  --adapter checkpoints/judge_v1/adapter \\
  --ablate-pattern brand_loyalty \\
  --mode force_transfer \\
  --output results/per_pattern_brand_force_transfer.json</pre>

<h3>1.5 산출물: Pattern Importance Heatmap</h3>

<p>7 patterns × 3 metrics (HR@10, NDCG@10, MRR) 의 heatmap 생성.</p>

<table>
<tr><th>Pattern</th><th>ΔHR@10</th><th>ΔNDCG@10</th><th>ΔMRR</th><th>해석</th></tr>
<tr><td>genre_preference</td><td>?</td><td>?</td><td>?</td><td>중요도 1순위</td></tr>
<tr><td>emotional_resonance</td><td>?</td><td>?</td><td>?</td><td>중요도 2순위</td></tr>
<tr><td>narrative_complexity</td><td>?</td><td>?</td><td>?</td><td>중요</td></tr>
<tr><td>...</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>
<tr><td>brand_loyalty</td><td>~0</td><td>~0</td><td>~0</td><td>(이미 학습된 BLOCK과 동일)</td></tr>
</table>

<h2 class="pagebreak">Phase 5b: Cold-Start Segment 분석</h2>

<h3>2.1 목적</h3>

<p>본 연구는 "Books 도메인 정보가 적은 사용자에게도 잘 작동한다"는 cold-start 강건성을 주장.
이를 검증하려면 Test 100명을 Books 활동량으로 segment 나눠서 segment별 성능 비교.</p>

<h3>2.2 Segment 정의</h3>

<table>
<tr><th>Segment</th><th>Books 리뷰 수</th><th>예상 비율 (Test 100명 기준)</th><th>특징</th></tr>
<tr><td>Severe</td><td>5권</td><td>~30%</td><td>가장 cold-start, Books 정보 최소</td></tr>
<tr><td>Moderate</td><td>6~7권</td><td>~40%</td><td>중간</td></tr>
<tr><td>Warm</td><td>8~10권</td><td>~30%</td><td>상대적 풍부</td></tr>
</table>

<h3>2.3 측정 지표</h3>

<table>
<tr><th>지표</th><th>비교 대상</th></tr>
<tr><td>Segment별 NDCG@10</td><td>Severe vs Moderate vs Warm</td></tr>
<tr><td>Segment별 HR@10</td><td>같음</td></tr>
<tr><td>Severe / Warm ratio</td><td>0.85 이상이면 cold-start 강건성 합격</td></tr>
<tr><td>(c) Ours vs (e) 전통 CDR (Severe segment)</td><td>가장 큰 격차 예상 (cold-start에 약한 전통 CDR)</td></tr>
</table>

<h3>2.4 실행 흐름</h3>

<pre>python3 scripts/cold_start_analysis.py \\
  --results-dir results/ \\
  --test-users data/test_users.parquet \\
  --books-reviews data/books_reviews_filtered.parquet \\
  --output results/cold_start_analysis.json

# 출력: 조건 6개 × segment 3개 = 18개 조합 (HR@10, NDCG@10, MRR)</pre>

<h3>2.5 산출물</h3>

<p>다음 형태의 결과 표:</p>

<table>
<tr><th>Condition</th><th>Severe (n~30)</th><th>Moderate (n~40)</th><th>Warm (n~30)</th><th>Severe/Warm</th></tr>
<tr><td>(a) Single LLM</td><td>?</td><td>?</td><td>?</td><td>?</td></tr>
<tr><td>(b) Prompt-only</td><td>?</td><td>?</td><td>?</td><td>?</td></tr>
<tr class="highlight-row"><td>(c) Ours ★</td><td>?</td><td>?</td><td>?</td><td>≥ 0.85 목표</td></tr>
<tr><td>(d) w/o Gate</td><td>?</td><td>?</td><td>?</td><td>?</td></tr>
<tr><td>(e) 전통 CDR</td><td>매우 낮음 예상</td><td>?</td><td>?</td><td>&lt; 0.5 예상</td></tr>
<tr><td>(f) Raw Review</td><td>?</td><td>?</td><td>?</td><td>?</td></tr>
</table>

<h2 class="pagebreak">3. 일정 + 비용</h2>

<table>
<tr><th>단계</th><th>내용</th><th>환경</th><th>시간</th><th>비용</th></tr>
<tr><td>5a-1</td><td>7개 패턴 × force_block ablation</td><td>RunPod</td><td>~3h (한 패턴 ~25분)</td><td>$3~5</td></tr>
<tr><td>5a-2</td><td>2개 패턴 × force_transfer (negative transfer test)</td><td>RunPod</td><td>~1h</td><td>$1~2</td></tr>
<tr><td>5a-3</td><td>Pattern importance heatmap 생성</td><td>Mac</td><td>~30분</td><td>0</td></tr>
<tr><td>5b</td><td>Cold-Start segment 분석 (Phase 4 결과 재사용)</td><td>Mac</td><td>~30분</td><td>0</td></tr>
<tr><td><strong>총</strong></td><td>—</td><td>—</td><td><strong>~5h</strong></td><td><strong>$4~7</strong></td></tr>
</table>

<h2>4. 완료 기준</h2>

<table>
<tr><th>기준</th><th>판정</th></tr>
<tr><td>7개 패턴 ablation 결과 모두 생성</td><td>필수</td></tr>
<tr><td>Pattern Importance Heatmap 생성</td><td>필수</td></tr>
<tr><td>Cold-Start segment 표 완성 (6 conditions × 3 segments)</td><td>필수</td></tr>
<tr><td>brand_loyalty ablation 결과 ≈ baseline</td><td>가설 검증 (이미 학습된 BLOCK)</td></tr>
<tr><td>brand_loyalty force_transfer 시 NDCG↓</td><td>negative transfer 증거</td></tr>
<tr><td>(c) Severe/Warm 비율 ≥ 0.85</td><td>cold-start 강건성</td></tr>
</table>

<div class="callout-green">
<strong>Phase 5 통과 시 → Phase 6 진입</strong>: 모든 결과 통합 시각화 + 통계 분석 + 논문 작성.
</div>

</body>
</html>
"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    weasyprint.HTML(string=html).write_pdf(str(OUTPUT_PATH))
    print(f"✅ Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
