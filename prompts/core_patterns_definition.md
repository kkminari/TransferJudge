# TransferJudge Core Patterns — 정의서

> **목적**: Profiler가 추출하는 7개 Core Pattern의 정의·근거·예시 정리
> **선정 절차**: 4가지 측면(이론·Pilot·CDR·직교) 종합 검토
> **이론 anchor**: Thet et al. (2010) 영화 리뷰 aspect mining + Liu (2012) ABSA
> **검증 도구**: Pilot Study (n=100) 임베딩 자동 매칭

---

## 0. 7개 패턴 한눈에 — 선정 결과표

| # | Pattern | 이론 | Pilot | CDR | 직교 | Transfer Gate |
|:---:|---------|:---:|:---:|:---:|:---:|:---:|
| 1 | `genre_preference` | ○ | △ 0.70 | ○ | ○ 0.47 | TRANSFER |
| 2 | `narrative_complexity` | ○ | ○ 0.80 | ○ | △ 0.67 | TRANSFER |
| 3 | `pacing_preference` | ○ | ○ 0.81 | ○ | △ 0.67 | TRANSFER |
| 4 | `quality_sensitivity` | ○ | △ 0.55 | △ | ○ 0.37 | PARTIAL |
| 5 | `brand_loyalty` | △ | △ 0.70 | ✗ | ○ 0.33 | BLOCK |
| 6 | `sensory_preference` | △ | △ 0.59 | △ | ○ 0.47 | BLOCK |
| 7 | `emotional_resonance` ★ | △ | ○ 0.82 | ○ | ○ 0.38 | TRANSFER |

★ = Pilot Study에서 emerge한 패턴

**검토 4가지 측면**:
- **이론 정합성**: aspect mining 선행연구의 일반 attribute 개념과 부합 여부
- **Pilot 발현**: Pilot 자유 추출과의 max cosine similarity
- **Cross-Domain 적합성**: Movies-only 키워드 자동 검출 결과
- **직교성**: 다른 패턴과의 max similarity (≤ 0.7)

---

## 1. genre_preference (선호 장르)

### 영문 정의
> The user's preference for specific content genres or categories (e.g., sci-fi, thriller, romance, biography). Includes both preferred genres (positive polarity) and disliked genres (negative polarity).

### 국문 설명
사용자가 선호하거나 회피하는 장르·카테고리. 좋아하는 것뿐 아니라 싫어하는 장르(negative)도 포함.

### Pilot 발현
- Top-1 매칭: `genre_diversity` (sim 0.699)
- 발현 강도: MEDIUM

### Cross-Domain 라벨: TRANSFER
- Movies-only 키워드 0개
- 장르명 직접 매핑 가능 (sci-fi → sci-fi)

### Movies / Books 예시
- Movies: *"Another brilliant Nolan sci-fi epic"* → `genre_preference: sci-fi (positive)`
- Books: 카테고리 필드 `["Books", "Mystery, Thriller & Suspense"]` 기반 매핑

---

## 2. narrative_complexity (서사 복잡도)

### 영문 정의
> The user's preference for complex versus simple narrative structures, including multi-layered plots, non-linear timelines, unreliable narrators, and depth of character development.

### 국문 설명
사용자가 복잡한 서사(다중 시간선, 비선형 플롯, 다층 캐릭터)를 선호하는지, 단순·선형 서사를 선호하는지의 정도.

### Pilot 발현
- Top-1 매칭: `narrative_complexity` (sim 0.803, 동일 이름)
- 발현 강도: STRONG (직접)

### Cross-Domain 라벨: TRANSFER
- Movies-only 키워드 0개, medium-agnostic
- 서사 복잡도는 책에 직접 적용

### Movies / Books 예시
- Movies: *"The time-loop structure was genius"* → `narrative_complexity: complex (positive)`
- Books: "Cloud Atlas" (David Mitchell) — 6개 중첩 시간선 → `complex`
- Books: "Where the Crawdads Sing" — 단선적 narrative → `simple`

---

## 3. pacing_preference (전개 속도)

### 영문 정의
> The user's preference for narrative pacing — fast-paced action and tension versus slow-burn, character-driven, contemplative storytelling.

### 국문 설명
사용자가 빠른 전개(액션·긴장감 위주)를 선호하는지, 느린 전개(인물 중심·여운 위주)를 선호하는지.

### Pilot 발현
- Top-1 매칭: `tolerance_for_slow_pacing` (sim 0.807)
- 발현 강도: STRONG

### Cross-Domain 라벨: TRANSFER
- page-turner ↔ slow-burn 매핑 자연
- 영화의 "action vs contemplative"가 책의 "thriller vs literary"와 직접 대응

### Movies / Books 예시
- Movies: *"Slow-burn but rewarding character study"* → `pacing_preference: slow (positive)`
- Books: "Lee Child Reacher series" — fast-paced → `fast`
- Books: "Donna Tartt The Goldfinch" — slow-burn → `slow`

---

## 4. quality_sensitivity (품질 민감도)

### 영문 정의
> The user's sensitivity to production quality, technical execution, and overall craft. Includes attention to ratings, professional reviews, and indicators of quality.

### 국문 설명
사용자가 제작 품질·기술적 완성도·전반적 장인정신에 얼마나 민감한지. 평점·평가에 영향받는 정도.

### Pilot 발현
- Top-1 매칭: `variable_rating_on_quality` (sim 0.552)
- 발현 강도: MEDIUM

### Cross-Domain 라벨: PARTIAL
- "acting" 키워드 1개 검출 (영화 한정 지표)
- 품질 민감도 자체는 도메인 독립적이나, 품질 지표가 매체별로 다름

### Movies / Books 예시
- Movies: *"Cinematography alone makes this a masterpiece"* → `quality_sensitivity: high (positive)`
- Books: "Pulitzer winner의 정교한 문체" 선호 → `high`
- Books: average_rating·출판 권위 기반 매핑

---

## 5. brand_loyalty (창작자·브랜드 충성도)

### 영문 정의
> The user's loyalty to specific creators (directors, actors, authors), franchises, series, or production brands. Includes both positive (favorite creators) and negative (avoided creators).

### 국문 설명
특정 감독·배우·작가·프랜차이즈에 대한 충성도. "Nolan 감독 팬", "Stephen King 작가의 모든 책 구매" 등.

### Pilot 발현
- Top-1 매칭: `franchise_loyalty` (sim 0.696)
- 발현 강도: MEDIUM

### Cross-Domain 라벨: BLOCK 후보
- "actor", "director" 키워드 2개 검출 (영화 한정)
- 동일 인물(Stephen King 등)은 TRANSFER, 영화감독은 BLOCK 빈도 높음
- **본 연구의 BLOCK 시연 후보**

### Movies / Books 예시
- Movies: *"Nolan never disappoints"* → `brand_loyalty: Christopher Nolan (positive)`
- Books: "Stephen King의 모든 작품 구매" → `brand_loyalty: Stephen King (author)`
- Movies: *"Avoid anything with Adam Sandler"* → `brand_loyalty: Adam Sandler (negative)`

---

## 6. sensory_preference (감각적 경험)

### 영문 정의
> The user's preference for sensory experiences in media — visual spectacle, auditory immersion, action choreography, atmospheric mood, and other medium-specific experiential qualities.

### 국문 설명
영상미·음향·액션 안무·분위기 등 감각적 경험을 중시하는 정도. 영화 매체에 특화된 패턴.

### Pilot 발현
- Top-1 매칭: `enjoyment_of_action_movies` (sim 0.591)
- 발현 강도: MEDIUM

### Cross-Domain 라벨: BLOCK 후보
- "cinematograph" 키워드 1개 검출
- 영화 매체 한정 (대부분 BLOCK)
- 드물게 "묘사 풍부한 책"으로 PARTIAL 변환 가능
- **본 연구의 핵심 BLOCK 후보**: Transfer Gate가 차단하여 Negative Transfer 방지

### Movies / Books 예시
- Movies: *"The IMAX visuals were breathtaking"* → `sensory_preference: visual (positive)`
- Movies: *"Hans Zimmer score elevated every scene"* → `sensory_preference: auditory (positive)`
- Books: 약한 매핑 — "묘사가 풍부한 책 (descriptive prose)"

---

## 7. emotional_resonance (감정적 울림) ★ Pilot 도출

### 영문 정의
> The user's emphasis on emotional impact and resonance — whether the content evokes deep feelings, lasting memory, and personal meaning beyond mere entertainment.

### 국문 설명
콘텐츠가 사용자에게 깊은 감정·여운·개인적 의미를 남기는지를 중시하는 정도. 단순 오락을 넘어 정서적 울림 추구.

### Pilot 발현
- Top-1 매칭: `emotional_resonance` (sim 0.816, 동일 이름, 14% 빈도)
- 발현 강도: STRONG (직접)

### Cross-Domain 라벨: TRANSFER
- Movies-only 키워드 0개, medium-agnostic
- 영화·책 모두에 동일 적용

### Movies / Books 예시
- Movies: *"Brought tears to my eyes"*, *"Stayed with me for days"* → `emotional_resonance: high (positive)`
- Books: "A Little Life" (Hanya Yanagihara) — emotionally devastating
- Books: "Where the Crawdads Sing" — emotional impact 강조

### 본 패턴의 특수 위치
- 사전 후보 6개에는 미포함이었으나, Pilot Study에서 강하게 emerge
- 14% 빈도, 동일 이름 sim 0.82 → 데이터 기반으로 추가 채택
- 이론 anchor가 약하나(△) Pilot 발현이 강함(○)

---

## 8. 패턴 간 직교성 (검증 결과)

### 7×7 직교성 matrix 요약
- **Off-diagonal max**: 0.669 (narrative_complexity ↔ pacing_preference)
- **Off-diagonal mean**: 0.310
- **Threshold (0.7) 위반**: 0건 ✅

### 가까운 쌍 (모두 안전 범위)
| Pair | sim | 평가 |
|---|:---:|---|
| narrative_complexity ↔ pacing_preference | 0.67 | △ 경계 (둘 다 narrative 차원) |
| genre_preference ↔ sensory_preference | 0.47 | ○ 안전 |
| sensory_preference ↔ pacing_preference | 0.40 | ○ 안전 |

→ 가장 가까운 쌍(narrative ↔ pacing)도 임계값 미만으로 통과.

---

## 9. Cross-Domain 적용 가이드 (Transfer Gate 라벨)

### TRANSFER 후보 (도메인 독립, 4개)
1. `narrative_complexity` — 책에도 복잡한 서사 존재
2. `pacing_preference` — page-turner vs slow-burn 직접 매핑
3. `emotional_resonance` — 매체 무관
4. `genre_preference` — 카테고리 직접 매핑

### PARTIAL 후보 (도메인 변환 필요, 1개)
1. `quality_sensitivity` — 매체별 품질 지표 다름

### BLOCK 후보 (Negative Transfer 위험, 2개)
1. `sensory_preference` — 영화 매체 한정 (가장 강한 BLOCK)
2. `brand_loyalty` (non-author 케이스) — 영화감독·배우는 책에 부재

→ Transfer Gate 3-level 판정의 모든 케이스를 데이터에 적용 가능한 구성

---

## 10. Pilot Study 사전 검토 항목

본 검토 항목들은 Pilot Study 결과 보기 전에 정해두었고, 결과로 모두 확인됨.

| ID | 검토 항목 | 결과 | 통과 |
|:---:|---|---|:---:|
| 1 | 후보 7개가 Pilot에서 sim ≥ 0.5로 발현 | 7/7 | ✅ |
| 2 | Pilot 자유 추출의 ≥60%가 비-CDR-적합 | 90.8% | ✅ |
| 3 | 7개 직교성 max ≤ 0.7 | 0.669 | ✅ |
| 4 | 매체 한정 패턴이 Movies-only 키워드 자동 검출 | sensory cinematograph 검출 | ✅ |
| 5 | Pilot에서 emerge한 패턴 직접 매칭 | sim 0.820 | ✅ |

---

## 11. 본 정의서의 학술적 위치

### 이론 anchor (인용 압축)
| 인용 | 역할 |
|---|---|
| **Thet, T. T., Na, J. C., & Khoo, C. S. G. (2010)** | 영화 리뷰 aspect mining 선행연구 — 후보 패턴 도출 anchor |
| **Liu, B. (2012)** | Aspect-Based Sentiment Analysis 일반 프레임워크 |

→ 패턴별 인용 6개 → 메인 anchor 2개로 압축

### 자기참조 회피
- **이론 anchor**: 본 연구가 정의하지 않고 aspect mining 선행연구에서 도출
- **검증 도구**: 본 연구가 매칭하지 않고 임베딩 cosine 자동 매칭
- **사전 검토**: 5가지 항목을 결과 보기 전에 정해둠
- **다중 측면**: 단일 빈도가 아닌 4가지 측면 종합

### 본 연구의 contribution
- **메인**: Profiler-Judge 구조의 LLM 기반 CDR 프레임워크
- **서브**: Pilot 기반 패턴 선정 절차 + 자기참조 회피

7개 패턴은 본 도메인(Movies&TV → Books)에 적용한 결과물.

---

## 12. 패턴 선정 절차 (5단계)

본 연구가 7개 패턴을 선정한 절차:

**Step 1 — 이론 anchor 검토**: aspect mining 선행연구(Thet 2010 등)의 일반 attribute 개념을 검토하여 후보 패턴 풀 6개 도출.

**Step 2 — Pilot Study (n=100)**: 자유 추출 prompt로 LLM이 사용자 리뷰에서 패턴 추출 → 806개 raw 패턴의 **"이름 + 설명" 결합 텍스트**를 `sentence-transformers all-MiniLM-L6-v2`로 384차원 임베딩 → HDBSCAN 클러스터링 (`min_cluster_size=3`, `min_samples=1`, `cluster_selection_epsilon=0.15`, cosine 거리) → 각 군집에서 빈도(n_users) 최고 멤버를 canonical로 자동 선정 → **391 canonical 도출** → 후보 6개 정의 텍스트와 임베딩 자동 매칭. 이름만이 아니라 설명까지 임베딩하여 같은 이름·다른 의미의 패턴이 정확히 분리되도록 설계.

**Step 3 — 자유 추출 한계 분석**: 391 canonical을 4 카테고리(cdr_relevant / surface / medium_specific / meta)로 분류하여 자유 추출의 매체 편향 정량화.

**Step 4 — 직교성 + Movies-only 검증**: 후보 패턴 정의 텍스트의 N×N similarity matrix 검사 (≤ 0.7) + Movies-only 키워드 자동 검출로 BLOCK 후보 식별.

**Step 5 — 4가지 측면 종합**: 이론·Pilot·CDR·직교 측면 각각을 ○/△/✗로 평가하여 패턴 채택. Pilot에서 강하게 emerge한 emotional_resonance를 추가하여 7개 확정.

---

## 부록 — 검토 가이드

### 정의서 검토 시 확인할 점
1. 각 패턴 정의가 1~2 문장으로 명확한가
2. 4가지 측면 평가(○/△/✗)가 합리적인가
3. Movies/Books 예시가 합리적인가
4. Cross-Domain 라벨(TRANSFER/PARTIAL/BLOCK)이 합리적인가
5. emotional_resonance를 7번째로 채택할 것인가

### 승인 후 진행
- Profiler 프롬프트 7개 패턴 정의 동기화
- Teacher Distillation Few-shot 예시 정합성 확인
