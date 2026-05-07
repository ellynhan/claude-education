_AGED_BRIE        = "Aged Brie"
_SULFURAS         = "Sulfuras, Hand of Ragnaros"
_BACKSTAGE_PASSES = "Backstage passes to a TAFKAL80ETC concert"

_MAX_QUALITY = 50
_MIN_QUALITY = 0


class GildedRose(object):
    def __init__(self, items):
        self.items = items

    def _is_sulfuras(self, item) -> bool:
        return item.name == _SULFURAS

    def _is_aged_brie(self, item) -> bool:
        return item.name == _AGED_BRIE

    def _is_backstage_pass(self, item) -> bool:
        return item.name == _BACKSTAGE_PASSES

    def _increase_quality(self, item, amount: int = 1) -> None:
        item.quality = min(item.quality + amount, _MAX_QUALITY)

    def _decrease_quality(self, item, amount: int = 1) -> None:
        item.quality = max(item.quality - amount, _MIN_QUALITY)

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


class Item:
    def __init__(self, name, sell_in, quality):
        self.name = name
        self.sell_in = sell_in
        self.quality = quality

    def __repr__(self):
        return "%s, %s, %s" % (self.name, self.sell_in, self.quality)