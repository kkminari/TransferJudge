#!/usr/bin/env python3
"""TransferJudge Overview PDF v3 생성 스크립트"""

import weasyprint
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "docs", "overview")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "TransferJudge_Overview_v6.pdf")

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  @page {
    size: A4;
    margin: 2.5cm 2cm;
    @bottom-center { content: counter(page); font-size: 10px; color: #999; }
  }
  body {
    font-family: -apple-system, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    font-size: 11pt;
    line-height: 1.65;
    color: #222;
  }
  h1 {
    text-align: center;
    font-size: 22pt;
    margin-bottom: 5px;
    color: #1a1a2e;
  }
  .subtitle {
    text-align: center;
    font-size: 10.5pt;
    color: #555;
    margin-bottom: 3px;
  }
  .author {
    text-align: center;
    font-size: 10.5pt;
    color: #777;
    margin-bottom: 30px;
  }
  h2 {
    font-size: 15pt;
    color: #16213e;
    border-bottom: 2.5px solid #e94560;
    padding-bottom: 4px;
    margin-top: 35px;
  }
  h3 { font-size: 12.5pt; color: #0f3460; margin-top: 20px; }
  h4 { font-size: 11pt; color: #333; margin-top: 15px; }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 15px 0;
    font-size: 10pt;
  }
  th {
    background: #16213e;
    color: white;
    padding: 7px 8px;
    text-align: left;
    font-weight: 600;
  }
  td {
    padding: 6px 8px;
    border-bottom: 1px solid #ddd;
    vertical-align: top;
  }
  tr:nth-child(even) td { background: #f8f9fa; }
  .highlight-row td { background: #e8f4fd !important; font-weight: 600; }
  .callout {
    background: #f0f4f8;
    border-left: 4px solid #4a90d9;
    padding: 12px 15px;
    margin: 12px 0;
    font-size: 10pt;
  }
  .callout-warn {
    background: #fff8e1;
    border-left: 4px solid #f5a623;
    padding: 12px 15px;
    margin: 12px 0;
    font-size: 10pt;
  }
  .callout-red {
    background: #ffeef0;
    border-left: 4px solid #e94560;
    padding: 12px 15px;
    margin: 12px 0;
    font-size: 10pt;
  }
  code {
    background: #f0f0f0;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 9.5pt;
  }
  pre {
    background: #f5f5f5;
    padding: 12px;
    border-radius: 4px;
    font-size: 9pt;
    line-height: 1.5;
    overflow-x: auto;
  }
  .tag-transfer { color: #2e7d32; font-weight: 700; }
  .tag-partial { color: #e65100; font-weight: 700; }
  .tag-block { color: #c62828; font-weight: 700; }
  .pagebreak { page-break-before: always; }
  /* === Process flow diagrams (Section 9, 10) === */
  .flow-wrap {
    background: #fafbfc;
    border: 1px solid #d8dde6;
    border-radius: 6px;
    padding: 14px 16px;
    margin: 14px 0;
  }
  .flow-row {
    display: flex;
    align-items: stretch;
    gap: 6px;
    margin-bottom: 10px;
    flex-wrap: nowrap;
  }
  .flow-row:last-child { margin-bottom: 0; }
  .flow-box {
    flex: 1;
    min-width: 0;
    border: 1.5px solid #6b7cb5;
    border-radius: 5px;
    padding: 7px 9px;
    background: #fff;
    text-align: center;
    font-size: 9pt;
    line-height: 1.35;
  }
  .flow-box-data { background: #fff4e6; border-color: #e08a3c; }
  .flow-box-api { background: #e7f1fb; border-color: #2f7bc4; }
  .flow-box-local { background: #e6f6ed; border-color: #2f9a53; }
  .flow-box-filter { background: #fff8d9; border-color: #c4a23c; }
  .flow-box-output { background: #eaeef7; border-color: #2d3e8a; font-weight: 600; }
  .flow-box-title { font-weight: 700; color: #1a2555; margin-bottom: 2px; font-size: 9.5pt; }
  .flow-box-sub { color: #444; font-size: 8.5pt; }
  .flow-arrow-h {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #2d3e8a;
    font-size: 14pt;
    font-weight: 700;
    flex: 0 0 18px;
  }
  .flow-caption {
    font-size: 8.8pt;
    color: #666;
    text-align: center;
    margin-top: 6px;
    font-style: italic;
  }
  .flow-legend {
    font-size: 8.5pt;
    color: #555;
    text-align: center;
    margin-top: 8px;
    padding-top: 6px;
    border-top: 1px dashed #ccc;
  }
  .flow-swatch {
    display: inline-block;
    width: 9px;
    height: 9px;
    border: 1px solid #888;
    border-radius: 2px;
    margin: 0 3px 0 8px;
    vertical-align: middle;
  }
  ul, ol { margin: 5px 0; padding-left: 22px; }
  li { margin: 3px 0; }
  strong { color: #1a1a2e; }
</style>
</head>
<body>

<!-- ===== TITLE ===== -->
<h1>TransferJudge</h1>
<p class="subtitle">A Profiler-Judge LLM-Based Framework for Selective Transfer in Cross-Domain Recommendation</p>
<p class="subtitle">선택적 전이를 위한 Profiler-Judge 구조의 LLM 기반 교차 도메인 추천 프레임워크</p>
<p class="subtitle" style="margin-top: 8px; color: #2e7d32; font-weight: 600;">Pilot Study 완료 · 7개 Core Pattern 확정 (4가지 측면 종합 검토)</p>
<p class="author">2026.05 빅데이터학과 17기 곽민아 · Overview v6</p>

<!-- ===== 1. 핵심 문제 정의 ===== -->
<h2>1. 핵심 문제 정의</h2>

<h3>1.1 연구 정의 (Objective)</h3>
<table>
<tr><th style="width:100px">구분</th><th>내용</th></tr>
<tr><td><strong>연구 배경</strong></td><td>추천 시스템은 과거 행동 데이터가 충분해야 개인화 추천이 가능. 특정 도메인에서 데이터가 부족한 상황을 Cold-Start 문제라 함.</td></tr>
<tr><td><strong>접근 방식</strong></td><td>데이터가 풍부한 영화 도메인의 리뷰를 활용하여 부족한 도서 도메인의 추천에 활용하는 Cross-Domain Recommendation.</td></tr>
<tr><td><strong>핵심 문제</strong></td><td>영화 취향이 모두 도서 추천에 유용하지 않음. "놀란 감독 팬" 같은 정보는 관련 없는 도서 추천을 유발. 이를 <strong>Negative Transfer</strong>라 함.</td></tr>
<tr><td><strong>해결 방법</strong></td><td><strong>Profiler</strong> (GPT-4o-mini): 리뷰에서 구조화된 선호 패턴 추출.<br><strong>Transfer Judge</strong> (Qwen3-14B, QLoRA): 패턴별 전이 가능 여부 판별(TRANSFER/PARTIAL/BLOCK) 후 추천 생성.</td></tr>
<tr><td><strong>연구 목표</strong></td><td>Transfer Gate로 Negative Transfer를 방지하여 Cross-Domain Cold-Start 추천 품질 향상.</td></tr>
</table>

<h3>1.2 Research Questions</h3>
<table>
<tr><th>RQ</th><th>연구 질문</th><th>쉽게 말하면</th><th>비교</th></tr>
<tr><td><strong>RQ1</strong></td><td>LLM 기반 구조화된 프로파일링이 원본 리뷰 직접 입력 대비 추천 품질을 개선하는가?</td><td>영화 리뷰를 "SF 좋아함" 식으로 <strong>정리해서</strong> 넣는 게, 원문을 <strong>그대로</strong> 넣는 것보다 나은가?</td><td>(c) vs (f)</td></tr>
<tr><td><strong>RQ2</strong></td><td>Transfer Gate를 통한 선호 패턴 자동 필터링이 추천 성능에 유의한 영향을 미치는가?</td><td>책에 <strong>써먹을 수 없는 취향</strong>(예: "놀란 감독 팬")을 <strong>걸러내면</strong> 추천이 더 정확해지는가?</td><td>(c) vs (d)</td></tr>
<tr><td><strong>RQ3</strong></td><td>분석과 판단을 별도 에이전트로 분리하고, 판단만 파인튜닝하는 전략이 단일 LLM보다 우수한가?</td><td>AI 1명이 혼자 하는 것보다 <strong>분석+판단 담당</strong>으로 나누고 판단만 훈련시키면 더 잘하는가?</td><td>(a)vs(b)vs(c)</td></tr>
</table>

<h3>1.3 핵심 개념</h3>

<h4>추천 시스템과 Cold-Start 문제</h4>
<p>추천 시스템은 사용자의 과거 행동 데이터(구매, 평점, 리뷰 등)를 분석하여 개인화된 아이템을 제안한다.
그러나 이 접근은 <strong>충분한 데이터가 있을 때만 작동</strong>한다.
새로운 서비스에 가입하거나, 기존 사용자가 새로운 카테고리를 탐색할 때처럼
행동 이력이 부족한 상황에서는 취향을 파악할 수 없어 추천 품질이 크게 저하된다.
이를 <strong>Cold-Start 문제</strong>라 한다.</p>

<div class="callout">
<strong>Cold-Start의 실제 영향</strong><br>
예를 들어, 영화 스트리밍 서비스에서 45편의 영화를 시청하고 상세 리뷰를 남긴 사용자가
전자책 서비스를 새로 시작했다고 하자. 책은 3권만 구매했고, 리뷰는 "재미있었어요" 1건뿐이다.
이 사용자에게 어떤 책을 추천해야 할까? — 책 구매 이력만으로는 취향을 파악할 수 없다.
</div>

<h4>Cross-Domain Recommendation (CDR)</h4>
<p>CDR은 Cold-Start 문제의 해결책 중 하나로, <strong>데이터가 풍부한 도메인(Source)의 정보를
활용하여 데이터가 부족한 도메인(Target)의 추천을 보완</strong>하는 접근법이다.
핵심 가정은 "한 도메인에서의 선호가 다른 도메인의 선호를 예측하는 데 도움이 된다"는 것이다.</p>

<table>
<tr><th>개념</th><th>설명</th><th>본 연구에서</th></tr>
<tr><td><strong>Source 도메인</strong></td><td>사용자 데이터가 풍부한 도메인</td><td>Movies &amp; TV (리뷰 15개 이상)</td></tr>
<tr><td><strong>Target 도메인</strong></td><td>사용자 데이터가 부족한 도메인 (Cold-Start)</td><td>Books (리뷰 5~10개)</td></tr>
<tr><td><strong>전이(Transfer)</strong></td><td>Source에서 추출한 선호 패턴을 Target 추천에 활용</td><td>"SF 장르 선호" → SF 소설 추천</td></tr>
</table>

<h4>Negative Transfer — CDR의 핵심 리스크</h4>
<p>그러나 Source의 모든 정보가 Target에 유용한 것은 아니다.
영화 도메인에서 추출한 선호 중 일부는 책 추천과 <strong>무관하거나 오히려 해로울 수 있다.</strong>
이처럼 Source 정보가 Target 추천 품질을 오히려 저하시키는 현상을 <strong>Negative Transfer</strong>라 한다.</p>

<div class="callout">
<strong>Negative Transfer 예시</strong><br>
✓ "SF 장르 선호" → SF 소설 추천에 유용 (<strong>Positive Transfer</strong>)<br>
△ "영상미 중시" → "묘사력 중시"로 변환하면 활용 가능 (<strong>Partial Transfer</strong>)<br>
✗ "놀란 감독 팬" → 책에는 영화 감독이 없음. 이 패턴을 그대로 전이하면 무관한 책이 추천됨 (<strong>Negative Transfer</strong>)
</div>

<p><strong>TransferJudge의 핵심 아이디어:</strong> 이 문제를 해결하기 위해 본 연구는 Transfer Gate를 도입하여
각 선호 패턴을 TRANSFER / PARTIAL / BLOCK으로 판정하고,
Negative Transfer를 사전에 차단한 뒤 추천을 생성한다.</p>

<table>
<tr><th>컴포넌트</th><th>역할</th><th>구현</th></tr>
<tr><td><strong>Profiler</strong></td><td>Source/Target 리뷰에서 구조화된 선호 패턴 추출</td><td>GPT-4o-mini (프롬프트 기반)</td></tr>
<tr><td><strong>Transfer Judge</strong></td><td>패턴별 전이 가능 여부를 3단계로 판정 + 추천 생성</td><td>Qwen3-14B (QLoRA 파인튜닝)</td></tr>
</table>

<!-- ===== 2. Cold-Start ===== -->
<h2 class="pagebreak">2. Cold-Start 문제와 CDR의 필요성</h2>

<h3>2.0 왜 Cold-Start가 중요한가?</h3>
<p>현대 추천 시스템은 사용자 행동 데이터에 기반하므로, 데이터가 부족한 상황에서는 구조적으로 성능이 저하된다.
Cold-Start는 다음과 같은 실제 시나리오에서 발생한다:</p>
<ul>
<li><strong>신규 사용자</strong>: 서비스에 처음 가입한 사용자는 행동 이력이 없음</li>
<li><strong>도메인 확장</strong>: 기존 사용자가 새로운 카테고리(예: 영화→책)를 탐색할 때</li>
<li><strong>장기 미활동 후 복귀</strong>: 과거 이력이 현재 취향을 반영하지 못함</li>
</ul>
<p>기존 해결 방법(인기 아이템 추천, 인구통계 기반)은 <strong>개인화가 불가능</strong>하다는 한계가 있다.
CDR은 "다른 도메인의 풍부한 데이터"를 활용하여 이 문제를 개인화된 방식으로 해결한다.</p>

<h3>2.1 본 연구의 시나리오</h3>
<div class="callout">
<strong>구체적 시나리오</strong><br>
<strong>Movies &amp; TV</strong>: 45편 시청, 상세 리뷰 (Source — 데이터 풍부).<br>
<strong>Books</strong>: 3권 구매, "재미있었어요" 1건뿐 (Target — Cold-Start).<br><br>
<strong>기존 방식</strong>: 책 3권의 이력만으로 추천 → 취향 파악 불가, 베스트셀러 추천에 그침.<br>
<strong>CDR 방식</strong>: 영화 45편의 리뷰에서 선호 패턴 추출 → 책에 전이 가능한 것만 선별 → <strong>개인화된</strong> 추천.<br>
<strong>TransferJudge</strong>: 여기에 Transfer Gate를 추가하여 전이 불가능한 패턴을 자동 차단 → Negative Transfer 방지.
</div>

<h3>2.2 Cold-Start 기준 정당화: 왜 리뷰 5~10개인가?</h3>
<table>
<tr><th>구간</th><th>리뷰 수</th><th>상태</th><th>처리</th></tr>
<tr><td>Zero-Shot</td><td>0개</td><td>Target 정보 전무 → 전이 효과 측정 불가</td><td>제외</td></tr>
<tr class="highlight-row"><td><strong>Cold-Start</strong></td><td><strong>5~10개</strong></td><td><strong>Target 단독으로는 부족, CDR 효과 검증 가능한 최적 구간</strong></td><td><strong>대상</strong></td></tr>
<tr><td>Warm-Start</td><td>10개 초과</td><td>Target 단독 추천 가능 → CDR 필요성 희석</td><td>제외</td></tr>
</table>
<div class="callout">
<strong>선행연구 기준</strong>: 대부분의 CDR 논문(EMCDR, LLM4CDR 등)은 Target &lt; 20개를 Cold-Start로 정의. 본 연구는 이 범위 내에서 구체화.<br>
<strong>하한(5개)</strong>: 5개 미만이면 Target 선호 파악 불가, 전이 효과 분리 어려움.<br>
<strong>상한(10개)</strong>: 10개 초과 시 Target 단독으로도 충분, Source 전이의 marginal effect 감소.<br>
<strong>Source &gt;= 15개</strong>: Profiler가 의미 있는 패턴을 추출하기 위한 최소 리뷰 수 (Pilot Study에서 검증).
</div>

<!-- ===== 3. 프로세스 플로우차트 ===== -->
<h2 class="pagebreak">3. 전체 프로세스 플로우차트</h2>
<table>
<tr><th>단계</th><th>처리 내용</th><th>결과물</th></tr>
<tr><td>Step 1</td><td>Source/Target 리뷰 수집 및 전처리</td><td>Source 최대 30개 + Target 최대 10개</td></tr>
<tr><td>Step 2</td><td>Profiler가 선호 패턴을 JSON으로 추출</td><td>6~9개 선호 패턴</td></tr>
<tr><td>Step 3</td><td>Transfer Judge가 TRANSFER/PARTIAL/BLOCK 판정</td><td>전이 결정 결과</td></tr>
<tr><td>Step 4</td><td>전이 가능 패턴만으로 Top-10 추천 생성</td><td>추천 리스트 + rationale</td></tr>
</table>

<!-- ===== 4. 데이터셋 ===== -->
<h2>4. 데이터셋 설명 및 구성</h2>

<h3>4.1 데이터 소스</h3>
<p>Amazon Review 2023 (McAuley Lab). 도메인 간 공통 사용자 존재.</p>

<h3>4.2 도메인 구성</h3>
<table>
<tr><th>구분</th><th>Source: Movies &amp; TV</th><th>Target: Books</th></tr>
<tr><td>사용자 조건</td><td>리뷰 15개 이상</td><td>리뷰 5~10개</td></tr>
<tr><td>입력 리뷰 수</td><td>최대 30개 (최신순)</td><td>전체 (최대 10개)</td></tr>
<tr><td>리뷰당 평균 토큰</td><td>~58 tokens/건</td><td>~98 tokens/건</td></tr>
<tr><td>토큰 예산</td><td>30 × 58 = ~1,740 tokens</td><td>10 × 98 = ~980 tokens</td></tr>
</table>

<div class="callout">
<strong>사용자 조건 및 입력 리뷰 수 근거</strong><br><br>
<strong>Source ≥ 15개:</strong> Profiler가 7개 Core Pattern을 안정적으로 추출하기 위한 최소 요건.
EMCDR(IJCAI 2019)은 Source 최소 10개, LLM4CDR(WWW 2025)은 5개 사용. 본 연구는 텍스트 리뷰에서
패턴 다양성 확보를 위해 15개로 상향. Pilot Study에서 15개 미만 시 패턴 누락률 검증 예정.<br><br>
<strong>입력 최대 30개:</strong> Movies &amp; TV 리뷰 평균 ~58 tokens/건(Amazon Reviews 2023 공식 통계 역산:
1.0B tokens ÷ 17.3M ratings). 30개 × 58 = ~1,740 tokens + Target ~980 + 프롬프트 ~500 =
<strong>총 ~3,220 tokens</strong>으로 GPT-4o-mini context 내 충분. 30개 이상은 새 패턴 발견 확률이 감소(수확 체감).<br><br>
<strong>토큰 통계 출처:</strong> Amazon Reviews 2023 공식 페이지 전체 통계 역산;
arXiv 2503.07761(CDR + LLM)의 카테고리별 리뷰 길이 보고(Movies &amp; TV 평균 38.18 words ≈ 50 tokens).
<strong>EDA에서 실제 P95 토큰 분포 확인 후 입력 수 조정 예정.</strong>
</div>

<h3>4.3 실험 데이터 규모</h3>
<ul>
<li>Overlapping User 1,000명 / Train 800 / Val 100 / Test 100</li>
<li>후보 아이템: 사용자당 50개 (GT 1 + Negative 49)</li>
</ul>
<div class="callout">
<strong>데이터 규모 근거</strong><br>
<strong>1,000명</strong>: TALLRec ~600명, LLM4CDR ~1,000명 수준. API 비용 ~$5 내 현실적 규모.<br>
<strong>8:1:1 분할</strong>: 추천 시스템 연구 표준 비율. Test 100명에서 Bootstrap CI로 95% 신뢰구간 확보 가능.
</div>

<h3>4.4 선행연구 데이터 구성 비교</h3>
<table style="font-size: 0.85em">
<tr><th>항목</th><th>TALLRec<br>(RecSys 2023)</th><th>LLM4CDR<br>(WWW 2025)</th><th>EMCDR<br>(IJCAI 2017)</th><th>TrineCDR<br>(KDD 2024)</th><th><strong>본 연구</strong></th></tr>
<tr><td><strong>데이터셋</strong></td><td>MovieLens + Amazon</td><td>Amazon 2018<br>(5-core)</td><td>Amazon<br>(5-core)</td><td>Amazon + Douban</td><td><strong>Amazon 2023</strong></td></tr>
<tr><td><strong>사용자 필터</strong></td><td>Few-shot<br>(16~256건)</td><td>Rating=5.0<br>구매>20</td><td>5-core</td><td>10-core</td><td><strong>Source≥15<br>Target 5~10</strong></td></tr>
<tr><td><strong>날짜 필터</strong></td><td>없음</td><td>없음</td><td>없음</td><td>없음</td><td><strong>없음</strong><br>(EDA 보고)</td></tr>
<tr><td><strong>리뷰 텍스트</strong></td><td>미사용</td><td>미사용</td><td>미사용</td><td>미사용</td><td><strong>사용 (핵심 입력)</strong></td></tr>
<tr><td><strong>후보 수</strong></td><td>없음 (binary)</td><td>20개</td><td>없음 (RMSE)</td><td>100개</td><td><strong>50개</strong></td></tr>
<tr class="highlight-row"><td><strong>GT 방식</strong></td><td>Implicit</td><td>5점만</td><td>Implicit</td><td>Implicit</td><td><strong>Explicit (≥4)</strong></td></tr>
</table>
<div class="callout">
<strong>리뷰 텍스트 활용:</strong> 조사한 CDR 선행연구 4편 모두 리뷰 텍스트를 사용하지 않고 평점/상호작용만 활용.
본 연구는 리뷰 텍스트에서 선호 패턴을 추출하는 최초의 LLM 기반 CDR 프레임워크로, 이것이 핵심 차별점이다.<br>
<strong>날짜 필터:</strong> 선행연구 4편 모두 시간 필터 미적용. 본 연구도 동일하되, EDA에서 시점 분포를 보고하여 타당성 문서화.
</div>

<h3>4.5 Ground Truth 선정 및 근거</h3>

<p><strong>GT 선정:</strong> 각 사용자의 Books 도메인에서 <strong>rating ≥ 4인 구매 중 가장 최근 아이템</strong> 1개</p>

<table>
<tr><th>논문</th><th>GT 방식</th><th>평점 처리</th></tr>
<tr><td>NCF (He et al., WWW 2017)</td><td>마지막 상호작용</td><td>모든 평점 → implicit(1) 변환</td></tr>
<tr><td>TALLRec (RecSys 2023)</td><td>마지막 상호작용</td><td>4점 이상=Yes, 미만=No</td></tr>
<tr><td>LLM4CDR (WWW 2025)</td><td>마지막 상호작용</td><td>5점만 남기고 전처리</td></tr>
<tr><td>TrineCDR (KDD 2024)</td><td>마지막 상호작용</td><td>implicit 변환</td></tr>
<tr class="highlight-row"><td><strong>본 연구</strong></td><td><strong>4점 이상 중 가장 최근</strong></td><td><strong>Explicit positive (≥4)</strong></td></tr>
</table>

<div class="callout">
<strong>왜 Implicit이 아닌 Explicit Positive인가?</strong><br><br>
Transfer Gate는 Negative Transfer를 방지하여 <strong>사용자가 만족할 아이템</strong>을 추천하는 것이 목표이다.
Implicit 방식(구매=positive)에서는 2점짜리 GT를 "맞혀야 할 정답"으로 취급하게 되어,
Transfer Gate가 올바르게 BLOCK한 판단이 오히려 <strong>성능 하락</strong>으로 측정되는 문제가 발생한다.<br><br>
<strong>연구 목적 정합성:</strong> Transfer Gate → "좋은 추천" 필터링 → GT도 "만족한 아이템"이어야 효과 정확 측정<br>
<strong>Negative Transfer 증명:</strong> GT가 positive여야 "TRANSFER해서 맞힌 것" vs "BLOCK해서 놓친 것" 구분 가능<br>
<strong>LLM4CDR 비교:</strong> LLM4CDR은 5점만 사용 — 본 연구는 4점 이상으로 더 현실적<br>
<strong>입력 리뷰:</strong> Profiler 입력은 1~5점 전체 사용 (낮은 평점도 "무엇을 싫어하는지" 패턴 추출에 기여)
</div>

<h4>한눈에 보는 Implicit vs Explicit Positive</h4>

<table>
<tr><th style="width:18%">방식</th><th style="width:30%">정답(GT)으로 인정하는 기준</th><th>비유</th></tr>
<tr><td><strong>Implicit</strong> (구매=positive)</td><td>"구매했다" → 무조건 좋아한 것으로 간주<br>(평점 1점도 정답으로 취급)</td><td>장바구니에 담은 모든 책을 "이 사람이 좋아하는 책"이라고 가정. 환불·후회한 책도 포함됨.</td></tr>
<tr class="highlight-row"><td><strong>Explicit Positive</strong> ★ <br>(rating ≥ 4)</td><td>"4점 이상 평점을 줬다" → 명시적으로 만족한 것만 정답</td><td>실제로 별점 4~5점을 준 책만 "정말 좋아한 책"으로 인정. 후회한 구매는 제외.</td></tr>
</table>

<table>
<tr><th>구체 시나리오</th><th>Implicit이라면</th><th>Explicit Positive라면</th></tr>
<tr><td>사용자가 영화 "놀란 감독 팬"이라 책 분야에서도 "놀란 자서전(2점)"을 구매<br><em>(Negative Transfer 사례)</em></td><td>"놀란 자서전 = 정답"<br>→ Transfer Gate가 brand_loyalty를 BLOCK해서 추천 안 함<br>→ <span class="tag-block">성능 하락</span>으로 측정<br>→ Gate의 올바른 판단이 <strong>왜곡 평가</strong></td><td>"놀란 자서전(2점) = 정답 아님"<br>→ Gate가 올바르게 BLOCK<br>→ <span class="tag-transfer">Gate 효과 정확 반영</span></td></tr>
<tr><td>사용자가 "복잡한 서사 선호" 패턴이 있고 "Cloud Atlas(5점)"를 구매</td><td>"Cloud Atlas = 정답"<br>→ TRANSFER로 추천 시 점수 ↑<br>→ 정상 측정</td><td>"Cloud Atlas = 정답"<br>→ TRANSFER로 추천 시 점수 ↑<br>→ 정상 측정</td></tr>
</table>

<div class="callout-warn">
<strong>핵심 정리:</strong> Implicit 방식에서는 "사용자가 후회한 구매(낮은 평점)"까지 정답 취급하므로,
Transfer Gate가 그것을 BLOCK한 <strong>올바른 판정</strong>이 평가에서 "맞히지 못한 것"으로 잘못 측정된다.
Explicit Positive는 "사용자가 진짜 만족한 것"만 정답으로 두어, BLOCK의 가치를 정확히 측정 가능하게 한다.<br><br>
즉, <strong>본 연구의 핵심 가설(Transfer Gate가 부정 전이를 막아 추천 품질을 높인다)을 검증하려면 GT가 Explicit Positive여야 한다.</strong>
</div>

<h3>4.5 후보 50개 선정 방법</h3>
<p><strong>선정 절차:</strong></p>
<ol>
<li>사용자의 Books 도메인에서 rating ≥ 4인 구매 중 <strong>가장 최근 아이템</strong>을 GT로 설정</li>
<li>해당 사용자가 구매하지 않은 Books 도메인 아이템 중 49개를 균일 랜덤 샘플링</li>
<li>GT 1개 + Negative 49개 = 50개를 섞어 후보 리스트 구성</li>
<li>후보 아이템 정보: 제목 + 저자 + 카테고리 + 평균 평점을 텍스트로 제공</li>
</ol>

<table>
<tr><th>근거</th><th>설명</th></tr>
<tr><td><strong>선행연구 표준</strong></td><td>LLM4CDR(WWW 2025)은 후보 20개, He et al.(WWW 2017)은 100개 사용. 50개는 LLM 토큰 한도 내에서 충분한 난이도를 제공</td></tr>
<tr><td><strong>LLM 토큰 제약</strong></td><td>후보 1개당 ~50 tokens × 50개 = ~2,500 tokens. Profiler Output ~800 + 시스템 프롬프트 ~500 = 총 ~3,800 tokens으로 4,096 시퀀스 길이 내 수용</td></tr>
<tr><td><strong>랜덤 확률 보정</strong></td><td>후보 50개 중 랜덤 추천 시 HR@1 기대값 = 2%, HR@10 기대값 = 20% → 실질적 성능 측정에 적절한 난이도</td></tr>
<tr><td><strong>균일 랜덤 샘플링</strong></td><td>TALLRec, LLM4CDR 등 선행연구와 동일한 프로토콜로 결과 비교 공정. 랜덤 시드 고정(seed=42)으로 모든 Ablation 조건이 동일 후보 셋 공유</td></tr>
</table>

<!-- ===== 5. 에이전트별 설정 ===== -->
<h2 class="pagebreak">5. 컴포넌트별 Input / Output 및 LLM 선정 근거</h2>

<h3>5.1 Profiler (GPT-4o-mini)</h3>
<table>
<tr><th style="width:80px">구분</th><th>상세 내용</th></tr>
<tr><td><strong>LLM</strong></td><td>GPT-4o-mini API (프롬프트 기반, 파인튜닝 없음)</td></tr>
<tr><td><strong>Input</strong></td><td>Source 리뷰 최대 30개(~1,740 tokens) + Target 리뷰 전체(~980 tokens) + 프롬프트(~500) ≈ ~3,220 tokens</td></tr>
<tr><td><strong>Output</strong></td><td>JSON: 5~8개 선호 패턴 (~800 tokens)</td></tr>
</table>
<div class="callout">
<strong>왜 GPT-4o-mini인가?</strong><br>
<strong>태스크</strong>: 텍스트 분석(Analytical) — 범용 LLM 능력 범위 내, 파인튜닝 불필요.<br>
<strong>API 효율</strong>: 파인튜닝 불필요 → API 호출이 인프라 없이 최적. $0.15/1M tokens, 1,000명 ~$1~2.<br>
<strong>재현성</strong>: 상용 API는 동일 프롬프트에 일관된 출력 보장.
</div>

<h3>5.2 Transfer Judge (Qwen3-14B, QLoRA)</h3>
<table>
<tr><th style="width:80px">구분</th><th>상세 내용</th></tr>
<tr><td><strong>LLM</strong></td><td>Qwen3-14B-Instruct (QLoRA 파인튜닝)</td></tr>
<tr><td><strong>Input</strong></td><td>Profiler Output + 후보 50개 (~3,800 tokens)</td></tr>
<tr><td><strong>Output</strong></td><td>transfer_decisions + recommendations Top-10 (~1,500 tokens)</td></tr>
</table>
<div class="callout">
<strong>왜 Qwen3-14B-Instruct인가?</strong><br>
<strong>오픈소스 필수</strong>: QLoRA를 위해 가중치 접근 필요 → GPT 계열 사용 불가.<br>
<strong>Instruct 완료</strong>: JSON 출력 + 복잡한 지시문 이해 필요 → Instruct 모델이어야 추가 FT 효율적.<br>
<strong>벤치마크 최상위</strong>: 14B급 오픈소스 중 MMLU 81.05, MMLU-Pro 61.03, BBH 81.07 (Qwen3 Technical Report, 2025).<br>
<strong>복잡 추론 능력</strong>: MMLU-Pro 61.03 — TRANSFER/PARTIAL/BLOCK 3단계 판정에 요구되는 복잡 추론에 직접적 이점.<br>
<strong>대안 비교</strong>: LLaMA-3는 8B→70B 점프로 14B급 비교 불가. Gemma-3-12B는 MMLU-Pro 44.91로 열위.
</div>

<!-- ===== 6. Core Patterns ===== -->
<h2 class="pagebreak">6. Profiler가 추출하는 선호 패턴 정의</h2>

<h3>6.1 반정형(Semi-Structured) 접근</h3>
<p>7개 Core Pattern 필수 분석 + 추가 패턴 자유 추출.</p>

<h3>6.2 Core Patterns (Pilot Study 검증 결과)</h3>
<table>
<tr><th>Pattern</th><th>설명</th><th>예시</th><th>Transfer Gate</th><th>Pilot sim</th></tr>
<tr><td>genre_preference</td><td>선호 장르</td><td>"Sci-Fi, Thriller"</td><td><span class="tag-transfer">TRANSFER</span></td><td>0.70</td></tr>
<tr><td>narrative_complexity</td><td>서사 복잡도</td><td>"Multi-layered, nonlinear"</td><td><span class="tag-transfer">TRANSFER</span></td><td>0.80 (직접)</td></tr>
<tr><td>pacing_preference</td><td>전개 속도</td><td>"Fast-paced"</td><td><span class="tag-transfer">TRANSFER</span></td><td>0.81</td></tr>
<tr><td>quality_sensitivity</td><td>품질 민감도</td><td>"Highly critical"</td><td><span class="tag-partial">PARTIAL</span></td><td>0.55</td></tr>
<tr><td>brand_loyalty</td><td>브랜드 충성도</td><td>"Nolan fan"</td><td><span class="tag-block">BLOCK 후보</span></td><td>0.70</td></tr>
<tr><td>sensory_preference</td><td>감각적 경험</td><td>"Values cinematography"</td><td><span class="tag-block">BLOCK 후보</span></td><td>0.59</td></tr>
<tr><td><strong>emotional_resonance</strong> ★</td><td>감정적 울림</td><td>"Stayed with me for days"</td><td><span class="tag-transfer">TRANSFER</span></td><td>0.82 (직접)</td></tr>
</table>
<p style="font-size: 9pt; color: #666;">★ = Pilot Study에서 emerge한 패턴 (14% 빈도, 직접 매칭)</p>

<h3>6.3 패턴 선정 근거: Pilot Study (실행 완료, 2026-04)</h3>

<table>
<tr><th>항목</th><th>값</th></tr>
<tr><td>샘플 규모</td><td>100명 (Train 800 中, seed=42)</td></tr>
<tr><td>비용</td><td>$0.081 (GPT-4o-mini)</td></tr>
<tr><td>이론 anchor</td><td>Thet et al. (2010) 영화 리뷰 aspect mining + Liu (2012) ABSA</td></tr>
<tr><td>검토 측면</td><td>이론 정합성 · Pilot 발현 · Cross-Domain 적합성 · 직교성 (4가지 종합)</td></tr>
<tr><td>사전 검토 결과</td><td>5/5 통과 (7/7 패턴 sim ≥ 0.5, 직교성 max 0.669 ≤ 0.7, BLOCK 후보 자동 식별)</td></tr>
<tr><td>자유 추출 한계</td><td>391 canonical 中 90.8%가 비-CDR-적합 → 명시 prompt 설계 데이터 정당화</td></tr>
<tr><td>채택 결정</td><td>7/7 ACCEPT (REJECT 0): 4 일반 + 1 조건부 + 1 BLOCK 후보 + 1 보완 필요</td></tr>
</table>

<div class="callout">
<strong>자기참조 회피 메커니즘</strong><br>
패턴 정의는 <strong>외부 학술(Thet 2010, Liu 2012)</strong>에서 도출, 검증은 <strong>본 연구가 직접 매칭하지 않고</strong>
sentence-transformers cosine similarity 자동 매칭이 수행. 사전 검토 5항목을 Pilot 결과 분석 전에 정해두어 짜맞춤을 방지.
</div>

<div class="callout">
<strong>관련 산출 문서</strong><br>
· <code>docs/Pilot_Study_Report.md</code> — Pilot Study 보고서 (전체 결과)<br>
· <code>docs/TransferJudge_Pilot_Report_v3.pdf</code> — 시각화된 Pilot 보고서 (9p, 본인 검토용)<br>
· <code>prompts/core_patterns_definition.md</code> — 7개 패턴 정의서 + 5단계 선정 절차
</div>

<h3>6.4 Profiler Input / Output 예시</h3>

<p><strong>Input (Source 리뷰 — 최신순 15~30개 발췌):</strong></p>
<pre>[Review 1] Rating: 5/5 | "Another brilliant Nolan epic, the time-loop structure was genius"
   ↑                ↑                    ↑                              ↑
   리뷰 번호    별점(5점=강한 긍정)   감독 충성도 신호           복잡한 서사 선호 신호

[Review 2] Rating: 5/5 | "Cinematography alone makes this a masterpiece"
                                  ↑
                          영상미 중시 → sensory_preference 신호 (영화 매체 한정)

[Review 3] Rating: 2/5 | "Generic rom-com, predictable and boring"
                ↑                ↑                   ↑
            낮은 점수도 사용 (싫어하는 장르 신호)  rom-com 비선호    단순한 서사 비선호

[Review 4] Rating: 4/5 | "Slow-burn but rewarding character study"
                                  ↑
                          느린 전개 선호 → pacing_preference 신호

... (총 15~30개, 토큰 예산 ~2,400 tokens)</pre>

<div class="callout">
<strong>Input 핵심 포인트:</strong>
<ul>
<li><strong>최신순 정렬</strong> — 최근 취향이 더 정확. Review 1이 가장 최근.</li>
<li><strong>전체 평점 사용 (1~5점)</strong> — 낮은 평점도 "싫어하는 것"의 정보. GT만 4점 이상 제한.</li>
<li><strong>제목 + 본문 모두 포함</strong> — 짧은 제목에도 강한 감정 신호 ("masterpiece", "boring") 존재.</li>
</ul>
</div>

<p><strong>Output (Profiler가 추출한 JSON 일부):</strong></p>
<pre>{
  "core_patterns": {
    "narrative_complexity": {                          // ← 7개 패턴 중 하나
      "value": "Strongly prefers complex, multi-layered narratives",
      "evidence": ["Review 1: 'time-loop structure was genius'"],
                  // ↑ 원문 인용 — 패턴이 데이터에 근거함을 증명 (hallucination 방지)
      "confidence": 0.85,                              // ← 0~1, 값이 클수록 강한 신호
      "polarity": "positive",                          // ← 좋아함/싫어함/혼합
      "transferability_hint": "high"                   // ← Books 도메인으로 전이 쉬움 힌트
    },
    "brand_loyalty": {
      "value": "Strong loyalty to Christopher Nolan",
      "confidence": 0.80,
      "polarity": "positive",
      "transferability_hint": "low"                    // ← ★ 영화감독은 책에 매핑 어려움
                                                       //   → Judge에게 "BLOCK 후보" 신호
    }
    // genre_preference, pacing_preference, quality_sensitivity, sensory_preference, emotional_resonance ...
    // (총 7개 Core + 추가 패턴 최대 3개)
  },
  "summary": "Sophisticated viewer preferring complex, slow-burn narratives..."
                  // ↑ 사람이 한눈에 이해 가능한 2~3문장 요약 (Judge의 추가 컨텍스트)
}</pre>

<div class="callout">
<strong>Output 핵심 포인트:</strong>
<ul>
<li><strong>evidence (원문 인용)</strong>: Profiler가 "왜 이 패턴이라 판단했는지" 증거. Judge·심사위원 검증 가능.</li>
<li><strong>confidence (신뢰도 0~1)</strong>: 약한 신호 패턴은 Judge가 필터링하거나 비중 낮춤.</li>
<li><strong>polarity (극성)</strong>: positive(선호) / negative(비선호) / mixed. "싫어하는 장르"도 추천 회피에 활용.</li>
<li><strong>transferability_hint</strong>: Profiler가 주는 초기 힌트일 뿐, <strong>최종 TRANSFER/PARTIAL/BLOCK 판정은 Judge가 결정</strong>.</li>
</ul>
</div>

<!-- ===== 7. Transfer Judge 필요한 이유 ===== -->
<h2>7. Transfer Judge가 필요한 이유</h2>
<div class="callout-warn">
✔ <span class="tag-transfer">genre_preference</span>: "SF, Thriller" → 그대로 전이 가능.<br>
△ <span class="tag-partial">sensory_preference</span>: "영상미 중시" → "묘사력 중시"로 변환 가능.<br>
✘ <span class="tag-block">brand_loyalty</span>: "놀란 감독 팬" → 전이 불가. 차단 필요.
</div>
<p><strong>왜 분리?</strong> 패턴 추출(Analytical)과 전이 판단(Judgmental)은 인지적으로 다른 태스크. 두 역할을 분리하면 각 LLM이 자신의 태스크에 특화되어 품질이 향상된다.</p>

<h3>7.1 Transfer Judge Input / Output 예시</h3>

<p><strong>Input (Profiler Output + 후보 50개 일부):</strong></p>
<pre>{
  "user_profile": { "core_patterns": { ...섹션 6.4의 Profiler 출력 그대로... } },
  // ↑ Profiler가 추출한 7개 패턴 JSON을 통째로 입력 (구조화된 사용자 프로파일)

  "candidates": [
    {"id": "B002", "title": "Cloud Atlas", "author": "David Mitchell",
     "categories": "Literary Fiction", "rating": 4.0,
     "synopsis": "Six nested timelines spanning centuries..."},
    // ↑ 후보 1개 정보: 제목 + 저자 + 카테고리 + 평균평점 + 줄거리 첫 50 토큰
    //   Judge가 패턴 매칭 판단할 수 있도록 충분한 정보 제공

    {"id": "B045", "title": "Nolan biography", "author": "T. Shone",
     "categories": "Biography", "rating": 4.2, "synopsis": "..."},
    // ↑ ★ 함정 케이스: "Nolan"이라는 이름이 들어 있지만 저자는 다름
    //   사용자가 영화감독 Nolan의 팬이라고 해서 이 책을 추천하면 Negative Transfer

    ... (총 50개: GT 1개 + 사용자가 구매하지 않은 Books 무작위 49개 shuffle)
  ]
}</pre>

<div class="callout">
<strong>Input 핵심 포인트:</strong>
<ul>
<li><strong>Profiler 출력을 그대로 입력</strong> — 두 LLM이 JSON 스키마를 공유하여 정보 손실 없음.</li>
<li><strong>후보당 5개 필드</strong> — 제목·저자·카테고리·평점·줄거리. Judge의 패턴별 매칭 근거.</li>
<li><strong>shuffle 후 입력</strong> — GT 위치 노출 방지 (LOO 평가 시에도 동일).</li>
</ul>
</div>

<p><strong>Output (transfer_decisions + Top-10):</strong></p>
<pre>{
  "transfer_decisions": {
    "narrative_complexity": {"decision": "<span class="tag-transfer">TRANSFER</span>",
                                          // ↑ 패턴이 책에도 그대로 적용 가능
       "rationale": "Multi-layered storytelling is medium-agnostic.",
                  // ↑ 왜 TRANSFER인지 설명 (Chain-of-Thought 학습용)
       "confidence": 0.90},

    "brand_loyalty": {"decision": "<span class="tag-block">BLOCK</span>",
                                  // ↑ ★ 핵심 — 영화감독 충성도는 책에 전이 불가
       "rationale": "Nolan is a film director, not an author.",
                  // ↑ "Nolan biography"를 추천에서 제외할 이유
       "confidence": 0.95},

    "sensory_preference": {"decision": "<span class="tag-block">BLOCK</span>",
       "rationale": "IMAX cinematography is film-specific.",
                  // ↑ 영상미는 책에 존재하지 않음 → 매체 특화 패턴
       "confidence": 0.95},

    "emotional_resonance": {"decision": "<span class="tag-transfer">TRANSFER</span>",
       "rationale": "Emotional impact is medium-agnostic, applies to literary fiction.",
                  // ↑ 감정적 울림은 책에도 그대로 적용 (Pilot 도출 패턴)
       "confidence": 0.85}
    // genre_preference: PARTIAL (장르 매핑 필요), pacing_preference: TRANSFER (페이싱은 책에도 존재) ...
  },

  "recommendations": [
    {"rank": 1, "item_id": "B002", "title": "Cloud Atlas", "score": 0.92,
                              // ↑ 후보 50개 중 1위로 추천 (점수 0~1)
     "applied_patterns": ["narrative_complexity", "pacing_preference"],
     // ↑ ★ 이 책을 추천한 근거 패턴들 — BLOCK 패턴은 절대 들어가지 않음
     //   (만약 brand_loyalty가 여기 있으면 학습 데이터에서 자동 배제: 섹션 9 5단계 필터)

     "reasoning": "Six nested timelines match preference for complex narratives."}
                // ↑ 사람이 읽을 수 있는 추천 근거 (rationale의 추천 버전)

    // rank 2~10 (총 10개 추천)
    // 주의: "Nolan biography(B045)"는 평점 4.2로 높지만 BLOCK 판정으로 Top-10 진입 못함
  ]
}</pre>

<div class="callout">
<strong>Output 핵심 포인트 — 왜 이게 Transfer Gate의 가치인가?</strong>
<ul>
<li><strong>"Nolan biography"는 평점 4.2 (높음)</strong>이지만 BLOCK 판정으로 추천에서 <strong>자동 제외</strong>.</li>
<li>단순 평점·인기도 기반 추천이라면 이 책이 추천될 가능성이 있음 → Negative Transfer 발생.</li>
<li>Transfer Judge는 사용자의 "Nolan 충성도"가 <strong>영화 한정</strong>임을 인식하고 책에는 적용 안 함.</li>
<li>이것이 본 연구의 핵심 가설: <strong>BLOCK이 추천 품질을 높인다</strong>.</li>
</ul>
<strong>학습 데이터 품질 자동 검증:</strong> <code>applied_patterns</code>에 BLOCK된 패턴이 들어가면 학습 데이터에서 자동 배제 (섹션 9.4의 5단계 필터 中 ③).
</div>

<!-- ===== 8. Transfer Gate ===== -->
<h2 class="pagebreak">8. Transfer Gate: 전이 판정 3단계 정의</h2>
<table>
<tr><th>판정</th><th>정의</th><th>예시</th></tr>
<tr><td><span class="tag-transfer">TRANSFER</span></td><td>양쪽 도메인에 공통 존재. 변환 없이 적용.</td><td>"SF 장르 선호"</td></tr>
<tr><td><span class="tag-partial">PARTIAL</span></td><td>의미적 변환으로 활용 가능.</td><td>"영상미" → "묘사력"</td></tr>
<tr><td><span class="tag-block">BLOCK</span></td><td>대응 개념 없음. 완전 배제.</td><td>"놀란 감독 팬"</td></tr>
</table>

<h3>왜 3단계인가? — 선행연구 근거</h3>
<p>기존 연구에서 negative transfer의 원인과 강도가 다층적임은 이미 인식되어 왔다 (Zhang et al. 2023; TrineCDR 2024). 그러나 이를 실제 전이 판정에 반영하여 이산적 multi-level decision으로 구현한 연구는 본 연구가 최초이다.</p>

<table>
<tr><th>논문</th><th>학회</th><th>관련성</th></tr>
<tr><td>Zhang &amp; Wu, "Survey on NT"</td><td>IEEE/CAA JAS 2023</td><td>NT 완화 접근을 Domain/Instance/Feature <strong>3단계</strong>로 분류 — 이론적 근거</td></tr>
<tr><td>TrineCDR</td><td>KDD 2024</td><td>NT 원인을 Feature/Interaction/Domain <strong>3 level</strong>로 분류 — 직접적 동기</td></tr>
<tr><td>Wang et al.</td><td>CVPR 2019</td><td>NT의 <strong>3가지 요인</strong> 식별 + gate 기반 filtering — 방법론적 선례</td></tr>
<tr><td>SAN (Cao et al.)</td><td>CVPR 2018</td><td>Binary selective transfer — PARTIAL 확장 필요성의 근거</td></tr>
<tr><td>FedGCDR</td><td>NeurIPS 2024</td><td>Soft/Hard NT 구분 — NT 강도 차이 근거</td></tr>
<tr><td>Park et al.</td><td>CIKM 2023</td><td>Shapley 연속 가중치 — 이산 판정 발전 선례</td></tr>
</table>

<div class="callout-red">
<strong>핵심 설계 원칙</strong>: Transfer Judge의 추천 rationale에는 BLOCK 판정된 패턴이 절대 등장해서는 안 된다.
</div>

<!-- ===== 9. Teacher Distillation ===== -->
<h2 class="pagebreak">9. Teacher Distillation: 학습 데이터 생성</h2>

<h3>9.1 왜 Teacher Distillation인가?</h3>
<p>Transfer Gate의 3단계 판정은 본 연구가 새롭게 정의한 태스크이므로, 기존에 레이블링된 데이터셋이 존재하지 않는다.</p>

<table>
<tr><th>대안</th><th>장점</th><th>한계</th><th>적합성</th></tr>
<tr><td><strong>(A) 수동 레이블링</strong></td><td>정확도 최고</td><td>800건 × 6~9패턴 = 5,000건+ 판정 필요, 비현실적 비용</td><td>✗</td></tr>
<tr class="highlight-row"><td><strong>(B) Teacher Distillation</strong></td><td>비용 효율적, 일관성 높음</td><td>Teacher 품질에 의존</td><td><strong>✓ 채택</strong></td></tr>
<tr><td><strong>(C) Self-Training</strong></td><td>Teacher 불필요</td><td>초기 품질 매우 낮음, 수렴 불안정</td><td>✗</td></tr>
</table>

<h3>9.2 선행연구 근거</h3>
<div class="callout">
<strong>Knowledge Distillation</strong>: 대형 Teacher LLM이 생성한 합성 데이터로 소형 Student 모델을 학습시키는 것은 NLP에서 확립된 방법론 (Hinton et al. 2015).<br>
<strong>TALLRec (RecSys 2023)</strong>: 50건 미만의 학습 데이터만으로도 추천 능력 달성 보고 → 본 연구의 700건은 충분한 규모.<br>
<strong>Chain-of-Thought Distillation</strong>: Teacher가 rationale을 포함한 출력을 생성하고 Student가 학습하면, 단순 레이블만 학습하는 것보다 일반화 성능 향상 (Wei et al. 2022).
</div>

<h3>9.3 Teacher에게 GT를 제공하는 이유</h3>
<div class="callout-warn">
GT를 제공하는 것은 <strong>정답 암기가 아니라 올바른 판정 과정(rationale) 시연을 위함</strong>이다. GT를 알려주면 Teacher는 "이 아이템이 추천되어야 하는 이유"를 역추론하여, 어떤 패턴이 TRANSFER이고 어떤 것이 BLOCK인지를 일관성 있게 판정할 수 있다. Student는 <strong>과정(process)</strong>을 학습하며, 추론 시에는 GT 없이 수행된다.
</div>

<h3>9.4 품질 필터링 (4단계)</h3>
<table>
<tr><th>단계</th><th>검증 항목</th><th>기준</th></tr>
<tr><td>1. 형식 검증</td><td>JSON 파싱 성공 여부</td><td>파싱 실패 시 재시도 (최대 3회)</td></tr>
<tr><td>2. 완전성 검증</td><td>transfer_decisions에 모든 패턴 판정 포함</td><td>누락 시 제외</td></tr>
<tr><td>3. 정확성 검증</td><td>GT가 Top-10 내 포함</td><td>미포함 시 Teacher 판정 실패로 제외</td></tr>
<tr><td>4. BLOCK 누출 검사</td><td>rationale에 BLOCK 판정 패턴 미등장</td><td>누출 시 핵심 설계 원칙 위반으로 제외</td></tr>
</table>
<p><strong>일관성 검사</strong>: Pilot 10명 대상 Teacher를 2회 실행(temperature=0)하여 판정 일치율 확인 (90% 이상 시 진행).</p>
<p><strong>필터링 통과율 목표</strong>: 80% 이상 (800명 → 700건 이상 확보).</p>

<h3>9.5 학습 데이터 구축 프로세스 — 가상 사용자 A를 따라가며 이해하기</h3>

<p>아래 다이어그램은 <strong>Train 사용자 1명("사용자 A")</strong>의 데이터가 어떻게 학습 데이터 1건으로 만들어지는지
실제 데이터 흐름을 단계별로 추적한다. 이 과정을 800명 모두에 반복하여 ~700건의 train.jsonl을 구축한다.</p>

<div class="flow-wrap">
<!-- ============== STEP 0: 시작 ============== -->
<div class="flow-row">
  <div class="flow-box flow-box-data" style="flex: 1; text-align: left; padding: 10px 14px;">
    <div class="flow-box-title">👤 가상 사용자 A — Train 800명 中 1명</div>
    <div class="flow-box-sub" style="margin-top: 4px;">
      <strong>Movies&amp;TV 리뷰 22개</strong> (다양한 평점):<br>
      &nbsp;&nbsp;Review 1 (5점, 최근): "Another brilliant Nolan epic..."<br>
      &nbsp;&nbsp;Review 2 (5점): "Cinematography alone makes this a masterpiece"<br>
      &nbsp;&nbsp;... (총 22개)<br>
      <strong>Books 리뷰 6개</strong>:<br>
      &nbsp;&nbsp;2019: "Foundation" rating 3<br>
      &nbsp;&nbsp;2020: "Dune" rating 4<br>
      &nbsp;&nbsp;<strong>2023: "Cloud Atlas" rating 5 ← ★ 가장 최근 4점 이상</strong><br>
      &nbsp;&nbsp;... (총 6개)
    </div>
  </div>
</div>

<div style="text-align:center; color:#2d3e8a; font-size:14pt;">↓</div>

<!-- ============== STEP 1: GT 분리 ============== -->
<div class="flow-row">
  <div class="flow-box flow-box-data" style="flex: 1; text-align: left; padding: 10px 14px;">
    <div class="flow-box-title">① GT 분리 (Books 리뷰에서 정답 1건 추출)</div>
    <div class="flow-box-sub" style="margin-top: 4px;">
      <strong>규칙:</strong> rating ≥ 4 중 가장 최근 1건 → <strong>"Cloud Atlas" (B002)</strong> 선정<br>
      <strong>왜:</strong> Teacher의 판정 품질을 검증할 정답으로 사용. "이 책이 Top-10에 들어가야 학습 데이터로 인정"이라는 기준이 됨<br>
      <strong>저장:</strong> 다음 단계의 input/output에서 별도 변수로 보관
    </div>
  </div>
</div>

<div style="text-align:center; color:#2d3e8a; font-size:14pt;">↓</div>

<!-- ============== STEP 2: 후보 50개 구성 ============== -->
<div class="flow-row">
  <div class="flow-box flow-box-data" style="flex: 1; text-align: left; padding: 10px 14px;">
    <div class="flow-box-title">② 후보 50개 구성</div>
    <div class="flow-box-sub" style="margin-top: 4px;">
      <strong>구성:</strong> GT "Cloud Atlas" 1개 + 사용자 A가 구매하지 않은 Books 49개 무작위 샘플 = 50개<br>
      <strong>shuffle 결과 (예):</strong> [B045 Nolan biography, B002 Cloud Atlas, B091 Foundation, ...]<br>
      <strong>왜 50개:</strong> 너무 적으면 천장 효과, 너무 많으면 토큰 초과 (섹션 4.5 근거)<br>
      <strong>왜 shuffle:</strong> Teacher가 위치 단서로 GT를 찾지 못하게
    </div>
  </div>
</div>

<div style="text-align:center; color:#2d3e8a; font-size:14pt;">↓</div>

<!-- ============== STEP 3: Profiler ============== -->
<div class="flow-row">
  <div class="flow-box flow-box-api" style="flex: 1; text-align: left; padding: 10px 14px;">
    <div class="flow-box-title">③ Profiler 실행 (GPT-4o-mini API)</div>
    <div class="flow-box-sub" style="margin-top: 4px;">
      <strong>입력:</strong> Movies&amp;TV 리뷰 22개 텍스트 전체 (Books 리뷰는 ❌ 제외 — Cold-Start 시뮬레이션)<br>
      <strong>출력 (요약):</strong>
      <pre style="margin: 4px 0; padding: 6px 8px; font-size: 8.5pt;">{
  "narrative_complexity": {value: "complex multi-layered", confidence: 0.85},
  "brand_loyalty":        {value: "Christopher Nolan",      confidence: 0.80},
  "sensory_preference":   {value: "IMAX cinematography",    confidence: 0.70},
  "emotional_resonance":  {value: "deep lasting impact",    confidence: 0.75},
  // genre_preference, pacing_preference, quality_sensitivity ...
}</pre>
      <strong>왜:</strong> Source 리뷰의 다양한 신호를 7개 구조화 패턴으로 추출 → Judge가 후보별 판단할 근거
    </div>
  </div>
</div>

<div style="text-align:center; color:#2d3e8a; font-size:14pt;">↓</div>

<!-- ============== STEP 4: Teacher ============== -->
<div class="flow-row">
  <div class="flow-box flow-box-api" style="flex: 1; text-align: left; padding: 10px 14px;">
    <div class="flow-box-title">④ Teacher 실행 (GPT-4o-mini API, GT 힌트 포함)</div>
    <div class="flow-box-sub" style="margin-top: 4px;">
      <strong>입력:</strong> Profile(③의 출력) + 후보 50개(②) + <span style="color:#c62828;">GT 힌트: "Cloud Atlas" (B002)</span><br>
      <strong>출력 (요약):</strong>
      <pre style="margin: 4px 0; padding: 6px 8px; font-size: 8.5pt;">{
  "transfer_decisions": {
    "narrative_complexity":  "<span class="tag-transfer">TRANSFER</span>",  // 책에 그대로 적용 가능
    "brand_loyalty":         "<span class="tag-block">BLOCK</span>",     // Nolan은 영화감독, 책엔 안 맞음
    "sensory_preference":    "<span class="tag-block">BLOCK</span>",     // IMAX는 책에 없음
    "emotional_resonance":   "<span class="tag-transfer">TRANSFER</span>",  // 감정적 울림은 책에도 적용
    ...
  },
  "recommendations": [
    {rank: 1, item_id: "B002", title: "Cloud Atlas",
     applied_patterns: ["narrative_complexity", "pacing_preference"]}
    // rank 2~10 (B045 Nolan biography는 BLOCK 때문에 추천에서 제외)
  ]
}</pre>
      <strong>왜 GT 힌트?</strong> Teacher가 "이 책이 추천되어야 한다"는 결과를 알고, 거기에 도달하는
      <strong>올바른 판정 과정</strong>을 시연하기 위함. Student는 이 과정을 학습.
    </div>
  </div>
</div>

<div style="text-align:center; color:#2d3e8a; font-size:14pt;">↓</div>

<!-- ============== STEP 5: 5-stage filter ============== -->
<div class="flow-row">
  <div class="flow-box flow-box-filter" style="flex: 1; text-align: left; padding: 10px 14px;">
    <div class="flow-box-title">⑤ 5단계 품질 필터 (자동 검증)</div>
    <div class="flow-box-sub" style="margin-top: 4px;">
      ① 형식: JSON 파싱 OK ✅<br>
      ② 완전성: 7개 패턴 + 10개 추천 모두 존재 ✅<br>
      ③ <strong>BLOCK 누출:</strong> recommendations의 applied_patterns에 brand_loyalty/sensory_preference가 등장? ❌ → 통과 ✅<br>
      ④ <strong>GT 텍스트 누출:</strong> rationale·reasoning에 "Cloud Atlas" 직접 언급? ❌ → 통과 ✅<br>
      ⑤ <strong>GT Top-10 포함:</strong> "Cloud Atlas"가 rank 1 → 통과 ✅<br>
      <strong>5/5 통과 → 학습 데이터로 채택</strong>
    </div>
  </div>
</div>

<div style="text-align:center; color:#2d3e8a; font-size:14pt;">↓</div>

<!-- ============== STEP 6: SFT 변환 ============== -->
<div class="flow-row">
  <div class="flow-box flow-box-output" style="flex: 1; text-align: left; padding: 10px 14px;">
    <div class="flow-box-title">⑥ SFT 형식 변환 (GT 정보 완전 제거 후 train.jsonl에 1줄 append)</div>
    <div class="flow-box-sub" style="margin-top: 4px;">
      <pre style="margin: 4px 0; padding: 6px 8px; font-size: 8.5pt;">{"messages": [
  {"role": "system",    "content": "You are a Cross-Domain Transfer Judge..."},
  // ↑ system 프롬프트에서 "GT 힌트" 관련 문구 모두 삭제

  {"role": "user",      "content": "Profile: {...} + Candidates: [...]"},
  // ↑ 사용자 입력에서도 GT 힌트 라인 삭제 (Student는 GT를 평생 모름)

  {"role": "assistant", "content": "{transfer_decisions, recommendations}"}
  // ↑ Teacher가 만든 정답 JSON 그대로 (Student가 모방할 목표)
]}</pre>
      <strong>왜 GT 제거?</strong> Student(QLoRA Qwen3-14B)는 추론 시 GT를 절대 보지 않는다.
      학습 시에도 같은 조건이어야 일관성 확보.
    </div>
  </div>
</div>

<div class="flow-caption" style="margin-top: 10px;">
Figure: 가상 사용자 A 1명 → train.jsonl 1줄. 이 과정을 800명 모두 반복 → ~700건 (87.5%+ 통과율)
</div>
<div class="flow-legend">
  <span class="flow-swatch" style="background:#fff4e6;border-color:#e08a3c;"></span>데이터 처리 (①②)
  <span class="flow-swatch" style="background:#e7f1fb;border-color:#2f7bc4;"></span>API LLM 호출 (③④)
  <span class="flow-swatch" style="background:#fff8d9;border-color:#c4a23c;"></span>품질 필터 (⑤)
  <span class="flow-swatch" style="background:#eaeef7;border-color:#2d3e8a;"></span>최종 산출물 (⑥)
</div>
</div>

<div class="callout">
<strong>이 다이어그램에서 꼭 이해해야 할 3가지:</strong><br>
<strong>(1) GT의 두 가지 역할</strong> — Teacher의 "정답 시연용"(④) + 품질 필터의 "검증용"(⑤). 둘 다 학습 데이터에는 들어가지 않음.<br>
<strong>(2) BLOCK이 가치 있는 이유</strong> — "Nolan biography"가 평점 4.2로 높지만 brand_loyalty BLOCK으로 추천에서 제외(④). 이것이 Negative Transfer 방지.<br>
<strong>(3) Student의 학습 목표</strong> — Student는 ⑥의 user입력만 보고 ⑥의 assistant출력을 만들어내야 함. GT 힌트 없이도 동일한 추론을 하도록 학습.
</div>

<h4>9.6 800명 → train.jsonl 전체 통계 흐름</h4>

<table>
<tr><th style="width:8%">단계</th><th>800명 적용 결과</th></tr>
<tr><td>0. 입력</td><td>Train 800명 (각자 Source 15~30개 + Target 5~10개 리뷰)</td></tr>
<tr><td>① GT 분리</td><td>800명 모두 rating ≥ 4 보유 (EDA 99.6% + 샘플링 후 100%) → <strong>800건</strong></td></tr>
<tr><td>② 후보 50개</td><td>800명 × 50개 = 40,000개 후보 (각자 다른 후보 셋, seed=42)</td></tr>
<tr><td>③ Profiler</td><td>800회 API 호출, ~$0.7</td></tr>
<tr><td>④ Teacher</td><td>800회 API 호출, ~$2.0</td></tr>
<tr><td>⑤ 5단계 필터</td><td>예상 통과율 87.5%+ → <strong>~700건</strong></td></tr>
<tr><td>⑥ train.jsonl</td><td><strong>~700줄의 SFT 학습 데이터</strong> → Qwen3-14B QLoRA 파인튜닝 입력</td></tr>
</table>

<!-- ===== 10. Leave-One-Out ===== -->
<h2 class="pagebreak">10. 평가 프로토콜: Leave-One-Out</h2>

<h3>10.1 개요</h3>
<p>Leave-One-Out(LOO)은 추천 시스템 평가에서 가장 널리 사용되는 프로토콜로, 각 사용자의 마지막 상호작용 1개를 테스트용으로 분리하고 나머지로 모델을 추론한다.</p>

<h3>10.2 LOO 적용 절차</h3>
<pre>
각 Test 사용자 u에 대해:
  1. Target(Books) 도메인에서 rating ≥ 4인 구매 중 가장 최근 아이템을 GT로 설정
  2. GT를 제외한 나머지 Target 리뷰(최대 9개)를 Profiler 입력으로 사용
  3. Source(Movies &amp; TV) 리뷰 최대 30개를 Profiler 입력으로 사용
  4. Profiler → Transfer Judge → Top-10 추천 생성
  5. GT가 Top-K에 포함되는지로 HR@K, NDCG@K, MRR 계산
</pre>

<h3>10.3 핵심 설계 결정</h3>
<table>
<tr><th>결정</th><th>선택</th><th>근거</th></tr>
<tr><td><strong>GT 선정</strong></td><td>rating ≥ 4 중 가장 최근</td><td>Transfer Gate 효과를 정확히 측정하기 위해 사용자가 만족한 아이템만 GT로 사용 (섹션 4.4 근거 참조)</td></tr>
<tr><td><strong>GT 평점 제한</strong></td><td>Explicit positive (≥ 4)</td><td>Implicit 방식은 BLOCK의 올바른 판단을 성능 하락으로 왜곡할 수 있음</td></tr>
<tr><td><strong>후보 구성</strong></td><td>GT 1 + Negative 49 = 50</td><td>섹션 4.4의 후보 선정 근거 참조</td></tr>
<tr><td><strong>GT 제외</strong></td><td>Target 리뷰에서 GT 제거 후 입력</td><td>정보 누출(data leakage) 방지</td></tr>
<tr><td><strong>LOO 단위</strong></td><td>사용자당 1개</td><td>Cold-Start 사용자의 Target 리뷰를 더 줄이면 Profiler 입력 품질 저하</td></tr>
</table>

<h3>10.4 왜 LOO인가?</h3>
<table>
<tr><th>프로토콜</th><th>설명</th><th>한계</th><th>선택</th></tr>
<tr class="highlight-row"><td><strong>Leave-One-Out</strong></td><td>마지막 아이템 1개 평가</td><td>사용자당 1회 → Bootstrap CI로 보완</td><td><strong>✓ 채택</strong></td></tr>
<tr><td>K-fold</td><td>상호작용 K개 분할 교차 평가</td><td>Cold-Start(5~10개) 더 분할 시 입력 부족</td><td>✗</td></tr>
<tr><td>Temporal Split</td><td>시간 기준 분리</td><td>LOO의 특수 형태 — 본 연구에서는 동일</td><td>—</td></tr>
</table>
<p><strong>선행연구 일치</strong>: TALLRec, LLM4CDR, TrineCDR, He et al.(2017) 모두 LOO 프로토콜 사용 → 결과 비교 가능.</p>

<h3>10.5 평가 흐름 요약</h3>
<pre>
Input: Source 리뷰 30개 + Target 리뷰 최대 9개 (GT 제외)
  ↓ Profiler: 선호 패턴 JSON 추출
  ↓ Transfer Judge: 패턴별 TRANSFER/PARTIAL/BLOCK 판정
  ↓ Output: Top-10 추천 리스트 (후보 50개 중 순위화)
  ↓ 평가: GT의 순위 확인 → HR@1, HR@5, HR@10, NDCG@10, MRR 계산
</pre>

<h3>10.6 평가 프로세스 (한눈에)</h3>

<div class="flow-wrap">
  <!-- Row 1: Test data -->
  <div class="flow-row">
    <div class="flow-box flow-box-data">
      <div class="flow-box-title">① Test 사용자</div>
      <div class="flow-box-sub">100명<br>(학습에 미사용)</div>
    </div>
    <div class="flow-arrow-h">&#10140;</div>
    <div class="flow-box flow-box-data">
      <div class="flow-box-title">② GT 분리 + 입력 준비</div>
      <div class="flow-box-sub">GT 1건 분리<br>Source 30개 + Target 9개 (GT 제외)</div>
    </div>
    <div class="flow-arrow-h">&#10140;</div>
    <div class="flow-box flow-box-data">
      <div class="flow-box-title">③ 후보 50개 구성</div>
      <div class="flow-box-sub">GT 1 + Negative 49<br>(seed=42 동일 후보)</div>
    </div>
  </div>
  <!-- Row 2: Inference -->
  <div class="flow-row">
    <div class="flow-box flow-box-api">
      <div class="flow-box-title">④ Profiler (추론)</div>
      <div class="flow-box-sub">GPT-4o-mini<br>Source 리뷰 → 7개 패턴 JSON</div>
    </div>
    <div class="flow-arrow-h">&#10140;</div>
    <div class="flow-box flow-box-local">
      <div class="flow-box-title">⑤ Transfer Judge (추론)</div>
      <div class="flow-box-sub">Qwen3-14B + QLoRA<br><strong>GT 모름 상태</strong>에서<br>TRANSFER/PARTIAL/BLOCK + Top-10 생성</div>
    </div>
    <div class="flow-arrow-h">&#10140;</div>
    <div class="flow-box flow-box-filter">
      <div class="flow-box-title">⑥ Top-10 추천 리스트</div>
      <div class="flow-box-sub">후보 50개를<br>점수 기준 순위화</div>
    </div>
  </div>
  <!-- Row 3: Evaluation -->
  <div class="flow-row">
    <div class="flow-box flow-box-output">
      <div class="flow-box-title">⑦ GT 순위 확인</div>
      <div class="flow-box-sub">예: GT가 rank 3이면<br>HR@5=1, HR@1=0, NDCG@10=0.50</div>
    </div>
    <div class="flow-arrow-h">&#10140;</div>
    <div class="flow-box flow-box-output">
      <div class="flow-box-title">⑧ 사용자별 점수 집계</div>
      <div class="flow-box-sub">HR@1/5/10 · NDCG@10 · MRR<br>100명 평균</div>
    </div>
    <div class="flow-arrow-h">&#10140;</div>
    <div class="flow-box flow-box-output">
      <div class="flow-box-title">⑨ Bootstrap 95% CI</div>
      <div class="flow-box-sub">100명에서 1,000회 재표본<br>조건 간 차이 통계 검정</div>
    </div>
  </div>
  <div class="flow-caption">Figure: Leave-One-Out 평가 파이프라인 (Test 100명, 6개 Ablation 조건 모두 동일 절차)</div>
  <div class="flow-legend">
    <span class="flow-swatch" style="background:#fff4e6;border-color:#e08a3c;"></span>데이터 준비
    <span class="flow-swatch" style="background:#e7f1fb;border-color:#2f7bc4;"></span>API LLM (Profiler)
    <span class="flow-swatch" style="background:#e6f6ed;border-color:#2f9a53;"></span>로컬 LLM (Judge)
    <span class="flow-swatch" style="background:#eaeef7;border-color:#2d3e8a;"></span>평가 산출물
  </div>
</div>

<div class="callout">
<strong>학습-평가의 핵심 차이:</strong><br>
학습 시(섹션 9.5): Teacher는 GT를 알고 시연 → Student가 판정 과정을 학습<br>
평가 시(본 섹션): Student(Transfer Judge)는 <strong>GT를 모르는 상태</strong>로 추론 → 실전 추천 시나리오 그대로 시뮬레이션<br>
→ 모든 6개 Ablation 조건은 이 동일한 평가 절차로 측정되며, 차이는 ④⑤ 단계의 모델 구성에서만 발생한다.
</div>

<!-- ===== 11. RQ별 검증 ===== -->
<h2 class="pagebreak">11. Research Question별 검증 방법</h2>

<h3>11.1 Ablation Study 전체 설계</h3>
<table>
<tr><th>조건</th><th>구성</th><th>검증 목적</th></tr>
<tr><td><strong>(a) Single LLM</strong></td><td>단일 프롬프트로 전체 수행</td><td>베이스라인 (LLM4CDR 재현)</td></tr>
<tr><td><strong>(b) Profiler-Judge (Prompt)</strong></td><td>Profiler(P) + Judge(P), 프롬프트 기반</td><td>Profiler-Judge 분리 효과</td></tr>
<tr class="highlight-row"><td><strong>(c) Ours ★</strong></td><td>Profiler(P) + Judge(QLoRA)</td><td>파인튜닝 효과</td></tr>
<tr><td><strong>(d) P-J w/o Gate</strong></td><td>Judge(FT), 모든 패턴 TRANSFER 강제</td><td>Transfer Gate 효과</td></tr>
<tr><td><strong>(e) 전통 CDR</strong></td><td>비LLM 임베딩 기반</td><td>LLM 접근 우위</td></tr>
<tr><td><strong>(f) Raw Review</strong></td><td>Profiler 생략, raw review 직접 입력</td><td>구조화 프로파일 효과</td></tr>
</table>

<h4>각 조건의 구체적 설계 방법</h4>

<table>
<tr><th style="width:14%">조건</th><th style="width:36%">구현 방식</th><th>차별 변인 (다른 조건 대비)</th></tr>
<tr><td><strong>(a) Single LLM</strong></td><td>GPT-4o-mini 1회 호출. 입력: Source 리뷰 + 후보 50개 + "Top-10을 추천하라" 프롬프트. 별도 패턴 추출/판정 단계 없음.</td><td>Profiler-Judge <strong>분리 없음</strong>. 단일 LLM이 모든 작업 수행 (LLM4CDR 방식 재현).</td></tr>
<tr><td><strong>(b) Profiler-Judge (Prompt)</strong></td><td>Profiler: (c)와 동일 GPT-4o-mini API. Judge: Qwen3-14B-Instruct를 <strong>파인튜닝 없이 프롬프트만으로</strong> 사용 (Few-shot 3예시 포함).</td><td>(a) 대비 <strong>역할 분리 추가</strong>, (c) 대비 <strong>QLoRA 파인튜닝 제외</strong>.</td></tr>
<tr><td><strong>(c) Ours ★</strong></td><td>Profiler: GPT-4o-mini API. Judge: Qwen3-14B + <strong>QLoRA 파인튜닝</strong> (Teacher Distillation 700건으로 학습). Section 9의 학습 데이터 사용.</td><td>본 연구의 완전한 구성. (b) 대비 <strong>파인튜닝 추가</strong>.</td></tr>
<tr><td><strong>(d) P-J w/o Gate</strong></td><td>Profiler·Judge 구조는 (c)와 동일. 단, Judge 추론 시 <strong>모든 패턴을 TRANSFER로 강제</strong> (BLOCK/PARTIAL 출력을 후처리로 TRANSFER 변환).</td><td>(c) 대비 <strong>Transfer Gate 비활성화</strong>. 패턴별 차단 효과만 분리 검증.</td></tr>
<tr><td><strong>(e) 전통 CDR</strong></td><td>비LLM 베이스라인. EMCDR(IJCAI 2017) 또는 CATN(SIGIR 2020) 재현 — 사용자/아이템 임베딩 학습 후 cross-domain mapping. 동일 1,000명 데이터 사용.</td><td>LLM 접근 자체의 우위 검증. <strong>LLM 미사용</strong>.</td></tr>
<tr><td><strong>(f) Raw Review</strong></td><td>Profiler 단계 생략. Source 리뷰 텍스트를 그대로 Judge(QLoRA)에 입력. Judge는 (c)와 동일하게 학습된 모델 사용.</td><td>(c) 대비 <strong>구조화된 Profile 입력 제거</strong> — 패턴 JSON vs raw text 효과 분리.</td></tr>
</table>

<h4>RQ별 비교 매핑 (어떤 조건끼리 비교하면 어떤 RQ를 검증하는가)</h4>

<table>
<tr><th style="width:14%">RQ</th><th>비교</th><th>분리되는 효과</th></tr>
<tr><td><strong>RQ1</strong></td><td>(c) vs (a) · (c) vs (e)</td><td>본 연구 프레임워크의 전반적 우위 (단일 LLM·전통 CDR 대비)</td></tr>
<tr><td><strong>RQ2</strong></td><td>(c) vs (d)</td><td>Transfer Gate(BLOCK·PARTIAL 차단)의 순효과</td></tr>
<tr><td><strong>RQ3</strong></td><td>(b) vs (c)</td><td>QLoRA 파인튜닝의 순효과 (구조 분리는 동일하게 유지)</td></tr>
<tr><td>보조</td><td>(c) vs (f)</td><td>Profiler 구조화 출력의 가치 (Profile JSON vs Raw Review)</td></tr>
<tr><td>보조</td><td>(a) vs (b)</td><td>역할 분리 자체의 효과 (파인튜닝 없이도 우위인지)</td></tr>
</table>

<div class="callout">
<strong>변인 통제 원칙:</strong> 모든 조건은 동일한 1,000명 데이터·동일 후보 50개(seed=42)·동일 평가 프로토콜(LOO, HR@K/NDCG@K)을 공유한다.
조건 간 차이는 표의 "차별 변인"으로만 발생하므로, 두 조건의 성능 차이는 해당 변인의 순효과로 해석 가능.
</div>

<h3>11.2 평가 지표</h3>
<table>
<tr><th>지표</th><th>설명</th></tr>
<tr><td>HR@1</td><td>1위 추천이 정답인 비율</td></tr>
<tr><td>HR@5</td><td>Top-5에 정답 포함 비율</td></tr>
<tr><td>HR@10</td><td>Top-10에 정답 포함 비율</td></tr>
<tr><td>NDCG@10</td><td>정답의 순위를 고려한 점수</td></tr>
<tr><td>MRR</td><td>정답 순위 역수의 평균</td></tr>
</table>

<h4>각 지표가 무엇을 의미하는가 (직관적 설명)</h4>

<table>
<tr><th style="width:12%">지표</th><th style="width:40%">의미와 계산 예시</th><th>왜 이 지표를 보는가</th></tr>
<tr><td><strong>HR@1</strong><br>(Hit Rate)</td><td>"1번 추천했을 때 적중한 비율"<br>예: 100명 중 25명이 1위 추천이 정답 → HR@1 = 0.25<br>값 범위: 0~1 (높을수록 좋음)</td><td>가장 엄격한 정확도. <strong>단 1개만 추천</strong>하는 시나리오의 품질을 본다. 추천 시스템의 "최상위 정확도"를 의미.</td></tr>
<tr><td><strong>HR@5</strong></td><td>"Top-5 안에 정답이 포함된 비율"<br>예: GT가 rank 4 → Hit / GT가 rank 7 → Miss<br>100명 중 60명 적중 → HR@5 = 0.60</td><td>현실적 추천 UI(상위 5개 노출)의 품질. HR@1보다 후하지만 여전히 엄격.</td></tr>
<tr><td><strong>HR@10</strong></td><td>"Top-10 안에 정답이 포함된 비율"<br>후보 50개 중 랜덤 추천 시 기댓값 = 20%<br>모델이 그 이상이어야 의미 있음</td><td>전체 추천 리스트 도달률. 본 연구의 주요 보고 지표.</td></tr>
<tr><td><strong>NDCG@10</strong><br>(Normalized DCG)</td><td>"정답이 몇 위에 있는지를 가중치로 점수화"<br>GT가 rank 1 → 1.00 / rank 3 → 0.50 / rank 10 → 0.29 / Top-10 밖 → 0<br>로그 감쇠로 상위 순위에 더 큰 가중</td><td>HR은 Top-K 안/밖만 보지만, NDCG는 <strong>"몇 위인지"</strong>까지 본다. rank 1 추천과 rank 10 추천을 다르게 평가.</td></tr>
<tr><td><strong>MRR</strong><br>(Mean Reciprocal Rank)</td><td>"정답 순위의 역수 평균"<br>GT가 rank 1 → 1/1 / rank 2 → 1/2 / rank 5 → 1/5<br>100명의 1/rank 평균값</td><td>"평균적으로 정답이 몇 위쯤에 있는가"의 직관적 표현. 1/MRR ≈ 정답의 평균 순위.</td></tr>
</table>

<div class="callout">
<strong>왜 5개 지표를 함께 보는가?</strong><br>
<strong>HR@1</strong>은 너무 엄격해서 모델 차이가 잘 안 보일 수 있고, <strong>HR@10</strong>은 너무 후해서 천장 효과 위험.
<strong>NDCG@10</strong>은 순위 품질을 정량화하지만 직관적 해석이 어렵고, <strong>HR</strong>은 Top-K 안/밖만 본다.
다섯 지표를 함께 보면 <strong>"정확도 + 순위 품질 + 도달률"</strong>의 다면적 평가가 가능하다.<br><br>
<strong>선행연구 일치:</strong> TALLRec, LLM4CDR, NCF 등 추천시스템 표준 보고 지표 그대로 사용 → 결과 비교 가능.
</div>

<h3>11.3 통계적 유의성: Bootstrap Confidence Interval</h3>
<p>Test 100명에서 1,000회 부트스트랩으로 95% 신뢰구간 산출.</p>
<p>논문 표기: <code>HR@10 = 0.72 (95% CI: 0.64-0.79)</code></p>

<h4>왜 Bootstrap CI가 필요한가?</h4>

<table>
<tr><th style="width:30%">문제</th><th>설명</th></tr>
<tr><td><strong>① 단일 점수 보고의 한계</strong></td><td>"HR@10 = 0.72"만 보고하면 그 값이 우연인지 진짜 모델 성능인지 알 수 없다. Test 100명이 다른 100명이었다면 0.65 또는 0.78이 나올 수도 있다.</td></tr>
<tr><td><strong>② 조건 비교의 신뢰성</strong></td><td>(c) HR@10=0.72 vs (a) HR@10=0.68 — 0.04 차이가 통계적으로 유의한가? 우연일 수도 있다. CI 겹침 여부로 판단.</td></tr>
<tr><td><strong>③ Test 샘플 크기 100명의 특수성</strong></td><td>샘플이 작을수록 단일 점수의 변동성이 커진다. 100명에서 측정한 값이 "모집단 전체에서도 비슷한지" 추정 필요.</td></tr>
<tr><td><strong>④ 정규성 가정 회피</strong></td><td>HR/NDCG는 정규분포를 따르지 않는다(이진/비대칭). Bootstrap은 분포 가정 없이 신뢰구간을 만들 수 있는 비모수적 방법.</td></tr>
</table>

<h4>Bootstrap CI 계산 절차</h4>

<table>
<tr><th style="width:6%">단계</th><th>내용</th></tr>
<tr><td>①</td><td>Test 100명 각각의 HR@10 값을 계산 (각 사용자: 0 또는 1)</td></tr>
<tr><td>②</td><td>이 100명에서 <strong>복원 추출(with replacement)</strong>로 100명을 재표본 → 평균 계산 (1개 부트스트랩 표본)</td></tr>
<tr><td>③</td><td>②를 <strong>1,000회 반복</strong> → 1,000개의 평균값 분포 확보</td></tr>
<tr><td>④</td><td>1,000개 값의 <strong>2.5 percentile ~ 97.5 percentile</strong>이 95% 신뢰구간</td></tr>
<tr><td>⑤</td><td>모든 지표(HR@1/5/10, NDCG@10, MRR)와 모든 조건(a~f)에 대해 동일 절차 적용</td></tr>
</table>

<h4>해석 예시 — 두 조건 비교</h4>

<table>
<tr><th>조건</th><th>HR@10</th><th>95% CI</th><th>유의성 판단</th></tr>
<tr><td>(c) Ours ★</td><td>0.72</td><td>[0.64, 0.79]</td><td rowspan="2">CI가 <strong>겹치지 않음</strong> → (c)가 (a)보다 통계적으로 유의하게 우수 (p &lt; 0.05)</td></tr>
<tr><td>(a) Single LLM</td><td>0.55</td><td>[0.48, 0.62]</td></tr>
<tr><td>(c) Ours ★</td><td>0.72</td><td>[0.64, 0.79]</td><td rowspan="2">CI가 <strong>겹침</strong> → 차이가 통계적 유의성 미달. 더 많은 Test 데이터 필요할 수 있음</td></tr>
<tr><td>(b) P-J Prompt</td><td>0.69</td><td>[0.61, 0.76]</td></tr>
</table>

<div class="callout">
<strong>왜 1,000회인가?</strong> 추천시스템 논문 표준 (NCF, TALLRec 등). 100~500회는 신뢰구간이 불안정하고, 5,000회 이상은 계산 비용 대비 추가 정확도 미미. 1,000회가 정확도와 비용의 균형점.<br><br>
<strong>왜 95% CI인가?</strong> 통계학 표준 (alpha=0.05). 99% CI는 너무 보수적이어서 작은 차이를 검출 못하고, 90% CI는 1종 오류 위험 증가. 95%가 표준.<br><br>
<strong>이 분석으로 강화되는 RQ 결론:</strong> 단순히 "(c) HR@10 = 0.72 > (a) HR@10 = 0.55"라고 하지 않고,
"(c)가 (a)보다 95% 신뢰수준에서 통계적으로 유의하게 우수 (CI 비겹침)"라고 보고 → <strong>심사 대응력 ↑</strong>.
</div>

<!-- ===== 12. 참고문헌 ===== -->
<h2 class="pagebreak">12. 참고문헌</h2>

<h3>12.1 핵심 인용 논문</h3>
<table>
<tr><th style="width:25px">#</th><th style="width:200px">논문</th><th style="width:110px">학회</th><th>인용 맥락</th></tr>
<tr><td>1</td><td>Bao et al., "TALLRec"</td><td>RecSys 2023</td><td>QLoRA 기반 LLM 추천 파인튜닝의 이론적 근거. 50건 미만 학습 데이터로도 추천 능력 달성 → Teacher Distillation 데이터 규모(700건) 충분성 근거</td></tr>
<tr><td>2</td><td>TrineCDR (Chen et al.)</td><td>KDD 2024</td><td>NT 원인을 Feature/Interaction/Domain 3 level로 분류 → Transfer Gate 3단계의 개념적 근거</td></tr>
<tr><td>3</td><td>LLM4CDR (Zhao et al.)</td><td>WWW 2025</td><td>Single LLM + 프롬프트 CDR. 가장 직접적인 비교 대상(베이스라인)</td></tr>
<tr><td>4</td><td>Zhang &amp; Wu, "Survey on NT"</td><td>IEEE/CAA JAS 2023</td><td>NT 완화 접근을 Domain/Instance/Feature 3단계로 분류한 서베이 — 이론적 토대</td></tr>
<tr><td>5</td><td>Wang et al.</td><td>CVPR 2019</td><td>NT의 3가지 요인 식별 + gate 기반 filtering — Transfer Gate 방법론적 선례</td></tr>
<tr><td>6</td><td>Cao et al. (SAN)</td><td>CVPR 2018</td><td>Binary selective transfer의 한계 → PARTIAL 등급 확장 필요성 근거</td></tr>
<tr><td>7</td><td>FedGCDR (Liu et al.)</td><td>NeurIPS 2024</td><td>Soft/Hard NT 구분 — NT 강도 차이의 실증적 근거</td></tr>
<tr><td>8</td><td>Park et al.</td><td>CIKM 2023</td><td>Shapley 연속 가중치 기반 전이 조절 — 이산 판정 발전 동기</td></tr>
<tr><td>9</td><td>McAuley Lab, Amazon Review 2023</td><td>Dataset</td><td>실험 데이터셋 소스</td></tr>
</table>

<h3>12.2 방법론 근거 논문</h3>
<table>
<tr><th style="width:25px">#</th><th style="width:200px">논문</th><th style="width:110px">학회</th><th>인용 맥락</th></tr>
<tr><td>10</td><td>Hinton et al., "Distilling the Knowledge in a Neural Network"</td><td>NeurIPS WS 2015</td><td>Knowledge Distillation 원론적 근거. Teacher-Student 패러다임의 이론적 토대</td></tr>
<tr><td>11</td><td>Wei et al., "Chain-of-Thought Prompting"</td><td>NeurIPS 2022</td><td>CoT rationale 포함 학습이 일반화 성능 향상 → Teacher rationale 포함 출력 설계 정당화</td></tr>
<tr><td>12</td><td>Hu et al., "LoRA"</td><td>ICLR 2022</td><td>LoRA/QLoRA 파인튜닝 방법론의 원론적 근거</td></tr>
<tr><td>13</td><td>Dettmers et al., "QLoRA"</td><td>NeurIPS 2023</td><td>4-bit 양자화 + LoRA 효율성 검증. 제한된 GPU에서 14B 파인튜닝 가능성 근거</td></tr>
<tr><td>14</td><td>Qwen Team, "Qwen3 Technical Report"</td><td>arXiv 2025</td><td>Qwen3-14B 벤치마크 성능 데이터. Transfer Judge LLM 선정 근거</td></tr>
</table>

<h3>12.3 평가 방법론 근거 논문</h3>
<table>
<tr><th style="width:25px">#</th><th style="width:200px">논문</th><th style="width:110px">학회</th><th>인용 맥락</th></tr>
<tr><td>15</td><td>He et al., "Neural Collaborative Filtering"</td><td>WWW 2017</td><td>LOO + Random Negative Sampling 평가 프로토콜의 표준 정립</td></tr>
<tr><td>16</td><td>Krichene &amp; Rendle, "On Sampled Metrics"</td><td>KDD 2020</td><td>샘플링 기반 평가(50개 후보)의 이론적 정당성 — 전체 아이템 대비 순위 상관성 유지 증명</td></tr>
</table>

</body>
</html>
"""

if __name__ == "__main__":
    doc = weasyprint.HTML(string=HTML_CONTENT)
    doc.write_pdf(OUTPUT_PATH)
    print(f"PDF generated: {OUTPUT_PATH}")
