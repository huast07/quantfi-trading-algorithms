# Strategy agent brief (shared by S1-S5)

You are one of five agents building competing QuantiFi 2026 strategies in parallel.
The approved plan is `Trading_Algorithm/.claude/plans/strategy-tournament.plan.md`; read sections 1-6 before starting.

## Read first

- `QuantFi/backtester/README.md`: the synthetic generator, the 42 cases and how scoring works.
- `QuantFi/backtester/quantgen/cases/catalog/*.yaml`: what each case changes.
- EDA text, already extracted: `/private/tmp/claude-503/-Users-sterling-Downloads-QuantFi-Trading-Algorithm/f7fcd4ef-c254-4bec-b1fc-b72d8816a6cb/scratchpad/reports.txt` (Prices report lines 1-2032, Trades report after).
  Read the pages for your products in full.
- `QuantFi/backtester/quantgen/scoring/reference_trader.py`: the baseline you must beat on your products.
- `QuantFi/backtester/params/params.json`: the calibrated generator parameters (true spreads, volumes, processes).

## Your workspace

- Write only inside `Trading_Algorithm/strategies/<your id>/`. Never edit the backtester, the harness, or another agent's folder.
- Deliver `trader.py` (your best version) and `NOTES.md`.
- Put variants you test in `variants/<name>.py` in your folder, so the results stay reproducible.

## The trader.py contract

- One self-contained file defining `class Trader` with `run(self, state) -> (orders_by_product, 0, trader_data_str)`.
- Import only `from datamodel import Order, OrderDepth, TradingState` (plus others from `datamodel` if needed), the standard library, and numpy.
- `state.order_depths[p].sell_orders` has **negative** volumes in this engine; use `abs()`.
- `state.position.get(p, 0)`; `state.market_trades` / `state.own_trades` are the trades since the last call.
- Persist state in the returned `traderData` string as compact JSON, and read it back from `state.traderData` (empty string on the first call). Keep it small, O(1) per product.
- Day 1 opens where day 0 closed; never assume a reset or a known starting price beyond what the EDA documents.
- Position limits (from `backtester/quantgen/products.py`): AMETHYST, TOFFEE_CAKE, PAPER_LANTERNS, JELLY, PEANUT_BUTTER 50; TELLURIUM, DRAGONFRUIT, GRANADILLA, MANGOSTEEN, FRUIT_BASKET 40; LYCHEE 200; each pearl 20; each VOUCHER_<strike> 50 (strikes 6800, 7000, 7200, 7300, 7400, 7500, 7600, 7750, 7900, 8100).
  If position plus the sum of your buy orders (or minus your sell orders) could exceed a limit, the engine cancels **all** your orders for that product that tick. Clip every order so this can never happen.
- Must never raise: guard empty books, missing history and missing products.

## Method requirements (from the user)

- **Statistics and probability first.** Express each signal as an online estimate of a conditional expectation or probability (EWMA mean/variance, recursive least squares, Kalman or OU filter, conjugate Bayesian updates such as Beta-Bernoulli fill rates), and size by expected edge relative to risk. Avoid unexplained magic thresholds; tie any constant you keep to an EDA statistic and name it.
- **Low computational complexity.** O(1) work and state per product per tick (the voucher smile fit over 10 strikes counts as O(1)). No refitting over long histories, no optimisers inside `run()`, no lists that grow with time. Target < 1 ms per tick for `run()`.
- Literature-grounded: cite the papers your design follows in `NOTES.md`.

## How to evaluate (tuning data only)

Run from `Trading_Algorithm/`:

```bash
uv run --project ../backtester python tournament/compare.py strategies/<id> --suite quick --workers 2 --out strategies/<id>/results --tag quick
uv run --project ../backtester python tournament/compare.py strategies/<id> strategies/<id>/variants/x.py --suite dev --workers 2 --out strategies/<id>/results --tag dev
```

- Use `--workers 2`: four other agents share the same 8 cores.
- A run also scores the built-in reference and the real days -2, -1, 0, and reports a paired bootstrap CI against the leader.
- Use `--cases <ids>` to iterate quickly on the cases that matter for your products.
- You may tune only on `quick`, `dev` (seeds 1-2) and the real days. **Never run the `heldout` or `full` suites**: seeds 3-5 are reserved for judging.
- Prefer parameters that sit in a flat region of a small sweep, and strategies that are rarely Weak over ones that win big on a few cases.

## Gates your final trader.py must pass

- Zero limit breaches and zero crashes on the dev suite and the real days.
- Positive total PnL on the real days (if that's impossible for your family, say why in NOTES.md).
- Beats the reference on your products' tier-weighted PnL on dev.

## NOTES.md must contain

1. Design: per product, the model, its estimators, the sizing rule and the risk controls (inventory skew, kill switches, jump/gap protection).
2. Statistics: the evidence (EDA numbers and your own measurements) behind each component.
3. Results: final dev-suite and real-day tables (paste from compare.py), per-product PnL, Weak cases and why.
4. Variants tried and how each did (a short table), so the judge can see what you rejected.
5. Measured ms/tick.
6. **Proposals:** new strategy ideas your results suggest, each with the statistic that motivates it.

## Final message

When done, reply with: dev weighted PnL, worst case, Weak count, real-day totals, ms/tick, and your top proposals.
Keep it under 300 words; the details go in NOTES.md.

## Update: sub-strategy interface for the Phase 3 orchestrator

The final trader.py will be an orchestrator that runs every profitable sub-strategy on each instrument at once, nets their orders, shares each position limit between them by edge per risk, and hedges net exposure (plan, Phase 3).
So that your work can plug in, structure each of your per-instrument components as a self-contained sub-strategy class with:

- `intent(state, product, mem) -> list[(price, signed_qty)]` (or a target position), computed **as if it had the whole position limit to itself, given position `q`**;
- `edge()`: its live expected edge per lot (an online estimate), and `variance()`: its risk per lot;
- its own small state in `mem` (a dict that gets serialised into traderData).

Your own trader.py still runs standalone. Keep a thin `Trader.run` that calls the sub-strategies and clips to the limits.
List your sub-strategies and their edge/variance estimators in NOTES.md.
Don't restructure work that's finished just for this: do it as you go, or as a final refactor if it's cheap.
