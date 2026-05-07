from abc import ABC, abstractmethod
from typing import Callable


class ItemUpdater(ABC):
    MAX_QUALITY = 50
    MIN_QUALITY = 0

    @abstractmethod
    def update(self, item) -> None:
        ...

    def _increase_quality(self, item, amount: int = 1) -> None:
        item.quality = min(item.quality + amount, self.MAX_QUALITY)

    def _decrease_quality(self, item, amount: int = 1) -> None:
        item.quality = max(item.quality - amount, self.MIN_QUALITY)


class NormalItemUpdater(ItemUpdater):
    def update(self, item) -> None:
        self._decrease_quality(item)
        item.sell_in -= 1
        if item.sell_in < 0:
            self._decrease_quality(item)


class AgedBrieUpdater(ItemUpdater):
    def update(self, item) -> None:
        self._increase_quality(item)
        item.sell_in -= 1
        if item.sell_in < 0:
            self._increase_quality(item)


class SulfurasUpdater(ItemUpdater):
    def update(self, item) -> None:
        pass


class BackstagePassUpdater(ItemUpdater):
    def update(self, item) -> None:
        if item.sell_in > 10:
            self._increase_quality(item, 1)
        elif item.sell_in > 5:
            self._increase_quality(item, 2)
        else:
            self._increase_quality(item, 3)
        item.sell_in -= 1
        if item.sell_in < 0:
            item.quality = self.MIN_QUALITY


class ConjuredItemUpdater(ItemUpdater):
    def update(self, item) -> None:
        self._decrease_quality(item, 2)
        item.sell_in -= 1
        if item.sell_in < 0:
            self._decrease_quality(item, 2)


class ItemUpdaterRegistry:
    def __init__(self) -> None:
        self._exact: dict[str, ItemUpdater] = {}
        self._predicates: list[tuple[Callable[[str], bool], ItemUpdater]] = []
        self._default: ItemUpdater = NormalItemUpdater()

    def register(self, name: str, updater: ItemUpdater) -> None:
        self._exact[name] = updater

    def register_predicate(self, predicate: Callable[[str], bool], updater: ItemUpdater) -> None:
        self._predicates.append((predicate, updater))

    def get_updater(self, name: str) -> ItemUpdater:
        if name in self._exact:
            return self._exact[name]
        for predicate, updater in self._predicates:
            if predicate(name):
                return updater
        return self._default


_default_registry = ItemUpdaterRegistry()
_default_registry.register("Aged Brie",                                AgedBrieUpdater())
_default_registry.register("Sulfuras, Hand of Ragnaros",               SulfurasUpdater())
_default_registry.register("Backstage passes to a TAFKAL80ETC concert", BackstagePassUpdater())
# Conjured 아이템이 정식 도입될 때 아래 한 줄을 활성화:
# _default_registry.register_predicate(lambda n: n.startswith("Conjured"), ConjuredItemUpdater())


class GildedRose:
    def __init__(self, items, registry: ItemUpdaterRegistry = None) -> None:
        self.items = items
        self._registry = registry if registry is not None else _default_registry

    def update_quality(self) -> None:
        for item in self.items:
            updater = self._registry.get_updater(item.name)
            updater.update(item)


class Item:
    def __init__(self, name, sell_in, quality):
        self.name = name
        self.sell_in = sell_in
        self.quality = quality

    def __repr__(self):
        return "%s, %s, %s" % (self.name, self.sell_in, self.quality)
