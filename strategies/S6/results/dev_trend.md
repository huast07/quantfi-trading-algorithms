# Leaderboard: dev suite (seeds [1, 2])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | trend_winsor | 1,261 | black-swan-crash (-3,612) | -6,566 | 3 | 3,656 | 0 | 0 |
| 2 | S6 | 1,238 | black-swan-crash (-4,292) | -8,235 | 3 | 4,033 | 0 | 0 |
| 3 | reference | -2,364 | black-swan-crash (-9,210) | -24,834 | 5 | 22,937 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| S6 | 23 | [0, 68] |
| reference | 3,625 | [2,503, 4,746] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| S6 | 1,452 | 666 | 1,669 | 3,787 | 0 | 0.98 |
| trend_winsor | 1,452 | 666 | 1,669 | 3,787 | 0 | 0.61 |

## Tier-weighted PnL by product

| Product | trend_winsor | S6 | reference |
|---|---:|---:|---:|
| AMETHYST | 0 | 0 | 279 |
| BLACK_PEARLS | 0 | 0 | 792 |
| BLUE_PEARLS | 0 | 0 | -20 |
| DRAGONFRUIT | 398 | 375 | 333 |
| FRUIT_BASKET | 696 | 696 | 2,081 |
| GOLDEN_PEARLS | 0 | 0 | -202 |
| GRANADILLA | 255 | 255 | -960 |
| JELLY | 0 | 0 | 6,166 |
| LYCHEE | 0 | 0 | -1,001 |
| MANGOSTEEN | -157 | -157 | -878 |
| PAPER_LANTERNS | 0 | 0 | 1,448 |
| PEANUT_BUTTER | 69 | 69 | -9,603 |
| PINK_PEARLS | 0 | 0 | -923 |
| TELLURIUM | 0 | 0 | 0 |
| TOFFEE_CAKE | 0 | 0 | -481 |
| VOUCHER_6800 | 0 | 0 | 0 |
| VOUCHER_7000 | 0 | 0 | 0 |
| VOUCHER_7200 | 0 | 0 | 0 |
| VOUCHER_7300 | 0 | 0 | 0 |
| VOUCHER_7400 | 0 | 0 | 0 |
| VOUCHER_7500 | 0 | 0 | 0 |
| VOUCHER_7600 | 0 | 0 | 0 |
| VOUCHER_7750 | 0 | 0 | 0 |
| VOUCHER_7900 | 0 | 0 | 0 |
| VOUCHER_8100 | 0 | 0 | 0 |
| WHITE_PEARLS | 0 | 0 | 602 |

## Weak cases

- **trend_winsor:** black-swan-crash (-3,612 mean; of which DRAGONFRUIT -1,655; loses money); liquidity-spiral (-2,030 mean; of which DRAGONFRUIT -2,087; loses money); momentum-crash (+470 mean; of which MANGOSTEEN -236; edge over S6, reference -1,235, well below its usual +1,920; behind reference on every seed)
- **S6:** black-swan-crash (-4,292 mean; of which DRAGONFRUIT -2,335; loses money); liquidity-spiral (-2,030 mean; of which DRAGONFRUIT -2,087; loses money; edge over trend_winsor, reference +3,388, well above its usual +1,750); momentum-crash (+470 mean; of which MANGOSTEEN -236; edge over trend_winsor, reference -1,235, well below its usual +1,750; behind reference on every seed)
- **reference:** black-swan-crash (-9,210 mean; of which PINK_PEARLS -18,328; loses money; seeds disagree (-24,834 to +6,414)); liquidity-spiral (-8,805 mean; of which PEANUT_BUTTER -8,122; loses money; edge over S6, trend_winsor -6,776, well below its usual -3,670; seeds disagree (-21,878 to +4,268)); trends-continue (-2,718 mean; of which PEANUT_BUTTER -9,504; loses money; behind S6, trend_winsor on every seed); regime-flip (-3,140 mean; of which PEANUT_BUTTER -11,589; loses money; behind S6, trend_winsor on every seed); flash-crash (-3,067 mean; of which PEANUT_BUTTER -9,488; loses money; seeds disagree (-6,884 to +750))
