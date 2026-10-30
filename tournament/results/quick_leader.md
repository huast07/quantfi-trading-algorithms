# Leaderboard: quick suite (seeds [1])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | orch_v3_newcore | 228,604 | toxic-flow (203,140) | 203,140 | 0 | 7,302 | 0 | 0 |
| 2 | orch_v4r_fs0 | 227,621 | toxic-flow (204,699) | 204,699 | 0 | 7,715 | 0 | 0 |
| 3 | orch_v4q_n200000_lam0 | 226,840 | toxic-flow (203,762) | 203,762 | 0 | 8,025 | 0 | 0 |
| 4 | orch_v4r_fs0.3 | 225,142 | toxic-flow (202,234) | 202,234 | 0 | 8,057 | 0 | 0 |
| 5 | reference | -974 | golden-continues (-3,306) | -3,306 | 4 | 16,570 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| orch_v4r_fs0 | 983 | [-3,780, 5,759] |
| orch_v4q_n200000_lam0 | 1,764 | [-3,255, 6,795] |
| orch_v4r_fs0.3 | 3,462 | [-1,057, 7,995] |
| reference | 229,578 | [222,102, 236,787] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| orch_v3_newcore | 153,636 | 132,665 | 131,391 | 417,692 | 0 | 1.74 |
| orch_v4q_n200000_lam0 | 146,956 | 120,486 | 122,092 | 389,534 | 0 | 2.88 |
| orch_v4r_fs0 | 148,910 | 129,957 | 122,216 | 401,082 | 0 | 2.63 |
| orch_v4r_fs0.3 | 148,278 | 126,279 | 122,274 | 396,832 | 0 | 2.83 |

## Tier-weighted PnL by product

| Product | orch_v3_newcore | orch_v4r_fs0 | orch_v4q_n200000_lam0 | orch_v4r_fs0.3 | reference |
|---|---:|---:|---:|---:|---:|
| AMETHYST | 582 | 581 | 584 | 583 | 275 |
| BLACK_PEARLS | 1,726 | 1,611 | 1,050 | 1,624 | 566 |
| BLUE_PEARLS | 2,029 | 2,029 | -853 | 1,034 | -1,103 |
| DRAGONFRUIT | 0 | 1,822 | 1,593 | 1,822 | 17 |
| FRUIT_BASKET | 0 | 0 | -1,104 | 0 | -2,294 |
| GOLDEN_PEARLS | 1,360 | 1,257 | 1,272 | 1,295 | -712 |
| GRANADILLA | 0 | -662 | 422 | -662 | -2,091 |
| JELLY | 318 | 5,427 | 5,599 | 5,606 | 5,562 |
| LYCHEE | -6,948 | -6,776 | -1,428 | -6,240 | -1,578 |
| MANGOSTEEN | 0 | 0 | -90 | 0 | -1,796 |
| PAPER_LANTERNS | 1,073 | 990 | 1,206 | 1,142 | 1,032 |
| PEANUT_BUTTER | 0 | 139 | 139 | 139 | 436 |
| PINK_PEARLS | 10,700 | 5,574 | 5,646 | 5,594 | -951 |
| TELLURIUM | 116,858 | 116,858 | 116,858 | 116,858 | 0 |
| TOFFEE_CAKE | 34,370 | 32,978 | 30,088 | 30,478 | 73 |
| VOUCHER_6800 | 5,047 | 5,049 | 5,049 | 5,049 | 0 |
| VOUCHER_7000 | 8,134 | 8,129 | 8,129 | 8,129 | 0 |
| VOUCHER_7200 | 13,402 | 13,235 | 13,235 | 13,235 | 0 |
| VOUCHER_7300 | 12,118 | 11,365 | 11,365 | 11,365 | 0 |
| VOUCHER_7400 | 2,079 | 1,955 | 1,955 | 1,955 | 0 |
| VOUCHER_7500 | 9,027 | 8,935 | 8,935 | 8,935 | 0 |
| VOUCHER_7600 | 6,627 | 7,026 | 7,026 | 7,026 | 0 |
| VOUCHER_7750 | 3,625 | 3,606 | 3,606 | 3,606 | 0 |
| VOUCHER_7900 | 4,203 | 4,180 | 4,180 | 4,180 | 0 |
| VOUCHER_8100 | 950 | 683 | 683 | 683 | 0 |
| WHITE_PEARLS | 1,324 | 1,630 | 1,697 | 1,708 | 1,591 |

## Weak cases

- **orch_v3_newcore:** none
- **orch_v4r_fs0:** none
- **orch_v4q_n200000_lam0:** none
- **orch_v4r_fs0.3:** none
- **reference:** busy-day (-3,118 mean; of which FRUIT_BASKET -5,196; loses money; behind orch_v3_newcore, orch_v4q_n200000_lam0, orch_v4r_fs0, orch_v4r_fs0.3 on the one seed run); golden-continues (-3,306 mean; of which GOLDEN_PEARLS -3,498; loses money; behind orch_v3_newcore, orch_v4q_n200000_lam0, orch_v4r_fs0, orch_v4r_fs0.3 on the one seed run); toxic-flow (-2,542 mean; of which BLUE_PEARLS -2,494; loses money; behind orch_v3_newcore, orch_v4q_n200000_lam0, orch_v4r_fs0, orch_v4r_fs0.3 on the one seed run); tellurium-storm (+44 mean; of which MANGOSTEEN -2,706; edge over orch_v3_newcore, orch_v4q_n200000_lam0, orch_v4r_fs0, orch_v4r_fs0.3 -430,669, well below its usual -249,605; behind orch_v3_newcore, orch_v4q_n200000_lam0, orch_v4r_fs0, orch_v4r_fs0.3 on the one seed run)
