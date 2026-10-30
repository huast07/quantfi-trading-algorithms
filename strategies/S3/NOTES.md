# S3: LYCHEE voucher volatility relative value

`trader.py` trades only VOUCHER_6800..8100 (limit 50 each) and LYCHEE (limit 200).
It is the component version of the design (`variants/components.py` is the same file).

## 1. Design

### Shared estimators

- **UnderlyingModel (LYCHEE).** The model keeps an EWMA tick variance (span 500) for the jump guard.
  It also keeps an EWMA of 10-tick squared returns (span 300 samples) as realised variance for the VRP kill switch; 10-tick returns avoid the ACF(1) -0.10 bias in 1-tick RV.
  Squared moves are winsorised at 5 sigma before they enter either EWMA.
- **SmileModel.** IV comes from a Black-Scholes inversion: 3 Newton steps per tick, warm-started from the last tick's IV, with an exact `math.erf` normal CDF.
  T = `DAYS_TO_EXPIRY_AT_OPEN` (5.0, the generator convention) minus timestamp / 1,000,000.
  The smile IV = a + b m + c m^2, m = ln(K/S)/sqrt(T), is fitted by closed-form weighted least squares over the 10 strikes (a 3x3 solve).
  The weights are vega^2 / (residual variance + rounding variance), i.e. inverse IV-error variance (GLS).
  The shape (b, c) is EWMA-smoothed (span 1,000 ticks) because it is constant in the generator and noisy tick to tick.
  The level a is refit every tick given the smoothed shape.
  Each strike's residual is r = mid - BS(S, K, T, smile IV), in price units.
  Per strike, EWMAs (span 3,000) of r^2 and of r_t r_{t-1} give the residual sd and an online AR(1) phi = cov / var, clipped to [0.95, 0.9995].
  The priors are params.json's residual_sd and phi = 0.993.
- **A wrong T degrades gracefully.** The fit, the residuals and the deltas are all computed under the same T, so a wrong T rescales IV and moneyness but leaves the price-space residual, which is the signal, almost unchanged.
  The real days (true T unknown; the EDA assumed 8/7/6) earn about as much as the synthetic ones.

### Sub-strategies (intent / edge / variance, per the orchestrator brief)

| Component | intent | edge() per lot | variance() per lot |
|---|---|---|---|
| `VoucherRV` (one per strike) | (price, qty) orders for the full limit given position q | \|r\| (1 - rho) - half spread, rho = phi^H | sd_r^2 (1 - rho^2), the residual risk not yet reverted at the horizon |
| `VegaTilt` | target short position, Kelly-style shift / (risk aversion x vega sd) | expected hedged bleed 0.5 Gamma S^2 (IV^2 - RV^2) x horizon | (vega x IV factor sd 0.0015)^2 |
| `DeltaHedger` | LYCHEE takes back to the edge of the band around -book delta | minus the half spread (a cost) | LYCHEE tick variance |
| `LycheeMaker` | passive bid/ask at the touch, leaning toward the hedge target | online EWMA of the 1-tick markout of our LYCHEE fills | LYCHEE tick variance |

The book's net delta (voucher delta plus LYCHEE after the hedge) is stored in traderData as `bd`, and the voucher-only delta as `vd`.
`Trader.book_delta` holds the same value.
An orchestrator that owns book-wide hedging can drop `DeltaHedger` and read `vd`.

### VoucherRV rule

- The value over the holding horizon is v = F + rho r, with F the smile price and rho = phi^H (H = 120 ticks, so rho ~ 0.43): the residual is expected to revert.
- The reservation curve is v(q) = v - slope q, with slope = RISK_AVERSION x sd_r / 50 and RISK_AVERSION = 0.35 (Avellaneda & Stoikov 2008 inventory skew, linearised).
  So the target position at price p is (v - TAKE_EDGE - p) / slope for buys and (v + TAKE_EDGE - p) / slope for sells.
  This sizes by expected edge relative to residual risk: about 2 sd of mispricing already reaches the full limit.
- **Taking.** We take every book level whose price is through the curve by at least TAKE_EDGE = 1.5.
  This means buying cheap and selling rich, on the same side as the IV-rule takers.
- **Resting.** We rest a quote at the touch only on the side the rule takers do not hit: a bid when r < 0 (they lift asks of cheap strikes) and an ask when r > 0, at most 10 lots.
  At the touch beats behind it, because prosperity3bt fills every trade at or through our price with no queue.
- **Exits** come from the same curve: as r reverts, the target shrinks and then flips.

### Risk controls

- A delta soft cap penalises the value by 0.05 x excess delta x own delta once |voucher delta| > 170, so the LYCHEE limit can always absorb it.
- The hedge uses a Whalley-Wilmott style no-trade band of +/-50 deltas and trades back to the band edge only.
- **Jump/gap guard.** A LYCHEE move above 6 sigma starts a 50-tick cooldown, during which vouchers may only reduce |position| and the LYCHEE maker stops; the hedger keeps working.
  This covers the black-swan, flash-crash and opening-gap ramps.
- The VRP tilt has a kill switch at IV/RV < 1.10, but the tilt itself is off in the shipped version (see variants).
- If the smile cannot be fitted (fewer than 4 valid strikes) the hedger keeps the last voucher delta instead of unhedging.
- Every product's orders are clipped so position plus all buys, and minus all sells, stay within the limit.
- `run()` catches all exceptions, logs them and trades nothing that tick.

## 2. Statistics behind each component

- **Residual AR(1).** params.json gives phi 0.992-0.994 (half-life ~100 ticks) and sd 2.1-5.3 by strike (largest at 7300-7600).
  The spread is 3 at 7200-8100 and 5-6 at 6800/7000.
  A 2 sd mispricing at 7500 (~10) therefore pays about 10 x (1 - 0.43) - 1.5 = 4.2 per lot over 120 ticks.
- **The IV-rule takers are on the same side.** Their side has corr -0.47 to -0.87 with the residual, and 86-95% of prints are rule-consistent (Trades report p. 26).
  We copy their side and never rest where they trade.
- The horizon sweep (H = 30 / 60 / 100 / 150 / 300 gave 117k / 351k / 442k / 453k / 216k over 9 days) peaks at 100-150, matching the ~100-tick half-life.
- **IV > RV by 20-30%** (EDA p. 22) motivated the VRP tilt, but a delta-hedged ATM short earns only ~4.7 per lot per day against a vega risk of ~10 per lot per day (factor sd 0.0015 x vega 6,600).
  Measured, the tilt costs far more than it earns (section 4).
- **Smile shape.** The generator has a constant skew and curvature, which justifies the heavy shape smoothing.
  Refitting the shape every tick (SHAPE_SPAN = 1) absorbs 3 of the 10 residuals' degrees of freedom and cost 14% of PnL.
- **Delta.** Plain BS delta beat the sticky-delta smile-adjusted delta (276k vs 269k over 9 days in sweep 1; 492k vs 486k in sweep 3).
  The EDA betas sit only slightly above BS delta.
- **LYCHEE making** is about neutral (MAKE_SIZE 0 vs 10: 491k vs 492k).
  It is kept because the EDA's at-touch replay is positive on all three real days.
- **Wings.** VOUCHER_6800 loses on all three real days (-1.4k to -5k) but earns on synthetic days.
  This matches the Trades report: rule-consistent prints at 6800 have a 100-tick markout of -3.3 to -5.7, so the quadratic smile is poorly identified there.

## 3. Results

RESULTS_PLACEHOLDER

## 4. Variants tried

The 9-day screen is regular-day, lychee-trend and vol-spike-skew x seeds 1-2, plus real days -2, -1, 0; the totals are summed PnL on my products.

| Variant | 9-day total | Verdict |
|---|---|---|
| v1_initial (RA 1.0, TAKE_EDGE 0.5, band 15, smile delta on) | 269k | baseline |
| RA 0.5 / 2.0 | 323k / 166k | lower risk aversion is better |
| TAKE_EDGE 0 / 1.5 (v1 base) | 175k / 302k | 1.5 kept |
| Band 5 / 40 (v1 base) | 226k / 300k | wider is better |
| PASSIVE_MAX 0 / 30 | 253k / 269k | passive rule-side quotes add ~6%; flat above 10 |
| SHAPE_SPAN 1 (no shape smoothing) | 232k | rejected |
| Sweep 2 base (RA 0.5, TE 1.5, band 40, BS delta) | 442k | |
| RA 0.25 | 467k | flat 0.25-0.5, so 0.35 chosen |
| TE 1.0 / 2.5 | 436k / 395k | flat at 1.0-1.5 |
| Band 25 / 70 | 420k / 467k | 50 chosen: more mean comes with more unhedged delta risk |
| SHAPE_SPAN 2000, H 150, H 60 | 454k, 453k, 351k | span 1,000 and H 120 chosen |
| Shipped (RA 0.35, H 120, span 1000, band 50) | 492k | **shipped** |
| + VRP tilt 0.5 / 2.0 days | 327k / 74k | rejected: the short-vega bias crowds out the RV trade and loses on IV moves |
| Band 200 (effectively unhedged) | 521k | rejected: higher mean, much higher delta variance |
| Smile-adjusted delta | 486k | rejected |
| MAKE_SIZE 0 | 491k | neutral |
| `meanadj` (slow per-strike residual mean, span 3,000) | 469k | rejected: it does not fix 6800 on real days and costs on synthetic ones |

## 5. Computation

TIMING_PLACEHOLDER

## 6. Proposals

1. **Wing haircut learned online.** VOUCHER_6800 is the only strike that loses on real days, matching the EDA's negative rule-side markout there.
   Track each strike's realised, delta-hedged PnL per lot with a Normal-Gamma posterior and scale its slope up when the posterior mean edge turns negative.
   That would recover ~3k a real day without hard-coding a strike list.
2. **Hedge through the vouchers, not LYCHEE.** The wider bands earned more (band 200: +6%), because LYCHEE hedging pays ~2 a unit.
   Pairing a cheap and a rich strike with similar delta (the IV-rule residuals are independent across strikes) would cut the net delta before any LYCHEE trade.
   A minimum-variance hedge-ratio allocation across strikes could replace part of the LYCHEE hedge.
3. **Orchestrator-level netting.** The voucher book's delta (`vd`) can be netted against any other LYCHEE sub-strategy's inventory before hedging, which saves the spread on both.
4. **Skip the VRP tilt intraday.** The variance premium (~4.7 per ATM lot per day) is too small against IV-factor noise (sd ~10 per lot) at a one-day horizon.
   Revisit it only if the competition runs several days with positions carried over.

## References

Avellaneda & Stoikov (2008); Whalley & Wilmott (1997); Carr & Wu (2009); Gatheral (2006); Derman (1999); Hull (2018); Black & Scholes (1973); Abramowitz & Stegun (1964) for the normal CDF used in v1.
