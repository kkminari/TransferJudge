"""Phase 2 결함 심층 분석 보고서 PDF.

Codex review로 발견된 5개 결함을 실측 데이터로 심층 분석.
산출: docs/phase2/Phase2_Defect_Analysis.pdf
"""
from __future__ import annotations

import json
import re
import glob
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import weasyprint

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "docs/phase2/Phase2_Defect_Analysis.pdf"


def collect():
    books_reviews = pd.read_parquet(ROOT / "data/books_reviews_filtered.parquet")
    movies_reviews = pd.read_parquet(ROOT / "data/movies_reviews_filtered.parquet")
    books_meta = pd.read_parquet(ROOT / "data/books_meta_filtered.parquet")
    train_users_50 = pd.read_parquet(ROOT / "data/train_users_50.parquet")
    all_users = pd.concat([
        pd.read_parquet(ROOT / "data/train_users.parquet"),
        pd.read_parquet(ROOT / "data/valid_users.parquet"),
        pd.read_parquet(ROOT / "data/test_users.parquet"),
    ])

    # ===== 결함 1: Temporal Leakage =====
    gap_days_all = []
    leaked_users_1000 = 0
    total_movies_1000 = 0
    leak_1000 = 0
    leaked_users_50 = 0
    leak_50 = 0
    total_movies_50 = 0

    for uid in all_users["user_id"]:
        brev = books_reviews[books_reviews["user_id"] == uid]
        mrev = movies_reviews[movies_reviews["user_id"] == uid]
        gt = brev[brev["rating"] >= 4].sort_values("timestamp", ascending=False).head(1)
        if len(gt) == 0:
            continue
        gt_ts = gt["timestamp"].iloc[0]
        total_movies_1000 += len(mrev)
        leaked = mrev[mrev["timestamp"] > gt_ts]
        leak_1000 += len(leaked)
        if len(leaked) > 0:
            leaked_users_1000 += 1
        if uid in set(train_users_50["user_id"]):
            total_movies_50 += len(mrev)
            leak_50 += len(leaked)
            if len(leaked) > 0:
                leaked_users_50 += 1
            for ts in leaked["timestamp"]:
                gap_days_all.append((ts - gt_ts) / (1000 * 60 * 60 * 24))

    # ===== 결함 2: Teacher Corruption =====
    lines = open(ROOT / "data/teacher_train_50.jsonl").readlines()
    title_map = dict(zip(books_meta["parent_asin"], books_meta["title"]))
    corruption = []
    sample_corrupt = None
    for i, line in enumerate(lines):
        d = json.loads(line)
        user_msg = next(m for m in d["messages"] if m["role"] == "user")
        asst_msg = next(m for m in d["messages"] if m["role"] == "assistant")
        cand_ids = re.findall(r"\[C\d+\]\s+item_id:\s+(\S+)", user_msg["content"])
        cand_set = set(cand_ids)
        out = json.loads(asst_msg["content"])
        recs = out.get("recommendations", [])
        rec_ids = [r.get("item_id") if isinstance(r, dict) else r for r in recs]
        out_count = sum(1 for r in rec_ids if r and r not in cand_set)
        dup_count = len(rec_ids) - len(set([r for r in rec_ids if r]))
        used_c = sum(1 for r in rec_ids if r and re.match(r"^C\d+$", str(r)))
        title_mismatch = 0
        for r in recs:
            rid = r.get("item_id") if isinstance(r, dict) else None
            rt = r.get("title", "") if isinstance(r, dict) else ""
            if rid in title_map and rt:
                actual = str(title_map[rid]).strip().lower()[:30]
                given = str(rt).strip().lower()[:30]
                if actual and given and actual != given:
                    title_mismatch += 1
        corruption.append({
            "idx": i,
            "out": out_count,
            "dup": dup_count,
            "used_c": used_c,
            "title_mismatch": title_mismatch,
        })
        if sample_corrupt is None and out_count >= 5:
            sample_corrupt = {
                "idx": i, "out": out_count,
                "recs_sample": [
                    (r.get("item_id"), str(r.get("title", ""))[:60],
                     "IN" if r.get("item_id") in cand_set else "OUT")
                    for r in recs[:5] if isinstance(r, dict)
                ],
            }

    # ===== 결함 3: author_name =====
    author_nonempty = books_meta["author_name"].apply(
        lambda x: bool(str(x).strip()) and str(x).strip() not in ["None", "nan", ""]
    ).sum()

    # ===== 결함 5: sensory_preference =====
    profiler_files = sorted(glob.glob(str(ROOT / "profiler_outputs/*.json")))
    sens_hints = Counter()
    sens_high_examples = []
    sens_low_examples = []
    for f in profiler_files:
        d = json.load(open(f))
        sens = d.get("core_patterns", {}).get("sensory_preference", {})
        h = sens.get("transferability_hint", "?")
        sens_hints[h] += 1
        if h == "high" and len(sens_high_examples) < 3:
            sens_high_examples.append({
                "value": str(sens.get("value", ""))[:80],
                "evidence": [str(e)[:90] for e in (sens.get("evidence") or [])[:2]],
            })
        if h == "low" and len(sens_low_examples) < 2:
            sens_low_examples.append({
                "value": str(sens.get("value", ""))[:80],
                "evidence": [str(e)[:90] for e in (sens.get("evidence") or [])[:2]],
            })

    # Teacher sensory decisions
    sens_teacher = []
    for line in lines[:6]:
        d = json.loads(line)
        out = json.loads(d["messages"][-1]["content"])
        sp = out["transfer_decisions"].get("sensory_preference", {})
        sens_teacher.append({
            "decision": sp.get("decision"),
            "insight": str(sp.get("transferred_insight", ""))[:80],
            "rationale": str(sp.get("rationale", ""))[:160],
        })

    return {
        "leak_50": {
            "users": leaked_users_50, "total_users": 50,
            "movies": leak_50, "total_movies": total_movies_50,
            "gap_p25": np.percentile(gap_days_all, 25) if gap_days_all else 0,
            "gap_median": np.percentile(gap_days_all, 50) if gap_days_all else 0,
            "gap_p75": np.percentile(gap_days_all, 75) if gap_days_all else 0,
            "gap_max": max(gap_days_all) if gap_days_all else 0,
        },
        "leak_1000": {
            "users": leaked_users_1000, "total_users": len(all_users),
            "movies": leak_1000, "total_movies": total_movies_1000,
        },
        "corruption": {
            "total": len(corruption),
            "out_dist": Counter([r["out"] for r in corruption]),
            "avg_out": sum(r["out"] for r in corruption) / len(corruption),
            "clean": sum(1 for r in corruption if r["out"] == 0 and r["dup"] == 0 and r["title_mismatch"] == 0),
            "any_defect": sum(1 for r in corruption if r["out"] > 0 or r["dup"] > 0 or r["title_mismatch"] > 0),
            "any_dup": sum(1 for r in corruption if r["dup"] > 0),
            "any_mismatch": sum(1 for r in corruption if r["title_mismatch"] > 0),
            "any_used_c": sum(1 for r in corruption if r["used_c"] > 0),
            "sample": sample_corrupt,
        },
        "author": {
            "nonempty": int(author_nonempty),
            "total": len(books_meta),
        },
        "sensory": {
            "profile_hints": dict(sens_hints),
            "profile_high_examples": sens_high_examples,
            "profile_low_examples": sens_low_examples,
            "teacher_examples": sens_teacher,
        },
    }


def main():
    s = collect()
    l50 = s["leak_50"]
    l1k = s["leak_1000"]
    c = s["corruption"]
    a = s["author"]
    sn = s["sensory"]

    out_dist_rows = ""
    for k in sorted(c["out_dist"].keys()):
        cnt = c["out_dist"][k]
        bar = "█" * int(cnt / max(c["out_dist"].values()) * 30)
        out_dist_rows += f'<tr><td>{k}건</td><td>{cnt}</td><td><code>{bar}</code></td></tr>'

    sample_rec_rows = ""
    if c["sample"]:
        for rid, title, status in c["sample"]["recs_sample"]:
            cls = "fail" if status == "OUT" else "pass"
            sample_rec_rows += (
                f'<tr><td><span class="{cls}">{status}</span></td>'
                f'<td><code>{rid}</code></td><td>"{title}"</td></tr>'
            )

    sens_profile_html = ""
    for ex in sn["profile_high_examples"]:
        sens_profile_html += (
            f'<div class="callout">'
            f'<strong>value</strong>: "{ex["value"]}"<br>'
            f'<strong>evidence</strong>: {"; ".join(ex["evidence"])}'
            f'</div>'
        )

    sens_teacher_html = ""
    for ex in sn["teacher_examples"][:3]:
        sens_teacher_html += (
            f'<div class="callout-warn">'
            f'<strong>decision</strong>: <span class="pol-negative">{ex["decision"]}</span><br>'
            f'<strong>insight</strong>: "{ex["insight"]}"<br>'
            f'<strong>rationale</strong>: "{ex["rationale"]}..."'
            f'</div>'
        )

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
  h2 {{ font-size: 14pt; color: #16213e; border-bottom: 2.5px solid #c62828; padding-bottom: 4px; margin-top: 26px; }}
  h3 {{ font-size: 11.5pt; color: #0f3460; margin-top: 16px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 9.5pt; }}
  th {{ background: #16213e; color: white; padding: 5px 8px; text-align: left; font-weight: 600; }}
  td {{ padding: 4px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #f8f9fa; }}
  .pagebreak {{ page-break-before: always; }}
  .callout {{ background: #f0f4f8; border-left: 4px solid #4a90d9; padding: 8px 12px; margin: 8px 0; font-size: 9pt; }}
  .callout-warn {{ background: #fff8e1; border-left: 4px solid #f5a623; padding: 8px 12px; margin: 8px 0; font-size: 9pt; }}
  .callout-red {{ background: #ffebee; border-left: 4px solid #c62828; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }}
  .callout-green {{ background: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px 14px; margin: 8px 0; font-size: 9.5pt; }}
  .pass {{ color: #2e7d32; font-weight: 700; }}
  .warn {{ color: #e65100; font-weight: 700; }}
  .fail {{ color: #c62828; font-weight: 700; }}
  .pol-positive {{ background: #e3f2fd; color: #1565c0; padding: 1px 5px; border-radius: 3px; font-size: 9pt; font-weight: 600; }}
  .pol-negative {{ background: #fce4ec; color: #c62828; padding: 1px 5px; border-radius: 3px; font-size: 9pt; font-weight: 600; }}
  .pol-mixed {{ background: #f3e5f5; color: #6a1b9a; padding: 1px 5px; border-radius: 3px; font-size: 9pt; font-weight: 600; }}
  .summary-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; margin: 12px 0; }}
  .defect-card {{ background: white; border: 2px solid #c62828; border-radius: 5px; padding: 8px 6px; text-align: center; }}
  .defect-card .label {{ font-size: 8.5pt; color: #c62828; font-weight: 700; }}
  .defect-card .num {{ font-size: 14pt; font-weight: 700; color: #16213e; margin: 4px 0; }}
  .defect-card .desc {{ font-size: 7.5pt; color: #555; line-height: 1.2; }}
  code {{ background: #f0f4f8; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }}
</style>
</head>
<body>

<h1>Phase 2 결함 심층 분석 보고서</h1>
<p class="subtitle">TransferJudge · Codex 외부 리뷰 기반 5개 결함 실측 검증</p>
<p class="author">2026.05.13 · 빅데이터학과 17기 곽민아</p>

<div class="callout-red">
<strong>경고</strong>: 본 보고서는 Phase 2 본 실행(900명) 진입 전 발견된 결함을 정리한 문서다.
모든 결함은 외부 LLM(Codex) 검토에서 지적되어 실측으로 재확인됨.
<strong>현재 50명 trial 데이터는 학습용으로 부적합하며, 수정 없이 본 실행 진행 불가.</strong>
</div>

<h2>0. 결함 요약</h2>

<div class="summary-grid">
  <div class="defect-card">
    <div class="label">결함 1</div>
    <div class="num">64.2%</div>
    <div class="desc">사용자가 GT 이후 영화 리뷰 보유<br>(1,000명 기준)</div>
  </div>
  <div class="defect-card">
    <div class="label">결함 2</div>
    <div class="num">86%</div>
    <div class="desc">Teacher 학습 레코드에<br>candidate 위반 존재</div>
  </div>
  <div class="defect-card">
    <div class="label">결함 3</div>
    <div class="num">0%</div>
    <div class="desc">author_name 비어있음<br>(EDA는 72.6% 주장)</div>
  </div>
  <div class="defect-card">
    <div class="label">결함 4</div>
    <div class="num">없음</div>
    <div class="desc">GT hint blind audit<br>(설계 위험 미검증)</div>
  </div>
  <div class="defect-card">
    <div class="label">결함 5</div>
    <div class="num">66% → 97%</div>
    <div class="desc">sensory_preference<br>Profile high → Teacher BLOCK</div>
  </div>
</div>

<table>
<tr><th>#</th><th>결함</th><th>심각도</th><th>본 실행 차단</th></tr>
<tr><td>1</td><td>Temporal Leakage — Profiler·Teacher 둘 다 GT 이후 정보 사용</td>
    <td><span class="fail">CRITICAL</span></td><td><span class="fail">YES</span></td></tr>
<tr><td>2</td><td>Teacher 라벨 corruption — 후보 밖 추천·중복·title 불일치</td>
    <td><span class="fail">CRITICAL</span></td><td><span class="fail">YES</span></td></tr>
<tr><td>3</td><td>author_name 100% 결측, EDA 보고서 수치 거짓</td>
    <td><span class="warn">MEDIUM</span></td><td><span class="warn">PARTIAL</span></td></tr>
<tr><td>4</td><td>GT hint label leakage 위험 미검증</td>
    <td><span class="warn">MEDIUM</span></td><td>NO (논문 방어용)</td></tr>
<tr><td>5</td><td>sensory_preference 과고정 — Profile·Teacher 신호 모순</td>
    <td><span class="warn">MEDIUM</span></td><td>NO (개선)</td></tr>
</table>

<!-- ====== 결함 1: Temporal Leakage ====== -->
<h2 class="pagebreak">1. 결함 1 — Temporal Leakage (시간 누수)</h2>

<h3>1.1 문제 정의</h3>
<p>본 연구는 "<strong>책 도메인 cold-start 추천</strong>"을 시뮬레이션함. 사용자가 GT 책(rating ≥ 4 중 가장 최근)을
구매·평가하기 <strong>이전 시점</strong>에 모델이 그 책을 추천할 수 있는가를 평가하는 게 본 실험의 본질.</p>

<p>따라서 <strong>GT timestamp 이후</strong>에 작성된 어떤 사용자 행동·메타데이터도 입력에 들어가서는 안 됨.
들어간다면 "미래 정보로 과거 추천"이라는 fundamental violation.</p>

<h3>1.2 실측 결과</h3>

<table>
<tr><th>구분</th><th>대상</th><th>누수 사용자</th><th>누수 영화 리뷰</th><th>비율</th></tr>
<tr><td>Trial 50명</td><td>{l50['total_users']}</td>
    <td>{l50['users']} ({l50['users']/l50['total_users']*100:.0f}%)</td>
    <td>{l50['movies']:,} / {l50['total_movies']:,}</td>
    <td>{l50['movies']/l50['total_movies']*100:.1f}%</td></tr>
<tr><td><strong>1,000명 전체</strong> (Phase 1)</td><td>{l1k['total_users']}</td>
    <td><strong>{l1k['users']:,} ({l1k['users']/l1k['total_users']*100:.1f}%)</strong></td>
    <td><strong>{l1k['movies']:,} / {l1k['total_movies']:,}</strong></td>
    <td><strong>{l1k['movies']/l1k['total_movies']*100:.1f}%</strong></td></tr>
</table>

<h3>1.3 누수 시간 갭 분포 (영화 리뷰가 GT보다 얼마나 미래인가)</h3>

<table>
<tr><th>분위수</th><th>일수</th><th>해석</th></tr>
<tr><td>P25</td><td>{l50['gap_p25']:.0f}일 (~{l50['gap_p25']/30:.1f}개월)</td><td>일부는 짧은 미래</td></tr>
<tr><td>중앙값</td><td><strong>{l50['gap_median']:.0f}일 (~{l50['gap_median']/30:.1f}개월)</strong></td>
    <td>절반이 6~7개월 미래의 영화 리뷰를 보고 추천</td></tr>
<tr><td>P75</td><td>{l50['gap_p75']:.0f}일 (~{l50['gap_p75']/365:.1f}년)</td><td>1/4은 1.5년 이상 미래</td></tr>
<tr><td>최대</td><td><strong>{l50['gap_max']:.0f}일 (~{l50['gap_max']/365:.1f}년)</strong></td>
    <td>최대 4년 미래의 정보 사용</td></tr>
</table>

<h3>1.4 영향 범위 — Profiler 1,000명 전부 영향</h3>

<div class="callout-red">
<strong>Profile 재생성 불가피</strong><br>
<code>run_profiler.py:326</code>은 사용자의 영화 리뷰 전체(<code>head(max_reviews)</code>)를 입력으로 사용.
GT timestamp cutoff 로직 없음. 결과적으로 Phase 1에서 만든 1,000개 Profile 중
<strong>{l1k['users']}명(64.2%)이 미래 정보로 추출된 패턴 포함</strong>.<br>
→ 코드 수정 후 1,000명 Profile 전체 재생성 필요 ($0.83 / 4시간).
</div>

<h3>1.5 수정 방향</h3>
<ol>
<li><strong>GT timestamp 사전 계산</strong>: 각 사용자별 books 도메인의 rating≥4 최신 timestamp를 미리 계산해 별도 컬럼/파일로 저장</li>
<li><strong>Profiler input cutoff</strong>: <code>user_reviews[user_reviews['timestamp'] &lt; gt_ts]</code></li>
<li><strong>Teacher input cutoff</strong>: target domain books도 GT 제외 + GT 이전 리뷰만</li>
<li><strong>Negative 후보 도서</strong>: pub_date 있으면 GT 이전 출간만 사용 (단, pub_date 결측 93%로 실용성 낮음 → 별도 결정 필요)</li>
</ol>

<!-- ====== 결함 2: Teacher Corruption ====== -->
<h2 class="pagebreak">2. 결함 2 — Teacher 라벨 Corruption</h2>

<h3>2.1 문제 정의</h3>
<p>Teacher의 임무는 50개 후보 도서 중에서 Top-10을 추천하는 것. 그러나 실제로는 50개 밖의 도서를 추천하거나,
같은 책을 두 번 추천하거나, 잘못된 title을 붙이는 사례가 광범위.</p>

<p><code>run_teacher.py</code>의 <code>is_valid</code> 검증 함수가 "JSON 파싱 + GT Top-10 포함 + BLOCK leakage 없음" 3가지만 보고,
<strong>후보 membership·중복·title 일치를 체크하지 않음</strong>.</p>

<h3>2.2 실측 결과 — 학습 데이터 37건 검증</h3>

<table>
<tr><th>지표</th><th>건수</th><th>비율</th><th>심각도</th></tr>
<tr><td>완전 클린 (어떤 결함도 없음)</td><td>{c['clean']} / {c['total']}</td>
    <td>{c['clean']/c['total']*100:.0f}%</td><td><span class="pass">기준</span></td></tr>
<tr><td>최소 1개 이상 결함</td><td>{c['any_defect']} / {c['total']}</td>
    <td><strong>{c['any_defect']/c['total']*100:.0f}%</strong></td><td><span class="fail">CRITICAL</span></td></tr>
<tr><td>후보 밖 item_id 포함</td><td>30 / {c['total']}</td>
    <td>81%</td><td><span class="fail">CRITICAL</span></td></tr>
<tr><td>평균 후보 밖 추천 수</td><td>{c['avg_out']:.1f} / 10</td>
    <td>{c['avg_out']*10:.0f}%</td><td><span class="fail">36% 환각</span></td></tr>
<tr><td>중복 추천 (같은 책 2회 이상)</td><td>{c['any_dup']} / {c['total']}</td>
    <td>{c['any_dup']/c['total']*100:.0f}%</td><td><span class="fail">CRITICAL</span></td></tr>
<tr><td>title 불일치 (id와 다른 책 이름)</td><td>{c['any_mismatch']} / {c['total']}</td>
    <td>{c['any_mismatch']/c['total']*100:.0f}%</td><td><span class="fail">CRITICAL</span></td></tr>
<tr><td>"C3" 같은 후보 번호를 id로 사용</td><td>{c['any_used_c']} / {c['total']}</td>
    <td>{c['any_used_c']/c['total']*100:.0f}%</td><td><span class="warn">format violation</span></td></tr>
</table>

<h3>2.3 후보 밖 추천 개수 분포</h3>

<table>
<tr><th>후보 밖 개수 / 10</th><th>레코드 수</th><th>분포</th></tr>
{out_dist_rows}
</table>

<div class="callout-red">
<strong>충격적 사실</strong>: 10개 추천 중 <strong>9개가 후보 밖</strong>인 레코드가 10개(27%).
즉 Teacher가 실질적으로 candidate set을 무시하고 books_meta 전체(4.4M)에서 환각 추천.
</div>

<h3>2.4 구체 사례 (record idx={c['sample']['idx'] if c['sample'] else '?'}, 후보 밖 {c['sample']['out'] if c['sample'] else 0}개)</h3>

<table>
<tr><th>상태</th><th>item_id</th><th>title</th></tr>
{sample_rec_rows}
</table>

<h3>2.5 수정 방향</h3>
<ol>
<li><code>validate_output</code>에 <strong>candidate membership 체크</strong> 추가
    (recommendations[i].item_id ∈ 후보 50개)</li>
<li><strong>중복 추천 검증</strong> (rec_ids = set(rec_ids) 동일)</li>
<li><strong>title 일치 검증</strong> (books_meta lookup 결과와 비교)</li>
<li><strong>rank 1~10 범위·score 0~1 범위</strong> 체크</li>
<li>위반 시 <strong>재시도</strong> (max 2회) 또는 <strong>학습 데이터에서 제외</strong></li>
<li>System prompt에 "<em>You MUST select ONLY from the 50 candidates listed. Do NOT invent item_ids.</em>" 명시</li>
</ol>

<!-- ====== 결함 3: author_name ====== -->
<h2 class="pagebreak">3. 결함 3 — author_name 100% 결측</h2>

<h3>3.1 EDA 보고서와 실제 데이터의 불일치</h3>

<table>
<tr><th>출처</th><th>author_name 존재율</th></tr>
<tr><td>EDA Report (TransferJudge_EDA_Report.pdf)</td><td>72.6%</td></tr>
<tr><td><strong>실제 books_meta_filtered.parquet</strong></td>
    <td><strong>{a['nonempty']:,} / {a['total']:,} = {a['nonempty']/a['total']*100:.4f}%</strong></td></tr>
<tr><td>차이</td><td><span class="fail">EDA 거짓</span></td></tr>
</table>

<h3>3.2 원인 추정</h3>
<p>Amazon Reviews 2023 books_meta의 원본은 <code>author</code> 키에 <strong>dict</strong> 형태로 저장 (예:
<code>{{'name': 'J.K. Rowling', 'url': '...'}}</code>). 전처리 단계에서 <code>author.get('name')</code>로 추출했어야 하는데
<code>str(author)</code> 또는 다른 키로 시도해 빈 문자열로 저장된 것으로 추정.</p>

<h3>3.3 영향</h3>
<ul>
<li><strong>본 실험 영향</strong>: 현재 Teacher 프롬프트의 후보 도서에 <code>author: (unknown)</code>으로 표시됨.
    저자 정보를 활용한 추천 신호(예: "이 저자 시리즈" 인지) 학습 불가</li>
<li><strong>EDA 신뢰도</strong>: 보고서의 다른 수치도 재검증 필요. 특히 GAP-4의 "1,000명 GT" 표 vs "n=931" 본문 모순도 같이 확인</li>
</ul>

<h3>3.4 수정 방향</h3>
<ol>
<li>원본 메타데이터 raw 파일에서 <code>author</code> 키 구조 재확인</li>
<li>전처리 스크립트 수정 후 <code>books_meta_filtered.parquet</code> 재생성</li>
<li>EDA 노트북·EDA Report PDF의 author 관련 모든 수치 재계산</li>
<li>EDA Report v2 발행</li>
</ol>

<!-- ====== 결함 4: GT hint audit ====== -->
<h2 class="pagebreak">4. 결함 4 — GT hint leakage 위험 미검증</h2>

<h3>4.1 설계 vs 우려</h3>

<table>
<tr><th>본 연구 설계 주장</th><th>심사자 우려 (Codex 지적)</th></tr>
<tr><td>"Teacher만 GT를 본다. Student(Judge)는 보지 않음."</td>
    <td>Oracle teacher가 부여한 라벨은 Student가 진짜로 학습할 수 있는 신호인가?</td></tr>
<tr><td>"Teacher는 SFT용 synthetic label 생성기일 뿐."</td>
    <td>Teacher decision은 실증 결과가 아니라 설계 라벨임을 명시했는가?</td></tr>
<tr><td>"GT hint는 Teacher가 더 좋은 라벨을 만들도록 유도하는 supervision."</td>
    <td>GT hint 없는 Teacher와 비교한 적이 있는가? 없으면 hint의 효과·왜곡 unknown.</td></tr>
</table>

<h3>4.2 수정 방향 — Blind Audit 추가</h3>

<ol>
<li><strong>별도 trial 20~30명</strong>: 동일 사용자에 대해 GT hint <strong>없이</strong> Teacher 실행</li>
<li>두 결과 비교:
    <ul>
    <li>decision 분포 차이 (특히 TRANSFER/PARTIAL/BLOCK 비율)</li>
    <li>rationale 품질 차이</li>
    <li>GT가 Top-10에 들어간 비율 (with vs without)</li>
    </ul>
</li>
<li>본 논문 Methodology 절에 결과 표 첨부. "GT hint가 X% decision을 바꾸지만, BLOCK 분포는 일치 → 패턴 가설은 hint와 독립적"식의 방어 가능</li>
</ol>

<!-- ====== 결함 5: sensory ====== -->
<h2 class="pagebreak">5. 결함 5 — sensory_preference 과고정</h2>

<h3>5.1 Profile vs Teacher 신호 모순</h3>

<table>
<tr><th>단계</th><th>sensory_preference 신호</th><th>의미</th></tr>
<tr><td>Phase 1 (Profile, n=1,000)</td>
    <td>high {sn['profile_hints'].get('high',0)} ({sn['profile_hints'].get('high',0)/1000*100:.0f}%)
        / medium {sn['profile_hints'].get('medium',0)} ({sn['profile_hints'].get('medium',0)/1000*100:.0f}%)
        / low {sn['profile_hints'].get('low',0)} ({sn['profile_hints'].get('low',0)/1000*100:.0f}%)</td>
    <td>Profiler는 sensory가 <strong>책에 충분히 전이 가능</strong>하다고 판정</td></tr>
<tr><td>Phase 2 (Teacher, n=37)</td>
    <td><strong>BLOCK 97%</strong></td>
    <td>Teacher는 일괄 BLOCK</td></tr>
<tr><td>모순도</td><td><span class="fail">완전 반대</span></td>
    <td>같은 패턴을 두 단계에서 정반대로 판정</td></tr>
</table>

<h3>5.2 Profile의 sensory 사례 (high transferability)</h3>
{sens_profile_html}

<h3>5.3 Teacher의 sensory decision 사례 (BLOCK)</h3>
{sens_teacher_html}

<h3>5.4 진단 — "sensory" 단일 라벨이 너무 광범위</h3>

<p>sensory_preference는 영화에서 <strong>두 가지 다른 신호</strong>를 포함:</p>

<table>
<tr><th>하위 유형</th><th>예시</th><th>책 전이 가능성</th></tr>
<tr><td><strong>Visual/Action Spectacle</strong></td>
    <td>"animation ahead of its time", "special effects", "explosions"</td>
    <td><span class="fail">BLOCK</span> — 책에는 영상이 없음</td></tr>
<tr><td><strong>Atmosphere / Imagery / Tone</strong></td>
    <td>"atmospheric, uplifting", "felt so real", "immersive"</td>
    <td><span class="pol-positive">TRANSFER</span> — 책에서 묘사·분위기로 직접 전이</td></tr>
</table>

<div class="callout-warn">
현재 Teacher 프롬프트는 두 유형을 구분 안 함. "sensory_preference = visual"로 보고 일괄 BLOCK.
결과적으로 <strong>책에 전이 가능한 atmosphere 신호도 BLOCK당해 학습 신호 손실</strong>.
</div>

<h3>5.5 수정 방향 — 옵션 A 우선 권장</h3>

<table>
<tr><th>옵션</th><th>내용</th><th>장단점</th><th>채택 여부</th></tr>
<tr><td><strong>A (보수) — 프롬프트 보강</strong></td>
    <td>sensory_preference 정의에 두 하위 유형 명시.<br>
    "visual/sound/action spectacle → BLOCK / atmosphere/imagery/tone → consider TRANSFER"</td>
    <td>Phase 1 통계·overview·논문 구조 변경 없음. 검증 비용 낮음.</td>
    <td><span class="pass">✅ 1차 채택</span></td></tr>
<tr><td>B (적극) — 패턴 분리</td>
    <td><code>sensory_preference</code>를 <code>visual_spectacle</code>과
    <code>atmosphere_preference</code> 두 패턴으로 분리</td>
    <td>Phase 1 Profile 재생성 외에 overview v6, 학습 가설·EDA·논문 contribution 절 등 다수 문서 동시 수정.
    리스크 큼.</td>
    <td><span class="warn">⏸ 1차에서 보류</span></td></tr>
</table>

<div class="callout-green">
<strong>의사결정</strong>: 본 실험 안정성을 위해 <strong>옵션 A를 우선 적용</strong>.
A1~B2 수정 후 trial v2에서 sensory의 BLOCK 비율이 여전히 95% 이상이라면 옵션 B 검토 또는
"sensory의 단일 패턴 한계"를 논문의 Limitation 절에 명시.
</div>

<!-- ====== 종합 수정 계획 ====== -->
<h2 class="pagebreak">6. 종합 수정 계획</h2>

<h3>6.1 단계별 일정</h3>

<table>
<tr><th>단계</th><th>작업</th><th>비용</th><th>시간</th><th>차단성</th></tr>
<tr><td><strong>A1</strong></td><td>run_profiler.py에 GT timestamp cutoff 추가</td><td>-</td><td>0.5일</td><td>본 실행 필수</td></tr>
<tr><td><strong>A2</strong></td><td>run_teacher.py에 후보 membership·중복·title 검증 추가</td><td>-</td><td>0.5일</td><td>본 실행 필수</td></tr>
<tr><td><strong>A3</strong></td><td>books_meta author_name 파싱 재실행 + EDA 수치 재계산</td><td>-</td><td>0.5일</td><td>EDA 수정</td></tr>
<tr><td><strong>A4</strong></td><td>sensory_preference 프롬프트 분리 또는 sub-type 명시</td><td>-</td><td>0.3일</td><td>품질 개선</td></tr>
<tr><td><strong>B1</strong></td><td>Profile 1,000명 재생성 (temporal cutoff 적용)</td><td>$0.83</td><td>4h</td><td>본 실행 필수</td></tr>
<tr><td><strong>B2</strong></td><td>Teacher 50명 trial v2 (수정된 파이프라인)</td><td>$0.11</td><td>1.5h</td><td>검증</td></tr>
<tr><td><strong>B3</strong></td><td>GT hint blind audit (20~30명)</td><td>$0.05</td><td>30분</td><td>논문 방어</td></tr>
<tr><td><strong>B4</strong></td><td>trial v1 vs v2 비교 보고서 작성</td><td>-</td><td>0.5일</td><td>품질 보증</td></tr>
<tr><td><strong>C1</strong></td><td>Teacher 900명 본 실행 (검증 완료 후)</td><td>$2.0</td><td>~10h</td><td>다음 단계</td></tr>
</table>

<h3>6.2 데이터 보존 정책</h3>

<table>
<tr><th>현재 산출물 (v1)</th><th>처리</th></tr>
<tr><td><code>profiler_outputs/</code> (1,000개)</td><td>보존 → <code>profiler_outputs_v1/</code>로 이름 변경 후 v2 새로 생성</td></tr>
<tr><td><code>teacher_outputs/</code> (50개)</td><td>보존 → <code>teacher_outputs_v1/</code>로 이름 변경 후 v2 새로 생성</td></tr>
<tr><td><code>data/teacher_train_50.jsonl</code></td><td>보존 → <code>teacher_train_50_v1.jsonl</code>로 이름 변경</td></tr>
<tr><td>Phase 1 Report PDF</td><td>v2 발행 시 본 결함 분석을 §11로 추가, 학습용 부적합 명시</td></tr>
</table>

<h3>6.3 우선순위 — A1·A2가 최상위 (외부 리뷰 확정)</h3>

<table>
<tr><th>층위</th><th>작업</th><th>이유</th></tr>
<tr><td><span class="fail">⚡ Tier 0 (최상위)</span></td>
    <td>A1 (Profiler temporal cutoff), A2 (Teacher 검증 강화)</td>
    <td>두 결함이 막히지 않으면 이후 모든 실험 결과의 의미가 흔들림.
    "실험 자체가 유효한가"의 전제조건.</td></tr>
<tr><td>Tier 1</td><td>B1 (Profile 1,000명 재생성)</td>
    <td>A1 적용 후 즉시 필요. v1 보존 + v2 새로 생성.</td></tr>
<tr><td>Tier 2</td><td>A3 (author 파싱), A4 (sensory 프롬프트 옵션 A)</td>
    <td>품질 개선이지만 본 실험 차단은 아님. B1과 병렬 가능.</td></tr>
<tr><td>Tier 3</td><td>B2~B4 (trial v2·blind audit·비교 보고서)</td>
    <td>검증 단계. 통과 기준(§7) 충족 여부가 본 실행 결정.</td></tr>
<tr><td>Tier 4</td><td>C1 (900명 본 실행)</td>
    <td>§7 통과 기준 모두 충족 후에만 진행.</td></tr>
</table>

<h3>6.4 데이터 보존 정책</h3>

<table>
<tr><th>현재 산출물 (v1)</th><th>처리</th></tr>
<tr><td><code>profiler_outputs/</code> (1,000개)</td><td>보존 → <code>profiler_outputs_v1/</code>로 이름 변경 후 v2 새로 생성</td></tr>
<tr><td><code>teacher_outputs/</code> (50개)</td><td>보존 → <code>teacher_outputs_v1/</code>로 이름 변경 후 v2 새로 생성</td></tr>
<tr><td><code>data/teacher_train_50.jsonl</code></td><td>보존 → <code>teacher_train_50_v1.jsonl</code>로 이름 변경</td></tr>
<tr><td>Phase 1 Report PDF</td><td>v2 발행 시 본 결함 분석을 §11로 추가, 학습용 부적합 명시</td></tr>
</table>

<!-- ====== Trial v2 Acceptance Criteria ====== -->
<h2 class="pagebreak">7. Trial v2 통과 기준 (Acceptance Criteria)</h2>

<p>Trial v2(B2 단계) 결과가 다음 8개 정량 기준을 <strong>전부 만족</strong>해야 본 실행(C1) 진입.
기준 미달 시 코드·프롬프트 추가 수정 후 trial v3 재실행.</p>

<h3>7.1 절대 기준 — 0이 아니면 실패 (Hard Constraints)</h3>

<table>
<tr><th>#</th><th>지표</th><th>v1 (현재)</th><th>v2 통과 기준</th><th>검증 방법</th></tr>
<tr><td>1</td><td>후보 밖 추천 (out-of-candidate)</td>
    <td><span class="fail">30/37 (134건)</span></td>
    <td><strong>0건</strong></td>
    <td>recommendations[i].item_id ∈ 후보 50개</td></tr>
<tr><td>2</td><td>중복 추천 (duplicate item_id)</td>
    <td><span class="fail">16/37</span></td>
    <td><strong>0건</strong></td>
    <td>len(rec_ids) == len(set(rec_ids))</td></tr>
<tr><td>3</td><td>title mismatch (id-title 불일치)</td>
    <td><span class="fail">15/37</span></td>
    <td><strong>0건</strong></td>
    <td>books_meta lookup 결과와 title 일치</td></tr>
<tr><td>4</td><td>BLOCK leakage (BLOCK 패턴이 recommendations 사용)</td>
    <td>0건 (v1도 통과)</td>
    <td><strong>0건</strong></td>
    <td>blocked_patterns_summary 검증 (기존)</td></tr>
<tr><td>5</td><td>GT leakage text (rationale에 GT title 노출)</td>
    <td>0건 (v1도 통과)</td>
    <td><strong>0건</strong></td>
    <td>rationale·insight 텍스트에 GT title 부분문자열 검색</td></tr>
</table>

<h3>7.2 분포 기준 — 범위 충족 (Soft Constraints)</h3>

<table>
<tr><th>#</th><th>지표</th><th>v1 (현재)</th><th>v2 통과 기준</th><th>실패 시 조치</th></tr>
<tr><td>6</td><td>학습 데이터 채택율 (valid training acceptance rate)</td>
    <td>37/50 = 74%</td>
    <td><strong>≥ 60~70%</strong></td>
    <td>이하 시 GT Top-10 필터 완화 또는 candidate pool 확장 검토</td></tr>
<tr><td>7</td><td>temporal cutoff 후 Source 리뷰 ≥ 15개 사용자 비율</td>
    <td>미측정 (cutoff 없음)</td>
    <td>50명 중 <strong>일부 누락 허용</strong>,<br>다만 누락 사용자는 segment로 분리·기록</td>
    <td>1,000명 본 실행 시 cutoff 후 &lt;15 리뷰 사용자 별도 트래킹</td></tr>
<tr><td>8</td><td>7-pattern 완전성</td>
    <td>37/37 (100%)</td>
    <td><strong>100%</strong></td>
    <td>JSON 검증 단계에서 즉시 fail</td></tr>
</table>

<h3>7.3 검증 자동화</h3>

<p>위 8개 기준을 trial 실행 직후 자동 측정하는 <code>scripts/validate_teacher_trial.py</code>를 작성.
출력 예시:</p>

<div class="callout">
<pre style="font-size: 9pt; margin: 0;">
=== Trial v2 Acceptance Check (n=50) ===
[1] out-of-candidate ........... 0 / 50    ✅ PASS
[2] duplicate recommendations .. 0 / 50    ✅ PASS
[3] title mismatch ............. 0 / 50    ✅ PASS
[4] BLOCK leakage .............. 0 / 50    ✅ PASS
[5] GT title leakage in text ... 0 / 50    ✅ PASS
[6] training acceptance rate ... 34/50 = 68%  ✅ PASS (>=60%)
[7] cutoff_short_reviews_users . 4 / 50 → segmented separately
[8] 7-pattern completeness ..... 50/50    ✅ PASS

ALL CRITERIA PASS → C1 (900명 본 실행) 진입 가능</pre>
</div>

<h3>7.4 통과 시 다음 단계 (C1)</h3>

<div class="callout-green">
<strong>v2 trial이 8개 기준 모두 통과한 경우에만 900명 본 실행 진입.</strong><br>
하나라도 실패 시 원인 분석 → A1~A4 또는 프롬프트 재조정 → trial v3 재실행.
"검증된 파이프라인 → 큰 실행"의 순서를 절대 어기지 않음.
</div>

<h3>6.5 최종 결정</h3>

<div class="callout-green">
<strong>본 보고서로 결함 5개 모두 파악·우선순위 확정 + v2 통과 기준 정량화 완료.</strong><br>
다음 단계: 수정 계획 A1→A4 코드 작업 → B1~B4 재실행 → §7 통과 기준 검증 → C1 본 실행.<br>
v1 데이터는 보존하여 v2와 비교 가능한 형태로 활용.
</div>

</body>
</html>
"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    weasyprint.HTML(string=html).write_pdf(str(OUTPUT_PATH))
    print(f"✅ Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
