# Leaderboard: quick suite (seeds [1])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | S6 | 475 | black-swan-crash (-350) | -350 | 1 | 2,648 | 0 | 0 |
| 2 | reference | -974 | golden-continues (-3,306) | -3,306 | 3 | 16,570 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| reference | 1,449 | [91, 2,722] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| S6 | 1,452 | 666 | 1,669 | 3,787 | 0 | 0.35 |

## Tier-weighted PnL by product

| Product | S6 | reference |
|---|---:|---:|
| AMETHYST | 0 | 275 |
| BLACK_PEARLS | 0 | 566 |
| BLUE_PEARLS | 0 | -1,103 |
| DRAGONFRUIT | 1,546 | 17 |
| FRUIT_BASKET | -1,678 | -2,294 |
| GOLDEN_PEARLS | 0 | -712 |
| GRANADILLA | 1,187 | -2,091 |
| JELLY | 0 | 5,562 |
| LYCHEE | 0 | -1,578 |
| MANGOSTEEN | -632 | -1,796 |
| PAPER_LANTERNS | 0 | 1,032 |
| PEANUT_BUTTER | 52 | 436 |
| PINK_PEARLS | 0 | -951 |
| TELLURIUM | 0 | 0 |
| TOFFEE_CAKE | 0 | 73 |
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
| WHITE_PEARLS | 0 | 1,591 |

## Weak cases

- **S6:** black-swan-crash (-350 mean; of which DRAGONFRUIT -894; loses money; edge over reference -6,763, well below its usual +782; behind reference on the one seed run; behind reference on the one seed run)
- **reference:** busy-day (-3,118 mean; of which FRUIT_BASKET -5,196; loses money; behind S6 on the one seed run); golden-continues (-3,306 mean; of which GOLDEN_PEARLS -3,498; loses money; behind S6 on the one seed run); toxic-flow (-2,542 mean; of which BLUE_PEARLS -2,494; loses money; edge over S6 -4,966, well below its usual -782; behind S6 on the one seed run)
