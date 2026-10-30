# S2 - Structural alpha on the delta-one products

`trader.py` trades the 15 benign delta-one products (no TELLURIUM, no vouchers).
It is one inventory-aware touch quoter plus five switchable structural components (`CONFIG` at the top of the file).

## 1. Design

### Base layer: touch quoter with an Avellaneda-Stoikov reservation price

The engine fills a resting order whenever a market trade prints at or through its price, and every noise-taker print sits at the same-tick touch (generator `takers.hit_touch`, EDA "100% of prints at or through the touch").
So a quote AT the touch has the same fill odds as one inside it and the largest edge, which is why the reference (one tick inside) leaves about 1 per lot on the table.

Per product and tick:

- `r = fair + alpha - k * (q - target)`, with `k = half_spread / soft` and `soft = clip(SOFT_C * half_spread / sigma^2, 4, limit)`.
  `sigma^2` is a live EWMA (1/500) of squared one-tick mid changes, so the inventory penalty grows with sigma^2 as in Avellaneda & Stoikov (2008); at `q - target = soft` the adding side is suppressed.
- Post the full remaining capacity at the best bid if `r - bid >= 1` and at the best ask if `ask - r >= 1`.
- Cross the book only when a component asks for it (`take`), only towards its target, and only at prices that still beat `r` by the component's `take_edge`.
- Orders are clipped so that position plus all same-side orders never exceeds the limit (zero breaches in every run).

Fair values: AMETHYST = span-200 EWMA started at 10,000 (follows an anchor break); GOLDEN = plateau EWMA, reset on a step; TOFFEE = span-3 EWMA; FRUIT_BASKET = 2D + 3G + 1M + Kalman premium; everything else raw mid (EDA: raw mid is best).

### Components (each is a `SubStrategy` for the Phase 3 orchestrator)

| Component | Products | Model and estimators | Sizing | Risk controls | `edge()` / `variance()` per lot |
|---|---|---|---|---|---|
| `touch_maker` | all 15 | reservation price above | full capacity at the touch | sigma^2-scaled skew, limit clipping | half spread / live tick variance |
| `pink_plug` | PINK | dev = sum of 5 pearl mids - total_hat. Hazard h(\|dev\|) is a Beta-Bernoulli posterior per bucket [0,5), [5,10), [10,inf) (priors 0.0004 / 0.0097 / 0.064 from params, 2,000-tick prior strength, capped for adaptivity). Jump size = slope x dev, slope by recursive LS with forgetting 0.97 per jump (prior -1.10). E[20-tick move] = (1 - (1-h)^20) x slope x dev. total_hat is re-read from the pearl sum right after each detected jump (EWMA 0.3, reset if > 6 away), so a shifted total is learned within one or two jumps. | target +-20 and cross when \|E[move]\| > half spread; otherwise hold (PINK is flat between jumps, so holding costs nothing) | kill switch if the Beta posterior of "jump restores the sum" (prior Beta(19,1)) falls below 0.75 or \|slope\| < 0.3 | \|E[move]\| - half spread / p(1-p)(slope dev)^2 + p 1.28^2 |
| `golden_step` | GOLDEN, WHITE, BLACK | Two-sided CUSUM on mid - plateau (k = 1 = 2 x noise sd, h = 5), O(1). Step size posterior over {100, 50} (prior 2/3, 1/3) from the EWMA ramp speed (ramp is 85 ticks, so speed = size / 85). E[remaining] = E[size] - moved. WHITE / BLACK expect -0.447 / -0.457 x remaining (params absorber shares). Works in both directions (golden-reverses). | target +-limit and cross while \|E[remaining]\| > 2 half spreads + 1 | crash guard: a one-tick move > 12, or WHITE+BLACK moving the same way as GOLDEN after 10 points, means a market shock, not a step: 300-tick cooldown. Step ends after 5 calm ticks. | \|remaining\| - half / (size uncertainty)^2 |
| `blue_trend` | BLUE | Bayesian drift: prior N(0.02, 0.015^2) (params drift 0.0198, three up days) combined with a slow EWMA (1/2000) of mid changes; momentum alpha = 0.23 x 10-tick EWMA move (EDA corr +0.23). | target = 20 x clip(drift x 400 / half spread, -1, 1), passive only | guard: target 0 when the fast EWMA (1/300) contradicts the drift by > 1 standard error (momentum crash, regime flip) | drift x 400 - half / 2 x 400 |
| `toffee_ou` | TOFFEE | OU around a slow-EWMA anchor (1/3000, prior 5,003.3). kappa from EWMA moments cov(dev, dx)/var(dev), shrunk to the prior 0.0046 with 3,000 pseudo-ticks. E[100-tick move] = (anchor - x)(1 - (1-kappa)^100). | target = 50 x clip(E / (2 half spread), -1, 1), passive | the kappa estimate shrinks the lean when reversion decays; the anchor EWMA follows a drifting anchor | \|E\| - half / OU variance over 100 ticks |
| basket fair value | FRUIT_BASKET | Kalman random-walk premium (Q = 4.15^2 per tick from params, R = 3) on basket mid - synthetic | quoting only, no stat-arb (EDA) | - | - |

PAPER_LANTERNS' span-5 EWMA fair value is implemented (`CONFIG["lantern_ewma"]`) but off: it lost money on dev and on the real days (section 4).

## 2. Statistics behind each component

- Touch quoting: generator prints are capped at touch volume and priced at the touch; EDA passive replay puts the best EV at the touch for AMETHYST, PAPER_LANTERNS, PINK (day 0), GOLDEN (days -2, 0).
- PINK: EDA 62-63 jumps/day, 100% restoring, slope -1.10 to -1.12, P(jump) 5-11% at \|dev\| > 10 vs 0.4%.
  My regeneration on regular-day seeds 1-2: 42 / 46 jumps, slope -1.14 / -1.17, 100% restoring, 20-tick PINK move +7.5 / +6.7 for dev in [-15, -10) and -4.9 / -7.8 for dev in [10, 15), -0.02 / -0.10 for \|dev\| < 5.
  Half spread is 2.0 (spread 4.0), so only the \|dev\| > 10 bucket clears the crossing cost over 20 ticks, which is what the entry rule reproduces.
- GOLDEN: params step sizes -100/-100/-50 over an 85-tick ramp, absorbed 44.7% / 45.7% by WHITE / BLACK; EDA "price kept falling ~33 over the next 20 ticks" after a step.
- BLUE: params drift 0.0198/tick, local-trend AR(1) phi 0.5; EDA 10-tick momentum corr +0.22 to +0.24, up all three days.
- TOFFEE: params kappa 0.0046 (half-life ~150 ticks), stationary sd ~23; EDA variance ratio 0.11 at 1,000 ticks.
- FRUIT_BASKET: premium is a random walk (EDA ADF p 0.19-0.99), so a near-1 Kalman gain; the fair value only filters basket quote noise (sd 1.14).

## 3. Results

Measured with `tools/minisim.py`, a re-implementation of prosperity3bt's mode-"all" matching restricted to the 15 products.
It reproduces the real engine to the unit on regular-day seed 1 (13,002 vs 13,002) and on all three real days (14,404 / 4,649 / 10,488 for an earlier build in both), and within 8 on seed 2.
The official `compare.py --suite dev` run was started but the machine sat at load average 500-750 (6/84 days in 15 minutes), so it was stopped; the minisim covers the same 42 cases x seeds 1-2 and the real days.

**Dev suite (42 cases x seeds 1-2), tier-weighted over my 15 products: S2 21,713 vs reference -3,362.**
Zero limit breaches and zero crashes on all 84 dev days and the 3 real days.
Every case is profitable on its mean; the lowest case is liquidity-drought (8,554, worst seed 1,618), and no seed of any case loses money.
Weak cases: 0 on the absolute rule (no losing case, none more than one sd below the mean); the relative part needs the other uploads.

**Real days: 15,552 / 13,568 / 9,674 = 38,794 total** (reference 7,930 / -2,260 / -3,094 on the same products).

Tier-weighted PnL by product (dev): AMETHY 500, TOFFEE 1,570, PAPER_ 575, JELLY 3,696, PEANUT -506, DRAGON 56, GRANAD -963, MANGOS -104, FRUIT_ 36, LYCHEE -650, WHITE_ 1,791, BLACK_ 2,020, GOLDEN 1,807, PINK_P 11,317, BLUE_P 568.
PINK is half the total; GOLDEN + WHITE + BLACK (the step trade) another ~5,600; the random-walk legs (PEANUT_BUTTER, GRANADILLA, LYCHEE, MANGOSTEEN) are small negatives that are inventory noise on random walks, not an edge sign.

| Case | S2 mean | S2 per seed | Reference mean | Breaches | Worst products (worst seed) |
|---|---:|---|---:|---:|---|
| busy-day | 14,486 | 12,522 16,450 | n/a | 0 | FRUIT_ -2,330, GRANAD -2,236, BLUE_P -1,791 |
| quiet-day | 12,391 | 14,028 10,754 | n/a | 0 | MANGOS -2,524, PEANUT -1,402, DRAGON -1,328 |
| regular-day | 15,977 | 11,553 20,402 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| regular-day-varied | 19,714 | 20,226 19,200 | n/a | 0 | GRANAD -1,606, LYCHEE -1,416, MANGOS -1,112 |
| trends-continue | 19,465 | 16,246 22,685 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| basket-dislocation | 16,260 | 11,400 21,120 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| clustered-arrivals | 12,572 | 9,715 15,430 | n/a | 0 | PEANUT -3,199, LYCHEE -2,795, GRANAD -1,469 |
| correlation-breakdown | 130,845 | 120,441 141,248 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| fat-tails | 15,330 | 8,666 21,994 | n/a | 0 | LYCHEE -3,099, FRUIT_ -2,096, GRANAD -2,012 |
| golden-continues | 22,523 | 18,565 26,480 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| golden-flat | 12,247 | 8,528 15,966 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| golden-reverses | 16,736 | 15,378 18,094 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| heavy-flow | 13,912 | 11,722 16,103 | n/a | 0 | FRUIT_ -2,406, GRANAD -1,556, MANGOS -1,396 |
| intraday-seasonality | 18,467 | 16,428 20,506 | n/a | 0 | MANGOS -1,543, LYCHEE -977, BLUE_P -959 |
| liquidity-drought | 8,554 | 1,618 15,490 | n/a | 0 | MANGOS -2,178, JELLY -1,337, FRUIT_ -1,286 |
| lychee-trend | 16,334 | 15,432 17,236 | n/a | 0 | LYCHEE -3,547, PEANUT -2,176, GRANAD -1,492 |
| mean-reversion-decay | 16,262 | 11,766 20,758 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| momentum-crash | 20,186 | 13,931 26,441 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| one-sided-flow | 14,763 | 6,026 23,500 | n/a | 0 | JELLY -2,684, GRANAD -1,492, PEANUT -1,339 |
| pearl-plug-weakens | 13,250 | 7,873 18,628 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| pearl-sum-shift | 18,478 | 13,608 23,348 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| regime-flip | 18,217 | 9,994 26,440 | n/a | 0 | LYCHEE -2,824, PEANUT -2,123, GRANAD -1,426 |
| smile-flattens | 15,977 | 11,553 20,402 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| smile-sticky-strike | 15,977 | 11,553 20,402 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| tellurium-informed | 15,977 | 11,553 20,402 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| tellurium-jumps-stick | 15,977 | 11,553 20,402 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| tellurium-whipsaw | 15,977 | 11,553 20,402 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| toxic-flow | 13,030 | 7,428 18,632 | n/a | 0 | GRANAD -2,134, PEANUT -1,752, LYCHEE -884 |
| vol-clustering | 17,080 | 14,460 19,700 | n/a | 0 | PEANUT -2,980, FRUIT_ -1,502, GRANAD -1,395 |
| vol-crush | 15,977 | 11,553 20,402 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| vol-regime-switch | 13,887 | 11,620 16,155 | n/a | 0 | PEANUT -6,754, FRUIT_ -2,134, BLACK_ -1,582 |
| vol-spike-skew | 15,977 | 11,553 20,402 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| wide-spreads | 17,406 | 14,693 20,118 | n/a | 0 | PEANUT -4,212, MANGOS -2,598, GRANAD -1,776 |
| anchor-break | 15,897 | 11,475 20,320 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| black-swan-crash | 110,740 | 111,877 109,604 | n/a | 0 | BLACK_ -24,508, WHITE_ -17,899, BLUE_P -6,126 |
| black-swan-squeeze | 127,733 | 121,077 134,388 | n/a | 0 | LYCHEE -13,837, PAPER_ -6,168, MANGOS -2,714 |
| flash-crash | 25,914 | 10,382 41,446 | n/a | 0 | PEANUT -3,131, GRANAD -1,861, LYCHEE -1,620 |
| liquidity-spiral | 45,490 | 43,770 47,210 | n/a | 0 | BLACK_ -10,082, WHITE_ -6,802, TOFFEE -4,509 |
| opening-gap | 36,496 | 27,898 45,094 | n/a | 0 | PEANUT -2,177, LYCHEE -1,528, GRANAD -1,492 |
| quant-quake | 133,154 | 123,849 142,458 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| tellurium-storm | 15,977 | 11,553 20,402 | n/a | 0 | PEANUT -2,176, LYCHEE -1,534, GRANAD -1,492 |
| vol-explosion | 18,565 | 14,159 22,970 | n/a | 0 | PEANUT -3,986, GRANAD -2,071, FRUIT_ -2,060 |
| real | 12,932 | 15,552 13,568 9,674 | n/a | 0 | JELLY -2,408, FRUIT_ -2,118, PEANUT -1,960 |


## 4. Variants and marginal contributions

Marginal contribution = tier-weighted dev PnL of the full trader minus the trader with that one component switched off (minisim, all 42 cases x seeds 1-2; the first-round trader, before the final GOLDEN and kill-switch changes, weighted 21,080).

| Component off | Dev weighted | Marginal of component | Real days, mean per day | Notes |
|---|---:|---:|---:|---|
| (none: round-1 trader) | 21,080 | - | 12,573 | |
| `pink` | 10,428 | **+10,652** | 5,703 | largest edge; +118k on correlation-breakdown and quant-quake, where the sum deviates more |
| `golden` | 16,988 | **+4,092** | 12,115 | +11.8k on golden-continues, 0 on golden-flat, +4.8k on golden-reverses; -24.9k on black-swan-crash (fixed, below) |
| `blue` | 19,932 | +1,148 | 10,858 | -3.4k on momentum-crash, -8.3k on black-swan-crash |
| `toffee` | 20,338 | +742 | 11,850 | only quant-quake negative (-461) |
| `basket_fv` | 20,830 | +250 | 11,538 | +1,035 on the real days; so the Kalman fair value beats raw mid |
| `lantern_ewma` | 21,141 | -61 | 13,007 | EWMA fair value loses vs raw mid: switched off |
| `pink_kill` (all PINK kill switches) | 21,797 | -717 | 12,573 | the \|sum - total\| > 30 band blocked +40k on black-swan-squeeze and +21k on opening-gap, where the plug keeps working; it never helped (pearl-sum-shift is handled by re-estimating the total). Band switched off, hit-rate and slope kills kept. |

Other variants:

| Variant | Result | Decision |
|---|---|---|
| reference market maker | dev -3,362 (minisim, my 15 products) | baseline |
| no inventory skew (SOFT_C = 1000) | regular-day 10,462 vs 15,992; PEANUT_BUTTER -20k on one seed | rejected |
| SOFT_C = 10 / 20 / 40 / 80 | regular-day 11,822 / 13,590 / 15,992 / 14,688 | 40 kept (middle of a flat-ish region) |
| GOLDEN v1 (settle on 1-tick moves) | ended 50-point steps early | replaced by EWMA-speed settle + step-size posterior |
| GOLDEN without the WHITE+BLACK absorption check | -24.9k on black-swan-crash | check added |
| Round-2 trader (band kill off, GOLDEN absorption check, lantern off) | regular-day 15,977, black-swan-crash 110,740 (from 112,767), liquidity-spiral 45,490 (from 44,244), real 12,932/day | shipped |

## 5. Run time

0.45 ms/tick for `run()` measured on an idle machine (minisim, regular day); 1-2 ms/tick while the machine ran at load average ~200 with the other agents.
All state is O(1) per product (about 1 KB of JSON).

## 6. Proposals

1. **Pearl inventory hedge.** WHITE, BLACK and BLUE have tick correlations -0.58 / -0.45 / -0.46, so their sum has a tick sd of ~1.1 against ~2.3 each. Skewing pearl quotes on the portfolio's sum exposure instead of each leg's own position would cut the pearls' inventory variance about 4x for the same fills (most of WHITE/BLACK's -18k to -25k on black-swan-crash is inventory).
2. **Passive PINK pre-positioning.** 60% of the PINK edge appears only once \|dev\| > 10; in the [5, 10) bucket the 20-tick move is still 1-3.5. Resting the full size at the touch on the restoring side from \|dev\| > 5 (already partly done through alpha) and measuring the Beta-Bernoulli fill rate would capture entries without paying the 2.0 half spread.
3. **Stress-aware PINK sizing.** PINK earns 50-130k on correlation-breakdown, quant-quake and both black swans because the deviation is large; the hazard is per tick, so E[move] scales with \|dev\|. Keeping the band kill off is right for this generator, but the orchestrator should cap PINK variance by `variance()` rather than a fixed band.
4. **DRAGONFRUIT / PAPER_LANTERNS drift prior.** The same Bayesian drift model as BLUE (DRAGONFRUIT +200/day and PAPER_LANTERNS -39/day on all three real days) would add a trend target; the trends-continue case is observed-tier (12% weight).
5. **BLUE crash guard.** The fast-EWMA guard did not move momentum-crash (-3.4k); a CUSUM on BLUE's 10-tick returns against the posterior drift would detect a -0.08/tick break in ~150 ticks instead of never.

## References

Ho & Stoll (1981); Avellaneda & Stoikov (2008); Gueant, Lehalle & Fernandez-Tapia (2013) for the inventory skew.
Page (1954) CUSUM and Adams & MacKay (2007) online changepoints for the GOLDEN steps.
Avellaneda & Lee (2010) and Uhlenbeck & Ornstein (1930) for the TOFFEE OU lean; Gatev, Goetzmann & Rouwenhorst (2006) for the pearl-sum plug as a cointegration residual.
Jegadeesh & Titman (1993) and Daniel & Moskowitz (2016) for BLUE momentum and its crash guard; Kalman (1960) for the basket premium; Perron (1989) for re-estimating a shifted total.

## Files

- `trader.py`: the submission; `variants/*.py`: `trader.py` plus override lines (`tools/mkvar.py`); `variants/reference.py`: the built-in reference.
- `variants/pinkH*`, `pinkE*`, `blue_fz2`, `lantern_on` were generated for a PINK horizon/entry sweep that was not run, so they have no results.
- `results_ablation1.txt` (component ablation) and `results_final_minisim.txt` (final dev + real days) are the raw outputs; `tools/minisim.py` and `tools/evalfast.py` reproduce them.
