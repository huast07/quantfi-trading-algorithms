"""Allocator and netting tests, including two sub-strategies sharing one product's limit.

Run from Trading_Algorithm/: uv run --project ../backtester python -m pytest strategies/S5/test_allocator.py -q
"""

import importlib.util
import sys
from pathlib import Path

import prosperity3bt.datamodel as datamodel

sys.modules.setdefault("datamodel", datamodel)
SPEC = importlib.util.spec_from_file_location("s5", Path(__file__).with_name("src_trader.py"))
s5 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s5)

ALL_PRODUCTS = [(p, s5.SIGMA_EDA[p] ** 2) for p in s5.PRODUCTS]


def _entries(pink_lean_edge, mm_edge=0.02):
    entries = [("mm", p, mm_edge, var) for p, var in ALL_PRODUCTS]
    entries.append(("pink", "PINK_PEARLS", pink_lean_edge, s5.SIGMA_EDA["PINK_PEARLS"] ** 2))
    return entries


def _allocate(rule, entries, budget=800.0):
    config = {"rule": rule, "budget": budget, "half_life": 1000.0, "share_step": 1.0}
    return s5.Allocator(config, {}).allocate(entries)


def test_two_subs_on_one_product_never_exceed_its_limit():
    for rule in ("EQ", "A1", "A2", "A3", "A1MR"):
        for budget in (50.0, 800.0, 1e6):
            slices = _allocate(rule, _entries(1.0), budget)
            pink = slices[("mm", "PINK_PEARLS")] + slices[("pink", "PINK_PEARLS")]
            assert pink <= s5.LIMITS["PINK_PEARLS"] + 1e-9
            assert all(v >= 0 for v in slices.values())


def test_kelly_moves_the_pink_limit_to_the_lean_when_its_edge_is_live():
    quiet = _allocate("A2", _entries(0.001), budget=100.0)
    live = _allocate("A2", _entries(1.0), budget=100.0)
    assert live[("pink", "PINK_PEARLS")] > quiet[("pink", "PINK_PEARLS")]
    assert live[("pink", "PINK_PEARLS")] > live[("mm", "PINK_PEARLS")]
    assert quiet[("pink", "PINK_PEARLS")] < quiet[("mm", "PINK_PEARLS")]


def test_budget_is_respected_when_it_binds():
    slices = _allocate("A3", _entries(0.5), budget=100.0)
    used = sum(lots * s5.SIGMA_EDA[p] for (_, p), lots in slices.items())
    assert used <= 100.0 + 1e-6


def test_equal_risk_gives_equal_risk_to_unclipped_entries():
    slices = _allocate("EQ", _entries(0.5), budget=100.0)
    risk = {k: v * s5.SIGMA_EDA[k[1]] for k, v in slices.items() if v < s5.LIMITS[k[1]] - 1e-9}
    values = list(risk.values())
    assert max(values) - min(values) < 1e-6


def test_share_step_limits_the_per_tick_change():
    config = {"rule": "A2", "budget": 100.0, "half_life": 1000.0, "share_step": 0.001}
    mem = {}
    first = s5.Allocator(config, mem).allocate(_entries(0.001))
    second = s5.Allocator(config, mem).allocate(_entries(1.0))
    sigma = s5.SIGMA_EDA["PINK_PEARLS"]
    change = abs(second[("pink", "PINK_PEARLS")] - first[("pink", "PINK_PEARLS")]) * sigma / 100.0
    assert change <= 0.001 + 1e-5  # shares are stored rounded to 6 dp


def test_netting_cancels_a_lean_buy_against_the_makers_ask():
    buys, sells = s5.net_orders([(100, 5), (100, -3), (99, 4), (101, -4)])
    assert dict(buys) == {100: 2, 99: 4}
    assert dict(sells) == {101: 4}


def test_clip_to_limit_never_breaches():
    orders = s5.clip_to_limit("PINK_PEARLS", 18, [(100, 5), (99, 5)], [(101, 50)])
    assert 18 + sum(o.quantity for o in orders if o.quantity > 0) <= 20
    assert 18 + sum(o.quantity for o in orders if o.quantity < 0) >= -20
