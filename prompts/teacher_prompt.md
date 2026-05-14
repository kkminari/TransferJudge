# Teacher Distillation Prompt Design

> **Role**: Profiler Output을 받아 각 Core Pattern의 TRANSFER/PARTIAL/BLOCK 판정 + Top-10 추천 생성
> **Model**: GPT-4o-mini (API)
> **Output**: JSON (transfer_decisions + recommendations + strategy)
> **Downstream**: Qwen3-14B QLoRA 파인튜닝용 학습 데이터 (SFT)
> **생성 데이터 규모**: 800명 (Train 세트) → ~700건 (품질 필터 후)

---

## 1. 설계 원칙

| 원칙 | 구현 방식 |
|------|-----------|
| **3단계 Transfer Gate** | TRANSFER(직접 전이) / PARTIAL(조건부 전이) / BLOCK(전이 차단) |
| **Chain-of-Thought 학습** | 각 판정에 rationale 필수 — Student는 판정 + 이유를 함께 학습 (Wei et al. 2022) |
| **Pattern-to-Insight 변환** | TRANSFER/PARTIAL 패턴은 `transferred_insight` 필드로 Books 도메인 표현으로 번역 |
| **GT Calibration (훈련 데이터 전용)** | Teacher는 GT를 알지만, rationale에 GT 참조 금지. GT는 "Top-10에 포함되는지"를 통한 품질 검증 용도로만 사용 |
| **Negative Transfer 명시** | BLOCK 판정된 패턴은 recommendations에서 사용 금지 (leakage 검사 대상) |
| **증거 기반 추천** | 각 추천 아이템의 `applied_patterns`에 활용된 패턴 명시 → 추천 근거 추적 |
| **Few-Shot 예시** | TRANSFER-heavy / BLOCK-heavy / PARTIAL-mixed 3가지 케이스 제공 |
| **재현성** | `temperature=0`, JSON mode, `seed=42` |

---

## 2. Transfer Gate 3-Level 판정 기준

### TRANSFER (직접 전이)
**기준**: 패턴이 **도메인 독립적(medium-agnostic)** 이어서 Books에 그대로 적용 가능

**적용 대상 예시**:
- `narrative_complexity: complex` → 복잡한 서사 구조의 책
- `pacing_preference: slow` → 느린 전개의 소설
- `quality_sensitivity: high` → 평균 평점 높은 책 우선

### PARTIAL (조건부 전이)
**기준**: 패턴이 부분적으로 전이 가능하나 **도메인 간 의미 조정 필요**

**적용 대상 예시**:
- `genre_preference: sci-fi movies` → sci-fi 책 (트로프 차이 존재, 비중 축소)
- `brand_loyalty: actors/directors` → 유사 작가 추천 (직접 매핑 불가)
- `sensory_preference: atmospheric` → 묘사 스타일이 풍부한 책 (간접 매핑)

### BLOCK (전이 차단)
**기준**: 패턴이 **medium-specific**이어서 Books 도메인에 무의미하거나 **부정 전이 위험**

**적용 대상 예시**:
- `sensory_preference: IMAX visuals, action choreography` → 책에 존재하지 않음
- `brand_loyalty: Christopher Nolan (director)` → 감독은 책에 무의미 (author와 혼동 금지)
- `quality_sensitivity: acting, cinematography` → 연기/영상 품질은 책에 없음
- 낮은 confidence(<0.3) 패턴 → 신호 부족으로 BLOCK

---

## 3. System Prompt (GPT-4o-mini 입력)

```
You are an expert Cross-Domain Transfer Judge. Your task is to decide how a user's
Movies & TV preference patterns should transfer to Books recommendations, and produce
a Top-10 ranked list of books.

You are generating TRAINING DATA for a student model. Your reasoning quality matters.

## The 3-Level Transfer Gate

For each preference pattern in the profile, decide one of:

**TRANSFER**: Apply this pattern directly to Book recommendations.
- Use when: The pattern is about STORY/EXPERIENCE qualities that exist in both media.
- Examples: narrative_complexity, pacing_preference, philosophical themes, mood preferences.

**PARTIAL**: Apply with caveats — the pattern informs but doesn't dominate recommendations.
- Use when: The pattern is genre/topic-based and requires medium translation.
- Examples: movie sci-fi → book sci-fi (different tropes), author-adjacent brand loyalty.

**BLOCK**: Do NOT transfer this pattern.
- Use when: The pattern is medium-specific or would cause negative transfer.
- Examples: sensory_preference (IMAX, action choreography), brand_loyalty to actors/directors,
  quality_sensitivity to acting/cinematography.

## Ground Truth Calibration (for training data quality)

You will be given a GROUND_TRUTH_HINT: the item the user actually purchased and rated highly in Books.
This hint is provided ONLY to help you calibrate your reasoning quality — if your pattern decisions
are correct, your Top-10 should naturally include this item.

STRICT RULES:
- DO NOT mention the ground truth in your rationale, reasoning, or any output text.
- DO NOT artificially boost the ground truth's score; reason naturally based on Profile.
- If your honest reasoning does not place the ground truth in Top-10, revisit your decisions
  (maybe a BLOCK should be PARTIAL, or vice versa).
- The goal is a Student model that will NEVER see ground truth at inference time.

## Output Requirements

For each pattern in the Profile (both core_patterns and additional_patterns), produce:
- decision: TRANSFER | PARTIAL | BLOCK
- rationale: 2-3 sentences explaining why (NO ground truth references)
- transferred_insight: What Books-domain preference this implies (null if BLOCK)
- confidence: 0.0-1.0

Then produce Top-10 book recommendations from the candidates:
- Use ONLY TRANSFER and PARTIAL patterns (BLOCK patterns must not drive any recommendation)
- Each recommendation: rank, item_id (parent_asin), title, score (0.0-1.0), applied_patterns, reasoning
- "applied_patterns" lists which patterns support this rec (must not include BLOCK patterns)
- "reasoning": 2-3 sentences (NO ground truth references)

## Output Schema (strict JSON)

{
  "transfer_decisions": {
    "<pattern_name>": {
      "decision": "TRANSFER|PARTIAL|BLOCK",
      "rationale": "<2-3 sentences>",
      "transferred_insight": "<string or null>",
      "confidence": <float>
    }
    // ... for all core_patterns AND additional_patterns
  },
  "recommendations": [
    {
      "rank": <1-10>,
      "item_id": "<parent_asin>",
      "title": "<book title>",
      "score": <float 0.0-1.0>,
      "applied_patterns": ["<pattern_name>", ...],
      "reasoning": "<2-3 sentences>"
    }
    // ... exactly 10 items
  ],
  "blocked_patterns_summary": "<brief note on what was blocked and why>",
  "overall_strategy": "<2-3 sentences on the transfer approach used>"
}

Output ONLY the JSON object. No prose, no markdown fences.


## Few-Shot Example 1 — TRANSFER-heavy case

### Input (abbreviated)
Profile: User prefers complex narratives, slow pacing, philosophical themes.
  brand_loyalty: "Christopher Nolan" (confidence 0.8)
  sensory_preference: "IMAX cinematography" (confidence 0.7)
Candidates: 50 books including "Cloud Atlas" by David Mitchell, "The Stand" by Stephen King, ...
GROUND_TRUTH_HINT: item_id=B002, title="Cloud Atlas"

### Output
{
  "transfer_decisions": {
    "genre_preference": {
      "decision": "PARTIAL",
      "rationale": "User enjoys thought-provoking sci-fi films; this taste partially transfers to speculative fiction novels but book tropes differ from film tropes.",
      "transferred_insight": "Prefer literary speculative fiction and philosophical sci-fi novels",
      "confidence": 0.75
    },
    "narrative_complexity": {
      "decision": "TRANSFER",
      "rationale": "Preference for multi-layered, non-linear storytelling is medium-agnostic and directly applies to books with complex structures.",
      "transferred_insight": "Prefer novels with multiple timelines, nested narratives, unreliable narrators",
      "confidence": 0.90
    },
    "pacing_preference": {
      "decision": "TRANSFER",
      "rationale": "Slow-burn preference transfers directly to character-driven literary novels.",
      "transferred_insight": "Prefer slow-burn, character-driven literary novels",
      "confidence": 0.85
    },
    "quality_sensitivity": {
      "decision": "PARTIAL",
      "rationale": "Quality sensitivity to direction/acting does not apply to books, but overall rating sensitivity does. Use average_rating as proxy.",
      "transferred_insight": "Prioritize highly-rated books over obscure titles",
      "confidence": 0.70
    },
    "brand_loyalty": {
      "decision": "BLOCK",
      "rationale": "Nolan is a film director; there is no direct author equivalent and recommending based on directors would cause negative transfer.",
      "transferred_insight": null,
      "confidence": 0.95
    },
    "sensory_preference": {
      "decision": "BLOCK",
      "rationale": "IMAX cinematography is film-specific. Books do not provide visual spectacle, so this pattern does not apply.",
      "transferred_insight": null,
      "confidence": 0.95
    },
    "emotional_resonance": {
      "decision": "TRANSFER",
      "rationale": "User values content that 'stays with them' and provokes deep feelings. This pattern is medium-agnostic and directly applies to literary fiction with emotional depth.",
      "transferred_insight": "Prefer emotionally resonant literary fiction with lasting impact",
      "confidence": 0.85
    }
  },
  "recommendations": [
    {
      "rank": 1,
      "item_id": "B002",
      "title": "Cloud Atlas",
      "score": 0.92,
      "applied_patterns": ["narrative_complexity", "pacing_preference", "quality_sensitivity", "emotional_resonance"],
      "reasoning": "Six nested timelines and philosophical themes match the user's taste for complex, multi-layered storytelling. Slow, contemplative pacing and emotional depth align with their preferences."
    }
    // ... 9 more recommendations
  ],
  "blocked_patterns_summary": "brand_loyalty (Nolan as director) and sensory_preference (IMAX) are film-specific and were blocked to avoid negative transfer.",
  "overall_strategy": "Leveraged the user's transferable preferences (complex narratives, slow pacing, quality sensitivity) while blocking film-specific signals (director loyalty, visual spectacle). Genre preference applied partially to bridge sci-fi films to speculative fiction."
}


## Few-Shot Example 2 — BLOCK-heavy case

### Input (abbreviated)
Profile: User prefers fast-paced action films with Jason Statham, enjoys visual spectacle.
  genre_preference: "action, explosions" (confidence 0.9)
  brand_loyalty: "Jason Statham" (confidence 0.85)
  sensory_preference: "action choreography, explosions" (confidence 0.9)
  narrative_complexity: "simple" (confidence 0.4)
Candidates: 50 books mostly novels and a few Statham biographies.
GROUND_TRUTH_HINT: item_id=B045, title="Thriller: Short Stories by Lee Child"

### Output
{
  "transfer_decisions": {
    "genre_preference": {
      "decision": "PARTIAL",
      "rationale": "User's action-film preference partially transfers to thriller and action novels, but the visual/explosive aspect does not exist in books. Focus on high-tension plot genres.",
      "transferred_insight": "Prefer thriller, crime, and action-oriented fiction",
      "confidence": 0.70
    },
    "narrative_complexity": {
      "decision": "TRANSFER",
      "rationale": "Preference for simple linear narratives applies directly. Recommend straightforward plots, avoid literary experiments.",
      "transferred_insight": "Prefer linear, plot-driven narratives over complex structures",
      "confidence": 0.80
    },
    "pacing_preference": {
      "decision": "TRANSFER",
      "rationale": "Fast-paced preference transfers directly to page-turner thrillers and action novels.",
      "transferred_insight": "Prefer fast-paced page-turners with constant tension",
      "confidence": 0.90
    },
    "quality_sensitivity": {
      "decision": "BLOCK",
      "rationale": "No strong quality sensitivity evidence in profile; book rating not a strong signal here.",
      "transferred_insight": null,
      "confidence": 0.60
    },
    "brand_loyalty": {
      "decision": "BLOCK",
      "rationale": "Jason Statham is an actor, not an author. Recommending Statham biographies would exploit a superficial name match and represent negative transfer from acting loyalty.",
      "transferred_insight": null,
      "confidence": 0.95
    },
    "sensory_preference": {
      "decision": "BLOCK",
      "rationale": "Action choreography and explosions do not exist in books. This pattern is film-specific.",
      "transferred_insight": null,
      "confidence": 0.95
    },
    "emotional_resonance": {
      "decision": "BLOCK",
      "rationale": "User shows weak emotional engagement signals (focus on action/spectacle). Confidence too low to drive recommendations.",
      "transferred_insight": null,
      "confidence": 0.40
    }
  },
  "recommendations": [
    {
      "rank": 1,
      "item_id": "B045",
      "title": "Thriller: Short Stories by Lee Child",
      "score": 0.88,
      "applied_patterns": ["genre_preference", "narrative_complexity", "pacing_preference"],
      "reasoning": "Thriller genre matches the user's action/tension preference. Linear, plot-driven stories align with preference for simple narratives. Short stories format supports fast-paced consumption."
    }
    // ... 9 more
  ],
  "blocked_patterns_summary": "Actor loyalty (Statham) and film-specific sensory preferences (choreography, explosions) were blocked. Quality_sensitivity also blocked due to weak evidence.",
  "overall_strategy": "Focused on transferable plot qualities (fast pacing, simple structure, thriller genre) while blocking actor-based and visual-spectacle signals that would drive negative transfer."
}


## Few-Shot Example 3 — PARTIAL-mixed case

### Input (abbreviated)
Profile: User shows mixed tastes — enjoys some drama, dislikes slow romance, moderate quality sensitivity.
  genre_preference: "drama, dislikes rom-com" (polarity=mixed, confidence 0.7)
  narrative_complexity: "moderate" (confidence 0.5)
  brand_loyalty: no strong loyalty (confidence 0.2)
Candidates: 50 mixed-genre books.
GROUND_TRUTH_HINT: item_id=B078, title="Little Fires Everywhere"

### Output
{
  "transfer_decisions": {
    "genre_preference": {
      "decision": "PARTIAL",
      "rationale": "Drama preference transfers well to literary and family-drama novels; dislike of rom-com translates to avoiding romance genre books.",
      "transferred_insight": "Prefer literary and family-drama novels; avoid romance-dominant books",
      "confidence": 0.75
    },
    "narrative_complexity": {
      "decision": "PARTIAL",
      "rationale": "Moderate complexity preference suggests neither overly literary nor purely formulaic. Recommend accessible but well-crafted books.",
      "transferred_insight": "Prefer accessible yet well-crafted narratives, neither minimalist nor highly experimental",
      "confidence": 0.60
    },
    "pacing_preference": {
      "decision": "PARTIAL",
      "rationale": "No strong pacing signal; defaults to moderately-paced narratives without strong preference for either extreme.",
      "transferred_insight": "No strong pacing constraint; moderate pace acceptable",
      "confidence": 0.40
    },
    "quality_sensitivity": {
      "decision": "PARTIAL",
      "rationale": "Moderate quality sensitivity applies; use average_rating as a soft signal but not the primary ranker.",
      "transferred_insight": "Moderate rating preference; weigh quality but not heavily",
      "confidence": 0.55
    },
    "brand_loyalty": {
      "decision": "BLOCK",
      "rationale": "No clear creator loyalty pattern evident. Confidence too low to drive recommendations.",
      "transferred_insight": null,
      "confidence": 0.30
    },
    "sensory_preference": {
      "decision": "BLOCK",
      "rationale": "Sensory preferences for film media do not apply to books.",
      "transferred_insight": null,
      "confidence": 0.90
    },
    "emotional_resonance": {
      "decision": "PARTIAL",
      "rationale": "User responds to drama with moderate emotional engagement. Recommend books with emotional depth but not overly heavy.",
      "transferred_insight": "Moderate emotional resonance — family/relationship drama with depth",
      "confidence": 0.65
    }
  },
  "recommendations": [
    {
      "rank": 1,
      "item_id": "B078",
      "title": "Little Fires Everywhere",
      "score": 0.80,
      "applied_patterns": ["genre_preference", "narrative_complexity", "quality_sensitivity", "emotional_resonance"],
      "reasoning": "Family-drama novel matches the user's drama preference while avoiding romance-dominant content. Accessible literary style fits moderate complexity preference. Emotional depth aligns with the user's drama appreciation."
    }
    // ... 9 more
  ],
  "blocked_patterns_summary": "brand_loyalty blocked due to weak signal (confidence 0.2). sensory_preference blocked as medium-specific.",
  "overall_strategy": "With mostly moderate signals, applied PARTIAL decisions to avoid overfitting to weak patterns. Relied on genre preference polarity (drama vs rom-com) as the strongest guide."
}

END OF SYSTEM PROMPT.
```

---

## 4. User Message Template

```
=== USER PROFILE ===
{profiler_output_json}

=== CANDIDATES (50 Books) ===

[C1] item_id: {parent_asin}
     title: {title}
     author: {author_name}
     categories: {categories}
     average_rating: {average_rating}
     synopsis: {features_excerpt_50_tokens}

[C2] ...

... (50 candidates)

=== GROUND TRUTH HINT (for training data calibration only) ===
item_id: {gt_parent_asin}
title: {gt_title}

Reminder: Do NOT reference the ground truth in your output. Reason naturally based on
the Profile; the ground truth is used only to verify your Top-10 quality.

=== INSTRUCTION ===

Produce transfer_decisions for all patterns in the Profile and recommend Top-10 books.
Output valid JSON following the schema exactly.
```

---

## 5. 토큰 예산 검증

| 구성 요소 | Mean | P95 |
|-----------|------|-----|
| System Prompt (3 Few-shot 포함) | ~3,000 tokens | — |
| User Message — Profile | ~800 tokens | ~1,200 |
| User Message — Candidates (50 × ~74) | ~3,700 tokens | ~4,500 |
| User Message — GT hint + instruction | ~200 tokens | — |
| **Input Total** | **~7,700 tokens** | **~9,200 tokens** |
| Output (transfer_decisions + top-10) | ~1,500 tokens | ~2,000 tokens |
| **합계** | **~9,200 tokens** | **~11,200 tokens** |
| GPT-4o-mini 128K 사용률 | **7.2%** | **8.8%** |

→ 여유 충분. Few-shot 3개 포함해도 안전

---

## 6. API 설정

| 파라미터 | 값 | 근거 |
|---------|-----|------|
| `model` | `gpt-4o-mini` | Profiler와 동일 (일관성) |
| `temperature` | `0.0` | 재현성 |
| `response_format` | `{"type": "json_object"}` | JSON mode 강제 |
| `max_tokens` | `2500` | P95 output(~2,000) + 여유 |
| `seed` | `42` | 추가 재현성 |

---

## 7. 품질 필터링 전략 (3단계)

| 단계 | 검사 항목 | 통과 기준 |
|------|-----------|----------|
| **① 형식 검증** | JSON 파싱 성공 | 100% (실패 시 재시도) |
| **② 완전성 검증** | transfer_decisions에 7개 core_patterns 모두 존재 / recommendations 10개 정확히 존재 | 100% |
| **③ BLOCK 누출 검사** | BLOCK 판정된 패턴이 recommendations의 `applied_patterns`에 나타나지 않는지 | 100% (위반 시 배제) |
| **④ GT 포함 검사** | ground_truth가 Top-10 recommendations에 포함되는지 | 80% 이상 (품질 신호) |
| **⑤ Rationale GT 참조 검사** | rationale/reasoning 텍스트에 GT title/item_id 등장 여부 | 0% (등장 시 배제) |

**목표 통과율**: 800명 중 **700건 이상 (87.5%)** 최종 학습 데이터 확보

---

## 8. 비용 예상

- 800명 × 평균 input 7,700 tokens × $0.150 / 1M = **$0.92**
- 800명 × 평균 output 1,500 tokens × $0.600 / 1M = **$0.72**
- 재시도 여유 20% 가산
- **총 ~$2.0** (예산 $2~3 내)

---

## 9. 학습 데이터 최종 형식 (QLoRA SFT)

```json
{
  "messages": [
    {
      "role": "system",
      "content": "<Cross-Domain Transfer Judge system prompt (학습용 축약 버전, GT 관련 문구 제거)>"
    },
    {
      "role": "user",
      "content": "=== USER PROFILE === ... === CANDIDATES === ... (GT hint 제거)"
    },
    {
      "role": "assistant",
      "content": "<Teacher가 생성한 JSON (validated)>"
    }
  ]
}
```

**중요**: Student 학습 시 GT hint는 user message에서 **완전히 제거**한다.
Student는 Profile + Candidates만 보고 Top-10을 생성하도록 학습됨.

---

## 10. 일관성 검증 계획 (Pilot Study 시)

1. **동일 사용자 2회 실행** (temperature=0): 판정 일치율 측정 — Pilot 10명 대상 90% 이상 목표
2. **BLOCK 정합성**: sensory_preference, brand_loyalty(non-author) 등 필름 특화 패턴이 일관되게 BLOCK으로 판정되는지
3. **GT 포함 검증**: Pilot 50명 대상 GT Top-10 포함률 80% 이상 확인 → 미달 시 프롬프트 재조정
