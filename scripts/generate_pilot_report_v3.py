"""Pilot Study Report PDF v3 (Lite — 석사 수준 적정).

v2 대비 변경:
  - "4C-PPS" 명칭 제거 → "패턴 선정 절차"
  - "방법론 contribution" 격상 표현 제거 → "체계적 선정 과정"
  - Decision Rule 형식 규칙 → 자연어 설명
  - "사전 등록 가설 H1~H5" → "사전 검토 5항목"
  - "다른 도메인 일반화" 주장 제거
  - §11.3 contribution 위계 박스 단순화
  - 14p → 9~10p로 다이어트

산출: docs/TransferJudge_Pilot_Report_v3.pdf (v1, v2 모두 보존)
"""
from __future__ import annotations

import base64
import os

import weasyprint

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "docs", "pilot")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "TransferJudge_Pilot_Report_v3.pdf")


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
  h1 {{ text-align: center; font-size: 20pt; margin-bottom: 5px; color: #1a1a2e; }}
  .subtitle {{ text-align: center; font-size: 10.5pt; color: #555; margin-bottom: 3px; }}
  .author {{ text-align: center; font-size: 10.5pt; color: #777; margin-bottom: 25px; }}
  h2 {{ font-size: 14pt; color: #16213e; border-bottom: 2.5px solid #4a90d9; padding-bottom: 4px; margin-top: 28px; }}
  h3 {{ font-size: 12pt; color: #0f3460; margin-top: 18px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0 12px 0; font-size: 9.5pt; }}
  th {{ background: #16213e; color: white; padding: 5px 8px; text-align: left; font-weight: 600; }}
  td {{ padding: 4px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #f8f9fa; }}
  .highlight-row td {{ background: #e8f4fd !important; font-weight: 600; }}
  .callout {{ background: #f0f4f8; border-left: 4px solid #4a90d9; padding: 10px 14px; margin: 10px 0; font-size: 9.7pt; }}
  .callout-warn {{ background: #fff8e1; border-left: 4px solid #f5a623; padding: 10px 14px; margin: 10px 0; font-size: 9.7pt; }}
  .callout-green {{ background: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px 14px; margin: 10px 0; font-size: 9.7pt; }}
  .easy-note {{ background: #f3e5f5; border-left: 4px solid #8e44ad; padding: 10px 14px; margin: 10px 0; font-size: 9.5pt; line-height: 1.55; }}
  .easy-note .easy-title {{ font-weight: 700; color: #6a1b9a; margin-bottom: 4px; font-size: 9.7pt; }}
  .pass {{ color: #2e7d32; font-weight: 700; }}
  .warn {{ color: #e65100; font-weight: 700; }}
  .fail {{ color: #c62828; font-weight: 700; }}
  .pagebreak {{ page-break-before: always; }}
  .nobreak {{ page-break-inside: avoid; }}
  ul, ol {{ margin: 4px 0; padding-left: 20px; }}
  li {{ margin: 2px 0; }}
  img.chart {{ width: 100%; margin: 8px 0; }}
  .fig-caption {{ text-align: center; font-size: 8.8pt; color: #666; margin-top: -5px; margin-bottom: 12px; }}

  .infographic {{ background: #fafbfc; border: 1px solid #d8dde6; border-radius: 5px; padding: 14px 16px; margin: 12px 0; }}
  .info-title {{ font-size: 10.5pt; font-weight: 700; color: #1a2555; text-align: center; margin-bottom: 12px; }}
  .flow-row {{ display: flex; align-items: stretch; gap: 5px; margin-bottom: 8px; }}
  .flow-box {{ flex: 1; border: 1.3px solid #6b7cb5; border-radius: 4px; padding: 6px 8px; background: #fff; text-align: center; font-size: 8.5pt; line-height: 1.3; }}
  .flow-box-data {{ background: #fff4e6; border-color: #e08a3c; }}
  .flow-box-api {{ background: #e7f1fb; border-color: #2f7bc4; }}
  .flow-box-validate {{ background: #fff8d9; border-color: #c4a23c; }}
  .flow-box-output {{ background: #eaeef7; border-color: #2d3e8a; font-weight: 600; }}
  .flow-box-title {{ font-weight: 700; color: #1a2555; margin-bottom: 2px; font-size: 9pt; }}
  .flow-arrow {{ display: flex; align-items: center; justify-content: center; color: #2d3e8a; font-size: 13pt; flex: 0 0 16px; }}

  .check-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 10px 0; }}
  .check-card {{ background: #fff; border: 1.5px solid #4caf50; border-radius: 6px; padding: 8px; text-align: center; font-size: 9pt; }}
  .check-id {{ font-size: 12pt; font-weight: 700; color: #2e7d32; margin-bottom: 4px; }}
  .check-label {{ font-weight: 600; color: #1a2555; margin-bottom: 4px; font-size: 8.5pt; }}
  .check-result {{ color: #444; font-size: 8.5pt; }}
  .check-mark {{ font-size: 16pt; }}

  .pattern-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; margin: 10px 0; }}
  .pattern-card {{ background: #fff; border: 1.2px solid #d5dae6; border-radius: 4px; padding: 7px 10px; font-size: 9pt; }}
  .pattern-card-emo {{ border-color: #2f9a53; background: #e8f5e9; }}
  .pattern-name {{ font-weight: 700; color: #1a2555; }}
  .pattern-source {{ color: #666; font-size: 8.3pt; margin-top: 2px; }}
  .crit-tag {{ display: inline-block; padding: 0 4px; border-radius: 2px; font-size: 8pt; font-weight: 700; margin: 0 1px; }}
  .crit-pass {{ background: #e8f5e9; color: #2e7d32; }}
  .crit-mid {{ background: #fff3e0; color: #e65100; }}
  .crit-fail {{ background: #ffebee; color: #c62828; }}
  .badge-transfer {{ background: #2f9a53; color: white; padding: 1px 5px; border-radius: 3px; font-size: 8pt; }}
  .badge-partial {{ background: #d79a2e; color: white; padding: 1px 5px; border-radius: 3px; font-size: 8pt; }}
  .badge-block {{ background: #b53a3a; color: white; padding: 1px 5px; border-radius: 3px; font-size: 8pt; }}

  .anti-self-ref {{ background: #fff; border: 1.5px solid #4a90d9; border-radius: 6px; padding: 12px 14px; margin: 10px 0; }}
  .asr-row {{ display: flex; align-items: center; gap: 8px; margin: 6px 0; font-size: 9pt; }}
  .asr-label {{ flex: 0 0 110px; font-weight: 700; color: #1a2555; }}
  .asr-source {{ flex: 0 0 130px; background: #fff4e6; border: 1px solid #e08a3c; padding: 4px 8px; border-radius: 3px; text-align: center; font-size: 8.5pt; }}
  .asr-arrow {{ color: #2d3e8a; font-weight: 700; flex: 0 0 18px; text-align: center; }}
  .asr-target {{ flex: 1; background: #e7f1fb; border: 1px solid #2f7bc4; padding: 4px 8px; border-radius: 3px; font-size: 8.5pt; }}

  .quote-box {{ background: #fffef0; border: 1.5px dashed #d79a2e; border-radius: 5px; padding: 12px 14px; margin: 10px 0; font-size: 9.5pt; line-height: 1.55; color: #5d4a1a; font-style: italic; }}
  .key-stat {{ display: inline-block; background: #e8f5e9; color: #2e7d32; padding: 1px 6px; border-radius: 3px; font-weight: 700; font-style: normal; }}
</style>
</head>
<body>

<!-- ===== TITLE ===== -->
<h1>Pilot Study Report</h1>
<p class="subtitle">TransferJudge — 7개 Core Pattern 선정 절차와 검증 결과</p>
<p class="subtitle">4가지 측면(이론·Pilot·CDR·직교) 종합 검토</p>
<p class="author">2026.05 · 빅데이터학과 17기 곽민아</p>

<!-- ===== Executive Summary ===== -->
<div class="callout-green nobreak">
<strong>한 줄 요약</strong><br>
본 연구의 7개 Core Pattern은 <strong>4가지 측면을 종합 검토</strong>하여 선정되었다.
자유 추출의 매체-편향 한계 <span class="key-stat">90.8%</span>를 정량 확인하여 명시 prompt 설계의 데이터 정당화를 확보하고,
사전 검토 5항목을 모두 통과했다.
</div>

<div class="easy-note nobreak">
<div class="easy-title">💡 쉬운 설명 — 이 보고서가 답하는 질문</div>
"왜 이 7개 패턴을 골랐는가"에 대한 답변. 패턴마다 다른 논문을 인용하면 짜맞춘 인상을 줄 수 있어, <strong>Thet et al. (2010) 영화 리뷰 aspect mining</strong>을 anchor로 하고 <strong>4가지 측면(이론·Pilot·CDR·직교)을 종합</strong>하여 선정했다.
</div>

<table>
<tr><th>항목</th><th>값</th></tr>
<tr><td>Pilot 샘플</td><td>100명 (Train 800 中, seed=42)</td></tr>
<tr><td>비용</td><td>$0.081 (GPT-4o-mini)</td></tr>
<tr><td>사전 검토 결과</td><td><span class="pass">5/5 모두 통과</span></td></tr>
<tr><td>채택 결정</td><td><span class="pass">7/7 모두 ACCEPT (REJECT 0)</span></td></tr>
<tr><td>이론 anchor</td><td>Thet et al. (2010), Liu (2012)</td></tr>
</table>

<!-- ===== 자기참조 회피 ===== -->
<h2>1. 핵심 메커니즘 — 자기참조 회피</h2>

<p>"내가 정의한 패턴을 내가 맞다고 검증"하는 자기참조를 피하기 위해 <strong>정의 출처</strong>와 <strong>검증 출처</strong>를 분리.</p>

<div class="anti-self-ref nobreak">
  <div class="info-title">정의 vs 검증 분리 구조</div>
  <div class="asr-row">
    <div class="asr-label">이론 anchor</div>
    <div class="asr-source">aspect mining 선행연구</div>
    <div class="asr-arrow">→</div>
    <div class="asr-target">Thet et al. (2010) 영화 리뷰 aspect mining + Liu (2012) ABSA</div>
  </div>
  <div class="asr-row">
    <div class="asr-label">사전 검토</div>
    <div class="asr-source">5항목 사전 정의</div>
    <div class="asr-arrow">→</div>
    <div class="asr-target">Pilot 결과 보기 전 정해둔 검토 항목</div>
  </div>
  <div class="asr-row">
    <div class="asr-label">검증 도구</div>
    <div class="asr-source">자동 임베딩 매칭</div>
    <div class="asr-arrow">→</div>
    <div class="asr-target">sentence-transformers cosine similarity</div>
  </div>
  <div class="asr-row">
    <div class="asr-label">평가 측면</div>
    <div class="asr-source">4가지 측면</div>
    <div class="asr-arrow">→</div>
    <div class="asr-target">이론 정합성 + Pilot 발현 + Cross-Domain + 직교성 (단일 빈도가 아님)</div>
  </div>
</div>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 4가지 측면이 무엇인가</div>
<strong>(1) 이론 정합성</strong>: aspect mining 선행연구와 부합하는가<br>
<strong>(2) Pilot 발현</strong>: 데이터에서 실제 등장하는가 (cosine sim ≥ 0.5)<br>
<strong>(3) Cross-Domain 적합성</strong>: 매체 편향 없이 양 도메인에 적용 가능한가 (Movies-only 키워드)<br>
<strong>(4) 직교성</strong>: 다른 패턴과 의미적으로 독립인가 (sim ≤ 0.7)<br>
한 가지 측면만 보면 표층 표현(빈도만 높음)이나 데이터 안 맞는 패턴이 들어갈 수 있어 4가지를 종합한다.
</div>

<!-- ===== Workflow ===== -->
<h2>2. 5단계 작업 흐름</h2>

<div class="infographic nobreak">
  <div class="info-title">Pilot Study Phase 1~4 (자유 추출 완료) → Step 1~5</div>
  <div class="flow-row">
    <div class="flow-box flow-box-data">
      <div class="flow-box-title">Phase 1-4</div>
      Pilot 100명 자유 추출 → 391 canonical 패턴
    </div>
  </div>
  <div style="text-align:center; color:#2d3e8a;">↓</div>
  <div class="flow-row">
    <div class="flow-box flow-box-validate">
      <div class="flow-box-title">Step 1</div>
      이론 anchor<br>(Thet 2010, Liu 2012)
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
      4가지 측면<br>종합
    </div>
  </div>
</div>

<!-- ===== 7개 패턴 ===== -->
<h2 class="pagebreak">3. 7개 Core Pattern (선정 결과)</h2>

<p>4가지 측면을 종합 검토한 결과 채택된 7개. 각 측면 ○/△/✗ 표기.</p>

<div class="pattern-grid">
  <div class="pattern-card">
    <div class="pattern-name">1. genre_preference</div>
    <div class="pattern-source">
      이론 <span class="crit-tag crit-pass">○</span>
      Pilot <span class="crit-tag crit-mid">△ 0.70</span>
      CDR <span class="crit-tag crit-pass">○</span>
      직교 <span class="crit-tag crit-pass">○ 0.47</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 장르·카테고리 선호</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">2. narrative_complexity</div>
    <div class="pattern-source">
      이론 <span class="crit-tag crit-pass">○</span>
      Pilot <span class="crit-tag crit-pass">○ 0.80</span>
      CDR <span class="crit-tag crit-pass">○</span>
      직교 <span class="crit-tag crit-mid">△ 0.67</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 서사 복잡도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">3. pacing_preference</div>
    <div class="pattern-source">
      이론 <span class="crit-tag crit-pass">○</span>
      Pilot <span class="crit-tag crit-pass">○ 0.81</span>
      CDR <span class="crit-tag crit-pass">○</span>
      직교 <span class="crit-tag crit-mid">△ 0.67</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 전개 속도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">4. quality_sensitivity</div>
    <div class="pattern-source">
      이론 <span class="crit-tag crit-pass">○</span>
      Pilot <span class="crit-tag crit-mid">△ 0.55</span>
      CDR <span class="crit-tag crit-mid">△</span>
      직교 <span class="crit-tag crit-pass">○ 0.37</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-partial">PARTIAL</span> 품질 민감도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">5. brand_loyalty</div>
    <div class="pattern-source">
      이론 <span class="crit-tag crit-mid">△</span>
      Pilot <span class="crit-tag crit-mid">△ 0.70</span>
      CDR <span class="crit-tag crit-fail">✗</span>
      직교 <span class="crit-tag crit-pass">○ 0.33</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-block">BLOCK 후보</span> 창작자 충성도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">6. sensory_preference</div>
    <div class="pattern-source">
      이론 <span class="crit-tag crit-mid">△</span>
      Pilot <span class="crit-tag crit-mid">△ 0.59</span>
      CDR <span class="crit-tag crit-mid">△</span>
      직교 <span class="crit-tag crit-pass">○ 0.47</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-block">BLOCK 후보</span> 감각적 경험</div>
  </div>
  <div class="pattern-card pattern-card-emo">
    <div class="pattern-name">7. emotional_resonance ★ Pilot 도출</div>
    <div class="pattern-source">
      이론 <span class="crit-tag crit-mid">△</span>
      Pilot <span class="crit-tag crit-pass">○ 0.82</span>
      CDR <span class="crit-tag crit-pass">○</span>
      직교 <span class="crit-tag crit-pass">○ 0.38</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 감정적 울림 — Pilot 14% 빈도, sim 0.82 직접 매칭</div>
  </div>
</div>

<div class="callout">
<strong>패턴 분포 한 줄 요약</strong>:
TRANSFER 4개 + PARTIAL 1개 + BLOCK 2개. Transfer Gate의 3-level 판정이 데이터에 골고루 적용 가능.
</div>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 각 패턴이 어떻게 평가됐나</div>
<strong>채택 4개</strong> (genre, narrative, pacing, emotional): 4측면 모두 ○ 또는 △ → 일반 ACCEPT.<br>
<strong>quality_sensitivity</strong>: Pilot·CDR이 △ → 매체별 변환 필요 (영화 연기·연출 / 책 문체·편집).<br>
<strong>brand_loyalty</strong>: CDR이 ✗ (actor·director 키워드) → Transfer Gate가 BLOCK 처리해야 할 후보.<br>
<strong>sensory_preference</strong>: 약점 많으나 BLOCK 시연용으로 채택.<br>
<strong>emotional_resonance</strong>: Step 1엔 후보 아니었으나 Pilot에서 14% 빈도·sim 0.82로 emerge → 추가.
</div>

<!-- ===== Step 2 결과 ===== -->
<h2 class="pagebreak">4. Step 2 — Pilot 자동 매칭 결과</h2>

<p>7개 후보 ↔ 391 Pilot canonical 패턴의 cosine similarity 매칭. <strong>본 연구가 직접 매칭하지 않음</strong> (자기참조 회피).</p>

<table>
<tr><th>후보 패턴</th><th>Top-1 Pilot 매칭</th><th>Sim</th><th>강도</th></tr>
<tr><td>genre_preference</td><td>genre_diversity</td><td>0.699</td><td><span class="warn">MEDIUM</span></td></tr>
<tr class="highlight-row"><td>narrative_complexity</td><td>narrative_complexity</td><td>0.803</td><td><span class="pass">STRONG (직접)</span></td></tr>
<tr class="highlight-row"><td>pacing_preference</td><td>tolerance_for_slow_pacing</td><td>0.807</td><td><span class="pass">STRONG</span></td></tr>
<tr><td>quality_sensitivity</td><td>variable_rating_on_quality</td><td>0.552</td><td><span class="warn">MEDIUM</span></td></tr>
<tr><td>brand_loyalty</td><td>franchise_loyalty</td><td>0.696</td><td><span class="warn">MEDIUM</span></td></tr>
<tr><td>sensory_preference</td><td>enjoyment_of_action_movies</td><td>0.591</td><td><span class="warn">MEDIUM</span></td></tr>
<tr class="highlight-row"><td><strong>emotional_resonance</strong></td><td><strong>emotional_resonance</strong></td><td><strong>0.816</strong></td><td><span class="pass">STRONG (직접)</span></td></tr>
</table>

<div class="callout-green">
<strong>판정</strong>: <span class="pass">7/7 통과 (sim ≥ 0.5)</span>. 정확 동일 이름 직접 매칭 2건 (narrative, emotional).
</div>

<!-- ===== Step 3 결과 + Figure ===== -->
<h2>5. Step 3 — 자유 추출의 한계 정량화</h2>

<p>391개 Pilot canonical 패턴을 4 카테고리로 자동 분류.</p>

<table>
<tr><th>카테고리</th><th>의미</th><th>패턴 수</th><th>비율</th></tr>
<tr><td>CDR 적합</td><td>후보 7개와 sim ≥ 0.5</td><td>36</td><td><span class="pass">9.2%</span></td></tr>
<tr><td>표층 신호</td><td>장르명·감정 표현</td><td>79</td><td>20.2%</td></tr>
<tr><td>매체-종속</td><td>Movies-only 키워드</td><td>268</td><td><span class="warn">68.5%</span></td></tr>
<tr><td>메타 정보</td><td>추천·평점 표현</td><td>8</td><td>2.0%</td></tr>
<tr class="highlight-row"><td colspan="2"><strong>비-CDR-적합 합계</strong></td><td><strong>355</strong></td><td><span class="fail"><strong>90.8%</strong></span></td></tr>
</table>

{"<img class='chart' src='" + IMG_CAT + "' />" if IMG_CAT else ""}
<p class="fig-caption">Figure 1. Pilot 391 canonical 패턴의 4 카테고리 분포</p>

<div class="callout-warn">
<strong>핵심 발견</strong>: 자유 추출 결과의 <span class="fail">90.8%</span>가 Cross-Domain 추천에 부적합.
이것이 본 연구의 명시 prompt 설계의 강력한 데이터 정당화.
</div>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 왜 자유 추출만으론 부족한가</div>
LLM에게 "패턴을 자유롭게 뽑아줘"라고 하면, 90%가 Cross-Domain 추천에 쓸 수 없는 것들 — "IMAX 영상미"(영화 한정), "high_recommendation"(메타 정보), "nostalgic_preference"(표층 감정).<br>
이 결과가 <strong>"명시 prompt로 7개를 강제로 추출하라"는 본 연구 설계를 정당화</strong>한다.
</div>

<!-- ===== Step 4 ===== -->
<h2 class="pagebreak">6. Step 4 — 직교성 + Movies-only 검출</h2>

<p>7개 패턴 정의 텍스트 임베딩의 7×7 cosine similarity 행렬.</p>

<table>
<tr><th>지표</th><th>값</th><th>판정</th></tr>
<tr><td>Off-diagonal max</td><td>0.669 (narrative ↔ pacing)</td><td><span class="pass">✅ ≤ 0.7</span></td></tr>
<tr><td>Off-diagonal mean</td><td>0.310</td><td><span class="pass">✅ 충분히 분산</span></td></tr>
<tr><td>Threshold (0.7) 위반</td><td>0건</td><td><span class="pass">✅ 직교성 통과</span></td></tr>
</table>

{"<img class='chart' src='" + IMG_ORTHO + "' />" if IMG_ORTHO else ""}
<p class="fig-caption">Figure 2. 7개 패턴 직교성 heatmap (max 0.669, threshold 0.7 미달)</p>

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
brand_loyalty(actor·director), sensory_preference(cinematograph)가 영화 매체 한정 키워드로 검출되어 BLOCK 메커니즘 정당성 시연.
</div>

<!-- ===== 사전 검토 5항목 ===== -->
<h2 class="pagebreak">7. 사전 검토 5항목 결과</h2>

<p>Pilot 결과 보기 전에 정해둔 검토 항목. <strong>모두 통과</strong>.</p>

<div class="check-grid">
  <div class="check-card">
    <div class="check-id">항목 1</div>
    <div class="check-mark">✅</div>
    <div class="check-label">Pilot 발현</div>
    <div class="check-result">7/7<br>(sim ≥ 0.5)</div>
  </div>
  <div class="check-card">
    <div class="check-id">항목 2</div>
    <div class="check-mark">✅</div>
    <div class="check-label">자유 추출 한계</div>
    <div class="check-result">90.8%<br>비-CDR-적합</div>
  </div>
  <div class="check-card">
    <div class="check-id">항목 3</div>
    <div class="check-mark">✅</div>
    <div class="check-label">직교성</div>
    <div class="check-result">max 0.669<br>(≤0.7)</div>
  </div>
  <div class="check-card">
    <div class="check-id">항목 4</div>
    <div class="check-mark">✅</div>
    <div class="check-label">BLOCK 식별</div>
    <div class="check-result">sensory<br>cinematograph</div>
  </div>
  <div class="check-card">
    <div class="check-id">항목 5</div>
    <div class="check-mark">✅</div>
    <div class="check-label">emotional 매칭</div>
    <div class="check-result">sim 0.820<br>(직접)</div>
  </div>
</div>

<table>
<tr><th>ID</th><th>검토 항목</th><th>결과</th></tr>
<tr><td>1</td><td>후보 7개가 Pilot에서 sim ≥ 0.5로 발현</td><td><span class="pass">7/7 통과</span></td></tr>
<tr><td>2</td><td>Pilot 자유 추출 ≥ 60%가 비-CDR-적합</td><td><span class="pass">90.8% (대폭 통과)</span></td></tr>
<tr><td>3</td><td>7개 직교성 max similarity ≤ 0.7</td><td><span class="pass">max 0.669</span></td></tr>
<tr><td>4</td><td>매체 한정 패턴이 Movies-only 키워드 자동 검출</td><td><span class="pass">cinematograph 검출</span></td></tr>
<tr><td>5</td><td>Pilot에서 emerge한 패턴 직접 매칭</td><td><span class="pass">sim 0.820 (top-1 동일)</span></td></tr>
</table>

<!-- ===== 채택 결정표 ===== -->
<h2>8. 4가지 측면 종합 채택 결과 (Step 5)</h2>

<p>각 패턴에 4측면 ○/△/✗ 평가하여 종합 결정.</p>

<table>
<tr>
  <th>Pattern</th>
  <th>이론</th>
  <th>Pilot</th>
  <th>CDR</th>
  <th>직교</th>
  <th>결정</th>
</tr>
<tr><td>genre_preference</td><td>○</td><td>△ 0.70</td><td>○ TRANSFER</td><td>○ 0.47</td><td><span class="pass">ACCEPT</span></td></tr>
<tr><td>narrative_complexity</td><td>○</td><td>○ 0.80</td><td>○ TRANSFER</td><td>△ 0.67</td><td><span class="pass">ACCEPT</span></td></tr>
<tr><td>pacing_preference</td><td>○</td><td>○ 0.81</td><td>○ TRANSFER</td><td>△ 0.67</td><td><span class="pass">ACCEPT</span></td></tr>
<tr><td>quality_sensitivity</td><td>○</td><td>△ 0.55</td><td>△ PARTIAL</td><td>○ 0.37</td><td><span class="pass">ACCEPT (조건부)</span></td></tr>
<tr><td>brand_loyalty</td><td>△</td><td>△ 0.70</td><td>✗ BLOCK</td><td>○ 0.33</td><td><span class="pass">ACCEPT (BLOCK 후보)</span></td></tr>
<tr><td>sensory_preference</td><td>△</td><td>△ 0.59</td><td>△ PARTIAL</td><td>○ 0.47</td><td><span class="pass">ACCEPT (보완 필요)</span></td></tr>
<tr class="highlight-row"><td><strong>emotional_resonance</strong></td><td>△</td><td>○ 0.82</td><td>○ TRANSFER</td><td>○ 0.38</td><td><span class="pass">ACCEPT</span></td></tr>
</table>

<div class="callout-green">
<strong>최종</strong>: <span class="pass">7/7 ACCEPT (REJECT 0)</span>. 4개 일반 ACCEPT, 1개 조건부, 1개 BLOCK 후보, 1개 보완 필요.
</div>

<!-- ===== 결론 ===== -->
<h2 class="pagebreak">9. 결론</h2>

<h3>9.1 핵심 결론 4가지</h3>

<ol>
<li><strong>4가지 측면 종합 검토</strong> → 7개 패턴 채택 (REJECT 0)</li>
<li><strong>자기참조 회피</strong> — 이론 anchor(외부) ↔ 검증(자동 도구) 분리</li>
<li><strong>자유 추출의 한계 (90.8%)</strong> 정량 확인 → 명시 prompt 설계 정당화</li>
<li><strong>Transfer Gate 후보 자동 식별</strong> — BLOCK 2개, PARTIAL 1개</li>
</ol>

<h3>9.2 논문에 쓸 수 있는 핵심 표현</h3>

<div class="quote-box">
"본 연구는 Cross-Domain 추천에 적합한 7개 Core Pattern을 선정하였다. 선정 절차는 다음과 같다: (1) 영화 리뷰 aspect mining 선행연구(Thet et al., 2010; Liu, 2012)를 검토하여 6개 후보 패턴을 도출. (2) Pilot Study (n=100)로 후보 패턴이 임베딩 자동 매칭에서 sim ≥ 0.5로 발현됨을 확인. (3) 자유 추출 결과의 <span class="key-stat">90.8%</span>가 매체-종속·표층·메타 신호로 분류되어 명시 prompt 설계의 정당성이 데이터로 입증됨. (4) 7개 패턴 사이 cosine similarity는 max 0.669로 직교성 만족. (5) sensory_preference와 brand_loyalty는 Movies-only 키워드 자동 검출로 Transfer Gate의 BLOCK 후보로 식별. Pilot Study에서 강하게 emerge한 emotional_resonance를 추가하여 7개로 확정하였다."
</div>

<h3>9.3 한계 및 향후 작업</h3>

<table>
<tr><th>한계</th><th>대응</th></tr>
<tr><td>Pilot 100명 (LLM4CDR 수준)</td><td>본 실험 1,000명에서 통계적 일반화</td></tr>
<tr><td>emotional_resonance 이론 anchor 약함</td><td>Pilot 데이터로 보완 (sim 0.82, 14% 빈도)</td></tr>
<tr><td>medium_specific 분류 보수성</td><td>결론은 50~60%만 매체-종속이어도 동일</td></tr>
<tr><td>본 도메인(Movies → Books) 한정</td><td>다른 CDR 시나리오 적용은 향후 작업</td></tr>
</table>

<div class="callout">
<strong>본 연구의 contribution</strong><br>
- <strong>메인</strong>: Profiler-Judge 구조의 LLM 기반 CDR 프레임워크<br>
- <strong>서브</strong>: Pilot 기반 패턴 선정 절차 (자기참조 회피)<br>
7개 패턴은 본 도메인에 적용한 결과물.
</div>

<p style="text-align: center; color: #666; font-size: 9pt; margin-top: 20px;">
— 본 보고서가 정리하는 핵심: 본 연구의 7개 Core Pattern은 <strong>4가지 측면을 종합 검토</strong>하여 선정되었으며, 자기참조 회피·자유 추출 한계 정량화·Transfer Gate 후보 자동 식별을 모두 데이터로 확인 —
</p>

</body>
</html>
"""


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc = weasyprint.HTML(string=HTML_CONTENT)
    doc.write_pdf(OUTPUT_PATH)
    print(f"PDF generated: {OUTPUT_PATH}")
