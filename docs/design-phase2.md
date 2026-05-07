# Design: Phase 2 — 메서드 레벨 리팩토링 (`refactor/method-level`)

## 1. 목표

`GildedRose.update_quality()` 내부의 가독성을 개선한다.  
공개 인터페이스와 `Item` 클래스는 변경하지 않으며, Phase 1 테스트가 전부 통과하는 상태를 항상 유지한다.

---

## 2. 현재 코드 분석

```python
# gilded_rose.py (현재, 29줄)
def update_quality(self):
    for item in self.items:
        if item.name != "Aged Brie" and item.name != "Backstage passes to a TAFKAL80ETC concert":
            if item.quality > 0:
                if item.name != "Sulfuras, Hand of Ragnaros":
                    item.quality = item.quality - 1        # depth 3
        else:
            if item.quality < 50:
                item.quality = item.quality + 1            # depth 2
                if item.name == "Backstage passes to a TAFKAL80ETC concert":
                    if item.sell_in < 11:
                        if item.quality < 50:
                            item.quality = item.quality + 1  # depth 4
                    if item.sell_in < 6:
                        if item.quality < 50:
                            item.quality = item.quality + 1  # depth 4
        if item.name != "Sulfuras, Hand of Ragnaros":
            item.sell_in = item.sell_in - 1
        if item.sell_in < 0:
            if item.name != "Aged Brie":
                if item.name != "Backstage passes to a TAFKAL80ETC concert":
                    if item.quality > 0:
                        if item.name != "Sulfuras, Hand of Ragnaros":
                            item.quality = item.quality - 1  # depth 5
                else:
                    item.quality = item.quality - item.quality
            else:
                if item.quality < 50:
                    item.quality = item.quality + 1        # depth 3
```

### 문제점 요약

| 문제 | 현황 |
|------|------|
| 최대 중첩 depth | 5단계 |
| 매직 스트링 | 아이템명 3종이 코드 내 총 7회 분산 등장 |
| 매직 넘버 | `0`, `50`, `11`, `6` — 의미 불명 |
| 메서드 역할 | sell_in 감소 + quality 증가/감소 + 상한/하한 보정이 한 메서드에 혼재 |
| sell_in 처리 시점 | 상단(quality 계산)과 하단(sell_in 경과 후 quality 재계산)이 분리되어 흐름 추적 어려움 |

---

## 3. Phase 2-1: 상수 추출

`GildedRose` 클래스 외부(모듈 최상단)에 상수를 정의한다.

```python
# gilded_rose.py 상단에 추가
_AGED_BRIE       = "Aged Brie"
_SULFURAS        = "Sulfuras, Hand of Ragnaros"
_BACKSTAGE_PASSES = "Backstage passes to a TAFKAL80ETC concert"

_MAX_QUALITY = 50
_MIN_QUALITY = 0
```

> 접두사 `_`는 모듈 내부 상수임을 나타낸다.  
> `Item`과 `GildedRose`는 변경 불가 제약이 있으므로 클래스 밖에 둔다.

**작업 후 검증**: `pytest` → 전체 통과 확인

---

## 4. Phase 2-2: 헬퍼 메서드 추출

`GildedRose` 클래스에 `_` 접두사 메서드를 추가한다. 기존 `update_quality()`는 아직 변경하지 않는다.

### 4.1 타입 판별 헬퍼

```python
def _is_sulfuras(self, item) -> bool:
    return item.name == _SULFURAS

def _is_aged_brie(self, item) -> bool:
    return item.name == _AGED_BRIE

def _is_backstage_pass(self, item) -> bool:
    return item.name == _BACKSTAGE_PASSES
```

### 4.2 Quality 조작 헬퍼

상한·하한 보정을 한 곳에서 처리한다.

```python
def _increase_quality(self, item, amount: int = 1) -> None:
    item.quality = min(item.quality + amount, _MAX_QUALITY)

def _decrease_quality(self, item, amount: int = 1) -> None:
    item.quality = max(item.quality - amount, _MIN_QUALITY)
```

### 4.3 아이템별 업데이트 헬퍼

각 헬퍼는 sell_in 감소까지 포함하여 해당 아이템의 하루치 로직을 완결한다.

```python
def _update_normal_item(self, item) -> None:
    self._decrease_quality(item)
    item.sell_in -= 1
    if item.sell_in < 0:
        self._decrease_quality(item)

def _update_aged_brie(self, item) -> None:
    self._increase_quality(item)
    item.sell_in -= 1
    if item.sell_in < 0:
        self._increase_quality(item)

def _update_backstage_pass(self, item) -> None:
    if item.sell_in > 10:
        self._increase_quality(item, 1)
    elif item.sell_in > 5:
        self._increase_quality(item, 2)
    else:
        self._increase_quality(item, 3)
    item.sell_in -= 1
    if item.sell_in < 0:
        item.quality = _MIN_QUALITY
```

> **Backstage pass 경계 정확도**:
> - sell_in=11 호출 전 → 11 > 10 이므로 +1
> - sell_in=10 호출 전 → 10 ≤ 10, 10 > 5 이므로 +2
> - sell_in=6 호출 전 →  6 ≤ 10, 6 > 5 이므로 +2
> - sell_in=5 호출 전 →  5 ≤ 5 이므로 +3
> - sell_in=0 호출 전 →  0 ≤ 5 이므로 +3, 이후 sell_in=−1 → quality=0

**작업 후 검증**: `pytest` → 전체 통과 확인 (헬퍼만 추가한 시점이므로 아직 기존 로직 유지)

---

## 5. Phase 2-3: `update_quality()` 평탄화

헬퍼 메서드가 준비된 상태에서 `update_quality()`를 교체한다.

### 리팩토링 후 전체 모습

```python
def update_quality(self) -> None:
    for item in self.items:
        if self._is_sulfuras(item):
            continue
        if self._is_aged_brie(item):
            self._update_aged_brie(item)
        elif self._is_backstage_pass(item):
            self._update_backstage_pass(item)
        else:
            self._update_normal_item(item)
```

> sell_in 감소는 각 헬퍼 내부로 이동했으므로 여기서는 처리하지 않는다.  
> Sulfuras는 `continue`로 즉시 skip — 아무것도 변경되지 않는다.

### Before / After 비교

| 지표 | Before | After |
|------|--------|-------|
| 최대 중첩 depth | 5 | 2 (`_update_backstage_pass` 내부 기준) |
| `update_quality()` 길이 | 29줄 | 8줄 |
| 아이템명 문자열 등장 횟수 | 7회 | 0회 (상수 + 헬퍼로 이동) |
| 매직 넘버 | 5개 | 0개 |

---

## 6. Phase 2-4: 테스트 통과 검증

### 6.1 실행 명령

```bash
pytest
```

### 6.2 확인 항목

| 항목 | 기준 |
|------|------|
| Phase 1 전체 테스트 | 모두 PASSED |
| `gilded_rose.py` 커버리지 | 100% 유지 |
| `update_quality()` depth | `_update_backstage_pass` 내부 최대 depth = 2 |

### 6.3 완료 기준 체크리스트

- [ ] `pytest` 실행 시 모든 Phase 1 테스트 통과
- [ ] 커버리지 100% 유지
- [ ] `update_quality()` 본문 8줄 이하
- [ ] `Item` 클래스 및 `GildedRose.items` 미변경 확인

---

## 7. 최종 파일 구조 (`gilded_rose.py`)

```python
# 모듈 상수
_AGED_BRIE        = "Aged Brie"
_SULFURAS         = "Sulfuras, Hand of Ragnaros"
_BACKSTAGE_PASSES = "Backstage passes to a TAFKAL80ETC concert"
_MAX_QUALITY = 50
_MIN_QUALITY = 0


class GildedRose:
    def __init__(self, items):
        self.items = items

    # --- 공개 인터페이스 ---
    def update_quality(self) -> None: ...        # 8줄

    # --- 타입 판별 헬퍼 ---
    def _is_sulfuras(self, item) -> bool: ...
    def _is_aged_brie(self, item) -> bool: ...
    def _is_backstage_pass(self, item) -> bool: ...

    # --- Quality 조작 헬퍼 ---
    def _increase_quality(self, item, amount=1) -> None: ...
    def _decrease_quality(self, item, amount=1) -> None: ...

    # --- 아이템별 업데이트 헬퍼 ---
    def _update_normal_item(self, item) -> None: ...
    def _update_aged_brie(self, item) -> None: ...
    def _update_backstage_pass(self, item) -> None: ...


class Item:                   # 변경 없음 (고블린 규칙)
    ...
```
