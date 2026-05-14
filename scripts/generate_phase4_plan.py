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
<tr><td>RQ1</td><td>구조화된 preference profile은 raw review 입력 및 전통 CDR baseline 대비 cold-start CDR 성능을 개선하는가?</td>
    <td>(c) vs (f), (c) vs (e)</td></tr>
<tr><td>RQ2</td><td>Pattern-level Transfer Gate는 모든 preference signal을 균일하게 전이하는 방식보다 negative transfer를 줄이고 성능을 높이는가?</td>
    <td>(c) vs (d)</td></tr>
<tr><td>RQ3</td><td>Profiler-Judge 구조와 Judge 파인튜닝은 single-prompt LLM / prompt-only / LLM-based CDR baseline 대비 더 효과적인가?</td>
    <td>(c) vs (a)(b)(g)</td></tr>
<tr><td>RQ4</td><td>Movies-to-Books 전이에서 어떤 preference pattern이 transferable, partially transferable, domain-specific으로 작동하는가?</td>
    <td>Phase 5a Per-Pattern Ablation</td></tr>
</table>

<div class="callout">
RQ 문장은 <strong>"비교 범주" 중심</strong>으로 기술 (특정 논문 이름 박지 않음).
구체적 baseline 모델은 아래 §1 8 conditions 표에서 명시.
</div>

<h2>1. 7개 평가 조건 (Conditions) — Codex 권장 현실 버전</h2>

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
<tr><td>(e) EMCDR (2017)</td><td>Embedding mapping (Man et al., IJCAI) — 전통 CDR 대표</td>
    <td>—</td><td>—</td><td>matrix factorization</td><td>☁️ RunPod</td></tr>
<tr><td>(f) Raw Review</td><td>Qwen3-14B (Profile 없이 raw review로 SFT)</td>
    <td>❌</td><td>❌</td><td>같은 데이터, raw 입력</td><td>☁️ RunPod</td></tr>
<tr><td><strong>(g) LLM4CDR-style</strong></td>
    <td><strong>single-LLM cross-domain recommendation (Liu et al., arXiv 2503.07761)</strong></td>
    <td>—</td><td>❌</td><td>prompt-only LLM CDR</td><td>☁️ RunPod</td></tr>
</table>

<div class="callout">
<strong>baseline 선정 근거 (Codex 3차 권장 — 현실 버전)</strong><br>
이전 6 conditions는 self-ablation 위주 → 외부 비교 부족.
이번엔 핵심만 1개씩 추가하여 7 conditions로 정리:
<ul>
<li><strong>(e) EMCDR</strong> (IJCAI 2017): 전통 CDR 대표. "LLM 기반 vs MF 기반" 검증 1개로 충분.</li>
<li><strong>(g) LLM4CDR-style</strong> (arXiv 2503.07761): LLM 기반 CDR 직접 비교. 본 연구 핵심 차별성 입증.</li>
</ul>
<strong>제외한 baseline (Related Work에서만 논의)</strong>:
<ul>
<li>PTUPCDR (WSDM 2022): meta-learning(MAML) 재현 부담 큼. 본 연구는 전통 CDR SOTA 재현이 목적 아님.</li>
<li>TALLRec (RecSys 2023): single-domain LLM recommendation tuning. CDR 비교 대상 아님.</li>
</ul>
본 연구 핵심은 <strong>selective transfer + pattern gate (RQ2, RQ4)</strong>이므로 외부 비교는
"방어용으로 충분히"만 가져가고 에너지는 (c) vs (d), (c) vs (g), RQ4 분석에 집중.
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
<tr><td>4c</td><td>(e) EMCDR</td><td>RunPod</td><td>~2h</td><td>$1~2</td></tr>
<tr><td><strong>4d</strong></td><td><strong>(g) LLM4CDR-style</strong></td><td>RunPod</td><td><strong>~3h (학습 + 평가)</strong></td><td><strong>$2~3</strong></td></tr>
<tr><td><strong>총</strong></td><td>—</td><td>—</td><td><strong>~15h</strong></td><td><strong>$12~19</strong></td></tr>
</table>

<div class="callout-green">
PTUPCDR 제거로 <strong>2-3일 구현 시간 절감</strong>. 절약된 에너지는 Phase 5a Per-Pattern (RQ4)와
(c) vs (g) LLM4CDR-style 비교 디버깅에 투입.
</div>

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
<tr><td>7개 결과 파일 모두 생성</td><td>필수</td></tr>
<tr><td>HR@10 (c) > HR@10 (a), (b), (f)</td><td>RQ3 부분 (단순 baseline)</td></tr>
<tr><td><strong>HR@10 (c) > HR@10 (g) LLM4CDR-style</strong></td><td><strong>RQ3 핵심 — LLM CDR 대비 우위</strong></td></tr>
<tr><td>NDCG@10 (c) > NDCG@10 (d)</td><td>RQ2 — Gate 효과</td></tr>
<tr><td>NDCG@10 (c) > NDCG@10 (e)</td><td>RQ1 — Profile 효과 vs 전통 CDR</td></tr>
<tr><td>Pattern Decision Accuracy ≥ 0.80</td><td>Judge 학습 품질</td></tr>
<tr><td>paired t-test (c) vs (a) p < 0.05</td><td>통계적 유의성 (vs 단순)</td></tr>
<tr><td><strong>paired t-test (c) vs (g) LLM4CDR-style p < 0.05</strong></td><td><strong>통계적 유의성 (vs LLM CDR)</strong></td></tr>
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
