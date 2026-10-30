# Leaderboard: dev suite (seeds [1, 2])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | A2 | 34,040 | black-swan-squeeze (19,272) | 1,410 | 1 | 5,514 | 0 | 0 |
| 2 | EQ | 28,894 | mean-reversion-decay (17,307) | 12,146 | 0 | 6,510 | 0 | 0 |
| 3 | A3 | 28,323 | black-swan-squeeze (-1,636) | -43,040 | 1 | 5,808 | 0 | 0 |
| 4 | A1 | 21,990 | busy-day (11,967) | -13,218 | 0 | 5,974 | 0 | 0 |
| 5 | reference | -3,363 | busy-day (-10,063) | -26,522 | 35 | 18,864 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| EQ | 5,146 | [3,466, 6,720] |
| A3 | 5,717 | [3,246, 8,136] |
| A1 | 12,050 | [10,393, 13,810] |
| reference | 37,403 | [34,125, 41,348] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| EQ | 27,362 | 17,779 | 23,524 | 68,665 | 0 | 0.46 |
| A1 | 21,716 | 12,860 | 19,120 | 53,696 | 0 | 0.45 |
| A2 | 27,956 | 21,950 | 32,298 | 82,205 | 0 | 0.43 |
| A3 | 31,913 | 25,179 | 26,381 | 83,473 | 0 | 0.45 |

## Tier-weighted PnL by product

| Product | A2 | EQ | A3 | A1 | reference |
|---|---:|---:|---:|---:|---:|
| AMETHYST | 557 | 557 | 557 | 538 | 281 |
| BLACK_PEARLS | 371 | 803 | 775 | 770 | 721 |
| BLUE_PEARLS | -247 | -639 | -627 | -623 | -925 |
| DRAGONFRUIT | -81 | 49 | 49 | 48 | 13 |
| FRUIT_BASKET | 398 | 491 | -433 | 1,019 | 1,018 |
| GOLDEN_PEARLS | -1,547 | -1,569 | -1,569 | -1,565 | 33 |
| GRANADILLA | -726 | -1,039 | -1,038 | -1,039 | -1,082 |
| JELLY | 1,992 | 3,168 | 2,809 | 3,080 | 5,016 |
| LYCHEE | -235 | -696 | -703 | -563 | -850 |
| MANGOSTEEN | 177 | -999 | -1,014 | -921 | -1,065 |
| PAPER_LANTERNS | 390 | 642 | 929 | 704 | 667 |
| PEANUT_BUTTER | -1,734 | -2,204 | -886 | -3,296 | -7,875 |
| PINK_PEARLS | 9,085 | 11,022 | 7,465 | 9,619 | -519 |
| TELLURIUM | 0 | 0 | 0 | 0 | 0 |
| TOFFEE_CAKE | 25,311 | 18,386 | 21,139 | 13,330 | 201 |
| VOUCHER_6800 | 0 | 0 | 0 | 0 | 0 |
| VOUCHER_7000 | 0 | 0 | 0 | 0 | 0 |
| VOUCHER_7200 | 0 | 0 | 0 | 0 | 0 |
| VOUCHER_7300 | 0 | 0 | 0 | 0 | 0 |
| VOUCHER_7400 | 0 | 0 | 0 | 0 | 0 |
| VOUCHER_7500 | 0 | 0 | 0 | 0 | 0 |
| VOUCHER_7600 | 0 | 0 | 0 | 0 | 0 |
| VOUCHER_7750 | 0 | 0 | 0 | 0 | 0 |
| VOUCHER_7900 | 0 | 0 | 0 | 0 | 0 |
| VOUCHER_8100 | 0 | 0 | 0 | 0 | 0 |
| WHITE_PEARLS | 331 | 924 | 870 | 889 | 1,003 |

## Weak cases

- **A2:** black-swan-squeeze (+19,272 mean; of which PAPER_LANTERNS -5,744; edge over EQ, A1, A3, reference -319, well below its usual +14,458)
- **EQ:** none
- **A3:** black-swan-squeeze (-1,636 mean; of which PAPER_LANTERNS -9,084; loses money; edge over EQ, A1, A2, reference -26,454, well below its usual +5,748; seeds disagree (-43,040 to +39,767))
- **A1:** none
- **reference:** busy-day (-10,063 mean; of which PEANUT_BUTTER -9,878; loses money; behind EQ, A1, A2, A3 on every seed); quiet-day (-5,458 mean; of which PEANUT_BUTTER -6,891; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-18,730 to +7,816)); regular-day (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,601 to +44)); trends-continue (-2,718 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed); basket-dislocation (-2,996 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed); clustered-arrivals (-10,042 mean; of which PEANUT_BUTTER -12,535; loses money; behind EQ, A1, A2, A3 on every seed); correlation-breakdown (-8,042 mean; of which PEANUT_BUTTER -9,504; loses money; edge over EQ, A1, A2, A3 -130,889, well below its usual -35,140; behind EQ, A1, A2, A3 on every seed; seeds disagree (-16,789 to +706)); fat-tails (-1,100 mean; of which PEANUT_BUTTER -8,174; loses money; behind EQ, A1, A2, A3 on every seed); golden-continues (-4,149 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed); golden-flat (-3,115 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-7,108 to +878)); golden-reverses (-2,319 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-7,871 to +3,234)); heavy-flow (-8,210 mean; of which FRUIT_BASKET -5,790; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-17,796 to +1,376)); liquidity-drought (-2,322 mean; of which PEANUT_BUTTER -2,191; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-7,656 to +3,012)); lychee-trend (-2,883 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-10,090 to +4,324)); mean-reversion-decay (-3,301 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,988 to +386)); pearl-plug-weakens (-3,302 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,640 to +36)); pearl-sum-shift (-3,128 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed); regime-flip (-3,140 mean; of which PEANUT_BUTTER -11,589; loses money; behind EQ, A1, A2, A3 on every seed); smile-flattens (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,601 to +44)); smile-sticky-strike (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,601 to +44)); tellurium-informed (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,601 to +44)); tellurium-jumps-stick (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,601 to +44)); tellurium-whipsaw (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,601 to +44)); vol-clustering (-1,146 mean; of which PEANUT_BUTTER -8,469; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-3,094 to +802)); vol-crush (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,601 to +44)); vol-regime-switch (-756 mean; of which PEANUT_BUTTER -4,700; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-2,516 to +1,004)); vol-spike-skew (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,601 to +44)); anchor-break (-3,377 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,799 to +44)); black-swan-crash (-9,210 mean; of which PINK_PEARLS -18,328; loses money; edge over EQ, A1, A2, A3 -96,765, well below its usual -35,140; behind EQ, A1, A2, A3 on every seed; seeds disagree (-24,834 to +6,414)); flash-crash (-3,067 mean; of which PEANUT_BUTTER -9,488; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,884 to +750)); liquidity-spiral (-8,805 mean; of which PEANUT_BUTTER -8,122; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-21,878 to +4,268)); opening-gap (-3,740 mean; of which PEANUT_BUTTER -9,496; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-7,561 to +82)); quant-quake (-7,103 mean; of which PEANUT_BUTTER -9,504; loses money; edge over EQ, A1, A2, A3 -125,771, well below its usual -35,140; behind EQ, A1, A2, A3 on every seed; seeds disagree (-15,866 to +1,660)); tellurium-storm (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind EQ, A1, A2, A3 on every seed; seeds disagree (-6,601 to +44)); vol-explosion (-1,732 mean; of which PEANUT_BUTTER -8,432; loses money; behind EQ, A1, A2, A3 on every seed)
