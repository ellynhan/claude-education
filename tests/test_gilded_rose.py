import pytest
from gilded_rose import Item, GildedRose


def _make_gilded_rose(name, sell_in, quality):
    items = [Item(name, sell_in, quality)]
    return GildedRose(items), items[0]


# ---------------------------------------------------------------------------
# Phase 1-2: 일반 아이템
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Phase 1-3: Aged Brie
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Phase 1-3: Sulfuras
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Phase 1-3 & 1-4: Backstage passes
# ---------------------------------------------------------------------------

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

    def test_quality_increases_by_one_at_eleven_days(self):
        item = self._run(sell_in=11, quality=20)
        assert item.quality == 21

    def test_quality_increases_by_two_at_ten_days(self):
        # sell_in=10 은 ≤10 경계 — +2 적용
        item = self._run(sell_in=10, quality=20)
        assert item.quality == 22

    def test_quality_increases_by_two_between_6_and_10(self):
        item = self._run(sell_in=8, quality=20)
        assert item.quality == 22

    def test_quality_increases_by_two_at_six_days(self):
        # sell_in=6 은 ≤10, >5 — +2 적용
        item = self._run(sell_in=6, quality=20)
        assert item.quality == 22

    def test_quality_increases_by_three_at_five_days(self):
        # sell_in=5 는 ≤5 경계 — +3 적용
        item = self._run(sell_in=5, quality=20)
        assert item.quality == 23

    def test_quality_increases_by_three_between_1_and_5(self):
        item = self._run(sell_in=3, quality=20)
        assert item.quality == 23

    def test_quality_drops_to_zero_after_concert(self):
        # sell_in=0: 호출 후 sell_in=-1, quality=0
        item = self._run(sell_in=0, quality=20)
        assert item.quality == 0

    def test_quality_is_zero_when_already_past(self):
        item = self._run(sell_in=-1, quality=20)
        assert item.quality == 0

    def test_quality_capped_at_50(self):
        item = self._run(sell_in=5, quality=49)
        assert item.quality == 50

    def test_sell_in_decreases(self):
        item = self._run(sell_in=15, quality=20)
        assert item.sell_in == 14


# ---------------------------------------------------------------------------
# Item.__repr__ 커버리지
# ---------------------------------------------------------------------------

class TestItemRepr:
    def test_repr(self):
        item = Item("foo", 5, 10)
        assert repr(item) == "foo, 5, 10"
