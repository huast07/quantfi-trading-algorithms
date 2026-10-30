"""Minimal re-implementation of prosperity3bt's matching (mode "all") on the 15 delta-one products, for fast
iteration. Validated against the real engine (see NOTES.md). Tuning data only: seeds 1-2 and real days.

    uv run --project ../backtester python strategies/S2/tools/minisim.py a.py b.py --cases all --seeds 1 2
"""

import argparse
import importlib.util
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from prosperity3bt import datamodel
from prosperity3bt.datamodel import Listing, Observation, OrderDepth, Trade, TradingState

sys.modules.setdefault("datamodel", datamodel)

from quantgen.cases.case import case_day, find_cases, load_catalog  # noqa: E402
from quantgen.generator.params import load_params  # noqa: E402

BACKTESTER = Path(__file__).resolve().parents[4] / "backtester"
CACHE = Path("/private/tmp/claude-503/-Users-sterling-Downloads-QuantFi-Trading-Algorithm/"
             "f7fcd4ef-c254-4bec-b1fc-b72d8816a6cb/scratchpad/mdcache")
PRODUCTS = ["AMETHYST", "TOFFEE_CAKE", "PAPER_LANTERNS", "JELLY", "PEANUT_BUTTER", "DRAGONFRUIT", "GRANADILLA",
            "MANGOSTEEN", "FRUIT_BASKET", "LYCHEE", "WHITE_PEARLS", "BLACK_PEARLS", "GOLDEN_PEARLS", "PINK_PEARLS",
            "BLUE_PEARLS"]
LIMITS = {p: 50 for p in PRODUCTS}
LIMITS.update({p: 40 for p in ("DRAGONFRUIT", "GRANADILLA", "MANGOSTEEN", "FRUIT_BASKET")})
LIMITS.update({p: 20 for p in PRODUCTS if p.endswith("PEARLS")})
LIMITS["LYCHEE"] = 200
TIER_W = {"observed": 0.6, "plausible": 0.3, "stress": 0.1}


def real_day(day):
    """Parse the real CSVs into per-product arrays like ProductDay."""
    prices = (BACKTESTER / "QuantFi Price Data" / f"prices_day_{day}.csv").read_text().splitlines()[1:]
    trades = (BACKTESTER / "QuantFi Trades Data" / f"trades_day_{day}.csv").read_text().splitlines()[1:]
    out = {}
    for line in prices:
        c = line.split(";")
        p = c[2]
        if p not in PRODUCTS:
            continue
        t = int(c[1]) // 100
        d = out.setdefault(p, {"bp": np.full((10000, 3), np.nan), "bv": np.full((10000, 3), np.nan),
                               "ap": np.full((10000, 3), np.nan), "av": np.full((10000, 3), np.nan),
                               "tt": [], "tp": [], "tq": []})
        for k in range(3):
            if c[3 + 2 * k]:
                d["bp"][t, k], d["bv"][t, k] = float(c[3 + 2 * k]), float(c[4 + 2 * k])
            if c[9 + 2 * k]:
                d["ap"][t, k], d["av"][t, k] = float(c[9 + 2 * k]), abs(float(c[10 + 2 * k]))
    for line in trades:
        c = line.split(";")
        if c[3] in out:
            out[c[3]]["tt"].append(int(c[0]) // 100)
            out[c[3]]["tp"].append(float(c[5]))
            out[c[3]]["tq"].append(int(c[6]))
    return {p: (d["bp"], d["bv"], d["ap"], d["av"], np.array(d["tt"]), np.array(d["tp"]), np.array(d["tq"]))
            for p, d in out.items()}


def load_day(case_id, seed):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{case_id}_{seed}.pkl"
    if path.exists():
        return pickle.loads(path.read_bytes())
    if case_id == "real":
        arrays = real_day(seed)
    else:
        if seed not in (1, 2):
            raise SystemExit("held-out seed refused")
        md = case_day(load_params(BACKTESTER / "params" / "params.json"), find_cases(load_catalog(), [case_id])[0], seed)
        arrays = {p: (v.bid_prices, v.bid_volumes, v.ask_prices, v.ask_volumes, v.trade_ticks, v.trade_prices,
                      v.trade_quantities) for p, v in md.products.items() if p in PRODUCTS}
    path.write_bytes(pickle.dumps(arrays))
    return arrays


def load_trader(file):
    spec = importlib.util.spec_from_file_location(f"t_{abs(hash(file))}", file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Trader()


def simulate(file, case_id, seed):
    day = load_day(case_id, seed)
    trader = load_trader(file)
    ticks = next(iter(day.values()))[0].shape[0]
    trades_by_tick = {p: {} for p in day}
    for p, arr in day.items():
        for t, pr, q in zip(arr[4].tolist(), arr[5].tolist(), arr[6].tolist()):
            trades_by_tick[p].setdefault(t, []).append([pr, q, q])
    pos = {p: 0 for p in day}
    cash = {p: 0.0 for p in day}
    data = ""
    breaches = 0
    elapsed = 0.0
    listings = {p: Listing(p, p, "COINS") for p in day}
    pnl_path = np.zeros(ticks)
    for t in range(ticks):
        depths = {}
        for p, arr in day.items():
            od = OrderDepth()
            for k in range(3):
                if not np.isnan(arr[0][t, k]):
                    od.buy_orders[int(arr[0][t, k])] = int(arr[1][t, k])
                if not np.isnan(arr[2][t, k]):
                    od.sell_orders[int(arr[2][t, k])] = -int(arr[3][t, k])
            depths[p] = od
        state = TradingState(data, t * 100, listings, depths, {}, {}, dict(pos), Observation({}, {}))
        t0 = time.perf_counter()
        orders, _, data = trader.run(state)
        elapsed += time.perf_counter() - t0
        for p, olist in orders.items():
            if p not in day:
                continue
            longs = sum(o.quantity for o in olist if o.quantity > 0)
            shorts = sum(-o.quantity for o in olist if o.quantity < 0)
            if pos[p] + longs > LIMITS[p] or pos[p] - shorts < -LIMITS[p]:
                breaches += 1
                continue
            od = depths[p]
            mts = trades_by_tick[p].get(t, [])
            for o in olist:
                q = o.quantity
                if q > 0:
                    for price in sorted(x for x in od.sell_orders if x <= o.price):
                        v = min(q, -od.sell_orders[price])
                        pos[p] += v; cash[p] -= price * v; od.sell_orders[price] += v; q -= v
                        if od.sell_orders[price] == 0:
                            del od.sell_orders[price]
                        if q == 0:
                            break
                    for mt in mts:
                        if q == 0:
                            break
                        if mt[2] == 0 or mt[0] > o.price:
                            continue
                        v = min(q, mt[2]); pos[p] += v; cash[p] -= o.price * v; mt[2] -= v; q -= v
                elif q < 0:
                    q = -q
                    for price in sorted((x for x in od.buy_orders if x >= o.price), reverse=True):
                        v = min(q, od.buy_orders[price])
                        pos[p] -= v; cash[p] += price * v; od.buy_orders[price] -= v; q -= v
                        if od.buy_orders[price] == 0:
                            del od.buy_orders[price]
                        if q == 0:
                            break
                    for mt in mts:
                        if q == 0:
                            break
                        if mt[1] == 0 or mt[0] < o.price:
                            continue
                        v = min(q, mt[1]); pos[p] -= v; cash[p] += o.price * v; mt[1] -= v; q -= v
        if t % 100 == 99 or t == ticks - 1:
            pnl_path[t] = sum(cash[p] + pos[p] * (day[p][0][t, 0] + day[p][2][t, 0]) / 2 for p in day)
    mid_last = {p: (day[p][0][-1, 0] + day[p][2][-1, 0]) / 2 for p in day}
    pnl = {p: cash[p] + pos[p] * mid_last[p] for p in day}
    path = pnl_path[99::100]
    dd = float(np.max(np.maximum.accumulate(path) - path)) if len(path) else 0.0
    return file, case_id, seed, pnl, breaches, 1000 * elapsed / ticks, dd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--cases", nargs="+", default=["regular-day"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2])
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--detail", action="store_true")
    a = ap.parse_args()
    catalog = load_catalog()
    cases = list(catalog) if a.cases == ["all"] else find_cases(catalog, a.cases)
    tiers = {c.id: c.tier for c in cases}
    jobs = [(f, c.id, s) for c in cases for s in a.seeds for f in a.files]
    if a.real:
        jobs += [(f, "real", d) for d in (-2, -1, 0) for f in a.files]
    with ProcessPoolExecutor(a.workers) as pool:
        res = list(pool.starmap(simulate, jobs)) if False else list(pool.map(simulate, *zip(*jobs)))
    counts = {}
    for c in cases:
        counts[c.tier] = counts.get(c.tier, 0) + 1
    tw = sum(TIER_W[t] for t in counts)
    summary = {}
    for f in a.files:
        rows = [r for r in res if r[0] == f]
        prod = {p: 0.0 for p in PRODUCTS}
        cm = {}
        for _, cid, seed, pnl, br, ms, dd in rows:
            cm.setdefault(cid, []).append((pnl, br, ms, dd))
        total = 0.0
        lines = []
        for cid, lst in cm.items():
            m = np.mean([sum(x[0].values()) for x in lst])
            if cid != "real":
                w = TIER_W[tiers[cid]] / tw / counts[tiers[cid]]
                total += w * m
                for p in PRODUCTS:
                    prod[p] += w * np.mean([x[0].get(p, 0.0) for x in lst])
            seeds = " ".join(f"{sum(x[0].values()):,.0f}" for x in lst)
            worst = {p: min(x[0].get(p, 0) for x in lst) for p in PRODUCTS}
            bad = ", ".join(f"{p[:6]} {v:,.0f}" for p, v in sorted(worst.items(), key=lambda kv: kv[1])[:3])
            lines.append(f"  {cid:24s} {m:9,.0f} [{seeds}] br {sum(x[1] for x in lst)} "
                         f"ms {np.mean([x[2] for x in lst]):.3f}  worst: {bad}")
        summary[f] = total
        print(f"\n### {f}  WEIGHTED {total:,.0f}")
        if a.detail or len(cm) <= 6:
            print("\n".join(lines))
        print("  by product: " + ", ".join(f"{p[:6]} {v:,.0f}" for p, v in prod.items()))
    print("\nSUMMARY " + " | ".join(f"{Path(f).stem} {v:,.0f}" for f, v in summary.items()))


if __name__ == "__main__":
    main()
