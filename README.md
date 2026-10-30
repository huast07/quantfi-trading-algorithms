# QuantiFi 2026 trading algorithms

Trading algorithms for the UTEFA QuantiFi 2026 competition, plus the tournament harness used to build, compare and combine them.
Each submission is a single self-contained `trader.py` that runs on a Prosperity-compatible engine.

| File | Version | One line |
|---|---|---|
| `trader.py` | v3 | The submission: a fixed-routing orchestrator, one owner strategy per product; it won held-out judging on worst-case robustness |
| `trader_v3.py` | v3 | Byte-identical copy of `trader.py`, kept for side-by-side comparison |
| `trader_v4.py` | v4 (eligible pairs) | Live risk-gated orchestrator over the strategy/product pairs that are profitable on both synthetic and real days |
| `trader_v4_allpairs.py` | v4 (all pairs) | The same gate with every pair available, letting the gate alone choose |

## 1. The competition rules and what they imply

QuantiFi gives three training days of order-book and trade data (days -2, -1 and 0, each 10,000 ticks) and scores the algorithm on an unseen day 1.
The rules that shaped the design are:

- **Per-product position limits, no capital constraint.**
  There is no starting cash, so the only binding resource is each product's limit (20 to 200 lots), and an order that would breach it cancels all of that product's orders for the tick.
  Consequence: allocation is not a budget problem across products.
  Every product with a real edge should be traded at once, and the hard question is how to share one product's limit between strategies.
- **The fill model is replay, not a queue.**
  A resting order fills against any market trade printed at or through its price, at our price, ahead of the bots.
  Every noise-taker print sits at the same-tick touch.
  Consequence: a quote at the touch gets the same fills as a quote inside it at a better price, so the strategies quote at the touch and passive edge per lot is the half spread.
- **The book does not react to us.**
  The book is regenerated each tick around a hidden fair value.
  Consequence: no market-impact model is needed, and the edge is in estimating that fair value well.
- **Counterparty identities are blank and conversions are unused.**
  Consequence: no trader-identity signals and no conversion arbitrage; state between ticks lives only in the `traderData` string.
- **Judging weighs breadth, depth and out-of-sample PnL.**
  Consequence: trade as many products as can be traded profitably, model each one specifically, and select strategies on held-out data rather than the days they were tuned on.

## 2. What the EDA found

The EDA of the price and trade tapes points one way: the money is in microstructure and structure, not in predicting which product will go up.

- **No directional signal from the book.**
  Order-book imbalance has no predictive power (|corr| < 0.035 everywhere), and weighted or wall mids are worse fair values than the raw mid.
- **Uninformed flow.**
  On 15 of 16 delta-one products the only takers are uniform-size noise traders who pay the half spread, so adverse selection is about zero and passive market making is the base layer everywhere.
- **A few real, repeatable structural edges:**

| Signal | Product | Evidence |
|---|---|---|
| Fixed anchor at 10,000, ACF(1) -0.50 | AMETHYST | +1.3 per lot at the touch, about 110 fills a day |
| Mean reversion (OU) around 5,000, spread 14 | TOFFEE_CAKE | +3.5 to +10.6 per lot passive; the single largest delta-one edge |
| The five pearls sum to 50,000, PINK restores it | PINK_PEARLS | 20-tick move of +5 to +10 against the deviation when it exceeds 10 |
| Quote noise, ACF(1) -0.50 | PAPER_LANTERNS | +1.3 to +1.6 per lot at the touch with an EWMA fair value |
| 10-tick momentum, corr +0.23 | BLUE_PEARLS | the only consistent momentum signal |
| Downward steps of about 100 | GOLDEN_PEARLS | price keeps falling about 33 over 20 ticks after a step |
| Implied vol 20-30% above realised, an IV-rule taker | LYCHEE vouchers | the only informed flow in the market |
| Jump diffusion, 8-13 jumps a day of mean size 170, chasers | TELLURIUM | naive quoting lost 13,000-44,000 a day |
| FRUIT_BASKET = 2 DRAGONFRUIT + 3 GRANADILLA + 1 MANGOSTEEN plus a premium | FRUIT_BASKET | the premium is a non-stationary random walk, so the basket cannot be fully hedged |

These findings set the strategy families below, and they also ruled ideas out.
Rotating everything into the single "best" product each tick was rejected: limits cap how much a winner can carry, most moves are noise that reverses, and each switch pays a 3-14 tick spread against a 1-2 per lot edge.

## 3. Strategy families

Six strategy families were built in parallel, each as a standalone trader with notes and results under `strategies/`.

| Family | Products | Idea |
|---|---|---|
| S1 diversified market maker | 15 delta-one products | Inventory-aware quoting at the touch, OU taking on TOFFEE_CAKE |
| S2 structural alpha | 15 delta-one products | Touch quoter with an Avellaneda-Stoikov reservation price plus PINK sum reversion, GOLDEN step, BLUE momentum and TOFFEE OU components |
| S3 voucher volatility relative value | LYCHEE and 10 vouchers | Sells rich implied volatility strike by strike, delta-hedged with LYCHEE |
| S4 jump specialist | TELLURIUM | Detects jumps, rides the post-jump drift and tilts quotes away from chasers |
| S5 adaptive allocator | 15 delta-one products | Sizes each product by edge per unit of risk (mu / sigma^2), which beat equal sizing by +5,146 [3,466, 6,720] on dev |
| S6 untraded instruments | FRUIT_BASKET, DRAGONFRUIT, GRANADILLA, MANGOSTEEN, PEANUT_BUTTER | Hedged basket maker, thin-leg makers, a DRAGONFRUIT trend follower and a wide PEANUT_BUTTER maker |

## 4. How strategies were judged

`tournament/compare.py` scores every strategy on the same generated days from the backtester's 42 market cases.

- **Suites:** quick (8 cases, seed 1) and dev (42 cases, seeds 1-2) for tuning; heldout (42 cases, seeds 3-5) for judging only.
- **Score:** tier-weighted PnL (observed cases 60%, plausible 30%, stress 10%), worst case, worst seed, drawdown, limit breaches and crashes.
- **Uncertainty:** paired case-bootstrap 95% confidence intervals on every difference, because all strategies see identical days.
- **Real days:** every candidate is also replayed on the three real training days.

Held-out results for the single families: S4 49,170, S3 46,808, S1 39,956, S5 34,580, S2 19,867, and the reference trader -5,680.
No single family wins everywhere, which is why the submission combines them.

## 5. How each trader version works

All versions are generated by `tournament/build_orchestrator.py` from a routing file in `tournament/routes/`.
The builder embeds each strategy's unmodified source in its own module namespace, so names never collide, and adds the orchestrator runtime from `tournament/orchestrator_core.py`.
Every tick the orchestrator attributes the last tick's fills back to the strategies that could have made them, keeps each strategy's virtual position summing to the real one, collects each strategy's orders, nets crossing orders between strategies and clips everything to the real limit.
Do not edit the generated files by hand: change the routing file and rebuild.

### v3: fixed routing (`trader.py`, `trader_v3.py`)

v3 gives each product to one owner: the strategy that scored best on the dev seeds, subject to being positive on the real days with at least 500 of dev edge.

| Owner | Products |
|---|---|
| S1 | TOFFEE_CAKE, AMETHYST, PAPER_LANTERNS, WHITE_PEARLS |
| S2 | PINK_PEARLS, GOLDEN_PEARLS, BLACK_PEARLS, BLUE_PEARLS |
| S3 | LYCHEE and all 10 vouchers |
| S4 | TELLURIUM |
| S5 | JELLY |

The owner always trades at its full limit.
The five products with no qualifying strategy (FRUIT_BASKET, PEANUT_BUTTER and the three fruits) are not traded.

Results: dev 167,198 and held-out 147,033 (paired gap over the best single family +97,862 [93,462, 102,155]), worst held-out seed +83,670, real days 153,636 / 132,665 / 131,391, 0 breaches.

### v4: live risk gate (`trader_v4.py`, `trader_v4_allpairs.py`)

v4 runs several strategies on the same product at once and decides every tick, for each (strategy, product) pair, whether the trade is worth the risk.

- **Edge:** each pair's PnL per tick, measured from its own fills and virtual position.
- **Prior:** one day holds too little evidence to judge an edge (TOFFEE_CAKE's live t-statistic stays near 1.6 although it earns about 30,000 a day), so each pair starts from a prior measured offline by `tournament/estimate_priors.py` over 42 dev days and the 3 real days.
  The prior counts as 200,000 ticks of evidence, and live data updates it.
- **Decision:** a pair switches on when its posterior t-statistic reaches 2 and off below 1 (hysteresis).
  A switched-off pair keeps a 10% probe so it can earn its way back; a pair whose t-statistic is -2 or worse gets no new risk at all.
- **Sizing:** the runtime supports mean-variance sizing, mean / (2 lambda x risk), with risk the instrument's live volatility squared times the pair's typical position squared.
  The sweep found lambda barely mattered (under 1,000 between 3e-5 and 0), so the shipped builds use lambda = 0 and an on pair trades at its full limit share.
- **Crowding:** strategies on one product share its limit and often trade the same signal, so only the pair with the best posterior edge trades at full size.
- **Always allowed:** risk-reducing orders pass in full, and hedges (S3's LYCHEE delta hedge) bypass the gate.
- **Removed by evidence:** a jump guard that froze trading after 5-sigma moves cost about 16,000 on the real days, because PINK_PEARLS and the vouchers earn exactly on those jumps.

The two v4 files differ only in which pairs the gate may choose from:

- **`trader_v4.py` (eligible pairs):** a pair is offered to the gate only if it is profitable on both the dev days and the real days.
  This drops JELLY for every strategy except S5, VOUCHER_6800, and S6's FRUIT_BASKET, MANGOSTEEN and PEANUT_BUTTER.
- **`trader_v4_allpairs.py`:** every strategy on every product it supports, including S6 on all five new instruments; the gate alone decides.

| Build | Quick suite (tuning) | Held-out (judging) | Held-out vs v3 (95% CI) | Worst held-out seed | Real days | ms per tick |
|---|---:|---:|---|---:|---:|---:|
| v3 | 228,604 | 147,033 | - | **83,670** | 417,692 | 2.3 |
| v4, eligible pairs | 227,677 | 143,778 | -3,255 | 81,882 | **428,022** | 2.4 |
| v4, all pairs | **235,264** | **148,792** | **+1,760 [859, 2,570]** | 80,674 | 417,689 | 3.2 |

The v4 settings were chosen on the quick suite, so their quick-suite lead is optimistic; the held-out seeds were never used for any choice.
On them, the all-pairs gate beats v3 by a small but significant 1.2%, almost all of it from extra strategies on JELLY.
The eligible-pairs build loses about 3,300, mostly by dropping VOUCHER_6800, which pays on generated days and loses on all three real days.
Its real-day lead is partly in-sample, because its eligibility filter was chosen on those same real days.

Acceptance rule, fixed before tuning: replace v3 only if a v4 build matches its held-out PnL, its worst held-out seed (83,670), stays positive on every real day and has no breaches.
Neither v4 build passes the worst-seed test, so `trader.py` stays v3.
The gate's lasting result is negative but useful: with per-product limits and a market that rewards structure, one well-chosen owner per product already captures nearly all the available edge.

## 6. Repository layout

```text
trader*.py                     generated, self-contained submissions
strategies/S1..S6/             each family: trader.py, NOTES.md (design, evidence, results), results/
strategies/reference_trader.py the backtester's reference trader, used as a baseline
tournament/BRIEF.md            rules every strategy agent followed
tournament/compare.py          leaderboard with paired bootstrap confidence intervals
tournament/orchestrator_core.py the orchestrator and risk gate runtime
tournament/build_orchestrator.py builds a trader from a routing file
tournament/estimate_priors.py  measures each pair's prior edge on dev and real days
tournament/routes/             routing files for every build
tournament/priors/             measured priors
tournament/results/            every leaderboard run, as Markdown and JSON
tournament/test_orchestrator.py unit tests for the orchestrator and gate
```

## 7. Reproducing

The harness needs the QuantiFi backtester checked out next to this folder as `../backtester`.

```bash
# unit tests
uv run --project ../backtester pytest -p no:xdist -o addopts="" tournament/test_orchestrator.py

# build a trader from a routing file
uv run --project ../backtester python tournament/build_orchestrator.py tournament/routes/v4s.json --out trader_v4.py

# compare traders on the quick suite plus the real days
uv run --project ../backtester python tournament/compare.py trader_v3.py trader_v4.py --suite quick --workers 4 --tag mine
```

Tune only on the quick and dev suites; the heldout suite (seeds 3-5) is for judging.
