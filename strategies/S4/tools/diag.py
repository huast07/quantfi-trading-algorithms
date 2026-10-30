"""Attribute a variant's TELLURIUM PnL on one cached day to ticks-since-jump buckets and trade types.

    uv run --project ../backtester python strategies/S4/tools/diag.py variant.py regular-day__1
"""

import pickle
import sys
from pathlib import Path

import numpy as np
from quantgen.adapter.runner import MatchMode, backtest
from quantgen.adapter.strategy import Strategy

CACHE = Path(__file__).resolve().parents[1] / "cache"


def main():
    path, key = sys.argv[1], sys.argv[2]
    _, day = pickle.loads((CACHE / f"{key}.pkl").read_bytes())
    res = backtest(Strategy(Path(path).stem, Path(path).read_text()), day, MatchMode.ALL)
    rows = [line.split(";") for line in day.prices_csv.splitlines()[1:]]
    bid = np.array([float(r[3]) for r in rows])
    ask = np.array([float(r[9]) for r in rows])
    mid = (bid + ask) / 2
    n = len(mid)
    pos = np.zeros(n)
    cash_cost = 0.0  # spread paid vs mid
    take_cost = passive_gain = 0.0
    vol = 0
    for row in res.trades:
        tr = row.trade
        if "SUBMISSION" not in (tr.buyer, tr.seller):
            continue
        i = tr.timestamp // 100
        q = tr.quantity if tr.buyer == "SUBMISSION" else -tr.quantity
        pos[i:] += q
        edge = (mid[i] - tr.price) * q  # >0 means bought below / sold above mid
        vol += abs(q)
        if edge < 0:
            take_cost += edge
        else:
            passive_gain += edge
    d = np.diff(mid)
    jumps = np.where(np.abs(d) > 39)[0] + 1
    since = np.full(n, 10 ** 6)
    last = -10 ** 6
    j = set(jumps.tolist())
    for i in range(n):
        if i in j:
            last = i
        since[i] = i - last
    # MTM pnl from holding: pos[i-1] * d[i-1] earned at tick i
    hold = pos[:-1] * d
    jump_pnl = hold[jumps - 1].sum()
    buckets = [(1, 50), (50, 200), (200, 400), (400, 600), (600, 10 ** 7)]
    print(f"{key}: jumps {len(jumps)}  volume {vol}  take cost {take_cost:,.0f}  passive gain {passive_gain:,.0f}")
    print(f"  PnL from holding through jump ticks: {jump_pnl:,.0f}")
    for lo, hi in buckets:
        mask = (since[1:] >= lo) & (since[1:] < hi)
        print(f"  holding PnL ticks-since-jump [{lo},{hi}): {hold[mask].sum():,.0f}  mean|pos| {np.abs(pos[1:][mask]).mean():.1f}")
    print(f"  total approx {hold.sum() + take_cost + passive_gain:,.0f}")


if __name__ == "__main__":
    main()
