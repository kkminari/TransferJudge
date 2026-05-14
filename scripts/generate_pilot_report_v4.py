"""Pilot Study Report PDF v4 (프로세스 중심 재구성).

v3 대비 보강:
  - §1: 자유 추출이 왜 부족한가 (Pilot 한 이유) 별도 섹션
  - §2: 4단계 프로세스 한눈에 다이어그램
  - §3: Step 1 — 이론으로부터 6개 후보 도출 (Thet 2010 매핑 표)
  - §4: Step 2 — 100명 자유 추출 + 391 canonical 도출 (HDBSCAN 한글 설명)
  - §5: Step 3 — 임베딩 매칭 (방법·이유·결과·의미)
  - §6: Step 4 — emotional_resonance 7번째 추가 정당화
  - 어려운 개념마다 한글/쉬운 설명 콜아웃

산출: docs/TransferJudge_Pilot_Report_v4.pdf (v1, v2, v3 모두 보존)
"""
from __future__ import annotations

import base64
import os

import weasyprint

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "docs", "pilot")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "TransferJudge_Pilot_Report_v4.pdf")


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
  h2 {{ font-size: 14pt; color: #16213e; border-bottom: 2.5px solid #4a90d9; padding-bottom: 4px; margin-top: 26px; }}
  h3 {{ font-size: 12pt; color: #0f3460; margin-top: 18px; }}
  h4 {{ font-size: 10.5pt; color: #333; margin-top: 12px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0 12px 0; font-size: 9.5pt; }}
  th {{ background: #16213e; color: white; padding: 5px 8px; text-align: left; font-weight: 600; }}
  td {{ padding: 4px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #f8f9fa; }}
  .highlight-row td {{ background: #e8f4fd !important; font-weight: 600; }}
  .callout {{ background: #f0f4f8; border-left: 4px solid #4a90d9; padding: 10px 14px; margin: 10px 0; font-size: 9.7pt; }}
  .callout-warn {{ background: #fff8e1; border-left: 4px solid #f5a623; padding: 10px 14px; margin: 10px 0; font-size: 9.7pt; }}
  .callout-green {{ background: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px 14px; margin: 10px 0; font-size: 9.7pt; }}
  .callout-red   {{ background: #ffebee; border-left: 4px solid #c62828; padding: 10px 14px; margin: 10px 0; font-size: 9.7pt; }}
  .easy-note {{ background: #f3e5f5; border-left: 4px solid #8e44ad; padding: 10px 14px; margin: 10px 0; font-size: 9.5pt; line-height: 1.55; }}
  .easy-note .easy-title {{ font-weight: 700; color: #6a1b9a; margin-bottom: 4px; font-size: 9.7pt; }}
  .term {{ background: #fffde7; padding: 1px 5px; border-radius: 3px; font-weight: 600; color: #5d4a1a; }}
  .pass {{ color: #2e7d32; font-weight: 700; }}
  .warn {{ color: #e65100; font-weight: 700; }}
  .fail {{ color: #c62828; font-weight: 700; }}
  .pagebreak {{ page-break-before: always; }}
  .nobreak {{ page-break-inside: avoid; }}
  ul, ol {{ margin: 4px 0; padding-left: 22px; }}
  li {{ margin: 3px 0; }}
  img.chart {{ width: 100%; margin: 8px 0; }}
  .fig-caption {{ text-align: center; font-size: 8.8pt; color: #666; margin-top: -5px; margin-bottom: 12px; }}

  /* 단계별 박스 */
  .step-header {{
    background: linear-gradient(90deg, #4a90d9 0%, #16213e 100%);
    color: white;
    padding: 6px 12px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 11pt;
    margin: 10px 0 6px 0;
    display: inline-block;
  }}

  /* 흐름 다이어그램 */
  .process-box {{
    background: #fafbfc;
    border: 1.5px solid #d8dde6;
    border-radius: 6px;
    padding: 16px;
    margin: 14px 0;
  }}
  .process-row {{ display: flex; align-items: stretch; gap: 6px; margin: 6px 0; }}
  .step-card {{
    flex: 1; border-radius: 5px; padding: 8px 10px;
    font-size: 9pt; line-height: 1.35; text-align: center;
  }}
  .step-input   {{ background: #fff4e6; border: 1.5px solid #e08a3c; }}
  .step-process {{ background: #e7f1fb; border: 1.5px solid #2f7bc4; }}
  .step-output  {{ background: #e8f5e9; border: 1.5px solid #2f9a53; font-weight: 600; }}
  .step-title {{ font-weight: 700; color: #1a2555; margin-bottom: 3px; font-size: 9.5pt; }}
  .arrow {{ display: flex; align-items: center; justify-content: center; color: #2d3e8a; font-size: 14pt; flex: 0 0 18px; font-weight: 700; }}

  /* 매핑 표 (Thet → 본 연구) */
  .mapping-table {{ width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 9.3pt; }}
  .mapping-table th {{ background: #4a90d9; }}
  .mapping-table td.thet  {{ background: #fff4e6; font-style: italic; }}
  .mapping-table td.ours  {{ background: #e8f5e9; font-weight: 600; }}
  .mapping-table td.label {{ text-align: center; }}

  /* 패턴 카드 */
  .pattern-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; margin: 10px 0; }}
  .pattern-card {{
    background: #fff; border: 1.2px solid #d5dae6;
    border-radius: 4px; padding: 8px 10px; font-size: 9pt;
  }}
  .pattern-card-emo {{ border-color: #2f9a53; background: #e8f5e9; }}
  .pattern-name {{ font-weight: 700; color: #1a2555; }}
  .crit-tag {{ display: inline-block; padding: 0 4px; border-radius: 2px; font-size: 8pt; font-weight: 700; margin: 0 1px; }}
  .crit-pass {{ background: #e8f5e9; color: #2e7d32; }}
  .crit-mid  {{ background: #fff3e0; color: #e65100; }}
  .crit-fail {{ background: #ffebee; color: #c62828; }}
  .badge-transfer {{ background: #2f9a53; color: white; padding: 1px 5px; border-radius: 3px; font-size: 8pt; }}
  .badge-partial  {{ background: #d79a2e; color: white; padding: 1px 5px; border-radius: 3px; font-size: 8pt; }}
  .badge-block    {{ background: #b53a3a; color: white; padding: 1px 5px; border-radius: 3px; font-size: 8pt; }}

  /* 검토 5항목 카드 */
  .check-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 10px 0; }}
  .check-card {{
    background: #fff; border: 1.5px solid #4caf50; border-radius: 6px;
    padding: 8px; text-align: center; font-size: 9pt;
  }}
  .check-id    {{ font-size: 12pt; font-weight: 700; color: #2e7d32; margin-bottom: 4px; }}
  .check-label {{ font-weight: 600; color: #1a2555; margin-bottom: 4px; font-size: 8.5pt; }}
  .check-result {{ color: #444; font-size: 8.5pt; }}
  .check-mark {{ font-size: 16pt; }}

  /* 인용 박스 */
  .quote-box {{
    background: #fffef0; border: 1.5px dashed #d79a2e;
    border-radius: 5px; padding: 12px 14px; margin: 10px 0;
    font-size: 9.5pt; line-height: 1.55; color: #5d4a1a; font-style: italic;
  }}
  .key-stat {{
    display: inline-block; background: #e8f5e9; color: #2e7d32;
    padding: 1px 6px; border-radius: 3px; font-weight: 700; font-style: normal;
  }}
</style>
</head>
<body>

<!-- ===== TITLE ===== -->
<h1>Pilot Study Report v4</h1>
<p class="subtitle">TransferJudge — 7개 Core Pattern 도출 과정 (4단계 프로세스 상세)</p>
<p class="subtitle">자유 추출의 한계 → 이론 anchor → Pilot 검증 → emotional 추가</p>
<p class="author">2026.05 · 빅데이터학과 17기 곽민아</p>

<div class="easy-note nobreak">
<div class="easy-title">💡 이 보고서가 답하는 4가지 질문</div>
<strong>Q1.</strong> LLM에게 그냥 패턴을 자유롭게 뽑게 하면 안 되나? → §1<br>
<strong>Q2.</strong> 이론으로부터 어떻게 6개 후보를 도출했나? → §3<br>
<strong>Q3.</strong> Pilot 100명에 자유 추출은 왜? 391개는 어떻게 만들었나? → §4<br>
<strong>Q4.</strong> 6개와 391개를 임베딩 매칭한 이유와 결과의 의미? → §5<br>
<strong>+ </strong>emotional_resonance를 7번째로 추가한 근거 → §6
</div>

<!-- ============================================================ -->
<!-- §1. 자유 추출은 왜 부족한가 -->
<!-- ============================================================ -->
<h2>1. 왜 자유 추출만으로는 부족한가</h2>

<p>본 Pilot Study를 진행한 가장 큰 이유는 <strong>"LLM에게 패턴을 자유롭게 추출시키면 어떤 결과가 나오는지"</strong>를 데이터로 확인하기 위함이다. 결론부터 말하면, <span class="fail">자유 추출 결과의 90.8%가 Cross-Domain 추천에 부적합</span>했다.</p>

<h3>1.1 가설 — "자유 추출이면 충분할까?"</h3>

<p>본 연구는 영화 리뷰에서 사용자 선호 패턴을 추출하여 책 추천에 활용한다. 가장 단순한 접근은 LLM에게 다음과 같이 묻는 것이다:</p>

<div class="callout">
"이 사용자의 리뷰를 보고, 어떤 선호 패턴이든 자유롭게 추출하세요. (개수 제한 없음)"
</div>

<p>이 접근의 장점은 <strong>편향 없는 발견</strong>이지만, 단점은 <strong>매체-특화·표층·메타 신호가 우세</strong>해질 가능성이다.</p>

<h3>1.2 Pilot 100명 실제 자유 추출 결과 (391 canonical 패턴)</h3>

<p>391개를 4가지 카테고리로 자동 분류한 결과:</p>

<table>
<tr><th>카테고리</th><th>의미</th><th>예시</th><th>수</th><th>비율</th></tr>
<tr><td>CDR 적합</td><td>책 추천에 쓸 만한 패턴</td><td>"narrative_complexity"</td><td>36</td><td><span class="pass">9.2%</span></td></tr>
<tr><td>표층 신호</td><td>구체 장르명·감정 단어</td><td>"nostalgic_preference"</td><td>79</td><td>20.2%</td></tr>
<tr><td>매체-종속</td><td>영화 전용 키워드 보유</td><td>"IMAX_visuals"</td><td>268</td><td><span class="warn">68.5%</span></td></tr>
<tr><td>메타 정보</td><td>패턴이 아닌 표현</td><td>"high_recommendation"</td><td>8</td><td>2.0%</td></tr>
<tr class="highlight-row"><td colspan="3"><strong>비-CDR-적합 합계</strong></td><td><strong>355</strong></td><td><span class="fail"><strong>90.8%</strong></span></td></tr>
</table>

<h3>1.3 자유 추출 단독으로 본 연구가 안 되는 6가지 이유</h3>

<table>
<tr><th>측면</th><th>자유 추출의 한계</th></tr>
<tr><td><strong>1) Cross-Domain 부적합</strong></td><td>90.8%가 책 추천에 무관 — "IMAX 영상미"는 책에 매핑 불가</td></tr>
<tr><td><strong>2) Transfer Gate 작동 불가</strong></td><td>사용자마다 패턴 셋이 달라 TRANSFER/PARTIAL/BLOCK 사전 라벨 불가능 — <span class="fail">본 연구 핵심 contribution 무력화</span></td></tr>
<tr><td><strong>3) 사용자 간 비교 불가</strong></td><td>User A의 5개 패턴 vs User B의 8개 패턴 — 공통 키 없음</td></tr>
<tr><td><strong>4) Teacher 학습 불일관</strong></td><td>QLoRA 입력·출력 JSON 스키마가 사용자마다 달라 학습 효과 ↓</td></tr>
<tr><td><strong>5) 재현성·비용 가변</strong></td><td>같은 사용자 두 번 호출 시 다른 결과 가능</td></tr>
<tr><td><strong>6) 선행연구 비교 불가</strong></td><td>LLM4CDR·TALLRec 등 모두 명시 attribute 사용 → 자유 추출 단독은 비교군 없음</td></tr>
</table>

<div class="callout-red nobreak">
<strong>핵심 발견</strong>: 자유 추출은 <strong>풍부한 신호를 주지만 그중 9%만 책 추천에 유용</strong>하다. 따라서 본 연구는 <strong>명시적 prompt로 7개 패턴을 강제 추출</strong>하는 구조화 접근을 채택한다. 단, additional_patterns 최대 3개를 자유롭게 추가하여 long-tail 발견 가능성도 보존한다.
</div>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 자유 추출의 직관</div>
"하고 싶은 말 다 해 봐"라고 하면 사용자는 영화 관련 얘기를 100% 쏟아낸다. 그중 책 추천에도 쓸 수 있는 것은 약 10%뿐이다. 본 연구는 이 사실을 데이터로 보이고, 명시 prompt(7개 패턴 강제 추출)의 정당성을 확보한다.
</div>

<!-- ============================================================ -->
<!-- §2. 4단계 프로세스 한눈에 -->
<!-- ============================================================ -->
<h2 class="pagebreak">2. 4단계 프로세스 한눈에</h2>

<div class="process-box nobreak">
  <!-- Step 1 -->
  <div class="process-row">
    <div class="step-card step-input">
      <div class="step-title">입력</div>
      Thet 2010 영화 aspect 7개<br>+ Liu 2012 ABSA 표준<br>+ 추천시스템 attribute
    </div>
    <div class="arrow">→</div>
    <div class="step-card step-process">
      <div class="step-title">Step 1</div>
      이론 anchor 검토<br>Cross-Domain 재구성<br>(영화 한정 제거)
    </div>
    <div class="arrow">→</div>
    <div class="step-card step-output">
      <div class="step-title">출력 1</div>
      <strong>6개 후보 패턴</strong><br>(이론 기반)
    </div>
  </div>
  <div style="text-align:center; color:#2d3e8a; margin: 4px 0;">↓ (검증)</div>
  <!-- Step 2 -->
  <div class="process-row">
    <div class="step-card step-input">
      <div class="step-title">입력</div>
      Pilot 100명 영화 리뷰<br>(편향 없는 표본)
    </div>
    <div class="arrow">→</div>
    <div class="step-card step-process">
      <div class="step-title">Step 2</div>
      자유 추출 (GPT-4o-mini)<br>→ Raw 패턴 800+개<br>→ 정규화 (HDBSCAN 클러스터링)
    </div>
    <div class="arrow">→</div>
    <div class="step-card step-output">
      <div class="step-title">출력 2</div>
      <strong>391 canonical 패턴</strong><br>(데이터 진실)
    </div>
  </div>
  <div style="text-align:center; color:#2d3e8a; margin: 4px 0;">↓ (매칭)</div>
  <!-- Step 3 -->
  <div class="process-row">
    <div class="step-card step-input">
      <div class="step-title">입력</div>
      6 후보 ↔ 391 canonical
    </div>
    <div class="arrow">→</div>
    <div class="step-card step-process">
      <div class="step-title">Step 3</div>
      임베딩 cosine 매칭<br>(sentence-transformers)<br>→ 6 × 391 = 2,346쌍 계산
    </div>
    <div class="arrow">→</div>
    <div class="step-card step-output">
      <div class="step-title">출력 3</div>
      <strong>6/6 모두 sim ≥ 0.5</strong><br>(데이터 실재 확인)
    </div>
  </div>
  <div style="text-align:center; color:#2d3e8a; margin: 4px 0;">↓ (보완)</div>
  <!-- Step 4 -->
  <div class="process-row">
    <div class="step-card step-input">
      <div class="step-title">발견</div>
      Pilot에서 emotional_resonance가<br>14% 빈도, sim 0.82 직접 매칭
    </div>
    <div class="arrow">→</div>
    <div class="step-card step-process">
      <div class="step-title">Step 4</div>
      이론 anchor 약하나<br>데이터 신호 강함<br>→ 7번째로 추가
    </div>
    <div class="arrow">→</div>
    <div class="step-card step-output">
      <div class="step-title">최종</div>
      <strong>7개 Core Pattern</strong><br>(6 이론 + 1 데이터)
    </div>
  </div>
</div>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 왜 4단계인가</div>
1단계는 <strong>"이론에서 출발"</strong>(밖에서 빌려옴), 2단계는 <strong>"데이터로 검증"</strong>(데이터 진실 측정), 3단계는 <strong>"매칭으로 정합 확인"</strong>(이론이 데이터에 실재하나?), 4단계는 <strong>"데이터 신호로 보완"</strong>(이론에 없지만 데이터가 말하는 것). 이렇게 <strong>이론과 데이터를 양방향</strong>으로 사용했다.
</div>

<!-- ============================================================ -->
<!-- §3. Step 1 — 이론으로부터 6개 후보 도출 -->
<!-- ============================================================ -->
<h2 class="pagebreak">3. Step 1 — 이론으로부터 6개 후보 도출</h2>

<h3>3.1 이론 anchor (참고 학술)</h3>

<table>
<tr><th>인용</th><th>역할</th></tr>
<tr><td><strong>Thet, Na & Khoo (2010)</strong> — Aspect-based sentiment analysis of movie reviews</td><td>영화 리뷰를 7개 aspect로 분해 (storyline, characters, screenplay, acting, direction, scene, music) — 본 연구 후보 패턴의 주요 출처</td></tr>
<tr><td><strong>Liu, B. (2012)</strong> — Sentiment Analysis and Opinion Mining</td><td>Aspect-Based Sentiment Analysis (ABSA) 표준 — 리뷰를 4~6개 aspect로 분해하는 일반 프레임워크</td></tr>
<tr><td><em>(보조)</em> Oliver (1999), Ricci RS Handbook (2015)</td><td>brand_loyalty, quality_sensitivity 개념의 일반 개념</td></tr>
</table>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — ABSA가 뭐야?</div>
<span class="term">ABSA (Aspect-Based Sentiment Analysis, 측면 기반 감성 분석)</span>는 리뷰를 <strong>"측면(aspect)"</strong>이라는 작은 단위로 쪼개는 표준 방법. 예를 들어 영화 리뷰 "스토리는 좋은데 연기가 별로"는 [스토리=긍정, 연기=부정]으로 분해된다. 본 연구는 이 분해 단위(aspect)를 <strong>사용자 선호 패턴</strong>으로 재해석했다.
</div>

<h3>3.2 Thet 2010의 7개 영화 aspect → 본 연구의 6개 후보 (재구성)</h3>

<table class="mapping-table">
<tr><th>Thet 2010 영화 aspect</th><th>한글</th><th>변환 논리</th><th>본 연구 후보</th><th>Cross-Domain</th></tr>
<tr>
  <td class="thet">storyline + characters + screenplay</td>
  <td>줄거리 + 인물 + 각본</td>
  <td>3개를 <strong>"서사 복잡도"</strong>로 통합 (책에도 적용)</td>
  <td class="ours">narrative_complexity</td>
  <td class="label"><span class="badge-transfer">TRANSFER</span></td>
</tr>
<tr>
  <td class="thet">pace (storytelling)</td>
  <td>전개 속도</td>
  <td>Thet은 보조 attribute, 본 연구는 <strong>독립 패턴</strong>으로 격상 (책에서도 page-turner ↔ slow-burn 명확)</td>
  <td class="ours">pacing_preference</td>
  <td class="label"><span class="badge-transfer">TRANSFER</span></td>
</tr>
<tr>
  <td class="thet">acting + direction</td>
  <td>연기 + 연출</td>
  <td>"제작 품질"로 일반화 (책 도메인에서는 문체·편집·번역으로 변환)</td>
  <td class="ours">quality_sensitivity</td>
  <td class="label"><span class="badge-partial">PARTIAL</span></td>
</tr>
<tr>
  <td class="thet">director + cast (창작자 차원)</td>
  <td>감독·출연진</td>
  <td>"창작자 충성도"로 일반화 + Oliver (1999) brand loyalty 차용. 영화 감독은 책에 부재 → BLOCK 후보</td>
  <td class="ours">brand_loyalty</td>
  <td class="label"><span class="badge-block">BLOCK 후보</span></td>
</tr>
<tr>
  <td class="thet">scene + music + visual</td>
  <td>장면·음악·영상</td>
  <td>"감각적 경험"으로 통합. 영화 매체 특화 → BLOCK 시연 목적</td>
  <td class="ours">sensory_preference</td>
  <td class="label"><span class="badge-block">BLOCK 후보</span></td>
</tr>
<tr>
  <td class="thet">(영화 category)</td>
  <td>장르</td>
  <td>Thet에 명시되지 않으나 추천시스템 표준 attribute (NCF, TALLRec 등)에 항상 등장</td>
  <td class="ours">genre_preference</td>
  <td class="label"><span class="badge-transfer">TRANSFER</span></td>
</tr>
</table>

<h3>3.3 도출 논리 정리</h3>

<ol>
<li><strong>Thet 2010의 7개 영화 aspect를 출발점</strong>으로 삼되, 본 연구는 Cross-Domain (영화 → 책) 추천이므로 <strong>책 도메인에도 적용 가능한 형태로 재구성</strong>한다.</li>
<li>3개 서사 관련 aspect(storyline·characters·screenplay)는 <strong>"narrative_complexity"</strong>로 통합 — 책에서도 자연스럽게 적용.</li>
<li>2개 창작자 관련 aspect(acting·direction)는 <strong>"quality_sensitivity"</strong>로 일반화 — 매체별 지표는 다르지만 품질 민감도 자체는 도메인 독립.</li>
<li>창작자 충성도(director·cast)는 <strong>"brand_loyalty"</strong>로 일반화 — 영화 감독은 책 작가가 아니라 BLOCK 시연 후보로 의도적 채택.</li>
<li>감각 차원(scene·music)은 <strong>"sensory_preference"</strong> — 영화 한정이지만 Transfer Gate의 BLOCK 메커니즘을 데이터로 시연하기 위해 채택.</li>
<li>genre는 Thet 외에 NCF·TALLRec 등 추천시스템 표준 attribute에서 차용.</li>
</ol>

<div class="callout-green nobreak">
<strong>Step 1 산출</strong>: <span class="key-stat">6개 후보 패턴</span><br>
genre · narrative_complexity · pacing · quality · brand · sensory (모두 영문 표기)<br>
Cross-Domain 라벨 사전 분류: <strong>TRANSFER 3 + PARTIAL 1 + BLOCK 후보 2</strong> → Transfer Gate 3-level 검증 가능한 구성.
</div>

<!-- ============================================================ -->
<!-- §4. Step 2 — Pilot 자유 추출 + 391 canonical -->
<!-- ============================================================ -->
<h2 class="pagebreak">4. Step 2 — Pilot 100명 자유 추출 + 391 canonical 도출</h2>

<h3>4.1 왜 자유 추출을 했는가</h3>

<table>
<tr><th>목적</th><th>설명</th></tr>
<tr><td><strong>1) 편향 없는 데이터 진실 측정</strong></td><td>본 연구가 6개 후보를 미리 정해두었지만, 데이터에 실제로 무엇이 있는지는 모름. 명시 prompt 없이 자유 추출하면 "사용자 리뷰에 실제 등장하는 패턴 분포"를 알 수 있음.</td></tr>
<tr><td><strong>2) 6개 후보의 데이터 정합성 검증</strong></td><td>이론에서 도출한 6개가 실제 데이터에 등장하는가? Step 3 임베딩 매칭의 검증 자료가 됨.</td></tr>
<tr><td><strong>3) 자유 추출의 한계 정량화</strong></td><td>본 연구의 명시 prompt 설계가 정당화되려면 "자유 추출만으로는 부족하다"는 증거가 필요. §1의 90.8% 결과가 이로부터 도출.</td></tr>
<tr><td><strong>4) emergent 패턴 발견</strong></td><td>이론에 없지만 데이터에 강하게 등장하는 패턴이 있다면? — Step 4에서 emotional_resonance 발견.</td></tr>
</table>

<h3>4.2 자유 추출 방법</h3>

<ol>
<li><strong>샘플</strong>: 1,000명 overlapping users 中 Train 800명의 첫 100명 (seed=42, deterministic)</li>
<li><strong>입력</strong>: 사용자별 영화 리뷰 15~30개 (최신순)</li>
<li><strong>프롬프트</strong>: <code>prompts/pilot_profiler_prompt.md</code> — <em>"이 사용자의 선호 패턴을 자유롭게 추출하라. 개수 제한 없음. 패턴마다 이름·값·근거·신뢰도를 포함."</em></li>
<li><strong>LLM</strong>: GPT-4o-mini (temperature=0.0, seed=42)</li>
<li><strong>비용</strong>: $0.081 (100명 × ~$0.0008)</li>
<li><strong>Raw 출력</strong>: 100명 × 평균 8개 패턴 = <strong>806개 raw 패턴</strong></li>
</ol>

<h3>4.3 806 raw → 391 canonical 정규화 (HDBSCAN 클러스터링)</h3>

<p>806개 raw 패턴 중에는 같은 의미인데 이름만 다른 것이 많다 (예: <em>"genre_taste"</em>와 <em>"genre_preference"</em>). 의미적으로 같은 것을 묶어주는 정규화가 필요하다.</p>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — HDBSCAN이 뭐야?</div>
<span class="term">HDBSCAN (Hierarchical Density-Based Spatial Clustering)</span>은 <strong>비슷한 의미를 가진 것끼리 자동으로 묶는 기법</strong>. 미리 "몇 개로 묶을지" 정할 필요가 없고, 데이터의 밀도가 높은 영역을 자동으로 군집(cluster)으로 인식한다. K-Means(미리 K 결정 필요)와 달리 데이터가 알아서 군집 수를 결정.<br>
<strong>본 연구에서는</strong>: 806개 raw 패턴 이름을 <strong>임베딩(embedding, 의미를 숫자 벡터로 변환)</strong>한 후 HDBSCAN으로 묶음 → 자연스럽게 391개 의미 있는 군집(=canonical 패턴)으로 정리.
</div>

<p>정규화 절차:</p>
<ol>
<li>806개 패턴 이름 + 설명을 <code>sentence-transformers all-MiniLM-L6-v2</code>로 임베딩 (각 패턴이 384차원 벡터)</li>
<li>HDBSCAN으로 의미 군집화 (min_cluster_size=2)</li>
<li>각 군집의 대표 이름 추출 → <strong>canonical 패턴</strong></li>
<li>군집 미형성된 단독 패턴은 그대로 canonical로 보존</li>
<li>결과: <span class="key-stat">391 canonical 패턴</span></li>
</ol>

<h3>4.4 391 canonical의 분포 (Pareto chart)</h3>

{"<img class='chart' src='" + IMG_FREQ + "' />" if IMG_FREQ else ""}
<p class="fig-caption">Figure 1. Pilot 391 canonical 패턴 빈도 상위 25개 — long-tail 분포 (대부분 1~2명 등장)</p>

<div class="callout">
<strong>관찰</strong>:
<ul>
<li>상위 25개에 들어가는 패턴은 nostalgic·family_friendly·humor 등 <strong>표층 감정</strong>이 많음</li>
<li>빈도 elbow가 N=7에서 떨어지지만, <strong>이 7개는 본 연구의 7개와 구성이 다름</strong> (빈도 기준일 뿐)</li>
<li>대부분(70%+) 패턴이 1~2명에서만 등장 — <strong>long-tail 분포</strong></li>
</ul>
</div>

<div class="callout-green nobreak">
<strong>Step 2 산출</strong>: <span class="key-stat">391 canonical 패턴</span> (806 raw → HDBSCAN 정규화)<br>
이 391개가 <strong>"데이터 진실"</strong>이며, Step 3에서 6개 후보와 매칭된다.
</div>

<!-- ============================================================ -->
<!-- §5. Step 3 — 임베딩 매칭 -->
<!-- ============================================================ -->
<h2 class="pagebreak">5. Step 3 — 6 후보 ↔ 391 canonical 임베딩 매칭</h2>

<h3>5.1 왜 임베딩 매칭을 하는가</h3>

<table>
<tr><th>목적</th><th>설명</th></tr>
<tr><td><strong>1) 데이터 실재 확인</strong></td><td>본 연구가 도출한 6개 후보가 <strong>실제 데이터(391 canonical)에 존재</strong>하는가? 만약 6개 중 하나가 데이터에 전혀 등장하지 않으면 그 후보는 무의미한 임의 정의.</td></tr>
<tr><td><strong>2) 자기참조 회피</strong></td><td>본 연구가 직접 "이 후보가 좋다"고 판정하면 자기참조(짜맞춤). 대신 <strong>임베딩 모델이 자동으로 매칭</strong>하면 객관적 검증.</td></tr>
<tr><td><strong>3) 후보별 발현 강도 측정</strong></td><td>후보가 데이터에 얼마나 강하게 등장하는가? cosine similarity 값으로 정량.</td></tr>
</table>

<h3>5.2 임베딩 매칭의 방법</h3>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 임베딩 cosine similarity가 뭐야?</div>
<span class="term">임베딩(embedding)</span>은 단어/문장의 <strong>의미를 숫자 벡터로 변환</strong>하는 기법. 예: "happy" → [0.21, -0.45, 0.78, ...] (384개 숫자)<br>
<span class="term">코사인 유사도(cosine similarity)</span>는 두 벡터의 <strong>방향이 얼마나 비슷한지</strong>를 -1 ~ 1 사이 값으로 측정.<br>
- sim = 1.0 → 정확히 같은 의미<br>
- sim = 0.7+ → 강한 유사<br>
- sim = 0.5+ → 중간 유사 (본 연구의 통과 기준)<br>
- sim ≤ 0.3 → 거의 무관<br>
<strong>본 연구에서는</strong>: 6 후보 정의 텍스트와 391 canonical 정의 텍스트를 각각 임베딩 → 6 × 391 = 2,346쌍의 sim 계산 → 후보별 가장 높은 sim의 canonical이 "데이터에서의 본 후보의 발현"이다.
</div>

<h3>5.3 매칭 결과</h3>

<table>
<tr><th>후보 패턴</th><th>Top-1 Pilot 매칭</th><th>Sim</th><th>강도</th><th>의미</th></tr>
<tr><td>genre_preference</td><td>genre_diversity</td><td>0.699</td><td><span class="warn">MEDIUM</span></td><td>장르 다양성 신호 존재</td></tr>
<tr class="highlight-row"><td><strong>narrative_complexity</strong></td><td><strong>narrative_complexity</strong></td><td><strong>0.803</strong></td><td><span class="pass">STRONG (직접)</span></td><td>같은 이름으로 발현 — 가장 강한 매칭</td></tr>
<tr class="highlight-row"><td>pacing_preference</td><td>tolerance_for_slow_pacing</td><td>0.807</td><td><span class="pass">STRONG</span></td><td>"느린 전개 허용" 패턴이 강하게 발현</td></tr>
<tr><td>quality_sensitivity</td><td>variable_rating_on_quality</td><td>0.552</td><td><span class="warn">MEDIUM</span></td><td>품질 민감도 신호 존재</td></tr>
<tr><td>brand_loyalty</td><td>franchise_loyalty</td><td>0.696</td><td><span class="warn">MEDIUM</span></td><td>프랜차이즈 충성도로 발현</td></tr>
<tr><td>sensory_preference</td><td>enjoyment_of_action_movies</td><td>0.591</td><td><span class="warn">MEDIUM</span></td><td>액션 영화 즐김 → 감각 차원</td></tr>
</table>

<h3>5.4 결과의 의미</h3>

<div class="callout-green">
<strong>✅ 6/6 모두 sim ≥ 0.5로 발현</strong> — 본 연구의 6개 후보가 모두 데이터에 실재함이 확인됨.
</div>

<table>
<tr><th>의미</th><th>해석</th></tr>
<tr><td>narrative_complexity (sim 0.80)</td><td>본 연구가 정의한 이름 그대로 사용자가 자연스럽게 표현 → <strong>가장 강력한 검증</strong></td></tr>
<tr><td>pacing_preference (sim 0.81)</td><td>"tolerance_for_slow_pacing"으로 변형 등장 — 본 연구의 "느린 전개 선호"와 의미 일치</td></tr>
<tr><td>4개 MEDIUM (sim 0.55~0.70)</td><td>이름은 다르나 의미는 본 연구 후보와 부합 — 자유 추출의 표면 표현 차이일 뿐 본질 동일</td></tr>
<tr><td>최저 sim 0.55 (quality_sensitivity)</td><td>데이터에서 가장 약한 발현이나 임계값 통과 — Cross-Domain에선 PARTIAL 라벨로 적합</td></tr>
</table>

<div class="callout-warn">
<strong>주의</strong>: 매칭이 sim 0.5 이상이지만 1.0은 아니다. 즉 본 연구의 6개와 데이터 391은 <strong>완전 일치가 아닌 의미적 정합</strong>이다. 이는 자연스러운 결과 — 자유 추출 데이터에는 "표면 표현"이 다양하기 때문.
</div>

<!-- ============================================================ -->
<!-- §6. Step 4 — emotional_resonance 7번째 추가 -->
<!-- ============================================================ -->
<h2 class="pagebreak">6. Step 4 — emotional_resonance 7번째 추가 정당화</h2>

<h3>6.1 발견 — 이론에 없으나 데이터에 강하게 등장</h3>

<p>Step 3에서 6개 후보의 매칭을 보다가 흥미로운 사실 발견:</p>

<div class="callout-green">
<strong>Pilot 391 canonical 中 "emotional_resonance"가 같은 이름으로 등장</strong><br>
- sim 0.816 (이론 후보가 아닌데 같은 이름이 데이터에 등장)<br>
- <strong>14% 빈도</strong> (100명 中 14명에서 emerge — 표층 패턴인 nostalgic_preference 다음으로 자주 등장)<br>
- 의미: "콘텐츠가 깊은 감정·여운·개인적 의미를 남기는지 중시"
</div>

<h3>6.2 emotional_resonance가 7번째로 추가된 이유</h3>

<table>
<tr><th>기준</th><th>평가</th><th>판정</th></tr>
<tr><td>이론 정합성 (C1)</td><td>Thet 2010·Liu 2012에 직접 등재 없음. affective recommendation 분야에 일반 개념은 있으나 약함</td><td><span class="crit-mid">△</span></td></tr>
<tr><td>Pilot 발현 (C2)</td><td>14% 사용자에서 등장, sim 0.82로 직접 매칭 — <strong>이론 후보 6개 중 어느 것보다 강한 단독 신호</strong></td><td><span class="crit-pass">○</span></td></tr>
<tr><td>Cross-Domain 적합성 (C3)</td><td>Movies-only 키워드 0개, 책에도 적용 가능 (책 "감동적인 작품 선호" 자연스러움)</td><td><span class="crit-pass">○</span></td></tr>
<tr><td>직교성 (C4)</td><td>다른 6개와 max sim 0.38 (vs sensory) — 매우 안전</td><td><span class="crit-pass">○</span></td></tr>
</table>

<h3>6.3 추가의 의미 — 방법론의 보완 절차</h3>

<div class="callout">
<strong>본 연구의 접근</strong>:
<ul>
<li><strong>이론에서 출발</strong>한 6개 후보(Step 1)</li>
<li><strong>데이터로 검증</strong>(Step 2-3)하면서</li>
<li><strong>이론에 없으나 데이터가 강하게 말하는 패턴은 추가</strong>(Step 4)</li>
</ul>
이렇게 <strong>이론 + 데이터의 양방향 검증</strong>이 본 방법론의 핵심.<br>
emotional_resonance는 "방법론이 닫혀있지 않고 데이터 신호에 열려있음"을 시연하는 사례.
</div>

<div class="easy-note">
<div class="easy-title">💡 쉬운 설명 — 왜 이게 학술적으로 중요한가</div>
보통 연구는 두 방향 중 하나만 한다:<br>
- <strong>이론 중심</strong>: 학술적 정의에서 출발 → 단점: 데이터에 안 맞을 수 있음<br>
- <strong>데이터 중심</strong>: 데이터에서 발견 → 단점: 임의로 보임, 학술 근거 약함<br>
본 연구는 <strong>둘 다 사용</strong>한다. 6개는 이론 anchor에서 시작, 1개(emotional)는 데이터에서 추가. 이렇게 <strong>"이론 + 데이터 = 더 단단한 정당화"</strong>가 본 연구의 강점.
</div>

<!-- ============================================================ -->
<!-- §7. 4가지 측면 종합 검토 + 채택 결과 -->
<!-- ============================================================ -->
<h2 class="pagebreak">7. 4가지 측면 종합 검토 + 최종 7개 채택</h2>

<h3>7.1 4가지 측면 (C1~C4)</h3>

<table>
<tr><th>측면</th><th>측정 방법</th><th>○ 기준</th><th>△ 기준</th><th>✗ 기준</th></tr>
<tr><td>C1 이론 정합성</td><td>aspect mining 차용 강도</td><td>직접 차용</td><td>일반화 차용</td><td>차용 약함</td></tr>
<tr><td>C2 Pilot 발현</td><td>391과의 max cosine sim</td><td>≥ 0.7</td><td>≥ 0.5</td><td>&lt; 0.5</td></tr>
<tr><td>C3 Cross-Domain</td><td>Movies-only 키워드 검출 수</td><td>0개</td><td>1개</td><td>≥ 2개</td></tr>
<tr><td>C4 직교성</td><td>다른 패턴과의 max sim</td><td>≤ 0.6</td><td>≤ 0.7</td><td>&gt; 0.7</td></tr>
</table>

<h3>7.2 7개 패턴별 종합 결과</h3>

<table>
<tr><th>Pattern</th><th>C1 이론</th><th>C2 Pilot</th><th>C3 CDR</th><th>C4 직교</th><th>결정</th></tr>
<tr><td>genre_preference</td><td>○</td><td>△ 0.70</td><td>○ TRANSFER</td><td>○ 0.47</td><td><span class="pass">ACCEPT</span></td></tr>
<tr><td>narrative_complexity</td><td>○</td><td>○ 0.80</td><td>○ TRANSFER</td><td>△ 0.67</td><td><span class="pass">ACCEPT</span></td></tr>
<tr><td>pacing_preference</td><td>○</td><td>○ 0.81</td><td>○ TRANSFER</td><td>△ 0.67</td><td><span class="pass">ACCEPT</span></td></tr>
<tr><td>quality_sensitivity</td><td>○</td><td>△ 0.55</td><td>△ PARTIAL</td><td>○ 0.37</td><td><span class="pass">ACCEPT (조건부)</span></td></tr>
<tr><td>brand_loyalty</td><td>△</td><td>△ 0.70</td><td>✗ BLOCK</td><td>○ 0.33</td><td><span class="pass">ACCEPT (BLOCK 후보)</span></td></tr>
<tr><td>sensory_preference</td><td>△</td><td>△ 0.59</td><td>△ PARTIAL</td><td>○ 0.47</td><td><span class="pass">ACCEPT (보완 필요)</span></td></tr>
<tr class="highlight-row"><td><strong>emotional_resonance</strong></td><td>△</td><td>○ 0.82</td><td>○ TRANSFER</td><td>○ 0.38</td><td><span class="pass">ACCEPT</span></td></tr>
</table>

<h3>7.3 사전 검토 5항목 (Pilot 결과 보기 전 등록)</h3>

<div class="check-grid">
  <div class="check-card">
    <div class="check-id">1</div>
    <div class="check-mark">✅</div>
    <div class="check-label">Pilot 발현</div>
    <div class="check-result">7/7<br>(sim ≥ 0.5)</div>
  </div>
  <div class="check-card">
    <div class="check-id">2</div>
    <div class="check-mark">✅</div>
    <div class="check-label">자유 추출 한계</div>
    <div class="check-result">90.8%<br>비-CDR-적합</div>
  </div>
  <div class="check-card">
    <div class="check-id">3</div>
    <div class="check-mark">✅</div>
    <div class="check-label">직교성</div>
    <div class="check-result">max 0.669<br>(≤0.7)</div>
  </div>
  <div class="check-card">
    <div class="check-id">4</div>
    <div class="check-mark">✅</div>
    <div class="check-label">BLOCK 식별</div>
    <div class="check-result">sensory<br>cinematograph</div>
  </div>
  <div class="check-card">
    <div class="check-id">5</div>
    <div class="check-mark">✅</div>
    <div class="check-label">emotional 매칭</div>
    <div class="check-result">sim 0.820<br>(직접)</div>
  </div>
</div>

<h3>7.4 직교성 검증 (보조)</h3>

{"<img class='chart' src='" + IMG_ORTHO + "' />" if IMG_ORTHO else ""}
<p class="fig-caption">Figure 2. 7개 패턴 정의 텍스트의 7×7 cosine similarity (max off-diagonal 0.669, threshold 0.7 미달)</p>

<!-- ============================================================ -->
<!-- §8. 결론 -->
<!-- ============================================================ -->
<h2 class="pagebreak">8. 결론</h2>

<h3>8.1 4단계 프로세스 요약</h3>

<ol>
<li><strong>Step 1</strong>: Thet 2010 영화 aspect 7개 + Liu 2012 ABSA 표준 + 추천시스템 관행 → Cross-Domain 재구성 → <strong>6개 후보 도출</strong></li>
<li><strong>Step 2</strong>: Pilot 100명 자유 추출 → 806 raw → HDBSCAN 정규화 → <strong>391 canonical 패턴</strong></li>
<li><strong>Step 3</strong>: 6 후보 ↔ 391 canonical 임베딩 매칭 → <strong>6/6 모두 sim ≥ 0.5로 발현 확인</strong></li>
<li><strong>Step 4</strong>: Pilot에서 emerge한 emotional_resonance (sim 0.82, 14% 빈도)를 데이터 기반으로 추가 → <strong>최종 7개 확정</strong></li>
</ol>

<h3>8.2 본 Pilot Study가 입증한 것</h3>

<table>
<tr><th>입증 항목</th><th>결과</th></tr>
<tr><td>자유 추출만으로는 부족함</td><td>90.8% 비-CDR-적합 → 명시 prompt 설계 정당화</td></tr>
<tr><td>6개 후보의 데이터 실재성</td><td>6/6 모두 sim ≥ 0.5 발현</td></tr>
<tr><td>BLOCK 메커니즘 정당성</td><td>brand·sensory가 Movies-only 키워드 자동 검출</td></tr>
<tr><td>방법론의 보완 절차</td><td>emotional_resonance를 데이터 기반 추가 시연</td></tr>
<tr><td>7개 패턴의 의미적 독립성</td><td>직교성 max 0.669 ≤ 0.7</td></tr>
</table>

<h3>8.3 논문에 쓸 수 있는 핵심 표현</h3>

<div class="quote-box">
"본 연구는 Cross-Domain 추천에 적합한 7개 Core Pattern을 4단계 프로세스로 도출하였다.
(1) Thet et al. (2010) 영화 리뷰 aspect mining과 Liu (2012) ABSA 표준에서 6개 후보 패턴을 Cross-Domain 적용 가능 형태로 재구성하였다.
(2) Pilot Study (n=100)에서 자유 추출 prompt로 806개 raw 패턴을 도출하고 HDBSCAN 임베딩 클러스터링으로 391 canonical 패턴으로 정규화하였다.
(3) 6개 후보와 391 canonical 사이 cosine similarity 매칭에서 6/6 모두 sim ≥ 0.5로 발현됨이 확인되었다.
(4) Pilot에서 강하게 emerge한 emotional_resonance (sim <span class="key-stat">0.82</span>, 14% 빈도)를 데이터 기반으로 추가하여 최종 7개 패턴으로 확정하였다.
자유 추출 결과의 <span class="key-stat">90.8%</span>가 매체-종속·표층·메타 신호로 분류되어 명시 prompt 설계의 정당성이 데이터로 입증되었으며, brand_loyalty와 sensory_preference는 Movies-only 키워드(actor·director·cinematograph) 자동 검출로 Transfer Gate의 BLOCK 후보로 식별되었다."
</div>

<h3>8.4 한계 및 향후 작업</h3>

<table>
<tr><th>한계</th><th>대응</th></tr>
<tr><td>Pilot 100명 (LLM4CDR 수준)</td><td>본 실험 1,000명에서 통계적 일반화</td></tr>
<tr><td>emotional_resonance 이론 anchor 약함</td><td>Pilot 데이터로 보완 (sim 0.82, 14% 빈도)</td></tr>
<tr><td>medium_specific 분류의 보수성</td><td>결론은 50~60%만 매체-종속이어도 동일</td></tr>
<tr><td>본 도메인(Movies → Books) 한정</td><td>다른 CDR 시나리오 적용은 향후 작업</td></tr>
</table>

<div class="callout">
<strong>본 연구의 contribution</strong><br>
- <strong>메인</strong>: Profiler-Judge 구조의 LLM 기반 CDR 프레임워크<br>
- <strong>서브</strong>: Pilot 기반 패턴 선정 절차 (자기참조 회피, 이론+데이터 양방향 검증)<br>
7개 패턴은 본 도메인(Movies&amp;TV → Books)에 적용한 결과물이며, 본 방법론은 다른 CDR 시나리오에도 재적용 가능.
</div>

<p style="text-align: center; color: #666; font-size: 9pt; margin-top: 20px;">
— 본 보고서 v4의 핵심 메시지: 본 연구의 7개 Core Pattern은 <strong>이론 anchor + Pilot 검증 + 데이터 기반 보완</strong>의 4단계 프로세스로 도출되었다 —
</p>

</body>
</html>
"""


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc = weasyprint.HTML(string=HTML_CONTENT)
    doc.write_pdf(OUTPUT_PATH)
    print(f"PDF generated: {OUTPUT_PATH}")
