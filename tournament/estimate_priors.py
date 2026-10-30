"""Estimate the risk gate's prior edge for every (sub-strategy, instrument) pair in a routing file.

    uv run --project ../backtester python tournament/estimate_priors.py tournament/routes/v4_pre.json \
        --out tournament/priors/v4_pre.json --workers 4

Each sub-strategy runs alone on all of its routed products at full size, with the gate in measuring mode (always
on, no risk penalty, no jump guard, no decay). Its per-tick markout statistics, the same quantity the live gate
uses, are pooled over the dev cases (seeds 1-2 only: seeds 3-5 are for judging) and the real days. The output maps
"strategy|product" to the mean and variance of the per-tick markout at full size, plus diagnostics.
"""

import argparse
import json
import sys
import types
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from quantgen.adapter.runner import MatchMode, run_day
from quantgen.adapter.strategy import Strategy
from quantgen.cases.case import case_day, load_catalog
from quantgen.generator.params import load_params
from quantgen.market_day import to_day_data
from quantgen.real_data import REAL_DAYS, load_real_day

sys.path.insert(0, str(Path(__file__).parent))
from build_orchestrator import render, validate

BACKTESTER = Path(__file__).resolve().parents[2] / "backtester"
DEV_SEEDS = (1, 2)
SINK = "_prior_sink"
MEASURE_GATE = {"half_life": 1e12, "lam": 0.0, "z_on": -1e18, "z_off": -1e18, "jump_guard": False}
SINK_HOOK = f'''
import sys as _sys
_Measured = Trader


class Trader(_Measured):
    def run(self, state):
        result, conversions, data = _Measured.run(self, state)
        _sys.modules["{SINK}"].last = data
        return result, conversions, data
'''


def measure_sources(config):
    """One measuring trader per sub-strategy: that strategy alone, at full size, on every product routed to it."""
    out = {}
    for name in sorted({n for slots in config["routes"].values() for n, _ in slots}):
        routes = {p: [[name, 1.0]] for p, slots in config["routes"].items() if any(n == name for n, _ in slots)}
        options = {name: {k: v for k, v in config.get("options", {}).get(name, {}).items() if k != "exempt"}}
        gate = {**(config.get("gate") or {}), **MEASURE_GATE}  # keeps the config's markout horizon
        measure = {"subs": config["subs"], "routes": routes, "gate": gate, "options": options}
        validate(measure)
        out[name] = render(measure, Path(f"measure_{name}.json")) + SINK_HOOK
    return out


def pair_sums(sources, day):
    """{strategy|product: [ticks, sum m, sum m^2]} for one day, each strategy run alone."""
    sink = types.ModuleType(SINK)
    sys.modules[SINK] = sink
    out = {}
    for name, source in sources.items():
        sink.last = None
        run_day(Strategy(name=f"measure_{name}", source=source), day, MatchMode.ALL, with_log=False)
        for key, ps in json.loads(sink.last)["pair"].items():
            out[key] = [ps[0], ps[1], ps[2]]
    return out


def job(args):
    sources, kind, case_id, seed = args
    if kind == "real":
        day = load_real_day(BACKTESTER, seed)
    else:
        params = load_params(BACKTESTER / "params" / "params.json")
        case = next(c for c in load_catalog() if c.id == case_id)
        day = to_day_data(case_day(params, case, seed))
    return f"{kind}:{case_id}:{seed}", pair_sums(sources, day)


def combine(per_day, real_weight=1.0):
    """Pool per-tick sums over days, each real day counting real_weight times; also report each pair's share of
    days with a positive mean markout."""
    totals, positive, days = {}, {}, {}
    for label, sums in per_day.items():
        w = real_weight if label.startswith("real:") else 1.0
        for key, (n, s1, s2) in sums.items():
            t = totals.get(key, [0.0, 0.0, 0.0])
            totals[key] = [t[0] + w * n, t[1] + w * s1, t[2] + w * s2]
            positive[key] = positive.get(key, 0) + (s1 > 0)
            days[key] = days.get(key, 0) + 1
    priors = {}
    for key, (n, s1, s2) in sorted(totals.items()):
        mean = s1 / n
        priors[key] = {
            "mean": mean,
            "var": max(s2 / n - mean * mean, 1e-12),
            "ticks": n,
            "days_positive": positive[key] / days[key],
        }
    return priors


def measure(config, args):
    sources = measure_sources(config)
    jobs = [(sources, "case", case.id, seed) for case in load_catalog() for seed in args.seeds]
    if not args.no_real:
        jobs += [(sources, "real", None, day) for day in REAL_DAYS]
    per_day = {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for done, (label, sums) in enumerate(pool.map(job, jobs), start=1):
            per_day[label] = sums
            print(f"{done}/{len(jobs)} {label}", flush=True)
    return per_day


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("routes", type=Path, help="routing JSON, or with --recombine an earlier priors file")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--recombine", action="store_true", help="re-pool an earlier output's per-day sums")
    parser.add_argument("--real-weight", type=float, default=1.0, help="how many dev days each real day counts as")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEV_SEEDS), choices=DEV_SEEDS)
    parser.add_argument("--no-real", action="store_true", help="skip the three real days")
    args = parser.parse_args()
    data = json.loads(args.routes.read_text(encoding="utf-8"))
    if args.recombine:
        routes_name, per_day = data["routes"], data["days"]
    else:
        routes_name, per_day = args.routes.name, measure(data, args)
    priors = combine(per_day, args.real_weight)
    out = {"routes": routes_name, "real_weight": args.real_weight, "priors": priors, "days": per_day}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1), encoding="utf-8")
    for key, p in priors.items():
        t = p["mean"] / (p["var"] / p["ticks"]) ** 0.5
        print(f"{key:28s} mean {p['mean']:9.4f} sd {p['var'] ** 0.5:8.3f} t {t:7.1f} days+ {p['days_positive']:.2f}")


if __name__ == "__main__":
    main()
