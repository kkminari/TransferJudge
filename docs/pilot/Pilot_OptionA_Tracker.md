# Pilot Study 옵션 A — 진행 추적기

> **목표**: 7개 Core Pattern (6개 학술 표준 + emotional_resonance) 채택 정당화
> **방식**: 자기참조 회피 — 외부 학술 정의 + 자동 도구 검증
> **총 작업 시간**: 약 2.5시간 (사용자 검토 1번 + 자동 작업 4단계)
> **시작일**: ____ / 완료일: ____

---

## 진행 현황 한눈에 보기

```bash
# 언제든지 다음 명령으로 현재 진행도 확인 가능
python scripts/check_pilot_progress.py
```

| Step | 상태 | 산출물 | 시간 | 자동/수동 |
|:---:|:---:|------|:---:|:---:|
| 1 | ⬜ Pending | `prompts/core_patterns_definition.md` | ~1h | 🤖 자동 작성 → 👤 검토 |
| 2 | ⬜ Pending | `data/pilot_to_predefined_matching.csv` | ~30분 | 🤖 자동 |
| 3 | ⬜ Pending | `data/pilot_pattern_categories.csv` | ~30분 | 🤖 자동 |
| 4 | ⬜ Pending | `data/pilot_pattern_orthogonality.png` | ~15분 | 🤖 자동 |
| 5 | ⬜ Pending | `docs/Pilot_Study_Report.md` | ~45분 | 🤖 자동 |
| **Phase 6** | ⬜ Pending | 6개 문서·코드 동기화 | ~1.5h | 🤖 자동 |

**상태 표시**:
- ⬜ Pending (시작 전)
- 🟡 In Progress (작업 중)
- ✅ Completed (완료)
- 👤 Awaiting Review (사용자 검토 대기)

---

## Step 1 — 7개 패턴 정의서 작성

### 목표
7개 패턴 각각의 정의 + 학술 근거 + Movies/Books 예시 + Cross-Domain 가능성을 한 문서에 정리.

### 작업 흐름
1. [ ] AI가 `prompts/core_patterns_definition.md` 초안 작성
2. [ ] **사용자 검토** (자세히 읽고 학술 인용 적절한지 확인)
3. [ ] 사용자 승인 또는 수정 요청
4. [ ] 승인 후 다음 Step 진행

### 시작 명령
```bash
# 사용자가 "Step 1 시작" 또는 "go"라고 말하면 AI가 진행
```

### 완료 검증
- [x] `prompts/core_patterns_definition.md` 파일 존재
- [x] 7개 패턴 모두 정의됨 (genre/narrative/pacing/quality/brand/sensory/emotional)
- [x] 각 패턴에 학술 근거 1~2건 인용
- [x] 사용자 승인 신호 받음

### 중단 시 재개
이 Step은 사용자 검토에서 중단되기 쉬움.
재개 명령: **"Step 1 재개"** 또는 정의서 검토 결과 알려주기 (수정 / 승인)

---

## Step 2 — Pilot 자동 매칭

### 목표
7개 사전 정의 ↔ 391 Pilot canonical 패턴 임베딩 cosine 유사도 매칭 (자기참조 회피).

### 작업 흐름
1. [ ] `scripts/match_pilot_to_predefined.py` 작성
2. [ ] 스크립트 실행
3. [ ] `data/pilot_to_predefined_matching.csv` 산출
4. [ ] 결과 요약 콘솔 출력

### 자동 시작
Step 1 완료 후 자동 시작.

### 완료 검증
- [x] `data/pilot_to_predefined_matching.csv` 파일 존재
- [x] 7개 사전 정의 패턴 각각에 매칭된 Top-3 Pilot 패턴 + 유사도 기록
- [x] 콘솔에 매칭 강도 통계 출력

### 중단 시 재개
스크립트 재실행만 하면 처음부터 진행 (idempotent).
```bash
python scripts/match_pilot_to_predefined.py
```

---

## Step 3 — 자유 추출 한계 분석

### 목표
391개 Pilot 패턴을 4 카테고리로 자동 분류 (매체-종속 / 메타 / 매칭 / 표층).

### 작업 흐름
1. [ ] `scripts/categorize_pilot_patterns.py` 작성
2. [ ] 스크립트 실행
3. [ ] `data/pilot_pattern_categories.csv` 산출
4. [ ] 카테고리별 비율 통계 출력

### 자동 시작
Step 2 완료 후 자동 시작.

### 완료 검증
- [x] `data/pilot_pattern_categories.csv` 파일 존재
- [x] 391개 패턴 각각에 카테고리 부여
- [x] 카테고리 비율 출력 (예: 매체-종속 X%, 매칭 Y% ...)

### 중단 시 재개
```bash
python scripts/categorize_pilot_patterns.py
```

---

## Step 4 — 7개 직교성 검증

### 목표
7개 패턴 사이 cosine similarity ≤ 0.7 검증 + Movies-only 키워드 자동 검출.

### 작업 흐름
1. [ ] `scripts/check_pattern_orthogonality.py --top-n 7` 실행 (스크립트는 이미 작성됨)
2. [ ] `data/pilot_pattern_orthogonality.png` 생성
3. [ ] 결과 요약

### 자동 시작
Step 3 완료 후 자동 시작.

### 완료 검증
- [x] `data/pilot_pattern_orthogonality.png` 파일 존재
- [x] 7×7 cosine matrix CSV 저장
- [x] 모든 off-diagonal ≤ 0.7 또는 위반 항목 명시

### 중단 시 재개
```bash
python scripts/check_pattern_orthogonality.py --top-n 7
```

---

## Step 5 — 채택 결정표 + Pilot 보고서

### 목표
4단계 결과 통합 → 7개 채택 결정표 + Pilot Study Report 작성.

### 작업 흐름
1. [ ] `scripts/integrate_pilot_evaluation.py` 작성·실행
2. [ ] 결정표 생성 (학술/Pilot/Cross-Domain/직교성 4기준 ○△✗)
3. [ ] `docs/Pilot_Study_Report.md` 작성 (5~7페이지)

### 자동 시작
Step 4 완료 후 자동 시작.

### 완료 검증
- [x] `docs/Pilot_Study_Report.md` 파일 존재
- [x] 결정표 + 4단계 요약 + 결론 포함
- [x] 7개 채택 정당화 명시

### 중단 시 재개
```bash
python scripts/integrate_pilot_evaluation.py
```

---

## Phase 6 — 문서·코드 동기화 (옵션 A 완료 후)

### 동기화 대상 (6개 파일)

| 파일 | 변경 내용 |
|------|----------|
| `experiment_plan.md` §4 | 7개 채택 + Pilot 결과 반영 |
| `prompts/profiler_prompt.md` | 7번째 패턴 (emotional_resonance) 추가 |
| `scripts/run_profiler.py` | `REQUIRED_CORE_PATTERNS` 7개로 |
| `prompts/teacher_prompt.md` | Few-shot 예시에 emotional_resonance 반영 |
| `scripts/run_teacher.py` | `REQUIRED_CORE_PATTERNS` 통일 |
| `scripts/generate_pdf.py` | Overview PDF §6 7개 패턴 표 + Pilot 결과 |

### 자동 시작
Step 5 완료 후 사용자 승인 시.

### 완료 검증
- [x] 6개 파일 모두 7개 패턴으로 통일
- [x] PDF 재생성 완료
- [x] Cross-reference 검증 (grep) 통과

### 중단 시 재개
파일별로 독립적이라 어디서 끊겨도 재개 쉬움. 진행 진단 스크립트로 어느 파일이 미반영인지 확인.

---

## 중단 후 재개 가이드

### 1. 현재 진행도 확인
```bash
python scripts/check_pilot_progress.py
```

이 명령은 모든 산출물 파일 존재 여부를 자동 확인하여 다음을 출력:
- ✅ 완료된 Step
- 🟡 진행 중인 Step
- ⬜ 대기 중인 Step
- 다음 실행할 명령 추천

### 2. 특정 Step부터 재개

| 재개 시작점 | 명령 |
|------------|------|
| Step 1부터 | "Step 1 다시" 또는 정의서 수정 요청 |
| Step 2부터 | `python scripts/match_pilot_to_predefined.py` |
| Step 3부터 | `python scripts/categorize_pilot_patterns.py` |
| Step 4부터 | `python scripts/check_pattern_orthogonality.py --top-n 7` |
| Step 5부터 | `python scripts/integrate_pilot_evaluation.py` |
| Phase 6부터 | "Phase 6 진행" |

### 3. 모든 결과 초기화 (처음부터)
```bash
# 옵션 A 산출물 삭제 (주의!)
rm -f prompts/core_patterns_definition.md
rm -f data/pilot_to_predefined_matching.csv
rm -f data/pilot_pattern_categories.csv
rm -f data/pilot_pattern_orthogonality.png
rm -f data/pilot_pattern_orthogonality.csv
rm -f docs/Pilot_Study_Report.md
```

---

## 진행 메모 (실시간 업데이트)

> 작업 진행 시 본 섹션에 기록

- **Step 1 시작**: ____  
  완료: ____  
  사용자 승인: ____
- **Step 2 시작**: ____  완료: ____
- **Step 3 시작**: ____  완료: ____
- **Step 4 시작**: ____  완료: ____
- **Step 5 시작**: ____  완료: ____
- **Phase 6 시작**: ____  완료: ____
- **전체 완료**: ____

---

## FAQ

### Q. 한 번에 다 해도 되나요?
A. Step 1만 사용자 검토 필요. 나머지 Step 2~5와 Phase 6는 한 번에 자동 진행 가능.

### Q. Step 1 검토 시 무엇을 봐야 하나요?
A. 7개 패턴 각각의:
- 학술 인용이 적절한가
- Movies/Books 예시가 합리적인가
- Cross-Domain 가능성 평가가 합리적인가

### Q. emotional_resonance를 빼고 6개로 가고 싶으면?
A. Step 1 시점에 알려주시면 됩니다. 정의서에서 emotional_resonance 제거하고 6개로 진행 가능.

### Q. Step 2~5 결과가 마음에 안 들면?
A. 각 Step은 idempotent이므로 스크립트 재실행 가능. 또는 그 시점에 옵션 변경 가능.

### Q. 작업 중에 OneDrive 동기화 충돌이 나면?
A. 이 폴더는 OneDrive 동기화 폴더. 동시 편집 충돌 가능성 있음. 시작 전 OneDrive 동기화 일시정지 권장.
