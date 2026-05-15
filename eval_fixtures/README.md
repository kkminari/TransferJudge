# Evaluation Fixtures (FROZEN)

생성 시점: 2026-05-15 15:56:07
SEED: 42 (sample_candidates)

## 파일 구조
- `test_users.json` — 평가 대상 user_id 100개 (frozen)
- `gt.json` — user_id → gt_id 매핑 (frozen)
- `candidates/user_<id>.json` — 사용자별 50권 후보 (frozen)

## 사용 방법
모든 baseline / model 평가는 이 fixture를 사용해야 함:
```python
import json
from pathlib import Path
FIXTURE = Path("eval_fixtures")
users = json.load(open(FIXTURE / "test_users.json"))
gt_map = json.load(open(FIXTURE / "gt.json"))
for uid in users:
    candidates = json.load(open(FIXTURE / f"candidates/user_{uid}.json"))
    gt_id = gt_map[uid]["gt_id"]
    # ... model 추론 ...
```

## 통계
- 평가 대상: 100 명
- GT 없는 사용자 (skip): 0 명
- 사용자별 후보: 50권 (GT 1 + Negative 49, shuffle)

## 주의
**절대 이 파일들을 수정하지 말 것.**
모델·baseline 비교의 공정성은 이 fixture가 frozen 상태일 때만 보장됨.
