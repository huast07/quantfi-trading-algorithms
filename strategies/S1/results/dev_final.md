# Leaderboard: dev suite (seeds [1, 2])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | S1 | 38,037 | liquidity-spiral (15,638) | 14,598 | 5 | 4,660 | 0 | 0 |
| 2 | reference | -3,363 | busy-day (-10,063) | -26,522 | 35 | 18,864 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| reference | 41,400 | [37,982, 45,127] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 32,494 | 35,658 | 27,994 | 96,146 | 0 | 5.06 |

## Tier-weighted PnL by product

| Product | S1 | reference |
|---|---:|---:|
| AMETHYST | 587 | 281 |
| BLACK_PEARLS | 787 | 721 |
| BLUE_PEARLS | -347 | -925 |
| DRAGONFRUIT | 96 | 13 |
| FRUIT_BASKET | 44 | 1,018 |
| GOLDEN_PEARLS | 1,803 | 33 |
| GRANADILLA | -941 | -1,082 |
| JELLY | 3,619 | 5,016 |
| LYCHEE | -613 | -850 |
| MANGOSTEEN | -309 | -1,065 |
| PAPER_LANTERNS | 710 | 667 |
| PEANUT_BUTTER | 250 | -7,875 |
| PINK_PEARLS | 438 | -519 |
| TELLURIUM | 0 | 0 |
| TOFFEE_CAKE | 31,224 | 201 |
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
| WHITE_PEARLS | 688 | 1,003 |

## Weak cases

- **S1:** one-sided-flow (+38,048 mean; of which GRANADILLA -1,094; edge over reference +25,753, well below its usual +41,051); toxic-flow (+34,712 mean; of which GRANADILLA -1,514; edge over reference +20,482, well below its usual +41,051; beats reference on every seed; beats reference on every seed); vol-regime-switch (+24,401 mean; of which PEANUT_BUTTER -1,050; well below its average of +38,496; edge over reference +25,157, well below its usual +41,051; beats reference on every seed; beats reference on every seed); black-swan-squeeze (+21,289 mean; of which LYCHEE -1,046; well below its average of +38,496; edge over reference +16,979, well below its usual +41,051; beats reference on every seed; beats reference on every seed); liquidity-spiral (+15,638 mean; of which GRANADILLA -1,065; well below its average of +38,496; edge over reference +24,443, well below its usual +41,051; beats reference on every seed; beats reference on every seed)
- **reference:** busy-day (-10,063 mean; of which PEANUT_BUTTER -9,878; loses money; behind S1 on every seed); quiet-day (-5,458 mean; of which PEANUT_BUTTER -6,891; loses money; behind S1 on every seed; seeds disagree (-18,730 to +7,816)); regular-day (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,601 to +44)); trends-continue (-2,718 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed); basket-dislocation (-2,996 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed); clustered-arrivals (-10,042 mean; of which PEANUT_BUTTER -12,535; loses money; behind S1 on every seed); correlation-breakdown (-8,042 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-16,789 to +706)); fat-tails (-1,100 mean; of which PEANUT_BUTTER -8,174; loses money; behind S1 on every seed); golden-continues (-4,149 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed); golden-flat (-3,115 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-7,108 to +878)); golden-reverses (-2,319 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-7,871 to +3,234)); heavy-flow (-8,210 mean; of which FRUIT_BASKET -5,790; loses money; behind S1 on every seed; seeds disagree (-17,796 to +1,376)); liquidity-drought (-2,322 mean; of which PEANUT_BUTTER -2,191; loses money; behind S1 on every seed; seeds disagree (-7,656 to +3,012)); lychee-trend (-2,883 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-10,090 to +4,324)); mean-reversion-decay (-3,301 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,988 to +386)); pearl-plug-weakens (-3,302 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,640 to +36)); pearl-sum-shift (-3,128 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed); regime-flip (-3,140 mean; of which PEANUT_BUTTER -11,589; loses money; behind S1 on every seed); smile-flattens (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,601 to +44)); smile-sticky-strike (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,601 to +44)); tellurium-informed (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,601 to +44)); tellurium-jumps-stick (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,601 to +44)); tellurium-whipsaw (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,601 to +44)); vol-clustering (-1,146 mean; of which PEANUT_BUTTER -8,469; loses money; behind S1 on every seed; seeds disagree (-3,094 to +802)); vol-crush (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,601 to +44)); vol-regime-switch (-756 mean; of which PEANUT_BUTTER -4,700; loses money; edge over S1 -25,157, well above its usual -41,051; behind S1 on every seed; seeds disagree (-2,516 to +1,004)); vol-spike-skew (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,601 to +44)); anchor-break (-3,377 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,799 to +44)); black-swan-crash (-9,210 mean; of which PINK_PEARLS -18,328; loses money; edge over S1 -124,437, well below its usual -41,051; behind S1 on every seed; seeds disagree (-24,834 to +6,414)); flash-crash (-3,067 mean; of which PEANUT_BUTTER -9,488; loses money; behind S1 on every seed; seeds disagree (-6,884 to +750)); liquidity-spiral (-8,805 mean; of which PEANUT_BUTTER -8,122; loses money; edge over S1 -24,443, well above its usual -41,051; behind S1 on every seed; seeds disagree (-21,878 to +4,268)); opening-gap (-3,740 mean; of which PEANUT_BUTTER -9,496; loses money; behind S1 on every seed; seeds disagree (-7,561 to +82)); quant-quake (-7,103 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-15,866 to +1,660)); tellurium-storm (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind S1 on every seed; seeds disagree (-6,601 to +44)); vol-explosion (-1,732 mean; of which PEANUT_BUTTER -8,432; loses money; behind S1 on every seed)
