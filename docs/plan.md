# Gilded Rose 리팩토링 계획

## 개요

Gilded Rose kata를 3단계 브랜치로 나누어 점진적으로 리팩토링한다.  
영향이 작은 변경(테스트 추가)부터 시작하여 점차 큰 구조적 변경으로 진행한다.

---

## 브랜치 전략

```
main
 ├── feat/unittest              ← 테스트 작성 (코드 변경 없음)
 ├── refactor/method-level      ← feat/unittest 기반, 메서드 수준 리팩토링
 └── refactor/class-level       ← refactor/method-level 기반, 클래스 구조 리팩토링
```

각 브랜치는 이전 브랜치를 기반으로 하며, 테스트가 항상 통과하는 상태를 유지한다.

---

## Phase 전체 흐름

```
Phase 1 (feat/unittest)
  └─ Phase 1-1: 테스트 환경 구성
  └─ Phase 1-2: 일반 아이템 테스트
  └─ Phase 1-3: 특수 아이템 테스트
  └─ Phase 1-4: 경계값 테스트 & 커버리지 확인

Phase 2 (refactor/method-level)
  └─ Phase 2-1: 상수 추출
  └─ Phase 2-2: 헬퍼 메서드 추출
  └─ Phase 2-3: update_quality() 평탄화
  └─ Phase 2-4: 테스트 통과 검증

Phase 3 (refactor/class-level)
  └─ Phase 3-1: ItemUpdater ABC 정의
  └─ Phase 3-2: 구체 Updater 클래스 작성
  └─ Phase 3-3: ItemUpdaterRegistry 구현
  └─ Phase 3-4: GildedRose 리팩토링
  └─ Phase 3-5: ConjuredItemUpdater 추가 (OCP 검증)
  └─ Phase 3-6: 전체 테스트 통과 검증
```

---

## Branch 1: unittest 생성

### 목표
- `README.md` 스펙을 기반으로 모든 아이템 타입에 대한 단위 테스트 작성
- `pytest-cov`로 커버리지 측정 및 리포트 생성

### 테스트 대상 아이템 타입
| 아이템 | 비고 |
|--------|------|
| 일반 아이템 (Normal) | 기본 동작 |
| Aged Brie | 시간이 지날수록 품질 증가 |
| Sulfuras, Hand of Ragnaros | 전설 아이템, 불변 |
| Backstage passes to a TAFKAL80ETC concert | 기간에 따라 품질 차등 증가 |

### 테스트 케이스 목록

#### 일반 아이템
- [ ] 하루가 지나면 SellIn 1 감소
- [ ] 하루가 지나면 Quality 1 감소
- [ ] SellIn 0 이후 Quality 2배 감소 (매일 2씩)
- [ ] Quality는 0 미만이 되지 않음 (SellIn 양수 / 음수 시)
- [ ] Quality는 50 초과하지 않음

#### Aged Brie
- [ ] 하루가 지나면 Quality 1 증가
- [ ] SellIn 0 이후 Quality 2씩 증가
- [ ] Quality는 50 초과하지 않음

#### Sulfuras
- [ ] SellIn 값이 변하지 않음
- [ ] Quality 값(80)이 변하지 않음

#### Backstage passes
- [ ] SellIn > 10 이면 Quality 1 증가
- [ ] SellIn 10 이하이면 Quality 2 증가
- [ ] SellIn 5 이하이면 Quality 3 증가
- [ ] SellIn 0 이하(콘서트 종료 후) Quality = 0
- [ ] Quality는 50 초과하지 않음

### 커버리지 설정
- `pytest-cov` 사용
- `--cov=gilded_rose --cov-report=html --cov-report=term` 옵션 적용
- `pytest.ini`에 addopts 업데이트

### 완료 기준
- 모든 스펙 케이스에 대해 테스트 작성 완료
- `gilded_rose.py` 라인 커버리지 100% 달성
- 모든 테스트 통과

---

## Branch 2: 메서드 레벨 리팩토링

### 목표
- `update_quality()` 메서드의 가독성 개선
- 중첩된 if문 평탄화, 의도를 드러내는 변수명 사용
- Branch 1 테스트가 모두 통과하는 것을 확인하며 진행

### 제약
- `Item` 클래스 변경 금지 (고블린 규칙)
- `GildedRose.items` 속성 변경 금지
- 공개 인터페이스(`update_quality()`) 시그니처 유지

### 리팩토링 방향

#### 현재 코드 문제점
1. 중첩 if문이 4~5 depth로 깊어 흐름 파악 어려움
2. 같은 아이템 이름 문자열이 여러 곳에 분산
3. 단일 메서드에 모든 로직이 집중 (SRP 위반)
4. 매직 넘버(0, 50, 80, 11, 6)가 설명 없이 등장

#### 개선 사항
1. **조기 반환(early return)** 패턴으로 중첩 depth 감소
2. **아이템 이름 상수화**: `AGED_BRIE`, `SULFURAS`, `BACKSTAGE_PASSES` 등
3. **가드 클로즈(guard clause)**: 각 아이템 처리 조건을 명확한 조건절로 분리
4. **헬퍼 메서드 추출**:
   - `_is_sulfuras(item)` → Sulfuras 여부 확인
   - `_is_aged_brie(item)` → Aged Brie 여부 확인
   - `_is_backstage_pass(item)` → Backstage pass 여부 확인
   - `_clamp_quality(item)` → Quality 범위 보정 (0~50)
   - `_update_sell_in(item)` → SellIn 감소
   - `_update_quality_for(item)` → 아이템별 Quality 업데이트

### 완료 기준
- Branch 1 테스트 전체 통과
- 커버리지 유지 (100%)
- `update_quality()` 메서드 내 최대 중첩 depth ≤ 2

---

## Branch 3: 클래스 레벨 리팩토링

### 목표
- OCP(Open/Closed Principle) 준수: 새 아이템 타입 추가 시 기존 코드 수정 없이 확장 가능
- Conjured 아이템이 추가되더라도 기존 코드 미수정으로 지원 가능한 구조

### 제약
- `Item` 클래스 변경 금지
- `GildedRose.items` 속성 변경 금지
- `GildedRose.update_quality()` 공개 인터페이스 유지

### 설계 방향: 전략 패턴(Strategy Pattern) + 레지스트리

```
GildedRose
  └── update_quality()
        └── ItemUpdaterRegistry.get_updater(item.name)
              └── updater.update(item)

ItemUpdater (Abstract Base)
  ├── NormalItemUpdater
  ├── AgedBrieUpdater
  ├── SulfurasUpdater
  ├── BackstagePassUpdater
  └── ConjuredItemUpdater  ← 나중에 추가 (OCP)

ItemUpdaterRegistry
  - 이름 → Updater 매핑 관리
  - register(name, updater) 로 동적 등록 가능
  - 미등록 아이템은 NormalItemUpdater 사용
```

### Conjured 아이템 추가 예시 (OCP 검증)
```python
# 기존 코드 수정 없이 아래만 추가하면 됨
class ConjuredItemUpdater(ItemUpdater):
    def update(self, item):
        ...

registry.register("Conjured Mana Cake", ConjuredItemUpdater())
```

### 완료 기준
- Branch 2 테스트 전체 통과
- 커버리지 유지 (100%)
- 새 아이템 타입 추가 시 `GildedRose` 또는 `ItemUpdater` 구현체 수정 불필요
- `Conjured` 아이템 updater 클래스 작성 및 테스트 추가

---

## 진행 순서 요약

| 순서 | 브랜치 | 주요 작업 | 코드 영향도 |
|------|--------|-----------|-------------|
| 1 | `feat/unittest` | 테스트 작성, 커버리지 설정 | 낮음 (테스트만) |
| 2 | `refactor/method-level` | 메서드 내부 리팩토링 | 중간 (내부 로직) |
| 3 | `refactor/class-level` | 전략 패턴 도입, OCP 구조화 | 높음 (구조 변경) |

---

## Phase 상세

### Phase 1-1: 테스트 환경 구성 (`feat/unittest`)

**목적**: pytest-cov 세팅 및 커버리지 측정 기반 마련

| 작업 | 대상 파일 | 내용 |
|------|-----------|------|
| pytest-cov 옵션 추가 | `pytest.ini` | `--cov=gilded_rose --cov-report=html --cov-report=term-missing` |
| 기존 stub 테스트 제거 | `tests/test_gilded_rose.py` | `test_foo()` 삭제 후 테스트 클래스 골격 작성 |

완료 기준: `pytest` 실행 시 커버리지 리포트 출력

---

### Phase 1-2: 일반 아이템 테스트 (`feat/unittest`)

**목적**: Normal item 비즈니스 규칙 검증

| 테스트 메서드 | 검증 내용 |
|--------------|-----------|
| `test_sell_in_decreases_by_one` | 하루 경과 시 sell_in −1 |
| `test_quality_decreases_by_one` | 하루 경과 시 quality −1 |
| `test_quality_decreases_twice_after_sell_by` | sell_in < 0 이후 quality −2/day |
| `test_quality_never_negative` | quality 최솟값 0 (sell_in 양수) |
| `test_quality_never_negative_after_sell_by` | quality 최솟값 0 (sell_in 음수) |

완료 기준: 5개 테스트 모두 통과

---

### Phase 1-3: 특수 아이템 테스트 (`feat/unittest`)

**목적**: Aged Brie / Sulfuras / Backstage passes 규칙 검증

**Aged Brie (4개)**

| 테스트 메서드 | 검증 내용 |
|--------------|-----------|
| `test_quality_increases` | 하루 경과 시 quality +1 |
| `test_quality_increases_twice_after_sell_by` | sell_in < 0 이후 quality +2/day |
| `test_quality_capped_at_50` | quality 최댓값 50 유지 |
| `test_quality_capped_at_50_after_sell_by` | sell_in 경과 후에도 50 초과 불가 |

**Sulfuras (2개)**

| 테스트 메서드 | 검증 내용 |
|--------------|-----------|
| `test_sell_in_never_changes` | sell_in 불변 |
| `test_quality_never_changes` | quality 80 고정 |

**Backstage passes (5개)**

| 테스트 메서드 | 검증 내용 |
|--------------|-----------|
| `test_quality_increases_by_one_far_from_concert` | sell_in > 10: +1 |
| `test_quality_increases_by_two_at_10_days` | sell_in ≤ 10: +2 |
| `test_quality_increases_by_three_at_5_days` | sell_in ≤ 5: +3 |
| `test_quality_drops_to_zero_after_concert` | sell_in < 0: quality = 0 |
| `test_quality_capped_at_50` | quality 최댓값 50 |

완료 기준: 11개 테스트 모두 통과

---

### Phase 1-4: 경계값 테스트 & 커버리지 확인 (`feat/unittest`)

**목적**: 분기 경계(sell_in = 0, 5, 10)에서의 동작 보강 및 커버리지 100% 달성

| 작업 | 내용 |
|------|------|
| 경계값 보강 | sell_in = 10, 5, 0 케이스 명시적 테스트 |
| 커버리지 확인 | `gilded_rose.py` 100% 달성 여부 확인, 미커버 라인 추가 테스트 |

완료 기준: `gilded_rose.py` 라인 커버리지 100%

---

### Phase 2-1: 상수 추출 (`refactor/method-level`)

**목적**: 매직 넘버·매직 스트링 제거로 의도 명확화

추출 대상:
```python
AGED_BRIE = "Aged Brie"
SULFURAS = "Sulfuras, Hand of Ragnaros"
BACKSTAGE_PASSES = "Backstage passes to a TAFKAL80ETC concert"
MAX_QUALITY = 50
MIN_QUALITY = 0
```

완료 기준: 상수 정의 후 기존 테스트 전체 통과

---

### Phase 2-2: 헬퍼 메서드 추출 (`refactor/method-level`)

**목적**: 반복 로직 분리, 각 메서드가 하나의 역할만 담당

추출 메서드:

| 메서드 | 역할 |
|--------|------|
| `_is_sulfuras(item)` | Sulfuras 여부 판별 |
| `_is_aged_brie(item)` | Aged Brie 여부 판별 |
| `_is_backstage_pass(item)` | Backstage pass 여부 판별 |
| `_increase_quality(item, amount)` | quality 증가 (상한 50 적용) |
| `_decrease_quality(item, amount)` | quality 감소 (하한 0 적용) |
| `_update_normal_item(item)` | 일반 아이템 quality/sell_in 업데이트 |
| `_update_aged_brie(item)` | Aged Brie quality/sell_in 업데이트 |
| `_update_backstage_pass(item)` | Backstage pass quality/sell_in 업데이트 |

완료 기준: 헬퍼 메서드 추출 후 기존 테스트 전체 통과

---

### Phase 2-3: `update_quality()` 평탄화 (`refactor/method-level`)

**목적**: 중첩 depth 5 → 2 이하로 감소, 가독성 확보

리팩토링 후 구조:
```python
def update_quality(self):
    for item in self.items:
        if self._is_sulfuras(item):
            continue
        if self._is_aged_brie(item):
            self._update_aged_brie(item)
        elif self._is_backstage_pass(item):
            self._update_backstage_pass(item)
        else:
            self._update_normal_item(item)
        item.sell_in -= 1
```

완료 기준: `update_quality()` 최대 중첩 depth ≤ 2

---

### Phase 2-4: 테스트 통과 검증 (`refactor/method-level`)

**목적**: 리팩토링으로 기존 스펙이 깨지지 않았음을 확인

| 검증 항목 | 기준 |
|-----------|------|
| Phase 1 전체 테스트 | 모두 통과 |
| 커버리지 | 100% 유지 |

---

### Phase 3-1: ItemUpdater ABC 정의 (`refactor/class-level`)

**목적**: 모든 Updater의 공통 인터페이스 및 품질 조작 유틸리티 정의

```python
class ItemUpdater(ABC):
    MAX_QUALITY = 50
    MIN_QUALITY = 0

    @abstractmethod
    def update(self, item: Item) -> None: ...

    def _increase_quality(self, item, amount=1): ...
    def _decrease_quality(self, item, amount=1): ...
```

완료 기준: ABC 정의 및 import 확인

---

### Phase 3-2: 구체 Updater 클래스 작성 (`refactor/class-level`)

**목적**: 아이템 타입별 로직을 독립 클래스로 캡슐화

| 클래스 | 담당 |
|--------|------|
| `NormalItemUpdater` | 기본 아이템 |
| `AgedBrieUpdater` | Aged Brie |
| `SulfurasUpdater` | Sulfuras (no-op) |
| `BackstagePassUpdater` | Backstage passes |

완료 기준: 4개 클래스 작성 완료

---

### Phase 3-3: ItemUpdaterRegistry 구현 (`refactor/class-level`)

**목적**: 이름 → Updater 매핑 관리, 미등록 아이템 fallback 처리

```python
class ItemUpdaterRegistry:
    def register(self, name: str, updater: ItemUpdater) -> None: ...
    def get_updater(self, name: str) -> ItemUpdater: ...  # fallback: NormalItemUpdater
```

모듈 레벨 기본 레지스트리 생성 및 3개 특수 아이템 등록

완료 기준: Registry 생성 + 등록/조회 동작 확인

---

### Phase 3-4: GildedRose 리팩토링 (`refactor/class-level`)

**목적**: `update_quality()`를 레지스트리에 위임하도록 변경

```python
class GildedRose:
    def __init__(self, items, registry=None):
        self.items = items
        self._registry = registry or _default_registry

    def update_quality(self):
        for item in self.items:
            self._registry.get_updater(item.name).update(item)
```

완료 기준: Phase 1/2 테스트 전체 통과

---

### Phase 3-5: ConjuredItemUpdater 추가 (`refactor/class-level`)

**목적**: 기존 코드 수정 없이 새 아이템 타입 추가 — OCP 검증

```python
class ConjuredItemUpdater(ItemUpdater):
    def update(self, item):
        self._decrease_quality(item, 2)
        item.sell_in -= 1
        if item.sell_in < 0:
            self._decrease_quality(item, 2)
```

추가 테스트:
- `TestConjuredItem`: Conjured 품질 감소 규칙
- `TestItemUpdaterRegistry`: register/get_updater 로직
- `TestGildedRoseWithCustomRegistry`: 커스텀 레지스트리 주입

완료 기준: 기존 코드(`GildedRose`, 기존 Updater) 수정 없이 Conjured 동작

---

### Phase 3-6: 전체 테스트 통과 검증 (`refactor/class-level`)

**목적**: 모든 Phase의 테스트가 통과하고 커버리지가 유지됨을 확인

| 검증 항목 | 기준 |
|-----------|------|
| Phase 1 + Phase 3 추가 테스트 전체 | 모두 통과 |
| 커버리지 | 100% 유지 |
| OCP 검증 | `GildedRose` / 기존 Updater 미수정 확인 |
