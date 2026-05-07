# Gilded Rose 리팩토링 설계 인덱스

각 Phase의 상세 설계는 아래 문서를 참조한다.

| Phase | 브랜치 | 문서 | 핵심 내용 |
|-------|--------|------|-----------|
| Phase 1 | `feat/unittest` | [design-phase1.md](design-phase1.md) | 테스트 환경 구성, 아이템별 테스트 케이스 명세, 커버리지 100% 달성 |
| Phase 2 | `refactor/method-level` | [design-phase2.md](design-phase2.md) | 상수 추출, 헬퍼 메서드 분리, `update_quality()` 평탄화 |
| Phase 3 | `refactor/class-level` | [design-phase3.md](design-phase3.md) | 전략 패턴 + 레지스트리, OCP 구조화, Conjured 아이템 확장 |

---

## 공통 제약

- `Item` 클래스 변경 금지 (고블린 규칙)
- `GildedRose.items` 속성 변경 금지
- `GildedRose.update_quality()` 공개 시그니처 유지
- 각 브랜치는 이전 브랜치 테스트가 **전부 통과**하는 상태를 유지하며 진행

## 공통 비즈니스 규칙 요약

| 아이템 | Quality 변화 |
|--------|-------------|
| Normal | −1/day; 기한 후 −2/day |
| Aged Brie | +1/day; 기한 후 +2/day |
| Sulfuras | 불변 (quality 고정 80) |
| Backstage passes | +1 (sell_in>10), +2 (≤10), +3 (≤5); 기한 후 0 |
| Conjured *(Phase 3)* | −2/day; 기한 후 −4/day |

Quality 범위: `[0, 50]` (Sulfuras 제외)
