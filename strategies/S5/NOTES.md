# S5: adaptive, volatility-aware, diversified allocator

Status: `trader.py` is `variants/v1_A2.py` (the validated dev-suite winner).
`src_trader.py` is v2: the same engine refactored into the sub-strategy interface from BRIEF.md's update, plus one fix (see Variants).
A dev run of v1_A2 against the v2 variants (`results/dev_final.*`) was still running when I handed off.

## 1. Design

- Engine, per product (15 benign delta-one products): quote at the touch, because noise takers always hit the touch and "all"-mode matching fills every print at that price, so improving the price only gives away edge.
  Sizes are skewed toward a centre (AS-style inventory control through size), and the position stays inside [centre - Q, centre + Q].
- Fair values: AMETHYST 10,000 (a kill switch moves to a 100-tick EWMA if that drifts more than 3 away); PAPER_LANTERNS EWMA span 5; TOFFEE OU fair = anchor + dev x exp(-kappa x 100), with a slow anchor (span 3000); GOLDEN plateau EWMA, which pauses quoting for 85 ticks after a step of more than 5; PINK E[20-tick value] = mid - 1.105 x dev x P(jump in 20 ticks | dev); everything else uses raw mid.
- Structural leans: PINK takes toward the target -dev x P(jump); TOFFEE leans -dev/sd_OU of the cap and takes when the book is at least 1 through its fair value.
- Allocator: risk budget sum Q_e x sigma_e <= B (B = 800, so the 100-tick PnL sd is at most 8,000).
  Shares come from the rule, slices are Q = w x B / sigma, and slices are water-filled against each product's limit.
  Each share can change by at most 0.002 per tick.
  - sigma_i(t): the long-run variance of mid changes, gamma0 + 2 x gamma1, an MA(1) estimate that strips quote noise, using EWMAs with a 1000-tick half-life.
  - mu_i(t): a discounted Beta-Bernoulli print rate x lots per print x an EWMA of the 1-tick markout, plus the signal edge (TOFFEE kappa x |dev|; PINK hazard x 1.105 x |dev|).
- Rules: EQ uses equal risk with static sigmas; A1 uses a share proportional to sigma; A2 sizes positions by Kelly, q proportional to mu / sigma^2, which makes the risk share proportional to mu / sigma; A3 uses a share proportional to 1 / sigma.
- Shock guard: a 1-tick move larger than 8 x max(sigma, 1) pauses that product's passive quotes for 20 ticks.

### Sub-strategy interface (v2, `src_trader.py`)

- `MarketMaker`, `PinkLean` and `ToffeeLean` each expose `intent(ctx, product, mem, q, cap, center)`, which returns [(price, qty)], plus `edge()` and `variance()`.
- `Allocator.allocate([(sub, product, edge, variance)])` returns the lot slices.
- `net_orders` cancels crossing intents against each other, and `clip_to_limit` enforces the limit.
- `test_allocator.py` has 7 passing tests, including MM plus PinkLean sharing the PINK limit.
  Under A2 the PINK limit moves to the lean when its edge is live, the slices never exceed the limit, and the budget, share-step and netting all behave as specified.

## 3. Results (dev, seeds 1-2, v1 engine, same engine and same budget for every rule)

| Rule | Weighted PnL | Worst case (mean) | Worst seed | Weak | Real -2/-1/0 | Real total |
|---|---:|---|---:|---:|---|---:|
| A2 Kelly | 34,040 | black-swan-squeeze 19,272 | 1,410 | 1 | 27,956/21,950/32,298 | 82,205 |
| EQ | 28,894 | mean-reversion-decay 17,307 | 12,146 | 0 | 27,362/17,779/23,524 | 68,665 |
| A3 1/sigma | 28,323 | black-swan-squeeze -1,636 | -43,040 | 1 | | 83,473 |
| A1 sigma | 21,990 | busy-day 11,967 | -13,218 | 0 | | 53,696 |
| reference | -3,363 | busy-day -10,063 | -26,522 | 35 | | |

Paired bootstrap, A2 minus the other rule: EQ +5,146 [3,466, 6,720]; A3 +5,717 [3,246, 8,136]; A1 +12,050 [10,393, 13,810].
A2's gain comes from TOFFEE (+6.9k vs EQ) and from cutting PEANUT_BUTTER and LYCHEE losses.
The literal vol-seeking rule A1 is clearly worst.
There were 0 breaches and 0 crashes, and the run took 0.43-0.46 ms per tick in the harness.
A2's single Weak case is black-swan-squeeze, a relative verdict (it still made +19k).
The loss there came from PAPER_LANTERNS: its lagging EWMA fair moved outside the touch during the spike, so it quoted one side only.
v2 keeps smoothed fair values inside the touch to fix this.

## 4. Variants

- `variants/EQ`, `A1`, `A2` and `A3` are the v1 runs above.
- `v2_*` and `v2_A2_hl300` are the interface refactor, the touch-clip fix and a 300-tick half-life, for the anti-whipsaw sweep; their results are pending in `results/dev_final.md`.
- The budget sweep (`EQ_B200`-`B3200`) and `A1MR` were not run because the machine was overloaded (load average 66-190).

## 6. Proposals

- Kelly sizing works, and its gain is concentrated in TOFFEE.
  A richer OU engine (online kappa by RLS) should get more of the limit.
- Use the shared-limit allocator across sub-strategies: PINK's lean edge (about 1/lot-tick when |dev| > 10, against about 0.02 for the maker) argues for moving the limit dynamically.
- Market making on PEANUT_BUTTER and LYCHEE loses on the dev suite under every rule, so its slice should be smaller or zero.
