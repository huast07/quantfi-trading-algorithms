# Leaderboard: quick suite (seeds [1])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | S1 | 51,222 | toxic-flow (28,658) | 28,658 | 0 | 5,831 | 0 | 0 |
| 2 | reference | -974 | golden-continues (-3,306) | -3,306 | 3 | 16,570 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| reference | 52,196 | [33,071, 71,000] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 18,238 | 33,285 | 35,463 | 86,986 | 0 | 3.34 |

## Tier-weighted PnL by product

| Product | S1 | reference |
|---|---:|---:|
| AMETHYST | 582 | 275 |
| BLACK_PEARLS | 1,720 | 566 |
| BLUE_PEARLS | -4 | -1,103 |
| DRAGONFRUIT | 721 | 17 |
| FRUIT_BASKET | 2,692 | -2,294 |
| GOLDEN_PEARLS | 1,393 | -712 |
| GRANADILLA | -1,235 | -2,091 |
| JELLY | 3,161 | 5,562 |
| LYCHEE | 2,824 | -1,578 |
| MANGOSTEEN | -189 | -1,796 |
| PAPER_LANTERNS | 2,116 | 1,032 |
| PEANUT_BUTTER | 1,250 | 436 |
| PINK_PEARLS | 835 | -951 |
| TELLURIUM | 0 | 0 |
| TOFFEE_CAKE | 33,420 | 73 |
| VOUCHER_6800 | 0 | 0 |
| VOUCHER_7000 | 0 | 0 |
| VOUCHER_7200 | 0 | 0 |
| VOUCHER_7300 | 0 | 0 |
| VOUCHER_7400 | 0 | 0 |
| VOUCHER_7500 | 0 | 0 |
| VOUCHER_7600 | 0 | 0 |
| VOUCHER_7750 | 0 | 0 |
| VOUCHER_7900 | 0 | 0 |
| VOUCHER_8100 | 0 | 0 |
| WHITE_PEARLS | 1,935 | 1,591 |

## Weak cases

- **S1:** none
- **reference:** busy-day (-3,118 mean; of which FRUIT_BASKET -5,196; loses money; behind S1 on the one seed run); golden-continues (-3,306 mean; of which GOLDEN_PEARLS -3,498; loses money; behind S1 on the one seed run); toxic-flow (-2,542 mean; of which BLUE_PEARLS -2,494; loses money; behind S1 on the one seed run)
