"""Phase 4 평가 계획 PDF 생성.

내용: 6 conditions 정의 + 평가 흐름 + 산출물 + 일정.
산출: docs/phase4/Phase4_Evaluation_Plan.pdf
"""
from pathlib import Path
import weasyprint

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "docs/phase4/Phase4_Evaluation_Plan.pdf"


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
  .highlight-row td { background: #e8f5e9 !important; font-weight: 600; }
  .pagebreak { page-break-before: always; }
  .callout { background: #f0f4f8; border-left: 4px solid #4a90d9; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }
  .callout-green { background: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }
  .callout-warn { background: #fff8e1; border-left: 4px solid #f5a623; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }
  code { background: #f0f4f8; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }
  pre { background: #1a1a2e; color: #e8e8e8; padding: 10px 14px; border-radius: 5px; font-size: 8.8pt; overflow-wrap: break-word; white-space: pre-wrap; word-wrap: break-word; line-height: 1.4; }
</style>
</head>
<body>

<h1>Phase 4 평가 계획</h1>
<p class="subtitle">TransferJudge · 6 conditions Ablation + 평가 지표</p>
<p class="author">2026.05.14 · 빅데이터학과 17기 곽민아</p>

<div class="callout-green">
<strong>한 줄 요약</strong><br>
학습된 Judge(Qwen3-14B QLoRA)와 5개 baseline을 Test set 100명에 대해 동일 조건으로 평가.
HR@k·NDCG@k·MRR + Pattern Decision Accuracy 등 11개 지표로 본 연구의 3가지 핵심 가설을 검증.
</div>

<h2>0. 핵심 가설 (Research Questions)</h2>

<table>
<tr><th>RQ</th><th>가설</th><th>검증 조건</th></tr>
<tr><td>RQ1</td><td>구조화된 Profile이 raw review와 전통 CDR보다 cross-domain 추천을 개선한다</td>
    <td>(c) vs (f) Raw Review, (c) vs (e1)(e2) 전통 CDR</td></tr>
<tr><td>RQ2</td><td>Transfer Gate (TRANSFER/PARTIAL/BLOCK)가 성능에 기여한다</td>
    <td>(c) vs (d) w/o Gate</td></tr>
<tr><td>RQ3</td><td>Profiler-Judge 분리 + Judge 파인튜닝이 단일 LLM·prompt-only·기존 LLM CDR보다 낫다</td>
    <td>(c) vs (a), (b), (g) TALLRec</td></tr>
</table>

<h2>1. 8개 평가 조건 (Conditions) — Codex 권장 baseline 확장</h2>

<table>
<tr><th>조건</th><th>모델·방식</th><th>Profile</th><th>Gate</th><th>학습</th><th>환경</th></tr>
<tr><td>(a) Single LLM</td><td>GPT-4o-mini (raw review 직접 입력 + Top-10 추천)</td>
    <td>❌</td><td>❌</td><td>zero-shot</td><td>💻 Mac (OpenAI)</td></tr>
<tr><td>(b) Prompt-only</td><td>GPT-4o-mini (Profile + 추천, 학습·gate 없음)</td>
    <td>✅</td><td>❌</td><td>zero-shot</td><td>💻 Mac (OpenAI)</td></tr>
<tr class="highlight-row"><td><strong>(c) Ours ★</strong></td><td>Qwen3-14B QLoRA (Profile + Gate + 578줄 SFT)</td>
    <td>✅</td><td>✅</td><td>578줄 SFT</td><td>☁️ RunPod</td></tr>
<tr><td>(d) w/o Gate</td><td>Qwen3-14B QLoRA (Profile만, gate 비활성)</td>
    <td>✅</td><td>❌</td><td>578줄 SFT</td><td>☁️ RunPod</td></tr>
<tr><td>(e1) EMCDR (2017)</td><td>Embedding mapping (Man et al., IJCAI)</td>
    <td>—</td><td>—</td><td>matrix factorization</td><td>☁️ RunPod</td></tr>
<tr><td><strong>(e2) PTUPCDR (2022)</strong></td><td><strong>Personalized Transfer (Zhu et al., WSDM) — 최신 전통 CDR</strong></td>
    <td>—</td><td>—</td><td>meta-learning</td><td>☁️ RunPod</td></tr>
<tr><td>(f) Raw Review</td><td>Qwen3-14B (Profile 없이 raw review로 SFT)</td>
    <td>❌</td><td>❌</td><td>같은 데이터, raw 입력</td><td>☁️ RunPod</td></tr>
<tr><td><strong>(g) TALLRec (2023)</strong></td><td><strong>Bao et al. (RecSys) — LLM as recommender via instruction SFT</strong></td>
    <td>—</td><td>❌</td><td>review-based SFT</td><td>☁️ RunPod</td></tr>
</table>

<div class="callout">
<strong>baseline 강화 근거 (Codex 권장 반영)</strong><br>
이전 6 conditions는 (e) 1개 외엔 모두 본 연구의 변형 → 사실상 self-ablation에 가까웠음.
강화한 baseline 2개:
<ul>
<li><strong>(e2) PTUPCDR</strong>: 2017 EMCDR만으로는 최신성 부족. 2022 SOTA 전통 CDR로 spectrum 확장.</li>
<li><strong>(g) TALLRec</strong>: 본 연구도 LLM 기반인데 다른 LLM CDR 비교 없으면 심사 약함.
가장 인용 많은 LLM CDR (RecSys 2023).</li>
</ul>
추가 비용 +$3, 시간 +2h. 본 연구 차별성(selective transfer)을 명확히 입증.
</div>

<div class="callout-warn">
모든 조건은 <strong>동일한 Test 100명</strong> + <strong>동일한 후보 50권 (seed=42)</strong>에서 평가.
이는 BLOCK leakage·data leakage 사전 차단 + 비교 공정성 확보.
</div>

<h2 class="pagebreak">2. 평가 지표 (자세한 정의: docs/phase4/Phase4_Metrics.md)</h2>

<h3>2.1 추천 정확도</h3>
<table>
<tr><th>지표</th><th>의미</th><th>본 연구 목표</th></tr>
<tr><td>HR@1, @5, @10</td><td>Top-k 안에 정답 포함 비율</td><td>HR@10 ≥ 0.60 (Teacher 60.2% 기준)</td></tr>
<tr><td>NDCG@5, @10</td><td>순위 가중 정확도</td><td>NDCG@10 ≥ 0.25</td></tr>
<tr><td>MRR</td><td>정답 역순위 평균</td><td>≥ 0.15</td></tr>
</table>

<h3>2.2 출력 품질</h3>
<table>
<tr><th>지표</th><th>의미</th><th>목표</th></tr>
<tr><td>JSONValid</td><td>유효 JSON 비율</td><td>≥ 0.95</td></tr>
<tr><td>SchemaComplete</td><td>스키마 충족 비율</td><td>≥ 0.95</td></tr>
<tr><td>CandMembership</td><td>후보 50권 내 추천 비율</td><td>= 1.00</td></tr>
<tr><td>BLOCKLeakage</td><td>BLOCK 패턴이 추천 근거로 사용</td><td>= 0.00</td></tr>
</table>

<h3>2.3 추론 품질 (신규 메트릭)</h3>
<table>
<tr><th>지표</th><th>의미</th><th>목표</th></tr>
<tr><td>PDA (Pattern Decision Accuracy)</td><td>Judge의 transfer_decisions가 Teacher와 일치율</td><td>≥ 0.80</td></tr>
<tr><td>Decision JSD</td><td>Decision 분포가 Teacher와 얼마나 일치 (Jensen-Shannon Divergence)</td><td>≤ 0.05</td></tr>
<tr><td>BrandLoyaltyBLOCK</td><td>brand_loyalty가 BLOCK으로 판정된 비율</td><td>≥ 0.90 (가설 검증)</td></tr>
<tr><td>SensoryTRANSFER</td><td>sensory_preference가 TRANSFER로 판정된 비율</td><td>30~75% (subtype 분리 효과)</td></tr>
</table>

<h2>3. 평가 흐름</h2>

<h3>3.1 입력 데이터</h3>

<table>
<tr><th>파일</th><th>역할</th></tr>
<tr><td><code>data/test_users.parquet</code></td><td>Test 100명 user_id</td></tr>
<tr><td><code>profiler_outputs/user_{id}.json</code></td><td>각 사용자의 7-pattern Profile</td></tr>
<tr><td><code>data/books_reviews_filtered.parquet</code></td><td>GT 추출 (rating≥4 최근)</td></tr>
<tr><td><code>data/books_meta_filtered.parquet</code></td><td>후보 도서 50권 sampling pool</td></tr>
<tr><td><code>checkpoints/judge_v1/adapter</code></td><td>학습된 LoRA adapter (Phase 3)</td></tr>
</table>

<h3>3.2 각 조건의 추론 흐름</h3>

<table>
<tr><th>조건</th><th>입력</th><th>출력</th></tr>
<tr><td>(a) Single LLM</td><td>raw 영화 리뷰 30개 + 후보 50권</td>
    <td>OpenAI API → Top-10 (JSON)</td></tr>
<tr><td>(b) Prompt-only</td><td>Profile JSON + 후보 50권</td>
    <td>OpenAI API → transfer_decisions + Top-10</td></tr>
<tr><td>(c) Ours</td><td>Profile JSON + 후보 50권</td>
    <td>Judge inference → transfer_decisions + Top-10</td></tr>
<tr><td>(d) w/o Gate</td><td>Profile JSON + 후보 50권</td>
    <td>Judge inference (gate 토큰 마스크 OFF) → Top-10</td></tr>
<tr><td>(e) 전통 CDR</td><td>Movies-Books 평점 행렬</td>
    <td>matrix factorization → 잠재 벡터 → Top-10</td></tr>
<tr><td>(f) Raw Review</td><td>raw 영화 리뷰 30개 + 후보 50권</td>
    <td>Qwen3-14B (Profile 없이 학습) → Top-10</td></tr>
</table>

<h3>3.3 산출물 파일 구조</h3>

<pre>results/
├── ablation_a_single.json         # (a) Single LLM
├── ablation_b_prompt.json         # (b) Prompt-only
├── ablation_c_ours.json           # (c) Ours (메인 결과)
├── ablation_d_no_gate.json        # (d) w/o Gate
├── ablation_e_traditional.json    # (e) 전통 CDR
├── ablation_f_raw.json            # (f) Raw Review
├── per_user_predictions.jsonl     # 사용자별 추천 결과
└── comparison_table.csv           # 6개 조건 통합 표</pre>

<h2 class="pagebreak">4. 일정 + 비용</h2>

<table>
<tr><th>단계</th><th>조건</th><th>환경</th><th>시간</th><th>비용</th></tr>
<tr><td>4a</td><td>(c) Ours ★</td><td>RunPod</td><td>~2h</td><td>$2~3</td></tr>
<tr><td>4b-i</td><td>(a) Single LLM</td><td>Mac (OpenAI)</td><td>~2h</td><td>$1~2</td></tr>
<tr><td>4b-ii</td><td>(b) Prompt-only</td><td>Mac (OpenAI)</td><td>~2h</td><td>$2~3</td></tr>
<tr><td>4b-iii</td><td>(d) w/o Gate</td><td>RunPod</td><td>~2h</td><td>$2~3</td></tr>
<tr><td>4b-iv</td><td>(f) Raw Review</td><td>RunPod</td><td>~2h</td><td>$2~3</td></tr>
<tr><td>4c-i</td><td>(e1) EMCDR</td><td>RunPod</td><td>~2h</td><td>$1~2</td></tr>
<tr><td><strong>4c-ii</strong></td><td><strong>(e2) PTUPCDR</strong></td><td>RunPod</td><td><strong>~2h</strong></td><td><strong>$1~2</strong></td></tr>
<tr><td><strong>4d</strong></td><td><strong>(g) TALLRec</strong></td><td>RunPod</td><td><strong>~3h (학습 + 평가)</strong></td><td><strong>$2~3</strong></td></tr>
<tr><td><strong>총</strong></td><td>—</td><td>—</td><td><strong>~17h</strong></td><td><strong>$13~21</strong></td></tr>
</table>

<h2>5. 코드 실행 명령어</h2>

<h3>5.1 (c) Ours 평가</h3>

<pre>python3 scripts/evaluate_judge.py \\
  --condition c_ours \\
  --adapter checkpoints/judge_v1/adapter \\
  --test-users data/test_users.parquet \\
  --profiles profiler_outputs/ \\
  --books-meta data/books_meta_filtered.parquet \\
  --books-reviews data/books_reviews_filtered.parquet \\
  --output results/ablation_c_ours.json</pre>

<h3>5.2 (a)(b) OpenAI API 기반</h3>

<pre>python3 scripts/run_ablation.py \\
  --condition a_single \\
  --test-users data/test_users.parquet \\
  --output results/ablation_a_single.json

python3 scripts/run_ablation.py \\
  --condition b_prompt \\
  --profiles profiler_outputs/ \\
  --output results/ablation_b_prompt.json</pre>

<h3>5.3 6개 조건 모두 한번에</h3>

<pre>bash scripts/run_all_ablations.sh
# 또는 Makefile:
make ablation-all</pre>

<h2>6. 평가 완료 기준</h2>

<table>
<tr><th>기준</th><th>판정</th></tr>
<tr><td>8개 결과 파일 모두 생성</td><td>필수</td></tr>
<tr><td>HR@10 (c) > HR@10 (a), (b), (f)</td><td>RQ3 부분 (단순 baseline)</td></tr>
<tr><td><strong>HR@10 (c) > HR@10 (g) TALLRec</strong></td><td><strong>RQ3 핵심 — LLM CDR 대비 우위</strong></td></tr>
<tr><td>NDCG@10 (c) > NDCG@10 (d)</td><td>RQ2 — Gate 효과</td></tr>
<tr><td>NDCG@10 (c) > NDCG@10 (e1), (e2)</td><td>RQ1 — Profile 효과 vs 전통 CDR</td></tr>
<tr><td>Pattern Decision Accuracy ≥ 0.80</td><td>Judge 학습 품질</td></tr>
<tr><td>paired t-test (c) vs (a) p < 0.05</td><td>통계적 유의성 (vs 단순)</td></tr>
<tr><td><strong>paired t-test (c) vs (g) TALLRec p < 0.05</strong></td><td><strong>통계적 유의성 (vs LLM SOTA)</strong></td></tr>
</table>

<div class="callout-green">
<strong>Phase 4 통과 시 → Phase 5 진입</strong>: Per-Pattern Ablation (7 패턴 각각 BLOCK 시 영향)
+ Cold-Start segment 분석 (Severe/Moderate/Warm).
</div>

</body>
</html>
"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    weasyprint.HTML(string=html).write_pdf(str(OUTPUT_PATH))
    print(f"✅ Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
