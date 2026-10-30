# Leaderboard: dev suite (seeds [1, 2])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | S6 | 564 | black-swan-crash (-4,292) | -8,235 | 8 | 2,952 | 0 | 0 |
| 2 | basket_cap6 | 239 | black-swan-crash (-5,014) | -9,680 | 12 | 2,912 | 0 | 0 |
| 3 | no_trend | 25 | black-swan-crash (-2,414) | -4,422 | 13 | 2,312 | 0 | 0 |
| 4 | reference | -3,363 | busy-day (-10,063) | -26,522 | 35 | 18,864 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| basket_cap6 | 326 | [174, 469] |
| no_trend | 539 | [324, 865] |
| reference | 3,927 | [2,127, 5,799] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| S6 | 1,452 | 666 | 1,669 | 3,787 | 0 | 0.72 |
| basket_cap6 | 3,316 | 798 | 1,146 | 5,260 | 0 | 1.12 |
| no_trend | -296 | -296 | -614 | -1,206 | 0 | 1.73 |

## Tier-weighted PnL by product

| Product | S6 | basket_cap6 | no_trend | reference |
|---|---:|---:|---:|---:|
| AMETHYST | 0 | 0 | 0 | 281 |
| BLACK_PEARLS | 0 | 0 | 0 | 721 |
| BLUE_PEARLS | 0 | 0 | 0 | -925 |
| DRAGONFRUIT | -34 | 26 | -573 | 13 |
| FRUIT_BASKET | 376 | -104 | 376 | 1,018 |
| GOLDEN_PEARLS | 0 | 0 | 0 | 33 |
| GRANADILLA | 331 | 326 | 331 | -1,082 |
| JELLY | 0 | 0 | 0 | 5,016 |
| LYCHEE | 0 | 0 | 0 | -850 |
| MANGOSTEEN | -183 | -84 | -183 | -1,065 |
| PAPER_LANTERNS | 0 | 0 | 0 | 667 |
| PEANUT_BUTTER | 74 | 74 | 74 | -7,875 |
| PINK_PEARLS | 0 | 0 | 0 | -519 |
| TELLURIUM | 0 | 0 | 0 | 0 |
| TOFFEE_CAKE | 0 | 0 | 0 | 201 |
| VOUCHER_6800 | 0 | 0 | 0 | 0 |
| VOUCHER_7000 | 0 | 0 | 0 | 0 |
| VOUCHER_7200 | 0 | 0 | 0 | 0 |
| VOUCHER_7300 | 0 | 0 | 0 | 0 |
| VOUCHER_7400 | 0 | 0 | 0 | 0 |
| VOUCHER_7500 | 0 | 0 | 0 | 0 |
| VOUCHER_7600 | 0 | 0 | 0 | 0 |
| VOUCHER_7750 | 0 | 0 | 0 | 0 |
| VOUCHER_7900 | 0 | 0 | 0 | 0 |
| VOUCHER_8100 | 0 | 0 | 0 | 0 |
| WHITE_PEARLS | 0 | 0 | 0 | 1,003 |

## Weak cases

- **S6:** busy-day (-231 mean; of which FRUIT_BASKET -1,092; loses money; edge over basket_cap6, no_trend, reference +3,404, well above its usual +1,241; beats reference on every seed; seeds disagree (-468 to +6)); clustered-arrivals (-207 mean; of which FRUIT_BASKET -1,581; loses money; edge over basket_cap6, no_trend, reference +3,509, well above its usual +1,241; beats reference on every seed; seeds disagree (-608 to +194)); heavy-flow (-1,146 mean; of which FRUIT_BASKET -3,544; loses money); momentum-crash (+470 mean; of which MANGOSTEEN -236; edge over basket_cap6, no_trend, reference -553, well below its usual +1,241; behind reference on every seed); one-sided-flow (+100 mean; of which DRAGONFRUIT -475; edge over basket_cap6, no_trend, reference -3,837, well below its usual +1,241; seeds disagree (-302 to +502)); toxic-flow (+1,030 mean; of which GRANADILLA -1,179; edge over basket_cap6, no_trend, reference -4,267, well below its usual +1,241; seeds disagree (-364 to +2,425)); black-swan-crash (-4,292 mean; of which DRAGONFRUIT -2,335; loses money); liquidity-spiral (-2,030 mean; of which DRAGONFRUIT -2,087; loses money)
- **basket_cap6:** busy-day (-164 mean; of which FRUIT_BASKET -896; loses money; edge over S6, no_trend, reference +3,492, well above its usual +741; beats reference on every seed; seeds disagree (-609 to +280)); clustered-arrivals (-864 mean; of which FRUIT_BASKET -2,245; loses money; edge over S6, no_trend, reference +2,633, well above its usual +741; beats reference on every seed; seeds disagree (-1,968 to +242)); momentum-crash (+92 mean; of which FRUIT_BASKET -342; edge over S6, no_trend, reference -1,057, well below its usual +741; behind reference on every seed; seeds disagree (-403 to +586)); one-sided-flow (-214 mean; of which DRAGONFRUIT -406; loses money; edge over S6, no_trend, reference -4,255, well below its usual +741; seeds disagree (-930 to +504)); toxic-flow (+1,150 mean; of which GRANADILLA -1,346; edge over S6, no_trend, reference -4,108, well below its usual +741; seeds disagree (-962 to +3,262)); vol-clustering (-488 mean; of which FRUIT_BASKET -737; loses money); vol-regime-switch (-434 mean; of which FRUIT_BASKET -1,224; loses money); black-swan-crash (-5,014 mean; of which FRUIT_BASKET -2,244; loses money); flash-crash (-268 mean; of which FRUIT_BASKET -356; loses money; seeds disagree (-1,266 to +731)); liquidity-spiral (-2,518 mean; of which DRAGONFRUIT -2,100; loses money); opening-gap (-120 mean; of which FRUIT_BASKET -396; loses money; beats reference on every seed; seeds disagree (-410 to +170)); quant-quake (-19 mean; of which FRUIT_BASKET -452; loses money; edge over S6, no_trend, reference +2,254, well above its usual +741; seeds disagree (-628 to +590))
- **no_trend:** busy-day (-676 mean; of which DRAGONFRUIT -1,416; loses money; edge over S6, basket_cap6, reference +2,810, well above its usual +753; beats reference on every seed; seeds disagree (-2,170 to +818)); quiet-day (-258 mean; of which DRAGONFRUIT -551; loses money); clustered-arrivals (-242 mean; of which FRUIT_BASKET -1,581; loses money; edge over S6, basket_cap6, reference +3,463, well above its usual +753; beats reference on every seed; seeds disagree (-1,092 to +610)); heavy-flow (-1,578 mean; of which FRUIT_BASKET -3,544; loses money; seeds disagree (-3,192 to +36)); liquidity-drought (-18 mean; of which MANGOSTEEN -441; loses money; seeds disagree (-2,165 to +2,130)); momentum-crash (+38 mean; of which DRAGONFRUIT -515; edge over S6, basket_cap6, reference -1,129, well below its usual +753; behind reference on every seed; seeds disagree (-1,378 to +1,454)); one-sided-flow (-271 mean; of which DRAGONFRUIT -846; loses money; edge over S6, basket_cap6, reference -4,332, well below its usual +753; seeds disagree (-1,362 to +821)); toxic-flow (+511 mean; of which GRANADILLA -1,179; edge over S6, basket_cap6, reference -4,959, well below its usual +753); black-swan-crash (-2,414 mean; of which PEANUT_BUTTER -1,233; loses money; edge over S6, basket_cap6, reference +3,759, well above its usual +753); flash-crash (-54 mean; of which DRAGONFRUIT -696; loses money; seeds disagree (-1,237 to +1,129)); liquidity-spiral (-467 mean; of which DRAGONFRUIT -524; loses money; edge over S6, basket_cap6, reference +3,984, well above its usual +753; seeds disagree (-2,983 to +2,050)); quant-quake (-73 mean; of which DRAGONFRUIT -515; loses money; seeds disagree (-1,374 to +1,228)); vol-explosion (-138 mean; of which DRAGONFRUIT -638; loses money; seeds disagree (-1,398 to +1,124))
- **reference:** busy-day (-10,063 mean; of which PEANUT_BUTTER -9,878; loses money; edge over S6, basket_cap6, no_trend -9,706, well below its usual -2,734; behind S6, basket_cap6, no_trend on every seed); quiet-day (-5,458 mean; of which PEANUT_BUTTER -6,891; loses money; seeds disagree (-18,730 to +7,816)); regular-day (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,601 to +44)); trends-continue (-2,718 mean; of which PEANUT_BUTTER -9,504; loses money); basket-dislocation (-2,996 mean; of which PEANUT_BUTTER -9,504; loses money); clustered-arrivals (-10,042 mean; of which PEANUT_BUTTER -12,535; loses money; edge over S6, basket_cap6, no_trend -9,605, well below its usual -2,734; behind S6, basket_cap6, no_trend on every seed); correlation-breakdown (-8,042 mean; of which PEANUT_BUTTER -9,504; loses money; edge over S6, basket_cap6, no_trend -8,241, well below its usual -2,734; seeds disagree (-16,789 to +706)); fat-tails (-1,100 mean; of which PEANUT_BUTTER -8,174; loses money); golden-continues (-4,149 mean; of which PEANUT_BUTTER -9,504; loses money; behind S6, basket_cap6, no_trend on every seed); golden-flat (-3,115 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-7,108 to +878)); golden-reverses (-2,319 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-7,871 to +3,234)); heavy-flow (-8,210 mean; of which FRUIT_BASKET -5,790; loses money; edge over S6, basket_cap6, no_trend -7,309, well below its usual -2,734; seeds disagree (-17,796 to +1,376)); liquidity-drought (-2,322 mean; of which PEANUT_BUTTER -2,191; loses money; seeds disagree (-7,656 to +3,012)); lychee-trend (-2,883 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-10,090 to +4,324)); mean-reversion-decay (-3,301 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,988 to +386)); pearl-plug-weakens (-3,302 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,640 to +36)); pearl-sum-shift (-3,128 mean; of which PEANUT_BUTTER -9,504; loses money); regime-flip (-3,140 mean; of which PEANUT_BUTTER -11,589; loses money; behind S6, basket_cap6, no_trend on every seed); smile-flattens (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,601 to +44)); smile-sticky-strike (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,601 to +44)); tellurium-informed (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,601 to +44)); tellurium-jumps-stick (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,601 to +44)); tellurium-whipsaw (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,601 to +44)); vol-clustering (-1,146 mean; of which PEANUT_BUTTER -8,469; loses money; seeds disagree (-3,094 to +802)); vol-crush (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,601 to +44)); vol-regime-switch (-756 mean; of which PEANUT_BUTTER -4,700; loses money; seeds disagree (-2,516 to +1,004)); vol-spike-skew (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,601 to +44)); anchor-break (-3,377 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,799 to +44)); black-swan-crash (-9,210 mean; of which PINK_PEARLS -18,328; loses money; seeds disagree (-24,834 to +6,414)); flash-crash (-3,067 mean; of which PEANUT_BUTTER -9,488; loses money; seeds disagree (-6,884 to +750)); liquidity-spiral (-8,805 mean; of which PEANUT_BUTTER -8,122; loses money; edge over S6, basket_cap6, no_trend -7,134, well below its usual -2,734; seeds disagree (-21,878 to +4,268)); opening-gap (-3,740 mean; of which PEANUT_BUTTER -9,496; loses money; seeds disagree (-7,561 to +82)); quant-quake (-7,103 mean; of which PEANUT_BUTTER -9,504; loses money; edge over S6, basket_cap6, no_trend -7,192, well below its usual -2,734; seeds disagree (-15,866 to +1,660)); tellurium-storm (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; seeds disagree (-6,601 to +44)); vol-explosion (-1,732 mean; of which PEANUT_BUTTER -8,432; loses money)
