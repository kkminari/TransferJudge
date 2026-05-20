# RQ1 보강 작업 플랜 — Base Qwen3-14B (Pre-FT) 평가

> **이 파일의 목적**: 작업이 중단되어도 이 파일만 보면 어디까지 됐고 무엇을 해야 할지 명확히 파악할 수 있도록 함. 진행할 때마다 체크박스 갱신.
>
> **마지막 업데이트**: 2026-05-19

---

## 1. 목적 (Why)

RQ1 보강: **Fine-tuning이 실제로 효과가 있었는가?** 를 정량적으로 증명한다.

- **Pre-FT** (이번 작업): Base Qwen3-14B로 Cross-Domain Transfer Judge 작업 수행
  - Zero-shot: Teacher prompt만 주고 평가
  - Few-shot: Teacher prompt + 3개 in-context 예시
- **Post-FT** (이미 측정 완료): Fine-tuned Qwen3-14B QLoRA 결과 → `results/ablation_c_ours.json`
- **비교 (Mac에서 별도 진행)**: `scripts/analysis/rq1_compare_pre_post_ft.py` 로 Pre vs Post FT
  - Teacher decisions 대비 agreement (overall + per-pattern)
  - Macro-F1, per-class F1 (TRANSFER/PARTIAL/BLOCK)
  - JSON format success rate
  - 7-pattern completeness

## 2. 환경

- **머신**: RunPod A100-SXM4-80GB (driver CUDA 13.0)
- **OS**: Linux 6.8.0-100-generic
- **Python**: 3.11.10 (system) → venv `.venv_thesis`
- **작업 디렉토리**: `/workspace/TransferJudge`
- **리포지토리**: https://github.com/kkminari/TransferJudge

## 3. 토큰 (보안: 작업 완료 후 반드시 폐기 후 재발급)

- `HF_TOKEN`: HuggingFace — Qwen3-14B 모델 다운로드 + private data repo 접근
- `GITHUB_PAT`: GitHub — 결과 push 용

**둘 다 작업 완료 후 ⚠️ 반드시 폐기**:
- https://github.com/settings/tokens
- https://huggingface.co/settings/tokens

## 4. 입출력 파일

### 입력 (이미 git에 있음 또는 다운로드 필요)
- `eval_fixtures/test_users.json` — 100명 test user fixture ✅ (git)
- `eval_fixtures/candidates/` — 후보 후보 books ✅ (git)
- `profiler_outputs/user_*.json` — preference profiles ✅ (git)
- `data/teacher_train_main.jsonl` — few-shot 예시 추출용 ✅ (git)
- `data/books_meta_filtered.parquet` (2.4GB) — ⬇️ HF Hub `majy468/transferjudge-data` 에서
- `data/movies_meta_filtered.parquet` (51MB) — ⬇️ HF Hub `majy468/transferjudge-data` 에서

### 출력 (이번 작업으로 생성)
- `results/analysis/rq1_pre_ft_qwen_zero_shot.json` — n=100, zero-shot decisions
- `results/analysis/rq1_pre_ft_qwen_few_shot.json` — n=100, few-shot decisions

## 5. 모델 & 추론 설정

- **모델**: `Qwen/Qwen3-14B` (HuggingFace)
- **양자화**: 4-bit (bitsandbytes), 일관성 위해 유지 (80GB 여유 있지만 prior 실험과 동일 setup)
- **max_new_tokens**: 2500
- **max_seq_length**: 12288
- **n_fewshot**: 3 (few-shot setting 시)
- **테스트 fixture**: 100명

## 6. 시간 예상

| Phase | 예상 시간 |
|---|---|
| Phase 1 환경세팅 | 10분 |
| Phase 2 데이터 DL | 10~15분 (2.5GB) |
| Phase 3 Smoke | 15~20분 |
| Phase 4-A zero_shot 본실행 | ~1.5시간 |
| Phase 4-B few_shot 본실행 | ~1.5~2시간 |
| Phase 5 Git push | 5분 |
| **총합** | **약 4~5시간** |

---

## 7. 진행 체크리스트

### Phase 1: 환경 세팅 ✅
- [x] `git clone https://github.com/kkminari/TransferJudge.git` → `/workspace/TransferJudge`
- [x] `python3 -m venv .venv_thesis`
- [x] `pip install --upgrade pip`
- [x] `pip install transformers accelerate bitsandbytes pandas pyarrow torch python-dotenv huggingface_hub` (분할 설치로 성공)
- [x] 검증: torch 2.12.0+cu130, A100-SXM4-80GB 인식 OK
- [x] 검증: transformers 5.8.1, accelerate 1.13.0, bitsandbytes 0.49.2, pandas 3.0.3, huggingface_hub 1.15.0

### Phase 2: 데이터 다운로드 ✅
- [x] `export HF_TOKEN=...` (셸 세션 변수)
- [x] `python scripts/download_data_runpod.py --repo kwaksuobusi/transferjudge-data` ⚠️ (사용자명: majy468 ❌ → kwaksuobusi ✅)
- [x] 검증: books 2.5G + movies 52M 확보

### Phase 3: Smoke Test (게이트) ✅
- [x] `mkdir -p results/analysis`
- [x] zero_shot smoke: `--setting zero_shot --limit 3 --output /tmp/smoke_zs.json` → 3/3 통과 (120s/user)
- [x] few_shot smoke: `--setting few_shot --limit 3 --max-seq-length 32768 --output /tmp/smoke_fs.json` → 3/3 통과 (132s/user)
- [x] 검증 게이트:
  - [x] JSON 정상 파싱 (3/3 양 setting)
  - [x] user 3명 모두 결과 있음
  - [x] 각 user 마다 7 패턴 모두 있음 (genre/narrative/pacing/quality/brand/sensory/emotional)
  - [x] decision 값 TRANSFER/PARTIAL/BLOCK 3종 한정
  - [x] 빈/잘린 응답 0건

**❗ 패치 사항 (이미 적용됨)**:
1. `apply_chat_template` 반환값이 transformers 5.x에서 BatchEncoding으로 바뀜 → tensor 추출 로직 추가
2. **Qwen3 thinking mode 기본 ON** → `enable_thinking=False`로 끔 (공정 비교: post-FT는 직접 JSON 출력하도록 학습됨)
3. few_shot의 input 토큰이 ~30k → `--max-seq-length 32768` 옵션 필수

### Phase 4-A: 본 실행 zero_shot (n=100) ✅
- [x] `.venv_thesis/bin/python scripts/analysis/rq1_pre_ft_qwen.py --setting zero_shot --output results/analysis/rq1_pre_ft_qwen_zero_shot.json`
- [x] 검증: 100/100 parse 성공, 7패턴 완비, elapsed 11730s (≈3h15m)

### Phase 4-B: 본 실행 few_shot (n=100) ✅
- [x] 백그라운드 실행 완료 (task ID `b31aom91m`)
- [x] 검증: 100/100 평가, parse 99/100 (99%), 7-pattern 완비 98/100, elapsed 12725s (≈3h32m)
- 문제 케이스 2건: 1명 모델이 8패턴 hallucinate, 1명 MAX_NEW_TOKENS=2500 한계로 잘림

### Phase 5: Git Push
- [ ] `git config user.email "majy468@gmail.com"`
- [ ] `git config user.name "kkminari"`
- [ ] `git remote set-url origin https://<PAT>@github.com/kkminari/TransferJudge.git`
- [ ] `git add results/analysis/rq1_pre_ft_qwen_*.json`
- [ ] `git commit -m "RQ1 보강 — base Qwen3-14B zero/few-shot 결과"`
- [ ] `git push origin main`

### Phase 6: 정리 (이번 작업 범위 외 — 사용자 직접)
- [ ] GitHub PAT 폐기 후 재발급
- [ ] HF Token 폐기 후 재발급
- [ ] Mac에서 `rq1_compare_pre_post_ft.py` 실행 → pre/post FT 비교 결과 산출

---

## 8. 위험 포인트 & 대응

| 위험 | 신호 | 대응 |
|---|---|---|
| pip install I/O 에러 | `OSError: [Errno 5]` | 재시도. NFS workspace 마운트 일시적 불안정 가능. pip 캐시 디렉토리를 `/root/.cache/pip` (overlay) 로 |
| OOM | CUDA OOM 에러 | `--max-seq-length` 12288 → 8192 |
| JSON 파싱 실패 다발 | smoke에서 빈 decisions | `MAX_NEW_TOKENS` 늘리기 or 프롬프트 조정 |
| tmux 세션 잃음 | pod restart | nohup으로 재실행 + `tail -f` |
| HF 401/403 | 권한 거부 | `HF_TOKEN` 재확인, repo private이면 본인 토큰 맞는지 |
| Git push 403 | permission denied | PAT scope에 `repo` 권한 |

## 9. 작업 재개 가이드 (중단된 경우)

이 파일의 **Phase 진행 체크리스트** 부분의 체크박스를 보고 다음을 수행:

1. 가장 마지막에 체크된 항목 다음부터 진행
2. Phase 1 `pip install` 실패 시 → 패키지 일부만 설치된 상태일 수 있음. `pip list | grep -iE "transformers|torch|..."` 로 무엇이 빠졌는지 확인하고 추가 설치
3. Phase 4 도중 끊김 → 출력 파일이 일부만 있을 가능성. 해당 setting을 처음부터 재실행 (스크립트는 incremental 지원하지 않을 수 있음)
4. Phase 5 push 실패 시 → 파일은 commit 되어있으므로 PAT만 갱신해서 push 재시도

## 10. 작업 로그

| 시각 | Phase | 이벤트 |
|---|---|---|
| 2026-05-19 14:54 | 0 | RunPod A100 확인, /workspace clone 완료 |
| 2026-05-19 ~15:00 | 1 | venv 생성, pip upgrade 완료 |
| 2026-05-19 ~15:00 | 1 | pip install 중 OSError I/O 에러로 일부만 설치됨 (pyarrow, python-dotenv만 성공) |
| 2026-05-19 ~15:10 | 1 | 재시도도 SIGKILL(137)로 죽음. /tmp/pip-* 정리 후 분할 설치로 전환 |
| 2026-05-19 ~15:15 | 1 | torch 단독 설치 성공 |
| 2026-05-19 ~15:18 | 1 | transformers/accelerate/huggingface_hub/pandas 일괄 설치 성공 |
| 2026-05-19 ~15:20 | 1 | bitsandbytes 설치 성공, 검증 통과 → Phase 1 완료 |
| 2026-05-19 ~16:30 | 2 | HF whoami: 사용자명은 `kwaksuobusi`. 재시도하여 데이터 다운로드 성공 → Phase 2 완료 |
| 2026-05-19 ~17:00 | 3 | zero_shot smoke #1: transformers 5.x apply_chat_template 반환 BatchEncoding 에러 → 패치 |
| 2026-05-19 ~17:10 | 3 | zero_shot smoke #2: parse 0/3 — Qwen3 thinking mode가 토큰 다 잡아먹음 → enable_thinking=False 패치 |
| 2026-05-19 ~17:20 | 3 | zero_shot smoke #3: parse 3/3 (100%), 120s/user. 게이트 통과 |
| 2026-05-19 ~17:30 | 3 | few_shot smoke #1: input 30k 토큰 > 12288 limit, 전부 skip + ZeroDivision → --max-seq-length 32768로 |
| 2026-05-19 ~17:40 | 3 | few_shot smoke #2: parse 3/3 (100%), 132s/user. 게이트 통과 → Phase 4 진입 |
| 2026-05-19 ~17:50 | 4-A | zero_shot 본 실행 시작 (background `byz08rezu`, ~3.3h 예상) |
| 2026-05-19 ~22:24 | 4-A | zero_shot 본 실행 완료 — 100/100 parse 성공, elapsed 11730s |
| 2026-05-20 00:38 | 4-B | few_shot 본 실행 시작 (background `b31aom91m`, ~3.7h 예상) |
| 2026-05-20 04:13 | 4-B | few_shot 본 실행 완료 — 99/100 parse 성공, elapsed 12725s |
| | | |
