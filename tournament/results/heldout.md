# Leaderboard: heldout suite (seeds [3, 4, 5])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | S4 | 49,170 | busy-day (29,574) | -6,642 | 3 | 12,431 | 0 | 0 |
| 2 | S3 | 46,808 | wide-spreads (33,133) | 6,219 | 8 | 3,308 | 0 | 0 |
| 3 | S1 | 39,956 | liquidity-spiral (16,080) | -550 | 5 | 4,681 | 0 | 0 |
| 4 | S5 | 34,580 | mean-reversion-decay (19,266) | 10,638 | 1 | 6,530 | 0 | 0 |
| 5 | S2 | 19,867 | liquidity-drought (7,373) | 4,608 | 1 | 5,422 | 0 | 0 |
| 6 | reference | -5,680 | black-swan-squeeze (-37,439) | -66,139 | 37 | 22,839 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| S3 | 2,363 | [-4,257, 10,125] |
| S1 | 9,215 | [1,565, 17,461] |
| S5 | 14,590 | [5,464, 24,465] |
| S2 | 29,304 | [20,960, 38,727] |
| reference | 54,851 | [47,294, 63,605] |

## Real days

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 32,494 | 35,658 | 27,994 | 96,146 | 0 | 0.66 |
| S2 | 15,552 | 13,568 | 9,674 | 38,794 | 0 | 0.30 |
| S3 | 62,542 | 54,232 | 45,624 | 162,398 | 0 | 0.43 |
| S4 | 49,974 | 27,534 | 44,398 | 121,906 | 0 | 0.27 |
| S5 | 27,956 | 21,950 | 32,298 | 82,205 | 0 | 0.41 |

## Tier-weighted PnL by product

| Product | S4 | S3 | S1 | S5 | S2 | reference |
|---|---:|---:|---:|---:|---:|---:|
| AMETHYST | 0 | 0 | 542 | 514 | 473 | 264 |
| BLACK_PEARLS | 0 | 0 | 301 | 77 | -259 | -224 |
| BLUE_PEARLS | 0 | 0 | 407 | 148 | 2,623 | -25 |
| DRAGONFRUIT | 0 | 0 | 4 | 177 | -41 | -220 |
| FRUIT_BASKET | 0 | 0 | -245 | 334 | 357 | 194 |
| GOLDEN_PEARLS | 0 | 0 | 1,642 | -1,320 | 1,637 | 436 |
| GRANADILLA | 0 | 0 | 632 | 55 | 607 | 697 |
| JELLY | 0 | 0 | 1,854 | 753 | 1,858 | 3,316 |
| LYCHEE | 0 | -3,655 | 340 | 167 | 406 | -10 |
| MANGOSTEEN | 0 | 0 | -293 | -13 | -332 | -646 |
| PAPER_LANTERNS | 0 | 0 | 817 | 569 | 714 | 618 |
| PEANUT_BUTTER | 0 | 0 | -698 | -1,958 | -1,504 | -10,400 |
| PINK_PEARLS | 0 | 0 | 578 | 8,808 | 10,855 | 391 |
| TELLURIUM | 49,170 | 0 | 0 | 0 | 0 | 0 |
| TOFFEE_CAKE | 0 | 0 | 34,532 | 26,213 | 2,021 | 885 |
| VOUCHER_6800 | 0 | 2,022 | 0 | 0 | 0 | 0 |
| VOUCHER_7000 | 0 | 5,374 | 0 | 0 | 0 | 0 |
| VOUCHER_7200 | 0 | 4,795 | 0 | 0 | 0 | 0 |
| VOUCHER_7300 | 0 | 6,622 | 0 | 0 | 0 | 0 |
| VOUCHER_7400 | 0 | 6,333 | 0 | 0 | 0 | 0 |
| VOUCHER_7500 | 0 | 5,263 | 0 | 0 | 0 | 0 |
| VOUCHER_7600 | 0 | 7,223 | 0 | 0 | 0 | 0 |
| VOUCHER_7750 | 0 | 7,149 | 0 | 0 | 0 | 0 |
| VOUCHER_7900 | 0 | 4,933 | 0 | 0 | 0 | 0 |
| VOUCHER_8100 | 0 | 748 | 0 | 0 | 0 | 0 |
| WHITE_PEARLS | 0 | 0 | -459 | 56 | 449 | -955 |

## Weak cases

- **S4:** correlation-breakdown (+55,944 mean; of which TELLURIUM +55,944; edge over S1, S2, S3, S5, reference -13,053, well below its usual +29,345; beats reference on every seed); black-swan-crash (+51,252 mean; of which TELLURIUM +51,252; edge over S1, S2, S3, S5, reference -11,239, well below its usual +29,345; seeds disagree (-6,642 to +106,808)); quant-quake (+55,944 mean; of which TELLURIUM +55,944; edge over S1, S2, S3, S5, reference -7,982, well below its usual +29,345; beats reference on every seed)
- **S3:** correlation-breakdown (+47,187 mean; of which LYCHEE -3,351; edge over S1, S2, S4, S5, reference -23,561, well below its usual +15,186; beats reference on every seed); lychee-trend (+43,108 mean; of which LYCHEE -6,080; well below its average of +46,241; beats reference on every seed); wide-spreads (+33,133 mean; of which LYCHEE -4,474; well below its average of +46,241; beats reference on every seed); black-swan-crash (+39,190 mean; of which VOUCHER_6800 -15,491; well below its average of +46,241; edge over S1, S2, S4, S5, reference -25,714, well below its usual +15,186); black-swan-squeeze (+47,744 mean; of which LYCHEE -31,937; edge over S1, S2, S4, S5, reference -1,813, well below its usual +15,186; beats reference on every seed); liquidity-spiral (+39,130 mean; of which VOUCHER_6800 -7,418; well below its average of +46,241; beats reference on every seed); quant-quake (+42,878 mean; of which LYCHEE -2,657; well below its average of +46,241; edge over S1, S2, S4, S5, reference -23,661, well below its usual +15,186; beats reference on every seed); tellurium-storm (+47,187 mean; of which LYCHEE -3,351; edge over S1, S2, S4, S5, reference -17,050, well below its usual +15,186; beats reference on every seed)
- **S1:** correlation-breakdown (+37,753 mean; of which PEANUT_BUTTER -932; edge over S2, S3, S4, S5, reference -34,881, well below its usual +7,708; beats reference on every seed); mean-reversion-decay (+27,848 mean; of which PEANUT_BUTTER -932; well below its average of +40,009; beats reference on every seed); liquidity-spiral (+16,080 mean; of which PAPER_LANTERNS -3,404; well below its average of +40,009; edge over S2, S3, S4, S5, reference -20,595, well below its usual +7,708; beats reference on every seed; seeds disagree (-550 to +42,878)); quant-quake (+27,095 mean; of which PEANUT_BUTTER -932; well below its average of +40,009; edge over S2, S3, S4, S5, reference -42,601, well below its usual +7,708; beats reference on every seed); tellurium-storm (+38,627 mean; of which PEANUT_BUTTER -932; edge over S2, S3, S4, S5, reference -27,322, well below its usual +7,708; beats reference on every seed)
- **S5:** tellurium-storm (+29,034 mean; of which PEANUT_BUTTER -3,394; edge over S1, S2, S3, S4, reference -38,833, well below its usual +5,165; beats reference on every seed)
- **S2:** tellurium-storm (+13,883 mean; of which PEANUT_BUTTER -2,249; edge over S1, S3, S4, S5, reference -57,014, well below its usual -10,074; beats reference on every seed)
- **reference:** busy-day (-7,892 mean; of which PEANUT_BUTTER -12,925; loses money; seeds disagree (-30,716 to +15,644)); regular-day (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); regular-day-varied (-5,180 mean; of which PEANUT_BUTTER -8,614; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-22,376 to +7,233)); trends-continue (-8,044 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-23,706 to +5,455)); basket-dislocation (-7,226 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-23,704 to +3,651)); clustered-arrivals (-4,897 mean; of which PEANUT_BUTTER -7,436; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,815 to +5,116)); correlation-breakdown (-3,713 mean; of which PEANUT_BUTTER -12,363; loses money; edge over S1, S2, S3, S4, S5 -84,641, well below its usual -47,331; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-27,190 to +13,726)); fat-tails (-8,558 mean; of which PEANUT_BUTTER -12,987; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-35,588 to +10,707)); golden-continues (-7,121 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,258 to +4,684)); golden-flat (-7,294 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,238 to +3,751)); golden-reverses (-7,022 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,026 to +3,833)); intraday-seasonality (-2,671 mean; of which PEANUT_BUTTER -10,333; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-14,206 to +3,580)); lychee-trend (-6,878 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-31,138 to +7,790)); mean-reversion-decay (-7,273 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,758 to +3,302)); momentum-crash (-4,112 mean; of which PEANUT_BUTTER -12,363; loses money; seeds disagree (-24,218 to +17,396)); one-sided-flow (-4,821 mean; of which PEANUT_BUTTER -16,010; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-28,242 to +9,151)); pearl-plug-weakens (-7,254 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,244 to +3,700)); pearl-sum-shift (-7,776 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,010 to +3,841)); regime-flip (-8,970 mean; of which PEANUT_BUTTER -14,571; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-25,526 to +2,427)); smile-flattens (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); smile-sticky-strike (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); tellurium-informed (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); tellurium-jumps-stick (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); tellurium-whipsaw (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); toxic-flow (-13,977 mean; of which PEANUT_BUTTER -14,875; loses money; behind S1, S2, S3, S4, S5 on every seed); vol-clustering (-5,424 mean; of which PEANUT_BUTTER -10,924; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-19,656 to +4,337)); vol-crush (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); vol-regime-switch (-1,368 mean; of which PEANUT_BUTTER -10,542; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,828 to +12,392)); vol-spike-skew (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); wide-spreads (-3,645 mean; of which PEANUT_BUTTER -12,064; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-21,994 to +8,016)); anchor-break (-7,331 mean; of which PEANUT_BUTTER -12,363; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,488 to +3,107)); black-swan-squeeze (-37,439 mean; of which WHITE_PEARLS -17,113; loses money; edge over S1, S2, S3, S4, S5 -104,033, well below its usual -47,331; behind S1, S2, S3, S4, S5 on every seed); flash-crash (-6,399 mean; of which PEANUT_BUTTER -12,354; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-23,796 to +4,116)); liquidity-spiral (-6,177 mean; of which PEANUT_BUTTER -10,697; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,472 to +12,700)); opening-gap (-8,159 mean; of which PEANUT_BUTTER -12,373; loses money; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,488 to +3,764)); quant-quake (-2,527 mean; of which PEANUT_BUTTER -12,363; loses money; edge over S1, S2, S3, S4, S5 -78,147, well below its usual -47,331; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,592 to +12,467)); tellurium-storm (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; edge over S1, S2, S3, S4, S5 -82,319, well below its usual -47,331; behind S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751))
