# S4 - TELLURIUM jump specialist

Trades only TELLURIUM (limit 40).
Everything else is left to the other families.

## 1. Design

### Shared estimator: `JumpModel` (O(1) state, updated once per tick)

- **Jump detector (idea a).**
  A tick is a jump candidate when |mid change| > max(JUMP_FLOOR, JUMP_Z x sigma_calm).
  sigma_calm is an EWMA (alpha 0.002) of squared mid changes on calm ticks (no active jump response), so it tracks vol regimes.
  JUMP_FLOOR = 77.5 / 2 (half the smallest of the 30 real jumps); JUMP_Z = 10 (the largest calm move on 30,000 real ticks is 13.5 = 8.5 sigma).
  Between those two levels the empirical calm and jump densities do not overlap, so the likelihood-ratio test reduces to this threshold.
  A candidate is confirmed one tick later if the next tick is calm.
  Two outsized ticks within SHOCK_MERGE = 5 ticks are a ramp (crash / squeeze), not a one-tick jump: active jumps are dropped and new jump trades pause for SHOCK_COOL = 1,000 ticks (the crash liquidity windows last 500-1,500).
- **Size-scale posterior.**
  Jump sizes are modelled as scale x u, u drawn from the 30 real sizes (kernel bandwidth 12 for book jitter), with a log-normal prior on scale (sd 0.5) over a grid 0.5-3.
  This is what keeps the response model right in tellurium-storm (sizes x2): a 400 jump is impossible at scale 1, so the posterior moves at once.
- **Direction posterior (the day's up-probability p).**
  The generator draws p ~ Beta(c, c) per day; c is calibrated at 0.55 with a 95% interval 0.07-5.1.
  I put a log-normal prior on c (centre 0.55, log sd 1.1, matching that interval) over a 6-point grid and average the Beta-Binomial predictive (c + n_up) / (2c + n) with weights prior x B(c + n_up, c + n_down) / B(c, c).
  On a one-way day the predictive goes to ~0.9 after 3 jumps; on a mixed day the marginal likelihood shifts weight to large c and p stays near 0.5 (whipsaw handled without a special case).
- **Jump rate.** Gamma-Poisson: (5 + n) / (5,000 + t), prior 10 jumps per 10,000 ticks worth 5,000 ticks.
- **Response factor beta.**
  Conjugate normal regression of each non-jump mid change on the model's predicted response increment of the active jumps (prior N(1, 0.5^2), noise variance 25 per tick to allow for the trend's persistence).
  In tellurium-jumps-stick beta falls toward 0 after a few jumps and the fade trades stop.

### Sub-strategies (each exposes `mean_var(h)`, `intent(q)`, `edge()`, `variance()`)

| Component | Idea | Mean over h ticks | Extra variance | Status |
|---|---|---|---|---|
| `DriftRider` | (b) post-jump state machine | beta x sum over jumps of sign x [R(k+h) - R(k)], R(k) = drift(k) x scale + slope(k) x (size - 170.13 x scale) | chase impact (860 over the 200-tick window) + Var(beta) x R^2 | **on** |
| `DirectionTilt` | jump-direction persistence | h x rate x (2p - 1) x scale x (170.13 + beta x drift(600)) | none beyond the base | **on** |
| `ChaserSeller` | (c) sell to the chasers | rests the chased side at the touch for 200 ticks if premium - sign x E[move to 600 ticks] > 0; holds fills to 600 ticks or a 60/lot stop | n/a | off (no gain) |
| `FlowLead` | informed-flow detector | Page CUSUM of chase-vs-background print likelihood ratios; mean p x sign x 170 | none | off (false alarms) |
| `CalmMaker` | (d) calm making | 2-lot quotes outside the touch when no jump in 400 ticks, dropped on a jump | n/a | off (~0, see variants/v2_components.py) |

Base variance over h ticks (every component): sigma_calm^2 x LR_RATIO x h + rate x h x scale^2 x E[u^2].
LR_RATIO = 7.0 / 2.6 converts the one-tick variance into the long-horizon variance of the calibrated local trend (sigma 0.70, trend sd 0.31, phi 0.95 give (c + tau / (1 - phi))^2 ~ 7.0 per tick).

### Netting, sizing and execution (`Trader`)

- For each horizon h in {10, 25, 50, 100, 150, 200, 300, 400, 600, 1000, 2000} the trader sums the enabled components' means and variances, takes the h with the largest |mu| / sigma, and sets target = mu / (GAMMA x var), clipped to +-40 (mean-variance optimal holding, Markowitz; Kelly-style sizing by edge over variance).
  Summing means (not clipped targets) matters: summing separately clipped targets cut the dev score in half (variant c_dd vs v3_driftdirection).
- Execution: if the expected move over URGENT_H ticks exceeds the half spread in the trade's direction, take the book up to mid + that move; otherwise join one tick inside the spread.
  Trades smaller than MIN_TRADE = 3 lots are skipped unless flattening.
- Every order is clipped to the remaining buy / sell room, so the limit can never be breached.

### Risk controls

- The position cap is the per-jump stop: the largest possible jump loss is 40 x jump size; it is only taken when the posterior expects the jump to go our way.
- Shock mode (above) stops the model from reading a crash ramp as a string of small jumps that "should follow through".
- beta regression and the size-scale posterior turn the fade off when the response is absent or the sizes are rescaled.
- The direction tilt shrinks automatically on mixed days (concentration posterior), which is the whipsaw kill switch.

## 2. Statistics (evidence behind each component)

EDA numbers (Prices report p.13, Trades report p.24-25, params.json):

- 8 / 9 / 13 jumps per real day, mean size 156-178, max 300.5; calm tick sigma ~1.6; jumps are single-tick.
- Direction clustered within a day: 7 of 8 down (day -2), 9 of 9 up (day -1), 6 up / 7 down (day 0); calibrated Beta concentration 0.55 (95% CI 0.07-5.1).
- Calibrated response (params.json): drift +0.9 / +3.5 / +12.0 / +23.7 / +1.4 / -12.8 / -23.8 at 10 / 50 / 100 / 200 / 300 / 400 / 600 ticks; size slope -0.15 ... -1.16 (at 200) ... -0.98.
- Chasers sweep L2+ on 23-34% of prints, 87% of prints within 200 ticks of a jump; post-jump prints lose 35 at 500 ticks; the market maker widens ~1.1-1.7 ticks and thins the chased side to ~0.56-0.8 of its volume for ~400 ticks.
- Flow before a jump nets ~0 lots on real days (no anticipation).

My own measurements (`tools/jump_study.py`, threshold |d mid| > 50):

| Sample | Jumps | Calm sigma (MAD) | Max calm \|d\| | Signed move at 100 / 200 / 600 (mean) | Size slope at 100 / 200 / 600 | Resid sd at 200 |
|---|---|---|---|---|---|---|
| Real days -2, -1, 0 | 30 | 1.59 (1.48) | 13.5 | +14.9 / +19.4 / -52.0 | -0.88 / -1.28 / -1.97 | 111 |
| Synthetic observed tier, seeds 1-2 | 114 | 1.66 (1.48) | 10.0 | +15.2 / +37.2 / +48.6 | -0.92 / -1.19 / -1.14 | 91 |

- The real-day size slope at 200 ticks is -1.28 with standard error ~0.34 (resid sd 111 / (size sd 60 x sqrt 30)): the give-back of oversized jumps is a ~4-sigma effect on the real data, not only a generator assumption.
- Signed moves at 600 ticks differ in sign between real and synthetic because later same-direction jumps land inside the window (direction clustering), which is exactly what DirectionTilt models.
- Calm and jump moves are separated by a gap (calm max 13.5, smallest jump 77.5), so the detector has no measurable false-positive rate on the real days; black-swan-crash seed 2 produced 11 consecutive ~55 "jumps", which is why the shock rule exists.

PnL attribution of the final trader (`tools/diag.py`, holding PnL by ticks since the last jump):

| Day | Through jump ticks | Ticks 1-200 after | Ticks 200-600 after | Later | Spread paid (net of passive gains) |
|---|---|---|---|---|---|
| regular-day seed 1 (16 jumps, all down) | +103,729 | +14,187 | -13,013 | +2,083 | -2,586 |
| real day 0 (13 jumps, mixed) | +27,306 | +8,475 | +11,234 | +979 | -3,596 |
| tellurium-whipsaw seed 1 (16 jumps, mixed) | -6,564 | +24,034 | +22,960 | +303 | -5,651 |

So DirectionTilt earns on one-way days and DriftRider carries the mixed days.

## 3. Results

### Dev suite (42 cases x seeds 1-2) and real days, from `tournament/compare.py` (`results/dev.md`)

| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | S4 | 62,624 | quiet-day (35,351) | 5,512 | 1 | 16,221 | 0 | 0 |
| 2 | reference | -3,363 | busy-day (-10,063) | -26,522 | 35 | 18,864 | 0 | 0 |

Paired difference vs reference: +65,987, 95% case-bootstrap CI [56,105, 77,493].

| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick (whole backtest) |
|---|---:|---:|---:|---:|---:|---:|
| S4 | 49,974 | 27,534 | 44,398 | 121,906 | 0 | 0.71 |

Per product: all of it is TELLURIUM (+62,624 tier-weighted); the reference does not trade TELLURIUM (0), so S4 beats it on its product by 62,624.

### Per case (TELLURIUM PnL; cases that do not touch TELLURIUM give identical days and are grouped)

| Case(s) | Tier | Mean | Seed 1 | Seed 2 |
|---|---|---:|---:|---:|
| quiet-day | observed | 35,351 | 29,092 | 41,610 |
| tellurium-whipsaw | plausible | 40,473 | 35,082 | 45,864 |
| black-swan-crash | stress | 53,907 | 102,302 | 5,512 |
| black-swan-squeeze | stress | 55,974 | 84,615 | 27,334 |
| regular-day-varied | observed | 56,806 | 75,412 | 38,199 |
| intraday-seasonality | plausible | 57,320 | 94,386 | 20,255 |
| liquidity-drought | plausible | 59,778 | 93,969 | 25,587 |
| wide-spreads | plausible | 60,230 | 103,316 | 17,143 |
| regular-day (and 21 other cases that leave TELLURIUM unchanged) | observed | 60,884 | 104,402 | 17,366 |
| opening-gap | stress | 61,236 | 103,874 | 18,599 |
| tellurium-informed | plausible | 61,302 | 99,324 | 23,279 |
| flash-crash | stress | 61,470 | 104,526 | 18,415 |
| heavy-flow | plausible | 61,498 | 100,619 | 22,378 |
| vol-explosion | stress | 61,899 | 111,927 | 11,871 |
| vol-regime-switch | plausible | 62,318 | 106,255 | 18,382 |
| vol-clustering | plausible | 62,364 | 104,406 | 20,322 |
| liquidity-spiral | stress | 68,222 | 122,404 | 14,041 |
| fat-tails | plausible | 68,790 | 116,903 | 20,677 |
| tellurium-jumps-stick | plausible | 76,374 | 111,571 | 41,177 |
| busy-day | observed | 89,372 | 109,110 | 69,634 |
| tellurium-storm | stress | 230,702 | 327,358 | 134,045 |

Every one of the 84 dev days is positive (worst day +5,512, black-swan-crash seed 2).

### Weak cases

- **quiet-day** (+35,351): Weak only by the relative rule (more than one sd below S4's own mean of +64,877); it is positive on both seeds and beats the reference on every seed.
  Fewer jumps (6 and 11) mean fewer bets, and the edge per day scales with the jump count.

Seed 2 is weaker than seed 1 on most cases because seed 2's day starts with reversals (+-++++-+++++-++, 12 of 15 up), so DirectionTilt holds less until the posterior firms up; seed 1 is a one-way day (16 of 16 down).

## 4. Variants tried

Scores in this table come from `tools/bt.py` on the TELLURIUM-only cached days: an 18-case subset covering every case that changes TELLURIUM plus the regular days (`tools/subset.txt`), seeds 1-2, tier-weighted within the subset ("W"), plus the real days.
Files are in `variants/`; raw outputs in `results/ablation*.txt` and `results/sweep*.txt`.

| Variant | What it is | W (subset) | Worst case mean | Worst day | Real -2 / -1 / 0 | Verdict |
|---|---|---:|---:|---:|---|---|
| v1_model (GAMMA 1.5e-3) | joint drift + direction model, cautious | 3,948 (all 42) | 1,939 | -474 | 2,398 / 2,540 / 2,728 | too small |
| v1_g5e-5 | same, GAMMA 5e-5 | 53,893 | 9,666 | -25,055 | 27,265 / 29,853 / 12,566 | crash day loses |
| c_drift | (b) DriftRider alone, GAMMA 5e-5 | -15,685 | -50,012 | -80,171 | -6,232 / -6,724 / 48,312 | rejected alone: its fades are run over by the next same-direction jump |
| c_dir | DirectionTilt alone | 51,788 | -16,104 (whipsaw) | -51,214 | 41,464 / 29,494 / -9,322 | loses on mixed days |
| c_dd | drift + direction, separately clipped targets summed | 25,414 | -2,042 | -21,842 | 22,402 / 18,016 / 28,246 | netting by clipped targets wastes edge |
| c_chaser | (c) ChaserSeller alone (premium vs response only) | -20,564 | -111,928 (storm) | -189,329 | -9,106 / 746 / 12,395 | rejected: selling to chasers fades the day's direction |
| c_calm | (d) CalmMaker alone | -497 | -10,456 (informed) | -15,591 | 7,378 / 5,287 / -1,002 | rejected: ~0 on synthetic days, run over by lead flow |
| c_all (v2) | all four, targets summed | -124 | -24,249 | -36,636 | -2,530 / 7,542 / 40,566 | rejected |
| v3_driftdirection | **joint mean / variance per horizon + shock rule**, GAMMA 5e-5, URGENT_H 50 | 58,638 | 31,192 | 4,027 | 42,615 / 28,568 / 21,501 | base of the final |
| v3_driftdirectionchaser | + ChaserSeller with direction-aware edge | 56,457 | 30,822 | 9,733 | 35,975 / 33,258 / 23,607 | no gain, kept off |
| v3_driftdirectionlead | + FlowLead CUSUM | 26,060 | -20,126 | -48,367 | -28,099 / 34,224 / 1,169 | rejected: false alarms on real bursts |
| v3_directionlead | direction + lead | 18,183 | -22,169 | -87,560 | -50,925 / 33,666 / -40,906 | rejected |
| v3dd GAMMA 2e-5 / 1e-4 / 2e-4 | risk-aversion sweep | 61,932 / 43,923 / 28,206 | all > 17,000 | all > 1,500 | 92.6k / 79.7k / 59.0k totals | flat from 2e-5 to 5e-5 |
| v3dd URGENT_H 25 / 100 / 200 / 400 | take-vs-join horizon | 55,305 / 61,089 / 60,385 / 58,502 | all > 13,000 | all > 1,500 | 99.2k / 121.6k / 107.2k / 96.9k totals | flat from 100 to 200 |
| v3dd URGENT_H 100, GAMMA 2e-5 | | 64,844 | 35,570 | 6,685 | 49,974 / 27,534 / 45,160 | |
| **final trader.py** | URGENT_H 100, GAMMA 3e-5 (middle of the flat region) | dev: 62,624 (all 42) | 35,351 | 5,512 | 49,974 / 27,534 / 44,398 | **submitted** |

## 5. Speed

`tools/timing.py` wraps `Trader.run` inside the real prosperity3bt run: real day 0 with all 26 products, mean **0.21 ms/tick** (p50 0.08 ms, p99 2.1 ms); tellurium-storm seed 1 mean 0.25 ms.
compare.py reports 0.71 ms/tick for the whole backtest including the engine.
State is O(1): a handful of scalars, an 8-point scale posterior and at most the jumps of the last 600 ticks (3-6 entries; 15 in storm).

## 6. Proposals

1. **Orchestrator: give TELLURIUM the full limit and let DirectionTilt run alone on one-way days.**
   On regular-day seed 1 the jump-tick holding PnL is +103,729 of +104,402: a single posterior (2p - 1) carries most of the edge, so in Phase 3 this product should not share risk budget with others while p is far from 0.5.
2. **Cross-day prior for the direction concentration.**
   Three real days and the case catalogue disagree on c (0.55 vs 5 in whipsaw); the 6-point grid already learns it within the day, but day 1 starts from the prior. If the competition runs several day-1 sets, updating the c prior from day to day is free edge (statistic: the c log-posterior on day 0's mixed 6/7 split already moves weight toward c > 1).
3. **Size the fade by the real-day slope, not the generator's.**
   The real-day slope at 600 ticks is -1.97 vs the calibrated -0.98; with only 30 jumps that is within 2 se, but if day 1 looks like the real days, a stronger give-back makes the fade of oversized jumps worth more (beta regression would find it within a few jumps since it is not capped at 1).
4. **Flow lead, done right.**
   The CUSUM failed because real calm-period prints come in bursts (count dispersion 37-52 on real days), so a Poisson background is wrong; a negative-binomial background or requiring the burst to be one-sided over >= 5 orders would cut the false alarms. Informed-case upside is ~60k per day at full size.
5. **Chaser liquidity as execution, not as a strategy.**
   ChaserSeller lost alone but the joint model already joins inside on the chased side when it wants to fade; a post-jump quote at L1 (thinned to ~0.56-0.8) instead of one tick inside could earn the extra tick on fades without changing the target.

## Literature

- Merton (1976), jump-diffusion; Bates (1996), jumps and stochastic volatility: the price model and the jump/diffusion split.
- Lee & Mykland (2008), jump detection by a standardised return statistic: the robust z-score detector.
- Page (1954), CUSUM: the flow-lead detector (rejected variant).
- Gelman et al., *Bayesian Data Analysis*, hierarchical Beta-Binomial: the concentration-mixed direction posterior.
- Markowitz (1952); Kelly (1956) / Thorp (2006): q* = mu / (gamma sigma^2) sizing.
- Kyle (1985); Bouchaud et al. (2004): chase impact as permanent, per-lot price impact (the generator's model; used here as variance only).
- De Bondt & Thaler (1985); Jegadeesh & Titman (1993): over- and under-reaction, i.e. the size-dependent give-back and follow-through.
- Almgren & Chriss (2001): take vs rest, by comparing the short-horizon expected move with the half spread.

## Files

- `trader.py`: the submission (ENABLE = ("drift", "direction"); ChaserSeller and FlowLead are in the file and can be switched on by an orchestrator).
- `variants/`: every variant in the table; `variants/v2_components.py` holds CalmMaker.
- `tools/cache_days.py` (TELLURIUM-only day cache, written to `cache/`; deleted to save 62 MB, rerun it before `bt.py`), `tools/bt.py` (fast scorer), `tools/jump_study.py`, `tools/diag.py`, `tools/timing.py`.
- `results/dev.md`, `results/dev.json` (compare.py), `results/ablation*.txt`, `results/sweep*.txt`.
