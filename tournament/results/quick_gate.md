# Leaderboard: quick suite (seeds [1])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | orch_v3_newcore | 228,604 | toxic-flow (203,140) | 203,140 | 0 | 7,302 | 0 | 0 |
| 2 | orch_v3_gated | 208,029 | toxic-flow (181,542) | 181,542 | 0 | 6,401 | 0 | 0 |
| 3 | orch_v4_pre | 200,981 | toxic-flow (179,406) | 179,406 | 1 | 8,626 | 0 | 0 |
| 4 | reference | -974 | golden-continues (-3,306) | -3,306 | 4 | 16,570 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| orch_v3_gated | 20,576 | [12,983, 28,310] |
| orch_v4_pre | 27,623 | [19,689, 35,733] |
| reference | 229,578 | [222,102, 236,787] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| orch_v3_newcore | 153,636 | 132,665 | 131,391 | 417,692 | 0 | 4.99 |
| orch_v3_gated | 131,868 | 110,902 | 118,130 | 360,901 | 0 | 6.77 |
| orch_v4_pre | 138,983 | 95,992 | 107,840 | 342,815 | 0 | 15.00 |

## Tier-weighted PnL by product

| Product | orch_v3_newcore | orch_v3_gated | orch_v4_pre | reference |
|---|---:|---:|---:|---:|
| AMETHYST | 582 | 562 | 579 | 275 |
| BLACK_PEARLS | 1,726 | 1,640 | 309 | 566 |
| BLUE_PEARLS | 2,029 | 1,942 | -948 | -1,103 |
| DRAGONFRUIT | 0 | 0 | 45 | 17 |
| FRUIT_BASKET | 0 | 0 | -2,198 | -2,294 |
| GOLDEN_PEARLS | 1,360 | 1,191 | 1,065 | -712 |
| GRANADILLA | 0 | 0 | -2,052 | -2,091 |
| JELLY | 318 | 1,135 | 5,713 | 5,562 |
| LYCHEE | -6,948 | 49 | -634 | -1,578 |
| MANGOSTEEN | 0 | 0 | -120 | -1,796 |
| PAPER_LANTERNS | 1,073 | 807 | 1,458 | 1,032 |
| PEANUT_BUTTER | 0 | 0 | 291 | 436 |
| PINK_PEARLS | 10,700 | 5,487 | 4,132 | -951 |
| TELLURIUM | 116,858 | 112,730 | 112,730 | 0 |
| TOFFEE_CAKE | 34,370 | 25,515 | 22,958 | 73 |
| VOUCHER_6800 | 5,047 | 816 | 816 | 0 |
| VOUCHER_7000 | 8,134 | 7,109 | 7,109 | 0 |
| VOUCHER_7200 | 13,402 | 12,737 | 12,737 | 0 |
| VOUCHER_7300 | 12,118 | 10,794 | 10,794 | 0 |
| VOUCHER_7400 | 2,079 | 1,807 | 1,807 | 0 |
| VOUCHER_7500 | 9,027 | 8,065 | 8,065 | 0 |
| VOUCHER_7600 | 6,627 | 6,869 | 6,869 | 0 |
| VOUCHER_7750 | 3,625 | 2,884 | 2,884 | 0 |
| VOUCHER_7900 | 4,203 | 4,234 | 4,234 | 0 |
| VOUCHER_8100 | 950 | 683 | 683 | 0 |
| WHITE_PEARLS | 1,324 | 973 | 1,655 | 1,591 |

## Weak cases

- **orch_v3_newcore:** none
- **orch_v3_gated:** none
- **orch_v4_pre:** black-swan-crash (+217,996 mean; of which VOUCHER_6800 -18,654; edge over orch_v3_newcore, orch_v3_gated, reference -3,847, well below its usual +56,885; beats reference on the one seed run)
- **reference:** busy-day (-3,118 mean; of which FRUIT_BASKET -5,196; loses money; behind orch_v3_newcore, orch_v3_gated, orch_v4_pre on the one seed run); golden-continues (-3,306 mean; of which GOLDEN_PEARLS -3,498; loses money; behind orch_v3_newcore, orch_v3_gated, orch_v4_pre on the one seed run); toxic-flow (-2,542 mean; of which BLUE_PEARLS -2,494; loses money; behind orch_v3_newcore, orch_v3_gated, orch_v4_pre on the one seed run); tellurium-storm (+44 mean; of which MANGOSTEEN -2,706; edge over orch_v3_newcore, orch_v3_gated, orch_v4_pre -412,308, well below its usual -234,154; behind orch_v3_newcore, orch_v3_gated, orch_v4_pre on the one seed run)
