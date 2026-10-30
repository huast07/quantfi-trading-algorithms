# Leaderboard: dev suite (seeds [1, 2])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | orch_v3 | 167,198 | quiet-day (128,133) | 80,834 | 1 | 10,274 | 0 | 0 |
| 2 | S4 | 62,624 | quiet-day (35,351) | 5,512 | 4 | 16,221 | 0 | 0 |
| 3 | S3 | 53,786 | wide-spreads (30,940) | 7,893 | 7 | 3,098 | 0 | 0 |
| 4 | reference | -3,363 | busy-day (-10,063) | -26,522 | 35 | 18,864 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| S4 | 104,573 | [99,775, 109,575] |
| S3 | 113,412 | [101,254, 124,696] |
| reference | 170,561 | [157,936, 183,382] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| orch_v3 | 153,636 | 132,665 | 131,391 | 417,692 | 0 | 1.42 |
| S3 | 62,542 | 54,232 | 45,624 | 162,398 | 0 | 0.42 |
| S4 | 49,974 | 27,534 | 44,398 | 121,906 | 0 | 0.26 |

## Tier-weighted PnL by product

| Product | orch_v3 | S4 | S3 | reference |
|---|---:|---:|---:|---:|
| AMETHYST | 587 | 0 | 0 | 281 |
| BLACK_PEARLS | 2,020 | 0 | 0 | 721 |
| BLUE_PEARLS | 568 | 0 | 0 | -925 |
| DRAGONFRUIT | 0 | 0 | 0 | 13 |
| FRUIT_BASKET | 0 | 0 | 0 | 1,018 |
| GOLDEN_PEARLS | 1,807 | 0 | 0 | 33 |
| GRANADILLA | 0 | 0 | 0 | -1,082 |
| JELLY | 1,866 | 0 | 0 | 5,016 |
| LYCHEE | -3,752 | 0 | -3,752 | -850 |
| MANGOSTEEN | 0 | 0 | 0 | -1,065 |
| PAPER_LANTERNS | 710 | 0 | 0 | 667 |
| PEANUT_BUTTER | 0 | 0 | 0 | -7,875 |
| PINK_PEARLS | 11,318 | 0 | 0 | -519 |
| TELLURIUM | 62,624 | 62,624 | 0 | 0 |
| TOFFEE_CAKE | 31,224 | 0 | 0 | 201 |
| VOUCHER_6800 | 2,706 | 0 | 2,706 | 0 |
| VOUCHER_7000 | 5,486 | 0 | 5,486 | 0 |
| VOUCHER_7200 | 8,640 | 0 | 8,640 | 0 |
| VOUCHER_7300 | 12,067 | 0 | 12,067 | 0 |
| VOUCHER_7400 | 3,635 | 0 | 3,635 | 0 |
| VOUCHER_7500 | 9,095 | 0 | 9,095 | 0 |
| VOUCHER_7600 | 6,429 | 0 | 6,429 | 0 |
| VOUCHER_7750 | 4,443 | 0 | 4,443 | 0 |
| VOUCHER_7900 | 3,466 | 0 | 3,466 | 0 |
| VOUCHER_8100 | 1,571 | 0 | 1,571 | 0 |
| WHITE_PEARLS | 688 | 0 | 0 | 1,003 |

## Weak cases

- **orch_v3:** quiet-day (+128,133 mean; of which LYCHEE -4,349; well below its average of +173,551; beats S3, S4, reference on every seed; beats reference on every seed)
- **S4:** quiet-day (+35,351 mean; of which TELLURIUM +35,351; well below its average of +64,877; beats reference on every seed); correlation-breakdown (+60,884 mean; of which TELLURIUM +60,884; edge over orch_v3, S3, reference -46,427, well below its usual -9,700; beats reference on every seed); black-swan-crash (+53,907 mean; of which TELLURIUM +53,907; edge over orch_v3, S3, reference -63,619, well below its usual -9,700; beats reference on every seed); quant-quake (+60,884 mean; of which TELLURIUM +60,884; edge over orch_v3, S3, reference -43,922, well below its usual -9,700; beats reference on every seed)
- **S3:** correlation-breakdown (+54,635 mean; of which LYCHEE -3,208; edge over orch_v3, S4, reference -54,759, well below its usual -25,891; beats reference on every seed); wide-spreads (+30,940 mean; of which LYCHEE -2,095; well below its average of +52,734; beats reference on every seed); black-swan-squeeze (+38,572 mean; of which LYCHEE -26,795; well below its average of +52,734; edge over orch_v3, S4, reference -51,601, well below its usual -25,891; beats reference on every seed); liquidity-spiral (+37,060 mean; of which LYCHEE -15,288; well below its average of +52,734; beats reference on every seed); opening-gap (+42,532 mean; of which LYCHEE -8,038; well below its average of +52,734; beats reference on every seed); quant-quake (+54,230 mean; of which LYCHEE -2,948; edge over orch_v3, S4, reference -52,794, well below its usual -25,891; beats reference on every seed); tellurium-storm (+54,635 mean; of which LYCHEE -3,208; edge over orch_v3, S4, reference -131,289, well below its usual -25,891; beats reference on every seed)
- **reference:** busy-day (-10,063 mean; of which PEANUT_BUTTER -9,878; loses money; edge over orch_v3, S3, S4 -123,014, well below its usual -99,609; behind orch_v3, S3, S4 on every seed); quiet-day (-5,458 mean; of which PEANUT_BUTTER -6,891; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-18,730 to +7,816)); regular-day (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,601 to +44)); trends-continue (-2,718 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed); basket-dislocation (-2,996 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed); clustered-arrivals (-10,042 mean; of which PEANUT_BUTTER -12,535; loses money; behind orch_v3, S3, S4 on every seed); correlation-breakdown (-8,042 mean; of which PEANUT_BUTTER -9,504; loses money; edge over orch_v3, S3, S4 -138,328, well below its usual -99,609; behind orch_v3, S3, S4 on every seed; seeds disagree (-16,789 to +706)); fat-tails (-1,100 mean; of which PEANUT_BUTTER -8,174; loses money; behind orch_v3, S3, S4 on every seed); golden-continues (-4,149 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed); golden-flat (-3,115 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-7,108 to +878)); golden-reverses (-2,319 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-7,871 to +3,234)); heavy-flow (-8,210 mean; of which FRUIT_BASKET -5,790; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-17,796 to +1,376)); liquidity-drought (-2,322 mean; of which PEANUT_BUTTER -2,191; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-7,656 to +3,012)); lychee-trend (-2,883 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-10,090 to +4,324)); mean-reversion-decay (-3,301 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,988 to +386)); pearl-plug-weakens (-3,302 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,640 to +36)); pearl-sum-shift (-3,128 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed); regime-flip (-3,140 mean; of which PEANUT_BUTTER -11,589; loses money; behind orch_v3, S3, S4 on every seed); smile-flattens (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,601 to +44)); smile-sticky-strike (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,601 to +44)); tellurium-informed (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,601 to +44)); tellurium-jumps-stick (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,601 to +44)); tellurium-whipsaw (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,601 to +44)); vol-clustering (-1,146 mean; of which PEANUT_BUTTER -8,469; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-3,094 to +802)); vol-crush (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,601 to +44)); vol-regime-switch (-756 mean; of which PEANUT_BUTTER -4,700; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-2,516 to +1,004)); vol-spike-skew (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,601 to +44)); anchor-break (-3,377 mean; of which PEANUT_BUTTER -9,504; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,799 to +44)); black-swan-crash (-9,210 mean; of which PINK_PEARLS -18,328; loses money; edge over orch_v3, S3, S4 -147,776, well below its usual -99,609; behind orch_v3, S3, S4 on every seed; seeds disagree (-24,834 to +6,414)); flash-crash (-3,067 mean; of which PEANUT_BUTTER -9,488; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,884 to +750)); liquidity-spiral (-8,805 mean; of which PEANUT_BUTTER -8,122; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-21,878 to +4,268)); opening-gap (-3,740 mean; of which PEANUT_BUTTER -9,496; loses money; behind orch_v3, S3, S4 on every seed; seeds disagree (-7,561 to +82)); quant-quake (-7,103 mean; of which PEANUT_BUTTER -9,504; loses money; edge over orch_v3, S3, S4 -134,572, well below its usual -99,609; behind orch_v3, S3, S4 on every seed; seeds disagree (-15,866 to +1,660)); tellurium-storm (-3,278 mean; of which PEANUT_BUTTER -9,504; loses money; edge over orch_v3, S3, S4 -208,506, well below its usual -99,609; behind orch_v3, S3, S4 on every seed; seeds disagree (-6,601 to +44)); vol-explosion (-1,732 mean; of which PEANUT_BUTTER -8,432; loses money; behind orch_v3, S3, S4 on every seed)
