"""Unit tests for the orchestrator core.

Run: uv run --project ../backtester pytest -p no:xdist -o addopts="" tournament/test_orchestrator.py
"""

import sys
from pathlib import Path
from types import SimpleNamespace

from prosperity3bt import datamodel

sys.modules.setdefault("datamodel", datamodel)
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator_core import (  # noqa: E402
    GATE_DEFAULTS,
    InstrumentStats,
    Orchestrator,
    PairStats,
    allocate,
    attribute_fills,
    clip_orders,
    net_crossing,
    scale_orders,
)

Order = datamodel.Order
P = "PINK_PEARLS"


def trade(price, qty, buy, timestamp=0):
    side = {"buyer": "SUBMISSION", "seller": ""} if buy else {"buyer": "", "seller": "SUBMISSION"}
    return SimpleNamespace(price=price, quantity=qty, timestamp=timestamp, **side)


def pairs(orders):
    return [(o.price, o.quantity) for o in orders]


def test_clip_orders_never_lets_resting_buys_exceed_the_limit():
    kept = clip_orders([Order(P, 10, 8), Order(P, 9, 8), Order(P, 12, -30)], position=5, limit=10)
    assert pairs(kept) == [(10, 5), (12, -15)]


def test_clip_orders_drops_everything_when_already_at_the_limit_on_that_side():
    assert clip_orders([Order(P, 10, 3)], position=10, limit=10) == []


def test_net_crossing_cancels_overlap_between_two_strategies():
    netted = net_crossing({"A": [Order(P, 101, 5)], "B": [Order(P, 100, -3)]})
    assert pairs(netted["A"]) == [(101, 2)]
    assert netted["B"] == []


def test_net_crossing_leaves_non_crossing_quotes_alone():
    netted = net_crossing({"A": [Order(P, 99, 5)], "B": [Order(P, 100, -3)]})
    assert pairs(netted["A"]) == [(99, 5)]
    assert pairs(netted["B"]) == [(100, -3)]


def test_attribute_fills_splits_pro_rata_between_eligible_buyers():
    last = {"A": [Order(P, 100, 6)], "B": [Order(P, 100, 2)], "C": [Order(P, 98, 5)]}
    assert attribute_fills([trade(100, 4, buy=True)], last) == {"A": [(3, 100)], "B": [(1, 100)]}


def test_attribute_fills_gives_unclaimed_fills_to_none():
    assert attribute_fills([trade(100, 2, buy=False)], {"A": [Order(P, 100, 3)]}) == {None: [(-2, 100)]}


def test_scale_orders_passes_risk_reducing_volume_and_scales_the_rest():
    scaled = scale_orders([Order(P, 100, 10), Order(P, 104, -4)], position=-6, allocation=0.25)
    assert pairs(scaled) == [(100, 6 + 1), (104, -1)]


def test_scale_orders_with_zero_allocation_only_reduces_risk():
    assert pairs(scale_orders([Order(P, 100, 10), Order(P, 104, -4)], position=3, allocation=0.0)) == [(104, -3)]


def _stats_with(markouts, position=0.0):
    ps = PairStats.new(1.0)
    beta = 0.999
    for m in markouts:
        ps[4] = 0.0
        PairStats.update(ps, [(1, 100 - m)], 100.0, 0.0, position, beta, horizon=1)
    return ps


def test_allocate_stays_at_probe_without_evidence():
    gate = dict(GATE_DEFAULTS)
    assert allocate(PairStats.new(gate["probe"]), 1.0, gate["lam"], gate, cap=1.0) == gate["probe"]


def test_allocate_switches_on_for_a_confident_edge_and_sizes_by_mean_over_risk():
    gate = dict(GATE_DEFAULTS)
    ps = _stats_with([2.0, 1.0, 3.0] * 100, position=10.0)
    allocation = allocate(ps, sigma2=1.0, lam=gate["lam"], gate=gate, cap=1.0)
    assert ps[7] == 1.0
    mean, _ = PairStats.t_stat(ps)
    assert allocation == min(1.0, max(gate["probe"], mean / (2 * gate["lam"] * ps[5])))


def test_allocate_keeps_a_noisy_or_losing_pair_at_probe():
    gate = dict(GATE_DEFAULTS)
    ps = _stats_with([-1.0, 1.5, -2.0, 1.0] * 50)
    assert allocate(ps, 1.0, gate["lam"], gate, cap=1.0) == gate["probe"]
    assert ps[7] == 0.0


def test_allocate_hysteresis_keeps_an_on_pair_on_between_z_off_and_z_on():
    gate = {**GATE_DEFAULTS, "z_on": 10.0, "z_off": 0.5}
    ps = _stats_with([1.0, -0.5, 1.2, -0.4] * 50)
    _, t = PairStats.t_stat(ps)
    assert gate["z_off"] <= t < gate["z_on"]
    ps[7] = 1.0
    allocate(ps, 1.0, gate["lam"], gate, cap=1.0)
    assert ps[7] == 1.0
    ps[7] = 0.0
    assert allocate(ps, 1.0, gate["lam"], gate, cap=1.0) == gate["probe"]
    assert ps[7] == 0.0


def test_a_strong_prior_switches_a_pair_on_before_any_live_evidence():
    gate = {**GATE_DEFAULTS, "prior_n": 2000}
    allocation = allocate(PairStats.new(gate["probe"]), 1.0, gate["lam"], gate, cap=1.0, prior=[0.5, 25.0])
    assert allocation > gate["probe"]


def test_live_losses_override_a_prior_once_they_outweigh_it():
    gate = {**GATE_DEFAULTS, "prior_n": 200}
    ps = _stats_with([-2.0, -1.0, -3.0] * 300)
    assert allocate(ps, 1.0, gate["lam"], gate, cap=1.0, prior=[0.5, 25.0]) == gate["probe"]


def test_prior_has_no_effect_with_zero_weight():
    ps = _stats_with([1.0, -0.5, 1.2, -0.4] * 50)
    assert PairStats.t_stat(ps, [5.0, 1.0], 0) == PairStats.t_stat(ps)


def test_a_confidently_losing_pair_gets_no_new_risk_when_z_drop_is_set():
    gate = {**GATE_DEFAULTS, "prior_n": 2000, "z_drop": -2.0}
    assert allocate(PairStats.new(gate["probe"]), 1.0, gate["lam"], gate, cap=1.0, prior=[-0.5, 25.0]) == 0.0


def test_followers_are_scaled_and_the_best_prior_leads():
    gate = {"prior_n": 2000, "follower_share": 0.0, "lam": 0.0}
    priors = {f"A|{P}": [0.5, 1.0], f"B|{P}": [0.4, 1.0]}
    orch = _orchestrator([Order(P, 100, 10)], [Order(P, 99, 10)], gate=gate)
    orch.priors = priors
    result, _, _ = orch.run(_state(0, 0))
    assert pairs(result[P]) == [(100, 5)]  # A at its 0.5 cap; B, the follower, adds nothing


def test_instrument_jump_guard_starts_a_cooldown_after_a_large_move():
    gate = dict(GATE_DEFAULTS)
    st, _ = InstrumentStats.update(None, 100.0, 2.0, 0.1, gate)
    for mid in (101.0, 100.0, 101.0, 100.0):
        st, _ = InstrumentStats.update(st, mid, 2.0, 0.1, gate)
    assert st[3] == 0
    st, dmid = InstrumentStats.update(st, 160.0, 2.0, 0.1, gate)
    assert dmid == 60.0 and st[3] == gate["jump_cooldown"]


class _Fixed:
    def __init__(self, orders):
        self.orders = orders
        self.seen = None

    def run(self, state):
        self.seen = dict(state.position)
        return {P: list(self.orders), "AMETHYST": [Order("AMETHYST", 1, 1)]}, 0, "x"


def _orchestrator(a_orders, b_orders, gate=None):
    modules = {
        "A": SimpleNamespace(Trader=lambda: _Fixed(a_orders)),
        "B": SimpleNamespace(Trader=lambda: _Fixed(b_orders)),
    }
    return Orchestrator(modules, {P: [["A", 0.5], ["B", 0.5]]}, {P: 20}, gate)


def _state(position, timestamp, own_trades=(), data=""):
    depth = SimpleNamespace(buy_orders={99: 5}, sell_orders={101: -5})
    return SimpleNamespace(
        position={P: position},
        own_trades={P: list(own_trades)},
        traderData=data,
        timestamp=timestamp,
        order_depths={P: depth},
    )


def test_fixed_routing_drops_unrouted_products_and_respects_slices():
    orch = _orchestrator([Order(P, 100, 50)], [Order(P, 99, 3)])
    result, _, _ = orch.run(_state(0, 0))
    assert set(result) == {P}
    assert pairs(result[P]) == [(100, 10), (99, 3)]


def test_virtual_positions_sum_to_the_real_position_and_split_by_fill():
    orch = _orchestrator([Order(P, 100, 5)], [Order(P, 100, 5)])
    _, _, data = orch.run(_state(0, 0))
    orch.run(_state(4, 100, [trade(100, 4, buy=True, timestamp=0)], data))
    assert orch.traders["A"].seen[P] == 2
    assert orch.traders["A"].seen[P] + orch.traders["B"].seen[P] == 4


def test_stale_own_trades_from_earlier_ticks_are_not_counted_twice():
    orch = _orchestrator([Order(P, 100, 5)], [Order(P, 100, 5)])
    _, _, data = orch.run(_state(0, 0))
    fill = trade(100, 4, buy=True, timestamp=0)
    _, _, data = orch.run(_state(4, 100, [fill], data))
    orch.run(_state(4, 200, [fill], data))  # the engine repeats the old fill: it must not move positions
    assert orch.traders["A"].seen[P] == 2 and orch.traders["B"].seen[P] == 2


def test_gated_orchestrator_starts_every_pair_at_probe_size():
    orch = _orchestrator([Order(P, 100, 10)], [Order(P, 99, 10)], gate={})
    result, _, _ = orch.run(_state(0, 0))
    assert pairs(result[P]) == [(100, 1), (99, 1)]


def test_exempt_pairs_bypass_the_gate_and_trade_at_their_cap():
    modules = {"A": SimpleNamespace(Trader=lambda: _Fixed([Order(P, 100, 10)]))}
    orch = Orchestrator(modules, {P: [["A", 1.0]]}, {P: 20}, gate={}, options={"A": {"exempt": [P]}})
    result, _, _ = orch.run(_state(0, 0))
    assert pairs(result[P]) == [(100, 10)]
