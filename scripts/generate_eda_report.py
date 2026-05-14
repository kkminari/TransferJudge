#!/usr/bin/env python3
"""TransferJudge EDA 보고서 PDF 생성 스크립트"""

import weasyprint
import os
import base64

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "docs", "eda")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "TransferJudge_EDA_Report.pdf")


def img_to_base64(filename):
    """이미지 파일을 base64 인코딩하여 HTML img src로 반환"""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"


# 이미지 base64 변환
IMG_OVERLAP = img_to_base64("eda_overlap_heatmap.png")
IMG_REVIEW_COUNT = img_to_base64("eda_review_count_dist.png")
IMG_TOKEN_DIST = img_to_base64("eda_token_distribution.png")
IMG_RATING = img_to_base64("eda_rating_distribution.png")
IMG_TEMPORAL = img_to_base64("eda_temporal_distribution.png")
IMG_RECENCY = img_to_base64("eda_temporal_recency.png")
IMG_CATEGORY = img_to_base64("eda_category_distribution.png")
IMG_CANDIDATE = img_to_base64("eda_candidate_tokens.png")
IMG_RATING_DIV = img_to_base64("eda_rating_diversity.png")
IMG_CROSS_DOMAIN = img_to_base64("eda_cross_domain_categories.png")
IMG_GT_VS_NEG = img_to_base64("eda_gt_vs_negative.png")

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
    line-height: 1.65;
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
    margin-bottom: 30px;
  }}
  h2 {{
    font-size: 14pt;
    color: #16213e;
    border-bottom: 2.5px solid #4a90d9;
    padding-bottom: 4px;
    margin-top: 35px;
  }}
  h3 {{ font-size: 12pt; color: #0f3460; margin-top: 20px; }}
  h4 {{ font-size: 10.5pt; color: #333; margin-top: 15px; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 15px 0;
    font-size: 9.5pt;
  }}
  th {{
    background: #16213e;
    color: white;
    padding: 6px 8px;
    text-align: left;
    font-weight: 600;
  }}
  td {{
    padding: 5px 8px;
    border-bottom: 1px solid #ddd;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #f8f9fa; }}
  .highlight-row td {{ background: #e8f4fd !important; font-weight: 600; }}
  .callout {{
    background: #f0f4f8;
    border-left: 4px solid #4a90d9;
    padding: 10px 14px;
    margin: 12px 0;
    font-size: 9.5pt;
  }}
  .callout-warn {{
    background: #fff8e1;
    border-left: 4px solid #f5a623;
    padding: 10px 14px;
    margin: 12px 0;
    font-size: 9.5pt;
  }}
  .callout-green {{
    background: #e8f5e9;
    border-left: 4px solid #4caf50;
    padding: 10px 14px;
    margin: 12px 0;
    font-size: 9.5pt;
  }}
  .result {{ color: #1565c0; font-weight: 700; }}
  .pass {{ color: #2e7d32; font-weight: 700; }}
  .warn {{ color: #e65100; font-weight: 700; }}
  .pagebreak {{ page-break-before: always; }}
  ul, ol {{ margin: 5px 0; padding-left: 22px; }}
  li {{ margin: 3px 0; }}
  img.chart {{ width: 100%; margin: 10px 0; }}
  img.chart-half {{ width: 48%; margin: 5px 1%; }}
  .fig-caption {{ text-align: center; font-size: 9pt; color: #666; margin-top: -5px; margin-bottom: 15px; }}
</style>
</head>
<body>

<!-- ===== TITLE ===== -->
<h1>TransferJudge EDA Report</h1>
<p class="subtitle">Amazon Reviews 2023 탐색적 데이터 분석 보고서</p>
<p class="subtitle">TransferJudge: A Profiler-Judge LLM-Based Framework for Selective Transfer in Cross-Domain Recommendation</p>
<p class="subtitle">선택적 전이를 위한 Profiler-Judge 구조의 LLM 기반 교차 도메인 추천 프레임워크</p>
<p class="author">2026.04 빅데이터학과 17기 곽민아</p>

<!-- ===== 목차 ===== -->
<h2>목차</h2>
<ol>
<li>분석 목적 및 개요</li>
<li>원본 데이터 구조 (리뷰 + 메타데이터)</li>
<li>데이터 전처리 및 Overlapping User 추출</li>
<li>리뷰 수 분포 분석</li>
<li>리뷰 토큰 수 분포 및 토큰 예산 검증</li>
<li>평점 분포 및 GT 확보율</li>
<li>시간 분포 및 시점 타당성</li>
<li>메타데이터 품질 분석</li>
<li>후보 아이템 토큰 검증</li>
<li>종합 판정 및 설계 결정</li>
<li>추가 검증 (GAP-1, GAP-2, GAP-4)</li>
</ol>

<!-- ===== 1. 분석 목적 ===== -->
<h2 class="pagebreak">1. 분석 목적 및 개요</h2>

<h3>1.1 목적</h3>
<p>본 EDA는 TransferJudge 실험 설계의 핵심 가정들을 실제 데이터로 검증하기 위해 수행되었다.
Pilot Study 및 본 실험 전에 데이터의 분포와 특성을 파악하여, 실험 조건의 타당성을 확인한다.</p>

<h3>1.2 검증 대상</h3>
<table>
<tr><th>검증 항목</th><th>가설/기준</th><th>판단 기준</th></tr>
<tr><td>Overlapping User 규모</td><td>1,000명 이상 추출 가능</td><td>Source≥15, Target 5~10 조건</td></tr>
<tr><td>리뷰 토큰 예산</td><td>GPT-4o-mini 128K context 내 수용</td><td>P95 worst-case 기준</td></tr>
<tr><td>GT 확보율</td><td>rating≥4 구매가 존재하는 사용자 비율</td><td>≥80%</td></tr>
<tr><td>시점 타당성</td><td>리뷰가 너무 오래되지 않았는지</td><td>2018년 이전 사용자 &lt;30%</td></tr>
<tr><td>메타데이터 품질</td><td>후보 아이템 정보 구성 가능 여부</td><td>title, rating 결측률</td></tr>
<tr><td>후보 아이템 토큰</td><td>50개 후보의 총 토큰이 예산 내</td><td>&lt;3,500 tokens</td></tr>
</table>

<h3>1.3 데이터 소스</h3>
<p><strong>Amazon Reviews 2023</strong> (McAuley Lab, UCSD) — HuggingFace <code>McAuley-Lab/Amazon-Reviews-2023</code></p>
<ul>
<li>전체 571.54M 리뷰, 54.51M 사용자, 48.19M 아이템</li>
<li>본 연구 대상: <strong>Movies &amp; TV</strong> (Source) + <strong>Books</strong> (Target)</li>
</ul>

<!-- ===== 2. 원본 데이터 구조 ===== -->
<h2 class="pagebreak">2. 원본 데이터 구조</h2>

<h3>2.1 리뷰 데이터 스키마</h3>
<p>HuggingFace <code>raw_review_Movies_and_TV</code>, <code>raw_review_Books</code>에서 로딩.</p>

<table>
<tr><th>필드명</th><th>타입</th><th>설명</th><th>예시</th></tr>
<tr><td><code>user_id</code></td><td>string</td><td>익명화된 사용자 고유 ID. <strong>도메인 간 동일 ID 공유</strong> → Overlapping User 식별 가능</td><td>AGGZ357AO26RQ...</td></tr>
<tr><td><code>parent_asin</code></td><td>string</td><td>아이템 고유 ID. 메타데이터 조인 키</td><td>B013488XFS</td></tr>
<tr><td><code>rating</code></td><td>float</td><td>사용자 평점 (1.0~5.0)</td><td>5.0</td></tr>
<tr><td><code>text</code></td><td>string</td><td>리뷰 본문 텍스트. <strong>Profiler의 핵심 입력</strong></td><td>"Amazon, please buy the show!"</td></tr>
<tr><td><code>title</code></td><td>string</td><td>리뷰 제목 (사용자가 작성)</td><td>"Five Stars"</td></tr>
<tr><td><code>timestamp</code></td><td>int64</td><td>리뷰 작성 시각 (밀리초 단위 Unix timestamp)</td><td>1440385637000</td></tr>
</table>

<div class="callout">
<strong>주요 특징:</strong> <code>user_id</code>는 모든 카테고리에서 동일한 익명화 문자열을 사용하므로,
Movies &amp; TV와 Books 양쪽에 리뷰를 남긴 사용자를 <code>user_id</code> 교집합으로 찾을 수 있다.
<code>text</code> 필드는 본 연구의 핵심 입력으로, Profiler가 이 텍스트에서 선호 패턴을 추출한다.
</div>

<h3>2.2 메타데이터 스키마</h3>
<p>HuggingFace <code>raw_meta_Books</code>, <code>raw_meta_Movies_and_TV</code>에서 로딩.</p>

<table>
<tr><th>필드명</th><th>타입</th><th>설명</th><th>용도</th></tr>
<tr><td><code>parent_asin</code></td><td>string</td><td>아이템 고유 ID (리뷰와 조인 키)</td><td>리뷰-아이템 매핑</td></tr>
<tr><td><code>title</code></td><td>string</td><td>제품명 (책 제목 / 영화 제목)</td><td>후보 아이템 표시</td></tr>
<tr><td><code>main_category</code></td><td>string</td><td>최상위 카테고리</td><td>"Books", "Movies &amp; TV"</td></tr>
<tr><td><code>categories</code></td><td>list</td><td>계층적 카테고리 (예: Books → Literature → Contemporary)</td><td>후보 아이템 장르</td></tr>
<tr><td><code>average_rating</code></td><td>float</td><td>아이템 평균 평점</td><td>후보 아이템 품질 지표</td></tr>
<tr><td><code>rating_number</code></td><td>int</td><td>총 평점 수</td><td>인기도 참고</td></tr>
<tr><td><code>features</code></td><td>list</td><td>제품 소개/줄거리 텍스트 배열</td><td><strong>책 내용 파악 (핵심)</strong></td></tr>
<tr><td><code>description</code></td><td>list</td><td>제품 설명 (저자 소개, 리뷰 인용 등 혼재)</td><td>품질 불균일 → 미사용</td></tr>
<tr><td><code>author</code></td><td>dict</td><td>저자 정보 (name, avatar, about)</td><td>후보 아이템 저자명</td></tr>
<tr><td><code>details</code></td><td>dict/JSON</td><td>상세 속성 (Publisher, ISBN, Language 등)</td><td>출판 정보</td></tr>
<tr><td><code>subtitle</code></td><td>string</td><td>판형 정보 (Hardcover, Kindle Edition 등)</td><td>참고용</td></tr>
<tr><td><code>price</code></td><td>float</td><td>가격</td><td>미사용</td></tr>
<tr><td><code>store</code></td><td>string</td><td>판매처/브랜드</td><td>미사용</td></tr>
</table>

<h3>2.3 Movies &amp; TV 메타데이터 — details 주요 키</h3>
<table>
<tr><th>키</th><th>설명</th><th>출현율 (샘플 5,000건)</th></tr>
<tr><td>Directors / Director</td><td>감독명 (리스트 또는 문자열)</td><td>~70%</td></tr>
<tr><td>Actors / Starring</td><td>출연 배우 (리스트)</td><td>~72%</td></tr>
<tr><td>Release date</td><td>개봉/출시일</td><td>~37%</td></tr>
<tr><td>Run time / Runtime</td><td>상영 시간</td><td>~37%</td></tr>
<tr><td>Genre</td><td>장르</td><td>~19%</td></tr>
</table>

<h3>2.4 Books 메타데이터 — details 주요 키</h3>
<table>
<tr><th>키</th><th>설명</th><th>출현율 (샘플 5,000건)</th></tr>
<tr><td>Language</td><td>언어</td><td>94.1%</td></tr>
<tr><td>Publisher</td><td>출판사 + 출판일</td><td>92.4%</td></tr>
<tr><td>ISBN 13 / ISBN 10</td><td>국제 표준 도서 번호</td><td>80~85%</td></tr>
<tr><td>Paperback / Hardcover / Print length</td><td>페이지 수</td><td>54~21%</td></tr>
<tr><td>Publication date</td><td>출판일 (별도 필드)</td><td>7.1%</td></tr>
</table>

<div class="callout">
<strong>핵심 발견 — <code>features</code> vs <code>description</code>:</strong><br>
<code>description</code> 필드는 리뷰 인용("Review ..."), 저자 소개("About the Author ...") 등
비정형 내용이 혼재되어 책의 내용을 파악하기 어렵다.<br>
반면 <code>features</code> 필드에 실제 책 소개/줄거리가 저장되어 있으며, <strong>88.3%의 아이템에 존재</strong>한다.
후보 아이템 정보 구성 시 features를 활용한다.
</div>

<!-- ===== 3. 전처리 및 Overlapping User ===== -->
<h2 class="pagebreak">3. 데이터 전처리 및 Overlapping User 추출</h2>

<h3>3.1 원본 데이터 규모</h3>
<table>
<tr><th>항목</th><th>Movies &amp; TV</th><th>Books</th></tr>
<tr><td>전체 리뷰 수</td><td>17,328,314</td><td>29,475,453</td></tr>
<tr><td>고유 사용자 수</td><td>6,503,429</td><td>10,297,355</td></tr>
<tr><td>고유 아이템 수</td><td>747,764</td><td>4,446,065</td></tr>
<tr><td>평점 범위</td><td>1.0 ~ 5.0</td><td>0.0 ~ 5.0</td></tr>
<tr><td>데이터 기간</td><td>1997-08 ~ 2023-09</td><td>1996-06 ~ 2023-09</td></tr>
<tr><td>text 결측률</td><td>0.00%</td><td>0.00%</td></tr>
</table>

<h3>3.2 전처리</h3>
<p>text가 null이거나 빈 문자열인 리뷰를 제거하였다.</p>
<table>
<tr><th></th><th>전처리 전</th><th>전처리 후</th><th>제거율</th></tr>
<tr><td>Movies &amp; TV</td><td>17,328,314</td><td>17,327,095</td><td>0.01%</td></tr>
<tr><td>Books</td><td>29,475,453</td><td>29,467,817</td><td>0.03%</td></tr>
</table>

<h3>3.3 Overlapping User 추출</h3>
<p><strong>분석 목적:</strong> 양쪽 도메인에 모두 리뷰를 남긴 사용자가 실험에 필요한 1,000명 이상 확보 가능한지 확인.</p>

<p>전처리 후 Overlapping 사용자: <span class="result">2,530,704명</span></p>

<h4>조건별 사용자 수 탐색</h4>
<p>Source(Movies) 최소 리뷰 수와 Target(Books) 리뷰 범위를 변화시키며 조건 충족 사용자 수를 확인하였다.</p>

<table>
<tr><th>Source 기준</th><th>Target 1~5</th><th>Target 3~10</th><th>Target 5~10</th><th>Target 5~15</th><th>Target 5~20</th></tr>
<tr><td>≥ 1</td><td>2,073,112</td><td>800,355</td><td>367,180</td><td>453,055</td><td>493,075</td></tr>
<tr><td>≥ 3</td><td>616,104</td><td>327,426</td><td>167,751</td><td>214,686</td><td>238,503</td></tr>
<tr><td>≥ 5</td><td>302,312</td><td>184,739</td><td>100,034</td><td>131,088</td><td>147,749</td></tr>
<tr><td>≥ 10</td><td>98,084</td><td>71,670</td><td>41,591</td><td>56,885</td><td>65,605</td></tr>
<tr class="highlight-row"><td>≥ 15</td><td>47,058</td><td>37,447</td><td><strong>22,465</strong></td><td>31,450</td><td>36,891</td></tr>
<tr><td>≥ 20</td><td>27,278</td><td>22,835</td><td>13,984</td><td>19,879</td><td>23,621</td></tr>
<tr><td>≥ 30</td><td>12,273</td><td>10,665</td><td>6,629</td><td>9,632</td><td>11,673</td></tr>
</table>

<div class="callout-green">
<strong>판정:</strong> 본 연구 조건 (Source ≥ 15, Target 5~10)에서 <strong>22,465명</strong> 확보 가능 →
목표 1,000명 대비 <span class="pass">22배 이상 여유</span>. seed=42로 1,000명 랜덤 샘플링 완료.
</div>

{"<img class='chart' src='" + IMG_OVERLAP + "' />" if IMG_OVERLAP else ""}
<p class="fig-caption">Figure 1. 조건별 Overlapping User 수 히트맵 (좌) 및 Source 리뷰 수 분포 (우)</p>

<h4>1,000명 샘플링 방식 타당성 (선행연구 비교)</h4>
<p><strong>분석 목적:</strong> "1,000명만 뽑아도 되는가?", "무작위 샘플링(최신 순 아님)이 타당한가?"에 대한 근거를 선행연구와 비교하여 문서화.</p>

<table>
<tr><th>논문</th><th>샘플 규모</th><th>샘플링 방식</th><th>시간 필터</th></tr>
<tr><td>TALLRec (RecSys 2023)</td><td>16 / 64 / 256 샘플 (few-shot)</td><td>Books: 사용자별 무작위 1건 · Movies: 최근 10K interaction</td><td>부분 (Movies만)</td></tr>
<tr><td>LLM4CDR (WWW 2025)</td><td><strong>100명</strong></td><td><strong>무작위</strong> (budget 제약)</td><td>❌ 없음</td></tr>
<tr><td>EMCDR (IJCAI 2017)</td><td>전체 overlapping user</td><td>무작위 비율 분할 (5% / 50% / 80%)</td><td>❌ 없음</td></tr>
<tr><td>CDRNP (WSDM 2024)</td><td>50% cold-start 시뮬레이션</td><td>무작위</td><td>❌ 없음</td></tr>
<tr><td>Serendipity-2018 (LLM 벤치마크)</td><td>500명 × 5 seeds</td><td>무작위 + 다중 seed</td><td>❌ 없음</td></tr>
<tr class="highlight-row"><td><strong>본 연구 (TransferJudge)</strong></td><td><strong>1,000명</strong></td><td><strong>무작위 (seed=42)</strong></td><td>❌ 없음</td></tr>
</table>

<div class="callout-green">
<strong>1. 샘플 규모 타당성 — 선행연구 대비 2~10배 큰 규모:</strong><br>
LLM4CDR 100명 대비 10배, TALLRec few-shot 256 대비 4배, Serendipity 500명 대비 2배.
LLM 기반 CDR norm에서 <strong>상위권</strong> 규모이며, Teacher Distillation 학습 데이터
~50,000건(800명 × 평균 60 후보) 생성을 위한 균형점으로 설정되었다.
LLM API 호출 비용 및 QLoRA 학습 시간을 고려한 결정이다.
</div>

<div class="callout-green">
<strong>2. 무작위 샘플링 타당성 — CDR 학계 표준 프로토콜:</strong><br>
비교한 주요 CDR 논문 4편(TALLRec, LLM4CDR, EMCDR, CDRNP) 모두
시간 기준 샘플링이 아닌 <strong>무작위 샘플링</strong>을 채택하였다.
이는 특정 시점 사용자에게 모델이 과적합되지 않도록 하는 표준 관행이다.
본 연구는 seed=42로 고정하여 재현성을 확보하였다.
</div>

<div class="callout-green">
<strong>3. 시점 편향 관리 — EDA로 정량 확인:</strong><br>
시간 필터 미적용에 따른 시점 편향을 확인한 결과:
Source-Target 시점 갭 <strong>중앙값 1.2년</strong>,
2018년 이전 사용자 <strong>25.8%</strong>(30% 미만)로 허용 범위 내
(상세: 섹션 7). 선행연구는 시점 분포를 명시적으로 보고하지 않았으나,
본 연구는 EDA에서 정량화하여 투명성을 강화하였다.
</div>

<h4>Overlapping User 데이터 vs GT 데이터 — 정의와 구성</h4>
<p><strong>분석 목적:</strong> 두 데이터 개념의 차이와 본 연구에서의 역할을 명확히 정의.</p>

<table>
<tr><th>구분</th><th>Overlapping User 데이터</th><th>GT (Ground Truth) 데이터</th></tr>
<tr><td>정의</td><td>두 도메인 모두에 리뷰를 남긴 사용자</td><td>모델 예측의 정답 아이템</td></tr>
<tr><td>단위</td><td>사용자 단위</td><td>아이템 단위 (사용자당 1건)</td></tr>
<tr><td>역할</td><td>실험 대상자 선정 기준</td><td>모델 평가의 정답 라벨</td></tr>
<tr><td>확보 방식</td><td>Movies&amp;TV ∩ Books 의 <code>user_id</code> 교집합</td><td>Target(Books) 리뷰 중 rating ≥ 4인 가장 최근 1건</td></tr>
<tr><td>수량</td><td>22,465명 → 샘플 1,000명</td><td>사용자당 1건 (총 1,000건)</td></tr>
<tr><td>근거</td><td>Cross-Domain 전이가 가능한 대상 확보</td><td>LOO(Leave-One-Out) 평가 프로토콜</td></tr>
</table>

<h4>본 연구의 사용자별 데이터 구성</h4>
<p>1,000명 각각에 대해 다음과 같이 데이터가 구성된다:</p>

<table>
<tr><th>구성 요소</th><th>내용</th><th>사용 목적</th></tr>
<tr><td>Source Input</td><td>Movies&amp;TV 리뷰 최근 15~30개</td><td>Profiler의 Core Pattern 추출 입력</td></tr>
<tr><td>Target Pool</td><td>Books 리뷰 5~10개 (Cold-Start)</td><td>GT 추출 대상 (입력으로 사용 안 함)</td></tr>
<tr><td><strong>GT</strong></td><td><strong>Target 중 rating ≥ 4인 가장 최근 1건</strong></td><td><strong>Transfer Judge가 Top-K에 올려야 할 정답</strong></td></tr>
<tr><td>Candidates</td><td>GT 1개 + Books 도메인 무작위 Negative 49개 = 50개 (아이템 정보: 제목 + 저자 + 카테고리 + 평점 + features 첫 50 tokens)</td><td>Transfer Judge의 랭킹 입력</td></tr>
</table>

<div class="callout">
<strong>Leakage 방지 원칙:</strong> GT로 선정된 아이템은 Profiler·Judge 입력에서 완전히 제외된다.
Target(Books) 리뷰는 전체가 입력에서 제외되며, 오직 Source(Movies&amp;TV) 리뷰만으로 선호를 추출한다.
이는 Cold-Start의 이론적 극한(Target 리뷰 0개 가정)을 시뮬레이션하는 엄격한 평가 조건이다.
</div>

<div class="callout">
<strong>Explicit Positive의 의미:</strong> rating ≥ 4 = 명시적 선호. Transfer Gate의 BLOCK 판정이
올바른 전이 차단인지 측정하려면 GT가 "사용자가 실제로 만족한 아이템"이어야 한다. Implicit
feedback(구매 자체 = positive) 방식에서는 BLOCK의 올바른 판단이 성능 하락으로 오측정되어
Transfer Gate 효과가 왜곡되므로 본 연구는 Explicit Positive를 채택하였다.
</div>

<h4>Source 리뷰 수 구간별 분포 (Overlapping User 전체)</h4>
<table>
<tr><th>구간</th><th>사용자 수</th><th>비율</th></tr>
<tr><td>1~2개</td><td>1,672,422</td><td>66.1%</td></tr>
<tr><td>3~5개</td><td>493,646</td><td>19.5%</td></tr>
<tr><td>6~10개</td><td>211,124</td><td>8.3%</td></tr>
<tr><td>11~15개</td><td>67,346</td><td>2.7%</td></tr>
<tr><td>16~20개</td><td>30,678</td><td>1.2%</td></tr>
<tr><td>21~30개</td><td>26,848</td><td>1.1%</td></tr>
<tr><td>31~50개</td><td>16,597</td><td>0.7%</td></tr>
<tr><td>51+개</td><td>12,043</td><td>0.5%</td></tr>
</table>

<h3>3.4 GT 확보율</h3>
<p><strong>분석 목적:</strong> GT(Ground Truth)로 사용할 rating ≥ 4 구매가 존재하는 사용자 비율을 확인.</p>
<p>본 연구는 Explicit Positive 방식(rating ≥ 4 중 가장 최근 구매)을 GT로 채택하였다.</p>

<table>
<tr><th>GT 방식</th><th>확보 사용자</th><th>비율</th></tr>
<tr><td>방식 A: 마지막 구매 ≥ 4점</td><td>18,898명</td><td>84.1%</td></tr>
<tr class="highlight-row"><td><strong>방식 B: ≥4점 중 가장 최근 (채택)</strong></td><td><strong>22,364명</strong></td><td><strong>99.6%</strong></td></tr>
</table>

<div class="callout-green">
<strong>판정:</strong> 채택한 방식 B로 <span class="pass">99.6%</span> GT 확보.
방식 A 대비 <strong>3,466명 추가 확보</strong>. 1,000명 샘플링 후 <strong>100% GT 확보</strong>.
</div>

<!-- ===== 4. 리뷰 수 분포 ===== -->
<h2 class="pagebreak">4. 리뷰 수 분포 분석</h2>

<p><strong>분석 목적:</strong> 최종 대상 1,000명의 도메인별 리뷰 수가 실험 설계(Source 최대 30개, Target 5~10개)와 정합하는지 확인.</p>

<h3>4.1 대상 사용자 리뷰 수 통계</h3>
<table>
<tr><th>통계량</th><th>Source (Movies &amp; TV)</th><th>Target (Books)</th></tr>
<tr><td>Mean</td><td>31.7</td><td>7.0</td></tr>
<tr><td>Median</td><td>22</td><td>7</td></tr>
<tr><td>P25</td><td>17</td><td>6</td></tr>
<tr><td>P75</td><td>33</td><td>8</td></tr>
<tr><td>P95</td><td>71</td><td>10</td></tr>
<tr><td>Min</td><td>15</td><td>5</td></tr>
<tr><td>Max</td><td>629</td><td>10</td></tr>
</table>

<div class="callout">
<strong>해석:</strong> Source 중앙값 22개로, "최신순 30개" 입력 시 대부분 사용자의 전체 또는 대부분의 리뷰가 활용된다.
Target은 5~10개 범위(Cold-Start 조건)에 정확히 분포한다.
</div>

{"<img class='chart' src='" + IMG_REVIEW_COUNT + "' />" if IMG_REVIEW_COUNT else ""}
<p class="fig-caption">Figure 2. 대상 사용자의 Source/Target 리뷰 수 분포</p>

<!-- ===== 5. 토큰 분포 ===== -->
<h2 class="pagebreak">5. 리뷰 토큰 수 분포 및 토큰 예산 검증</h2>

<p><strong>분석 목적:</strong> 리뷰당 토큰 수를 측정하여 Profiler 입력의 토큰 예산이 GPT-4o-mini context(128K) 내에 수용되는지 검증.
토크나이저는 <code>tiktoken cl100k_base</code> 사용.</p>

<h3>5.1 도메인별 토큰 통계</h3>
<table>
<tr><th>통계량</th><th>Movies &amp; TV</th><th>Books</th><th>참조값 (Amazon 2023 역산)</th></tr>
<tr><td>Mean</td><td><strong>80.4</strong></td><td><strong>67.3</strong></td><td>~58 / ~98</td></tr>
<tr><td>Median</td><td>28</td><td>30</td><td>—</td></tr>
<tr><td>P75</td><td>73</td><td>69</td><td>—</td></tr>
<tr><td>P95</td><td><strong>343</strong></td><td><strong>266</strong></td><td>—</td></tr>
<tr><td>Max</td><td>4,749</td><td>1,872</td><td>—</td></tr>
</table>

<div class="callout-warn">
<strong>발견:</strong> 평균은 참조값과 유사하나, <strong>P95가 참조값의 4~6배</strong>로 높다.
이는 소수의 장문 리뷰(영화 에세이, 독후감 등)가 분포의 꼬리를 끌어올리기 때문이다.
중앙값(28~30 tokens)과 평균(67~80 tokens) 사이의 큰 차이는 <strong>right-skewed 분포</strong>를 나타낸다.
</div>

<h3>5.2 Profiler 입력 토큰 예산 검증</h3>
<table>
<tr><th>시나리오</th><th>Source 30개</th><th>Target 10개</th><th>프롬프트</th><th>합계</th><th>GPT-4o-mini 128K</th></tr>
<tr><td>평균 기준</td><td>80 × 30 = 2,412</td><td>67 × 10 = 673</td><td>500</td><td><strong>3,585</strong></td><td class="pass">✅ 2.8%</td></tr>
<tr><td>P95 worst-case</td><td>343 × 30 = 10,290</td><td>266 × 10 = 2,658</td><td>500</td><td><strong>13,448</strong></td><td class="pass">✅ 10.5%</td></tr>
</table>

<div class="callout-green">
<strong>판정:</strong> P95 worst-case에서도 13,448 tokens으로 GPT-4o-mini 128K context의 <span class="pass">10.5%</span>만 사용.
<strong>리뷰 truncation 불필요</strong> — 전체 리뷰를 잘림 없이 입력 가능.
</div>

{"<img class='chart' src='" + IMG_TOKEN_DIST + "' />" if IMG_TOKEN_DIST else ""}
<p class="fig-caption">Figure 3. 도메인별 리뷰 토큰 수 분포 (히스토그램, 박스플롯, CDF)</p>

<!-- ===== 6. 평점 분포 ===== -->
<h2 class="pagebreak">6. 평점 분포 및 GT 확보율</h2>

<p><strong>분석 목적:</strong> 평점 분포의 편향(J-shaped skew) 정도를 확인하고,
GT 조건(rating ≥ 4) 충족 비율을 검증.</p>

<h3>6.1 도메인별 평점 분포</h3>
<table>
<tr><th>평점</th><th>Movies &amp; TV</th><th>Books</th></tr>
<tr><td>Rating ≥ 4 비율</td><td><strong>79.5%</strong></td><td><strong>85.0%</strong></td></tr>
</table>

<div class="callout">
<strong>해석:</strong> 양쪽 도메인 모두 고평점 편향(J-shaped)을 보이며, 4점 이상이 79~85%를 차지한다.
이는 Amazon 리뷰 데이터의 일반적 특성이다. GT(rating ≥ 4) 확보에 유리한 분포이다.
</div>

{"<img class='chart' src='" + IMG_RATING + "' />" if IMG_RATING else ""}
<p class="fig-caption">Figure 4. 도메인별 평점 분포</p>

<h3>6.2 GT 확보율 상세</h3>
<table>
<tr><th>기준</th><th>마지막 구매 기준</th></tr>
<tr><td>평점 ≥ 3.0</td><td>916명 (91.6%)</td></tr>
<tr><td>평점 ≥ 3.5</td><td>844명 (84.4%)</td></tr>
<tr><td>평점 ≥ 4.0</td><td>844명 (84.4%)</td></tr>
<tr><td>평점 ≥ 4.5</td><td>718명 (71.8%)</td></tr>
<tr><td>평점 ≥ 5.0</td><td>718명 (71.8%)</td></tr>
</table>

<p>채택한 방식 B(rating ≥ 4 중 가장 최근)로 전환하면 <strong>1,000명 전원(100%) GT 확보</strong>.</p>

<!-- ===== 7. 시간 분포 ===== -->
<h2 class="pagebreak">7. 시간 분포 및 시점 타당성</h2>

<p><strong>분석 목적:</strong> 리뷰가 너무 오래되어 현재 선호를 반영하지 못하는 사용자가 얼마나 되는지 확인.
선행연구(TALLRec, LLM4CDR, EMCDR, TrineCDR) 4편 모두 날짜 필터를 적용하지 않았으므로,
본 연구도 동일하되 시점 분포를 보고하여 타당성을 문서화한다.</p>

<h3>7.1 마지막 리뷰 시점</h3>
<table>
<tr><th>통계량</th><th>Source (Movies)</th><th>Target (Books)</th><th>어느 도메인이든</th></tr>
<tr><td>가장 오래된</td><td>2000-05-18</td><td>2000-02-24</td><td>2000-05-18</td></tr>
<tr><td>중앙값</td><td><strong>2019-04-14</strong></td><td><strong>2018-11-24</strong></td><td><strong>2020-08-29</strong></td></tr>
<tr><td>가장 최근</td><td>2023-05-31</td><td>2023-05-04</td><td>2023-05-31</td></tr>
</table>

<h3>7.2 날짜 필터 필요 여부</h3>
<table>
<tr><th>기준</th><th>결과</th><th>판정</th></tr>
<tr><td>2018년 이전 사용자 비율</td><td><strong>25.8%</strong></td><td class="pass">30% 미만 → 필터 불필요</td></tr>
<tr><td>Source-Target 시점 갭 중앙값</td><td><strong>1.2년</strong></td><td class="pass">3년 미만 → 전이 타당성 유지</td></tr>
<tr><td>시점 갭 5년 이상</td><td>96명 (9.6%)</td><td>소수 → 허용 범위</td></tr>
</table>

<h3>7.3 최신순 30개의 시간 범위</h3>
<table>
<tr><th>통계량</th><th>값</th></tr>
<tr><td>평균</td><td>5.3년</td></tr>
<tr><td>중앙값</td><td>4.6년</td></tr>
<tr><td>P25</td><td>2.4년</td></tr>
<tr><td>P75</td><td>7.4년</td></tr>
</table>

<div class="callout-green">
<strong>판정:</strong> 날짜 필터 미적용. 2018년 이전 사용자 <span class="pass">25.8%</span>(30% 미만),
Source-Target 시점 갭 중앙값 <span class="pass">1.2년</span>으로 전이 타당성 유지.
선행연구 4편 모두 날짜 필터를 적용하지 않았으므로 일관된 프로토콜.
</div>

{"<img class='chart' src='" + IMG_RECENCY + "' />" if IMG_RECENCY else ""}
<p class="fig-caption">Figure 5. 마지막 리뷰 연도 분포 (좌), Source-Target 시점 scatter (중), 시점 갭 분포 (우)</p>

<!-- ===== 8. 메타데이터 품질 ===== -->
<h2 class="pagebreak">8. 메타데이터 품질 분석</h2>

<p><strong>분석 목적:</strong> 후보 아이템 정보 구성에 필요한 메타데이터 필드의 결측률과 품질을 확인.</p>

<h3>8.1 Books 메타데이터 결측률</h3>
<table>
<tr><th>필드</th><th>결측률</th><th>용도</th></tr>
<tr><td>title</td><td class="pass">0.0%</td><td>후보 아이템 표시 (필수)</td></tr>
<tr><td>average_rating</td><td class="pass">0.0%</td><td>후보 아이템 품질 지표 (필수)</td></tr>
<tr><td>categories</td><td class="pass">0.0%</td><td>장르/카테고리 (필수)</td></tr>
<tr><td>features (줄거리)</td><td class="pass">11.7%</td><td>책 내용 파악 (선택적 추가)</td></tr>
<tr><td><strong>author_name (수정 후)</strong></td><td class="pass"><strong>27.4%</strong></td><td><strong>저자명 — brand_loyalty 판단 근거 (수정된 파싱으로 72.6% 추출 가능)</strong></td></tr>
<tr><td>publisher</td><td>12.7%</td><td>출판 정보</td></tr>
<tr><td>pub_date</td><td class="warn">92.8%</td><td>출판일 — 대부분 누락</td></tr>
<tr><td>language</td><td>11.1%</td><td>언어</td></tr>
</table>

<div class="callout">
<strong>author_name 파싱 수정 이력:</strong><br>
최초 EDA에서 <code>author</code> 필드를 dict로 가정하고 <code>isinstance(author_val, dict)</code>로 검사하여
100% 결측으로 측정되었으나, 재검증 결과 실제 타입은 <code>str</code>(dict를 문자열로 직렬화한 형태)임이 확인되었다.
예: <code>"{{'avatar': '...', 'name': 'Peter Ackroyd', 'about': [...]}}"</code><br><br>
수정된 파싱 로직(<code>ast.literal_eval</code>을 통한 dict 복원 후 <code>name</code> 키 추출):
<ul>
  <li>NULL(저자 정보 없음): <strong>27.4%</strong></li>
  <li>정상 추출: <strong>72.6%</strong></li>
  <li>파싱 실패: 0.0%</li>
</ul>
→ <strong>후보 아이템 정보에 저자명 포함 가능</strong>. brand_loyalty Core Pattern 판단 근거로 활용.
</div>

<h3>8.2 Movies &amp; TV 메타데이터 결측률</h3>
<table>
<tr><th>필드</th><th>결측률</th><th>비고</th></tr>
<tr><td>title</td><td class="warn">42.0%</td><td>높은 결측 — 본 연구에서는 Books 후보만 사용</td></tr>
<tr><td>average_rating</td><td class="pass">0.0%</td><td>—</td></tr>
<tr><td>director</td><td>29.6%</td><td>—</td></tr>
<tr><td>actors</td><td>27.6%</td><td>—</td></tr>
<tr><td>release_date</td><td class="warn">63.4%</td><td>—</td></tr>
<tr><td>runtime</td><td class="warn">63.5%</td><td>—</td></tr>
<tr><td>description</td><td class="warn">42.0%</td><td>—</td></tr>
</table>

<div class="callout">
<strong>해석:</strong> Books의 핵심 필드(title, average_rating, categories)는 결측률 0%.
features(줄거리)도 88.3% 존재. 후보 아이템 정보 구성에 충분하다.<br>
<strong>author_name 100% 결측</strong>은 <code>author</code> dict 구조의 파싱 문제로 추정 — 별도 확인 필요.
</div>

<h3>8.3 description vs features 품질 비교</h3>
<p>EDA에서 description과 features 필드의 내용을 샘플링하여 비교한 결과:</p>

<table>
<tr><th>필드</th><th>실제 내용</th><th>품질</th></tr>
<tr><td><code>description</code></td><td>"Review ...", "About the Author ...", 빈 값</td><td class="warn">부적합</td></tr>
<tr class="highlight-row"><td><code>features</code></td><td>책 소개, 줄거리 요약, 핵심 내용</td><td class="pass">적합</td></tr>
</table>

<div class="callout">
<strong>description 예시:</strong> "Review 'This uplifting story will have you cheering...'" (리뷰 인용)<br>
<strong>features 예시:</strong> "In the year 2032, eighty-year-old Moira Burke watches as life on Earth becomes a series of natural disasters..." (실제 줄거리)
</div>

<h3>8.4 features 토큰 통계</h3>
<table>
<tr><th>통계량</th><th>값</th></tr>
<tr><td>존재율</td><td>88.3%</td></tr>
<tr><td>Mean</td><td>183.0 tokens</td></tr>
<tr><td>Median</td><td>155 tokens</td></tr>
<tr><td>P95</td><td>455 tokens</td></tr>
</table>

{"<img class='chart' src='" + IMG_CATEGORY + "' />" if IMG_CATEGORY else ""}
<p class="fig-caption">Figure 6. Books 도메인 상위 카테고리 분포</p>

<!-- ===== 9. 후보 아이템 토큰 ===== -->
<h2 class="pagebreak">9. 후보 아이템 토큰 검증</h2>

<p><strong>분석 목적:</strong> Transfer Judge에 입력되는 50개 후보 아이템의 총 토큰이 예산 내인지 확인.</p>

<h3>9.1 후보 아이템 텍스트 형식</h3>
<p>현재 형식: <code>제목 | 카테고리 | Rating: X.X</code></p>

<table>
<tr><th>통계량</th><th>값</th></tr>
<tr><td>아이템당 Mean</td><td>20.0 tokens</td></tr>
<tr><td>아이템당 Median</td><td>18 tokens</td></tr>
<tr><td>아이템당 P95</td><td>37 tokens</td></tr>
<tr><td>50개 총 토큰 (평균)</td><td><strong>998 tokens</strong></td></tr>
<tr><td>50개 총 토큰 (P95)</td><td>1,850 tokens</td></tr>
</table>

<div class="callout-green">
<strong>판정:</strong> 후보 50개 토큰 <span class="pass">~1,000 tokens</span>으로 실험 설계 예상치(~2,500) 이하.
features(줄거리) 첫 50 tokens를 추가해도 ~3,500 tokens으로 예산 내.
</div>

<h3>9.2 features 추가 시 토큰 예산</h3>
<table>
<tr><th>구성</th><th>아이템당</th><th>50개 합계</th></tr>
<tr><td>(A) 제목 + 카테고리 + 평점</td><td>~20</td><td>~1,000</td></tr>
<tr><td>(B) + features 첫 50 tokens</td><td>~70</td><td>~3,500</td></tr>
</table>

{"<img class='chart' src='" + IMG_CANDIDATE + "' />" if IMG_CANDIDATE else ""}
<p class="fig-caption">Figure 7. 후보 아이템 1개당 토큰 수 분포</p>

<!-- ===== 10. 종합 판정 ===== -->
<h2 class="pagebreak">10. 종합 판정 및 설계 결정</h2>

<h3>10.1 EDA 체크리스트</h3>
<table>
<tr><th>판정</th><th>검증 항목</th><th>결과</th></tr>
<tr><td class="pass">✅</td><td>Overlapping User ≥ 1,000명</td><td>22,465명 (22배 여유)</td></tr>
<tr><td class="pass">✅</td><td>GT 확보율 (rating≥4 중 최근)</td><td>99.6% (1,000명 샘플 후 100%)</td></tr>
<tr><td class="pass">✅</td><td>Profiler 토큰 P95 worst-case</td><td>13,448 tokens (128K의 10.5%)</td></tr>
<tr><td class="pass">✅</td><td>리뷰 truncation 불필요</td><td>GPT-4o-mini 128K context 충분</td></tr>
<tr><td class="pass">✅</td><td>날짜 필터 불필요</td><td>2018년 이전 25.8% (30% 미만)</td></tr>
<tr><td class="pass">✅</td><td>Source-Target 시점 갭</td><td>중앙값 1.2년 (3년 미만)</td></tr>
<tr><td class="pass">✅</td><td>메타 title+rating 사용 가능</td><td>결측률 0%</td></tr>
<tr><td class="pass">✅</td><td>features(줄거리) 존재율</td><td>88.3%</td></tr>
<tr><td class="pass">✅</td><td>후보 50개 토큰</td><td>~1,000 tokens (예산 내)</td></tr>
<tr><td class="pass">✅</td><td>author_name 추출</td><td>72.6% 존재 (str 파싱 수정 후 재측정). NULL 27.4%는 원본 데이터에 저자 정보 없음</td></tr>
</table>

<h3>10.2 주요 설계 결정</h3>
<table>
<tr><th>결정 사항</th><th>선택</th><th>근거</th></tr>
<tr><td>GT 선정 방식</td><td>rating ≥ 4 중 가장 최근 (Explicit Positive)</td><td>Transfer Gate BLOCK 효과 정확 측정. 기존 방식 대비 +3,466명 확보</td></tr>
<tr><td>날짜 필터</td><td>미적용</td><td>선행연구 4편 동일. 2018년 이전 25.8%로 허용 범위</td></tr>
<tr><td>리뷰 truncation</td><td>미적용 (전체 사용)</td><td>P95 worst-case 13,448 tokens → GPT-4o-mini 128K의 10.5%</td></tr>
<tr><td>후보 아이템 정보</td><td>제목 + 저자 + 카테고리 + 평점 + features 50 tokens</td><td>features(줄거리 88.3%) + author_name(72.6%, str 파싱 수정 후) 포함. description은 품질 부적합으로 제외</td></tr>
<tr><td>description 제외</td><td>미사용</td><td>리뷰 인용, 저자 소개 등 비정형 내용 혼재. EDA에서 확인</td></tr>
</table>

<h3>10.3 논문용 Dataset Statistics</h3>
<table>
<tr><th>항목</th><th>Movies &amp; TV</th><th>Books</th></tr>
<tr><td>Total Reviews</td><td>17,327,095</td><td>29,467,817</td></tr>
<tr><td>Unique Users</td><td>6,502,818</td><td>10,292,988</td></tr>
<tr><td>Unique Items</td><td>747,764</td><td>4,446,065</td></tr>
<tr><td>Overlapping Users (sampled)</td><td colspan="2" style="text-align:center">1,000</td></tr>
<tr><td>Reviews per User (mean)</td><td>31.7</td><td>7.0</td></tr>
<tr><td>Tokens per Review (mean)</td><td>80.4</td><td>67.3</td></tr>
<tr><td>Tokens per Review (P95)</td><td>343</td><td>266</td></tr>
<tr><td>Input Reviews (max)</td><td>30</td><td>10</td></tr>
<tr><td>Rating ≥ 4 (%)</td><td>79.5%</td><td>85.0%</td></tr>
<tr><td>Data Period</td><td>1997-08 ~ 2023-09</td><td>1996-06 ~ 2023-09</td></tr>
<tr><td>Last Review Median Year</td><td colspan="2" style="text-align:center">2020</td></tr>
<tr><td>Features (synopsis) Rate</td><td>N/A</td><td>88.3%</td></tr>
</table>

<!-- ===== 11. 추가 검증 ===== -->
<h2 class="pagebreak">11. 추가 검증 (GAP-1, GAP-2, GAP-4)</h2>

<p>본 섹션은 실험 계획서와 EDA 보고서의 격차 분석에서 식별된 3가지 검증 항목을 추가로 다룬다.
계획서의 핵심 가정과 자기 설계의 데이터 근거, 평가 공정성을 정량적으로 확인한다.</p>

<table>
<tr><th>GAP</th><th>검증 대상</th><th>왜 중요한가</th></tr>
<tr><td><strong>GAP-2</strong></td><td>사용자별 Source 평점 다양성</td><td>Profiler가 polarity=negative 패턴을 추출할 수 있는지 데이터로 검증 (계획서 §5.5 설계 근거)</td></tr>
<tr><td><strong>GAP-1</strong></td><td>Source-Target Top-Genre 매핑</td><td>Cross-Domain 전이의 데이터 근거. CDR의 핵심 가정을 시각적으로 증명</td></tr>
<tr><td><strong>GAP-4</strong></td><td>GT vs Negative 후보 분포 비교</td><td>평가 공정성. 단순 카테고리/평점 정렬로 GT가 풀리지 않는지 확인</td></tr>
</table>

<!-- ===== GAP-2 ===== -->
<h3>11.1 GAP-2 — 사용자별 Source 평점 다양성</h3>

<p><strong>분석 목적:</strong> Profiler 설계에 따르면 낮은 평점(rating ≤ 2) 리뷰도 polarity=negative 패턴 추출에 활용된다.
실제 데이터에서 이러한 비선호 신호가 충분히 존재하는지 검증한다.</p>

<table>
<tr><th>지표</th><th>값</th><th>의미</th></tr>
<tr><td>사용자별 Source 평점 표준편차 (mean)</td><td><strong>0.90</strong> (P25 0.54 / P75 1.25)</td><td>대부분 사용자가 평점을 다양하게 매김 (단일 평점만 주는 경우 드뭄)</td></tr>
<tr><td>rating ≤ 2 리뷰를 1개 이상 보유한 사용자 비율</td><td class="pass"><strong>64.2%</strong></td><td>강한 비선호 신호(2점 이하) 보유 사용자가 다수</td></tr>
<tr><td>rating ≤ 3 리뷰를 1개 이상 보유한 사용자 비율</td><td class="pass"><strong>81.6%</strong></td><td>거의 모든 사용자가 mild negative 신호 보유</td></tr>
<tr><td>평균 사용자의 rating ≤ 2 리뷰 비중</td><td>11.1%</td><td>평균적으로 리뷰의 약 1/10이 강한 negative</td></tr>
<tr><td>평균 사용자의 rating ≤ 3 리뷰 비중</td><td>19.9%</td><td>평균적으로 리뷰의 약 1/5이 비선호 신호</td></tr>
</table>

{"<img class='chart' src='" + IMG_RATING_DIV + "' />" if IMG_RATING_DIV else ""}
<p class="fig-caption">Figure 8. (a) 사용자별 Source 평점 표준편차 / (b) 비선호 신호 보유 사용자 수 / (c) ≤3점 비중 분포</p>

<div class="callout-green">
<strong>판정:</strong> <span class="pass">Profiler의 polarity=negative 추출 가능성 충분히 입증</span>.
사용자의 64%가 강한 negative(≤2점) 신호를, 82%가 mild negative(≤3점) 신호를 보유.
Profiler는 이러한 비선호 신호를 통해 "사용자가 무엇을 싫어하는지"까지 패턴화할 수 있으며,
이는 Judge의 BLOCK/PARTIAL 판정에 활용된다 (계획서 §5.5).
</div>

<!-- ===== GAP-1 ===== -->
<h3>11.2 GAP-1 — Source(Movies) ↔ Target(Books) Top-Genre 매핑</h3>

<p><strong>분석 목적:</strong> Cross-Domain Recommendation의 핵심 가정인 "도메인 간 선호 패턴이 부분 전이됨"을 데이터로 확인한다.
각 사용자의 Source/Target 도메인에서 가장 많이 본 장르(top-1) 쌍을 추출하여 매핑 패턴을 분석한다.</p>

<table>
<tr><th>지표</th><th>값</th></tr>
<tr><td>Source/Target 모두에서 top-genre 추출 가능한 사용자</td><td><strong>983 / 1,000명 (98.3%)</strong></td></tr>
<tr><td>Top-10 × Top-10 매핑된 사용자 쌍</td><td>707쌍</td></tr>
<tr><td>동일 명칭 직접 매칭 (예: Sci-Fi 영화 → Sci-Fi 책)</td><td class="warn"><strong>0건</strong></td></tr>
</table>

<div class="callout-warn">
<strong>핵심 발견:</strong> Movies와 Books의 카테고리 분류 체계가 서로 달라 동일 명칭으로 직접 매칭되는 경우는 0건이다.
예를 들어 Movies는 "Science Fiction", "Drama", "Comedy"로 분류되지만,
Books는 "Literature & Fiction", "Mystery, Thriller & Suspense", "Children's Books" 등으로 분류된다.
<br><br>
이는 본 연구의 <strong>PARTIAL 판정의 필요성을 데이터로 직접 증명</strong>한다.
"동일 장르 직접 전이"는 데이터상 불가능하며, 의미적 연관성을 가진 PARTIAL 매핑이 본질적으로 요구된다.
</div>

<h4>주요 매핑 패턴 (Movies 장르 → 가장 많이 매핑된 Books 장르 Top 1)</h4>
<table>
<tr><th>Movies 장르</th><th>가장 많이 매핑된 Books 장르</th><th>비율 (n / 매핑 사용자 수)</th><th>의미</th></tr>
<tr class="highlight-row"><td>Suspense</td><td>Literature & Fiction</td><td>33.3% (13/39)</td><td>스릴러 영화 → 문학 소설</td></tr>
<tr class="highlight-row"><td>Comedy</td><td>Children's Books</td><td>28.0% (21/75)</td><td>코미디 영화 → 아동 도서 (가족 단위 사용자 추정)</td></tr>
<tr class="highlight-row"><td>Genre for Featured Categories</td><td>Literature & Fiction</td><td>25.9% (29/112)</td><td>일반 영화 → 일반 문학</td></tr>
<tr class="highlight-row"><td>Science Fiction</td><td>Literature & Fiction</td><td>25.0% (4/16)</td><td>SF 영화 → 문학 (SF 책이 Lit&Fic 산하 분류)</td></tr>
<tr class="highlight-row"><td>Drama</td><td>Mystery, Thriller & Suspense</td><td>22.8% (18/79)</td><td>드라마 영화 → 스릴러 책 (서사 선호 매핑)</td></tr>
<tr><td>Documentary</td><td>Literature & Fiction</td><td>23.1% (3/13)</td><td>다큐멘터리 → 문학</td></tr>
<tr><td>Action</td><td>Children's Books</td><td>36.4% (4/11)</td><td>액션 영화 → 아동 도서 (가족 단위)</td></tr>
</table>

{"<img class='chart' src='" + IMG_CROSS_DOMAIN + "' />" if IMG_CROSS_DOMAIN else ""}
<p class="fig-caption">Figure 9. (a) Movies × Books Top-10 장르 cross-tabulation 절대값 / (b) 행 정규화 (Movies 장르 → Books 장르 조건부 확률)</p>

<div class="callout-green">
<strong>판정:</strong> <span class="pass">CDR의 데이터 근거 확보</span>.
98.3% 사용자가 양 도메인에서 top-genre 추출 가능하며, 도메인 간 비자명한 매핑 패턴이 관찰된다
(Drama→Mystery·Thriller, Suspense→Literature, Comedy→Children's 등).
다만 동일 명칭 직접 매칭이 0건이라는 사실은 <strong>Transfer Gate의 PARTIAL 판정이 단순 옵션이 아니라 데이터상 필수임을 증명</strong>한다.
</div>

<!-- ===== GAP-4 ===== -->
<h3>11.3 GAP-4 — GT vs Negative 후보 분포 비교 (평가 공정성)</h3>

<p><strong>분석 목적:</strong> 평가 시 GT가 단순 카테고리·평점 정렬로 식별되지 않는지 확인하여 평가의 공정성을 검증한다.
1,000명의 GT 1개씩 (총 1,000건) vs Negative 후보 49개씩 (총 ~49,000건)의 분포를 비교한다.</p>

<table>
<tr><th>비교 항목</th><th>GT (n=931)</th><th>Negative (n=42,999)</th><th>차이/검정</th></tr>
<tr><td>평균 평점</td><td>4.55</td><td>4.40</td><td>+0.15 (작은 차이)</td></tr>
<tr><td>KS Test (분포 차이)</td><td colspan="2" style="text-align:center">statistic = <strong>0.158</strong></td><td>p-value = 3.2e-20</td></tr>
<tr><td>GT 카테고리 분포 vs Neg 카테고리 분포</td><td colspan="2" style="text-align:center">Top-10 장르가 거의 동일</td><td>Figure 10 참조</td></tr>
</table>

{"<img class='chart' src='" + IMG_GT_VS_NEG + "' />" if IMG_GT_VS_NEG else ""}
<p class="fig-caption">Figure 10. (a) Top-10 Books 장르 비율 비교 (GT vs Negative) / (b) 아이템 평균 평점 분포 비교 (KS=0.158)</p>

<div class="callout-green">
<strong>판정:</strong> <span class="pass">평가 공정성 확보</span>.
<ul>
  <li><strong>평점 차이 0.15</strong>는 통계적으로 유의(p&lt;0.001)하나 절대값이 작아 단순 평점 정렬로 GT 식별 불가.
  GT 평점 분포의 P25-P75가 Negative 분포와 크게 겹침.</li>
  <li><strong>카테고리 분포는 GT와 Negative가 거의 동일</strong> (Top-10 장르 비율이 유사).
  단순 카테고리 빈도 기반 추천으로는 GT를 우선순위화 불가.</li>
  <li><strong>KS statistic 0.158</strong>은 분포 차이가 작음을 시사. 큰 차이가 있다면 0.3+ 수준이어야 함.</li>
</ul>
→ Top-K 추천 정확도(HR@K, NDCG@K)는 <strong>패턴 매칭 능력</strong>에서 의미 있게 측정되며,
단순 baseline(평점 정렬, 카테고리 매칭)이 우연히 좋은 성능을 내는 leakage는 차단된다.
</div>

<h3>11.4 추가 검증 종합</h3>

<table>
<tr><th>GAP</th><th>검증 결과</th><th>설계상 함의</th></tr>
<tr><td>GAP-2 (평점 다양성)</td><td class="pass">≤2점 보유 64.2%, ≤3점 보유 81.6%</td><td>Profiler의 polarity=negative 패턴 추출 가능. 계획서 §5.5의 "낮은 평점 리뷰도 활용" 정당화</td></tr>
<tr><td>GAP-1 (도메인 매핑)</td><td class="pass">98.3% 매핑 가능 / 동일 명칭 매칭 0건</td><td>CDR 가능성 확인 + <strong>PARTIAL 판정 필수성</strong> 데이터 증명. 계획서 §8 Transfer Gate 3단계 정당화 강화</td></tr>
<tr><td>GAP-4 (평가 공정성)</td><td class="pass">평점 차이 0.15, 카테고리 분포 유사</td><td>단순 baseline으로 GT 식별 불가. HR@K/NDCG@K가 진짜 모델 성능을 측정</td></tr>
</table>

</body>
</html>
"""

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc = weasyprint.HTML(string=HTML_CONTENT)
    doc.write_pdf(OUTPUT_PATH)
    print(f"PDF generated: {OUTPUT_PATH}")
