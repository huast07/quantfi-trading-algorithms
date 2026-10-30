# S1 - Diversified, inventory-aware market maker

Products: the 15 benign delta-one products (no TELLURIUM, no vouchers).
File: `trader.py` (self-contained; `datamodel` + stdlib only).

## 0. Two facts about the engine that drive the design

1. **Fill model.** prosperity3bt fills a resting order against every tape trade at our price or better, up to the trade's full size, ahead of the bot's book.
   Noise takers hit the touch of the same tick's book (`takers.hit_touch`).
   So a quote AT the touch gets exactly the same fills as one inside it, at a better price, and quotes behind the touch get no fills.
   Passive edge per lot is therefore the half spread, and size per fill is capped by the taker's size (1-6).
2. **Book model.** Each level sits at `round(center +/- half_width) +/- U{0..jitter}` around a hidden center (`generator/book.py`).
   The book never quotes through fair, so value takes need a fair value that differs from the book center: quote noise (PAPER_LANTERNS), an OU lean (TOFFEE_CAKE), or a regime break.

## 1. Design

One sub-strategy class per archetype, all sharing one engine (`MarketMaker`):

| Class | Products | Fair value | Inventory valuation |
|---|---|---|---|
| `AnchoredMaker` | AMETHYST | `PlateauFair` with a 10,000 prior worth 200 ticks; the change test is the anchor-break guard | plateau |
| `PlateauMaker` | GOLDEN_PEARLS, PINK_PEARLS | `PlateauFair`: EWMA-200 plateau, change test on an EWMA-5, tracking mode until 20 calm ticks; GOLDEN adds a 10-tick drift lookahead while tracking a step | plateau / tracked mid |
| `SmoothedMaker` | PAPER_LANTERNS | `LevelFair`, local-level Kalman with gain fixed to EWMA span 5 | filtered level |
| `MeanRevertMaker` | TOFFEE_CAKE | `MeanRevertFair`: OU Kalman (kappa 0.0046/tick, gain 0.5 = span 3) around an anchor learned by EWMA-3000 from a 5,000 prior | E[fair in 50 ticks] = f + (1 - phi^50)(mu - f) |
| `RandomWalkMaker` | JELLY, PEANUT_BUTTER, LYCHEE, DRAGONFRUIT, GRANADILLA, MANGOSTEEN, FRUIT_BASKET, WHITE/BLACK/BLUE_PEARLS | `LevelFair`, Kalman gain from online q/r (gives about the raw mid when quote noise is small) | filtered level |

Shared engine, per tick, all O(1):

- **`MidStats`**: EWMA (span 500) of Var(dm) and Cov(dm_t, dm_t-1) for mid changes dm.
  The local-level identities give fair-innovation variance `q = Var + 2 Cov` and quote-noise variance `r = -Cov`.
  So sigma_t^2 = q is the variance that actually creates inventory risk, not the mid's noise.
- **Reservation price and size by edge** (Avellaneda-Stoikov / Gueant-Lehalle-Fernandez-Tapia with a quadratic inventory penalty): `r = fair_inv - kappa q`, with `kappa = max(gamma H sigma_t^2, half_spread / (0.8 L))`.
  Maximising `v (edge) - kappa/2 ((q + v)^2 - q^2)` gives target position `(fair_inv - price - adverse) / kappa`.
  The quoted size is target minus position, so size grows with edge and shrinks with inventory and sigma_t.
  The kappa floor makes the passive band at most 80% of the limit (the soft cap).
- **Takes**: the same target formula with `kappa / TAKE_BAND_MULT` (4) and a hurdle of `TAKE_Z = 2` standard errors of the fair estimate (Kalman posterior sd `sqrt(K r)`, or plateau `s / sqrt(n)`).
  This covers value takes (e.g. AMETHYST asks below 10,000, TOFFEE far from its anchor) and inventory flattening beyond 4x the passive band.
- **Quote offset**: `OffsetBandit`, a Beta-Bernoulli fill rate per offset (touch / improve by one), chosen by Thompson sampling on P(fill) x edge.
  In this engine it converges to the touch, because fill rates are equal and the edge is one tick larger; in an engine where improving earns priority it would learn to improve.
- **`AdverseSelection`**: markout cost per passive lot, estimated as decayed fill inventory X (20-tick half-life) times later fair changes, divided by lots plus a 50-lot prior at 0 (Normal shrinkage).
  It is subtracted from passive edge, which is what protects the book in `toxic-flow`.
- **Risk controls**:
  - **Jump/trend guard** (all products except plateaus): it fires on a tick move > 5 sigma (and >= 2 ticks), or on a residual `e = mid - EWMA20(mid)` beyond 6 sd(e).
    Here sd(e) = s (1-a) / sqrt(a(2-a)) is exact for a random walk.
    For 50 ticks it quotes only the side the move favours, suspends value takes, and **flattens inventory that the move runs against** by crossing.
  - TOFFEE keeps the guard but does not flatten: a jump in an OU product is a reversion opportunity.
  - **Plateau break**: while tracking a break, the book quotes only the favoured side, and when the break exceeds 0.5% of price (GOLDEN steps of ~100 = 1.3%, but not PINK's routine 10-point jumps) it flattens.
  - All orders are clipped so position plus all same-side orders stays within the limit (`clip_to_limit`).
  - A per-product exception is caught and counted in `mem["err"]`, so one product can never kill the tick.

### Sub-strategy interface (Phase 3 orchestrator)

Every class above implements:

- `intent(state, product, mem) -> [(price, signed_qty)]`, computed as if it owned the whole limit, given position q; it is already limit-clipped.
- `edge()`: EWMA over ~200 lots of realised `side x (fair at order time - fill price)` per lot, minus the `AdverseSelection` markout cost.
- `variance()`: risk per lot over the markout horizon, `20 x q_t` (fair-innovation variance from `MidStats`).
- state lives in `mem` (one small dict per product, about 30 floats, serialised in traderData).

`Trader.run` only loads traderData, calls `SUB_STRATEGIES[product].intent`, clips and serialises.

## 2. Statistics behind each component

| Component | Evidence |
|---|---|
| AMETHYST 10,000 prior | EDA: mid never left 9,999.5-10,000.5; ACF(1) -0.50; best fair EWMA span 200 (RMSE 0.35 vs 0.50). Params: constant 10,000, book half-width 1 + jitter 1, so touch edge is 1-2 |
| Plateau change test | Noise sd around the plateau is about 0.35 (s2 ~ 0.125); 5 sd of an EWMA-5 is about 0.8, while the mid can only be 0.5 from a constant plateau, so false alarms are impossible on AMETHYST. GOLDEN steps ramp at about 1.2/tick, so detection takes ~2 ticks |
| GOLDEN lookahead 10 | EDA: after every move > 2, price kept falling ~33 over 20 ticks |
| PAPER span 5 | EDA: best RMSE at span 5 (1.35 vs 1.61). Local-level check with params (q = 0.447^2, r ~ 0.83 + jitter): steady-state Kalman gain 0.36, i.e. span 4.6 |
| TOFFEE OU | params kappa 0.0046 (half-life 150 ticks), sigma 2.24, mean 5,003; EDA variance ratio at 1,000 ticks ~0.11. Stationary sd 23 vs spread 14, so leaning against deviations pays. Real days: ~2,000 lots/day each way, buys near 4,994 and sells near 5,008 |
| Take hurdle | v1 without it: PAPER traded 870 lots/day against ~260 lots of noise flow, buying above where it sold (-3.1k on the real days); with TAKE_Z = 2 it made +6.1k |
| Trend guard | v1 used an EWMA-5 drift test: it false-triggered on LYCHEE's real 2-tick runs (-7.3k on day -2). The EWMA-20 residual at 6 sd fixed that (-0.8k), and adding flattening turned black-swan-squeeze from -2.7k to +36.9k |
| gamma H = 0.03 | sweep: 0.01 gives 33.2k, 0.03 gives 33.3k, 0.1 gives 18.8k on the 12-case subset (flat at 0.01-0.03) |

## 3. Results

Official `compare.py --suite dev` (42 cases x seeds 1-2) on the final `trader.py`, from `results/dev_final.md`:

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | S1 | 38,037 | liquidity-spiral (15,638) | 14,598 | 5 | 4,660 | 0 | 0 |
| 2 | reference | -3,363 | busy-day (-10,063) | -26,522 | 35 | 18,864 | 0 | 0 |

Paired difference vs the reference: +41,400, 95% CI [37,982, 45,127].
Every dev case is positive; the lowest are liquidity-spiral 15.6k, black-swan-squeeze 21.3k, vol-regime-switch 24.4k and quant-quake 27.5k.

Real days (gate: positive on each):

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches |
|---|---:|---:|---:|---:|---:|
| S1 | 32,494 | 35,658 | 27,994 | 96,146 | 0 |

Tier-weighted PnL by product (dev): TOFFEE_CAKE 31,224; JELLY 3,619; GOLDEN_PEARLS 1,803; BLACK_PEARLS 787; PAPER_LANTERNS 710; WHITE_PEARLS 688; AMETHYST 587; PINK_PEARLS 438; PEANUT_BUTTER 250; DRAGONFRUIT 96; FRUIT_BASKET 44; MANGOSTEEN -309; BLUE_PEARLS -347; LYCHEE -613; GRANADILLA -941.
The reference loses about 9.5k a day on PEANUT_BUTTER alone; S1 makes +250 there by sizing down with sigma^2 (kappa = gamma H sigma^2).

Weak cases (5, all **positive**, all beating the reference on every seed; they are Weak only because they sit more than one sd below S1's own mean or its usual edge):

- liquidity-spiral (+15.6k): the market maker withdraws, so passive flow dries up during a slow decline.
- black-swan-squeeze (+21.3k): inventory held when the ramp starts is flattened at a loss; v2, without the flatten, lost 2.7k here.
- vol-regime-switch (+24.4k): kappa rises with sigma^2, so quoting shrinks in the 3x regime (by design).
- toxic-flow (+34.7k) and one-sided-flow (+38.0k): only Weak relative to the reference's edge; the small loss is in GRANADILLA (~-1.1k to -1.5k).


## 4. Variants tried

12-case subset (all observed cases plus fat-tails, toxic-flow, one-sided-flow, mean-reversion-decay, black-swan-squeeze, opening-gap and vol-regime-switch) x seeds 1-2, tier-weighted, plus real-day total.
Files are in `variants/` (`make_variant.py` regenerates each sweep from `trader.py`).

| Variant | Change | Subset W | Real total |
|---|---|---:|---:|
| v1_base | first engine (drift lookahead in the guard, no take hurdle) | quick 51.2k | 88.3k |
| v2_takehurdle | take hurdle 2 SE; guard only pulls a side | full dev 34.7k | 95.2k |
| v3_flatten | EWMA-20 residual trend test + flatten on guard | (stress subset 37.7k) | 91.8k |
| v4_ouguard | no flatten for TOFFEE | 33.3k (full dev 35.5k) | 92.0k |
| sw_band1 / sw_band4 | TAKE_BAND_MULT 1 / 4 (8 not run: machine overloaded) | 25.7k / 35.2k | 70.1k / 96.1k |
| sw_gamma01 / sw_gamma10 | RISK_GAMMA 0.01 / 0.1 | 33.2k / 18.8k | 93.1k / 57.0k |
| sw_hold25 / 100 / 200 | OU_HOLD_TICKS | 25.0k / 34.0k / 30.4k | 73.6k / 90.0k / 81.9k |
| sw_takez1 / sw_takez3 | TAKE_Z 1 / 3 | 33.5k / 32.0k | 89.9k / 86.9k |
| sw_cap06 / sw_cap10 | SOFT_CAP 0.6 / 1.0 | 31.8k / 33.8k | 81.8k / 96.8k |
| sw_touchonly | never improve (bandit off) | 33.3k | 93.1k |

Chosen: v4 with TAKE_BAND_MULT = 4 (`v5_final.py` = `trader.py`).
SOFT_CAP 1.0 was +0.5k but removes the inventory buffer, so I kept 0.8.
The bandit is PnL-neutral here (it converges to the touch) and is kept because the live engine's fill rule is unknown.

## 5. Run time

`run()` alone, measured with a timing wrapper on real day 0: **1.4 ms/tick** on an idle machine (v2, same per-tick work as the final).
compare.py reports 4-7 ms/tick (5.06 mean), but that wall clock includes the engine and was measured at load average ~430 with five agents sharing 8 cores.
Work per tick is O(products x book levels); state is about 30 floats per product (~6 KB of traderData).
Remaining costs: JSON encode of traderData (~0.3 ms) and Thompson sampling (normal approximation, sampled only when improving is allowed).

## 6. Proposals

1. **TOFFEE_CAKE OU taking is the dominant edge** (31.2k of 38.0k tier-weighted on dev, and about 26k per real day).
   The S2/allocator layers should give TOFFEE the most risk budget, and S2 could estimate kappa online (RLS of df on f - mu) so `mean-reversion-decay` (kappa x 0.2-0.35) re-sizes the lean automatically.
   OU_HOLD_TICKS 50-100 is flat; 25 and 200 lose 8k and 3k.
2. **Multi-level center estimate.** Each book level is an independent `round(c +/- hw_k) +/- U{0..j}` observation of the same center c.
   Averaging the L1-L3 implied centers would cut fair-value noise well below the raw mid's, which tightens the take hurdle on every product.
   The EDA only tested volume-weighted mids, which are a different and worse estimator.
3. **Basket legs and pearls lose small amounts passively** (GRANADILLA -0.9k, LYCHEE -0.6k, MANGOSTEEN -0.3k, BLUE -0.3k tier-weighted).
   Their spread edge (0.75-2 per lot) is below the inventory drift risk at the ~15-25 prints/day they get.
   Hedging leg inventory through FRUIT_BASKET (2D+3G+1M), and WHITE/BLACK through their -0.6 correlation, would cut variance without giving up flow.
4. **Regime flatten triggers are profitable stress alpha**: black-swan-crash makes ~90-110k because the guard sells into the 5-30 tick ramp.
   A small continuation trade after a confirmed > 6 sd residual (like v1's lookahead, but only on the EWMA-20 test) is worth testing in S2, with the LYCHEE false alarms as the control.
