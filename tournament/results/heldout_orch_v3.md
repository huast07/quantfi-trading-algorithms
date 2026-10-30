# Leaderboard: heldout suite (seeds [3, 4, 5])

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | orch_v3 | 147,033 | quiet-day (119,057) | 83,670 | 1 | 9,461 | 0 | 0 |
| 2 | S4 | 49,170 | busy-day (29,574) | -6,642 | 4 | 12,431 | 0 | 0 |
| 3 | S3 | 46,808 | wide-spreads (33,133) | 6,219 | 8 | 3,308 | 0 | 0 |
| 4 | S1 | 39,956 | liquidity-spiral (16,080) | -550 | 5 | 4,681 | 0 | 0 |
| 5 | S5 | 34,580 | mean-reversion-decay (19,266) | 10,638 | 1 | 6,530 | 0 | 0 |
| 6 | S2 | 19,867 | liquidity-drought (7,373) | 4,608 | 1 | 5,422 | 0 | 0 |
| 7 | reference | -5,680 | black-swan-squeeze (-37,439) | -66,139 | 37 | 22,839 | 0 | 0 |

## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)

| Strategy | Leader minus strategy | 95% CI |
|---|---:|---|
| S4 | 97,862 | [93,462, 102,155] |
| S3 | 100,225 | [92,164, 108,730] |
| S1 | 107,077 | [99,109, 115,728] |
| S5 | 112,453 | [103,635, 122,326] |
| S2 | 127,166 | [119,577, 136,055] |
| reference | 152,713 | [143,334, 162,319] |

## Tier-weighted PnL by product

| Product | orch_v3 | S4 | S3 | S1 | S5 | S2 | reference |
|---|---:|---:|---:|---:|---:|---:|---:|
| AMETHYST | 542 | 0 | 0 | 542 | 514 | 473 | 264 |
| BLACK_PEARLS | -259 | 0 | 0 | 301 | 77 | -259 | -224 |
| BLUE_PEARLS | 2,623 | 0 | 0 | 407 | 148 | 2,623 | -25 |
| DRAGONFRUIT | 0 | 0 | 0 | 4 | 177 | -41 | -220 |
| FRUIT_BASKET | 0 | 0 | 0 | -245 | 334 | 357 | 194 |
| GOLDEN_PEARLS | 1,637 | 0 | 0 | 1,642 | -1,320 | 1,637 | 436 |
| GRANADILLA | 0 | 0 | 0 | 632 | 55 | 607 | 697 |
| JELLY | 765 | 0 | 0 | 1,854 | 753 | 1,858 | 3,316 |
| LYCHEE | -3,655 | 0 | -3,655 | 340 | 167 | 406 | -10 |
| MANGOSTEEN | 0 | 0 | 0 | -293 | -13 | -332 | -646 |
| PAPER_LANTERNS | 817 | 0 | 0 | 817 | 569 | 714 | 618 |
| PEANUT_BUTTER | 0 | 0 | 0 | -698 | -1,958 | -1,504 | -10,400 |
| PINK_PEARLS | 10,855 | 0 | 0 | 578 | 8,808 | 10,855 | 391 |
| TELLURIUM | 49,170 | 49,170 | 0 | 0 | 0 | 0 | 0 |
| TOFFEE_CAKE | 34,532 | 0 | 0 | 34,532 | 26,213 | 2,021 | 885 |
| VOUCHER_6800 | 2,022 | 0 | 2,022 | 0 | 0 | 0 | 0 |
| VOUCHER_7000 | 5,374 | 0 | 5,374 | 0 | 0 | 0 | 0 |
| VOUCHER_7200 | 4,795 | 0 | 4,795 | 0 | 0 | 0 | 0 |
| VOUCHER_7300 | 6,622 | 0 | 6,622 | 0 | 0 | 0 | 0 |
| VOUCHER_7400 | 6,333 | 0 | 6,333 | 0 | 0 | 0 | 0 |
| VOUCHER_7500 | 5,263 | 0 | 5,263 | 0 | 0 | 0 | 0 |
| VOUCHER_7600 | 7,223 | 0 | 7,223 | 0 | 0 | 0 | 0 |
| VOUCHER_7750 | 7,149 | 0 | 7,149 | 0 | 0 | 0 | 0 |
| VOUCHER_7900 | 4,933 | 0 | 4,933 | 0 | 0 | 0 | 0 |
| VOUCHER_8100 | 748 | 0 | 748 | 0 | 0 | 0 | 0 |
| WHITE_PEARLS | -459 | 0 | 0 | -459 | 56 | 449 | -955 |

## Weak cases

- **orch_v3:** quiet-day (+119,057 mean; of which LYCHEE -3,665; well below its average of +160,985; edge over S1, S2, S3, S4, S5, reference +91,630, well below its usual +127,400; beats S1, S2, S3, S4, S5, reference on every seed; beats reference on every seed)
- **S4:** correlation-breakdown (+55,944 mean; of which TELLURIUM +55,944; edge over orch_v3, S1, S2, S3, S5, reference -44,995, well below its usual +7,296; beats reference on every seed); black-swan-crash (+51,252 mean; of which TELLURIUM +51,252; edge over orch_v3, S1, S2, S3, S5, reference -36,251, well below its usual +7,296; seeds disagree (-6,642 to +106,808)); black-swan-squeeze (+54,964 mean; of which TELLURIUM +54,964; edge over orch_v3, S1, S2, S3, S5, reference -26,784, well below its usual +7,296; beats reference on every seed); quant-quake (+55,944 mean; of which TELLURIUM +55,944; edge over orch_v3, S1, S2, S3, S5, reference -38,109, well below its usual +7,296; beats reference on every seed)
- **S3:** correlation-breakdown (+47,187 mean; of which LYCHEE -3,351; edge over orch_v3, S1, S2, S4, S5, reference -55,211, well below its usual -6,469; beats reference on every seed); lychee-trend (+43,108 mean; of which LYCHEE -6,080; well below its average of +46,241; beats reference on every seed); wide-spreads (+33,133 mean; of which LYCHEE -4,474; well below its average of +46,241; beats reference on every seed); black-swan-crash (+39,190 mean; of which VOUCHER_6800 -15,491; well below its average of +46,241; edge over orch_v3, S1, S2, S4, S5, reference -50,324, well below its usual -6,469); black-swan-squeeze (+47,744 mean; of which LYCHEE -31,937; edge over orch_v3, S1, S2, S4, S5, reference -35,207, well below its usual -6,469; beats reference on every seed); liquidity-spiral (+39,130 mean; of which VOUCHER_6800 -7,418; well below its average of +46,241; beats reference on every seed); quant-quake (+42,878 mean; of which LYCHEE -2,657; well below its average of +46,241; edge over orch_v3, S1, S2, S4, S5, reference -53,352, well below its usual -6,469; beats reference on every seed); tellurium-storm (+47,187 mean; of which LYCHEE -3,351; edge over orch_v3, S1, S2, S4, S5, reference -63,149, well below its usual -6,469; beats reference on every seed)
- **S1:** correlation-breakdown (+37,753 mean; of which PEANUT_BUTTER -932; edge over orch_v3, S2, S3, S4, S5, reference -66,217, well below its usual -13,739; beats reference on every seed); mean-reversion-decay (+27,848 mean; of which PEANUT_BUTTER -932; well below its average of +40,009; beats reference on every seed); liquidity-spiral (+16,080 mean; of which PAPER_LANTERNS -3,404; well below its average of +40,009; edge over orch_v3, S2, S3, S4, S5, reference -38,276, well below its usual -13,739; beats reference on every seed; seeds disagree (-550 to +42,878)); quant-quake (+27,095 mean; of which PEANUT_BUTTER -932; well below its average of +40,009; edge over orch_v3, S2, S3, S4, S5, reference -71,765, well below its usual -13,739; beats reference on every seed); tellurium-storm (+38,627 mean; of which PEANUT_BUTTER -932; edge over orch_v3, S2, S3, S4, S5, reference -73,135, well below its usual -13,739; beats reference on every seed)
- **S5:** tellurium-storm (+29,034 mean; of which PEANUT_BUTTER -3,394; edge over orch_v3, S1, S2, S3, S4, reference -84,327, well below its usual -16,212; beats reference on every seed)
- **S2:** tellurium-storm (+13,883 mean; of which PEANUT_BUTTER -2,249; edge over orch_v3, S1, S3, S4, S5, reference -102,003, well below its usual -31,027; beats reference on every seed)
- **reference:** busy-day (-7,892 mean; of which PEANUT_BUTTER -12,925; loses money; seeds disagree (-30,716 to +15,644)); regular-day (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); regular-day-varied (-5,180 mean; of which PEANUT_BUTTER -8,614; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-22,376 to +7,233)); trends-continue (-8,044 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-23,706 to +5,455)); basket-dislocation (-7,226 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-23,704 to +3,651)); clustered-arrivals (-4,897 mean; of which PEANUT_BUTTER -7,436; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,815 to +5,116)); correlation-breakdown (-3,713 mean; of which PEANUT_BUTTER -12,363; loses money; edge over orch_v3, S1, S2, S3, S4, S5 -114,594, well below its usual -67,249; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-27,190 to +13,726)); fat-tails (-8,558 mean; of which PEANUT_BUTTER -12,987; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-35,588 to +10,707)); golden-continues (-7,121 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,258 to +4,684)); golden-flat (-7,294 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,238 to +3,751)); golden-reverses (-7,022 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,026 to +3,833)); intraday-seasonality (-2,671 mean; of which PEANUT_BUTTER -10,333; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-14,206 to +3,580)); lychee-trend (-6,878 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-31,138 to +7,790)); mean-reversion-decay (-7,273 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,758 to +3,302)); momentum-crash (-4,112 mean; of which PEANUT_BUTTER -12,363; loses money; seeds disagree (-24,218 to +17,396)); one-sided-flow (-4,821 mean; of which PEANUT_BUTTER -16,010; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-28,242 to +9,151)); pearl-plug-weakens (-7,254 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,244 to +3,700)); pearl-sum-shift (-7,776 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,010 to +3,841)); regime-flip (-8,970 mean; of which PEANUT_BUTTER -14,571; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-25,526 to +2,427)); smile-flattens (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); smile-sticky-strike (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); tellurium-informed (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); tellurium-jumps-stick (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); tellurium-whipsaw (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); toxic-flow (-13,977 mean; of which PEANUT_BUTTER -14,875; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed); vol-clustering (-5,424 mean; of which PEANUT_BUTTER -10,924; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-19,656 to +4,337)); vol-crush (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); vol-regime-switch (-1,368 mean; of which PEANUT_BUTTER -10,542; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,828 to +12,392)); vol-spike-skew (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751)); wide-spreads (-3,645 mean; of which PEANUT_BUTTER -12,064; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-21,994 to +8,016)); anchor-break (-7,331 mean; of which PEANUT_BUTTER -12,363; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,488 to +3,107)); black-swan-squeeze (-37,439 mean; of which WHITE_PEARLS -17,113; loses money; edge over orch_v3, S1, S2, S3, S4, S5 -134,588, well below its usual -67,249; behind orch_v3, S1, S2, S3, S4, S5 on every seed); flash-crash (-6,399 mean; of which PEANUT_BUTTER -12,354; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-23,796 to +4,116)); liquidity-spiral (-6,177 mean; of which PEANUT_BUTTER -10,697; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,472 to +12,700)); opening-gap (-8,159 mean; of which PEANUT_BUTTER -12,373; loses money; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,488 to +3,764)); quant-quake (-2,527 mean; of which PEANUT_BUTTER -12,363; loses money; edge over orch_v3, S1, S2, S3, S4, S5 -106,324, well below its usual -67,249; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,592 to +12,467)); tellurium-storm (-7,204 mean; of which PEANUT_BUTTER -12,363; loses money; edge over orch_v3, S1, S2, S3, S4, S5 -126,605, well below its usual -67,249; behind orch_v3, S1, S2, S3, S4, S5 on every seed; seeds disagree (-24,180 to +3,751))
