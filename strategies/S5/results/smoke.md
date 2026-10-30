# Leaderboard: quick suite (seeds [1])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | EQ | 26,200 | golden-continues (15,232) | 15,232 | 0 | 6,127 | 0 | 0 |
| 2 | reference | -974 | golden-continues (-3,306) | -3,306 | 3 | 16,570 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| reference | 27,174 | [21,149, 33,209] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| EQ | 27,362 | 17,779 | 23,524 | 68,665 | 0 | 0.48 |

## Tier-weighted PnL by product

| Product | EQ | reference |
|---|---:|---:|
| AMETHYST | 562 | 275 |
| BLACK_PEARLS | 620 | 566 |
| BLUE_PEARLS | -496 | -1,103 |
| DRAGONFRUIT | 48 | 17 |
| FRUIT_BASKET | -1,883 | -2,294 |
| GOLDEN_PEARLS | -1,163 | -712 |
| GRANADILLA | -2,045 | -2,091 |
| JELLY | 2,443 | 5,562 |
| LYCHEE | -1,368 | -1,578 |
| MANGOSTEEN | -1,726 | -1,796 |
| PAPER_LANTERNS | 422 | 1,032 |
| PEANUT_BUTTER | 254 | 436 |
| PINK_PEARLS | 10,350 | -951 |
| TELLURIUM | 0 | 0 |
| TOFFEE_CAKE | 18,878 | 73 |
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
| WHITE_PEARLS | 1,303 | 1,591 |

## Weak cases

- **EQ:** none
- **reference:** busy-day (-3,118 mean; of which FRUIT_BASKET -5,196; loses money; behind EQ on the one seed run); golden-continues (-3,306 mean; of which GOLDEN_PEARLS -3,498; loses money; behind EQ on the one seed run); toxic-flow (-2,542 mean; of which BLUE_PEARLS -2,494; loses money; behind EQ on the one seed run)
