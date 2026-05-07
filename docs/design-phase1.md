# Design: Phase 1 — unittest 생성 (`feat/unittest`)

## 1. 목표

`README.md` 스펙을 유일한 기준으로 삼아 단위 테스트를 작성한다.  
프로덕션 코드(`gilded_rose.py`)는 이 Phase에서 **일절 변경하지 않는다.**  
`pytest-cov`로 라인 커버리지 100%를 달성하는 것이 완료 기준이다.

---

## 2. 환경 구성 (Phase 1-1)

### 2.1 pytest.ini 변경

```ini
# 변경 전
[pytest]
pythonpath = .
addopts = -s --cov-report=html

# 변경 후
[pytest]
pythonpath = .
addopts = -s --cov=gilded_rose --cov-report=html --cov-report=term-missing
```

- `--cov=gilded_rose` : 커버리지 측정 대상을 `gilded_rose.py`로 한정
- `--cov-report=term-missing` : 터미널에 미커버 라인 번호 출력
- `--cov-report=html` : `htmlcov/` 에 브라우저용 리포트 생성

### 2.2 기존 stub 테스트 제거

`tests/test_gilded_rose.py`의 `test_foo()`는 의도적으로 실패하도록 작성된 stub이다.  
이를 삭제하고 테스트 클래스 골격으로 교체한다.

```python
import pytest
from gilded_rose import Item, GildedRose

class TestNormalItem:     ...
class TestAgedBrie:       ...
class TestSulfuras:       ...
class TestBackstagePasses: ...
```

---

## 3. 테스트 클래스 구조

```
tests/test_gilded_rose.py
  ├── _make_gilded_rose(name, sell_in, quality)   ← 공통 팩토리 헬퍼
  ├── class TestNormalItem          (Phase 1-2)
  ├── class TestAgedBrie            (Phase 1-3)
  ├── class TestSulfuras            (Phase 1-3)
  └── class TestBackstagePasses     (Phase 1-3, 1-4)
```

### 공통 헬퍼

```python
def _make_gilded_rose(name, sell_in, quality):
    items = [Item(name, sell_in, quality)]
    return GildedRose(items), items[0]
```

`update_quality()` 호출 후 `items[0]`을 바로 단언할 수 있도록 item 참조도 함께 반환한다.

---

## 4. Phase 1-2: 일반 아이템 테스트

아이템명: `"normal item"` (특수 아이템명이 아닌 임의 문자열)

### 테스트 케이스 명세

| # | 메서드명 | 초기 sell_in | 초기 quality | 호출 횟수 | 기대 sell_in | 기대 quality | 검증 규칙 |
|---|----------|-------------|-------------|---------|-------------|-------------|-----------|
| 1 | `test_sell_in_decreases_by_one` | 10 | 20 | 1 | 9 | 19 | 매일 sell_in −1 |
| 2 | `test_quality_decreases_by_one` | 10 | 20 | 1 | 9 | 19 | 매일 quality −1 |
| 3 | `test_quality_decreases_twice_after_sell_by_date` | 0 | 10 | 1 | −1 | 8 | sell_in < 0 이후 quality −2 |
| 4 | `test_quality_is_never_negative` | 5 | 0 | 1 | 4 | 0 | quality 최솟값 0 |
| 5 | `test_quality_is_never_negative_after_sell_by` | 0 | 0 | 1 | −1 | 0 | sell_in 경과 후에도 최솟값 0 |
| 6 | `test_quality_decreases_twice_when_overdue` | −1 | 10 | 1 | −2 | 8 | 이미 sell_in 음수인 경우에도 −2 |

> **경계 주의**: sell_in이 정확히 `0`일 때 `update_quality()` 실행 후 sell_in은 `−1`이 되며, 이 시점부터 quality 2배 감소가 적용된다.  
> 즉, sell_in=0 상태에서 1회 호출하면 quality는 **−2** 적용된다.

### 구현 예시

```python
class TestNormalItem:
    NAME = "normal item"

    def _run(self, sell_in, quality, times=1):
        gr, item = _make_gilded_rose(self.NAME, sell_in, quality)
        for _ in range(times):
            gr.update_quality()
        return item

    def test_sell_in_decreases_by_one(self):
        item = self._run(sell_in=10, quality=20)
        assert item.sell_in == 9

    def test_quality_decreases_by_one(self):
        item = self._run(sell_in=10, quality=20)
        assert item.quality == 19

    def test_quality_decreases_twice_after_sell_by_date(self):
        item = self._run(sell_in=0, quality=10)
        assert item.quality == 8

    def test_quality_is_never_negative(self):
        item = self._run(sell_in=5, quality=0)
        assert item.quality == 0

    def test_quality_is_never_negative_after_sell_by(self):
        item = self._run(sell_in=0, quality=0)
        assert item.quality == 0

    def test_quality_decreases_twice_when_overdue(self):
        item = self._run(sell_in=-1, quality=10)
        assert item.quality == 8
```

---

## 5. Phase 1-3: 특수 아이템 테스트

### 5.1 Aged Brie (`"Aged Brie"`)

| # | 메서드명 | 초기 sell_in | 초기 quality | 호출 횟수 | 기대 quality | 검증 규칙 |
|---|----------|-------------|-------------|---------|-------------|-----------|
| 1 | `test_quality_increases_by_one` | 10 | 20 | 1 | 21 | 시간이 지날수록 quality +1 |
| 2 | `test_quality_increases_twice_after_sell_by` | 0 | 20 | 1 | 22 | sell_in < 0 이후 quality +2 |
| 3 | `test_quality_capped_at_50` | 10 | 50 | 1 | 50 | quality 최댓값 50 |
| 4 | `test_quality_capped_at_50_when_near_max` | 10 | 49 | 1 | 50 | 49 → 50 (상한 정확히 적용) |
| 5 | `test_quality_capped_at_50_after_sell_by` | 0 | 49 | 1 | 50 | sell_in 경과 후에도 50 초과 불가 |
| 6 | `test_sell_in_decreases` | 10 | 20 | 1 | 9 sell_in | — | sell_in은 동일하게 감소 |

> **경계 주의**: sell_in=0, quality=49 → quality 기대값은 50 (1번 증가 후 상한 적용, sell_in 경과 후 +1 더 시도하지만 이미 50이므로 50 유지).  
> sell_in=0, quality=48 → quality 기대값은 50 (+1 → 49, sell_in 감소 후 −1 미만이므로 +1 → 50).

```python
class TestAgedBrie:
    NAME = "Aged Brie"

    def _run(self, sell_in, quality, times=1):
        gr, item = _make_gilded_rose(self.NAME, sell_in, quality)
        for _ in range(times):
            gr.update_quality()
        return item

    def test_quality_increases_by_one(self):
        item = self._run(sell_in=10, quality=20)
        assert item.quality == 21

    def test_quality_increases_twice_after_sell_by(self):
        item = self._run(sell_in=0, quality=20)
        assert item.quality == 22

    def test_quality_capped_at_50(self):
        item = self._run(sell_in=10, quality=50)
        assert item.quality == 50

    def test_quality_capped_at_50_when_near_max(self):
        item = self._run(sell_in=10, quality=49)
        assert item.quality == 50

    def test_quality_capped_at_50_after_sell_by(self):
        item = self._run(sell_in=0, quality=49)
        assert item.quality == 50

    def test_sell_in_decreases(self):
        item = self._run(sell_in=10, quality=20)
        assert item.sell_in == 9
```

---

### 5.2 Sulfuras (`"Sulfuras, Hand of Ragnaros"`)

| # | 메서드명 | 초기 sell_in | 초기 quality | 기대 sell_in | 기대 quality | 검증 규칙 |
|---|----------|-------------|-------------|-------------|-------------|-----------|
| 1 | `test_sell_in_never_changes` | 0 | 80 | 0 | 80 | sell_in 불변 |
| 2 | `test_quality_never_changes` | 0 | 80 | 0 | 80 | quality 80 고정 |
| 3 | `test_never_changes_over_multiple_days` | 5 | 80 | 5 | 80 | 다회 호출에도 불변 |

```python
class TestSulfuras:
    NAME = "Sulfuras, Hand of Ragnaros"

    def _run(self, sell_in=0, quality=80, times=1):
        gr, item = _make_gilded_rose(self.NAME, sell_in, quality)
        for _ in range(times):
            gr.update_quality()
        return item

    def test_sell_in_never_changes(self):
        item = self._run(sell_in=0)
        assert item.sell_in == 0

    def test_quality_never_changes(self):
        item = self._run(quality=80)
        assert item.quality == 80

    def test_never_changes_over_multiple_days(self):
        item = self._run(sell_in=5, quality=80, times=10)
        assert item.sell_in == 5
        assert item.quality == 80
```

---

### 5.3 Backstage passes (`"Backstage passes to a TAFKAL80ETC concert"`)

| # | 메서드명 | 초기 sell_in | 초기 quality | 기대 quality | 검증 규칙 |
|---|----------|-------------|-------------|-------------|-----------|
| 1 | `test_quality_increases_by_one_far_from_concert` | 15 | 20 | 21 | sell_in > 10: +1 |
| 2 | `test_quality_increases_by_two_at_ten_days` | 10 | 20 | 22 | sell_in = 10 (≤10): +2 |
| 3 | `test_quality_increases_by_two_between_6_and_10` | 8 | 20 | 22 | sell_in = 8 (≤10): +2 |
| 4 | `test_quality_increases_by_three_at_five_days` | 5 | 20 | 23 | sell_in = 5 (≤5): +3 |
| 5 | `test_quality_increases_by_three_between_1_and_5` | 3 | 20 | 23 | sell_in = 3 (≤5): +3 |
| 6 | `test_quality_drops_to_zero_after_concert` | 0 | 20 | 0 | sell_in = 0: 호출 후 quality = 0 |
| 7 | `test_quality_is_zero_when_already_past` | −1 | 20 | 0 | sell_in 이미 음수: quality = 0 |
| 8 | `test_quality_capped_at_50` | 5 | 49 | 50 | quality 최댓값 50 |

> **경계 주의**:
> - sell_in=11 → +1 (> 10)
> - sell_in=10 → +2 (≤ 10, > 5)
> - sell_in=6  → +2 (≤ 10, > 5)
> - sell_in=5  → +3 (≤ 5)
> - sell_in=1  → +3 (≤ 5)
> - sell_in=0  → 호출 직후 sell_in = −1, quality = 0

```python
class TestBackstagePasses:
    NAME = "Backstage passes to a TAFKAL80ETC concert"

    def _run(self, sell_in, quality, times=1):
        gr, item = _make_gilded_rose(self.NAME, sell_in, quality)
        for _ in range(times):
            gr.update_quality()
        return item

    def test_quality_increases_by_one_far_from_concert(self):
        item = self._run(sell_in=15, quality=20)
        assert item.quality == 21

    def test_quality_increases_by_two_at_ten_days(self):
        item = self._run(sell_in=10, quality=20)
        assert item.quality == 22

    def test_quality_increases_by_two_between_6_and_10(self):
        item = self._run(sell_in=8, quality=20)
        assert item.quality == 22

    def test_quality_increases_by_three_at_five_days(self):
        item = self._run(sell_in=5, quality=20)
        assert item.quality == 23

    def test_quality_increases_by_three_between_1_and_5(self):
        item = self._run(sell_in=3, quality=20)
        assert item.quality == 23

    def test_quality_drops_to_zero_after_concert(self):
        item = self._run(sell_in=0, quality=20)
        assert item.quality == 0

    def test_quality_is_zero_when_already_past(self):
        item = self._run(sell_in=-1, quality=20)
        assert item.quality == 0

    def test_quality_capped_at_50(self):
        item = self._run(sell_in=5, quality=49)
        assert item.quality == 50
```

---

## 6. Phase 1-4: 경계값 보강 & 커버리지 100%

### 6.1 커버리지 측정 방법

```bash
pytest
# 터미널 출력에서 Stmts / Miss / Cover 확인
# htmlcov/index.html 에서 라인별 커버리지 확인
```

### 6.2 미커버 라인 대응 전략

| 현재 코드 라인 | 대응 테스트 |
|---------------|-------------|
| `item.quality = item.quality - item.quality` (line 30) | `test_quality_drops_to_zero_after_concert` 로 커버 |
| sell_in < 0 분기 전체 | 각 아이템의 `_after_sell_by` 테스트로 커버 |
| quality > 0 가드 (line 8, 26) | quality=0 케이스 (`test_quality_is_never_negative*`) 로 커버 |

### 6.3 완료 기준 체크리스트

- [ ] `pytest` 실행 시 모든 테스트 통과 (PASSED only)
- [ ] `gilded_rose.py` 커버리지 **100%** (`term-missing` 출력에서 `Miss = 0` 확인)
- [ ] `htmlcov/` 리포트 갱신 확인
- [ ] 프로덕션 코드 변경 없음 (`gilded_rose.py` diff 없음)
