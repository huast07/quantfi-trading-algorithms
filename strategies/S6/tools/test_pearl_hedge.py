"""Tiny harness: PearlGroupHedge must cross-hedge book-wide pearl exposure, never unwind others, respect limits."""
import sys, json, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "backtester/.venv/lib/python3.12/site-packages/prosperity3bt"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datamodel import OrderDepth, TradingState
import trader as T

def depth(mid, half):
    d = OrderDepth(); d.buy_orders = {mid - half: 10}; d.sell_orders = {mid + half: -10}; return d

def state(mids, own, book, td):
    depths = {p: depth(m, int(T.HALF_SPREAD[p])) for p, m in mids.items()}
    s = TradingState(td, 0, {}, depths, {}, {}, dict(own), None)
    s.book_position = dict(book)
    return s

tr = T.Trader(); td = ""; random.seed(1)
mids = {"WHITE_PEARLS": 15000, "BLACK_PEARLS": 12000, "BLUE_PEARLS": 5000}
for _ in range(50):  # warm the covariance with anti-correlated moves
    mids = {k: v + random.choice([-2, 0, 2]) for k, v in mids.items()}
    _, _, td = tr.run(state(mids, {}, {}, td))
# Another strategy is long 20 WHITE: the hedge should BUY BLACK and/or BLUE (negative corr), never sell WHITE.
orders, _, td = tr.run(state(mids, {}, {"WHITE_PEARLS": 20}, td))
print("long 20 WHITE ->", {p: [(o.price, o.quantity) for o in v] for p, v in orders.items()})
assert "WHITE_PEARLS" not in orders and orders, orders
assert all(o.quantity > 0 for v in orders.values() for o in v)
# No exposure -> no trade. Own-only position (standalone): hedge reduces own risk.
orders, _, td = tr.run(state(mids, {}, {}, td)); assert not orders, orders
orders, _, td = tr.run(state(mids, {"BLACK_PEARLS": 15}, {"BLACK_PEARLS": 15}, td))
print("own long 15 BLACK ->", {p: [(o.price, o.quantity) for o in v] for p, v in orders.items()})
# Book at limit on BLACK: hedge must not push the book over.
orders, _, td = tr.run(state(mids, {}, {"WHITE_PEARLS": 20, "BLACK_PEARLS": 20, "BLUE_PEARLS": 20}, td))
print("all long 20 ->", {p: [(o.price, o.quantity) for o in v] for p, v in orders.items()})
assert all(o.quantity < 0 for v in orders.values() for o in v) or not orders
print("edge", tr.pearls.edge(json.loads(td)["H"]), "OK")
