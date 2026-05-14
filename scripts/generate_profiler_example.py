"""Profiler 작동 과정 예시 PDF — 두 사용자 사례 + 단계별 다이어그램.

사용자:
  - 좋은 예시 (Good): AFV67EPET244JPRAPVGZUYZ64OXA (다양한 패턴 잘 추출)
  - Random: AG5KBUJWC64SJJMRZ5QHZ6HO375A (편향 없는 표본)

산출: docs/Profiler_Process_Example.pdf
"""
from __future__ import annotations

import base64
import html
import json
import os
from pathlib import Path

import pandas as pd
import weasyprint

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "docs/phase1/Profiler_Process_Example.pdf"

USER_GOOD = "AFV67EPET244JPRAPVGZUYZ64OXA"
USER_RANDOM = "AG5KBUJWC64SJJMRZ5QHZ6HO375A"
N_REVIEWS_TO_SHOW = 5


def load_user_data(user_id: str, reviews_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """사용자의 원본 리뷰 + Profile JSON 로드."""
    profile_path = ROOT / f"profiler_outputs/user_{user_id}.json"
    profile = json.load(open(profile_path))
    user_reviews = reviews_df[reviews_df["user_id"] == user_id].sort_values("timestamp", ascending=False).head(N_REVIEWS_TO_SHOW)
    return user_reviews, profile


def format_reviews(reviews_df: pd.DataFrame) -> str:
    """리뷰를 HTML로 포맷."""
    rows = []
    for i, (_, r) in enumerate(reviews_df.iterrows(), start=1):
        title = html.escape(str(r.get("title", ""))[:100])
        text = html.escape(str(r.get("text", ""))[:200])
        rating = r.get("rating", "N/A")
        rows.append(f'<div class="review-item"><span class="rev-num">[{i}]</span> <span class="rev-rating">★{rating}/5</span> <strong>"{title}"</strong><br>"{text}{"..." if len(str(r.get("text","")))>200 else ""}"</div>')
    return "\n".join(rows)


def format_profile(profile: dict) -> str:
    """Profile JSON을 7-pattern 카드로 포맷."""
    cards = []
    cp = profile.get("core_patterns", {})
    pattern_order = [
        "genre_preference", "narrative_complexity", "pacing_preference",
        "quality_sensitivity", "brand_loyalty", "sensory_preference",
        "emotional_resonance",
    ]
    for name in pattern_order:
        p = cp.get(name, {})
        if not p:
            continue
        value = html.escape(str(p.get("value", ""))[:80])
        conf = p.get("confidence", "?")
        pol = p.get("polarity", "?")
        tr = p.get("transferability_hint", "?")
        evid = p.get("evidence", [])
        evid_str = html.escape(str(evid[0])[:120]) if evid else "(없음)"
        # 색상
        conf_class = "conf-high" if float(conf) >= 0.7 else ("conf-mid" if float(conf) >= 0.4 else "conf-low")
        pol_class = f"pol-{pol}"
        cards.append(f'''
        <div class="pattern-card">
          <div class="pattern-name">{name}</div>
          <div class="pattern-value">{value}</div>
          <div class="pattern-meta">
            <span class="{conf_class}">conf {conf}</span>
            <span class="{pol_class}">{pol}</span>
            <span class="tr-tag">tr:{tr}</span>
          </div>
          <div class="pattern-evidence">📝 {evid_str}</div>
        </div>''')
    additional = profile.get("additional_patterns", [])
    add_str = ""
    if additional:
        add_items = [f'<li><strong>{html.escape(str(a.get("name","")))}</strong>: {html.escape(str(a.get("value",""))[:60])} (conf {a.get("confidence","?")})</li>' for a in additional[:3]]
        add_str = '<div class="additional-box"><strong>Additional Patterns</strong><ul>' + "".join(add_items) + '</ul></div>'
    summary = html.escape(str(profile.get("summary", ""))[:300])
    return "\n".join(cards) + add_str + f'<div class="summary-box"><strong>Summary</strong>: {summary}</div>'


def main() -> None:
    print("[Loading] reviews + profiles")
    reviews_df = pd.read_parquet(ROOT / "data/movies_reviews_filtered.parquet")
    good_reviews, good_profile = load_user_data(USER_GOOD, reviews_df)
    rand_reviews, rand_profile = load_user_data(USER_RANDOM, reviews_df)
    print(f"  Good: {len(good_reviews)} reviews shown")
    print(f"  Random: {len(rand_reviews)} reviews shown")

    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 2cm 1.8cm;
    @bottom-center {{ content: counter(page); font-size: 10px; color: #999; }}
  }}
  body {{
    font-family: -apple-system, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    font-size: 10pt;
    line-height: 1.5;
    color: #222;
  }}
  h1 {{ text-align: center; font-size: 18pt; margin-bottom: 5px; color: #1a1a2e; }}
  .subtitle {{ text-align: center; font-size: 10pt; color: #555; margin-bottom: 20px; }}
  h2 {{
    font-size: 13pt; color: #16213e;
    border-bottom: 2.5px solid #4a90d9; padding-bottom: 4px;
    margin-top: 22px;
  }}
  h3 {{ font-size: 11pt; color: #0f3460; margin-top: 14px; }}
  .pagebreak {{ page-break-before: always; }}
  .nobreak {{ page-break-inside: avoid; }}

  /* 단계별 다이어그램 */
  .step-row {{
    display: flex; align-items: stretch; gap: 6px;
    margin: 8px 0;
  }}
  .step-box {{
    flex: 1; border-radius: 5px; padding: 10px 12px;
    font-size: 9pt; line-height: 1.4;
  }}
  .step-input {{ background: #fff4e6; border: 1.5px solid #e08a3c; }}
  .step-process {{ background: #e7f1fb; border: 1.5px solid #2f7bc4; }}
  .step-validate {{ background: #fff8d9; border: 1.5px solid #c4a23c; }}
  .step-output {{ background: #e8f5e9; border: 1.5px solid #2f9a53; }}
  .step-title {{ font-weight: 700; font-size: 10pt; color: #1a2555; margin-bottom: 4px; }}
  .arrow {{ text-align: center; color: #2d3e8a; font-size: 16pt; font-weight: 700; margin: 2px 0; }}

  /* 리뷰 박스 */
  .reviews-container {{
    background: #fafbfc; border: 1px solid #d8dde6;
    border-radius: 5px; padding: 10px 12px;
    margin: 8px 0;
  }}
  .review-item {{
    margin: 6px 0; padding: 6px 8px;
    background: white; border-left: 3px solid #4a90d9;
    font-size: 9pt; line-height: 1.4;
  }}
  .rev-num {{ font-weight: 700; color: #4a90d9; }}
  .rev-rating {{ background: #fff4e6; padding: 1px 6px; border-radius: 3px; margin: 0 4px; font-size: 8.5pt; }}

  /* 패턴 카드 */
  .pattern-grid {{
    display: grid; grid-template-columns: repeat(2, 1fr);
    gap: 6px; margin: 8px 0;
  }}
  .pattern-card {{
    background: white; border: 1.2px solid #d5dae6;
    border-radius: 4px; padding: 7px 9px; font-size: 8.8pt;
  }}
  .pattern-name {{ font-weight: 700; color: #1a2555; font-size: 9.5pt; }}
  .pattern-value {{ color: #444; margin-top: 2px; font-size: 9pt; }}
  .pattern-meta {{ margin-top: 4px; font-size: 8pt; }}
  .pattern-meta span {{ display: inline-block; padding: 1px 5px; border-radius: 3px; margin-right: 3px; }}
  .conf-high {{ background: #e8f5e9; color: #2e7d32; font-weight: 600; }}
  .conf-mid {{ background: #fff3e0; color: #e65100; }}
  .conf-low {{ background: #ffebee; color: #c62828; }}
  .pol-positive {{ background: #e3f2fd; color: #1565c0; }}
  .pol-negative {{ background: #fce4ec; color: #c62828; }}
  .pol-mixed {{ background: #f3e5f5; color: #6a1b9a; }}
  .tr-tag {{ background: #f0f4f8; color: #555; }}
  .pattern-evidence {{ margin-top: 4px; font-size: 8pt; color: #666; font-style: italic; }}

  /* 추가 박스 */
  .additional-box {{
    background: #f0f4f8; border-left: 3px solid #4a90d9;
    padding: 6px 10px; margin: 8px 0; font-size: 9pt;
  }}
  .additional-box ul {{ margin: 3px 0; padding-left: 18px; }}
  .summary-box {{
    background: #fffef0; border: 1px dashed #d79a2e;
    padding: 8px 10px; margin: 8px 0; font-size: 9pt;
    line-height: 1.5;
  }}

  /* 사용자 헤더 */
  .user-header {{
    background: linear-gradient(90deg, #4a90d9 0%, #16213e 100%);
    color: white; padding: 6px 12px;
    border-radius: 4px; font-weight: 700;
    font-size: 10.5pt; margin: 14px 0 8px 0;
  }}
  .user-badge {{
    display: inline-block; background: rgba(255,255,255,0.3);
    padding: 1px 6px; border-radius: 3px;
    font-size: 9pt; margin-left: 6px;
  }}

  .callout {{
    background: #f0f4f8; border-left: 4px solid #4a90d9;
    padding: 8px 12px; margin: 8px 0; font-size: 9pt;
  }}

  /* 패턴 정의 표 */
  .pattern-def-table {{
    width: 100%; border-collapse: collapse; margin: 6px 0 12px 0;
    font-size: 8.7pt; line-height: 1.4;
  }}
  .pattern-def-table th {{
    background: #16213e; color: white; padding: 5px 7px;
    text-align: left; font-weight: 600; font-size: 8.7pt;
  }}
  .pattern-def-table td {{
    padding: 5px 7px; border-bottom: 1px solid #ddd;
    vertical-align: top;
  }}
  .pattern-def-table tr:nth-child(even) td {{ background: #f8f9fa; }}
</style>
</head>
<body>

<h1>Profiler 작동 과정 — 예시 2명</h1>
<p class="subtitle">TransferJudge · GPT-4o-mini 기반 7-Core Pattern 추출 · 2026.05</p>

<!-- ========== 1. Profiler 작동 단계 다이어그램 ========== -->
<h2>1. Profiler 작동 단계</h2>

<div class="step-row nobreak">
<div class="step-box step-input">
  <div class="step-title">① 입력 (Source 리뷰)</div>
  사용자별 최신 15~30개 Movies&amp;TV 리뷰 (rating + title + text). 평균 23개 리뷰, ~2,400 tokens.
</div>
</div>
<div class="arrow">↓</div>
<div class="step-row nobreak">
<div class="step-box step-process">
  <div class="step-title">② Profiler (GPT-4o-mini)</div>
  System Prompt: 7개 Core Pattern 정의 + JSON 스키마 강제.<br>
  설정: temperature=0.0, seed=42, response_format=json_object, max_tokens=2000.<br>
  비용: ~$0.001/사용자.
</div>
</div>
<div class="arrow">↓</div>
<div class="step-row nobreak">
<div class="step-box step-validate">
  <div class="step-title">③ JSON 검증</div>
  7개 core_patterns 키 완전성 / polarity ∈ {{positive, negative, mixed}} /
  confidence ∈ [0,1] / transferability_hint ∈ {{high, medium, low}} / evidence 비공백 / summary 존재.
  실패 시 3회 self-correction 재시도 (temperature 약간 상승).
</div>
</div>
<div class="arrow">↓</div>
<div class="step-row nobreak">
<div class="step-box step-output">
  <div class="step-title">④ 출력 (Profile JSON)</div>
  7 core_patterns × (value, evidence, confidence, polarity, transferability_hint)
  + additional_patterns 최대 3개 + summary (2~3문장).<br>
  저장: <code>profiler_outputs/user_{{user_id}}.json</code>
</div>
</div>

<div class="callout">
<strong>핵심 설계 포인트</strong><br>
- <strong>Semi-Structured</strong>: 7개는 필수, additional은 자유 (long-tail 보존)<br>
- <strong>Evidence Grounding</strong>: 모든 패턴은 원문 인용 필수 (hallucination 방지)<br>
- <strong>negative polarity 활용</strong>: 낮은 평점 리뷰에서 "싫어하는 것" 신호 추출<br>
- <strong>transferability_hint</strong>: Profiler가 주는 초기 힌트일 뿐, 최종 TRANSFER/PARTIAL/BLOCK 판정은 다음 단계 Judge가 결정
</div>

<!-- ========== 2. 7개 Core Pattern 정의 + 출력 판단 ========== -->
<h2 class="pagebreak">2. 7개 Core Pattern — 정의 + 어떻게 판단·출력되나</h2>

<p>Profiler가 추출하는 7개 패턴 각각의 <strong>정의</strong>, <strong>리뷰에서 찾는 신호</strong>, <strong>value·polarity·transferability_hint 결정 방식</strong>을 한눈에 정리.</p>

<h3>2.1 패턴 정의 + 판단 신호</h3>

<table class="pattern-def-table">
<tr>
  <th style="width: 16%;">패턴 (영문/국문)</th>
  <th style="width: 30%;">정의 (무엇을 측정하나)</th>
  <th style="width: 30%;">리뷰에서 찾는 신호</th>
  <th style="width: 24%;">value 출력 형태 + 예시</th>
</tr>
<tr>
  <td><strong>genre_preference</strong><br>선호 장르</td>
  <td>사용자가 좋아하는·싫어하는 콘텐츠 장르·카테고리 (sci-fi, thriller, drama 등)</td>
  <td>리뷰에 명시된 장르 단어, 반복 등장 빈도, 낮은 평점 + 부정 표현 ("rom-com is boring")</td>
  <td>장르 이름 나열 — 예: <em>"drama, documentary, romance"</em></td>
</tr>
<tr>
  <td><strong>narrative_complexity</strong><br>서사 복잡도</td>
  <td>복잡한 서사(다중 시간선·비선형 플롯·다층 캐릭터) vs 단순 서사 선호도</td>
  <td>"plot was confusing/genius", "multi-layered", "straightforward", "twists", "character depth" 등 서사 구조 언급</td>
  <td><em>complex / medium / simple</em> 또는 mixed</td>
</tr>
<tr>
  <td><strong>pacing_preference</strong><br>전개 속도</td>
  <td>빠른 전개(액션·긴장) vs 느린 전개(인물 중심·여운) 선호도</td>
  <td>"slow-burn", "fast-paced", "boring", "page-turner", "dragged on", "well-paced" 등 속도 관련 표현</td>
  <td><em>fast / slow / mixed</em></td>
</tr>
<tr>
  <td><strong>quality_sensitivity</strong><br>품질 민감도</td>
  <td>제작 품질·기술적 완성도(연기·연출·평점)에 대한 민감도</td>
  <td>"great acting", "poor directing", "cinematography", "ratings", "production value" 언급 빈도</td>
  <td><em>high / medium / low</em></td>
</tr>
<tr>
  <td><strong>brand_loyalty</strong><br>창작자 충성도</td>
  <td>특정 감독·배우·작가·프랜차이즈에 대한 충성도</td>
  <td>창작자 이름 반복 언급, "Nolan never disappoints", "I watch everything by X" 표현</td>
  <td>창작자 이름 — 예: <em>"Christopher Nolan, Denis Villeneuve"</em>, 또는 high/medium/low</td>
</tr>
<tr>
  <td><strong>sensory_preference</strong><br>감각적 경험</td>
  <td>영상미·음향·액션 안무·분위기 등 감각 경험 중시도</td>
  <td>"cinematography", "IMAX", "soundtrack", "visuals", "action choreography", "atmospheric" 등</td>
  <td><em>high / medium / low</em> + 감각 종류 (visual·auditory·action)</td>
</tr>
<tr>
  <td><strong>emotional_resonance</strong> ★<br>감정적 울림</td>
  <td>콘텐츠의 깊은 감정·여운·개인적 의미를 중시하는 정도</td>
  <td>"brought tears", "stayed with me", "emotional", "moving", "soulless" (부정), "felt nothing" (부정)</td>
  <td><em>high / medium / low</em> + 정서 종류 (deep / sentimental / cathartic)</td>
</tr>
</table>

<p style="font-size: 8.7pt; color: #666;">★ = Pilot Study에서 데이터 기반으로 추가된 7번째 패턴 (이론 anchor 약함, 데이터 신호 강함)</p>

<h3>2.2 polarity (감정 극성) 판단 기준</h3>

<table class="pattern-def-table">
<tr><th style="width: 16%;">polarity</th><th>판단 기준</th><th>예시</th></tr>
<tr>
  <td><span class="pol-positive" style="padding:2px 6px;">positive</span></td>
  <td>사용자가 이 패턴 차원에서 <strong>좋아함·선호함·강하게 추구함</strong>을 명시</td>
  <td>"loved the cinematography" → sensory_preference: positive<br>"Nolan never disappoints" → brand_loyalty: positive</td>
</tr>
<tr>
  <td><span class="pol-negative" style="padding:2px 6px;">negative</span></td>
  <td>사용자가 이 패턴 차원에서 <strong>싫어함·회피함</strong>을 명시 (보통 낮은 평점 리뷰에 등장)</td>
  <td>"rom-com is boring" → genre_preference: negative (rom-com)<br>"felt nothing, soulless" → emotional_resonance: negative</td>
</tr>
<tr>
  <td><span class="pol-mixed" style="padding:2px 6px;">mixed</span></td>
  <td>긍정·부정 신호가 함께 등장하거나, 사용자가 양쪽 모두 즐김</td>
  <td>"좋아하는 장르도 있고 싫어하는 장르도 있음" → genre_preference: mixed<br>신호가 약한 경우 default로 mixed</td>
</tr>
</table>

<h3>2.3 transferability_hint (전이 가능성 힌트) 판단 기준</h3>

<p style="font-size: 9pt; color: #666; margin-bottom: 6px;">
Profiler가 Source(영화) 리뷰에서 추출한 신호가 Target(책) 도메인으로 전이될 수 있는지의 <strong>초기 힌트</strong>.
최종 TRANSFER/PARTIAL/BLOCK 판정은 Judge가 별도 수행.
</p>

<table class="pattern-def-table">
<tr><th style="width: 16%;">힌트</th><th>판단 기준</th><th>해당 패턴 경향</th></tr>
<tr>
  <td><span class="tr-tag" style="padding:2px 6px; background:#e8f5e9; color:#2e7d32;">high</span></td>
  <td>패턴이 <strong>매체 독립적</strong> — 영화 신호가 책에도 적용 가능</td>
  <td>narrative_complexity, pacing_preference, emotional_resonance, genre_preference (대부분)</td>
</tr>
<tr>
  <td><span class="tr-tag" style="padding:2px 6px; background:#fff3e0; color:#e65100;">medium</span></td>
  <td>패턴이 <strong>매체별 변환 필요</strong> — 영화 신호를 책 도메인 신호로 매핑 가능하나 동일하진 않음</td>
  <td>quality_sensitivity (영화 연기 → 책 문체)</td>
</tr>
<tr>
  <td><span class="tr-tag" style="padding:2px 6px; background:#ffebee; color:#c62828;">low</span></td>
  <td>패턴이 <strong>영화 매체 한정</strong> — 책에 적용하기 어려움</td>
  <td>sensory_preference (IMAX·사운드), brand_loyalty (영화 감독·배우)</td>
</tr>
</table>

<h3>2.4 confidence (신뢰도) 결정 방식</h3>

<table class="pattern-def-table">
<tr><th style="width: 16%;">confidence 범위</th><th>의미</th><th>예시</th></tr>
<tr>
  <td><span class="conf-high" style="padding:2px 6px;">0.7 ~ 1.0</span></td>
  <td><strong>강한 신호</strong>: 여러 리뷰에서 일관되게 명시</td>
  <td>"Nolan", "Villeneuve" 4번 이상 언급 → brand_loyalty conf 0.8</td>
</tr>
<tr>
  <td><span class="conf-mid" style="padding:2px 6px;">0.4 ~ 0.7</span></td>
  <td><strong>중간 신호</strong>: 부분적으로 명시되거나 mixed</td>
  <td>일부 리뷰에서만 언급, 일관성 약함</td>
</tr>
<tr>
  <td><span class="conf-low" style="padding:2px 6px;">0.0 ~ 0.4</span></td>
  <td><strong>약한/없는 신호</strong>: 리뷰에 거의 근거 없음, default 추측</td>
  <td>리뷰가 "Five Stars, gift for niece" 같이 빈약 → brand_loyalty conf 0.2~0.3</td>
</tr>
</table>

<div class="callout">
<strong>핵심 설계 — 약한 신호 처리</strong><br>
어떤 패턴에 대해 리뷰에 근거가 부족하면 Profiler는 <strong>억지로 강한 판단을 하지 않고</strong> confidence를 낮게(≤ 0.3) 표시 + polarity를 mixed로 설정. Judge가 후처리에서 이 약한 신호를 자동으로 약화/무시 처리. 이는 <strong>hallucination 방지</strong>와 <strong>정직한 신호 보존</strong>의 핵심 메커니즘.
</div>

<!-- ========== 3. 사례 A — 좋은 예시 ========== -->
<h2 class="pagebreak">3. 사례 A — 좋은 예시 (다양한 패턴 잘 추출됨)</h2>

<div class="user-header">User ID: {USER_GOOD} <span class="user-badge">drama·documentary 팬</span></div>

<h3>📝 입력 — Source 리뷰 (최신 {N_REVIEWS_TO_SHOW}개 발췌, 실제는 30개)</h3>
<div class="reviews-container">
{format_reviews(good_reviews)}
</div>

<h3>📊 출력 — Profile JSON (7 Core Patterns)</h3>
<div class="pattern-grid">
{format_profile(good_profile)}
</div>

<!-- ========== 4. 사례 B — Random 사용자 ========== -->
<h2 class="pagebreak">4. 사례 B — Random 사용자 (편향 없는 표본)</h2>

<div class="user-header">User ID: {USER_RANDOM} <span class="user-badge">Random seed=7 선정</span></div>

<h3>📝 입력 — Source 리뷰 (최신 {N_REVIEWS_TO_SHOW}개 발췌)</h3>
<div class="reviews-container">
{format_reviews(rand_reviews)}
</div>

<h3>📊 출력 — Profile JSON (7 Core Patterns)</h3>
<div class="pattern-grid">
{format_profile(rand_profile)}
</div>

<!-- ========== 5. 비교 + 관찰 ========== -->
<h2>5. 두 사례 비교 + 관찰</h2>

<div class="callout">
<strong>관찰 1 — 7-Pattern 완전성</strong><br>
두 사용자 모두 7개 패턴이 빠짐 없이 추출됨. confidence는 사용자별·패턴별로 다양 (0.3~0.9).
신호가 약한 패턴은 LLM이 자동으로 낮은 confidence + mixed polarity로 표시 → Judge가 후처리에서 약한 신호를 약화 처리.
</div>

<div class="callout">
<strong>관찰 2 — Evidence Grounding</strong><br>
모든 패턴의 evidence 필드에 원문 인용이 포함됨 (📝 표시). Profiler가 hallucination 없이 실제 리뷰에 근거함을 보장.
</div>

<div class="callout">
<strong>관찰 3 — Polarity 다양성</strong><br>
positive·negative·mixed 모두 등장. 낮은 평점 리뷰가 있는 사용자는 negative polarity가 추출되어 "싫어하는 것" 정보가 보존됨.
</div>

<div class="callout">
<strong>관찰 4 — Transferability Hint</strong><br>
Profiler가 추출 단계에서 high/medium/low 힌트를 부여. 이는 Judge의 Transfer Gate 판정 입력으로 사용됨.
다만 최종 TRANSFER/PARTIAL/BLOCK 결정은 Judge가 별도로 수행.
</div>

<!-- ========== 6. 다음 단계 (Teacher → QLoRA → Judge → 평가) ========== -->
<h2 class="pagebreak">6. Profile JSON이 다음 단계로 어떻게 전달되나</h2>

<p>Profiler 출력(Profile JSON)이 본 연구의 후속 파이프라인 — <strong>Teacher Distillation → QLoRA 학습 → Judge 추론 → 평가</strong> — 으로 어떻게 흘러가는지 정리.</p>

<h3>6.1 전체 파이프라인 흐름</h3>

<div class="step-row nobreak">
<div class="step-box step-output">
  <div class="step-title">[현재 단계] Profiler 출력</div>
  <code>profiler_outputs/user_*.json</code> × 1,000<br>
  · 7 core_patterns × (value, evidence, confidence, polarity, transferability_hint)<br>
  · additional_patterns 최대 3개 + summary
</div>
</div>
<div class="arrow">↓ (학습 단계 / Train 800명)</div>
<div class="step-row nobreak">
<div class="step-box step-process">
  <div class="step-title">② Teacher Distillation (GPT-4o-mini, Train 800 + Valid 100)</div>
  <strong>입력</strong>: Profile JSON + 후보 50권 (GT 1권 + Negative 49권, seed=42) + <span style="color:#c62828;">GT 힌트 (학습용)</span><br>
  <strong>출력</strong>: <code>data/teacher_train.jsonl</code> (~800 lines)<br>
   - transfer_decisions: 7 패턴 × (decision, rationale, transferred_insight, confidence)<br>
   - recommendations: Top-10 책 (rank, item_id, title, score, applied_patterns, reasoning)
</div>
</div>
<div class="arrow">↓ (학습 단계)</div>
<div class="step-row nobreak">
<div class="step-box step-validate">
  <div class="step-title">③ QLoRA 파인튜닝 (Qwen3-14B-Instruct, GPU)</div>
  <strong>입력</strong>: teacher_train.jsonl (700~800건) — Profile + 후보를 prompt로, decisions + recs를 target으로<br>
  <strong>출력</strong>: <code>checkpoints/judge_best/</code> — 학습된 Judge 모델<br>
  학습 설정: LoRA r=16, 3 epoch, lr=2e-4, 4-bit 양자화
</div>
</div>
<div class="arrow">↓ (추론 단계 / Test 100명)</div>
<div class="step-row nobreak">
<div class="step-box step-output">
  <div class="step-title">④ Judge 추론 (Test 시) — GT 힌트 없음 ★</div>
  <strong>입력</strong>: Test 사용자의 Profile JSON + 후보 50권 (Test 시점에 새로 샘플링) <span style="color:#2e7d32;">(GT 힌트 제거 ★)</span><br>
  <strong>출력</strong>: transfer_decisions + Top-10 책 추천<br>
  → NDCG@10, HR@10, MRR로 평가
</div>
</div>

<div class="callout">
<strong>★ 학습-추론 비대칭 — 본 연구의 핵심 설계</strong><br>
Teacher는 <strong>GT 힌트를 받고</strong> 올바른 decisions + Top-10을 생성 (학습 데이터 품질 보장). 그러나 Judge는 <strong>Test 추론 시 GT 힌트 없이</strong> Profile만 보고 추천. 이렇게 학습-추론의 비대칭으로 Cold-Start 시뮬레이션 완성.
</div>

<h3>6.2 단계별 데이터 매핑 — Profile JSON의 어떤 필드가 어디로?</h3>

<table class="pattern-def-table">
<tr>
  <th style="width: 25%;">Profile JSON 필드</th>
  <th style="width: 25%;">Teacher 단계 활용</th>
  <th style="width: 25%;">QLoRA 학습 시</th>
  <th style="width: 25%;">Judge 추론 시</th>
</tr>
<tr>
  <td><code>core_patterns.{{name}}.value</code></td>
  <td>Teacher가 각 패턴의 의미 파악 → decision 결정</td>
  <td>prompt에 그대로 포함 (Profile 전체를 모델 입력으로)</td>
  <td>동일 형식으로 입력 → decision·추천 생성</td>
</tr>
<tr>
  <td><code>core_patterns.{{name}}.evidence</code></td>
  <td>Teacher의 reasoning에 인용됨 (rationale 작성 시)</td>
  <td>prompt에 포함 (CoT 학습 강화)</td>
  <td>동일</td>
</tr>
<tr>
  <td><code>core_patterns.{{name}}.confidence</code></td>
  <td>약한 신호(≤0.3) 패턴은 Teacher가 자동 BLOCK 경향</td>
  <td>prompt에 포함</td>
  <td>동일</td>
</tr>
<tr>
  <td><code>core_patterns.{{name}}.polarity</code></td>
  <td>negative polarity → "이것을 피하라" 신호로 활용</td>
  <td>prompt에 포함</td>
  <td>동일</td>
</tr>
<tr>
  <td><code>core_patterns.{{name}}.transferability_hint</code></td>
  <td>Teacher의 decision 초기 힌트 (high → TRANSFER 경향, low → BLOCK 경향). 최종 결정은 Teacher의 별도 판단</td>
  <td>prompt에 포함</td>
  <td>동일</td>
</tr>
<tr>
  <td><code>additional_patterns</code></td>
  <td>Teacher가 추가 신호로 활용 (선택적)</td>
  <td>prompt에 포함</td>
  <td>동일</td>
</tr>
<tr>
  <td><code>summary</code></td>
  <td>Teacher의 overall_strategy 작성 시 참조</td>
  <td>prompt에 포함 (사용자 전체 그림)</td>
  <td>동일</td>
</tr>
</table>

<h3>6.3 핵심 변환 — Profile JSON → Teacher 학습 데이터</h3>

<div class="callout">
<strong>변환 1: 사용자별 후보 50권 + GT 힌트 추가</strong><br>
Profile JSON에는 책 정보가 없음. Teacher는 다음 정보를 함께 받음:<br>
- <strong>후보 50권</strong>: GT 1권(실제 사용자가 평점 ≥4로 구매한 책 중 가장 최근) + Negative 49권(랜덤 샘플링, seed=42)<br>
- <strong>각 책 메타</strong>: 제목, 저자, 카테고리, average_rating, features(synopsis 50 tokens)<br>
- <strong>GT 힌트</strong>: "사용자가 실제 구매한 책은 ID=BXXX 입니다" (Train·Valid에서만, Test에선 제거)
</div>

<div class="callout">
<strong>변환 2: Teacher 출력 → QLoRA 학습 형식</strong><br>
Teacher의 JSON 출력(transfer_decisions + recommendations)을 <code>(prompt, completion)</code> 쌍으로 변환:<br>
- <strong>prompt</strong>: System prompt + "User Profile: [profile_json] \\n Candidates: [50 books]"<br>
- <strong>completion</strong>: transfer_decisions + recommendations JSON<br>
Qwen3-14B + LoRA 학습 시 모델은 <strong>prompt를 보고 completion을 예측</strong>하도록 학습됨.
</div>

<div class="callout-warn">
<strong>중요 — Test 시점의 후보 50권은 학습 시점과 다름</strong><br>
Train 사용자의 후보 50권은 학습 데이터 생성용. Test 사용자는 평가 시점에 <strong>새로 후보 50권 샘플링</strong> (동일 seed=42 적용). 이는 Judge가 "이 책이 GT라고 외우는 게 아니라 진짜 추천 능력을 학습"하도록 강제하는 안전장치.
</div>

<h3>6.4 평가 흐름 (Phase 4)</h3>

<div class="step-row nobreak">
<div class="step-box step-input">
  <div class="step-title">Test 사용자 100명 입력</div>
  Profile JSON + 후보 50권 (GT 힌트 ❌)
</div>
<div class="arrow">→</div>
<div class="step-box step-process">
  <div class="step-title">Judge 추론</div>
  학습된 QLoRA 모델로<br>Top-10 추천 생성
</div>
<div class="arrow">→</div>
<div class="step-box step-output">
  <div class="step-title">평가 지표</div>
  HR@1, HR@5, HR@10<br>NDCG@5, NDCG@10, MRR
</div>
</div>

<div class="callout">
<strong>핵심: Profile JSON이 본 연구의 모든 후속 단계의 입력</strong><br>
Profiler 출력 품질이 본 실험의 기반. 따라서 Phase 1(현재)에서 7-pattern 완전성·confidence·evidence 품질 확보가 결정적.
</div>

<p style="text-align: center; color: #666; font-size: 9pt; margin-top: 25px;">
— 본 예시 2명은 Profiler 50명 시험 실행 (2026-05-12) 결과에서 추출 —
</p>

</body>
</html>
"""

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    weasyprint.HTML(string=html_content).write_pdf(str(OUTPUT_PATH))
    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
