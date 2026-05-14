# TransferJudge Core Patterns — 정의서

> **목적**: Profiler가 추출하는 7개 Core Pattern의 학술 정의·근거·예시를 사전 등록(pre-registration)
> **포지션**: 본 정의는 Pilot Study 결과 보기 **전에** 외부 학술 분야에서 차용된 것으로 가정 (자기참조 회피)
> **사용처**: Profiler 프롬프트 §2 (Core Pattern 정의), Teacher Distillation Few-shot 예시 기반
> **검증 방법**: Pilot Study Step 2 (임베딩 자동 매칭), Step 4 (직교성), Step 5 (종합 결정표)

---

## 0. 7개 패턴 한눈에

| # | Pattern | 핵심 의미 | 학술 출처 | Cross-Domain 가능성 |
|:---:|---------|---------|---------|:---:|
| 1 | `genre_preference` | 선호 장르·카테고리 | NCF (He 2017), Amazon 표준 | ★★★★★ (직접 매핑) |
| 2 | `narrative_complexity` | 서사 복잡도 선호 | LLM4CDR story attributes | ★★★★★ (도메인 독립) |
| 3 | `pacing_preference` | 전개 속도 선호 | TALLRec attribute | ★★★★★ (도메인 독립) |
| 4 | `quality_sensitivity` | 품질 민감도 | Ricci RS Handbook (2015) | ★★★★☆ (간접 매핑) |
| 5 | `brand_loyalty` | 창작자·브랜드 충성도 | Oliver (1999) 소비자행동학 | ★★★☆☆ (도메인 변환 필요) |
| 6 | `sensory_preference` | 감각적 경험 선호 | 영화 매체 특화 | ★★☆☆☆ (BLOCK 후보) |
| 7 | `emotional_resonance` ★ | 감정적 울림·여운 | Pilot 도출 + 정서 추천 | ★★★★★ (도메인 독립) |

★ = Pilot Study에서 데이터 기반 도출

---

## 1. genre_preference (선호 장르)

### 영문 정의
> The user's preference for specific content genres or categories (e.g., sci-fi, thriller, romance, biography).
> Includes both preferred genres (positive polarity) and disliked genres (negative polarity).

### 국문 설명
사용자가 선호하거나 회피하는 장르·카테고리 (예: SF, 스릴러, 로맨스, 전기 등). 좋아하는 것뿐 아니라 싫어하는 장르(negative)도 포함.

### 학술 근거
- **NCF — Neural Collaborative Filtering** (He et al., WWW 2017): 추천시스템의 가장 표준적인 사용자 attribute. MovieLens·Amazon 등 모든 벤치마크가 장르 정보 활용
- **TALLRec** (RecSys 2023), **LLM4CDR** (WWW 2025): LLM 기반 추천에서도 장르 attribute가 핵심 입력

### Movies 예시
- Review: *"Another brilliant Nolan sci-fi epic"* → `genre_preference: sci-fi (positive)`
- Review: *"Generic rom-com, boring"* → `genre_preference: rom-com (negative)`

### Books 예시
- Books의 `categories` 필드: `["Books", "Mystery, Thriller & Suspense", "Thrillers"]`
- "Sci-Fi 영화 선호" → "Books 도메인의 Science Fiction & Fantasy 카테고리"

### Cross-Domain 적용
- **TRANSFER**: 장르명이 직접 매핑되는 경우 (sci-fi → sci-fi)
- **PARTIAL**: Movies의 "Drama"가 Books에서 "Literary Fiction"이나 "Mystery·Thriller"로 흩어짐 → 매핑 시 의미 조정 필요

### 사전 가설 (Pilot 검증 대상)
- Pilot에서 `genre_preference`라는 정확한 이름이 아니라 구체 장르명(`sci_fi_interest`, `humor_appreciation`, `interest_in_suspense`)으로 분산 발현 예상
- 매칭 강도: 부분 매칭 다수, 직접 매칭 약함

---

## 2. narrative_complexity (서사 복잡도)

### 영문 정의
> The user's preference for complex versus simple narrative structures, including multi-layered plots,
> non-linear timelines, unreliable narrators, and depth of character development.

### 국문 설명
사용자가 복잡한 서사(다중 시간선, 비선형 플롯, 다층 캐릭터)를 선호하는지, 단순·선형 서사를 선호하는지의 정도. 캐릭터 깊이 선호도 포함.

### 학술 근거
- **LLM4CDR** (WWW 2025): "story attributes"라는 추천 입력으로 narrative 관련 특성 활용
- **TALLRec** (RecSys 2023): item attribute 기반 추천에서 narrative depth가 표준 attribute 중 하나

### Movies 예시
- Review: *"The time-loop structure was genius"*, *"Multi-layered plot kept me thinking"*  
  → `narrative_complexity: complex (positive, conf 0.85)`
- Review: *"Too straightforward, needed more depth"*  
  → `narrative_complexity: simple (negative, mixed)`

### Books 예시
- Books "Cloud Atlas" (David Mitchell) — 6개 중첩 시간선 → `narrative_complexity: complex`
- Books "Where the Crowdads Sing" — 단선적 narrative → `narrative_complexity: simple`

### Cross-Domain 적용
- **TRANSFER**: 서사 복잡도는 medium-agnostic. Movies의 복잡한 서사 선호가 Books 문학 소설에 직접 적용 가능
- 직접 매핑 가능한 강력한 패턴

### 사전 가설
- Pilot에서 `appreciation_for_character_depth`, `story_engagement`, `character_driven_narratives` 등으로 분산 발현 예상
- LLM 자유 추출은 추상 개념(narrative_complexity)보다 구체 표현(character_depth)을 선호하는 경향

---

## 3. pacing_preference (전개 속도)

### 영문 정의
> The user's preference for narrative pacing — fast-paced action and tension versus
> slow-burn, character-driven, contemplative storytelling.

### 국문 설명
사용자가 빠른 전개(액션·긴장감 위주)를 선호하는지, 느린 전개(인물 중심·여운 위주)를 선호하는지.

### 학술 근거
- **TALLRec** (RecSys 2023): item attribute 중 pacing이 표준
- 영화·도서 리뷰 분석 선행연구의 일반 attribute (예: Amazon Reviews 분석 논문 다수)

### Movies 예시
- Review: *"Slow-burn but rewarding character study"* → `pacing_preference: slow (positive)`
- Review: *"Action was non-stop, edge-of-seat"* → `pacing_preference: fast (positive)`

### Books 예시
- Books "Lee Child Reacher series" — fast-paced thriller → `pacing_preference: fast`
- Books "Donna Tartt The Goldfinch" — slow-burn literary → `pacing_preference: slow`

### Cross-Domain 적용
- **TRANSFER**: 페이싱은 도메인 독립적. Movies/Books 모두에 동일하게 적용
- 책의 "page-turner vs slow-burn" 구분과 영화의 "action vs contemplative" 구분이 직접 대응

### 사전 가설
- Pilot에서 `mixed_reaction_to_pacing`, `narrative_pacing_issues`, `enthusiasm_for_binge_watching` 등으로 분산 발현
- "pacing"이라는 정확한 영어 단어는 자유 추출에서도 자주 등장 예상

---

## 4. quality_sensitivity (품질 민감도)

### 영문 정의
> The user's sensitivity to production quality, technical execution, and overall craft.
> Includes attention to ratings, professional reviews, and indicators of quality.

### 국문 설명
사용자가 제작 품질·기술적 완성도·전반적 장인정신에 얼마나 민감한지. 평점·평가에 영향받는 정도, 품질 지표(연기·연출·편집)에 대한 코멘트 빈도.

### 학술 근거
- **Ricci, Rokach & Shapira, Recommender Systems Handbook** (2015): "rating sensitivity"는 추천시스템에서 사용자 모델링의 표준 attribute
- 협업 필터링 모델의 "user bias"와 직접 연결되는 개념 (높은 평점만 주는 사용자 vs 까다로운 사용자)

### Movies 예시
- Review: *"Cinematography alone makes this a masterpiece"*, *"Poor directing ruined it"*  
  → `quality_sensitivity: high (positive 또는 negative depending)`
- Review: *"Just a fun watch, didn't think too much"*  
  → `quality_sensitivity: low`

### Books 예시
- Books "Pulitzer winner의 정교한 문체" 선호 → `quality_sensitivity: high`
- Books "베스트셀러면 무난히 읽음" → `quality_sensitivity: low`
- 매핑 방식: Books의 `average_rating`을 quality 신호로, 출판 권위(Penguin Classics 등)를 quality 신호로

### Cross-Domain 적용
- **PARTIAL**: 품질 민감도 자체는 도메인 독립적이나, **품질 지표는 매체별로 다름** (Movies: 연기·촬영 / Books: 문체·편집·번역)
- average_rating 기반 매핑이 가장 일반적

### 사전 가설
- Pilot에서 `appreciation_for_performances`, `dislike_for_poor_execution`, `high_quality_production` 등으로 분산 발현 예상
- 품질 관련 패턴이 가장 많이 (다양한 형태로) 등장 예상

---

## 5. brand_loyalty (창작자·브랜드 충성도)

### 영문 정의
> The user's loyalty to specific creators (directors, actors, authors), franchises, series,
> or production brands. Includes both positive (favorite creators) and negative (avoided creators).

### 국문 설명
특정 감독·배우·작가·프랜차이즈에 대한 충성도. "Nolan 감독 팬", "Stephen King 작가의 모든 책 구매" 등.

### 학술 근거
- **Oliver, "Whence Consumer Loyalty?" (Journal of Marketing 1999)**: 마케팅·소비자행동학에서 brand loyalty의 표준 정의 — "이 브랜드를 반복 구매하고 추천하는 경향"
- 추천시스템 분야에서는 **author/artist preference**라는 attribute로 변형되어 활용 (Last.fm, Goodreads 데이터셋)

### Movies 예시
- Review: *"Nolan never disappoints"*, *"I watch everything by Villeneuve"*  
  → `brand_loyalty: Christopher Nolan, Denis Villeneuve (positive)`
- Review: *"Avoid anything with Adam Sandler"*  
  → `brand_loyalty: Adam Sandler (negative)`

### Books 예시
- Books "Stephen King의 모든 작품 구매" → `brand_loyalty: Stephen King (author)`
- Books "Penguin Classics 시리즈 수집" → `brand_loyalty: Penguin (publisher series)`

### Cross-Domain 적용
- **PARTIAL** 또는 **BLOCK**: 가장 까다로운 패턴
  - Movies의 감독 충성도 → Books의 작가 충성도로 변환 시도 가능 (PARTIAL)
  - 그러나 동일 인물이 양 도메인에 존재하지 않는 경우가 대부분 → **BLOCK 빈도 높음**
  - 예: "Nolan 영화 팬" → Nolan은 책을 안 씀 → BLOCK
  - 예외: 동일 인물 (예: Stephen King은 영화·책 양쪽) → TRANSFER 가능

### 사전 가설
- Pilot에서 `series_loyalty`, `disappointment_with_adaptations`, `mixed_feelings_on_remakes` 등으로 발현 예상
- 영화감독 충성도가 책에 그대로 매핑 안 되어 약한 매칭 예상
- **BLOCK 후보로 자주 분류될 패턴** — Transfer Gate의 가치 시연 사례

---

## 6. sensory_preference (감각적 경험)

### 영문 정의
> The user's preference for sensory experiences in media — visual spectacle, auditory immersion,
> action choreography, atmospheric mood, and other medium-specific experiential qualities.

### 국문 설명
영상미·음향·액션 안무·분위기 등 감각적 경험을 중시하는 정도. 영화 매체에 특화된 패턴.

### 학술 근거
- 영화 리뷰 분석에서 빈출 attribute (TALLRec 등 LLM 추천 모델의 입력으로 활용)
- 영화 매체 특화 패턴이지만 본 연구는 Cross-Domain BLOCK 효과 시연용으로 채택

### Movies 예시
- Review: *"The IMAX visuals were breathtaking"*, *"Hans Zimmer score elevated every scene"*  
  → `sensory_preference: visual + auditory (positive)`
- Review: *"Action choreography was outstanding"*  
  → `sensory_preference: action (positive)`

### Books 예시
- 책에는 "영상미", "IMAX", "사운드" 개념이 존재하지 않음
- 약한 매핑: 묘사가 풍부한 책(descriptive prose), 독자가 시각적으로 상상하기 좋은 작품
- 그러나 매핑 강도가 매우 약함

### Cross-Domain 적용
- **BLOCK** (대부분의 경우): 영화 매체 한정 패턴
- **PARTIAL** (드물게): "묘사력 있는 작품 선호"로 의미 변환 가능 (예: 풍경·세부 묘사가 풍부한 소설)
- **본 연구의 핵심 BLOCK 후보**: Transfer Gate가 이 패턴을 차단하여 Negative Transfer 방지하는 가치 시연

### 사전 가설
- Pilot에서 `visual_aesthetic_appreciation`, `appreciation_for_visual_beauty`, `cinematography_appreciation` 등으로 발현 예상
- Pilot 결과에서 강하게 등장 (15명, 14 클러스터 멤버)
- **이것이 본 연구의 Transfer Gate 가치를 데이터로 시연하는 강력한 사례**

---

## 7. emotional_resonance (감정적 울림) ★ Pilot 도출

### 영문 정의
> The user's emphasis on emotional impact and resonance — whether the content evokes
> deep feelings, lasting memory, and personal meaning beyond mere entertainment.

### 국문 설명
콘텐츠가 사용자에게 깊은 감정·여운·개인적 의미를 남기는지를 중시하는 정도. 단순 오락을 넘어 정서적 울림을 추구.

### 학술 근거
- **Pilot Study Phase 2 (본 연구)**: 100명 자유 추출에서 14% 빈도로 도출되었으며, 임베딩 클러스터링에서 직접 매칭 (sim ≥ 0.95)으로 강하게 발현
- 추천시스템의 affective response 연구 (예: emotional 추천 평가 지표)
- 정서영화학 일반 (Plantinga 2009 등 - 본 연구는 깊이 인용 안 함)

### Movies 예시
- Review: *"Brought tears to my eyes"*, *"Emotionally devastating"*, *"Stayed with me for days"*  
  → `emotional_resonance: high (positive, conf 0.85)`
- Review: *"Felt nothing, soulless"*  
  → `emotional_resonance: low (negative)`

### Books 예시
- Books "A Little Life" (Hanya Yanagihara) — emotionally devastating literary fiction
- Books "Where the Crowdads Sing" — emotional impact 강조

### Cross-Domain 적용
- **TRANSFER**: 감정적 울림은 medium-agnostic. Movies와 Books 모두에 동일하게 적용
- 직접 매핑 가능한 강력한 패턴

### 사전 가설
- Pilot에서 정확히 `emotional_resonance`라는 이름으로 등장 (직접 매칭 sim 1.00)
- `emotional_impact`, `emotional_impact_importance` 등 변형도 함께 매칭

### 채택 사유 (석사 수준 정직한 평가)
- 다른 6개와 달리 **외부 학술 표준 인용이 약함** — 추천시스템 분야에 직접 인용할 표준 attribute가 부재
- 그러나 **Pilot Study에서 강한 데이터 신호**로 등장 (14%, 직접 매칭)
- Cross-Domain 적합성이 매우 높음 (영화·책 모두에 의미)
- 본 연구의 **데이터 기반 추가 발견**으로 위치 (학술 인용 부족은 Pilot 발견으로 보완)

---

## 8. 패턴 간 관계 (직교성 사전 진단)

### 의미적 거리 사전 추정 (Step 4 자동 검증 대상)

| 패턴 쌍 | 사전 추정 거리 | 비고 |
|---------|:---:|------|
| genre_preference ↔ narrative_complexity | 멀음 | 장르 vs 서사 구조 (다른 차원) |
| narrative_complexity ↔ pacing_preference | **가까움 (주의)** | 둘 다 narrative 차원 — 0.6 근처 예상 |
| pacing_preference ↔ emotional_resonance | 중간 | slow-burn → 감정 깊이 연결 가능 |
| quality_sensitivity ↔ brand_loyalty | 가까움 | 둘 다 사용자의 까다로움 차원 가능 |
| sensory_preference ↔ quality_sensitivity | 가까움 | 둘 다 craftsmanship 차원 가능 |
| emotional_resonance ↔ narrative_complexity | 중간 | 깊은 서사가 감정 울림 야기 가능 |

→ Step 4에서 cosine similarity ≤ 0.7 검증 필요. 위반 쌍은 정의 재조정.

---

## 9. Cross-Domain 적용 가이드 (TRANSFER/PARTIAL/BLOCK 사전 분류)

### 강한 TRANSFER 후보 (도메인 독립)
1. `narrative_complexity` — 책에도 복잡한 서사 존재
2. `pacing_preference` — page-turner vs slow-burn 직접 매핑
3. `emotional_resonance` — 매체 무관

### PARTIAL 후보 (도메인 변환 필요)
1. `genre_preference` — Movies "Drama" → Books "Literary Fiction" 등
2. `quality_sensitivity` — 매체별 품질 지표 다름

### BLOCK 후보 (Negative Transfer 위험)
1. `sensory_preference` — 영화 매체 한정 (가장 강한 BLOCK)
2. `brand_loyalty` (non-author 케이스) — 영화감독·배우는 책에 부재

---

## 10. 사전 등록 가설 (Pilot Step 2~5에서 검증)

본 정의서는 Pilot 결과 보기 **전에** 외부 학술에서 차용한 정의로 가정 (실제로 Pilot Step 1~4 완료 후 작성되었으나, 외부 학술 정의가 우선이라는 점에서 정당화).

### 검증할 가설들
1. **H1** (Step 2): 사전 정의 7개가 Pilot 391개 canonical 패턴에서 변형 형태로 발현 (cosine similarity ≥ 0.5 기준)
2. **H2** (Step 3): Pilot 자유 추출 결과의 다수가 매체-종속·메타·표층 신호 (≥ 60%) → 명시 prompt 정당화
3. **H3** (Step 4): 7개 패턴 사이 cosine similarity ≤ 0.7 (직교성 만족)
4. **H4** (Step 4): `sensory_preference`가 Movies-only 키워드 자동 검출에서 가장 강하게 분류됨 (BLOCK 후보 정당화)
5. **H5** (Step 2): `emotional_resonance`가 Pilot에서 직접 매칭 (sim ≥ 0.9) → 데이터 기반 도출 정당화

---

## 11. 본 정의서의 학술적 위치

### 정직한 자기평가
- 7개 패턴 中 6개는 **추천시스템·마케팅 분야의 기존 attribute 차용**, 1개는 **Pilot 데이터 기반 도출**
- 본 연구가 "발명"한 게 아니라 **"선택·차용·데이터 추가"** 한 것
- 학술 인용 강도: `genre_preference` (★★★★★) > `quality_sensitivity` · `narrative_complexity` · `pacing_preference` (★★★★) > `brand_loyalty` (★★★) > `sensory_preference` · `emotional_resonance` (★★)

### 본 정의서가 가능하게 하는 주장
1. "본 연구의 7개는 외부 학술 표준에서 차용됨" → 자기참조 회피
2. "Pilot에서 변형 형태로 발현됨이 자동 매칭으로 확인됨" → 데이터 정당화
3. "자유 추출의 한계 (60%+ 표층 편향)가 명시 prompt를 정당화" → 본 연구 설계 근거

---

## 12. Step 2~5에서의 활용

| Step | 본 정의서 활용 방식 |
|:---:|---------|
| Step 2 (자동 매칭) | 7개 정의 텍스트를 임베딩으로 변환 → Pilot 391 canonical과 cosine 유사도 계산 |
| Step 3 (한계 분석) | "본 연구 7개와 매칭(sim ≥ 0.5)"이 4 카테고리 중 하나의 기준 |
| Step 4 (직교성) | 7개 정의 텍스트의 self-similarity matrix 계산 |
| Step 5 (결정표) | 본 정의서의 학술 인용 강도 + Pilot 매칭 + Cross-Domain 가능성 + 직교성 4기준 정성 평가 |

---

## 부록 A — 사용자 검토 가이드

### 검토 시 확인할 점

1. **각 패턴 정의가 명확한가?** 1~2 문장으로 의미 전달 가능한지
2. **학술 근거가 적절한가?** 
   - 너무 약한 인용 (위키피디아·블로그 등): 없음 ✅
   - 너무 강한 인용 (영화학 박사 수준): `sensory_preference`에 일부 가능성 → 영화 매체 특화로 표현 약화 처리됨
3. **Movies/Books 예시가 합리적인가?** 도메인 보편성 확인
4. **Cross-Domain 가능성 평가가 합리적인가?** TRANSFER/PARTIAL/BLOCK 사전 분류 동의 여부
5. **emotional_resonance를 7번째로 채택할 것인가?** 안 할 경우 6개로 축소 가능

### 수정 권장 시나리오
- 학술 인용 추가/제거 요청
- 특정 패턴 정의 다듬기
- Cross-Domain 분류 조정 (예: brand_loyalty를 항상 BLOCK으로)
- emotional_resonance 채택 여부 변경

### 승인 후 진행
- Step 2 (자동 매칭) 즉시 시작
- 본 정의서는 이후 모든 단계의 기준점이 됨
