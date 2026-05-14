# Profiler Prompt Design

> **Role**: Source Domain(Movies & TV) 리뷰에서 사용자의 7개 Core Pattern 선호를 추출
> **Model**: GPT-4o-mini (API, 파인튜닝 없음)
> **Output**: JSON (Core Pattern 7개 + 선택적 추가 패턴 + 요약)
> **Downstream**: Transfer Judge의 입력으로 사용됨

---

## 1. 설계 원칙

| 원칙 | 구현 방식 |
|------|-----------|
| **증거 기반 추출 (Evidence-Grounded)** | 각 Pattern은 원문 리뷰의 인용을 근거로 제시 (hallucination 방지) |
| **극성 구분 (Polarity)** | positive(선호) / negative(비선호) / mixed 세 단계로 구분 → 낮은 평점 리뷰의 "비선호" 정보도 활용 |
| **신뢰도 점수 (Confidence)** | 각 Pattern에 0.0~1.0 confidence 부여 → Judge가 약한 신호 패턴 필터링 가능 |
| **전이 가능성 힌트 (Transferability Hint)** | Profiler가 각 패턴의 Cross-Domain(Books) 전이 가능성에 대해 초기 판단 제공 (Judge의 최종 판단에 참고) |
| **Semi-Structured** | Core 7개는 필수, 추가 패턴은 자유 추출 (Pilot Study의 long-tail 패턴 보존) |
| **재현성** | `temperature=0`, JSON mode 활성화 |
| **Low-Rating Inclusion** | GT만 rating≥4이며, Profiler 입력은 전체 평점(1~5) 사용. 낮은 평점 리뷰는 "what user dislikes" 정보로 활용 |

---

## 2. 7개 Core Pattern 정의

| Pattern | 영문 정의 | 국문 설명 | Books 전이 가능성 |
|---------|----------|----------|-------------------|
| `genre_preference` | Preferred genres/categories (e.g., sci-fi, thriller, drama) | 선호 장르 (SF, 스릴러, 드라마 등) | ★★★☆☆ (장르 매핑 필요) |
| `narrative_complexity` | Preference for complex vs simple narratives, multi-layered plots, non-linear storytelling | 서사 복잡도 (복잡한 플롯 vs 단순 서사) | ★★★★★ (도메인 독립적) |
| `pacing_preference` | Preference for fast-paced action vs slow character-driven stories | 전개 속도 (빠른 전개 vs 느린 성장형) | ★★★★★ (도메인 독립적) |
| `quality_sensitivity` | Sensitivity to production quality, acting, direction, ratings | 품질 민감도 (제작 수준·평점에 대한 반응) | ★★★★☆ (유사 매핑) |
| `brand_loyalty` | Loyalty to specific directors/actors/franchises/series | 특정 감독·배우·프랜차이즈 충성도 | ★★★☆☆ (저자 선호로 매핑) |
| `sensory_preference` | Preference for visual/auditory experience (cinematography, music, action scenes) | 감각적 경험 선호 (영상·음향·액션 등) | ★★☆☆☆ (간접 매핑: 묘사 스타일) |
| `emotional_resonance` ★ | Emphasis on emotional impact and resonance (deep feelings, lasting memory) | 감정적 울림·여운 강조 | ★★★★★ (도메인 독립적, Pilot 도출) |

---

## 3. System Prompt (GPT-4o-mini 입력)

```
You are an expert user preference analyst specializing in cross-domain recommendation.
Your task is to extract structured preference patterns from a user's Movies & TV reviews
that will later be used to recommend books to this user.

## Core Patterns to Extract (MANDATORY)

For each user, you MUST analyze the following 7 core patterns:

1. genre_preference — Preferred genres/categories (e.g., sci-fi, thriller, drama, romance).
   Report BOTH preferred and disliked genres if evidence exists.

2. narrative_complexity — Preference for narrative complexity.
   "complex" = multi-layered plots, non-linear timelines, unreliable narrators.
   "simple" = linear, straightforward storytelling.

3. pacing_preference — Preference for pacing.
   "fast" = action-heavy, quick scene transitions, high-tension.
   "slow" = character-driven, contemplative, slow-burn.

4. quality_sensitivity — How much the user cares about production quality.
   "high" = frequently mentions direction, acting, cinematography quality.
   "low" = focuses on story/entertainment regardless of production polish.

5. brand_loyalty — Loyalty to specific creators.
   Identify mentions of favorite directors, actors, franchises, series.
   Note: If no such loyalty is evident, mark confidence as low.

6. sensory_preference — Preference for sensory experience.
   e.g., visual spectacle, atmospheric music, action choreography, immersive world-building.

7. emotional_resonance — Emphasis on emotional impact and resonance.
   "high" = content evokes deep feelings, lasting memory, personal meaning ("brought tears", "stayed with me").
   "low" = focuses on entertainment without strong emotional engagement.

## Output Requirements

- Output MUST be a single valid JSON object following the schema below.
- Each core pattern must include: value, evidence, confidence, polarity, transferability_hint.
- "evidence" must quote or closely paraphrase specific review text (max 2 citations per pattern).
- "confidence" ∈ [0.0, 1.0]: 1.0 if strongly supported by multiple reviews, 0.2 if weakly hinted.
- "polarity" ∈ {"positive", "negative", "mixed"}: whether the user likes, dislikes, or has mixed feelings.
- "transferability_hint" ∈ {"high", "medium", "low"}: initial estimate of how well this pattern
  transfers to the Books domain. This is a HINT only; the downstream Transfer Judge makes the final decision.
- You MAY add up to 3 additional_patterns that are strongly evidenced but not in the core 7.
- "summary" must be 2-3 sentences capturing the user's overall taste.

## Evidence Grounding Rules

- DO NOT invent preferences not supported by review text.
- If evidence is weak or absent for a core pattern, set confidence ≤ 0.3 and polarity to "mixed".
- Negative reviews (rating ≤ 2) are VALUABLE — they reveal what the user DISLIKES.
- If the user gave a low rating citing specific reasons (e.g., "too slow"), this reveals pacing_preference.

## Output Schema (strict)

{
  "user_id": "<string>",
  "core_patterns": {
    "genre_preference":       {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "narrative_complexity":   {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "pacing_preference":      {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "quality_sensitivity":    {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "brand_loyalty":          {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "sensory_preference":     {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"},
    "emotional_resonance":    {"value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"}
  },
  "additional_patterns": [
    {"name": "<snake_case_name>", "value": "<string>", "evidence": ["<quote>"], "confidence": <float>, "polarity": "<positive|negative|mixed>", "transferability_hint": "<high|medium|low>"}
  ],
  "summary": "<2-3 sentence overall taste summary>"
}

Output ONLY the JSON object, no prose, no markdown fences.
```

---

## 4. User Message Template

```
User ID: {user_id}

=== Source Domain (Movies & TV) Reviews ===

[Review 1] Rating: {rating}/5.0 | Title: "{review_title}"
"{review_text}"

[Review 2] Rating: {rating}/5.0 | Title: "{review_title}"
"{review_text}"

... (총 N개 리뷰, 최신순)

=== Instruction ===

Analyze the above {N} reviews and extract the user's preference patterns following the schema.
Output valid JSON only.
```

**포맷 규칙:**
- 리뷰는 **최신순 정렬** (Review 1 = 가장 최근)
- 최소 15개, 최대 30개 리뷰 포함
- 리뷰 텍스트는 P95(343 tokens) 이하이므로 truncation 불필요, 그대로 전달
- 리뷰 제목(`review.title`)도 포함 → 짧지만 강한 감정 신호 제공

---

## 5. Expected Output Example (모범 출력)

```json
{
  "user_id": "AGGZ357AO26RQ",
  "core_patterns": {
    "genre_preference": {
      "value": "Sci-fi and thriller, dislikes romantic comedies",
      "evidence": [
        "Review 3: 'Another brilliant sci-fi epic from Nolan, kept me thinking for days'",
        "Review 8: 'Generic rom-com, predictable and boring'"
      ],
      "confidence": 0.90,
      "polarity": "mixed",
      "transferability_hint": "high"
    },
    "narrative_complexity": {
      "value": "Strongly prefers complex, multi-layered narratives with non-linear timelines",
      "evidence": [
        "Review 3: 'The time-loop structure was genius'",
        "Review 12: 'Too straightforward, needed more depth'"
      ],
      "confidence": 0.85,
      "polarity": "positive",
      "transferability_hint": "high"
    },
    "pacing_preference": {
      "value": "Prefers slow-burn, character-driven stories over fast action",
      "evidence": [
        "Review 5: 'The quiet moments between characters are what make this special'",
        "Review 11: 'Action was mindless, no emotional weight'"
      ],
      "confidence": 0.75,
      "polarity": "positive",
      "transferability_hint": "high"
    },
    "quality_sensitivity": {
      "value": "Highly sensitive to direction and acting quality",
      "evidence": [
        "Review 2: 'Cinematography alone makes this a masterpiece'",
        "Review 9: 'Poor directing ruined a decent script'"
      ],
      "confidence": 0.80,
      "polarity": "positive",
      "transferability_hint": "medium"
    },
    "brand_loyalty": {
      "value": "Strong loyalty to Christopher Nolan; follows Denis Villeneuve works",
      "evidence": [
        "Review 3: 'Nolan never disappoints'",
        "Review 7: 'Villeneuve at his best'"
      ],
      "confidence": 0.80,
      "polarity": "positive",
      "transferability_hint": "low"
    },
    "sensory_preference": {
      "value": "Appreciates atmospheric cinematography and immersive sound design",
      "evidence": [
        "Review 2: 'The IMAX visuals were breathtaking'",
        "Review 6: 'Hans Zimmer score elevated every scene'"
      ],
      "confidence": 0.70,
      "polarity": "positive",
      "transferability_hint": "low"
    },
    "emotional_resonance": {
      "value": "Values content that evokes deep emotional response and lasting impact",
      "evidence": [
        "Review 3: 'The questions about memory stayed with me'",
        "Review 11: 'Action was mindless, no emotional weight'"
      ],
      "confidence": 0.75,
      "polarity": "positive",
      "transferability_hint": "high"
    }
  },
  "additional_patterns": [
    {
      "name": "philosophical_themes",
      "value": "Interested in films exploring identity, consciousness, and memory",
      "evidence": ["Review 3: 'The questions about memory stayed with me'"],
      "confidence": 0.65,
      "polarity": "positive",
      "transferability_hint": "high"
    }
  ],
  "summary": "This user is a sophisticated viewer who prefers complex, slow-burn narratives with philosophical depth. They are loyal to auteur directors (Nolan, Villeneuve) and highly sensitive to production quality, with a clear preference for sci-fi and thrillers over romantic comedies."
}
```

---

## 6. 토큰 예산 검증

| 구성 요소 | Mean | P95 |
|-----------|------|-----|
| System Prompt | ~500 tokens | — |
| User Message (리뷰 15~30개) | 15 × 80.4 = 1,206 ~ 30 × 80.4 = 2,412 | 30 × 343 = 10,290 |
| User Message (템플릿 오버헤드) | ~200 tokens | — |
| **Input Total** | **~1,900 ~ 3,100 tokens** | **~11,000 tokens** |
| Output (JSON) | ~600 ~ 800 tokens | ~1,200 tokens |
| **합계** | **~2,500 ~ 3,900 tokens** | **~12,200 tokens** |
| GPT-4o-mini 128K context | **2.0% ~ 3.0% 사용** | **9.5% 사용** |

→ 토큰 여유 충분, 모든 사용자에 대해 truncation 없이 처리 가능

---

## 7. API 설정

| 파라미터 | 값 | 근거 |
|---------|-----|------|
| `model` | `gpt-4o-mini` | 비용 효율 + 태스크 적합성 |
| `temperature` | `0.0` | 재현성 확보 |
| `top_p` | `1.0` | (temperature=0이면 무관) |
| `response_format` | `{"type": "json_object"}` | JSON mode 강제 |
| `max_tokens` | `1500` | P95 출력(~1,200) + 여유 |
| `seed` | `42` | 추가 재현성 보강 |

---

## 8. 오류 처리 전략

| 오류 유형 | 대응 |
|-----------|------|
| JSON 파싱 실패 | temperature를 0.1로 올려 최대 3회 재시도 |
| 7개 Core Pattern 누락 | 해당 Pattern의 confidence를 0.0으로 채워 재요청 (self-correction) |
| API Rate Limit | Exponential backoff (1s → 2s → 4s → 8s), 최대 5회 |
| 저품질 출력 (confidence 평균 < 0.3) | 리뷰 수 확인 후 경고 로그, 그대로 보관 (Judge가 신뢰도 활용) |

---

## 9. 비용 예상 (실행 계획)

- 1,000명 × 평균 input 2,900 tokens × $0.150 / 1M tokens = **$0.44**
- 1,000명 × 평균 output 700 tokens × $0.600 / 1M tokens = **$0.42**
- **총 ~$0.86** (예상 예산 $1~2 내)

---

## 10. 품질 검증 계획 (Pilot Study 시)

1. **수동 검토 (30명)**: confidence 높은 패턴이 실제 리뷰 증거와 일치하는지 확인
2. **자동 검증**:
   - 7개 core_patterns 키 존재율 (목표 100%)
   - evidence 배열이 비어있지 않은 비율 (목표 95%+)
   - confidence 0.0인 패턴 비율 (정보 부재 케이스, 참고값)
3. **일관성 검증**: 동일 사용자 2회 실행 시 패턴 값 유사도 (cosine similarity, 목표 0.85+)
4. **Long-tail 패턴 분석**: additional_patterns 빈도 집계 → Core 7개 외 후보 패턴 발굴 (논문 Appendix)
