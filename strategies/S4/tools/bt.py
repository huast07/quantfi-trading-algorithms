"""Backtest S4 variants on the cached TELLURIUM-only days (see cache_days.py).

    uv run --project ../backtester python strategies/S4/tools/bt.py strategies/S4/variants/a.py [b.py ...] \
        [--cases id1,id2] [--workers 2]

Prints, per variant: tier-weighted mean over the dev cases (seeds 1-2), worst case mean, worst single day,
number of losing case means, real days -2/-1/0, and (with -v) the per-case table.
"""

import argparse
import pickle
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from quantgen.adapter.runner import MatchMode, run_day
from quantgen.adapter.strategy import Strategy

CACHE = Path(__file__).resolve().parents[1] / "cache"
TIER_WEIGHTS = {"observed": 0.6, "plausible": 0.3, "stress": 0.1}


def job(args):
    path, key = args
    tier, day = pickle.loads((CACHE / f"{key}.pkl").read_bytes())
    strategy = Strategy(name=Path(path).stem, source=Path(path).read_text())
    started = time.perf_counter()
    try:
        result = run_day(strategy, day, MatchMode.ALL, with_log=False)
        pnl, breaches = result.total_pnl, result.limit_breaches
    except Exception as error:  # report a crash as a huge loss so it is impossible to miss
        print("CRASH", key, error)
        pnl, breaches = -1e9, -1
    return path, key, tier, pnl, breaches, time.perf_counter() - started


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--cases", default=None)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("-v", action="store_true")
    args = ap.parse_args()
    keys = sorted(p.stem for p in CACHE.glob("*.pkl"))
    if args.cases:
        wanted = set(args.cases.split(","))
        keys = [k for k in keys if k.split("__")[0] in wanted or k.startswith("real")]
    jobs = [(f, k) for f in args.files for k in keys]
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(job, jobs))
    by_file = defaultdict(list)
    for r in results:
        by_file[r[0]].append(r)
    table = defaultdict(dict)
    for f, rows in by_file.items():
        cases = defaultdict(list)
        tiers = {}
        real = {}
        breaches = 0
        secs = 0.0
        for _, key, tier, pnl, br, sec in rows:
            breaches += abs(br)
            secs += sec
            case, seed = key.split("__")
            if tier == "real":
                real[seed] = pnl
                continue
            cases[case].append(pnl)
            tiers[case] = tier
        means = {c: sum(v) / len(v) for c, v in cases.items()}
        counts = defaultdict(int)
        for c in means:
            counts[tiers[c]] += 1
        weighted = sum(TIER_WEIGHTS[tiers[c]] / counts[tiers[c]] * m for c, m in means.items()) / sum(
            TIER_WEIGHTS[t] for t in counts
        )
        worst_case = min(means, key=means.get) if means else None
        worst_day = min(p for v in cases.values() for p in v) if means else 0
        losing = sum(1 for m in means.values() if m < 0)
        rtxt = " ".join(f"{k}:{v:,.0f}" for k, v in sorted(real.items(), key=lambda kv: int(kv[0])))
        print(
            f"{Path(f).stem:28s} W={weighted:9,.0f} worstcase={worst_case}:{means.get(worst_case, 0):,.0f} "
            f"worstday={worst_day:,.0f} losing={losing} real[{rtxt}] sum={sum(real.values()):,.0f} "
            f"breach={breaches} s/day={secs / len(rows):.1f}"
        )
        for c, m in means.items():
            table[c][Path(f).stem] = (m, min(cases[c]))
    if args.v:
        names = [Path(f).stem for f in args.files]
        print("case".ljust(28) + "".join(n[:16].rjust(18) for n in names))
        for c in sorted(table):
            print(c.ljust(28) + "".join(f"{table[c][n][0]:9,.0f}/{table[c][n][1]:8,.0f}" for n in names))


if __name__ == "__main__":
    main()
