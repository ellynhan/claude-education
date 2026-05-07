# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
pytest

# Run a single test class
pytest tests/test_gilded_rose.py::TestNormalItem

# Run a single test method
pytest tests/test_gilded_rose.py::TestNormalItem::test_quality_decreases_by_one

# Run tests with coverage (configured in pytest.ini)
pytest --cov=gilded_rose --cov-report=html --cov-report=term-missing
```

## Architecture

### Current State

`gilded_rose.py` contains two classes:

- `Item` — data class with `name`, `sell_in`, `quality`. **Must not be modified** (goblin rule from spec).
- `GildedRose` — holds `self.items` list and exposes `update_quality()`. All item logic is currently crammed into this single method with up to 5 levels of nested `if` statements.

### Refactoring Plan (3 branches, in order)

See `docs/plan.md` for the full plan and `docs/design.md` for detailed design.

**Branch `feat/unittest`** — add spec-based tests, no production code changes.  
**Branch `refactor/method-level`** — improve readability inside `update_quality()`, extract helper methods, replace magic numbers with constants. Tests must stay green.  
**Branch `refactor/class-level`** — introduce Strategy pattern + Registry so new item types require zero changes to existing code (OCP).

### Target Architecture (Branch 3)

```
ItemUpdater (ABC)
  ├── NormalItemUpdater
  ├── AgedBrieUpdater
  ├── SulfurasUpdater
  ├── BackstagePassUpdater
  └── ConjuredItemUpdater   ← OCP validation

ItemUpdaterRegistry
  register(name, updater)   ← extend here, never modify existing updaters
  get_updater(name)         ← falls back to NormalItemUpdater

GildedRose
  update_quality()          ← delegates to registry.get_updater(item.name).update(item)
```

## Business Rules (from README)

| Item | Quality behaviour |
|------|-------------------|
| Normal | −1/day; −2/day after sell_in < 0 |
| Aged Brie | +1/day; +2/day after sell_in < 0 |
| Sulfuras | sell_in and quality never change (quality fixed at 80) |
| Backstage passes | +1 (sell_in > 10), +2 (≤ 10), +3 (≤ 5); drops to 0 after concert |
| Conjured *(future)* | −2/day; −4/day after sell_in < 0 |

Quality is always clamped to `[0, 50]` (Sulfuras is the only exception at 80).

## Constraints

- `Item` class and `GildedRose.items` property must not be modified.
- `GildedRose.update_quality()` public signature must be preserved across all branches.
- Coverage target: 100% line coverage on `gilded_rose.py`.
