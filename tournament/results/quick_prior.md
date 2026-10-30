# Leaderboard: quick suite (seeds [1])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | orch_v3_newcore | 228,604 | toxic-flow (203,140) | 203,140 | 0 | 7,302 | 0 | 0 |
| 2 | orch_v4p_n20000 | 219,037 | toxic-flow (195,605) | 195,605 | 1 | 8,503 | 0 | 0 |
| 3 | orch_v4p_n200000 | 217,555 | toxic-flow (194,365) | 194,365 | 1 | 7,826 | 0 | 0 |
| 4 | orch_v3p_n200000 | 216,782 | toxic-flow (194,435) | 194,435 | 0 | 7,044 | 0 | 0 |
| 5 | orch_v3p_n20000 | 215,264 | vol-clustering (191,746) | 191,746 | 0 | 7,074 | 0 | 0 |
| 6 | reference | -974 | golden-continues (-3,306) | -3,306 | 4 | 16,570 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| orch_v4p_n20000 | 9,568 | [3,102, 16,124] |
| orch_v4p_n200000 | 11,049 | [3,904, 18,439] |
| orch_v3p_n200000 | 11,822 | [7,351, 16,325] |
| orch_v3p_n20000 | 13,340 | [8,101, 18,626] |
| reference | 229,578 | [222,102, 236,787] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| orch_v3_newcore | 153,636 | 132,665 | 131,391 | 417,692 | 0 | 2.74 |
| orch_v3p_n20000 | 140,070 | 122,696 | 121,976 | 384,742 | 0 | 3.69 |
| orch_v3p_n200000 | 144,952 | 127,186 | 127,394 | 399,532 | 0 | 2.91 |
| orch_v4p_n20000 | 145,538 | 122,762 | 118,387 | 386,686 | 0 | 4.70 |
| orch_v4p_n200000 | 151,198 | 120,096 | 121,802 | 393,096 | 0 | 4.11 |

## Tier-weighted PnL by product

| Product | orch_v3_newcore | orch_v4p_n20000 | orch_v4p_n200000 | orch_v3p_n200000 | orch_v3p_n20000 | reference |
|---|---:|---:|---:|---:|---:|---:|
| AMETHYST | 582 | 584 | 584 | 581 | 581 | 275 |
| BLACK_PEARLS | 1,726 | 1,701 | 1,298 | 1,611 | 1,611 | 566 |
| BLUE_PEARLS | 2,029 | -881 | -912 | 2,029 | 2,029 | -1,103 |
| DRAGONFRUIT | 0 | 1,465 | 1,589 | 0 | 0 | 17 |
| FRUIT_BASKET | 0 | -1,104 | -1,104 | 0 | 0 | -2,294 |
| GOLDEN_PEARLS | 1,360 | 1,264 | 1,264 | 1,313 | 1,313 | -712 |
| GRANADILLA | 0 | 482 | 482 | 0 | 0 | -2,091 |
| JELLY | 318 | 5,621 | 5,616 | 556 | 1,009 | 5,562 |
| LYCHEE | -6,948 | -590 | -768 | -3,211 | -3,390 | -1,578 |
| MANGOSTEEN | 0 | -90 | -90 | 0 | 0 | -1,796 |
| PAPER_LANTERNS | 1,073 | 1,360 | 1,483 | 1,002 | 996 | 1,032 |
| PEANUT_BUTTER | 0 | 100 | 100 | 0 | 0 | 436 |
| PINK_PEARLS | 10,700 | 3,381 | 5,210 | 5,605 | 5,297 | -951 |
| TELLURIUM | 116,858 | 113,312 | 113,312 | 113,312 | 113,312 | 0 |
| TOFFEE_CAKE | 34,370 | 32,162 | 28,305 | 32,753 | 32,924 | 73 |
| VOUCHER_6800 | 5,047 | 816 | 816 | 816 | 816 | 0 |
| VOUCHER_7000 | 8,134 | 8,015 | 8,129 | 8,129 | 8,015 | 0 |
| VOUCHER_7200 | 13,402 | 13,213 | 13,235 | 13,235 | 13,213 | 0 |
| VOUCHER_7300 | 12,118 | 11,367 | 11,363 | 11,363 | 11,367 | 0 |
| VOUCHER_7400 | 2,079 | 1,565 | 1,860 | 1,860 | 1,565 | 0 |
| VOUCHER_7500 | 9,027 | 8,870 | 8,935 | 8,935 | 8,870 | 0 |
| VOUCHER_7600 | 6,627 | 6,913 | 7,018 | 7,018 | 6,913 | 0 |
| VOUCHER_7750 | 3,625 | 2,884 | 3,606 | 3,606 | 2,884 | 0 |
| VOUCHER_7900 | 4,203 | 4,234 | 4,234 | 4,234 | 4,234 | 0 |
| VOUCHER_8100 | 950 | 683 | 683 | 683 | 683 | 0 |
| WHITE_PEARLS | 1,324 | 1,712 | 1,307 | 1,353 | 1,023 | 1,591 |

## Weak cases

- **orch_v3_newcore:** none
- **orch_v4p_n20000:** black-swan-crash (+253,832 mean; of which VOUCHER_6800 -18,654; edge over orch_v3_newcore, orch_v3p_n20000, orch_v3p_n200000, orch_v4p_n200000, reference +10,251, well below its usual +43,962; beats reference on the one seed run)
- **orch_v4p_n200000:** black-swan-crash (+251,672 mean; of which VOUCHER_6800 -18,654; edge over orch_v3_newcore, orch_v3p_n20000, orch_v3p_n200000, orch_v4p_n20000, reference +7,658, well below its usual +42,034; beats reference on the one seed run)
- **orch_v3p_n200000:** none
- **orch_v3p_n20000:** none
- **reference:** busy-day (-3,118 mean; of which FRUIT_BASKET -5,196; loses money; behind orch_v3_newcore, orch_v3p_n20000, orch_v3p_n200000, orch_v4p_n20000, orch_v4p_n200000 on the one seed run); golden-continues (-3,306 mean; of which GOLDEN_PEARLS -3,498; loses money; behind orch_v3_newcore, orch_v3p_n20000, orch_v3p_n200000, orch_v4p_n20000, orch_v4p_n200000 on the one seed run); toxic-flow (-2,542 mean; of which BLUE_PEARLS -2,494; loses money; behind orch_v3_newcore, orch_v3p_n20000, orch_v3p_n200000, orch_v4p_n20000, orch_v4p_n200000 on the one seed run); tellurium-storm (+44 mean; of which MANGOSTEEN -2,706; edge over orch_v3_newcore, orch_v3p_n20000, orch_v3p_n200000, orch_v4p_n20000, orch_v4p_n200000 -417,437, well below its usual -240,453; behind orch_v3_newcore, orch_v3p_n20000, orch_v3p_n200000, orch_v4p_n20000, orch_v4p_n200000 on the one seed run)
