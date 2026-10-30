"""Event study of TELLURIUM jumps on cached days: post-jump signed drift vs jump size, spread, between-jump sigma.

    uv run --project ../backtester python strategies/S4/tools/jump_study.py real regular-day ...
"""

import pickle
import sys
from pathlib import Path

import numpy as np

CACHE = Path(__file__).resolve().parents[1] / "cache"
H = (10, 50, 100, 200, 300, 400, 600)
THRESH = 50.0


def book(day):
    rows = [line.split(";") for line in day.prices_csv.splitlines()[1:]]
    bid = np.array([float(r[3]) if r[3] else np.nan for r in rows])
    ask = np.array([float(r[9]) if r[9] else np.nan for r in rows])
    return bid, ask


def study(keys):
    sizes, fwd, spreads = [], [], []
    calm = []
    for key in keys:
        _, day = pickle.loads((CACHE / f"{key}.pkl").read_bytes())
        bid, ask = book(day)
        mid = (bid + ask) / 2
        d = np.diff(mid)
        jumps = np.where(np.abs(d) > THRESH)[0] + 1
        n = len(mid)
        near = np.zeros(n, bool)
        for j in jumps:
            near[max(0, j - 1) : j + 1] = True
            s = np.sign(d[j - 1])
            sizes.append(abs(d[j - 1]))
            fwd.append([s * (mid[min(j + h, n - 1)] - mid[j]) for h in H])
        calm.extend(d[~near[1:]][np.isfinite(d[~near[1:]])])
        spreads.append(np.nanmean(ask - bid))
        print(f"{key}: {len(jumps)} jumps, signs {''.join('+' if d[j-1] > 0 else '-' for j in jumps)}, "
              f"sizes {[round(abs(d[j-1])) for j in jumps]}")
    sizes, fwd = np.array(sizes), np.array(fwd)
    calm = np.array(calm)
    print(f"n={len(sizes)} mean size {sizes.mean():.1f}; calm sigma {calm.std():.2f}, MAD-sigma "
          f"{1.4826*np.median(np.abs(calm-np.median(calm))):.2f}, max calm |d| {np.abs(calm).max():.1f}; spread {np.mean(spreads):.2f}")
    x = sizes - 170.13
    for i, h in enumerate(H):
        y = fwd[:, i]
        A = np.column_stack([np.ones_like(x), x])
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        res = y - A @ coef
        print(f"h={h:4d}: mean {y.mean():7.1f}  fit drift {coef[0]:7.1f} slope {coef[1]:6.2f}  resid sd {res.std():6.1f}")


if __name__ == "__main__":
    keys = []
    for arg in sys.argv[1:]:
        keys += sorted(p.stem for p in CACHE.glob(f"{arg}__*.pkl"))
    study(keys)
