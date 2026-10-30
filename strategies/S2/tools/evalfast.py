"""Fast S2 evaluation helper: caches generated days, runs strategy files, prints per-product PnL.

Run from Trading_Algorithm/:
    uv run --project ../backtester python strategies/S2/tools/evalfast.py a.py b.py --cases regular-day ... --seeds 1 2
Tuning data only (seeds 1-2 and the real days).
"""

import argparse
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from quantgen.adapter.runner import MatchMode, run_day
from quantgen.adapter.strategy import Strategy
from quantgen.cases.case import case_day, find_cases, load_catalog
from quantgen.generator.params import load_params
from quantgen.market_day import to_day_data
from quantgen.real_data import load_real_day

BACKTESTER = Path(__file__).resolve().parents[4] / "backtester"
CACHE = Path("/private/tmp/claude-503/-Users-sterling-Downloads-QuantFi-Trading-Algorithm/"
             "f7fcd4ef-c254-4bec-b1fc-b72d8816a6cb/scratchpad/daycache")
ALLOWED_SEEDS = {1, 2}
TIER_W = {"observed": 0.6, "plausible": 0.3, "stress": 0.1}


def day_for(case_id: str, seed: int):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{case_id}_{seed}.pkl"
    if path.exists():
        return pickle.loads(path.read_bytes())
    if case_id.startswith("real"):
        day = load_real_day(BACKTESTER, seed)
    else:
        if seed not in ALLOWED_SEEDS:
            raise SystemExit("held-out seed refused")
        case = find_cases(load_catalog(), [case_id])[0]
        day = to_day_data(case_day(load_params(BACKTESTER / "params" / "params.json"), case, seed))
    path.write_bytes(pickle.dumps(day))
    return day


def job(args):
    file, case_id, seed = args
    strat = Strategy(name=Path(file).stem, source=Path(file).read_text())
    t0 = time.perf_counter()
    res = run_day(strat, day_for(case_id, seed), MatchMode.ALL, with_log=False)
    return file, case_id, seed, dict(res.product_pnl), res.limit_breaches, time.perf_counter() - t0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--cases", nargs="+", default=["regular-day"])
    p.add_argument("--seeds", nargs="+", type=int, default=[1, 2])
    p.add_argument("--real", action="store_true")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--products", nargs="*", default=None)
    a = p.parse_args()
    cases = list(load_catalog()) if a.cases == ["all"] else find_cases(load_catalog(), a.cases)
    tiers = {c.id: c.tier for c in cases}
    jobs = [(f, c.id, s) for c in cases for s in a.seeds for f in a.files]
    if a.real:
        jobs += [(f, "real", d) for d in (-2, -1, 0) for f in a.files]
        tiers["real"] = "real"
    with ProcessPoolExecutor(a.workers) as pool:
        results = list(pool.map(job, jobs))
    by = {}
    for file, cid, seed, pnl, br, sec in results:
        by.setdefault(file, []).append((cid, seed, pnl, br, sec))
    for file, rows in by.items():
        print(f"\n### {file}")
        prods = sorted({k for r in rows for k in r[2]})
        if a.products:
            prods = [x for x in prods if x in a.products]
        per_case = {}
        for cid, seed, pnl, br, sec in rows:
            per_case.setdefault(cid, []).append((pnl, br, sec))
        tot_prod = {k: 0.0 for k in prods}
        wsum = {}
        for cid in per_case:
            t = tiers[cid]
            if t != "real":
                wsum[t] = wsum.get(t, 0) + 1
        for cid, lst in per_case.items():
            mean_tot = sum(sum(x[0].values()) for x in lst) / len(lst)
            breaches = sum(x[1] for x in lst)
            secs = sum(x[2] for x in lst) / len(lst)
            mine = {k: sum(x[0].get(k, 0) for x in lst) / len(lst) for k in prods}
            seeds = " ".join(f"{sum(x[0].values()):,.0f}" for x in lst)
            print(f"{cid:24s} {tiers[cid]:9s} mean {mean_tot:10,.0f}  seeds [{seeds}] br {breaches} {secs:.1f}s")
            if tiers[cid] != "real":
                tw = sum(TIER_W[t] for t in wsum)
                w = TIER_W[tiers[cid]] / tw / wsum[tiers[cid]]
                for k in prods:
                    tot_prod[k] += w * mine[k]
        print("weighted by product: " + ", ".join(f"{k[:6]} {v:,.0f}" for k, v in tot_prod.items() if abs(v) > 0.5))
        print(f"WEIGHTED TOTAL {sum(tot_prod.values()):,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
