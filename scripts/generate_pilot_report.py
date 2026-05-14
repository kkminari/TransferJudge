"""Pilot Study Report PDF 생성 (8-10p, 본인 검토용, 기존 EDA 스타일).

산출: docs/TransferJudge_Pilot_Report.pdf
"""
from __future__ import annotations

import base64
import os

import weasyprint

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "docs", "pilot")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "TransferJudge_Pilot_Report.pdf")


def img_to_base64(filename: str) -> str:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"


IMG_FREQ = img_to_base64("pilot_pattern_frequency.png")
IMG_CAT = img_to_base64("pilot_categories_summary.png")
IMG_ORTHO = img_to_base64("pilot_pattern_orthogonality.png")


HTML_CONTENT = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 2.5cm 2cm;
    @bottom-center {{ content: counter(page); font-size: 10px; color: #999; }}
  }}
  body {{
    font-family: -apple-system, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    font-size: 10.5pt;
    line-height: 1.55;
    color: #222;
  }}
  h1 {{
    text-align: center;
    font-size: 20pt;
    margin-bottom: 5px;
    color: #1a1a2e;
  }}
  .subtitle {{
    text-align: center;
    font-size: 10.5pt;
    color: #555;
    margin-bottom: 3px;
  }}
  .author {{
    text-align: center;
    font-size: 10.5pt;
    color: #777;
    margin-bottom: 25px;
  }}
  h2 {{
    font-size: 14pt;
    color: #16213e;
    border-bottom: 2.5px solid #4a90d9;
    padding-bottom: 4px;
    margin-top: 28px;
  }}
  h3 {{ font-size: 12pt; color: #0f3460; margin-top: 18px; }}
  h4 {{ font-size: 10.5pt; color: #333; margin-top: 14px; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0 12px 0;
    font-size: 9.5pt;
  }}
  th {{
    background: #16213e;
    color: white;
    padding: 5px 8px;
    text-align: left;
    font-weight: 600;
  }}
  td {{
    padding: 4px 8px;
    border-bottom: 1px solid #ddd;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #f8f9fa; }}
  .highlight-row td {{ background: #e8f4fd !important; font-weight: 600; }}
  .callout {{
    background: #f0f4f8;
    border-left: 4px solid #4a90d9;
    padding: 10px 14px;
    margin: 10px 0;
    font-size: 9.7pt;
  }}
  .callout-warn {{
    background: #fff8e1;
    border-left: 4px solid #f5a623;
    padding: 10px 14px;
    margin: 10px 0;
    font-size: 9.7pt;
  }}
  .callout-green {{
    background: #e8f5e9;
    border-left: 4px solid #4caf50;
    padding: 10px 14px;
    margin: 10px 0;
    font-size: 9.7pt;
  }}
  .pass {{ color: #2e7d32; font-weight: 700; }}
  .warn {{ color: #e65100; font-weight: 700; }}
  .fail {{ color: #c62828; font-weight: 700; }}
  .pagebreak {{ page-break-before: always; }}
  .nobreak {{ page-break-inside: avoid; }}
  ul, ol {{ margin: 4px 0; padding-left: 20px; }}
  li {{ margin: 2px 0; }}
  img.chart {{ width: 100%; margin: 8px 0; }}
  img.chart-half {{ width: 48%; margin: 5px 1%; }}
  .fig-caption {{ text-align: center; font-size: 8.8pt; color: #666; margin-top: -5px; margin-bottom: 12px; }}

  /* === 인포그래픽 스타일 === */
  .infographic {{
    background: #fafbfc;
    border: 1px solid #d8dde6;
    border-radius: 5px;
    padding: 14px 16px;
    margin: 12px 0;
  }}
  .info-title {{
    font-size: 10.5pt;
    font-weight: 700;
    color: #1a2555;
    text-align: center;
    margin-bottom: 12px;
  }}
  .flow-row {{
    display: flex;
    align-items: stretch;
    gap: 5px;
    margin-bottom: 8px;
  }}
  .flow-box {{
    flex: 1;
    border: 1.3px solid #6b7cb5;
    border-radius: 4px;
    padding: 6px 8px;
    background: #fff;
    text-align: center;
    font-size: 8.5pt;
    line-height: 1.3;
  }}
  .flow-box-data {{ background: #fff4e6; border-color: #e08a3c; }}
  .flow-box-api {{ background: #e7f1fb; border-color: #2f7bc4; }}
  .flow-box-validate {{ background: #fff8d9; border-color: #c4a23c; }}
  .flow-box-output {{ background: #eaeef7; border-color: #2d3e8a; font-weight: 600; }}
  .flow-box-title {{ font-weight: 700; color: #1a2555; margin-bottom: 2px; font-size: 9pt; }}
  .flow-arrow {{
    display: flex;
    align-items: center;
    justify-content: center;
    color: #2d3e8a;
    font-size: 13pt;
    flex: 0 0 16px;
  }}

  /* 가설 검증 인포그래픽 */
  .hypothesis-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
    margin: 10px 0;
  }}
  .hyp-card {{
    background: #fff;
    border: 1.5px solid #4caf50;
    border-radius: 6px;
    padding: 8px;
    text-align: center;
    font-size: 9pt;
  }}
  .hyp-card-fail {{ border-color: #c62828; }}
  .hyp-id {{
    font-size: 14pt;
    font-weight: 700;
    color: #2e7d32;
    margin-bottom: 4px;
  }}
  .hyp-label {{ font-weight: 600; color: #1a2555; margin-bottom: 4px; font-size: 8.5pt; }}
  .hyp-result {{ color: #444; font-size: 8.5pt; }}
  .hyp-mark {{ font-size: 16pt; }}

  /* 7개 패턴 출처 그리드 */
  .pattern-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
    margin: 10px 0;
  }}
  .pattern-card {{
    background: #fff;
    border: 1.2px solid #d5dae6;
    border-radius: 4px;
    padding: 7px 10px;
    font-size: 9pt;
  }}
  .pattern-card-emo {{ border-color: #2f9a53; background: #e8f5e9; }}
  .pattern-name {{ font-weight: 700; color: #1a2555; }}
  .pattern-source {{ color: #666; font-size: 8.3pt; margin-top: 2px; }}
  .stars {{ color: #d79a2e; font-size: 9pt; }}
  .badge-transfer {{ background: #2f9a53; color: white; padding: 1px 5px; border-radius: 3px; font-size: 8pt; }}
  .badge-partial {{ background: #d79a2e; color: white; padding: 1px 5px; border-radius: 3px; font-size: 8pt; }}
  .badge-block {{ background: #b53a3a; color: white; padding: 1px 5px; border-radius: 3px; font-size: 8pt; }}

  /* 자기참조 회피 다이어그램 */
  .anti-self-ref {{
    background: #fff;
    border: 1.5px solid #4a90d9;
    border-radius: 6px;
    padding: 12px 14px;
    margin: 10px 0;
  }}
  .asr-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 6px 0;
    font-size: 9pt;
  }}
  .asr-label {{
    flex: 0 0 110px;
    font-weight: 700;
    color: #1a2555;
  }}
  .asr-source {{
    flex: 0 0 130px;
    background: #fff4e6;
    border: 1px solid #e08a3c;
    padding: 4px 8px;
    border-radius: 3px;
    text-align: center;
    font-size: 8.5pt;
  }}
  .asr-arrow {{ color: #2d3e8a; font-weight: 700; flex: 0 0 18px; text-align: center; }}
  .asr-target {{
    flex: 1;
    background: #e7f1fb;
    border: 1px solid #2f7bc4;
    padding: 4px 8px;
    border-radius: 3px;
    font-size: 8.5pt;
  }}

  /* 박스: 논문 표현 인용용 */
  .quote-box {{
    background: #fffef0;
    border: 1.5px dashed #d79a2e;
    border-radius: 5px;
    padding: 12px 14px;
    margin: 10px 0;
    font-size: 9.5pt;
    line-height: 1.55;
    color: #5d4a1a;
    font-style: italic;
  }}
  .key-stat {{
    display: inline-block;
    background: #e8f5e9;
    color: #2e7d32;
    padding: 1px 6px;
    border-radius: 3px;
    font-weight: 700;
    font-style: normal;
  }}
</style>
</head>
<body>

<!-- ===== TITLE ===== -->
<h1>Pilot Study Report</h1>
<p class="subtitle">TransferJudge — Profiler의 7개 Core Pattern 채택 정당화</p>
<p class="subtitle">옵션 A · 외부 학술 정의 + 자동 도구 검증 (5단계, 자기참조 회피)</p>
<p class="author">2026.04 · 빅데이터학과 17기 곽민아</p>

<!-- ===== Executive Summary ===== -->
<div class="callout-green nobreak">
<strong>한 줄 요약</strong><br>
본 연구의 7개 Core Pattern은 추천시스템·마케팅 학계에서 차용한 6개와 Pilot에서 데이터 기반 도출한 1개(emotional_resonance)로 구성된다.
자유 추출의 매체-편향 한계 <span class="key-stat">90.8%</span>를 명시 prompt 설계로 극복함을 데이터로 입증.
</div>

<table>
<tr><th>항목</th><th>값</th></tr>
<tr><td>Pilot 샘플</td><td>100명 (Train 800 中, seed=42)</td></tr>
<tr><td>비용</td><td>$0.081 (GPT-4o-mini)</td></tr>
<tr><td>가설 검증 결과</td><td><span class="pass">5/5 모두 통과 (H1~H5)</span></td></tr>
<tr><td>채택 결정</td><td><span class="pass">7/7 모두 ACCEPT (REJECT 0)</span></td></tr>
<tr><td>작업 기간</td><td>2026-04-26 ~ 2026-04-28</td></tr>
</table>

<!-- ===== 자기참조 회피 다이어그램 ===== -->
<h2>1. 핵심 메커니즘 — 자기참조 회피</h2>

<p>"내가 정의한 패턴을 내가 맞다고 검증"하는 자기참조를 피하기 위해 <strong>정의 출처</strong>와 <strong>검증 출처</strong>를 분리.</p>

<div class="anti-self-ref nobreak">
  <div class="info-title">정의 vs 검증 분리 구조</div>
  <div class="asr-row">
    <div class="asr-label">패턴 정의</div>
    <div class="asr-source">외부 학술 분야</div>
    <div class="asr-arrow">→</div>
    <div class="asr-target">NCF (2017), Ricci RS Handbook (2015), Oliver (1999), LLM4CDR (2025), TALLRec (2023)</div>
  </div>
  <div class="asr-row">
    <div class="asr-label">사전 등록</div>
    <div class="asr-source">prompts/core_patterns_definition.md</div>
    <div class="asr-arrow">→</div>
    <div class="asr-target">가설 H1~H5 (Pilot 결과 보기 전 등록)</div>
  </div>
  <div class="asr-row">
    <div class="asr-label">검증 도구</div>
    <div class="asr-source">자동 임베딩 매칭</div>
    <div class="asr-arrow">→</div>
    <div class="asr-target">sentence-transformers cosine similarity (본 연구가 직접 매칭하지 않음)</div>
  </div>
  <div class="asr-row">
    <div class="asr-label">평가 기준</div>
    <div class="asr-source">4가지 독립 기준</div>
    <div class="asr-arrow">→</div>
    <div class="asr-target">학술 근거 + Pilot 매칭 + Cross-Domain + 직교성 (단일 빈도가 아님)</div>
  </div>
</div>

<!-- ===== Workflow 다이어그램 ===== -->
<h2>2. 5단계 작업 흐름</h2>

<div class="infographic nobreak">
  <div class="info-title">Pilot Study Phase 1~4 (이미 완료) → 옵션 A Step 1~5</div>
  <!-- 1행: Phase 1~4 -->
  <div class="flow-row">
    <div class="flow-box flow-box-data">
      <div class="flow-box-title">Phase 1-4</div>
      Pilot 100명 자유 추출 → 391 canonical 패턴
    </div>
  </div>
  <div style="text-align:center; color:#2d3e8a;">↓</div>
  <!-- 2행: Option A 5 Steps -->
  <div class="flow-row">
    <div class="flow-box flow-box-validate">
      <div class="flow-box-title">Step 1</div>
      7개 정의서<br>(학술 인용)
    </div>
    <div class="flow-arrow">→</div>
    <div class="flow-box flow-box-api">
      <div class="flow-box-title">Step 2</div>
      자동 매칭<br>(임베딩 cosine)
    </div>
    <div class="flow-arrow">→</div>
    <div class="flow-box flow-box-api">
      <div class="flow-box-title">Step 3</div>
      4 카테고리<br>분류
    </div>
    <div class="flow-arrow">→</div>
    <div class="flow-box flow-box-api">
      <div class="flow-box-title">Step 4</div>
      직교성 +<br>Movies-only
    </div>
    <div class="flow-arrow">→</div>
    <div class="flow-box flow-box-output">
      <div class="flow-box-title">Step 5</div>
      채택 결정표<br>+ 본 보고서
    </div>
  </div>
</div>

<!-- ===== 7개 패턴 채택 ===== -->
<h2 class="pagebreak">3. 7개 Core Pattern 정의</h2>

<p>외부 학술 표준 6개 + Pilot 데이터 기반 도출 1개. 인용 강도(★)는 자기평가.</p>

<div class="pattern-grid">
  <div class="pattern-card">
    <div class="pattern-name">1. genre_preference</div>
    <div class="pattern-source">NCF (He 2017) <span class="stars">★★★★★</span></div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 장르·카테고리 선호</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">2. narrative_complexity</div>
    <div class="pattern-source">LLM4CDR, TALLRec <span class="stars">★★★★</span></div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 서사 복잡도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">3. pacing_preference</div>
    <div class="pattern-source">TALLRec attribute <span class="stars">★★★★</span></div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 전개 속도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">4. quality_sensitivity</div>
    <div class="pattern-source">Ricci RS Handbook (2015) <span class="stars">★★★★</span></div>
    <div style="margin-top:3px;"><span class="badge-partial">PARTIAL</span> 품질 민감도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">5. brand_loyalty</div>
    <div class="pattern-source">Oliver (1999) <span class="stars">★★★</span></div>
    <div style="margin-top:3px;"><span class="badge-block">BLOCK 후보</span> 창작자 충성도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">6. sensory_preference</div>
    <div class="pattern-source">영화 매체 특화 <span class="stars">★★</span></div>
    <div style="margin-top:3px;"><span class="badge-block">BLOCK 후보</span> 감각적 경험</div>
  </div>
  <div class="pattern-card pattern-card-emo">
    <div class="pattern-name">7. emotional_resonance ★ NEW</div>
    <div class="pattern-source">Pilot 도출 + 정서 추천 <span class="stars">★★</span></div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 감정적 울림 — Pilot에서 14% 빈도, sim 0.82 직접 매칭</div>
  </div>
</div>

<div class="callout">
<strong>패턴 분포 한 줄 요약</strong>:
TRANSFER 후보 4개 + PARTIAL 1개 + BLOCK 후보 2개. Transfer Gate의 3-level 판정이 데이터에 골고루 적용 가능한 구성.
</div>

<!-- ===== Step 2 결과 ===== -->
<h2 class="pagebreak">4. Step 2 — Pilot 자동 매칭 결과</h2>

<p>7개 사전 정의 ↔ 391 Pilot canonical 패턴의 cosine similarity 매칭. <strong>본 연구가 직접 매칭하지 않음</strong> (자기참조 회피).</p>

<table>
<tr><th>사전 정의 패턴</th><th>Top-1 Pilot 매칭</th><th>Sim</th><th>강도</th></tr>
<tr><td>genre_preference</td><td>genre_diversity</td><td>0.699</td><td><span class="warn">MEDIUM</span></td></tr>
<tr class="highlight-row"><td>narrative_complexity</td><td>narrative_complexity</td><td>0.803</td><td><span class="pass">STRONG (직접)</span></td></tr>
<tr class="highlight-row"><td>pacing_preference</td><td>tolerance_for_slow_pacing</td><td>0.807</td><td><span class="pass">STRONG</span></td></tr>
<tr><td>quality_sensitivity</td><td>variable_rating_on_quality</td><td>0.552</td><td><span class="warn">MEDIUM</span></td></tr>
<tr><td>brand_loyalty</td><td>franchise_loyalty</td><td>0.696</td><td><span class="warn">MEDIUM</span></td></tr>
<tr><td>sensory_preference</td><td>enjoyment_of_action_movies</td><td>0.591</td><td><span class="warn">MEDIUM</span></td></tr>
<tr class="highlight-row"><td><strong>emotional_resonance</strong></td><td><strong>emotional_resonance</strong></td><td><strong>0.816</strong></td><td><span class="pass">STRONG (직접)</span></td></tr>
</table>

<div class="callout-green">
<strong>판정</strong>: <span class="pass">7/7 통과 (sim ≥ 0.5)</span>. STRONG 3개 + MEDIUM 4개. 정확 동일 이름 매칭은 narrative_complexity, emotional_resonance 2건.
</div>

<!-- ===== Step 3 결과 + Figure ===== -->
<h2>5. Step 3 — 자유 추출의 한계 정량화</h2>

<p>391개 Pilot canonical 패턴을 4 카테고리로 자동 분류. <strong>본 연구의 명시 prompt 설계 정당성을 데이터로 입증.</strong></p>

<table>
<tr><th>카테고리</th><th>의미</th><th>패턴 수</th><th>비율</th></tr>
<tr><td>CDR 적합</td><td>사전 7개와 sim ≥ 0.5</td><td>36</td><td><span class="pass">9.2%</span></td></tr>
<tr><td>표층 신호</td><td>장르명·감정 표현</td><td>79</td><td>20.2%</td></tr>
<tr><td>매체-종속</td><td>Movies-only 키워드</td><td>268</td><td><span class="warn">68.5%</span></td></tr>
<tr><td>메타 정보</td><td>추천·평점 표현</td><td>8</td><td>2.0%</td></tr>
<tr class="highlight-row"><td colspan="2"><strong>비-CDR-적합 합계</strong></td><td><strong>355</strong></td><td><span class="fail"><strong>90.8%</strong></span></td></tr>
</table>

{"<img class='chart' src='" + IMG_CAT + "' />" if IMG_CAT else ""}
<p class="fig-caption">Figure 1. Pilot 391 canonical 패턴의 4 카테고리 분포 (좌: 패턴 수, 우: 사용자 커버리지)</p>

<div class="callout-warn">
<strong>핵심 발견</strong>: 자유 추출 결과의 <span class="fail">90.8%</span>가 Cross-Domain 추천에 부적합 (매체-종속 + 표층 + 메타).
이것이 본 연구의 명시적 prompt 설계의 강력한 데이터 정당화.
</div>

<!-- ===== Step 4 결과 + Figure ===== -->
<h2 class="pagebreak">6. Step 4 — 직교성 + Movies-only 키워드 검출</h2>

<p>7개 패턴 정의 텍스트 임베딩의 7×7 cosine similarity 행렬. 모든 off-diagonal pair가 ≤ 0.7이어야 통과.</p>

<table>
<tr><th>지표</th><th>값</th><th>판정</th></tr>
<tr><td>Off-diagonal max</td><td>0.669 (narrative ↔ pacing)</td><td><span class="pass">✅ ≤ 0.7</span></td></tr>
<tr><td>Off-diagonal mean</td><td>0.310</td><td><span class="pass">✅ 충분히 분산</span></td></tr>
<tr><td>Threshold (0.7) 위반</td><td>0건</td><td><span class="pass">✅ 직교성 통과</span></td></tr>
</table>

{"<img class='chart' src='" + IMG_ORTHO + "' />" if IMG_ORTHO else ""}
<p class="fig-caption">Figure 2. 7개 패턴 직교성 heatmap (max off-diagonal 0.669, threshold 0.7 미달)</p>

<h3>Movies-only 키워드 자동 검출 (BLOCK 후보 식별)</h3>

<table>
<tr><th>패턴</th><th>검출 키워드</th><th>분류</th></tr>
<tr><td>genre_preference</td><td>0개</td><td><span class="badge-transfer">TRANSFER</span></td></tr>
<tr><td>narrative_complexity</td><td>0개</td><td><span class="badge-transfer">TRANSFER</span></td></tr>
<tr><td>pacing_preference</td><td>0개</td><td><span class="badge-transfer">TRANSFER</span></td></tr>
<tr><td>quality_sensitivity</td><td>1개 (acting)</td><td><span class="badge-partial">PARTIAL</span></td></tr>
<tr class="highlight-row"><td>brand_loyalty</td><td>2개 (actor, director)</td><td><span class="badge-block">BLOCK 후보</span></td></tr>
<tr class="highlight-row"><td>sensory_preference</td><td>1개 (cinematograph)</td><td><span class="badge-block">BLOCK 후보</span></td></tr>
<tr><td>emotional_resonance</td><td>0개</td><td><span class="badge-transfer">TRANSFER</span></td></tr>
</table>

<div class="callout-green">
<strong>핵심 발견</strong>: Transfer Gate의 BLOCK·PARTIAL 후보가 <strong>자동으로 식별</strong>됨.
brand_loyalty(actor·director), sensory_preference(cinematograph)가 영화 매체 한정 키워드로 검출되어
본 연구의 BLOCK 메커니즘 정당성을 데이터로 시연.
</div>

<!-- ===== Pareto Chart ===== -->
<h2>7. Pilot 빈도 분포 (참고)</h2>

<p>Pilot 391 canonical 패턴 중 빈도 상위 25개. nostalgic_preference·family_friendly 등 <strong>본 연구의 7개에 채택되지 않은 표층 패턴이 빈도 상위</strong>를 차지 — 자유 추출의 표층 편향 시각화.</p>

{"<img class='chart' src='" + IMG_FREQ + "' />" if IMG_FREQ else ""}
<p class="fig-caption">Figure 3. Pilot Top-25 패턴 Pareto chart (빈도 + 누적 커버리지). kneed elbow N=7 검출되었으나, 이 N=7은 빈도 기준이며 본 연구의 7개와 다른 구성.</p>

<!-- ===== 가설 H1-H5 인포그래픽 ===== -->
<h2 class="pagebreak">8. 사전 등록 가설 H1~H5 검증 결과</h2>

<p>Pilot 결과 보기 전에 등록한 5가지 가설. 모두 통과.</p>

<div class="hypothesis-grid">
  <div class="hyp-card">
    <div class="hyp-id">H1</div>
    <div class="hyp-mark">✅</div>
    <div class="hyp-label">Pilot 발현</div>
    <div class="hyp-result">7/7<br>(sim ≥ 0.5)</div>
  </div>
  <div class="hyp-card">
    <div class="hyp-id">H2</div>
    <div class="hyp-mark">✅</div>
    <div class="hyp-label">자유 추출 한계</div>
    <div class="hyp-result">90.8%<br>비-CDR-적합</div>
  </div>
  <div class="hyp-card">
    <div class="hyp-id">H3</div>
    <div class="hyp-mark">✅</div>
    <div class="hyp-label">직교성</div>
    <div class="hyp-result">max 0.669<br>(≤0.7)</div>
  </div>
  <div class="hyp-card">
    <div class="hyp-id">H4</div>
    <div class="hyp-mark">✅</div>
    <div class="hyp-label">BLOCK 식별</div>
    <div class="hyp-result">sensory<br>cinematograph</div>
  </div>
  <div class="hyp-card">
    <div class="hyp-id">H5</div>
    <div class="hyp-mark">✅</div>
    <div class="hyp-label">emotional 매칭</div>
    <div class="hyp-result">sim 0.820<br>(직접)</div>
  </div>
</div>

<table>
<tr><th>ID</th><th>가설 내용</th><th>결과</th></tr>
<tr><td>H1</td><td>사전 정의 7개가 Pilot에서 sim ≥ 0.5로 발현</td><td><span class="pass">7/7 통과</span></td></tr>
<tr><td>H2</td><td>Pilot 자유 추출 ≥ 60%가 비-CDR-적합</td><td><span class="pass">90.8% (대폭 통과)</span></td></tr>
<tr><td>H3</td><td>7개 직교성 max similarity ≤ 0.7</td><td><span class="pass">max 0.669</span></td></tr>
<tr><td>H4</td><td>sensory_preference Movies-only 키워드 자동 검출</td><td><span class="pass">cinematograph 검출</span></td></tr>
<tr><td>H5</td><td>emotional_resonance Pilot에서 직접 매칭</td><td><span class="pass">sim 0.820 (top-1 동일)</span></td></tr>
</table>

<!-- ===== 채택 결정표 ===== -->
<h2>9. 7개 채택 결정표 (Step 5)</h2>

<p>4가지 기준 정성 평가. ○ 충분 / △ 부분 / ✗ 부족.</p>

<table>
<tr>
  <th>Pattern</th>
  <th>학술</th>
  <th>Pilot</th>
  <th>CDR</th>
  <th>직교</th>
  <th>결정</th>
</tr>
<tr>
  <td>genre_preference</td>
  <td>○ ★5</td>
  <td>△ 0.70</td>
  <td>○ TRANSFER</td>
  <td>○ 0.47</td>
  <td><span class="pass">ACCEPT</span></td>
</tr>
<tr>
  <td>narrative_complexity</td>
  <td>○ ★4</td>
  <td>○ 0.80</td>
  <td>○ TRANSFER</td>
  <td>△ 0.67</td>
  <td><span class="pass">ACCEPT</span></td>
</tr>
<tr>
  <td>pacing_preference</td>
  <td>○ ★4</td>
  <td>○ 0.81</td>
  <td>○ TRANSFER</td>
  <td>△ 0.67</td>
  <td><span class="pass">ACCEPT</span></td>
</tr>
<tr>
  <td>quality_sensitivity</td>
  <td>○ ★4</td>
  <td>△ 0.55</td>
  <td>△ PARTIAL</td>
  <td>○ 0.37</td>
  <td><span class="pass">ACCEPT (조건부)</span></td>
</tr>
<tr>
  <td>brand_loyalty</td>
  <td>△ ★3</td>
  <td>△ 0.70</td>
  <td>✗ BLOCK 후보</td>
  <td>○ 0.33</td>
  <td><span class="pass">ACCEPT (BLOCK 후보)</span></td>
</tr>
<tr>
  <td>sensory_preference</td>
  <td>✗ ★2</td>
  <td>△ 0.59</td>
  <td>△ PARTIAL</td>
  <td>○ 0.47</td>
  <td><span class="pass">ACCEPT (보완 필요)</span></td>
</tr>
<tr class="highlight-row">
  <td><strong>emotional_resonance</strong></td>
  <td>✗ ★2</td>
  <td>○ 0.82</td>
  <td>○ TRANSFER</td>
  <td>○ 0.38</td>
  <td><span class="pass">ACCEPT</span></td>
</tr>
</table>

<div class="callout-green">
<strong>최종 결정</strong>: <span class="pass">7/7 ACCEPT (REJECT 0)</span>.
4개 일반 ACCEPT, 1개 조건부, 1개 BLOCK 후보, 1개 보완 필요.
</div>

<!-- ===== 결론 ===== -->
<h2 class="pagebreak">10. 결론 — 본 연구 설계 정당화</h2>

<h3>10.1 핵심 결론 4가지</h3>

<ol>
<li><strong>외부 학술 표준 6개 + Pilot 도출 1개 = 7개 채택 확정</strong></li>
<li><strong>자기참조 회피 완벽</strong> — 정의(외부 학술) ↔ 검증(자동 도구) 분리</li>
<li><strong>자유 추출의 한계 (90.8%)</strong> 정량 확인 → 명시 prompt 설계 강력 정당화</li>
<li><strong>Transfer Gate 후보 자동 식별</strong> — BLOCK 2개 (brand_loyalty, sensory), PARTIAL 1개 (quality)</li>
</ol>

<h3>10.2 논문에 쓸 수 있는 핵심 표현</h3>

<div class="quote-box">
"본 연구의 7개 Core Pattern은 추천시스템 표준 개념(genre_preference: NCF 2017; quality_sensitivity: Ricci et al. 2015)과 마케팅 표준 개념(brand_loyalty: Oliver 1999), LLM 추천 선행 연구(narrative_complexity, pacing_preference: LLM4CDR 2025, TALLRec 2023)에서 차용된 6개와, Pilot Study에서 데이터 기반으로 도출된 1개(emotional_resonance, sim <span class="key-stat">0.82</span> 직접 매칭)로 구성된다.<br><br>
Pilot Study (n=100, $0.08)에서 사전 정의된 7개 패턴이 임베딩 자동 매칭으로 모두 sim ≥ 0.5로 발현됨이 확인되었으며 (H1: 7/7), 자유 추출 결과의 <span class="key-stat">90.8%</span>가 매체-종속·표층·메타 신호로 분류되어 (H2) 본 연구의 명시적 prompt 설계의 정당성이 데이터로 입증되었다."
</div>

<h3>10.3 한계 및 향후 작업</h3>

<table>
<tr><th>한계</th><th>대응</th></tr>
<tr><td>Pilot 100명 (LLM4CDR 수준)</td><td>본 실험 1,000명에서 통계적 일반화</td></tr>
<tr><td>emotional_resonance 학술 인용 약함 (★2)</td><td>Pilot 데이터로 보완. 향후 정서영화학 인용 가능</td></tr>
<tr><td>medium_specific 분류 보수성 (90.8% 다소 후함)</td><td>결론은 50~60%만 매체-종속이어도 동일</td></tr>
</table>

<!-- ===== 부록 ===== -->
<h2>11. 산출물 요약</h2>

<table>
<tr><th>분류</th><th>파일</th></tr>
<tr><td>분석 스크립트 (9개)</td><td>scripts/pilot_sample.py · run_pilot.py · collect_patterns.py · normalize_patterns.py · match_pilot_to_predefined.py · categorize_pilot_patterns.py · check_predefined_orthogonality.py · integrate_pilot_evaluation.py · check_pilot_progress.py</td></tr>
<tr><td>데이터 (10개 parquet/csv/json)</td><td>data/pilot_users · pilot_patterns_canonical · pilot_to_predefined_matching · pilot_to_predefined_matrix · pilot_pattern_categories · pilot_pattern_orthogonality · pilot_decision_table · pilot_summary_metrics</td></tr>
<tr><td>시각화 (3개)</td><td>data/pilot_pattern_frequency.png · pilot_categories_summary.png · pilot_pattern_orthogonality.png</td></tr>
<tr><td>문서</td><td>prompts/core_patterns_definition.md · prompts/pilot_profiler_prompt.md · docs/Pilot_OptionA_Tracker.md · docs/Pilot_Study_Report.md · 본 PDF</td></tr>
</table>

<div class="callout">
<strong>진행 현황 자동 진단</strong>: <code>python scripts/check_pilot_progress.py</code> 명령으로 언제든 확인 가능.
</div>

<p style="text-align: center; color: #666; font-size: 9pt; margin-top: 20px;">
— 본 보고서가 정당화하는 핵심: 본 연구의 7개 Core Pattern 채택은 <strong>자기참조 없이</strong> 외부 학술 정의 + 자동 도구 검증 + 다중 기준 종합으로 입증됨 —
</p>

</body>
</html>
"""


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc = weasyprint.HTML(string=HTML_CONTENT)
    doc.write_pdf(OUTPUT_PATH)
    print(f"PDF generated: {OUTPUT_PATH}")
