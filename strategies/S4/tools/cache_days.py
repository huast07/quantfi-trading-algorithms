"""Cache TELLURIUM-only DayData for every case x seed (1, 2) plus the real days.

The S4 trader only trades TELLURIUM, so its PnL depends only on TELLURIUM's book and tape; filtering the CSVs makes
each backtest ~25x faster. Run from Trading_Algorithm/:

    uv run --project ../backtester python strategies/S4/tools/cache_days.py
"""

import pickle
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from quantgen.adapter.dataset import DayData
from quantgen.cases.case import case_day, load_catalog
from quantgen.generator.params import load_params
from quantgen.market_day import to_day_data
from quantgen.real_data import REAL_DAYS, load_real_day

BACKTESTER = Path(__file__).resolve().parents[4] / "backtester"
OUT = Path(__file__).resolve().parents[1] / "cache"
PRODUCT = "TELLURIUM"
SEEDS = (1, 2)


def only(day: DayData) -> DayData:
    p = day.prices_csv.splitlines()
    t = day.trades_csv.splitlines()
    prices = [p[0]] + [line for line in p[1:] if line.split(";")[2] == PRODUCT]
    trades = [t[0]] + [line for line in t[1:] if line.split(";")[3] == PRODUCT]
    return DayData(day.day, "\n".join(prices) + "\n", "\n".join(trades) + "\n")


def job(args):
    case_id, seed = args
    params = load_params(BACKTESTER / "params" / "params.json")
    case = next(c for c in load_catalog() if c.id == case_id)
    day = only(to_day_data(case_day(params, case, seed)))
    (OUT / f"{case_id}__{seed}.pkl").write_bytes(pickle.dumps((case.tier, day)))
    return case_id, seed


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for d in REAL_DAYS:
        (OUT / f"real__{d}.pkl").write_bytes(pickle.dumps(("real", only(load_real_day(BACKTESTER, d)))))
    jobs = [(c.id, s) for c in load_catalog() for s in SEEDS if not (OUT / f"{c.id}__{s}.pkl").exists()]
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    with ProcessPoolExecutor(workers) as pool:
        for case_id, seed in pool.map(job, jobs):
            print(case_id, seed, flush=True)


if __name__ == "__main__":
    main()
