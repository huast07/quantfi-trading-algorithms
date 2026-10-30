# Leaderboard: heldout suite (seeds [3, 4, 5])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | orch_v4r_fs0_nojump | 148,792 | quiet-day (120,699) | 80,674 | 1 | 9,707 | 0 | 0 |
| 2 | orch_v3_newcore | 147,033 | quiet-day (119,057) | 83,670 | 1 | 9,461 | 0 | 0 |
| 3 | orch_v4s | 143,778 | quiet-day (117,572) | 81,882 | 1 | 9,723 | 0 | 0 |
| 4 | reference | -5,680 | black-swan-squeeze (-37,439) | -66,139 | 37 | 22,839 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| orch_v3_newcore | 1,760 | [859, 2,570] |
| orch_v4s | 5,014 | [4,219, 5,781] |
| reference | 154,472 | [144,814, 164,363] |

## Tier-weighted PnL by product

| Product | orch_v4r_fs0_nojump | orch_v3_newcore | orch_v4s | reference |
|---|---:|---:|---:|---:|
| AMETHYST | 542 | 542 | 542 | 264 |
| BLACK_PEARLS | -261 | -259 | -258 | -224 |
| BLUE_PEARLS | 2,623 | 2,623 | 2,623 | -25 |
| DRAGONFRUIT | -424 | 0 | -424 | -220 |
| FRUIT_BASKET | 0 | 0 | 0 | 194 |
| GOLDEN_PEARLS | 1,642 | 1,637 | 1,642 | 436 |
| GRANADILLA | 276 | 0 | 276 | 697 |
| JELLY | 3,316 | 765 | 299 | 3,316 |
| LYCHEE | -3,486 | -3,655 | -3,443 | -10 |
| MANGOSTEEN | 0 | 0 | 0 | -646 |
| PAPER_LANTERNS | 828 | 817 | 828 | 618 |
| PEANUT_BUTTER | 35 | 0 | 0 | -10,400 |
| PINK_PEARLS | 10,855 | 10,855 | 10,855 | 391 |
| TELLURIUM | 49,170 | 49,170 | 49,170 | 0 |
| TOFFEE_CAKE | 34,532 | 34,532 | 34,532 | 885 |
| VOUCHER_6800 | 2,021 | 2,022 | 0 | 0 |
| VOUCHER_7000 | 5,374 | 5,374 | 5,377 | 0 |
| VOUCHER_7200 | 4,795 | 4,795 | 4,796 | 0 |
| VOUCHER_7300 | 6,622 | 6,622 | 6,624 | 0 |
| VOUCHER_7400 | 6,216 | 6,333 | 6,219 | 0 |
| VOUCHER_7500 | 5,263 | 5,263 | 5,263 | 0 |
| VOUCHER_7600 | 7,224 | 7,223 | 7,225 | 0 |
| VOUCHER_7750 | 7,151 | 7,149 | 7,154 | 0 |
| VOUCHER_7900 | 4,932 | 4,933 | 4,933 | 0 |
| VOUCHER_8100 | 565 | 748 | 565 | 0 |
| WHITE_PEARLS | -1,019 | -459 | -1,019 | -955 |

## Weak cases

- **orch_v4r_fs0_nojump:** quiet-day (+120,699 mean; of which LYCHEE -3,508; well below its average of +162,748; edge over orch_v3_newcore, orch_v4s, reference +41,602, well below its usual +58,720; beats orch_v3_newcore, orch_v4s, reference on every seed; beats reference on every seed)
- **orch_v3_newcore:** quiet-day (+119,057 mean; of which LYCHEE -3,665; well below its average of +160,985; edge over orch_v4r_fs0_nojump, orch_v4s, reference +39,413, well below its usual +56,370; beats reference on every seed)
- **orch_v4s:** quiet-day (+117,572 mean; of which LYCHEE -3,666; edge over orch_v3_newcore, orch_v4r_fs0_nojump, reference +37,434, well below its usual +50,997; beats reference on every seed)
- **reference:** busy-day (-7,892 mean; of which PEANUT_BUTTER -12,925; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-30,716 to +15,644)); regular-day (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,180 to +3,751)); regular-day-varied (-5,180 mean; of which PEANUT_BUTTER -8,614; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-22,376 to +7,233)); trends-continue (-8,044 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-23,706 to +5,455)); basket-dislocation (-7,226 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-23,704 to +3,651)); clustered-arrivals (-4,897 mean; of which PEANUT_BUTTER -7,436; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,815 to +5,116)); correlation-breakdown (-3,713 mean; of which PEANUT_BUTTER -12,363; loses money; edge over orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s -263,947, well below its usual -166,086; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-27,190 to +13,726)); fat-tails (-8,558 mean; of which PEANUT_BUTTER -12,987; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-35,588 to +10,707)); golden-continues (-7,121 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,258 to +4,684)); golden-flat (-7,294 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,238 to +3,751)); golden-reverses (-7,022 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,026 to +3,833)); intraday-seasonality (-2,671 mean; of which PEANUT_BUTTER -10,333; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-14,206 to +3,580)); lychee-trend (-6,878 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-31,138 to +7,790)); mean-reversion-decay (-7,273 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,758 to +3,302)); momentum-crash (-4,112 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,218 to +17,396)); one-sided-flow (-4,821 mean; of which PEANUT_BUTTER -16,010; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-28,242 to +9,151)); pearl-plug-weakens (-7,254 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,244 to +3,700)); pearl-sum-shift (-7,776 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,010 to +3,841)); regime-flip (-8,970 mean; of which PEANUT_BUTTER -14,571; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-25,526 to +2,427)); smile-flattens (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,180 to +3,751)); smile-sticky-strike (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,180 to +3,751)); tellurium-informed (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,180 to +3,751)); tellurium-jumps-stick (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,180 to +3,751)); tellurium-whipsaw (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,180 to +3,751)); toxic-flow (-13,977 mean; of which PEANUT_BUTTER -14,875; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed); vol-clustering (-5,424 mean; of which PEANUT_BUTTER -10,924; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-19,656 to +4,337)); vol-crush (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,180 to +3,751)); vol-regime-switch (-1,368 mean; of which PEANUT_BUTTER -10,542; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,828 to +12,392)); vol-spike-skew (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,180 to +3,751)); wide-spreads (-3,645 mean; of which PEANUT_BUTTER -12,064; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-21,994 to +8,016)); anchor-break (-7,331 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,488 to +3,107)); black-swan-squeeze (-37,439 mean; of which WHITE_PEARLS -17,113; loses money; edge over orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s -271,343, well below its usual -166,086; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed); flash-crash (-6,399 mean; of which PEANUT_BUTTER -12,354; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-23,796 to +4,116)); liquidity-spiral (-6,177 mean; of which PEANUT_BUTTER -10,697; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,472 to +12,700)); opening-gap (-8,159 mean; of which PEANUT_BUTTER -12,373; loses money; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,488 to +3,764)); quant-quake (-2,527 mean; of which PEANUT_BUTTER -12,363; loses money; edge over orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s -246,615, well below its usual -166,086; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,592 to +12,467)); tellurium-storm (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; edge over orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s -347,620, well below its usual -166,086; behind orch_v3_newcore, orch_v4r_fs0_nojump, orch_v4s on every seed; seeds disagree (-24,180 to +3,751))
