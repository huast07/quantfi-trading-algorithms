# Leaderboard: quick suite (seeds [1])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | orch_v4r_fs0_nojump | 235,264 | toxic-flow (206,512) | 206,512 | 0 | 7,695 | 0 | 0 |
| 2 | orch_v3_newcore | 228,604 | toxic-flow (203,140) | 203,140 | 0 | 7,302 | 0 | 0 |
| 3 | orch_v4s | 227,677 | toxic-flow (201,531) | 201,531 | 0 | 7,449 | 0 | 0 |
| 4 | reference | -974 | golden-continues (-3,306) | -3,306 | 4 | 16,570 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| orch_v3_newcore | 6,659 | [5,013, 8,301] |
| orch_v4s | 7,587 | [6,137, 8,937] |
| reference | 236,238 | [226,885, 244,987] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| orch_v3_newcore | 153,636 | 132,665 | 131,391 | 417,692 | 0 | 2.26 |
| orch_v4r_fs0_nojump | 155,722 | 133,694 | 128,272 | 417,689 | 0 | 3.20 |
| orch_v4s | 158,030 | 135,670 | 134,322 | 428,022 | 0 | 2.38 |

## Tier-weighted PnL by product

| Product | orch_v4r_fs0_nojump | orch_v3_newcore | orch_v4s | reference |
|---|---:|---:|---:|---:|
| AMETHYST | 582 | 582 | 582 | 275 |
| BLACK_PEARLS | 1,726 | 1,726 | 1,726 | 566 |
| BLUE_PEARLS | 2,029 | 2,029 | 2,029 | -1,103 |
| DRAGONFRUIT | 1,822 | 0 | 1,822 | 17 |
| FRUIT_BASKET | 0 | 0 | 0 | -2,294 |
| GOLDEN_PEARLS | 1,394 | 1,360 | 1,394 | -712 |
| GRANADILLA | -662 | 0 | -662 | -2,091 |
| JELLY | 5,562 | 318 | -16 | 5,562 |
| LYCHEE | -6,790 | -6,948 | -3,652 | -1,578 |
| MANGOSTEEN | 0 | 0 | 0 | -1,796 |
| PAPER_LANTERNS | 1,073 | 1,073 | 1,073 | 1,032 |
| PEANUT_BUTTER | 94 | 0 | 0 | 436 |
| PINK_PEARLS | 10,700 | 10,700 | 10,700 | -951 |
| TELLURIUM | 116,858 | 116,858 | 116,858 | 0 |
| TOFFEE_CAKE | 34,370 | 34,370 | 34,370 | 73 |
| VOUCHER_6800 | 5,047 | 5,047 | 0 | 0 |
| VOUCHER_7000 | 8,134 | 8,134 | 8,134 | 0 |
| VOUCHER_7200 | 13,402 | 13,402 | 13,402 | 0 |
| VOUCHER_7300 | 12,111 | 12,118 | 12,112 | 0 |
| VOUCHER_7400 | 2,059 | 2,079 | 2,060 | 0 |
| VOUCHER_7500 | 9,027 | 9,027 | 9,027 | 0 |
| VOUCHER_7600 | 6,623 | 6,627 | 6,614 | 0 |
| VOUCHER_7750 | 3,625 | 3,625 | 3,625 | 0 |
| VOUCHER_7900 | 4,203 | 4,203 | 4,203 | 0 |
| VOUCHER_8100 | 685 | 950 | 685 | 0 |
| WHITE_PEARLS | 1,591 | 1,324 | 1,591 | 1,591 |

## Weak cases

- **orch_v4r_fs0_nojump:** none
- **orch_v3_newcore:** none
- **orch_v4s:** none
- **reference:** busy-day (-3,118 mean; of which FRUIT_BASKET -5,196; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on the one seed run); golden-continues (-3,306 mean; of which GOLDEN_PEARLS -3,498; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on the one seed run); toxic-flow (-2,542 mean; of which BLUE_PEARLS -2,494; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on the one seed run); tellurium-storm (+44 mean; of which MANGOSTEEN -2,706; edge over orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s -430,453, well below its usual -257,319; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on the one seed run)
