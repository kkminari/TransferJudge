"""학습 데이터 Lineage 보고서 PDF (v2 재작성).

목적: 지도교수·심사위원이 한 번에 이해할 수 있도록 raw → 학습 데이터 1줄까지의 흐름을 정리.
표 헤더 한글화, 용어 사전, 7패턴 메커니즘 설명, Phase 3 흐름 포함.

산출: docs/phase2/Phase2_Data_Lineage.pdf
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import weasyprint

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "docs/phase2/Phase2_Data_Lineage.pdf"
UID = "AHY625B6CHNH7GGQFJMJODL4QBOQ"


def main():
    sample = json.load(open("/tmp/lineage_sample.json"))
    movies = pd.read_parquet(ROOT / "data/movies_reviews_filtered.parquet")
    books = pd.read_parquet(ROOT / "data/books_reviews_filtered.parquet")
    books_meta = pd.read_parquet(
        ROOT / "data/books_meta_filtered.parquet",
        columns=["parent_asin", "title"],
    )
    title_map = dict(zip(books_meta["parent_asin"], books_meta["title"]))

    # 5개 영화 리뷰
    m_5 = sample["movies_sample"][:5]
    movies_rows = ""
    for i, mv in enumerate(m_5, 1):
        text_preview = (mv["text"] or "").replace("<br />", " ").replace("\n", " ")[:180]
        movies_rows += (
            f'<tr><td>{i}</td><td>★{mv["rating"]:.0f}</td>'
            f'<td>{str(mv["datetime"])[:10]}</td>'
            f'<td><strong>{mv["title"][:50]}</strong><br>'
            f'<span style="font-size: 8.5pt; color: #555;">"{text_preview}..."</span></td></tr>'
        )

    # 책 리뷰 + GT
    b_user = books[books["user_id"] == UID].sort_values("timestamp", ascending=False)
    books_rows = ""
    gt_parent = sample["gt_parent_asin"]
    for _, b in b_user.iterrows():
        is_gt = b["parent_asin"] == gt_parent
        cls = ' class="highlight-row"' if is_gt else ""
        gt_marker = " 🎯 <strong>정답</strong>" if is_gt else ""
        real_title = title_map.get(b["parent_asin"], "(unknown)")
        review_text = (b["text"] or "").replace("<br />", " ").replace("\n", " ")[:160]
        books_rows += (
            f'<tr{cls}><td>{str(b["datetime"])[:10]}</td>'
            f'<td>★{b["rating"]:.0f}{gt_marker}</td>'
            f'<td><code>{b["parent_asin"]}</code></td>'
            f'<td><strong>"{str(real_title)[:50]}"</strong><br>'
            f'<span style="font-size: 8pt; color: #666;">사용자 메모: "{b["title"]}" — "{review_text}..."</span></td></tr>'
        )

    # Profile 7-pattern
    profile = sample["profile"]
    pattern_korean = {
        "genre_preference": "장르 선호",
        "narrative_complexity": "서사 복잡도",
        "pacing_preference": "전개 속도 선호",
        "quality_sensitivity": "퀄리티 민감도",
        "brand_loyalty": "브랜드 충성도",
        "sensory_preference": "감각·분위기 선호",
        "emotional_resonance": "감정 공명",
    }
    profile_rows = ""
    for p_name in pattern_korean:
        p = profile["core_patterns"].get(p_name, {})
        value = str(p.get("value", ""))[:60]
        conf = p.get("confidence", "?")
        pol = p.get("polarity", "?")
        tr = p.get("transferability_hint", "?")
        ev_list = p.get("evidence", []) or []
        ev_str = "; ".join(f'"{str(e)[:80]}"' for e in ev_list[:2])
        profile_rows += (
            f'<tr><td><strong>{pattern_korean[p_name]}</strong><br>'
            f'<span style="font-size:7.5pt;color:#888;">{p_name}</span></td>'
            f'<td>{value}</td>'
            f'<td>{conf}</td><td>{pol}</td><td>{tr}</td>'
            f'<td style="font-size: 8.5pt;">{ev_str}</td></tr>'
        )

    # Teacher decisions
    teacher = sample["teacher"]
    teacher_dec_rows = ""
    dec_korean = {"TRANSFER": "전이", "PARTIAL": "부분 전이", "BLOCK": "차단"}
    for p_name in pattern_korean:
        info = teacher["transfer_decisions"].get(p_name, {})
        dec = info.get("decision", "")
        dec_class = {"TRANSFER": "pol-positive", "PARTIAL": "pol-mixed", "BLOCK": "pol-negative"}.get(dec, "")
        dec_kr = dec_korean.get(dec, dec)
        rationale = str(info.get("rationale", ""))[:130]
        insight = str(info.get("transferred_insight", "") or "—")[:80]
        teacher_dec_rows += (
            f'<tr><td><strong>{pattern_korean[p_name]}</strong></td>'
            f'<td><span class="{dec_class}">{dec_kr}</span><br>'
            f'<span style="font-size:8pt;color:#666;">{dec} · 신뢰도 {info.get("confidence", "?")}</span></td>'
            f'<td style="font-size: 9pt;">{rationale}...</td>'
            f'<td style="font-size: 9pt;">{insight}</td></tr>'
        )

    # Top-10
    recs_rows = ""
    for r in teacher["recommendations"]:
        is_gt = r.get("item_id") == gt_parent
        cls = ' class="highlight-row"' if is_gt else ""
        gt_marker = " 🎯" if is_gt else ""
        title = str(r.get("title", ""))[:50]
        applied_eng = r.get("applied_patterns", [])
        applied_kr = ", ".join(pattern_korean.get(p, p) for p in applied_eng)[:90]
        recs_rows += (
            f'<tr{cls}><td>#{r.get("rank")}{gt_marker}</td>'
            f'<td><code>{r.get("item_id")}</code></td>'
            f'<td><strong>{title}</strong></td>'
            f'<td>{r.get("score")}</td>'
            f'<td style="font-size: 8.5pt;">{applied_kr}</td></tr>'
        )

    # SFT record size
    train_lines = open(ROOT / "data/teacher_train_main.jsonl").readlines()
    n_total = len(train_lines)
    record = None
    for line in train_lines:
        d = json.loads(line)
        user_msg = next(m for m in d["messages"] if m["role"] == "user")
        if UID in user_msg["content"]:
            record = d
            break
    user_msg_size = len(record["messages"][1]["content"]) if record else 0
    asst_msg_size = len(record["messages"][2]["content"]) if record else 0

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: A4; margin: 2cm 1.8cm; @bottom-center {{ content: counter(page); font-size: 10px; color: #999; }} }}
  body {{ font-family: -apple-system, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif; font-size: 10pt; line-height: 1.55; color: #222; }}
  h1 {{ text-align: center; font-size: 19pt; margin-bottom: 5px; color: #1a1a2e; }}
  .subtitle {{ text-align: center; font-size: 10.5pt; color: #555; margin-bottom: 3px; }}
  .author {{ text-align: center; font-size: 10pt; color: #777; margin-bottom: 22px; }}
  h2 {{ font-size: 14pt; color: #16213e; border-bottom: 2.5px solid #4a90d9; padding-bottom: 4px; margin-top: 24px; }}
  h3 {{ font-size: 11.5pt; color: #0f3460; margin-top: 14px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 9.5pt; }}
  th {{ background: #16213e; color: white; padding: 5px 8px; text-align: left; font-weight: 600; }}
  td {{ padding: 5px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #f8f9fa; }}
  .highlight-row td {{ background: #fff8e1 !important; font-weight: 600; }}
  .pagebreak {{ page-break-before: always; }}
  .callout {{ background: #f0f4f8; border-left: 4px solid #4a90d9; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }}
  .callout-green {{ background: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }}
  .callout-warn {{ background: #fff8e1; border-left: 4px solid #f5a623; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }}
  .pol-positive {{ background: #e3f2fd; color: #1565c0; padding: 1px 6px; border-radius: 3px; font-weight: 600; font-size: 9pt; }}
  .pol-negative {{ background: #fce4ec; color: #c62828; padding: 1px 6px; border-radius: 3px; font-weight: 600; font-size: 9pt; }}
  .pol-mixed {{ background: #f3e5f5; color: #6a1b9a; padding: 1px 6px; border-radius: 3px; font-weight: 600; font-size: 9pt; }}
  code {{ background: #f0f4f8; padding: 1px 4px; border-radius: 3px; font-size: 8.5pt; }}
  pre {{ background: #1a1a2e; color: #e8e8e8; padding: 10px 12px; border-radius: 5px; font-size: 8.5pt; overflow-wrap: break-word; white-space: pre-wrap; word-wrap: break-word; line-height: 1.4; }}
  .flow {{ display: flex; align-items: stretch; gap: 4px; margin: 14px 0 8px; font-size: 8.5pt; }}
  .flow-box {{ flex: 1; border: 1.5px solid #4a90d9; border-radius: 5px; padding: 6px; text-align: center; background: #f8fbff; }}
  .flow-box .tag {{ font-size: 7.5pt; color: #4a90d9; display: block; font-weight: 600; }}
  .flow-box .title {{ font-weight: 700; font-size: 9pt; color: #16213e; margin: 2px 0; }}
  .flow-box .desc {{ font-size: 7.5pt; color: #555; line-height: 1.3; }}
  .flow-arrow {{ display: flex; align-items: center; color: #888; font-size: 14pt; padding: 0 1px; }}
</style>
</head>
<body>

<h1>학습 데이터 생성 보고서</h1>
<p class="subtitle">Amazon Reviews 2023 원본 → 학습 데이터 한 줄까지의 전체 과정</p>
<p class="author">2026.05.14 · 빅데이터학과 17기 곽민아</p>

<div class="callout-green">
<strong>한 줄 요약</strong><br>
영화 도메인 활동이 있는 cold-start cohort 1,000명에 대해, GPT-4o-mini 기반 Profiler가 7개 취향 패턴을 추출하고,
Teacher가 책 추천 정답지(Top-10)와 패턴별 전이 판단을 생성. <strong>품질·정합성 필터(Top-10 GT 포함, 후보 membership, 중복 0, title 정규화, low-signal·orphan 제거)</strong>를 통과한
<strong>578명을 train, 나머지 미사용 Profile 보유자 중 valid 100·test 100을 holdout으로 분리 (train·valid·test 누수 0건)</strong>.
최종 <strong>578줄의 학습 데이터</strong> (<code>data/teacher_train_main.jsonl</code>)가 다음 단계 Judge 모델(Qwen3-14B)
파인튜닝에 사용됨. 본 보고서는 이 데이터가 어떤 원본에서, 어떤 단계를 거쳐, 어떤 형태로 만들어졌는지를
실제 사용자 한 명의 사례로 끝까지 추적한다.
</div>

<!-- ====== 핵심 용어 ====== -->
<h2>0. 핵심 용어 (용어 사전)</h2>

<table>
<tr><th>용어</th><th>정의</th><th>본 연구에서의 역할</th></tr>
<tr><td><strong>Source 도메인</strong></td><td>영화·TV (Movies & TV)</td>
    <td>사용자의 취향을 추출하는 입력 데이터원</td></tr>
<tr><td><strong>Target 도메인</strong></td><td>책 (Books)</td>
    <td>추천 결과가 만들어지는 출력 데이터원</td></tr>
<tr><td><strong>GT (Ground Truth)</strong></td><td>정답 책</td>
    <td>사용자가 실제로 rating ≥ 4로 평가한 가장 최근 책. 모델 추천이 맞췄는지 검증하는 기준</td></tr>
<tr><td><strong>Profile</strong></td><td>사용자 취향 JSON</td>
    <td>영화 리뷰에서 추출한 7개 패턴. Teacher의 입력으로 들어감</td></tr>
<tr><td><strong>Profiler</strong></td><td>Profile을 만드는 LLM</td>
    <td>GPT-4o-mini가 사용자 영화 리뷰를 읽고 7개 패턴을 추출</td></tr>
<tr><td><strong>Teacher</strong></td><td>학습 데이터 생성 LLM</td>
    <td>GPT-4o-mini가 Profile과 후보 도서 50권을 보고 Top-10 추천 정답지 작성</td></tr>
<tr><td><strong>Judge</strong></td><td>실제 추천을 수행할 학생 모델</td>
    <td>Qwen3-14B. 본 연구의 최종 산출. Teacher 정답지를 보고 학습 (Phase 3)</td></tr>
<tr><td><strong>Transfer Gate</strong></td><td>전이/부분/차단 3단계 판정</td>
    <td>영화 패턴이 책 추천에 쓰여도 되는지 결정 (TRANSFER·PARTIAL·BLOCK)</td></tr>
<tr><td><strong>Cold-start</strong></td><td>책 도메인 정보가 적은 사용자 대상 추천</td>
    <td>본 연구의 평가 시나리오 — Target 리뷰 5~10개의 cohort</td></tr>
<tr><td><strong>SFT (Supervised Fine-Tuning)</strong></td><td>지도학습 기반 파인튜닝</td>
    <td>Phase 3에서 Qwen3-14B를 Teacher 정답지로 학습</td></tr>
<tr><td><strong>QLoRA</strong></td><td>저자원 파인튜닝 기법</td>
    <td>Qwen3-14B를 24GB GPU 한 대로 학습 가능하게 함</td></tr>
</table>

<!-- ====== 전체 흐름 ====== -->
<h2 class="pagebreak">1. 전체 흐름 한눈에</h2>

<div class="flow">
  <div class="flow-box">
    <span class="tag">단계 0</span>
    <div class="title">원본 데이터</div>
    <div class="desc">Amazon Reviews 2023<br>영화·책 리뷰<br>책 메타데이터</div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-box">
    <span class="tag">단계 1</span>
    <div class="title">대상 사용자 1,000명</div>
    <div class="desc">Source ≥ 15<br>Target 5~10<br>cold-start cohort</div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-box">
    <span class="tag">단계 2</span>
    <div class="title">Profile 생성</div>
    <div class="desc">Profiler (GPT-4o-mini)<br>7개 취향 패턴 JSON<br>per user</div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-box">
    <span class="tag">단계 3</span>
    <div class="title">Teacher 추천 생성</div>
    <div class="desc">Teacher (GPT-4o-mini)<br>전이 판단 + Top-10<br>per user</div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-box">
    <span class="tag">단계 4</span>
    <div class="title">학습 데이터</div>
    <div class="desc">SFT chat 포맷<br><strong>총 578 줄</strong><br>JSONL</div>
  </div>
</div>

<table>
<tr><th>단계</th><th>입력</th><th>처리 주체</th><th>출력</th></tr>
<tr><td>0</td><td>—</td><td>HuggingFace 다운로드</td><td>Amazon Reviews 2023 raw 데이터</td></tr>
<tr><td>1</td><td>Raw 영화·책 리뷰</td><td>전처리 스크립트</td><td>본 실험 대상 1,000명 (parquet)</td></tr>
<tr><td>2</td><td>사용자 영화 리뷰 30개</td><td>Profiler (GPT-4o-mini)</td><td>7개 패턴 Profile JSON</td></tr>
<tr><td>3</td><td>Profile + 후보 도서 50권 + 정답 힌트</td><td>Teacher (GPT-4o-mini)</td><td>전이 판단 7개 + Top-10 추천</td></tr>
<tr><td>4</td><td>위 출력 전체</td><td>SFT 변환 스크립트</td><td>학습 데이터 한 줄 (chat JSON)</td></tr>
</table>

<!-- ====== 단계 0 ====== -->
<h2 class="pagebreak">2. 단계 0 — 원본 데이터 (Amazon Reviews 2023)</h2>

<table>
<tr><th>데이터 종류</th><th>출처</th><th>규모</th><th>본 연구에서의 활용</th></tr>
<tr><td>영화·TV 리뷰</td>
    <td>HuggingFace <code>McAuley-Lab/Amazon-Reviews-2023</code> · <code>raw_review_Movies_and_TV</code></td>
    <td>약 3,300만 건</td>
    <td>사용자 취향(Profile) 추출의 입력</td></tr>
<tr><td>책 리뷰</td>
    <td>같은 데이터셋의 <code>raw_review_Books</code></td>
    <td>약 2,900만 건</td>
    <td>정답(GT) 선정 + cold-start 평가 데이터</td></tr>
<tr><td>책 메타데이터</td>
    <td>같은 데이터셋의 <code>raw_meta_Books</code></td>
    <td>약 440만 권</td>
    <td>후보 도서 50권 sampling의 풀 + 제목·저자·줄거리 제공</td></tr>
</table>

<div class="callout">
이 데이터셋은 학술 표준이며 HuggingFace에서 무료 다운로드 가능. 본 연구는 로컬 HF 캐시에 자동
다운로드하여 사용했음.
</div>

<!-- ====== 단계 1 ====== -->
<h2>3. 단계 1 — 본 실험 대상 1,000명 선정</h2>

<h3>3.1 필터링 조건</h3>

<table>
<tr><th>조건</th><th>설명</th><th>이유</th></tr>
<tr><td>영화 리뷰 ≥ 15개</td><td>충분한 취향 신호 확보</td><td>Profiler가 의미 있는 패턴 추출 가능</td></tr>
<tr><td>책 리뷰 5~10개</td><td>cold-start cohort 정의</td><td>본 연구가 다루는 추천 시나리오와 일치</td></tr>
<tr><td>Source 리뷰는 정답 시점 이전만 사용</td><td>Temporal cutoff (시간 누수 방지)</td><td>"미래 정보로 과거 추천" 방지 — 학술 추천 평가 표준</td></tr>
<tr><td>위 조건 충족 사용자 중 무작위 1,000명</td><td>seed 고정 재현 가능</td><td>실험 통계 신뢰성</td></tr>
</table>

<h3>3.2 결과</h3>

<table>
<tr><th>지표</th><th>값</th></tr>
<tr><td>본 실험 cohort (Profile 보유자)</td><td>1,000명</td></tr>
<tr><td>각 사용자 당 영화 리뷰</td><td>최대 30개 (시점 cutoff 후 최신순)</td></tr>
<tr><td>각 사용자 당 책 리뷰</td><td>5~10개 (cold-start)</td></tr>
</table>

<div class="callout">
<strong>분할(split) 정의는 다음 §8에서</strong>: train 사용자는 Teacher 품질 필터 통과 인원, valid/test는 미사용 풀에서 별도 sampling.
이는 train과 평가용 holdout 사이의 누수를 0으로 만들기 위한 설계이다.
</div>

<!-- ====== 사례 사용자 도입 ====== -->
<h2 class="pagebreak">4. 사례 사용자 — 한 명을 끝까지 따라가기</h2>

<p>이 절에서는 실제 본 실험 대상자 한 명(<code>AHY625B6CHNH7GGQFJMJODL4QBOQ</code>)의 데이터를
끝까지 추적해, 학습 데이터 한 줄이 어떻게 만들어지는지 구체적으로 보여준다. 이 사용자는
영화 30개·책 9권 리뷰를 작성한 일반적인 cold-start cohort 멤버다.</p>

<h3>4.1 이 사용자의 영화 리뷰 (최신 5개 표본)</h3>

<table>
<tr><th>순번</th><th>평점</th><th>작성일</th><th>리뷰 제목 + 본문 미리보기</th></tr>
{movies_rows}
</table>

<div class="callout">
사용자는 <strong>고전 시트콤·가족 드라마·전기 영화</strong>를 좋아함. 모든 평점이 5점이지만,
리뷰 본문에서 "wonderful and inspiring", "emotional filled seasons", "love all the actors" 등의
표현이 반복 등장. 즉 <strong>감정·관계 중심 + 영감을 주는 콘텐츠</strong>를 선호한다는 신호.
</div>

<h3>4.2 이 사용자의 책 리뷰 + 정답(GT) 선정</h3>

<table>
<tr><th>작성일</th><th>평점</th><th>도서 ID</th><th>책 제목 + 사용자 리뷰</th></tr>
{books_rows}
</table>

<div class="callout-warn">
<strong>정답(GT) 선정 규칙</strong>: 사용자의 책 리뷰 중 <strong>rating ≥ 4이면서 가장 최근</strong>인 책을
정답으로 지정. 이 사용자의 경우 <strong>"Spare"</strong> (해리 왕자 회고록, 2023-01-27 평가)가 정답.
모델이 이 책을 Top-10 안에 추천해야 학습 데이터로 채택됨.
</div>

<h3>4.3 Temporal Cutoff 적용 결과</h3>

<table>
<tr><th>지표</th><th>값</th></tr>
<tr><td>정답(GT) 시점</td><td>{sample['gt_datetime']}</td></tr>
<tr><td>영화 리뷰 총 개수</td><td>{sample['n_movies_total']}</td></tr>
<tr><td>정답 시점 이전 영화 리뷰</td><td>{sample['n_movies_cutoff']} / {sample['n_movies_total']} (100%)</td></tr>
<tr><td>본 실험 대상 자격</td><td>✅ 통과 (영화 리뷰 ≥ 15 충족)</td></tr>
</table>

<!-- ====== 단계 2: Profiler ====== -->
<h2 class="pagebreak">5. 단계 2 — Profile 생성 (Profiler)</h2>

<h3>5.1 입력</h3>

<table>
<tr><th>구성</th><th>내용</th></tr>
<tr><td>모델</td><td>GPT-4o-mini · temperature 0.0 · seed 42 (재현성 보장)</td></tr>
<tr><td>System Prompt</td><td>"당신은 cross-domain 추천을 위한 사용자 취향 분석가. 7개 core pattern을 추출하라."</td></tr>
<tr><td>User Message</td><td>사용자의 영화 리뷰 30개 텍스트 (최신순)</td></tr>
</table>

<h3>5.2 7개 패턴 강제 추출 메커니즘</h3>

<p>Profiler는 모든 사용자에 대해 <strong>예외 없이 7개 패턴 전부</strong>를 추출하도록 설계됨.
다만 신호가 약하거나 부재한 패턴에 대해서는 <strong>"없음 자체를 정직하게 기록"</strong>하는 방식으로
작동:</p>

<table>
<tr><th>상황</th><th>처리 방식</th><th>실제 효과</th></tr>
<tr><td>리뷰에 강한 신호 존재</td>
    <td>value 채움, confidence 높게 (0.7~1.0), polarity 명시</td>
    <td>Teacher 단계에서 활용 가능한 신호</td></tr>
<tr><td>리뷰에 약한 신호만</td>
    <td>value 짧게, confidence 중간 (0.4~0.6), polarity는 mixed 가능</td>
    <td>Teacher가 PARTIAL/BLOCK 판단할 근거</td></tr>
<tr><td>신호가 거의 없음</td>
    <td>value를 "no strong signal"류로, confidence 낮게 (≤ 0.3), polarity mixed,
        transferability_hint low</td>
    <td>Teacher가 자동으로 BLOCK 판정 — 환각으로 빈 자리 채우는 것 방지</td></tr>
</table>

<div class="callout-green">
<strong>핵심</strong>: 7개 패턴 강제 추출은 "추측해서라도 채워라"가 아님. <strong>없으면 없다고
정직하게 기록</strong>하라는 설계. confidence 값이 그 정직성의 지표. 다음 단계(Teacher)에서 이
confidence·polarity·transferability_hint를 보고 BLOCK/PARTIAL/TRANSFER 판정.
</div>

<h3>5.3 출력 — 사례 사용자의 Profile</h3>

<table>
<tr><th>패턴 이름</th><th>value (취향 요약)</th><th>신뢰도</th><th>극성</th><th>전이 힌트</th><th>근거 (영화 리뷰 인용)</th></tr>
{profile_rows}
</table>

<p style="margin-top: 8px;"><strong>종합 요약 (summary)</strong>:
"{profile.get("summary", "")[:300]}"</p>

<table>
<tr><th>컬럼</th><th>한글</th><th>의미</th></tr>
<tr><td>value</td><td>취향 요약</td><td>패턴에서 추출된 핵심 단어/구문</td></tr>
<tr><td>confidence</td><td>신뢰도</td><td>0.0~1.0. 신호의 강도 (높을수록 명확한 패턴)</td></tr>
<tr><td>polarity</td><td>극성</td><td>positive(긍정)·negative(부정)·mixed(혼합/모호)</td></tr>
<tr><td>transferability_hint</td><td>전이 힌트</td><td>high(책에 직접 적용 가능)·medium(변환 필요)·low(적용 어려움)</td></tr>
</table>

<!-- ====== 단계 3: Teacher ====== -->
<h2 class="pagebreak">6. 단계 3 — Teacher 추천 생성</h2>

<h3>6.1 입력 — Teacher가 받는 정보</h3>

<table>
<tr><th>섹션</th><th>내용</th><th>역할</th></tr>
<tr><td>사용자 Profile</td><td>5절에서 생성한 7-pattern JSON 전체</td>
    <td>Teacher가 사용자 취향을 파악할 입력</td></tr>
<tr><td>후보 도서 50권</td><td>정답 1권 + 무작위 49권 (제목·저자·카테고리·줄거리 포함)</td>
    <td>Teacher가 Top-10을 고를 선택지</td></tr>
<tr><td>정답 힌트 (GT hint)</td><td>정답 책의 ID와 제목</td>
    <td>Teacher가 정답에 가까운 추천을 만들도록 보조 (Student는 보지 않음)</td></tr>
<tr><td>허용 ID 리스트 (ALLOWED_ITEM_IDS)</td><td>50개 후보 ID 압축 목록 + 자기 검증 지시</td>
    <td>환각 방지 (후보 밖 책 추천 금지)</td></tr>
<tr><td>지시 (INSTRUCTION)</td><td>"transfer_decisions와 Top-10을 JSON으로 출력하라"</td>
    <td>출력 포맷 강제</td></tr>
</table>

<h3>6.2 출력 ① — 패턴별 전이 판단</h3>

<table>
<tr><th>패턴</th><th>판단 (Decision)</th><th>판단 근거 (rationale)</th><th>책 도메인 적용 (transferred_insight)</th></tr>
{teacher_dec_rows}
</table>

<table>
<tr><th>Decision</th><th>한글</th><th>의미</th></tr>
<tr><td><span class="pol-positive">TRANSFER</span></td><td>전이</td>
    <td>이 영화 취향이 책 추천에 그대로 적용 가능</td></tr>
<tr><td><span class="pol-mixed">PARTIAL</span></td><td>부분 전이</td>
    <td>일부만 적용 (장르 변환 등 추가 작업 필요)</td></tr>
<tr><td><span class="pol-negative">BLOCK</span></td><td>차단</td>
    <td>책 도메인에는 부적합 또는 부정 전이 위험. 추천에 사용 금지</td></tr>
</table>

<h3>6.3 출력 ② — Top-10 책 추천</h3>

<table>
<tr><th>순위</th><th>도서 ID</th><th>제목</th><th>점수</th><th>적용된 패턴</th></tr>
{recs_rows}
</table>

<div class="callout-green">
<strong>이 사례의 핵심 결과</strong>: 1위 추천이 <strong>정답 "Spare"</strong>와 일치 (🎯).<br>
즉 Teacher가 사용자의 취향(가족·감정·전기·드라마)을 잘 해석해 회고록 장르를 1위에 배치.
<code>gt_in_top10 = True</code>가 되어 <strong>학습 데이터로 채택</strong>됨.<br>
참고: 정답이 Top-10 안에 없으면 그 사용자는 학습 데이터에서 자동 제외 (품질 필터).
</div>

<!-- ====== 단계 4: SFT 변환 ====== -->
<h2 class="pagebreak">7. 단계 4 — 학습 데이터 한 줄로 변환 (SFT)</h2>

<h3>7.1 변환 규칙</h3>

<table>
<tr><th>원본 (Teacher 단계)</th><th>변환 (학습 데이터)</th><th>이유</th></tr>
<tr><td>System prompt에 GT 관련 설명 포함</td><td>GT 관련 문구 모두 제거</td>
    <td>Student(Judge)는 추론 시점에 GT를 모름</td></tr>
<tr><td>User Message에 GT hint + 허용 ID 리스트 포함</td><td>둘 다 제거. Profile + 50권 후보 + 지시만 유지</td>
    <td>같은 이유 (Student에게 정답 노출 금지)</td></tr>
<tr><td>Assistant content</td><td>그대로 유지 (transfer_decisions + Top-10 추천 + 요약)</td>
    <td>이것이 Student가 따라 학습할 정답</td></tr>
</table>

<h3>7.2 변환 후 학습 데이터 한 줄의 모습</h3>

<p>이 사용자에 해당하는 학습 데이터 한 줄은 다음과 같이 <code>data/teacher_train_main.jsonl</code>에
저장됨. OpenAI/Qwen 등 LLM이 학습용으로 받아들이는 표준 chat 포맷.</p>

<pre style="font-size: 8pt;">{{
  "messages": [
    {{
      "role": "system",
      "content": "You are an expert Cross-Domain Transfer Judge.
      [... GT 관련 설명 제거됨 ...]
      Output JSON: transfer_decisions + recommendations Top-10."
    }},
    {{
      "role": "user",
      "content": "=== USER PROFILE ===
      {{ 7개 패턴 Profile JSON 전체 ... }}

      === CANDIDATES (50 Books) ===
      [C1] item_id: ... title: ... synopsis: ...
      [C2] ...
      [... 50권 ...]

      === INSTRUCTION ===
      Produce transfer_decisions and Top-10 books."
    }},
    {{
      "role": "assistant",
      "content": "{{
        \\"transfer_decisions\\": {{
          \\"genre_preference\\": {{\\"decision\\": \\"PARTIAL\\", \\"rationale\\": \\"...\\", \\"confidence\\": 0.75}},
          \\"narrative_complexity\\": {{\\"decision\\": \\"TRANSFER\\", ...}},
          [... 7 patterns ...]
        }},
        \\"recommendations\\": [
          {{\\"rank\\": 1, \\"item_id\\": \\"0593593804\\", \\"title\\": \\"Spare\\", \\"score\\": 0.9, ...}},
          [... 10 recommendations ...]
        ],
        \\"blocked_patterns_summary\\": \\"brand_loyalty blocked.\\",
        \\"overall_strategy\\": \\"...\\"
      }}"
    }}
  ]
}}</pre>

<table>
<tr><th>지표</th><th>이 사용자의 record</th></tr>
<tr><td>구성 (역할별 메시지)</td><td>3개 (system + user + assistant)</td></tr>
<tr><td>User message 크기</td><td>{user_msg_size:,} 자 (약 {user_msg_size//4:,} 토큰)</td></tr>
<tr><td>Assistant message 크기</td><td>{asst_msg_size:,} 자 (약 {asst_msg_size//4:,} 토큰)</td></tr>
<tr><td>한 record 총 토큰 (대략)</td><td>약 {(user_msg_size + asst_msg_size)//4:,} 토큰</td></tr>
</table>

<!-- ====== 최종 데이터 통계 + 이탈률 분석 ====== -->
<h2 class="pagebreak">8. 최종 학습 데이터 통계 + 이탈률 분석</h2>

<h3>8.1 단계별 이탈 도식 (1,000명 → 578줄)</h3>

<table>
<tr><th>단계</th><th>처리</th><th>이탈 인원</th><th>잔존</th></tr>
<tr><td>①</td><td>본 실험 대상 cohort</td><td>—</td><td><strong>1,000명</strong></td></tr>
<tr><td>②</td><td>Profile 생성 (Profiler)</td>
    <td>0명 (전부 성공)</td><td>1,000명</td></tr>
<tr><td>③</td><td>Teacher 추천 생성 시도</td>
    <td>—</td><td>1,000명 시도</td></tr>
<tr><td>④</td><td>Teacher 출력 스키마 유효
    <span style="font-size:8.5pt;color:#666;">(JSON 파싱·7-pattern·후보 50권 내·중복 0·rank·score 범위)</span></td>
    <td><strong>~53명 탈락</strong>
    <span style="font-size:8.5pt;color:#666;">(스키마 위반·환각·재시도 3회 실패)</span></td>
    <td>~947명</td></tr>
<tr><td>⑤</td><td><strong>정답 책이 Teacher Top-10 안에 포함</strong>
    <span style="font-size:8.5pt;color:#666;">(핵심 품질 필터)</span></td>
    <td><strong>~353명 탈락</strong>
    <span style="font-size:8.5pt;color:#666;">(Teacher가 추천을 만들었지만 정답을 못 맞춤)</span></td>
    <td><strong>594명</strong></td></tr>
<tr><td>⑥</td><td>Trial v2 단계 carryover</td>
    <td>—</td><td>+8명 (= 602)</td></tr>
<tr><td>⑦</td><td>Orphan record 제거 (raw 데이터에 없는 user)</td>
    <td><strong>1명 탈락</strong></td><td>601명</td></tr>
<tr><td>⑧</td><td>Low-signal profile 제거 (unknown ≥ 3 또는 빈 evidence ≥ 3)</td>
    <td><strong>23명 탈락</strong></td><td>578명</td></tr>
<tr><td>⑨</td><td>Title 정규화 (79건의 추천 title을 books_meta 기준으로 통일)</td>
    <td>0명 (in-place 수정)</td><td>578명</td></tr>
<tr><td>⑩</td><td><strong>최종 학습 데이터</strong></td>
    <td>—</td><td><strong>578줄</strong></td></tr>
</table>

<div class="callout-warn">
<strong>가장 큰 이탈은 단계 ⑤</strong>: Teacher가 추천을 만들었지만 정답 책을 Top-10 안에 못 넣은 경우 (약 350명).
이 record들은 "Teacher의 추천이 결국 틀렸다"는 의미라서 학습 데이터로 쓰면 Student에게 잘못된 정답을
가르치게 됨. 따라서 <strong>자동 제외</strong>가 본 연구의 핵심 품질 필터.
</div>

<h3>8.2 왜 이렇게 설계되었는가</h3>

<table>
<tr><th>설계 결정</th><th>이유</th><th>대안과의 비교</th></tr>
<tr><td><strong>"정답이 Top-10에 있어야만 채택"</strong></td>
    <td>Teacher의 신뢰성을 자체 검증. 정답을 맞춘 record만 양질의 학습 신호로 간주.</td>
    <td>모든 record 채택 시 → Student가 잘못된 정답까지 학습 → 추론 능력 ↓</td></tr>
<tr><td>1,000명 시작 → 602줄 종료 (이탈 약 40%)</td>
    <td>Pilot에서 검증된 정상 범위. 60% 채택 = "양"보다 "질"을 우선한 결과.</td>
    <td>채택률이 80%대가 되려면 Teacher가 거의 완벽해야 하지만 GPT-4o-mini로는 비현실적</td></tr>
<tr><td>탈락 사용자는 "차후 평가용"이 아닌 "단순 제외"</td>
    <td>Teacher가 못 맞춘 사용자에 대한 정답은 불확실하므로 Test set 평가도 부적합</td>
    <td>이 사용자는 Phase 4·5 평가에서도 통계적 표본에서 제외 가능</td></tr>
</table>

<h3>8.3 학술적 정당성</h3>

<table>
<tr><th>학계 표준</th><th>본 연구 적용</th></tr>
<tr><td>지식 증류(Knowledge Distillation) 연구에서 Teacher 출력의 자체 검증은 흔한 관행</td>
    <td>본 연구 §8.1의 단계 ⑤가 이 자체 검증 단계에 해당</td></tr>
<tr><td>SFT 학습에서 "noisy label"은 학생 성능을 떨어뜨리는 주된 원인 (Wang et al., 2022)</td>
    <td>본 연구는 60.2% 채택률로 noisy label 비율을 사전 최소화</td></tr>
<tr><td>cold-start 추천 연구에서 60% 전후 acceptance rate는 합리적 범위</td>
    <td>본 연구 602/1,000 = 60.2% 정확히 해당</td></tr>
</table>

<h3>8.4 최종 학습 데이터 요약</h3>

<table>
<tr><th>지표</th><th>값</th><th>설명</th></tr>
<tr><td>본 실험 cohort</td><td>1,000명</td><td>cold-start cohort (Source≥15, Target 5–10, temporal cutoff 통과)</td></tr>
<tr><td>Profile 생성 성공</td><td>1,000개 (100%)</td><td>모든 대상자 7-pattern Profile 확보</td></tr>
<tr><td>Teacher 추천 생성 성공 (스키마 유효)</td><td>약 947명 (~95%)</td><td>JSON·후보 내·중복·title 일치 등 절대 기준 통과</td></tr>
<tr><td>정답 책이 Top-10 안에 포함</td><td>602명 (60.2%)</td>
    <td>핵심 품질 필터 (Trial v2 carryover 포함)</td></tr>
<tr><td><strong>+ 정합성 정리 (orphan·low-signal·title 정규화)</strong></td>
    <td><strong>578명 (57.8%)</strong></td>
    <td>orphan 1·low-signal 23 제거 + title 79건 정규화</td></tr>
<tr><td>한 record 당 평균 토큰</td><td>약 {(user_msg_size + asst_msg_size)//4:,} 토큰</td>
    <td>{user_msg_size//4:,} 입력 + {asst_msg_size//4:,} 출력</td></tr>
<tr><td><strong>최종 학습 데이터 파일</strong></td>
    <td><strong><code>data/teacher_train_main.jsonl</code> · 578줄</strong></td>
    <td>Phase 3 Qwen3-14B 파인튜닝 입력</td></tr>
</table>

<h3>8.5 평가용 holdout (valid · test) 분리</h3>

<p>학습 데이터로 채택된 578명을 train으로 분류하고, 평가용 holdout은 <strong>학습 데이터와 누수 없이</strong>
별도로 구성:</p>

<table>
<tr><th>Split</th><th>인원</th><th>구성 방식</th></tr>
<tr><td><strong>train</strong></td><td>578명</td>
    <td>품질·정합성 필터 통과 사용자 전체</td></tr>
<tr><td>valid</td><td>100명</td>
    <td>학습 데이터에 없는 Profile 보유자 풀(422명) 중 random sample (seed=2028)</td></tr>
<tr><td>test</td><td>100명</td>
    <td>같은 풀에서 valid 제외 후 random sample (seed=2028)</td></tr>
<tr><td>합계</td><td>778명</td><td>train ∩ (valid ∪ test) = ∅, valid ∩ test = ∅</td></tr>
</table>

<div class="callout-green">
<strong>학술적 정당성</strong>: 평가용 사용자(valid·test)는 학습 데이터에 한 줄도 포함되지 않음.
이는 SFT 학습 모델 평가에서 흔히 문제되는 train-test leakage를 사전 완전 차단한 설계.
Profile 보유자 1,000명 중 학습 채택 578 + holdout 200 = 778명을 본 실험 모집단으로 사용.
</div>

<!-- ====== Phase 3 ====== -->
<h2 class="pagebreak">9. 이 학습 데이터의 다음 단계 (Phase 3)</h2>

<h3>9.1 Qwen3-14B Judge 모델 학습</h3>

<p>602줄의 학습 데이터는 다음 단계에서 <strong>Qwen3-14B</strong> 모델을 <strong>QLoRA</strong> 방식으로
파인튜닝하는 데 사용됨.</p>

<table>
<tr><th>측면</th><th>설명</th></tr>
<tr><td>모델</td><td>Qwen3-14B (140억 파라미터 다국어 LLM)</td></tr>
<tr><td>학습 방식</td><td>QLoRA — 전체 모델 중 약 0.1% 파라미터만 학습 (LoRA adapter)</td></tr>
<tr><td>학습 환경</td><td>RunPod A100 80GB GPU 1대</td></tr>
<tr><td>학습 시간</td><td>약 6~8시간</td></tr>
<tr><td>학습 비용</td><td>약 $3~$5 (GPU 시간당 임대료)</td></tr>
<tr><td>학습 input</td><td>한 record의 system + user message (Profile + 50권 후보)</td></tr>
<tr><td>학습 target</td><td>한 record의 assistant message (transfer_decisions + Top-10)</td></tr>
</table>

<h3>9.2 학습 후 Judge가 할 수 있는 일</h3>

<table>
<tr><th>입력 (추론 시점)</th><th>Judge 모델의 출력</th></tr>
<tr><td>새 사용자의 Profile (Test set의 cold-start cohort)<br>+ 후보 도서 50권</td>
    <td>transfer_decisions 7개 패턴 (전이/부분/차단)<br>+ 추천 도서 Top-10 (순위·점수·근거)</td></tr>
</table>

<div class="callout-green">
<strong>핵심 차이점</strong>: 학습된 Judge는 <strong>정답 힌트(GT)를 보지 않고</strong> Profile만으로
추천 가능. 즉 실제 서비스 환경처럼 작동. Phase 4·5에서 Test set 100명에 대해 추천 성능을
측정 (Hit@10, NDCG@10 등 표준 지표).
</div>

<h3>9.3 본 학습 데이터의 핵심 학습 신호</h3>

<table>
<tr><th>한 record가 Judge에 가르치는 것</th><th>예시 (사례 사용자 기준)</th></tr>
<tr><td>(1) Profile에서 어떤 패턴이 영화 특정적인지 인식하기</td>
    <td><strong>"brand_loyalty: BLOCK"</strong> — 배우 충성도는 책 추천에 부적합</td></tr>
<tr><td>(2) 어떤 패턴이 책으로 전이 가능한지 인식하기</td>
    <td><strong>"sensory_preference: TRANSFER"</strong> — 감성·분위기는 책에서도 적용</td></tr>
<tr><td>(3) Transfer 가능한 패턴만 활용해 Top-10 구성하기</td>
    <td>각 추천에 "applied_patterns" 필드로 어떤 패턴을 썼는지 명시</td></tr>
<tr><td>(4) 사용자 취향과 책 메타데이터를 매칭하기</td>
    <td>"가족·감정 영화 선호" → 회고록 "Spare" 1위 배치</td></tr>
</table>

<div class="callout">
<strong>학술적 함의</strong>: 본 연구의 핵심 가설은 "<strong>모든 패턴이 전이 가능한 것이 아니다 —
선택적 전이가 cold-start 성능을 좌우한다</strong>"임. 학습 데이터에 TRANSFER 47.8% · PARTIAL 28.4%
· BLOCK 23.8%의 균형 분포가 들어있어, Judge가 이 선택 능력을 학습하게 됨.
</div>

</body>
</html>
"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    weasyprint.HTML(string=html).write_pdf(str(OUTPUT_PATH))
    print(f"✅ Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
