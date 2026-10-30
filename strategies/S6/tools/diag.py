"""Diagnostics on the real days: per product fills, lots, mean fill edge vs mid, max |position|, final position."""
import sys
from collections import defaultdict
from pathlib import Path

from quantgen.adapter.runner import MatchMode, backtest
from quantgen.adapter.strategy import Strategy
from quantgen.real_data import load_real_day

BACKTESTER = Path(__file__).resolve().parents[4] / "backtester"
src = Path(sys.argv[1]).read_text()
days = [int(d) for d in sys.argv[2:]] or [-2, -1, 0]
for day in days:
    res = backtest(Strategy(name="x", source=src), load_real_day(BACKTESTER, day), MatchMode.ALL)
    mids = {(r.timestamp, r.columns[2]): r.columns[-2] for r in res.activity_logs}
    stats = defaultdict(lambda: [0, 0, 0.0, 0, 0])
    pos = defaultdict(int)
    for row in sorted(res.trades, key=lambda r: r.trade.timestamp):
        t = row.trade
        side = 1 if t.buyer == "SUBMISSION" else -1 if t.seller == "SUBMISSION" else 0
        if not side:
            continue
        s = stats[t.symbol]
        mid = mids.get((t.timestamp, t.symbol))
        s[0] += 1
        s[1] += t.quantity
        if mid:
            s[2] += side * (mid - t.price) * t.quantity
        pos[t.symbol] += side * t.quantity
        s[3] = max(s[3], abs(pos[t.symbol]))
    pnl = {r.columns[2]: r.columns[-1] for r in res.activity_logs if r.timestamp == res.activity_logs[-1].timestamp}
    print(f"day {day}")
    for p, s in sorted(stats.items()):
        print(f"  {p:15s} fills {s[0]:4d} lots {s[1]:5d} edge/lot {s[2]/max(s[1],1):6.2f} max|q| {s[3]:3d} final {pos[p]:4d} pnl {pnl.get(p,0):8.1f}")
