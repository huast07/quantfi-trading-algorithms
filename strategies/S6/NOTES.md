# S6: hedged basket, thin-leg makers, DRAGONFRUIT trend, PEANUT_BUTTER maker, pearl group hedge

S6 supplies sub-strategies for the instruments that had none (FRUIT_BASKET, DRAGONFRUIT, GRANADILLA, MANGOSTEEN, PEANUT_BUTTER), plus two hedges (basket legs, pearl group).
None of them is meant to win alone.
The orchestrator's live mean-variance gate decides when each one trades, so each class exposes `intent`, `edge` and `variance`, and `Trader.run` combines them standalone.

## 1. Design

One risk-aversion constant ties everything together.
`RISK_GT = half_spread_basket / (BASKET_CAP * sigma_basket^2)` is the Avellaneda-Stoikov skew coefficient (gamma times horizon) for which the reservation-price skew at the basket's cap equals the basket half spread.
Every no-trade hedging band is then the Davis-Norman / Whalley-Wilmott cube-root band for that same risk aversion: `band = (3c / (2 * RISK_GT * sigma^2))^(1/3)`, where c is the half spread.
At the EDA sigmas that gives bands of about 5.7 (DRAGONFRUIT), 6.6 (GRANADILLA) and 5.2 (MANGOSTEEN) lots.

| Class | Product | Model | Estimators | Sizing | Risk controls |
|---|---|---|---|---|---|
| `HedgedBasketMaker` | FRUIT_BASKET | fair = 2D + 3G + 1M + premium; the premium is a random-walk Kalman state (Q = 4.15^2 from params.json premium_sigma, R = basket + MANGOSTEEN quote noise^2) | scalar Kalman, EWMA tick variance, EWMA per-lot fill markout | 3 lots per side (largest taker print), improve the 6-wide touch by 1, never closer than 1.5 to the reservation price | AS skew `q * RISK_GT * sigma^2`; cap 12 lots (the 3-per-lot GRANADILLA hedge must fit in 40); a premium innovation above 5 sigma resets the filter and skips quoting for a tick |
| (hedge) | legs | `hedge_targets(q) = -(2, 3, 1) * q` | - | target position on each leg | executed by the leg maker inside its band, so most of the hedge is done passively |
| `LegMaker` | D, G, M | passive quotes at the touch around a reservation price skewed by `dev = q - anchor`, anchor = basket hedge (+ trend lean on D) | EWMA tick variance, per-lot passive markout | 2 lots per side; cross back to the band edge when `abs(dev) > band` | skew `c / band` per lot, so resting and crossing are equally attractive at the band edge; quotes pulled for a tick after a 5-sigma move; the anchor is clipped to `limit - 2` so maker and hedge share each leg's limit |
| `DragonfruitTrend` | DRAGONFRUIT | conjugate-normal posterior on the drift with prior N(0.02, 0.02^2) (EDA mean real-day drift +200/day), exponential forgetting with a one-day half-life | posterior mean; fast EWMA drift (half-life 1,000) | lean `TREND_MAX * clip(mu_post / mu0, -1, 1)`, max 10 lots, fed into the leg maker's anchor | regime-flip guard: if the fast drift is 2 standard errors against the lean, the lean goes to 0 |
| `PeanutWideMaker` | PEANUT_BUTTER | Avellaneda-Stoikov: `r = mid - q * gamma * sigma^2`, half width `= 3 + gamma * sigma^2 / 2`, never inside the touch | live EWMA sigma, per-lot markout | 2 lots per side, cap 10 | skew equals the half spread at the cap at the EDA sigma; crosses back when above the cap; pulled after a 5-sigma move |
| `PearlGroupHedge` | WHITE/BLACK/BLUE | minimum-variance cross hedge of the book-wide pearl vector x with EWMA covariance S: trading h of pearl i removes `(Sx)_i^2 / S_ii` at `h = -(Sx)_i / S_ii` | 3x3 EWMA covariance of tick returns (half-life 2,000), prior from params.json correlations | trades only the part of h beyond the Davis-Norman band, crossing at the touch | picks the pearl with the largest exact variance drop; never trades a pearl in the direction that would unwind another strategy's position there; clips to both its own and the book's limit |

The pearl hedge reads `getattr(state, "book_position", None) or state.position`.
Standalone it has no pearl positions and never trades.
`tools/test_pearl_hedge.py` checks it with a harness: long 20 WHITE elsewhere makes it buy 4 BLACK (the -0.58 correlation leg), it does nothing when flat, it hedges its own position, and it refuses to unwind others when all three are long.

`Trader.run` wraps the whole tick in a try/except that counts errors in `traderData["err"]` and returns no orders, so it can never raise; every order is clipped so position plus all same-side orders stays inside the limit.

## 2. Statistics behind each component

- Basket: legs explain 64-78% of 100-tick basket returns with betas near (2, 3, 1) every day.
  The premium is non-stationary (ADF p 0.19-0.99, -779 to +809 on day -2), so it is tracked, not traded.
  With Q = 17.2 against R = 1.47 the Kalman gain is about 0.93, so fair value is close to the mid but filters the basket's 1.14 quote noise.
  Passive fill edge measured on the real days: +2.3 per lot (day -2).
- Legs: tick sigma 2.05 / 1.63 / 2.34, spread 4, 12-33 prints a day, at-touch passive replay positive on GRANADILLA on all days (+32 to +56 per lot-day).
- DRAGONFRUIT: +216.5, +144.5, +237.5 on the three real days; the generator's own drift is 0, so only the real days and `trends-continue` carry it.
  The per-tick drift (0.02) equals its one-day standard error (2.05 / 100), so an online estimate alone cannot confirm it within a day, hence the informative prior with forgetting.
- PEANUT_BUTTER: tick sigma 4.8 against spread 6, no autocorrelation or imbalance signal, aggressor 5-tick markout -2.5 to -3.0 (passive side earns that), but trend days wipe it out.
- Pearls: params.json return correlations WHITE-BLACK -0.58, WHITE-BLUE -0.45, BLACK-BLUE -0.46.

## 3. Results

Final `trader.py` = v1 plus the winsorised trend guard (`variants/trend_winsor.py`, identical code).
The full dev table is v1's (`results/dev.md`); the guard change only touches DRAGONFRUIT on ticks with a move above 5 sigma, and was checked on the six cases that have such moves (`results/dev_trend.md`).

Dev suite (42 cases x seeds 1-2), tier-weighted PnL, v1:

| Product | S6 | reference |
|---|---:|---:|
| FRUIT_BASKET | 376 | 1,018 |
| DRAGONFRUIT | -34 | 13 |
| GRANADILLA | 331 | -1,082 |
| MANGOSTEEN | -183 | -1,065 |
| PEANUT_BUTTER | 74 | -7,875 |
| Total (S6 products) | 564 | -8,991 |

Overall: weighted 564 vs reference -3,363 (all products), Weak 8, 0 breaches, 0 crashes.
Worst case is black-swan-crash (-4,292 in v1, -3,612 with the guard; DRAGONFRUIT trend lean caught by the crash).
liquidity-spiral is the other loser (-2,030, mostly DRAGONFRUIT); heavy-flow, busy-day and clustered-arrivals lose on FRUIT_BASKET (more fills, so more unhedgeable premium inventory).

Real days (final):

| Product | Day -2 | Day -1 | Day 0 | Total |
|---|---:|---:|---:|---:|
| FRUIT_BASKET | -1,548 | -3,629 | -1,106 | -6,283 |
| DRAGONFRUIT | 1,628 | 1,589 | 4,458 | 7,675 |
| GRANADILLA | 1,217 | 1,547 | -1,242 | 1,522 |
| MANGOSTEEN | 144 | 769 | 79 | 991 |
| PEANUT_BUTTER | 11 | 391 | -520 | -118 |
| Total | 1,452 | 666 | 1,669 | 3,787 |

0 breaches; 0.35-0.98 ms/tick (it varied with machine load, which was 200-450 during these runs).
Fill edge measured by `tools/diag.py` (fill price vs mid): basket +2.2 to +2.3 per lot, PEANUT_BUTTER +3.3 per lot, leg fills about 0 (they are mostly hedge and trend crossings).
The basket loses on the real days although its fills earn the spread: the premium trended (+1,590 on day -2), and that part of the basket's risk cannot be hedged with the legs.
The basket plus its leg hedges (excluding the trend) is roughly flat across the real days.

### Variants

| Variant | Change | Dev weighted | Real total | Verdict |
|---|---|---:|---:|---|
| v1 | as designed | 564 | 3,787 | kept |
| basket_cap6 | basket cap 12 -> 6 (twice the skew) | 239 | 5,260 | rejected: worse on dev (CI of the difference [174, 469]); its real-day gain is basket noise on 3 days |
| no_trend | TREND_MAX = 0 | 25 | -1,206 | rejected: the trend lean is the main contributor, on dev too (DRAGONFRUIT -573 without it) |
| trend_winsor | winsorise >5-sigma moves into the trend estimate instead of skipping them | +23 on the 6 crash/trend cases | 3,787 | adopted |

## 4. Gate hints

How each sub-strategy's `edge()` / `variance()` should be read, and when I expect the edge to be positive:

- **HedgedBasketMaker** (FRUIT_BASKET): the edge is positive per fill (+2 to +5 per lot, prior = the EDA 5-tick markout), but the inventory PnL is dominated by the premium random walk (sigma 4.15 per tick, about 415 per lot-day), so a markout gate will see a positive mean with a weak t-stat.
  Expect it to pay when the premium is quiet relative to flow: regular, quiet and wide-spread days.
  Expect it to lose under basket-dislocation, quant-quake and opening-gap (premium shocks), and on heavy-flow, busy-day and clustered-arrivals (more fills, more premium inventory).
  Gate it together with the leg hedges: its own position risk is `(1 - 0.70) * sigma_B^2` only if the legs are routed to S6 too.
- **LegMaker** (D/G/M): standalone passive edge is small (12-33 prints a day); positive on GRANADILLA at the touch on all real days, mixed on DRAGONFRUIT and MANGOSTEEN.
  Its fills are mostly hedge and trend execution, so do not switch a leg off on its markout alone while the basket is routed here: the leg position is the basket hedge, and cutting it unhedges the basket.
- **DragonfruitTrend**: positive edge only if the real-day drift (+200 per day) persists: trends-continue and the real days, where it makes 1.6k-4.5k a day.
  The generator's drift is 0, so on ordinary synthetic days its expected PnL is 0 and its variance is 10 lots x 2.05^2 per tick; it loses under black-swan-crash, liquidity-spiral and regime-flip until the guard trips.
  `edge()` returns the posterior drift per lot per tick (~0.02 at the prior), `variance()` the per-tick sigma^2; a markout-based gate needs a long horizon (about a day) to see it, so a prior allocation is more appropriate than waiting for z_on.
- **PeanutWideMaker**: positive per fill (+3.3 per lot measured, prior +2.7) with tight inventory (cap 10); it loses on strongly trending or one-sided days (one-sided-flow, black-swan-crash).
  Dev: +74 against the reference's -7,875 on PEANUT_BUTTER.
- **PearlGroupHedge**: its edge is variance reduction, not markout, so its markout mean is negative by about the half spread per lot.
  `edge()` returns `RISK_GT * variance removed per lot - half spread` for its last trade (positive whenever it trades, by construction of the band).
  Give it a fixed allocation, or score it on the change in book variance; a markout gate would switch it off.
  It only trades when other strategies hold concentrated pearl exposure beyond the band (about 5 lots), and when correlations hold: under correlation-breakdown and quant-quake (pearl correlations flip) the EWMA covariance (half-life 2,000) lags and the hedge can add risk for a while.

## 5. Sub-strategies and estimators

| Class | intent | edge() | variance() |
|---|---|---|---|
| HedgedBasketMaker | quotes; `hedge_targets(q)` for the legs | EWMA per-lot passive markout (prior 4.6) | hedged residual `0.3 * sigma_B^2 / turnover` |
| LegMaker | quotes + band crossings around an anchor | EWMA per-lot passive markout | `sigma^2 / turnover` |
| DragonfruitTrend | target lean (lots) | posterior drift per tick | `sigma^2` per tick |
| PeanutWideMaker | quotes | EWMA per-lot passive markout (prior 2.7) | `sigma^2 / turnover` |
| PearlGroupHedge | one crossing order on the best pearl | risk-adjusted benefit per lot | 0 (risk-reducing) |

## 6. Proposals

- PEANUT_BUTTER and JELLY have a return correlation of +0.66 in params.json; a PEANUT_BUTTER maker could take its fair value from JELLY's move (or hedge PB inventory with JELLY at beta 0.66 * 4.8 / 3.14 = 1.0).
- The basket premium's risk (sigma 4.15 per tick, about 415 per day per lot) is the only unhedgeable part of the basket book; the gate should judge the basket maker together with its leg hedges, not alone.

## References

Avellaneda and Stoikov (2008), High-frequency trading in a limit order book.
Davis and Norman (1990), Portfolio selection with transaction costs; Whalley and Wilmott (1997), An asymptotic analysis of an optimal hedging model for option pricing with transaction costs.
Kalman (1960); Ederington (1979), The hedging performance of the new futures markets (minimum-variance hedge ratio).
Gatev, Goetzmann and Rouwenhorst (2006), Pairs trading (why the premium is not traded here: no mean reversion).
