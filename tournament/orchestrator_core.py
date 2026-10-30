"""Orchestrator runtime, embedded verbatim into the generated trader.py by build_orchestrator.py.

Each sub-strategy is an unmodified trader.py loaded into its own module namespace, so names never collide.
Several sub-strategies can run on the same instrument at once. Every tick the orchestrator:

1. attributes the previous tick's fills back to the sub-strategies whose orders could have produced them, and
   keeps their *virtual* positions summing to the real position;
2. updates, for every (sub-strategy, instrument) pair, a live estimate of its edge and its risk (the risk gate);
3. gives each sub-strategy a view of the state holding only its own virtual positions, and collects its orders;
4. scales each pair's risk-increasing orders by the gate's allocation, lets risk-reducing orders through, then
   nets crossing orders between sub-strategies and clips everything to the real position limit.

The risk gate (mean-variance, per pair). Marking a whole position to market every tick is far too noisy to show
an edge within a day, so edge and risk are measured separately:

- edge: the *markout* PnL of the pair's fills. A pseudo-position y gets each fill and decays with the pair's
  holding horizon h; per tick m = y_prev * dmid + sum((mid - fill price) * signed qty). Its decayed mean and
  variance give a t-statistic for "edge > 0";
- risk: inventory variance per tick, sigma_instrument^2 * E[q^2], with sigma from an EWMA of squared mid changes;
- prior: a pair may carry an offline prior [mean, var] of its per-tick markout (measured on the dev seeds by
  tournament/estimate_priors.py). It enters the statistics as prior_n pseudo-ticks that never decay, so a pair
  with a strong offline record starts switched on, and live evidence has to contradict it to switch it off. A
  single day holds too little evidence for a pure live test: TOFFEE_CAKE's live t-statistic stays near 1.6;
- allocation a in [probe, cap]: if the edge is confidently positive (hysteresis between z_on and z_off),
  a = mean / (2 * lam * risk), the maximiser of a*mean - lam*a^2*risk; otherwise a = probe, so a switched-off
  pair keeps producing evidence at a small, bounded cost. Measurements are divided by the allocation in force,
  so they describe the pair at full size;
- crowding: strategies on one product share its limit and often trade the same signal, so only the pair with
  the highest posterior mean edge keeps its full allocation; the others are scaled by follower_share;
- an instrument-level jump guard: after a move above jump_k sigma, guarded pairs may only reduce risk for
  jump_cooldown ticks; a spread wider than usual scales lam up.

Everything is O(pairs) per tick with O(1) state per pair. With "gate": null in the routing, allocations are
fixed at each route's share of the limit, which reproduces fixed routing exactly.
"""

import copy
import json
import math
import types

from datamodel import Order

SUBMISSION = "SUBMISSION"
GATE_DEFAULTS = {
    "half_life": 2000,  # ticks of evidence the edge estimate remembers
    "vol_half_life": 500,  # ticks for the instrument's volatility and spread estimates
    "lam": 3e-5,  # risk aversion, 1 / PnL units
    "z_on": 2.0,  # t-statistic to switch a pair on
    "z_off": 1.0,  # ...and to switch it back off (hysteresis)
    "probe": 0.1,  # allocation of a switched-off pair
    "horizon": 100,  # default markout holding horizon, ticks
    "jump_k": 5.0,  # jump guard threshold, in instrument sigmas
    "jump_cooldown": 100,  # ticks during which guarded pairs may only reduce risk
    "jump_guard": True,  # per-strategy option: False for strategies built to trade jumps
    "prior_n": 0,  # weight of a pair's offline prior, in ticks of live evidence
    "follower_share": 1.0,  # allocation multiplier for every gated pair on a product except its best one
    "z_drop": None,  # a pair whose t-statistic is at or below this gets no new risk at all, not even the probe
}


def load_module(name, source):
    module = types.ModuleType(name)
    exec(compile(source, name, "exec"), module.__dict__)
    return module


def mid_price(depth):
    if not depth.buy_orders or not depth.sell_orders:
        return None, None
    bid, ask = max(depth.buy_orders), min(depth.sell_orders)
    return (bid + ask) / 2, ask - bid


def clip_orders(orders, position, limit):
    """Keep orders in sequence while position plus all resting buys (or sells) stays within +/- limit."""
    kept, buys, sells = [], 0, 0
    for order in orders:
        if order.quantity > 0:
            qty = max(min(order.quantity, limit - position - buys), 0)
            buys += qty
        else:
            qty = -max(min(-order.quantity, limit + position - sells), 0)
            sells -= qty
        if qty != 0:
            kept.append(Order(order.symbol, order.price, qty))
    return kept


def scale_orders(orders, position, allocation):
    """Risk-reducing volume passes in full; risk-increasing volume is scaled by `allocation` (at least one lot
    when allocation > 0). Orders are taken in sequence, so the first ones use up the reducing capacity."""
    reduce_buy, reduce_sell = max(-position, 0), max(position, 0)
    out = []
    for order in orders:
        side = 1 if order.quantity > 0 else -1
        qty = abs(order.quantity)
        capacity = reduce_buy if side > 0 else reduce_sell
        reducing = min(qty, capacity)
        extra = qty - reducing
        scaled = 0 if extra == 0 or allocation <= 0 else max(1, int(extra * allocation + 0.5))
        if side > 0:
            reduce_buy -= reducing
        else:
            reduce_sell -= reducing
        if reducing + scaled:
            out.append(Order(order.symbol, order.price, side * (reducing + scaled)))
    return out


def _sides(orders_by_strategy):
    buys, sells = [], []
    for name, orders in orders_by_strategy.items():
        for index, order in enumerate(orders):
            (buys if order.quantity > 0 else sells).append((order.price, name, index))
    return sorted(buys, reverse=True), sorted(sells)


def net_crossing(orders_by_strategy):
    """Cancel overlapping volume where one sub-strategy's buy price is at or above another's sell price."""
    buys, sells = _sides(orders_by_strategy)
    qty = {(name, i): o.quantity for name, orders in orders_by_strategy.items() for i, o in enumerate(orders)}
    bi = si = 0
    while bi < len(buys) and si < len(sells) and buys[bi][0] >= sells[si][0]:
        buy_key, sell_key = buys[bi][1:], sells[si][1:]
        if buy_key[0] == sell_key[0]:  # a sub-strategy's own crossing orders are left as it sent them
            si += 1
            continue
        overlap = min(qty[buy_key], -qty[sell_key])
        qty[buy_key] -= overlap
        qty[sell_key] += overlap
        bi += qty[buy_key] == 0
        si += qty[sell_key] == 0
    return {
        name: [Order(o.symbol, o.price, qty[(name, i)]) for i, o in enumerate(orders) if qty[(name, i)] != 0]
        for name, orders in orders_by_strategy.items()
    }


def attribute_fills(trades, last_orders):
    """Split our fills on one product between the sub-strategies whose last orders could have filled at that price,
    pro rata by order size. Returns {strategy: [(signed qty, price), ...]}; fills nobody can claim go under None."""
    out = {}
    for trade in trades:
        side = 1 if trade.buyer == SUBMISSION else -1 if trade.seller == SUBMISSION else 0
        if side == 0:
            continue
        eligible = [
            (name, side * o.quantity)
            for name, orders in last_orders.items()
            for o in orders
            if side * o.quantity > 0 and side * (o.price - trade.price) >= 0
        ]
        total = sum(q for _, q in eligible)
        remaining = trade.quantity
        for name, q in eligible:
            share = min(remaining, trade.quantity * q // total)
            if share:
                out.setdefault(name, []).append((side * share, trade.price))
            remaining -= share
        if remaining:
            owner = eligible[0][0] if eligible else None
            out.setdefault(owner, []).append((side * remaining, trade.price))
    return out


def decay(half_life):
    return 0.5 ** (1.0 / half_life)


class PairStats:
    """Decayed markout statistics and inventory risk for one (sub-strategy, instrument) pair. State is a list of
    floats: [S0, S1, S2, W2, y, q2, allocation, on]."""

    @staticmethod
    def new(allocation):
        return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, allocation, 0.0]

    @staticmethod
    def update(ps, fills, mid, dmid, position, beta, horizon):
        scale = max(ps[6], 1e-9)
        markout = ps[4] * dmid + sum((mid - price) * qty for qty, price in fills)
        m = markout / scale
        ps[0] = beta * ps[0] + 1.0
        ps[1] = beta * ps[1] + m
        ps[2] = beta * ps[2] + m * m
        ps[3] = beta * beta * ps[3] + 1.0
        ps[4] = ps[4] * (1.0 - 1.0 / horizon) + sum(qty for qty, _ in fills)
        q_full = position / scale
        ps[5] = beta * ps[5] + (1.0 - beta) * q_full * q_full

    @staticmethod
    def t_stat(ps, prior=None, prior_n=0):
        """Mean per-tick markout and its t-statistic, with an optional prior [mean, var] worth prior_n ticks."""
        s0, s1, s2, w2 = ps[0], ps[1], ps[2], ps[3]
        if prior is not None and prior_n > 0:
            mu, var = prior
            s0, s1, s2, w2 = s0 + prior_n, s1 + prior_n * mu, s2 + prior_n * (var + mu * mu), w2 + prior_n
        if s0 < 2:
            return 0.0, 0.0
        mean = s1 / s0
        var = max(s2 / s0 - mean * mean, 1e-12)
        n_eff = s0 * s0 / w2
        return mean, mean / math.sqrt(var / n_eff)


def allocate(ps, sigma2, lam, gate, cap, prior=None):
    """The gate's decision for one pair: returns the new allocation and stores it with the on/off state."""
    mean, t = PairStats.t_stat(ps, prior, gate["prior_n"])
    on = t >= gate["z_on"] or (ps[7] and t >= gate["z_off"])
    if gate["z_drop"] is not None and t <= gate["z_drop"]:
        allocation = 0.0
    elif not on:
        allocation = min(gate["probe"], cap)
    else:
        risk = sigma2 * ps[5]
        allocation = cap if lam * risk <= 0 else min(cap, max(gate["probe"], mean / (2.0 * lam * risk)))
    ps[6], ps[7] = allocation, 1.0 if on else 0.0
    return allocation


class InstrumentStats:
    """Live characteristics of one instrument: [mid_prev, var, spread_avg, cooldown]."""

    @staticmethod
    def update(st, mid, spread, alpha, gate):
        if st is None:
            return [mid, 0.0, spread, 0], 0.0
        dmid = mid - st[0]
        jumped = st[1] > 0 and dmid * dmid > gate["jump_k"] ** 2 * st[1]
        st[1] = (1 - alpha) * st[1] + alpha * dmid * dmid
        st[2] = (1 - alpha) * st[2] + alpha * spread
        st[3] = gate["jump_cooldown"] if jumped else max(st[3] - 1, 0)
        st[0] = mid
        return st, dmid


class Orchestrator:
    def __init__(self, modules, routes, limits, gate=None, options=None, priors=None):
        self.traders = {name: module.Trader() for name, module in modules.items()}
        self.routes = routes
        self.limits = limits
        self.gate = None if gate is None else {**GATE_DEFAULTS, **gate}
        self.options = options or {}
        self.priors = priors or {}
        self.caps = {(name, p): share for p, slots in routes.items() for name, share in slots}
        self.owned = {}
        for product, slots in routes.items():
            for name, _ in slots:
                self.owned.setdefault(name, []).append(product)

    @staticmethod
    def _load(raw):
        try:
            data = json.loads(raw) if raw else {}
        except (TypeError, ValueError):
            data = {}
        mem = {k: data.get(k, {}) for k in ("sub", "vpos", "last", "pair", "inst")}
        mem["ts"] = data.get("ts", -1)
        return mem

    def _option(self, name, key):
        defaults = self.gate if self.gate is not None else GATE_DEFAULTS
        return self.options.get(name, {}).get(key, defaults[key])

    def _exempt(self, name, product):
        """Pairs listed under a strategy's "exempt" option (hedges) bypass the gate and the jump guard."""
        return product in self.options.get(name, {}).get("exempt", ())

    def _reconcile(self, state, mem):
        """Attribute last tick's fills and force each product's virtual positions to sum to the real position.
        The engine leaves a product's old own_trades in place on ticks without new fills, so only fills stamped
        at the previous tick count. Returns {(strategy, product): [(signed qty, price), ...]}."""
        vpos, fills = mem["vpos"], {}
        for product, slots in self.routes.items():
            names = [name for name, _ in slots]
            trades = [t for t in state.own_trades.get(product, []) if getattr(t, "timestamp", mem["ts"]) == mem["ts"]]
            last = {n: [Order(product, p, q) for p, q in mem["last"].get(n, {}).get(product, [])] for n in names}
            for name, got in attribute_fills(trades, last).items():
                owner = name if name in names else names[0]
                fills.setdefault((owner, product), []).extend(got)
                vpos.setdefault(owner, {})[product] = vpos.get(owner, {}).get(product, 0) + sum(q for q, _ in got)
            gap = state.position.get(product, 0) - sum(vpos.get(n, {}).get(product, 0) for n in names)
            if gap:
                vpos.setdefault(names[0], {})[product] = vpos.get(names[0], {}).get(product, 0) + gap
        return fills

    def _allocations(self, state, mem, fills):
        """{(strategy, product): allocation} and the set of products under a jump cooldown."""
        if self.gate is None:
            return dict(self.caps), set()
        gate, alpha = self.gate, 1 - decay(self.gate["vol_half_life"])
        beta = decay(gate["half_life"])
        allocations, cooling = {}, set()
        for product, slots in self.routes.items():
            depth = state.order_depths.get(product)
            mid, spread = mid_price(depth) if depth else (None, None)
            if mid is None:
                allocations.update({(n, product): 0.0 for n, _ in slots})
                continue
            inst, dmid = InstrumentStats.update(mem["inst"].get(product), mid, spread, alpha, gate)
            mem["inst"][product] = inst
            if inst[3] > 0:
                cooling.add(product)
            lam = gate["lam"] * max(1.0, spread / inst[2]) if inst[2] > 0 else gate["lam"]
            means = {}
            for name, cap in slots:
                key = f"{name}|{product}"
                ps = mem["pair"].get(key) or PairStats.new(min(gate["probe"], cap))
                position = mem["vpos"].get(name, {}).get(product, 0)
                horizon = self._option(name, "horizon")
                PairStats.update(ps, fills.get((name, product), []), mid, dmid, position, beta, horizon)
                if self._exempt(name, product):  # hedges must never be throttled by their own (negative) markout
                    ps[6], allocations[(name, product)] = cap, cap
                else:
                    allocations[(name, product)] = allocate(ps, inst[1], lam, gate, cap, self.priors.get(key))
                    means[name] = PairStats.t_stat(ps, self.priors.get(key), gate["prior_n"])[0]
                mem["pair"][key] = ps
            if len(means) > 1 and gate["follower_share"] != 1.0:
                leader = max(means, key=means.get)
                for name in means:
                    if name != leader:
                        allocations[(name, product)] *= gate["follower_share"]
        return allocations, cooling

    def _view(self, state, name, mem):
        view = copy.copy(state)
        vpos = mem["vpos"].get(name, {})
        view.position = {p: vpos.get(p, 0) for p in self.owned[name]}
        view.book_position = dict(state.position)
        view.traderData = mem["sub"].get(name, "")
        return view

    def _pair_orders(self, name, product, orders, mem, allocations, cooling):
        position = mem["vpos"].get(name, {}).get(product, 0)
        allocation = allocations[(name, product)]
        if self.gate is None:
            return clip_orders(orders, position, int(self.limits[product] * allocation))
        guarded = self._option(name, "jump_guard") is not False and not self._exempt(name, product)
        if product in cooling and guarded:
            allocation = 0.0
        return scale_orders(clip_orders(orders, position, self.limits[product]), position, allocation)

    def _collect(self, state, mem, allocations, cooling):
        per_product, new_sub = {}, {}
        for name, trader in self.traders.items():
            try:
                orders, _, data = trader.run(self._view(state, name, mem))
            except Exception:  # one broken sub-strategy must never take the whole book down
                orders, data = {}, mem["sub"].get(name, "")
            new_sub[name] = data
            for product in self.owned[name]:
                mine = self._pair_orders(name, product, orders.get(product, []), mem, allocations, cooling)
                per_product.setdefault(product, {})[name] = mine
        return per_product, new_sub

    def _priority(self, product, names, mem):
        """Order sub-strategies on one product by their current edge t-statistic, best first."""
        if self.gate is None:
            return names

        def rank(name):
            key = f"{name}|{product}"
            t = PairStats.t_stat(mem["pair"].get(key, [0] * 8), self.priors.get(key), self.gate["prior_n"])[1]
            return (not self._exempt(name, product), -t)

        return sorted(names, key=rank)

    def run(self, state):
        mem = self._load(state.traderData)
        fills = self._reconcile(state, mem)
        allocations, cooling = self._allocations(state, mem, fills)
        per_product, mem["sub"] = self._collect(state, mem, allocations, cooling)
        result, new_last = {}, {}
        for product, by_strategy in per_product.items():
            netted = net_crossing(by_strategy) if len(by_strategy) > 1 else by_strategy
            ordered = self._priority(product, list(netted), mem)
            combined = [o for name in ordered for o in netted[name]]
            result[product] = clip_orders(combined, state.position.get(product, 0), self.limits[product])
            for name, orders in netted.items():
                new_last.setdefault(name, {})[product] = [[o.price, o.quantity] for o in orders]
        mem["last"] = new_last
        mem["ts"] = state.timestamp
        return result, 0, json.dumps(mem, separators=(",", ":"))
