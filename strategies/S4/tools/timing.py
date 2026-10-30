"""Measure Trader.run() time per tick on one cached day (full-product real day when given 'full').

    uv run --project ../backtester python strategies/S4/tools/timing.py strategies/S4/trader.py [key]
"""

import pickle
import sys
import tempfile
import time
from pathlib import Path

from prosperity3bt.file_reader import FileSystemReader
from prosperity3bt.runner import run_backtest
from quantgen.adapter.dataset import ROUND, stage_day
from quantgen.adapter.limits import quantifi_limits
from quantgen.adapter.runner import MatchMode
from quantgen.adapter.strategy import Strategy, load_trader
from quantgen.real_data import load_real_day

CACHE = Path(__file__).resolve().parents[1] / "cache"
BACKTESTER = Path(__file__).resolve().parents[4] / "backtester"


def main():
    path = sys.argv[1]
    key = sys.argv[2] if len(sys.argv) > 2 else "real__0"
    day = load_real_day(BACKTESTER, 0) if key == "full" else pickle.loads((CACHE / f"{key}.pkl").read_bytes())[1]
    trader = load_trader(Strategy(Path(path).stem, Path(path).read_text()))
    inner = trader.run
    times = []

    def timed(state):
        t0 = time.perf_counter()
        out = inner(state)
        times.append(time.perf_counter() - t0)
        return out

    trader.run = timed
    with tempfile.TemporaryDirectory() as tmp, quantifi_limits():
        stage_day(day, Path(tmp))
        run_backtest(trader, FileSystemReader(Path(tmp)), ROUND, day.day, False, MatchMode.ALL, True, False)
    times.sort()
    n = len(times)
    print(f"{key}: ticks {n}, mean {1000 * sum(times) / n:.3f} ms, p50 {1000 * times[n // 2]:.3f} ms, "
          f"p99 {1000 * times[int(n * 0.99)]:.3f} ms, max {1000 * times[-1]:.3f} ms")


if __name__ == "__main__":
    main()
