# Pilot Profiler Prompt — 비구조화 패턴 추출

> **목적**: Core Pattern 6개 사전 정보 없이 LLM이 데이터에서 자연스럽게 패턴을 도출하도록 유도
> **사용**: Pilot Study Phase 2 (100명 GPT-4o-mini 호출)
> **차이점 (본 실험 Profiler 대비)**: 본 실험은 6개 패턴 강제 + transferability_hint, Pilot은 free-form

---

## 1. 설계 원칙

| 원칙 | 구현 방식 |
|------|-----------|
| **편향 최소화** | Core Pattern 6개 사전 노출 금지. "패턴 종류·이름·개수는 자유" 명시 |
| **Snake_case 강제** | 정규화 단계의 표면 정리 부담 감소 |
| **Evidence 필수** | hallucination 방지 + 정규화 시 description 활용 |
| **Polarity 포함** | 본 실험과 일관 (positive/negative/mixed) |
| **5~15개 권장** | 너무 적으면 patterns 부족, 너무 많으면 노이즈 |
| **재현성** | temperature=0.0, seed=42, JSON mode |

---

## 2. System Prompt (GPT-4o-mini 입력)

```
You are an expert user preference analyst. Your task is to read a user's
Movies & TV reviews and extract the preference patterns you genuinely observe in the data.

## Important Rules

- Naming and number of patterns is up to YOU. Discover patterns naturally from the reviews.
- DO NOT use any predefined list of pattern types. Avoid generic catch-all categories.
- Pattern names must be snake_case (e.g., "narrative_complexity", "atmospheric_mood",
  "auteur_loyalty"). Be specific and descriptive.
- Each pattern must include:
  - name (snake_case)
  - description (1-2 sentences explaining what this pattern captures)
  - evidence (1-2 review quotes that directly support this pattern)
  - confidence (0.0-1.0): how strongly the data supports this pattern
  - polarity (positive | negative | mixed): whether the user likes, dislikes, or is mixed

## Quality Guidelines

- Aim for 5-15 patterns per user — extract what you genuinely observe.
- Avoid trivial patterns (e.g., "user_likes_movies", "watches_films" are too vague).
- Patterns should be ACTIONABLE for cross-domain recommendation
  (e.g., useful for recommending books to this user — think about what transfers vs what doesn't).
- Negative reviews (rating <= 2) are valuable — they reveal what the user DISLIKES.
- DO NOT invent preferences not supported by review text.
- Each pattern's evidence must directly quote or closely paraphrase actual review content.

## Output Schema (strict JSON)

{
  "user_id": "<string>",
  "patterns": [
    {
      "name": "<snake_case_name>",
      "description": "<1-2 sentences>",
      "evidence": ["<review quote 1>", "<review quote 2>"],
      "confidence": <float 0.0-1.0>,
      "polarity": "<positive|negative|mixed>"
    }
    // ... 5 to 15 patterns
  ],
  "summary": "<2-3 sentence overall taste summary>"
}

Output ONLY the JSON object. No prose, no markdown fences.
```

---

## 3. User Message Template

```
User ID: {user_id}

=== Movies & TV Reviews (most recent first) ===

[Review 1] Rating: {rating}/5.0 | Title: "{review_title}"
"{review_text}"

[Review 2] Rating: {rating}/5.0 | Title: "{review_title}"
"{review_text}"

... (총 N개 리뷰, 최신순)

=== Instruction ===

Analyze the above {N} reviews and extract the user's preference patterns.
Discover patterns naturally — do not use any predefined list.
Output valid JSON following the schema.
```

---

## 4. API 설정

| 파라미터 | 값 |
|---------|-----|
| `model` | `gpt-4o-mini` |
| `temperature` | `0.0` |
| `seed` | `42` |
| `response_format` | `{"type": "json_object"}` |
| `max_tokens` | `2000` (비구조화이므로 본 실험 1500보다 약간 ↑) |

---

## 5. 토큰 예산 (예상)

| 구성 | 토큰 |
|------|------|
| System Prompt | ~700 |
| User Message (15-30 리뷰, mean 80.4 tokens/건) | ~1,200~2,400 |
| **Input 합계** | ~2,000~3,100 |
| Output (5-15 patterns, 패턴당 ~100 tokens) | ~600~1,500 |
| **Total** | ~2,600~4,600 |

128K context의 ~3.6% 사용. 충분한 여유.

---

## 6. 비용 (100명)

- 평균 input ~2,500 tokens × 100 × $0.15/1M = **$0.038**
- 평균 output ~1,000 tokens × 100 × $0.60/1M = **$0.06**
- **합계: ~$0.10**

---

## 7. 본 실험 Profiler와의 차이 (정리)

| 항목 | 본 실험 Profiler | Pilot Profiler |
|------|------------------|----------------|
| 패턴 종류 | 6개 Core 강제 + 추가 3개까지 | 자유 (5~15개) |
| `transferability_hint` 필드 | 필수 | 없음 (사후 분석에서 도출) |
| 사전 정의 | genre/narrative/pacing/quality/brand/sensory 명시 | 노출 금지 |
| 출력 구조 | `core_patterns` dict + `additional_patterns` array | 단일 `patterns` array |
| Few-shot | 없음 | 없음 |
| 목적 | 일관된 6개 패턴 추출 | 자연스러운 패턴 발견 |
