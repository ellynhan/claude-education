# Design: Phase 3 — 클래스 레벨 리팩토링 (`refactor/class-level`)

## 1. 목표

전략 패턴(Strategy Pattern)과 레지스트리를 도입하여 OCP(Open/Closed Principle)를 준수한다.  
새로운 아이템 타입(예: Conjured)을 추가할 때 **기존 클래스를 수정하지 않고** 새 클래스를 등록하는 것만으로 동작하는 구조를 만든다.

---

## 2. 설계 원칙

| 원칙 | 적용 내용 |
|------|-----------|
| OCP (Open/Closed) | 새 아이템 → 새 Updater 클래스 작성 + `register()` 호출만. 기존 코드 수정 없음 |
| SRP (Single Responsibility) | 각 Updater는 단 하나의 아이템 타입 로직만 담당 |
| DI (Dependency Injection) | `GildedRose`는 `registry`를 생성자에서 주입받아 테스트 용이성 확보 |
| 고블린 규칙 | `Item` 클래스, `GildedRose.items` 속성 변경 금지 |

---

## 3. 전체 클래스 구조

```
gilded_rose.py
  │
  ├── Item                          (변경 불가)
  │
  ├── ItemUpdater          [ABC]    (Phase 3-1)
  │   ├── update(item)     [abstract]
  │   ├── _increase_quality(item, amount)
  │   └── _decrease_quality(item, amount)
  │
  ├── NormalItemUpdater             (Phase 3-2)
  ├── AgedBrieUpdater               (Phase 3-2)
  ├── SulfurasUpdater               (Phase 3-2)
  ├── BackstagePassUpdater          (Phase 3-2)
  ├── ConjuredItemUpdater           (Phase 3-5)  ← OCP 검증
  │
  ├── ItemUpdaterRegistry           (Phase 3-3)
  │   ├── register(name, updater)
  │   └── get_updater(name) → ItemUpdater
  │
  ├── _default_registry             (모듈 레벨 싱글턴)
  │
  └── GildedRose                    (Phase 3-4)
        ├── __init__(items, registry=None)
        └── update_quality()
```

---

## 4. Phase 3-1: `ItemUpdater` ABC

### 4.1 역할

- 모든 Updater의 공통 인터페이스를 강제한다.
- quality 조작 유틸리티(`_increase_quality`, `_decrease_quality`)를 상속으로 제공하여 각 구체 클래스에서 중복 구현하지 않도록 한다.

### 4.2 코드

```python
from abc import ABC, abstractmethod

class ItemUpdater(ABC):
    MAX_QUALITY = 50
    MIN_QUALITY = 0

    @abstractmethod
    def update(self, item: "Item") -> None:
        ...

    def _increase_quality(self, item: "Item", amount: int = 1) -> None:
        item.quality = min(item.quality + amount, self.MAX_QUALITY)

    def _decrease_quality(self, item: "Item", amount: int = 1) -> None:
        item.quality = max(item.quality - amount, self.MIN_QUALITY)
```

> `ABC`와 `abstractmethod`는 Python 표준 라이브러리 `abc` 모듈에서 제공.  
> 추가 의존성 없음.

---

## 5. Phase 3-2: 구체 Updater 클래스

### 5.1 NormalItemUpdater

**비즈니스 규칙**: 매일 quality −1, sell_in < 0 이후 −2 누적 (−1 다시 적용)

```python
class NormalItemUpdater(ItemUpdater):
    def update(self, item: "Item") -> None:
        self._decrease_quality(item)
        item.sell_in -= 1
        if item.sell_in < 0:
            self._decrease_quality(item)
```

| 시나리오 | sell_in 초기 | quality 초기 | quality 결과 |
|----------|-------------|-------------|-------------|
| 일반 감소 | 5 | 10 | 9 |
| 기한 직후 | 0 | 10 | 8 |
| 이미 기한 경과 | −1 | 10 | 8 |
| quality 0 바닥 | 5 | 0 | 0 |

---

### 5.2 AgedBrieUpdater

**비즈니스 규칙**: 매일 quality +1, sell_in < 0 이후 +2 누적

```python
class AgedBrieUpdater(ItemUpdater):
    def update(self, item: "Item") -> None:
        self._increase_quality(item)
        item.sell_in -= 1
        if item.sell_in < 0:
            self._increase_quality(item)
```

| 시나리오 | sell_in 초기 | quality 초기 | quality 결과 |
|----------|-------------|-------------|-------------|
| 일반 증가 | 5 | 20 | 21 |
| 기한 직후 | 0 | 20 | 22 |
| quality 50 상한 | 5 | 50 | 50 |
| 기한 후 상한 근접 | 0 | 49 | 50 (두 번째 +1이 상한 초과 차단) |

---

### 5.3 SulfurasUpdater

**비즈니스 규칙**: sell_in, quality 모두 불변

```python
class SulfurasUpdater(ItemUpdater):
    def update(self, item: "Item") -> None:
        pass
```

> No-op. Sulfuras는 전설 아이템이므로 아무것도 변경하지 않는다.

---

### 5.4 BackstagePassUpdater

**비즈니스 규칙**:
- sell_in > 10: +1
- 5 < sell_in ≤ 10: +2
- sell_in ≤ 5: +3
- 콘서트 종료(sell_in < 0 after 감소): quality = 0

```python
class BackstagePassUpdater(ItemUpdater):
    def update(self, item: "Item") -> None:
        if item.sell_in > 10:
            self._increase_quality(item, 1)
        elif item.sell_in > 5:
            self._increase_quality(item, 2)
        else:
            self._increase_quality(item, 3)

        item.sell_in -= 1

        if item.sell_in < 0:
            item.quality = self.MIN_QUALITY
```

> sell_in 감소 전에 증가량을 결정하고, 감소 후에 콘서트 종료 여부를 확인한다.  
> `item.quality = self.MIN_QUALITY`는 `_decrease_quality`를 쓰지 않는다 — 품질이 얼마든 0으로 강제 설정해야 하기 때문.

| 시나리오 | sell_in 초기 | quality 초기 | quality 결과 |
|----------|-------------|-------------|-------------|
| 먼 미래 | 15 | 20 | 21 |
| 10일 경계 | 10 | 20 | 22 |
| 6일 | 6 | 20 | 22 |
| 5일 경계 | 5 | 20 | 23 |
| 1일 | 1 | 20 | 23 |
| 당일(sell_in=0) | 0 | 20 | 0 |
| 이미 경과 | −1 | 20 | 0 |
| quality 상한 | 5 | 49 | 50 |

---

### 5.5 ConjuredItemUpdater (Phase 3-5)

**비즈니스 규칙**: 일반 아이템의 2배 속도로 quality 감소 (매일 −2, 기한 후 −4 누적)

```python
class ConjuredItemUpdater(ItemUpdater):
    def update(self, item: "Item") -> None:
        self._decrease_quality(item, 2)
        item.sell_in -= 1
        if item.sell_in < 0:
            self._decrease_quality(item, 2)
```

| 시나리오 | sell_in 초기 | quality 초기 | quality 결과 |
|----------|-------------|-------------|-------------|
| 일반 감소 | 5 | 10 | 8 |
| 기한 직후 | 0 | 10 | 6 |
| quality 바닥 | 5 | 1 | 0 (하한 보정) |
| 기한 후 바닥 | 0 | 3 | 0 (−2 → 1, −2 → 0 하한 보정) |

---

## 6. Phase 3-3: `ItemUpdaterRegistry`

### 6.1 역할

- 아이템 이름(문자열) → `ItemUpdater` 인스턴스 매핑을 관리한다.
- 미등록 아이템은 `NormalItemUpdater`로 fallback한다.
- `register()`로 런타임에 새 타입을 등록할 수 있어 OCP를 구현 레벨에서 보장한다.

### 6.2 코드

```python
class ItemUpdaterRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, ItemUpdater] = {}
        self._default: ItemUpdater = NormalItemUpdater()

    def register(self, name: str, updater: ItemUpdater) -> None:
        self._registry[name] = updater

    def get_updater(self, name: str) -> ItemUpdater:
        return self._registry.get(name, self._default)
```

### 6.3 모듈 레벨 기본 레지스트리

```python
_default_registry = ItemUpdaterRegistry()
_default_registry.register("Aged Brie",                               AgedBrieUpdater())
_default_registry.register("Sulfuras, Hand of Ragnaros",              SulfurasUpdater())
_default_registry.register("Backstage passes to a TAFKAL80ETC concert", BackstagePassUpdater())

# Phase 3-5에서 아래 한 줄 추가 (기존 코드 수정 없음)
# _default_registry.register("Conjured Mana Cake", ConjuredItemUpdater())
```

---

## 7. Phase 3-4: `GildedRose` 리팩토링

### 7.1 변경 사항

- 생성자에 `registry` 매개변수 추가 (기본값: `_default_registry`)
- `update_quality()`를 레지스트리 위임 구조로 교체

### 7.2 코드

```python
class GildedRose:
    def __init__(self, items, registry: ItemUpdaterRegistry = None) -> None:
        self.items = items
        self._registry = registry if registry is not None else _default_registry

    def update_quality(self) -> None:
        for item in self.items:
            updater = self._registry.get_updater(item.name)
            updater.update(item)
```

> `registry or _default_registry` 대신 `if registry is not None` 사용.  
> 빈 `ItemUpdaterRegistry()`가 falsy가 아니므로 문제는 없지만, 의도를 명확히 한다.

---

## 8. Phase 3-5: OCP 검증

### 8.1 검증 방법

1. `ConjuredItemUpdater` 클래스 작성
2. `_default_registry.register("Conjured Mana Cake", ConjuredItemUpdater())` 추가
3. 기존 `GildedRose`, `NormalItemUpdater`, `AgedBrieUpdater`, `SulfurasUpdater`, `BackstagePassUpdater` 코드 **수정 없음** 확인

### 8.2 OCP 준수 매트릭스

| 시나리오 | `GildedRose` 수정? | 기존 Updater 수정? | 필요 작업 |
|----------|-------------------|-------------------|-----------|
| Conjured 추가 | ❌ | ❌ | `ConjuredItemUpdater` 작성 + `register()` |
| 임의 신규 아이템 추가 | ❌ | ❌ | 새 Updater 작성 + `register()` |
| 기존 아이템 로직 변경 | ❌ | 해당 Updater만 | 해당 클래스 내부 수정 |

---

## 9. Phase 3-6: 추가 테스트 설계

Phase 1의 테스트는 그대로 통과해야 한다. 아래 테스트를 추가한다.

### 9.1 `TestConjuredItem`

```python
class TestConjuredItem:
    NAME = "Conjured Mana Cake"

    def _run(self, sell_in, quality, times=1):
        gr, item = _make_gilded_rose(self.NAME, sell_in, quality)
        for _ in range(times):
            gr.update_quality()
        return item

    def test_quality_decreases_by_two(self):
        item = self._run(sell_in=5, quality=10)
        assert item.quality == 8

    def test_quality_decreases_by_four_after_sell_by(self):
        item = self._run(sell_in=0, quality=10)
        assert item.quality == 6

    def test_quality_never_negative(self):
        item = self._run(sell_in=5, quality=1)
        assert item.quality == 0

    def test_quality_never_negative_after_sell_by(self):
        item = self._run(sell_in=0, quality=3)
        assert item.quality == 0

    def test_sell_in_decreases(self):
        item = self._run(sell_in=5, quality=10)
        assert item.sell_in == 4
```

### 9.2 `TestItemUpdaterRegistry`

```python
class TestItemUpdaterRegistry:
    def test_returns_normal_updater_for_unknown_item(self):
        registry = ItemUpdaterRegistry()
        updater = registry.get_updater("unknown item")
        assert isinstance(updater, NormalItemUpdater)

    def test_returns_registered_updater(self):
        registry = ItemUpdaterRegistry()
        custom = AgedBrieUpdater()
        registry.register("Test Item", custom)
        assert registry.get_updater("Test Item") is custom

    def test_registered_updater_overrides_default(self):
        registry = ItemUpdaterRegistry()
        registry.register("special", SulfurasUpdater())
        items = [Item("special", 5, 10)]
        gr = GildedRose(items, registry=registry)
        gr.update_quality()
        assert items[0].sell_in == 5   # Sulfuras updater: no-op
        assert items[0].quality == 10
```

### 9.3 `TestGildedRoseWithCustomRegistry`

```python
class TestGildedRoseWithCustomRegistry:
    def test_custom_registry_is_used(self):
        registry = ItemUpdaterRegistry()
        registry.register("Aged Brie", NormalItemUpdater())  # Aged Brie를 일반 취급
        items = [Item("Aged Brie", 5, 20)]
        gr = GildedRose(items, registry=registry)
        gr.update_quality()
        assert items[0].quality == 19  # 증가가 아닌 감소

    def test_default_registry_used_when_none_passed(self):
        items = [Item("Aged Brie", 5, 20)]
        gr = GildedRose(items)
        gr.update_quality()
        assert items[0].quality == 21  # 기본 동작: 증가
```

---

## 10. 완료 기준 체크리스트

- [ ] Phase 1 테스트 전체 통과 유지
- [ ] Phase 3 추가 테스트 전체 통과
- [ ] `gilded_rose.py` 커버리지 100% 유지
- [ ] `GildedRose`, 기존 4개 Updater 수정 없이 Conjured 동작 확인
- [ ] `Item` 클래스 및 `GildedRose.items` 속성 미변경 확인

---

## 11. 최종 파일 구조 (`gilded_rose.py`)

```python
from abc import ABC, abstractmethod


# ── Updater 추상 기반 ──────────────────────────────
class ItemUpdater(ABC):
    MAX_QUALITY = 50
    MIN_QUALITY = 0
    @abstractmethod
    def update(self, item) -> None: ...
    def _increase_quality(self, item, amount=1) -> None: ...
    def _decrease_quality(self, item, amount=1) -> None: ...


# ── 구체 Updater ───────────────────────────────────
class NormalItemUpdater(ItemUpdater):     ...
class AgedBrieUpdater(ItemUpdater):       ...
class SulfurasUpdater(ItemUpdater):       ...
class BackstagePassUpdater(ItemUpdater):  ...
class ConjuredItemUpdater(ItemUpdater):   ...  # Phase 3-5


# ── 레지스트리 ─────────────────────────────────────
class ItemUpdaterRegistry:
    def register(self, name, updater) -> None: ...
    def get_updater(self, name) -> ItemUpdater: ...

_default_registry = ItemUpdaterRegistry()
_default_registry.register("Aged Brie",                                AgedBrieUpdater())
_default_registry.register("Sulfuras, Hand of Ragnaros",               SulfurasUpdater())
_default_registry.register("Backstage passes to a TAFKAL80ETC concert", BackstagePassUpdater())
_default_registry.register("Conjured Mana Cake",                        ConjuredItemUpdater())


# ── GildedRose (공개 인터페이스 유지) ────────────────
class GildedRose:
    def __init__(self, items, registry=None): ...
    def update_quality(self) -> None: ...


# ── Item (변경 불가) ───────────────────────────────
class Item:
    def __init__(self, name, sell_in, quality): ...
    def __repr__(self): ...
```
