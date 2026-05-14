"""TransferJudge 프레임워크 다이어그램 (한 장짜리 PDF).

3단 수직 레이아웃:
  Stage 1. 데이터 구축
  Stage 2. 학습 파이프라인 (Teacher Distillation + QLoRA)
  Stage 3. 추론 프레임워크 (Profiler -> Transfer Judge)

용지: 가로 A3
생성: docs/TransferJudge_Framework_Diagram.pdf
"""
from pathlib import Path
from weasyprint import HTML, CSS

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "docs"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "TransferJudge_Framework_Diagram.pdf"

HTML_CONTENT = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>TransferJudge Framework Diagram</title>
</head>
<body>

<div class="page">

  <div class="title-bar">
    <div class="title-ko">TransferJudge: 선택적 전이를 위한 Profiler-Judge 구조의 LLM 기반 교차 도메인 추천 프레임워크</div>
    <div class="title-en">A Profiler-Judge LLM-Based Framework for Selective Transfer in Cross-Domain Recommendation</div>
  </div>

  <!-- ========== STAGE 1 ========== -->
  <div class="stage stage-1">
    <div class="stage-head">
      <span class="stage-label">Stage 1</span>
      <span class="stage-title">데이터 구축 · Data Construction</span>
      <span class="stage-desc">Amazon Reviews 2023에서 Overlapping User를 추출하고 LOO 분할로 학습·평가 데이터 구성</span>
    </div>

    <div class="stage-body">
      <div class="node data">
        <div class="node-title">원본 데이터</div>
        <div class="node-sub">Amazon Reviews 2023<br>(McAuley Lab)</div>
        <div class="node-meta">Movies&amp;TV · Books</div>
      </div>
      <div class="arrow">&#10140;</div>
      <div class="node process">
        <div class="node-title">전처리 · 필터링</div>
        <div class="node-sub">Overlapping User 추출<br>Source &ge; 15, Target 5-10</div>
        <div class="node-meta">22,465명</div>
      </div>
      <div class="arrow">&#10140;</div>
      <div class="node process">
        <div class="node-title">샘플링 · 분할</div>
        <div class="node-sub">1,000명 무작위 추출<br>Train 800 / Valid 100 / Test 100</div>
        <div class="node-meta">LOO (Leave-One-Out)</div>
      </div>
      <div class="arrow">&#10140;</div>
      <div class="node output">
        <div class="node-title">사용자별 구성</div>
        <div class="dataset-spec">
          <div><b>Source</b>: Movies&amp;TV 최근 15-30개 리뷰</div>
          <div><b>Target</b>: Books 5-10개 (Cold-Start)</div>
          <div><b>GT</b>: rating &ge; 4 중 가장 최근 1건</div>
          <div><b>Candidates</b>: Books 후보 50개</div>
        </div>
      </div>
    </div>
  </div>

  <!-- ========== STAGE 2 ========== -->
  <div class="stage stage-2">
    <div class="stage-head">
      <span class="stage-label">Stage 2</span>
      <span class="stage-title">학습 파이프라인 · Training Pipeline</span>
      <span class="stage-desc">Teacher(GPT-4o-mini)의 판단을 증류하여 경량 LLM(Qwen3-14B)을 QLoRA로 파인튜닝</span>
    </div>

    <div class="stage-body training-body">
      <div class="col">
        <div class="node api teacher">
          <div class="node-badge">API (Cloud)</div>
          <div class="node-title">Teacher LLM</div>
          <div class="node-sub">GPT-4o-mini</div>
          <div class="node-meta">Few-shot Prompting</div>
        </div>
        <div class="io-block">
          <div class="io-label">입력 (Input)</div>
          <div class="io-content">
            Source 리뷰 + Target 후보 1건<br>
            + Few-shot 예시 3건
          </div>
        </div>
        <div class="io-block">
          <div class="io-label">출력 (Output)</div>
          <div class="io-content">
            {<br>
            &nbsp;&nbsp;"decision": "TRANSFER",<br>
            &nbsp;&nbsp;"score": 0.82,<br>
            &nbsp;&nbsp;"reason": "..."<br>
            }
          </div>
        </div>
      </div>

      <div class="arrow-v">
        <span class="arrow-label">레이블 생성<br>(Distillation)</span>
        <span class="arrow-mark">&#10140;</span>
      </div>

      <div class="col">
        <div class="node dataset">
          <div class="node-title">학습 데이터셋</div>
          <div class="node-sub">
            입력: 리뷰 + 후보<br>
            출력: 판단 + 점수 + 이유
          </div>
          <div class="node-meta">~50,000 샘플 (800명 &times; 평균 60 후보)</div>
        </div>
      </div>

      <div class="arrow-v">
        <span class="arrow-label">Supervised<br>Fine-tuning</span>
        <span class="arrow-mark">&#10140;</span>
      </div>

      <div class="col">
        <div class="node local student">
          <div class="node-badge">Local (Trained)</div>
          <div class="node-title">Student LLM</div>
          <div class="node-sub">Qwen3-14B + QLoRA</div>
          <div class="node-meta">4bit Quantization · LoRA rank 16</div>
        </div>
        <div class="io-block">
          <div class="io-label">학습 설정</div>
          <div class="io-content">
            Epochs: 3<br>
            LR: 2e-4 (cosine)<br>
            Batch: 4 &times; grad_accum 8
          </div>
        </div>
        <div class="io-block highlight">
          <div class="io-label">산출물</div>
          <div class="io-content">
            <b>Transfer Judge 모델</b><br>
            (Fine-tuned Qwen3-14B)
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ========== STAGE 3 ========== -->
  <div class="stage stage-3">
    <div class="stage-head">
      <span class="stage-label">Stage 3</span>
      <span class="stage-title">추론 프레임워크 · Inference Framework</span>
      <span class="stage-desc">Profiler가 Source 리뷰에서 Core Pattern을 추출하고, Transfer Judge가 후보별 전이 여부를 판단</span>
    </div>

    <div class="stage-body inference-body">

      <div class="input-col">
        <div class="input-box">
          <div class="input-title">사용자 Source 리뷰</div>
          <div class="input-sub">Movies&amp;TV 15-30개</div>
        </div>
        <div class="input-box">
          <div class="input-title">Target 후보 아이템</div>
          <div class="input-sub">Books 50개</div>
        </div>
      </div>

      <div class="flow-col">
        <!-- Step 1: Profiler -->
        <div class="inference-step">
          <div class="step-num">1</div>
          <div class="node api profiler">
            <div class="node-badge">API (Cloud)</div>
            <div class="node-title">Profiler</div>
            <div class="node-sub">GPT-4o-mini</div>
            <div class="node-meta">선호 패턴 추출</div>
          </div>
        </div>

        <div class="arrow">&#10140;</div>

        <!-- Core Pattern -->
        <div class="core-pattern">
          <div class="cp-title">Core Pattern (6차원 선호)</div>
          <ul class="cp-list">
            <li><b>genre_preference</b> &mdash; 장르 선호</li>
            <li><b>narrative_complexity</b> &mdash; 서사 복잡도</li>
            <li><b>pacing_preference</b> &mdash; 전개 속도 선호</li>
            <li><b>quality_sensitivity</b> &mdash; 품질 민감도</li>
            <li><b>brand_loyalty</b> &mdash; 브랜드/작가 충성도</li>
            <li><b>sensory_preference</b> &mdash; 감각적 선호</li>
          </ul>
        </div>

        <div class="arrow">&#10140;</div>

        <!-- Step 2: Judge -->
        <div class="inference-step">
          <div class="step-num">2</div>
          <div class="node local judge">
            <div class="node-badge">Local (Fine-tuned)</div>
            <div class="node-title">Transfer Judge</div>
            <div class="node-sub">Qwen3-14B + QLoRA</div>
            <div class="node-meta">후보별 전이 판단</div>
          </div>
        </div>

        <div class="arrow">&#10140;</div>

        <!-- Decision -->
        <div class="decision-box">
          <div class="dec-title">전이 판단 결과 (후보별)</div>
          <div class="dec-items">
            <span class="dec transfer">TRANSFER</span>
            <span class="dec partial">PARTIAL</span>
            <span class="dec block">BLOCK</span>
          </div>
          <div class="dec-note">+ score + reason</div>
        </div>

        <div class="arrow">&#10140;</div>

        <!-- Output -->
        <div class="output-box">
          <div class="out-title">최종 추천 Top-K</div>
          <div class="out-sub">BLOCK 제외 &middot; score 기준 정렬</div>
        </div>
      </div>

    </div>
  </div>

  <!-- Legend -->
  <div class="legend">
    <span class="legend-item"><span class="swatch api-c"></span> API (Cloud) 모델</span>
    <span class="legend-item"><span class="swatch local-c"></span> 로컬 파인튜닝 모델</span>
    <span class="legend-item"><span class="swatch data-c"></span> 데이터 / 산출물</span>
    <span class="legend-item"><span class="swatch proc-c"></span> 처리 단계</span>
  </div>

</div>

</body>
</html>
"""

CSS_CONTENT = r"""
@page {
  size: A3 landscape;
  margin: 12mm 14mm;
}

* { box-sizing: border-box; }

body {
  font-family: "Apple SD Gothic Neo", "Noto Sans KR", "Helvetica Neue", sans-serif;
  font-size: 10pt;
  color: #1a1a1a;
  margin: 0;
}

.page {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 6mm;
}

/* ---------- Title Bar ---------- */
.title-bar {
  border-left: 6px solid #2d3e8a;
  padding: 4mm 6mm;
  background: #f4f6fb;
}
.title-ko {
  font-size: 16pt;
  font-weight: 700;
  color: #1a2555;
}
.title-en {
  font-size: 10.5pt;
  color: #555;
  margin-top: 1.5mm;
  font-style: italic;
}

/* ---------- Stage Common ---------- */
.stage {
  border: 1px solid #d5dae6;
  border-radius: 3mm;
  overflow: hidden;
}
.stage-head {
  padding: 2.5mm 5mm;
  background: #eaeef7;
  border-bottom: 1px solid #d5dae6;
  display: flex;
  align-items: baseline;
  gap: 4mm;
}
.stage-label {
  background: #2d3e8a;
  color: #fff;
  padding: 1mm 3mm;
  border-radius: 2mm;
  font-size: 9pt;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.stage-title {
  font-size: 13pt;
  font-weight: 700;
  color: #1a2555;
}
.stage-desc {
  font-size: 9.5pt;
  color: #555;
  margin-left: auto;
  font-style: italic;
}

.stage-body {
  padding: 5mm 6mm;
  display: flex;
  align-items: center;
  gap: 3mm;
}

/* ---------- Nodes ---------- */
.node {
  border: 1.2px solid #888;
  border-radius: 2.5mm;
  padding: 3mm 4mm;
  min-width: 42mm;
  background: #fff;
  text-align: center;
  flex-shrink: 0;
}
.node-title {
  font-weight: 700;
  font-size: 10.5pt;
  margin-bottom: 1mm;
  color: #1a2555;
}
.node-sub {
  font-size: 9pt;
  color: #333;
  margin-bottom: 1mm;
  line-height: 1.3;
}
.node-meta {
  font-size: 8.5pt;
  color: #666;
  font-style: italic;
}
.node-badge {
  display: inline-block;
  font-size: 7.5pt;
  padding: 0.5mm 2mm;
  border-radius: 1mm;
  margin-bottom: 1.5mm;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* Node color variants */
.data { background: #fff4e6; border-color: #e08a3c; }
.process { background: #f0f4ff; border-color: #6b7cb5; }
.output { background: #e6f4ea; border-color: #3c8a4f; min-width: 58mm; }

.api { background: #e7f1fb; border-color: #2f7bc4; }
.api .node-badge { background: #2f7bc4; color: #fff; }

.local { background: #e6f6ed; border-color: #2f9a53; }
.local .node-badge { background: #2f9a53; color: #fff; }

.dataset { background: #fff8d9; border-color: #c4a23c; min-width: 60mm; }

/* ---------- Arrows ---------- */
.arrow {
  font-size: 20pt;
  color: #2d3e8a;
  flex-shrink: 0;
}
.arrow-v {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1mm;
  flex-shrink: 0;
}
.arrow-label {
  font-size: 8.5pt;
  color: #2d3e8a;
  font-style: italic;
  text-align: center;
  line-height: 1.2;
}
.arrow-mark {
  font-size: 18pt;
  color: #2d3e8a;
}

/* ---------- Stage 1 specific ---------- */
.dataset-spec {
  font-size: 8.8pt;
  text-align: left;
  line-height: 1.5;
}
.dataset-spec div { margin-bottom: 0.5mm; }

/* ---------- Stage 2 specific ---------- */
.training-body {
  justify-content: space-between;
  align-items: stretch;
}
.training-body .col {
  display: flex;
  flex-direction: column;
  gap: 2mm;
  flex: 1;
  max-width: 78mm;
}
.io-block {
  border: 1px solid #ccc;
  border-radius: 2mm;
  padding: 2mm 3mm;
  background: #fafafa;
  font-size: 8.8pt;
}
.io-block.highlight {
  background: #fff3cd;
  border-color: #c4a23c;
  font-weight: 600;
}
.io-label {
  font-weight: 700;
  font-size: 8.5pt;
  color: #2d3e8a;
  margin-bottom: 0.8mm;
}
.io-content {
  font-size: 8.7pt;
  line-height: 1.35;
  color: #333;
  font-family: "SF Mono", "Menlo", monospace;
  font-family: "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
}

/* ---------- Stage 3 specific ---------- */
.inference-body {
  gap: 4mm;
}
.input-col {
  display: flex;
  flex-direction: column;
  gap: 3mm;
  flex-shrink: 0;
}
.input-box {
  border: 1.5px dashed #888;
  border-radius: 2mm;
  padding: 3mm 4mm;
  background: #fff;
  text-align: center;
  min-width: 42mm;
}
.input-title {
  font-weight: 700;
  font-size: 10pt;
  color: #1a2555;
}
.input-sub {
  font-size: 8.8pt;
  color: #555;
  margin-top: 1mm;
}

.flow-col {
  display: flex;
  align-items: center;
  gap: 2.5mm;
  flex: 1;
  flex-wrap: nowrap;
}

.inference-step {
  position: relative;
  flex-shrink: 0;
}
.step-num {
  position: absolute;
  top: -3mm;
  left: -3mm;
  width: 6mm;
  height: 6mm;
  background: #2d3e8a;
  color: #fff;
  border-radius: 50%;
  text-align: center;
  line-height: 6mm;
  font-weight: 700;
  font-size: 9.5pt;
  z-index: 2;
}

.core-pattern {
  border: 1.2px solid #6b7cb5;
  border-radius: 2mm;
  padding: 2.5mm 3.5mm;
  background: #f0f4ff;
  flex-shrink: 0;
  min-width: 50mm;
}
.cp-title {
  font-weight: 700;
  font-size: 9.5pt;
  color: #1a2555;
  margin-bottom: 1.5mm;
  text-align: center;
  border-bottom: 1px solid #c5cee8;
  padding-bottom: 1mm;
}
.cp-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 8.4pt;
  line-height: 1.45;
}
.cp-list li {
  padding-left: 2.5mm;
  position: relative;
}
.cp-list li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: #2d3e8a;
  font-weight: 700;
}

.decision-box {
  border: 1.2px solid #888;
  border-radius: 2mm;
  padding: 3mm;
  background: #fff;
  text-align: center;
  flex-shrink: 0;
  min-width: 48mm;
}
.dec-title {
  font-size: 9pt;
  font-weight: 700;
  color: #1a2555;
  margin-bottom: 1.5mm;
}
.dec-items {
  display: flex;
  gap: 1.5mm;
  justify-content: center;
  margin-bottom: 1mm;
}
.dec {
  padding: 0.8mm 2mm;
  border-radius: 1.5mm;
  font-size: 8pt;
  font-weight: 700;
  color: #fff;
}
.dec.transfer { background: #2f9a53; }
.dec.partial  { background: #d79a2e; }
.dec.block    { background: #b53a3a; }
.dec-note {
  font-size: 8.2pt;
  color: #666;
  font-style: italic;
}

.output-box {
  border: 2px solid #2d3e8a;
  border-radius: 2.5mm;
  padding: 3mm 4mm;
  background: #eaeef7;
  text-align: center;
  flex-shrink: 0;
  min-width: 42mm;
}
.out-title {
  font-size: 10pt;
  font-weight: 700;
  color: #1a2555;
}
.out-sub {
  font-size: 8.5pt;
  color: #555;
  margin-top: 1mm;
}

/* ---------- Legend ---------- */
.legend {
  display: flex;
  gap: 8mm;
  padding: 2mm 5mm;
  font-size: 9pt;
  color: #555;
  border-top: 1px dashed #ccc;
  justify-content: center;
}
.legend-item { display: inline-flex; align-items: center; gap: 2mm; }
.swatch {
  display: inline-block;
  width: 4mm;
  height: 4mm;
  border-radius: 1mm;
  border: 1px solid #888;
}
.swatch.api-c   { background: #e7f1fb; border-color: #2f7bc4; }
.swatch.local-c { background: #e6f6ed; border-color: #2f9a53; }
.swatch.data-c  { background: #fff4e6; border-color: #e08a3c; }
.swatch.proc-c  { background: #f0f4ff; border-color: #6b7cb5; }
"""


def main() -> None:
    HTML(string=HTML_CONTENT).write_pdf(
        str(OUTPUT_PATH),
        stylesheets=[CSS(string=CSS_CONTENT)],
    )
    print(f"Generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
