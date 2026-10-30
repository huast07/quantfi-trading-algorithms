# Leaderboard: quick suite (seeds [1])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | orch_v3_newcore | 228,604 | toxic-flow (203,140) | 203,140 | 0 | 7,302 | 0 | 0 |
| 2 | orch_v4q_n200000_lam0 | 226,840 | toxic-flow (203,762) | 203,762 | 0 | 8,025 | 0 | 0 |
| 3 | orch_v4q_n200000_lam1e-05 | 226,374 | toxic-flow (203,762) | 203,762 | 0 | 8,380 | 0 | 0 |
| 4 | orch_v4q_n200000_lam3e-05 | 226,026 | toxic-flow (203,092) | 203,092 | 0 | 8,337 | 0 | 0 |
| 5 | orch_v4q_n20000_lam3e-05 | 223,159 | toxic-flow (200,944) | 200,944 | 1 | 8,473 | 0 | 0 |
| 6 | reference | -974 | golden-continues (-3,306) | -3,306 | 4 | 16,570 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| orch_v4q_n200000_lam0 | 1,764 | [-3,255, 6,795] |
| orch_v4q_n200000_lam1e-05 | 2,230 | [-3,255, 7,728] |
| orch_v4q_n200000_lam3e-05 | 2,578 | [-3,168, 8,337] |
| orch_v4q_n20000_lam3e-05 | 5,446 | [168, 10,749] |
| reference | 229,578 | [222,102, 236,787] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| orch_v3_newcore | 153,636 | 132,665 | 131,391 | 417,692 | 0 | 1.78 |
| orch_v4q_n20000_lam3e-05 | 146,584 | 116,747 | 121,120 | 384,451 | 0 | 3.63 |
| orch_v4q_n200000_lam3e-05 | 145,580 | 120,486 | 122,464 | 388,531 | 0 | 2.88 |
| orch_v4q_n200000_lam1e-05 | 146,530 | 120,486 | 122,092 | 389,109 | 0 | 3.70 |
| orch_v4q_n200000_lam0 | 146,956 | 120,486 | 122,092 | 389,534 | 0 | 3.03 |

## Tier-weighted PnL by product

| Product | orch_v3_newcore | orch_v4q_n200000_lam0 | orch_v4q_n200000_lam1e-05 | orch_v4q_n200000_lam3e-05 | orch_v4q_n20000_lam3e-05 | reference |
|---|---:|---:|---:|---:|---:|---:|
| AMETHYST | 582 | 584 | 584 | 584 | 577 | 275 |
| BLACK_PEARLS | 1,726 | 1,050 | 1,050 | 1,050 | 885 | 566 |
| BLUE_PEARLS | 2,029 | -853 | -855 | -853 | -855 | -1,103 |
| DRAGONFRUIT | 0 | 1,593 | 1,593 | 1,593 | 1,286 | 17 |
| FRUIT_BASKET | 0 | -1,104 | -1,104 | -1,104 | -1,104 | -2,294 |
| GOLDEN_PEARLS | 1,360 | 1,272 | 1,272 | 1,272 | 1,272 | -712 |
| GRANADILLA | 0 | 422 | 422 | 422 | 494 | -2,091 |
| JELLY | 318 | 5,599 | 5,599 | 5,599 | 5,660 | 5,562 |
| LYCHEE | -6,948 | -1,428 | -1,430 | -1,430 | 1,816 | -1,578 |
| MANGOSTEEN | 0 | -90 | -90 | -90 | -99 | -1,796 |
| PAPER_LANTERNS | 1,073 | 1,206 | 1,209 | 1,212 | 1,339 | 1,032 |
| PEANUT_BUTTER | 0 | 139 | 150 | 160 | 146 | 436 |
| PINK_PEARLS | 10,700 | 5,646 | 5,165 | 5,165 | 4,813 | -951 |
| TELLURIUM | 116,858 | 116,858 | 116,858 | 116,487 | 116,742 | 0 |
| TOFFEE_CAKE | 34,370 | 30,088 | 30,069 | 30,073 | 29,880 | 73 |
| VOUCHER_6800 | 5,047 | 5,049 | 5,072 | 5,072 | 1,183 | 0 |
| VOUCHER_7000 | 8,134 | 8,129 | 8,129 | 8,129 | 8,129 | 0 |
| VOUCHER_7200 | 13,402 | 13,235 | 13,235 | 13,235 | 13,215 | 0 |
| VOUCHER_7300 | 12,118 | 11,365 | 11,365 | 11,365 | 11,367 | 0 |
| VOUCHER_7400 | 2,079 | 1,955 | 1,955 | 1,958 | 1,565 | 0 |
| VOUCHER_7500 | 9,027 | 8,935 | 8,935 | 8,935 | 8,935 | 0 |
| VOUCHER_7600 | 6,627 | 7,026 | 7,026 | 7,026 | 7,018 | 0 |
| VOUCHER_7750 | 3,625 | 3,606 | 3,606 | 3,606 | 2,884 | 0 |
| VOUCHER_7900 | 4,203 | 4,180 | 4,180 | 4,180 | 4,152 | 0 |
| VOUCHER_8100 | 950 | 683 | 683 | 683 | 683 | 0 |
| WHITE_PEARLS | 1,324 | 1,697 | 1,697 | 1,697 | 1,176 | 1,591 |

## Weak cases

- **orch_v3_newcore:** none
- **orch_v4q_n200000_lam0:** none
- **orch_v4q_n200000_lam1e-05:** none
- **orch_v4q_n200000_lam3e-05:** none
- **orch_v4q_n20000_lam3e-05:** black-swan-crash (+269,708 mean; of which VOUCHER_6800 -16,070; edge over orch_v3_newcore, orch_v4q_n200000_lam3e-05, orch_v4q_n200000_lam1e-05, orch_v4q_n200000_lam0, reference +23,702, well below its usual +42,994; beats reference on the one seed run)
- **reference:** busy-day (-3,118 mean; of which FRUIT_BASKET -5,196; loses money; behind orch_v3_newcore, orch_v4q_n20000_lam3e-05, orch_v4q_n200000_lam3e-05, orch_v4q_n200000_lam1e-05, orch_v4q_n200000_lam0 on the one seed run); golden-continues (-3,306 mean; of which GOLDEN_PEARLS -3,498; loses money; behind orch_v3_newcore, orch_v4q_n20000_lam3e-05, orch_v4q_n200000_lam3e-05, orch_v4q_n200000_lam1e-05, orch_v4q_n200000_lam0 on the one seed run); toxic-flow (-2,542 mean; of which BLUE_PEARLS -2,494; loses money; behind orch_v3_newcore, orch_v4q_n20000_lam3e-05, orch_v4q_n200000_lam3e-05, orch_v4q_n200000_lam1e-05, orch_v4q_n200000_lam0 on the one seed run); tellurium-storm (+44 mean; of which MANGOSTEEN -2,706; edge over orch_v3_newcore, orch_v4q_n20000_lam3e-05, orch_v4q_n200000_lam3e-05, orch_v4q_n200000_lam1e-05, orch_v4q_n200000_lam0 -426,540, well below its usual -247,528; behind orch_v3_newcore, orch_v4q_n20000_lam3e-05, orch_v4q_n200000_lam3e-05, orch_v4q_n200000_lam1e-05, orch_v4q_n200000_lam0 on the one seed run)
