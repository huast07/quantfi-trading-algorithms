# Leaderboard: quick suite (seeds [1])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | orch_v1 | 229,979 | toxic-flow (206,185) | 206,185 | 0 | 7,473 | 0 | 0 |
| 2 | orch_v2_stacked | 224,344 | toxic-flow (202,900) | 202,900 | 0 | 7,734 | 0 | 0 |
| 3 | reference | -974 | golden-continues (-3,306) | -3,306 | 4 | 16,570 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| orch_v2_stacked | 5,635 | [2,977, 8,295] |
| reference | 230,953 | [221,786, 239,721] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| orch_v1 | 152,409 | 119,550 | 125,568 | 397,526 | 0 | 1.22 |
| orch_v2_stacked | 146,381 | 113,212 | 123,398 | 382,992 | 0 | 1.50 |

## Tier-weighted PnL by product

| Product | orch_v1 | orch_v2_stacked | reference |
|---|---:|---:|---:|
| AMETHYST | 582 | 582 | 275 |
| BLACK_PEARLS | 1,726 | 1,726 | 566 |
| BLUE_PEARLS | 2,029 | 2,029 | -1,103 |
| DRAGONFRUIT | 0 | 0 | 17 |
| FRUIT_BASKET | -2,294 | -2,294 | -2,294 |
| GOLDEN_PEARLS | 1,360 | 1,360 | -712 |
| GRANADILLA | 0 | 0 | -2,091 |
| JELLY | 5,562 | 5,590 | 5,562 |
| LYCHEE | -6,948 | -6,948 | -1,578 |
| MANGOSTEEN | 0 | 0 | -1,796 |
| PAPER_LANTERNS | 1,073 | 1,073 | 1,032 |
| PEANUT_BUTTER | 0 | 0 | 436 |
| PINK_PEARLS | 10,700 | 6,920 | -951 |
| TELLURIUM | 116,858 | 116,858 | 0 |
| TOFFEE_CAKE | 34,370 | 32,486 | 73 |
| VOUCHER_6800 | 5,047 | 5,047 | 0 |
| VOUCHER_7000 | 8,134 | 8,134 | 0 |
| VOUCHER_7200 | 13,402 | 13,402 | 0 |
| VOUCHER_7300 | 12,118 | 12,118 | 0 |
| VOUCHER_7400 | 2,079 | 2,079 | 0 |
| VOUCHER_7500 | 9,027 | 9,027 | 0 |
| VOUCHER_7600 | 6,627 | 6,627 | 0 |
| VOUCHER_7750 | 3,625 | 3,625 | 0 |
| VOUCHER_7900 | 4,203 | 4,203 | 0 |
| VOUCHER_8100 | 950 | 950 | 0 |
| WHITE_PEARLS | -251 | -251 | 1,591 |

## Weak cases

- **orch_v1:** none
- **orch_v2_stacked:** none
- **reference:** busy-day (-3,118 mean; of which FRUIT_BASKET -5,196; loses money; behind orch_v1, orch_v2_stacked on the one seed run); golden-continues (-3,306 mean; of which GOLDEN_PEARLS -3,498; loses money; behind orch_v1, orch_v2_stacked on the one seed run); toxic-flow (-2,542 mean; of which BLUE_PEARLS -2,494; loses money; behind orch_v1, orch_v2_stacked on the one seed run); tellurium-storm (+44 mean; of which MANGOSTEEN -2,706; edge over orch_v1, orch_v2_stacked -429,566, well below its usual -251,049; behind orch_v1, orch_v2_stacked on the one seed run)
