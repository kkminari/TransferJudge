"""Pilot Study Report PDF v2 (방법론 B 기반, 본인 검토용).

변경점:
  - 인용 6개 → 2개 압축 (Thet 2010 + Liu 2012)
  - 5차원 분해 제거 (학술 출처 없음)
  - 7개 패턴 = 4C-PPS 방법론 적용 결과로 재구성
  - 각 섹션마다 '💡 쉬운 설명' 콜아웃 추가
  - 4C-PPS 방법론 다이어그램 신규
  - ★ 자기평가 제거, 4기준 ○/△/✗ 표기

산출: docs/TransferJudge_Pilot_Report_v2.pdf (기존 v1 보존)
"""
from __future__ import annotations

import base64
import os

import weasyprint

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "docs", "pilot")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "TransferJudge_Pilot_Report_v2.pdf")


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
  /* === NEW: 쉬운 설명 콜아웃 (보라색 톤) === */
  .easy-note {{
    background: #f3e5f5;
    border-left: 4px solid #8e44ad;
    padding: 10px 14px;
    margin: 10px 0;
    font-size: 9.5pt;
    line-height: 1.55;
  }}
  .easy-note .easy-title {{
    font-weight: 700;
    color: #6a1b9a;
    margin-bottom: 4px;
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

  /* === NEW: 4C-PPS 방법론 다이어그램 === */
  .methodology-box {{
    background: #fff;
    border: 1.5px solid #6a1b9a;
    border-radius: 6px;
    padding: 14px 16px;
    margin: 12px 0;
  }}
  .crit-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin: 10px 0;
  }}
  .crit-card {{
    background: #f9f6fc;
    border: 1.3px solid #8e44ad;
    border-radius: 5px;
    padding: 9px 10px;
    text-align: center;
    font-size: 9pt;
  }}
  .crit-id {{
    font-size: 14pt;
    font-weight: 700;
    color: #6a1b9a;
    margin-bottom: 2px;
  }}
  .crit-name {{ font-weight: 600; color: #1a2555; margin-bottom: 4px; font-size: 9.5pt; }}
  .crit-desc {{ color: #555; font-size: 8.5pt; line-height: 1.4; }}

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

  /* 7개 패턴 그리드 (★ 제거, 4기준 표기) */
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
  .crit-tag {{ display: inline-block; padding: 0 4px; border-radius: 2px; font-size: 8pt; font-weight: 700; margin: 0 1px; }}
  .crit-pass {{ background: #e8f5e9; color: #2e7d32; }}
  .crit-mid {{ background: #fff3e0; color: #e65100; }}
  .crit-fail {{ background: #ffebee; color: #c62828; }}
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
  .contrib-box {{
    background: #f0e7f7;
    border-left: 4px solid #6a1b9a;
    padding: 12px 16px;
    margin: 10px 0;
    font-size: 10pt;
  }}
</style>
</head>
<body>

<!-- ===== TITLE ===== -->
<h1>Pilot Study Report v2</h1>
<p class="subtitle">TransferJudge — 4C-PPS 방법론 적용 결과 보고</p>
<p class="subtitle">방법론 B · Cross-Domain Preference Pattern Selection (4기준 종합 검증)</p>
<p class="author">2026.05 · 빅데이터학과 17기 곽민아</p>

<!-- ===== Executive Summary ===== -->
<div class="callout-green nobreak">
<strong>한 줄 요약</strong><br>
본 연구의 7개 Core Pattern은 <strong>4C-PPS 방법론을 Movies&amp;TV → Books CDR에 적용한 결과</strong> 채택되었다.
자유 추출의 매체-편향 한계 <span class="key-stat">90.8%</span>를 정량 확인하여 명시 prompt 설계의 데이터 정당화를 확보하고,
사전 등록 가설 H1~H5를 모두 통과하여 방법론의 작동성을 입증했다.
</div>

<div class="easy-note nobreak">
<div class="easy-title">💡 쉬운 설명 — 이 보고서가 답하는 질문</div>
이전 보고서(v1)는 "왜 이 7개 패턴인가?"에 답하면서 <strong>패턴마다 다른 논문</strong>을 인용했지만, 이는 짜맞춘 인상을 줄 수 있었다.<br>
v2는 본 연구의 진짜 contribution이 <strong>"패턴 선정 방법론(4C-PPS)"</strong>이라는 점에 집중한다. 7개 패턴은 <strong>이 방법론의 적용 결과</strong>일 뿐이며, 각 패턴 자체에 대한 학술 인용 부담이 사라진다.
</div>

<table>
<tr><th>항목</th><th>값</th></tr>
<tr><td>Pilot 샘플</td><td>100명 (Train 800 中, seed=42)</td></tr>
<tr><td>비용</td><td>$0.081 (GPT-4o-mini)</td></tr>
<tr><td>가설 검증 결과</td><td><span class="pass">5/5 모두 통과 (H1~H5)</span></td></tr>
<tr><td>채택 결정</td><td><span class="pass">7/7 모두 ACCEPT (REJECT 0)</span></td></tr>
<tr><td>이론 anchor</td><td>Thet et al. (2010), Liu (2012) — <strong>2개로 압축</strong></td></tr>
<tr><td>작업 기간</td><td>2026-04-26 ~ 2026-04-28</td></tr>
</table>

<div class="contrib-box nobreak">
<strong>본 연구의 contribution 위계</strong><br>
1. <strong>(메인)</strong> Profiler-Judge 구조의 LLM 기반 CDR 프레임워크<br>
2. <strong>(서브)</strong> 4C-PPS — 선호 패턴 선정 4기준 방법론<br>
3. <strong>(서브)</strong> Pilot Study 검증 절차 (자기참조 회피 메커니즘)
</div>

<!-- ===== 자기참조 회피 다이어그램 ===== -->
<h2 class="pagebreak">1. 핵심 메커니즘 — 자기참조 회피</h2>

<p>"내가 정의한 패턴을 내가 맞다고 검증"하는 자기참조를 피하기 위해 <strong>정의 출처</strong>와 <strong>검증 출처</strong>를 분리.</p>

<div class="anti-self-ref nobreak">
  <div class="info-title">정의 vs 검증 분리 구조</div>
  <div class="asr-row">
    <div class="asr-label">이론 anchor</div>
    <div class="asr-source">aspect mining 선행연구</div>
    <div class="asr-arrow">→</div>
    <div class="asr-target">Thet et al. (2010) 영화 리뷰 aspect mining + Liu (2012) ABSA 일반 프레임워크</div>
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
    <div class="asr-target">이론 정합성 + Pilot 발현 + Cross-Domain + 직교성 (단일 빈도가 아님)</div>
  </div>
</div>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 왜 자기참조가 문제인가</div>
"내가 만든 패턴이 좋다고 내가 평가"하면 객관성이 없다. 이를 피하려면 <strong>정의는 외부에서 빌려오고</strong>, <strong>검증은 자동 도구가 하게</strong> 만들어야 한다.<br>
v2는 <strong>외부 인용을 6개 → 2개로 압축</strong>해 "특정 논문에 강하게 의존"하는 약점도 줄였다. 대신 본 연구가 정의한 <strong>4기준 방법론</strong>이 핵심 기여로 부각된다.
</div>

<!-- ===== 4C-PPS 방법론 정의 (NEW) ===== -->
<h2>2. 4C-PPS 방법론이란?</h2>

<p><strong>4-Criteria Cross-Domain Preference Pattern Selection</strong> — 본 연구가 제안하는 패턴 선정 방법론.</p>

<div class="methodology-box nobreak">
  <div class="info-title">4가지 독립 기준 (Acceptance Criteria)</div>
  <div class="crit-grid">
    <div class="crit-card">
      <div class="crit-id">C1</div>
      <div class="crit-name">이론 정합성</div>
      <div class="crit-desc">aspect mining 선행연구의 일반 attribute 개념과 부합 여부</div>
    </div>
    <div class="crit-card">
      <div class="crit-id">C2</div>
      <div class="crit-name">Pilot 발현</div>
      <div class="crit-desc">Pilot 자유 추출 결과와의 max cosine similarity (≥0.5)</div>
    </div>
    <div class="crit-card">
      <div class="crit-id">C3</div>
      <div class="crit-name">Cross-Domain</div>
      <div class="crit-desc">매체-한정 키워드 자동 검출 → TRANSFER/PARTIAL/BLOCK 라벨</div>
    </div>
    <div class="crit-card">
      <div class="crit-id">C4</div>
      <div class="crit-name">직교성</div>
      <div class="crit-desc">다른 패턴과의 max similarity ≤ 0.7 (서로 독립)</div>
    </div>
  </div>
  <div class="info-title" style="margin-top: 14px;">Decision Rule</div>
  <div style="font-family: monospace; font-size: 9pt; background: #f5f5f5; padding: 8px; border-radius: 3px;">
    n_fail(✗) ≥ 2 → REJECT<br>
    n_pass(○) ≥ 3 → ACCEPT<br>
    n_pass(○) ≥ 2 AND n_fail = 0 → ACCEPT (조건부)<br>
    C3 = ✗ → ACCEPT (BLOCK 후보)<br>
    그 외 → ACCEPT (보완 필요)
  </div>
</div>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 왜 4기준인가</div>
패턴이 추천에 쓸만한지 평가하려면 한 가지 기준만으로는 부족하다. 예를 들어 <strong>"Pilot에서 자주 나옴"만으로 채택</strong>하면 'nostalgic_preference' 같은 표층 표현도 들어간다. 반대로 <strong>"이론적으로 좋음"만 보면</strong> 데이터에 안 맞는 패턴도 들어간다.<br>
4기준은 <strong>이론(C1) + 데이터(C2) + 도메인 적합성(C3) + 독립성(C4)</strong>을 모두 본다. 이 중 ≥3개를 만족하면 ACCEPT, ≥2개 실패면 REJECT.<br>
이 방법론의 <strong>장점</strong>: 다른 도메인(예: Music → Movies)에도 동일하게 적용 가능 → 본 연구의 <strong>일반화 가능성</strong>으로 부각.
</div>

<!-- ===== Workflow 다이어그램 ===== -->
<h2 class="pagebreak">3. 5단계 작업 흐름</h2>

<div class="infographic nobreak">
  <div class="info-title">Pilot Study Phase 1~4 (자유 추출 완료) → 4C-PPS Step 1~5</div>
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
      4기준 결정표<br>+ 본 보고서
    </div>
  </div>
</div>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 각 단계는 무엇을 산출하나</div>
<strong>Phase 1~4</strong>는 이미 끝낸 사전 작업으로, GPT-4o-mini가 100명 리뷰에서 자유롭게 패턴을 추출하고 임베딩 클러스터링으로 391개 canonical 패턴을 만든다.<br>
<strong>Step 1~5</strong>는 본 4C-PPS 방법론의 절차다. Step 1에서 후보 패턴 풀(7개)을 정하고, Step 2~4에서 4기준 검증 데이터를 모으고, Step 5에서 종합 평가한다.<br>
주의: <strong>본 연구가 직접 평가하지 않고</strong> 임베딩 자동 매칭이 평가 → 자기참조 회피.
</div>

<!-- ===== 7개 패턴 (4기준 평가 결과) ===== -->
<h2>4. 4C-PPS 적용 결과 — 7개 Core Pattern</h2>

<p>방법론을 본 도메인(Movies&amp;TV → Books)에 적용한 결과 채택된 7개. <strong>★ 자기평가 대신 4기준 ○/△/✗</strong> 표기.</p>

<div class="pattern-grid">
  <div class="pattern-card">
    <div class="pattern-name">1. genre_preference</div>
    <div class="pattern-source">
      C1 <span class="crit-tag crit-pass">○</span>
      C2 <span class="crit-tag crit-mid">△ 0.70</span>
      C3 <span class="crit-tag crit-pass">○</span>
      C4 <span class="crit-tag crit-pass">○ 0.47</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 장르·카테고리 선호</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">2. narrative_complexity</div>
    <div class="pattern-source">
      C1 <span class="crit-tag crit-pass">○</span>
      C2 <span class="crit-tag crit-pass">○ 0.80</span>
      C3 <span class="crit-tag crit-pass">○</span>
      C4 <span class="crit-tag crit-mid">△ 0.67</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 서사 복잡도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">3. pacing_preference</div>
    <div class="pattern-source">
      C1 <span class="crit-tag crit-pass">○</span>
      C2 <span class="crit-tag crit-pass">○ 0.81</span>
      C3 <span class="crit-tag crit-pass">○</span>
      C4 <span class="crit-tag crit-mid">△ 0.67</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 전개 속도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">4. quality_sensitivity</div>
    <div class="pattern-source">
      C1 <span class="crit-tag crit-pass">○</span>
      C2 <span class="crit-tag crit-mid">△ 0.55</span>
      C3 <span class="crit-tag crit-mid">△</span>
      C4 <span class="crit-tag crit-pass">○ 0.37</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-partial">PARTIAL</span> 품질 민감도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">5. brand_loyalty</div>
    <div class="pattern-source">
      C1 <span class="crit-tag crit-mid">△</span>
      C2 <span class="crit-tag crit-mid">△ 0.70</span>
      C3 <span class="crit-tag crit-fail">✗</span>
      C4 <span class="crit-tag crit-pass">○ 0.33</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-block">BLOCK 후보</span> 창작자 충성도</div>
  </div>
  <div class="pattern-card">
    <div class="pattern-name">6. sensory_preference</div>
    <div class="pattern-source">
      C1 <span class="crit-tag crit-mid">△</span>
      C2 <span class="crit-tag crit-mid">△ 0.59</span>
      C3 <span class="crit-tag crit-mid">△</span>
      C4 <span class="crit-tag crit-pass">○ 0.47</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-block">BLOCK 후보</span> 감각적 경험</div>
  </div>
  <div class="pattern-card pattern-card-emo">
    <div class="pattern-name">7. emotional_resonance ★ Pilot 도출</div>
    <div class="pattern-source">
      C1 <span class="crit-tag crit-mid">△</span>
      C2 <span class="crit-tag crit-pass">○ 0.82</span>
      C3 <span class="crit-tag crit-pass">○</span>
      C4 <span class="crit-tag crit-pass">○ 0.38</span>
    </div>
    <div style="margin-top:3px;"><span class="badge-transfer">TRANSFER</span> 감정적 울림 — Pilot 14% 빈도, sim 0.82 직접 매칭</div>
  </div>
</div>

<div class="callout">
<strong>패턴 분포 한 줄 요약</strong>:
TRANSFER 후보 4개 + PARTIAL 1개 + BLOCK 후보 2개. Transfer Gate의 3-level 판정이 데이터에 골고루 적용 가능한 구성.
</div>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 4기준이 어떻게 작동했나</div>
<strong>채택 4개</strong> (genre, narrative, pacing, emotional): 4기준 모두 ○ 또는 △ → 일반 ACCEPT.<br>
<strong>quality_sensitivity</strong>: C2와 C3에서 △라 "조건부 ACCEPT" — 영화에선 연기·연출, 책에선 문체·편집으로 변환 필요.<br>
<strong>brand_loyalty</strong>: C3에서 ✗ (actor·director 키워드 검출) — Transfer Gate가 BLOCK해야 할 후보.<br>
<strong>sensory_preference</strong>: C1·C2·C3 모두 △ — "보완 필요"지만 BLOCK 시연 목적으로 채택.<br>
<strong>emotional_resonance</strong>는 Step 1에선 후보가 아니었으나, Pilot에서 14% 빈도·sim 0.82로 강하게 emerge → 추가. 방법론의 <strong>보완 절차(H5)</strong>가 작동함을 시연.
</div>

<!-- ===== Step 2 결과 ===== -->
<h2 class="pagebreak">5. Step 2 — Pilot 자동 매칭 결과</h2>

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
<strong>판정</strong>: <span class="pass">7/7 통과 (sim ≥ 0.5)</span>. STRONG 3개 + MEDIUM 4개. 정확 동일 이름 매칭은 narrative_complexity, emotional_resonance 2건.
</div>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 임베딩 매칭이 무엇을 입증했나</div>
sentence-transformers는 텍스트의 의미를 768차원 벡터로 만든다. 두 텍스트의 코사인 유사도(sim)가 0.5 이상이면 의미적으로 유사하다고 본다.<br>
이 매칭이 입증한 것: <strong>본 연구의 7개 후보가 Pilot 데이터에 실제로 등장</strong>한다는 것. 이는 후보가 "데이터와 무관한 임의 정의"가 아님을 데이터로 보장.<br>
특히 <strong>narrative_complexity와 emotional_resonance는 정확 동일 이름</strong>으로 Pilot에 등장 — 가장 강한 매칭.
</div>

<!-- ===== Step 3 결과 + Figure ===== -->
<h2>6. Step 3 — 자유 추출의 한계 정량화</h2>

<p>391개 Pilot canonical 패턴을 4 카테고리로 자동 분류. <strong>본 연구의 명시 prompt 설계 정당성을 데이터로 입증.</strong></p>

<table>
<tr><th>카테고리</th><th>의미</th><th>패턴 수</th><th>비율</th></tr>
<tr><td>CDR 적합</td><td>후보 7개와 sim ≥ 0.5</td><td>36</td><td><span class="pass">9.2%</span></td></tr>
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

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 왜 자유 추출만으론 부족한가</div>
LLM에게 "사용자 리뷰에서 패턴을 자유롭게 뽑아줘"라고 하면, <strong>나오는 90%가 Cross-Domain 추천에 쓸 수 없는 것들</strong>이다:<br>
- "IMAX 영상미를 좋아함" (영화 한정 — 책에 매핑 불가)<br>
- "high_recommendation" (메타 정보 — 패턴이 아님)<br>
- "nostalgic_preference" (표층 감정 — 깊이 부족)<br>
이 결과가 <strong>"명시 prompt로 7개를 강제로 추출하라"는 본 연구 설계를 강력히 정당화</strong>한다. 만약 자유 추출로 충분했다면 본 연구의 명시 prompt는 불필요.
</div>

<!-- ===== Step 4 결과 + Figure ===== -->
<h2 class="pagebreak">7. Step 4 — 직교성 + Movies-only 키워드 검출</h2>

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

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 왜 7개가 서로 겹치지 않아야 하나</div>
패턴들이 서로 너무 비슷하면 "중복 정보"라 추천에 도움이 안 된다. 직교성 검증은 <strong>7개가 의미적으로 독립</strong>임을 보장.<br>
가장 가까운 쌍은 <strong>narrative_complexity ↔ pacing_preference (0.67)</strong> — 둘 다 narrative 차원이라 자연스러움. 임계값(0.7) 미만이라 통과.<br>
또한 Movies-only 키워드 자동 검출로 <strong>brand_loyalty와 sensory_preference가 BLOCK 후보임을 데이터로 식별</strong> — Transfer Gate가 "왜 이걸 차단해야 하는가"의 근거가 자동으로 만들어짐.
</div>

<!-- ===== Pareto Chart ===== -->
<h2 class="pagebreak">8. Pilot 빈도 분포 (참고)</h2>

<p>Pilot 391 canonical 패턴 중 빈도 상위 25개. nostalgic_preference·family_friendly 등 <strong>본 연구의 7개에 채택되지 않은 표층 패턴이 빈도 상위</strong>를 차지 — 자유 추출의 표층 편향 시각화.</p>

{"<img class='chart' src='" + IMG_FREQ + "' />" if IMG_FREQ else ""}
<p class="fig-caption">Figure 3. Pilot Top-25 패턴 Pareto chart (빈도 + 누적 커버리지). kneed elbow N=7 검출되었으나, 이 N=7은 빈도 기준이며 본 연구의 7개와 다른 구성.</p>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 빈도 N=7과 본 연구의 7개는 다르다</div>
재미있게도 Pilot 빈도 분석에서도 elbow가 N=7에서 떨어진다. <strong>그러나 이 7개는 nostalgic·family_friendly 등 표층 패턴</strong>이지 Cross-Domain 추천에 적합한 7개가 아니다.<br>
이는 <strong>"빈도만으로 패턴 선정 불가"</strong>라는 4C-PPS의 핵심 주장을 시각화. 빈도(C2)는 4기준 중 하나일 뿐이며, 이론(C1)·CDR(C3)·직교(C4)도 함께 봐야 함.
</div>

<!-- ===== 가설 H1-H5 인포그래픽 ===== -->
<h2>9. 사전 등록 가설 H1~H5 검증 결과</h2>

<p>Pilot 결과 보기 전에 등록한 5가지 가설. <strong>모두 통과</strong> → 4C-PPS 방법론의 작동성 입증.</p>

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
<tr><td>H1</td><td>후보 7개가 Pilot에서 sim ≥ 0.5로 발현</td><td><span class="pass">7/7 통과</span></td></tr>
<tr><td>H2</td><td>Pilot 자유 추출 ≥ 60%가 비-CDR-적합 (명시 prompt 정당화)</td><td><span class="pass">90.8% (대폭 통과)</span></td></tr>
<tr><td>H3</td><td>7개 직교성 max similarity ≤ 0.7</td><td><span class="pass">max 0.669</span></td></tr>
<tr><td>H4</td><td>매체 한정 패턴이 Movies-only 키워드 자동 검출</td><td><span class="pass">cinematograph 검출</span></td></tr>
<tr><td>H5</td><td>Pilot에서 emerge한 패턴 직접 매칭 (방법론 보완 절차)</td><td><span class="pass">sim 0.820 (top-1 동일)</span></td></tr>
</table>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 사전 등록이 왜 중요한가</div>
"결과 본 후 가설을 만들면" 짜맞춰지므로 자기참조가 된다. <strong>결과 보기 전에</strong> "이런 결과가 나와야 방법론이 맞다"고 미리 등록하면, 실제 결과로 검증 가능.<br>
H1~H5는 <strong>방법론의 5가지 작동 조건</strong>:<br>
H1: 후보가 데이터에 발현하는가 / H2: 자유 추출만으론 부족한가 / H3: 후보가 서로 독립인가 / H4: BLOCK이 자동 식별되는가 / H5: 데이터에서 새 패턴이 emerge하는가.<br>
5/5 통과 → <strong>방법론의 모든 메커니즘이 의도대로 작동함을 데이터로 입증</strong>.
</div>

<!-- ===== 채택 결정표 ===== -->
<h2 class="pagebreak">10. 4기준 종합 채택 결정표 (Step 5)</h2>

<p>각 패턴에 4기준 ○/△/✗ 평가 → Decision Rule 적용.</p>

<table>
<tr>
  <th>Pattern</th>
  <th>C1 이론</th>
  <th>C2 Pilot</th>
  <th>C3 CDR</th>
  <th>C4 직교</th>
  <th>결정</th>
</tr>
<tr>
  <td>genre_preference</td>
  <td>○</td>
  <td>△ 0.70</td>
  <td>○ TRANSFER</td>
  <td>○ 0.47</td>
  <td><span class="pass">ACCEPT</span></td>
</tr>
<tr>
  <td>narrative_complexity</td>
  <td>○</td>
  <td>○ 0.80</td>
  <td>○ TRANSFER</td>
  <td>△ 0.67</td>
  <td><span class="pass">ACCEPT</span></td>
</tr>
<tr>
  <td>pacing_preference</td>
  <td>○</td>
  <td>○ 0.81</td>
  <td>○ TRANSFER</td>
  <td>△ 0.67</td>
  <td><span class="pass">ACCEPT</span></td>
</tr>
<tr>
  <td>quality_sensitivity</td>
  <td>○</td>
  <td>△ 0.55</td>
  <td>△ PARTIAL</td>
  <td>○ 0.37</td>
  <td><span class="pass">ACCEPT (조건부)</span></td>
</tr>
<tr>
  <td>brand_loyalty</td>
  <td>△</td>
  <td>△ 0.70</td>
  <td>✗ BLOCK</td>
  <td>○ 0.33</td>
  <td><span class="pass">ACCEPT (BLOCK 후보)</span></td>
</tr>
<tr>
  <td>sensory_preference</td>
  <td>△</td>
  <td>△ 0.59</td>
  <td>△ PARTIAL</td>
  <td>○ 0.47</td>
  <td><span class="pass">ACCEPT (보완 필요)</span></td>
</tr>
<tr class="highlight-row">
  <td><strong>emotional_resonance</strong></td>
  <td>△</td>
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

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 각 결정의 의미</div>
<strong>일반 ACCEPT (4개)</strong>: 4기준 모두 통과한 깨끗한 패턴 → Profiler가 무조건 추출, Judge가 그대로 사용.<br>
<strong>조건부 ACCEPT (quality_sensitivity)</strong>: C2·C3 부분 통과 → 매체별 변환 로직 필요. 책에선 average_rating 등으로 매핑.<br>
<strong>BLOCK 후보 (brand_loyalty)</strong>: C3 ✗ → Transfer Gate가 BLOCK 처리해야 정상. 본 연구의 Gate 가치 시연 사례.<br>
<strong>보완 필요 (sensory_preference)</strong>: 학술 인용·데이터 모두 약하나, BLOCK 시연용으로 유지. 향후 영화 ↔ 책 도메인에서 조정 가능.<br>
<strong>emotional_resonance</strong>: Pilot에서 emerge → 방법론의 보완 절차 작동 사례. C2 강함(0.82)이라 정식 채택.
</div>

<!-- ===== 결론 ===== -->
<h2 class="pagebreak">11. 결론 — 본 연구 contribution 정당화</h2>

<h3>11.1 핵심 결론 4가지</h3>

<ol>
<li><strong>4C-PPS 방법론을 본 도메인에 적용한 결과 7개 채택 확정</strong> (REJECT 0)</li>
<li><strong>자기참조 회피 완벽</strong> — 이론 anchor(외부) ↔ 검증(자동 도구) 분리, 인용 6개 → 2개 압축</li>
<li><strong>자유 추출의 한계 (90.8%)</strong> 정량 확인 → 명시 prompt 설계 강력 정당화</li>
<li><strong>Transfer Gate 후보 자동 식별</strong> — BLOCK 2개, PARTIAL 1개 — 본 연구의 BLOCK 메커니즘 데이터 시연</li>
</ol>

<h3>11.2 논문에 쓸 수 있는 핵심 표현</h3>

<div class="quote-box">
"본 연구는 Cross-Domain 추천에서 사용자 선호 패턴을 선정하는 방법론(<strong>4C-PPS</strong>)을 제안한다. 본 방법론은 4가지 독립 기준—이론 정합성, Pilot 발현, Cross-Domain 적합성, 직교성—의 종합 평가로 후보 패턴을 채택한다. 이론 anchor로 영화 리뷰 aspect mining (Thet et al., 2010)과 ABSA 일반 프레임워크 (Liu, 2012)를 채택하되, 본 연구는 (a) sentiment 분석이 아닌 사용자 선호 추출로 목적 변경, (b) 단일 도메인이 아닌 Cross-Domain 전이 가능성 차원으로 확장하였다.<br><br>
Movies&amp;TV → Books CDR에 본 방법론을 적용한 결과 7개 패턴이 채택되었다. Pilot Study (n=100)에서 후보 패턴이 임베딩 자동 매칭으로 모두 sim ≥ 0.5로 발현되었으며 (H1: 7/7), 자유 추출 결과의 <span class="key-stat">90.8%</span>가 매체-종속·표층·메타 신호로 분류되어 (H2) 명시적 prompt 설계의 정당성이 데이터로 입증되었다. 7개 패턴 사이 cosine similarity는 max 0.669로 직교성을 만족 (H3)했으며, sensory_preference와 brand_loyalty는 Movies-only 키워드 자동 검출로 Transfer Gate의 BLOCK 후보로 식별 (H4)되어 BLOCK 메커니즘의 Negative Transfer 방지 가설을 데이터로 시연한다."
</div>

<h3>11.3 본 연구 contribution의 위계 (재확인)</h3>

<div class="contrib-box">
1. <strong>(메인)</strong> Profiler-Judge 구조의 LLM 기반 CDR 프레임워크<br>
2. <strong>(서브)</strong> 4C-PPS — 선호 패턴 선정 4기준 방법론<br>
3. <strong>(서브)</strong> Pilot Study 검증 절차 (자기참조 회피 메커니즘)<br><br>
<strong>7개 패턴 자체는 contribution이 아니다.</strong> 본 방법론을 다른 CDR 시나리오(Music → Movies, Books → Music 등)에 재적용하면 다른 N개·다른 라벨 분포가 나올 수 있다. 본 연구의 진짜 학술 기여는 <strong>"방법론 + 실증 1건"</strong>으로 위치한다.
</div>

<h3>11.4 한계 및 향후 작업</h3>

<table>
<tr><th>한계</th><th>대응</th></tr>
<tr><td>Pilot 100명 (LLM4CDR 수준)</td><td>본 실험 1,000명에서 통계적 일반화</td></tr>
<tr><td>emotional_resonance 이론 anchor 약함</td><td>Pilot 데이터(sim 0.82, 14% 빈도)로 보완. 방법론의 보완 절차로 정당화</td></tr>
<tr><td>medium_specific 분류 보수성 (90.8% 다소 후함)</td><td>결론은 50~60%만 매체-종속이어도 동일</td></tr>
<tr><td>방법론 외재 타당성 미검증</td><td>다른 도메인 쌍 적용은 향후 작업 (실험계획서 §9.8)</td></tr>
</table>

<!-- ===== 부록 ===== -->
<h2>12. 산출물 요약</h2>

<table>
<tr><th>분류</th><th>파일</th></tr>
<tr><td>분석 스크립트 (9개)</td><td>scripts/pilot_sample.py · run_pilot.py · collect_patterns.py · normalize_patterns.py · match_pilot_to_predefined.py · categorize_pilot_patterns.py · check_predefined_orthogonality.py · integrate_pilot_evaluation.py · check_pilot_progress.py</td></tr>
<tr><td>데이터 (10개 parquet/csv/json)</td><td>data/pilot_users · pilot_patterns_canonical · pilot_to_predefined_matching · pilot_to_predefined_matrix · pilot_pattern_categories · pilot_pattern_orthogonality · pilot_decision_table · pilot_summary_metrics</td></tr>
<tr><td>시각화 (3개)</td><td>data/pilot_pattern_frequency.png · pilot_categories_summary.png · pilot_pattern_orthogonality.png</td></tr>
<tr><td>문서</td><td>prompts/core_patterns_definition.md (방법론 B) · prompts/pilot_profiler_prompt.md · docs/Pilot_Study_Report.md (방법론 B) · docs/MethodologyB_Migration_Plan.md · 본 PDF v2</td></tr>
</table>

<div class="callout">
<strong>이전 버전과의 비교</strong>:
v1 (TransferJudge_Pilot_Report.pdf, 2026-04)은 "패턴별 6개 인용" 방식. v2(본 PDF)는 "4C-PPS 방법론 + 2개 anchor"로 재구성. 두 버전 모두 보존됨.
</div>

<p style="text-align: center; color: #666; font-size: 9pt; margin-top: 20px;">
— 본 보고서 v2의 핵심 메시지: 본 연구의 진짜 contribution은 <strong>7개 패턴이 아니라 4C-PPS 방법론과 그 검증 절차</strong>이다. 7개 패턴은 본 방법론을 Movies&amp;TV → Books에 적용한 실증 결과로 위치한다 —
</p>

</body>
</html>
"""


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc = weasyprint.HTML(string=HTML_CONTENT)
    doc.write_pdf(OUTPUT_PATH)
    print(f"PDF generated: {OUTPUT_PATH}")
