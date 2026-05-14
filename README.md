# TransferJudge — Selective Transfer for Cross-Domain Recommendation

A Profiler-Judge LLM-Based Framework for Cold-Start CDR (Movies → Books)

저자: 곽민아 (빅데이터학과 17기 석사 졸업논문)

## 개요

본 연구는 영화 도메인의 사용자 취향을 책 도메인 추천에 **선택적으로 전이**(Selective Transfer)
하는 새로운 cold-start CDR 프레임워크를 제안한다. 핵심 가설:

> "모든 사용자 취향 패턴이 도메인 간 전이 가능한 것은 아니다. 어떤 패턴은 매체 특정적이며,
> 강제 전이 시 부정 효과를 일으킨다."

이를 검증하기 위해 7개 core preference pattern에 대해 **TRANSFER / PARTIAL / BLOCK**의
3단계 Transfer Gate를 LLM 기반으로 결정하는 **Judge 모델**(Qwen3-14B QLoRA)을 학습한다.

## 파이프라인 5단계

| Phase | 내용 | 입력 | 출력 | 모델 |
|-------|------|------|------|------|
| Phase 0 | EDA + 전처리 | Amazon Reviews 2023 raw | `data/*_filtered.parquet` | - |
| Phase 1 | Profile 생성 | 영화 리뷰 30개 | `profiler_outputs/*.json` | GPT-4o-mini |
| Phase 2 | Teacher Distillation | Profile + 후보 50권 + GT 힌트 | `data/teacher_train_main.jsonl` | GPT-4o-mini |
| **Phase 3** | **Judge QLoRA 학습** | 학습 데이터 578줄 | LoRA adapter | **Qwen3-14B** (RunPod) |
| Phase 4·5 | Ablation + 평가 | 학습된 Judge | 평가 결과 | Qwen3-14B |

## 데이터 통계

| 항목 | 값 |
|------|-----|
| 본 실험 cohort | 1,000명 (Source≥15, Target 5–10, temporal cutoff 통과) |
| Profile 보유 | 1,000명 (100%) |
| **학습 데이터 (train)** | **578줄** |
| valid (튜닝) | 100명 |
| test (평가) | 100명 |
| **Train ∩ (Valid ∪ Test) 누수** | **0건** ✅ |

자세한 검증 결과는 `docs/phase2/Phase2_Final_Report.pdf` 참조.

## 디렉토리 구조

```
.
├── README.md                              # 본 문서
├── requirements.txt                       # Python 의존성
├── experiment_plan.md                     # 본 연구 실험 계획서
├── data/
│   ├── teacher_train_main.jsonl           # 학습 데이터 578줄
│   ├── train_users.parquet                # 578명
│   ├── valid_users.parquet                # 100명
│   ├── test_users.parquet                 # 100명
│   ├── main_experiment_users.parquet      # 778명 (train + valid + test)
│   ├── *_reviews_filtered.parquet         # Movies/Books 리뷰 (작은 파일)
│   └── (books_meta_filtered.parquet은 HF Hub에서 다운로드)
├── scripts/
│   ├── run_profiler.py                    # Phase 1
│   ├── run_teacher.py                     # Phase 2
│   ├── train_judge.py                     # Phase 3 (QLoRA 학습)
│   ├── validate_teacher_trial.py          # §7 통과 기준 검증
│   ├── redefine_splits.py                 # data leakage 방지 split 재정의
│   ├── clean_training_data.py             # orphan·low-signal·title 정합성 정리
│   ├── upload_data_to_hub.py              # books_meta → HF Hub
│   └── download_data_runpod.py            # RunPod에서 books_meta 다운로드
├── profiler_outputs/                      # Phase 1 Profile JSON (1,000개)
├── docs/
│   ├── overview/                          # 개요 PDF
│   ├── phase1/                            # Phase 1 Profile 보고서
│   ├── phase2/                            # Phase 2 Teacher 보고서
│   │   ├── Phase2_Final_Report.pdf
│   │   ├── Phase2_Data_Lineage.pdf
│   │   └── Phase2_Defect_Analysis.pdf
│   ├── pilot/                             # Pilot Study 보고서
│   ├── eda/                               # EDA 보고서
│   └── plans/                             # 실험 트래커
└── notebooks/
    └── eda.ipynb                          # Phase 0 EDA 노트북
```

## RunPod 환경 셋업

### 1. 저장소 클론

```bash
git clone https://github.com/<USERNAME>/transferjudge.git
cd transferjudge
```

### 2. Python 환경

```bash
pip install -r requirements.txt
```

### 3. books_meta 다운로드 (HF Hub)

```bash
export HF_TOKEN=hf_...
python3 scripts/download_data_runpod.py --repo <USERNAME>/transferjudge-data
```

### 4. Phase 3 학습 실행

```bash
python3 scripts/train_judge.py \
  --training-data data/teacher_train_main.jsonl \
  --model Qwen/Qwen3-14B \
  --output checkpoints/judge_v1 \
  --batch-size 1 --grad-accum 16 --epochs 3 --lr 2e-4
```

예상: A100 80GB 1대로 6~8시간, $3~$5.

## 결함 수정 이력 (Codex 외부 리뷰)

본 연구는 외부 LLM 리뷰(Codex)로 발견한 결함을 모두 수정한 v2 파이프라인을 사용:

| # | 결함 | 수정 |
|---|------|------|
| 1 | Profile temporal leakage (사용자 64% 영향) | Profiler에 GT timestamp cutoff |
| 2 | Teacher 후보 외 환각 추천 (81%) | validation 5종 + ALLOWED_IDS 블록 |
| 3 | author_name 100% 결측 (EDA 오보) | raw HF 캐시 재파싱 (0 → 64.5%) |
| 4 | sensory_preference 일괄 BLOCK (97%) | subtype 분리 프롬프트 |
| 5 | Train·Test data leakage (95명 overlap) | split 재정의 (누수 0) |
| 6 | System prompt GT 잔재 (5회) | 후처리 제거 |
| 7 | Orphan record + low-signal profile | 24건 추가 제거 |
| 8 | Title exact mismatch (79건) | books_meta 기준 정규화 |

자세한 비교는 `docs/phase2/Phase2_Final_Report.pdf` §4 참조.

## 라이선스 및 인용

본 연구는 학위논문 목적. Amazon Reviews 2023 dataset의 라이선스를 따른다.

```bibtex
@mastersthesis{kwak2026transferjudge,
  title={TransferJudge: A Profiler-Judge LLM Framework for Selective Transfer in Cross-Domain Recommendation},
  author={Kwak, Mina},
  year={2026},
  school={Big Data Department}
}
```
