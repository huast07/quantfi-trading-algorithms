"""S6: hedged fruit basket, thin-leg makers, a DRAGONFRUIT trend lean, a wide PEANUT_BUTTER maker and a pearl
group hedge. Each component is a sub-strategy class with intent / edge / variance (BRIEF, Phase 3 interface);
Trader.run combines them standalone and clips every product to its limit.

One risk-aversion constant (RISK_GT) ties the components together: it is set so that an Avellaneda-Stoikov
reservation skew at the basket's position cap equals the basket half spread, and every no-trade hedging band is the
Davis-Norman / Whalley-Wilmott cube-root band for that same risk aversion. All estimators are O(1) EWMAs or scalar
Kalman / conjugate-normal updates; state is a few floats per product.
"""

import json
import math

from datamodel import Order

LIMITS = {
    "FRUIT_BASKET": 40, "DRAGONFRUIT": 40, "GRANADILLA": 40, "MANGOSTEEN": 40, "PEANUT_BUTTER": 50,
    "WHITE_PEARLS": 20, "BLACK_PEARLS": 20, "BLUE_PEARLS": 20,
}
BASKET = "FRUIT_BASKET"
LEG_WEIGHTS = {"DRAGONFRUIT": 2, "GRANADILLA": 3, "MANGOSTEEN": 1}  # EDA regression betas 1.9 / 3.0 / 0.9
LEGS = tuple(LEG_WEIGHTS)
PEANUT = "PEANUT_BUTTER"
PEARLS = ("WHITE_PEARLS", "BLACK_PEARLS", "BLUE_PEARLS")
TICKS_PER_DAY = 10000  # params.json "ticks"

# Tick sigma priors (EDA / params.json process sigma) and L1 half spreads (EDA mean spread / 2).
SIGMA0 = {
    "FRUIT_BASKET": 8.0, "DRAGONFRUIT": 2.05, "GRANADILLA": 1.63, "MANGOSTEEN": 2.34, "PEANUT_BUTTER": 4.82,
    "WHITE_PEARLS": 2.27, "BLACK_PEARLS": 2.23, "BLUE_PEARLS": 1.42,
}
HALF_SPREAD = {
    "FRUIT_BASKET": 3.0, "DRAGONFRUIT": 2.0, "GRANADILLA": 2.0, "MANGOSTEEN": 2.0, "PEANUT_BUTTER": 3.0,
    "WHITE_PEARLS": 2.0, "BLACK_PEARLS": 4.0, "BLUE_PEARLS": 3.0,
}
# Passive per-lot edge prior = minus the EDA aggressor 5-tick markout (mean over the three real days).
MARKOUT0 = {"FRUIT_BASKET": 4.6, "DRAGONFRUIT": 2.4, "GRANADILLA": 2.2, "MANGOSTEEN": 2.7, "PEANUT_BUTTER": 2.7}
# Noise-taker prints per tick x mean lots per print (params.json flow): the passive turnover rate in lots/tick.
TURNOVER = {"FRUIT_BASKET": 0.0016 * 2.2, "DRAGONFRUIT": 0.0019 * 2.2, "GRANADILLA": 0.0025 * 2.2,
            "MANGOSTEEN": 0.0019 * 2.2, "PEANUT_BUTTER": 0.0065 * 2.5}

VOL_HL = 500.0  # ticks; EDA tick sigma is stable within and across days, so a medium memory suffices
JUMP_K = 5.0  # a move above 5 sigma is a gap/jump (EDA: zero such moves on legs/PB on real days)
EDGE_ALPHA = 1.0 / 30  # per-fill EWMA weight; legs fill only 12-33 times a day
EDGE_PRIOR_N = 10.0  # pseudo-fills behind the markout prior

# Risk aversion: AS skew per lot = RISK_GT * sigma^2. Calibrated so the skew at the basket cap equals its half spread.
BASKET_CAP = 6  # VARIANT  # 12: the GRANADILLA hedge (3/lot) must fit
RISK_GT = HALF_SPREAD[BASKET] / (12 * SIGMA0[BASKET] ** 2)
BASKET_SKEW_GT = HALF_SPREAD[BASKET] / (BASKET_CAP * SIGMA0[BASKET] ** 2)

# Basket premium Kalman filter (random walk state, params.json premium_sigma 4.15; quote noise 1.14 basket, 0.40 M).
PREMIUM_Q = 4.149 ** 2
PREMIUM_R = 1.145 ** 2 + 0.403 ** 2
BASKET_IMPROVE = 1  # EDA replay: improving the 6-wide basket touch beat quoting behind on 2 of 3 days
BASKET_MIN_EDGE = 1.5  # half of the basket half spread: never quote closer than this to the reservation price
BASKET_SIZE = 3  # largest noise-taker print on the basket (params.json sizes 1-3)
BASKET_RESID_R2 = 0.70  # legs explain 64-78% of basket return variance (EDA); hedged residual is the rest

LEG_SIZE = 2  # thin flow (mean print 2.2 lots): two lots per side
LEG_MIN_EDGE = 1.0  # at a 4-wide touch this quotes at the touch (EDA: at-touch replay positive on GRANADILLA)

# DRAGONFRUIT drift: conjugate normal posterior with exponential forgetting.
TREND_MU0 = (216.5 + 144.5 + 237.5) / 3 / TICKS_PER_DAY  # EDA mean real-day drift, ~0.02 per tick
TREND_TAU = TREND_MU0  # prior sd = the effect itself: one sd from "no drift"
TREND_FORGET_HL = float(TICKS_PER_DAY)  # evidence half-life: one day
TREND_MAX = 10  # lots at full conviction; a quarter of the limit, leaving room for the basket hedge (<= 24)
FLIP_HL = 1000.0  # fast drift estimate for the regime-flip guard (regime-flip case reverses within a day)
FLIP_Z = 2.0  # fast-drift t-statistic against the lean that forces the lean to zero

# PEANUT_BUTTER Avellaneda-Stoikov: skew at PB_CAP equals the half spread at the EDA sigma.
PB_CAP = 10  # a fifth of the limit: tick sigma 4.8 vs spread 6, every strategy lost on PB inventory
PB_RISK_GT = HALF_SPREAD[PEANUT] / (PB_CAP * SIGMA0[PEANUT] ** 2)
PB_SIZE = 2  # mean noise print 2.5 lots

# Pearl group hedge: EWMA covariance of tick returns, prior from params.json correlation matrix.
PEARL_COV_HL = 2000.0
PEARL_CORR0 = {(0, 1): -0.580, (0, 2): -0.449, (1, 2): -0.455}


# ---------------------------------------------------------------- helpers


def top_of_book(depth):
    if depth is None or not depth.buy_orders or not depth.sell_orders:
        return None
    bid, ask = max(depth.buy_orders), min(depth.sell_orders)
    if bid >= ask:
        return None
    return bid, abs(depth.buy_orders[bid]), ask, abs(depth.sell_orders[ask])


def ewma_beta(half_life):
    return 0.5 ** (1.0 / half_life)


def update_vol(mem, mid, sigma0):
    """EWMA of squared mid changes, winsorised at JUMP_K sigma. Returns (sigma^2, dmid, jumped)."""
    var = mem.get("v", sigma0 * sigma0)
    last = mem.get("m")
    mem["m"] = mid
    if last is None:
        mem["v"] = var
        return var, 0.0, False
    dmid = mid - last
    jumped = dmid * dmid > JUMP_K * JUMP_K * var
    beta = ewma_beta(VOL_HL)
    mem["v"] = beta * var + (1.0 - beta) * min(dmid * dmid, JUMP_K * JUMP_K * var)
    return mem["v"], dmid, jumped


def update_markout(mem, state, product, mid, passive_only):
    """Per-lot markout of last tick's own fills against the current mid, folded into an EWMA (edge estimate).
    With passive_only, only fills on the favourable side of the previous mid (resting quotes) count."""
    prev = mem.get("pm", mid)
    for trade in state.own_trades.get(product, []) or []:
        side = 1 if trade.buyer == "SUBMISSION" else -1 if trade.seller == "SUBMISSION" else 0
        if side == 0 or trade.quantity <= 0:
            continue
        if passive_only and side * (prev - trade.price) <= 0:
            continue
        markout = side * (mid - trade.price)
        for _ in range(min(int(trade.quantity), 5)):
            mem["e"] = mem.get("e", MARKOUT0.get(product, 0.0)) * (1 - EDGE_ALPHA) + EDGE_ALPHA * markout
        mem["n"] = mem.get("n", 0) + int(trade.quantity)
    mem["pm"] = mid


def no_trade_band(half_spread, sigma2):
    """Davis-Norman / Whalley-Wilmott band for linear exposure under proportional cost c: (3c / (2 gamma s^2))^1/3."""
    return max(1.0, (1.5 * half_spread / (RISK_GT * max(sigma2, 1e-6))) ** (1.0 / 3.0))


def cross(book, qty):
    """Aggressive order for signed qty at the touch, capped by visible size."""
    bid, bid_vol, ask, ask_vol = book
    if qty > 0:
        return [(ask, min(qty, ask_vol))]
    if qty < 0:
        return [(bid, -min(-qty, bid_vol))]
    return []


def clip_orders(orders, position, limit):
    """Keep orders in sequence while position plus all buys (or minus all sells) stays within +/- limit."""
    kept, buys, sells = [], 0, 0
    for price, qty in orders:
        if qty > 0:
            qty = max(min(qty, limit - position - buys), 0)
            buys += qty
        else:
            qty = -max(min(-qty, limit + position - sells), 0)
            sells -= qty
        if qty:
            kept.append((int(price), int(qty)))
    return kept


# ---------------------------------------------------------------- sub-strategies


class HedgedBasketMaker:
    """Quote FRUIT_BASKET around 2D + 3G + 1M + premium, the premium a random-walk Kalman state. Inventory is
    hedged through the legs (hedge_targets), so the maker carries only the premium's residual risk."""

    def fair(self, state, mem):
        synth = 0.0
        for leg, weight in LEG_WEIGHTS.items():
            book = top_of_book(state.order_depths.get(leg))
            if book is None:
                return None, None
            synth += weight * (book[0] + book[2]) / 2.0
        book = top_of_book(state.order_depths.get(BASKET))
        if book is None:
            return None, book
        z = (book[0] + book[2]) / 2.0 - synth
        p, var = mem.get("p"), mem.get("P", PREMIUM_Q)
        if p is None or (z - p) ** 2 > JUMP_K * JUMP_K * (var + PREMIUM_Q + PREMIUM_R):
            mem["p"], mem["P"], mem["gap"] = z, PREMIUM_R, 1  # first tick or premium jump: reset, sit out
            return synth + z, book
        var += PREMIUM_Q
        gain = var / (var + PREMIUM_R)
        mem["p"], mem["P"], mem["gap"] = p + gain * (z - p), (1.0 - gain) * var, 0
        return synth + mem["p"], book

    def intent(self, state, product, mem):
        fair, book = self.fair(state, mem)
        if fair is None or book is None:
            return []
        bid, _, ask, _ = book
        sigma2, _, jumped = update_vol(mem, (bid + ask) / 2.0, SIGMA0[BASKET])
        update_markout(mem, state, BASKET, (bid + ask) / 2.0, passive_only=True)
        if jumped or mem.get("gap"):
            return []
        q = state.position.get(BASKET, 0)
        r = fair - q * BASKET_SKEW_GT * sigma2  # skew = half spread at the cap at the EDA sigma
        out = []
        if q < BASKET_CAP:
            out.append((min(bid + BASKET_IMPROVE, math.floor(r - BASKET_MIN_EDGE)), min(BASKET_SIZE, BASKET_CAP - q)))
        if q > -BASKET_CAP:
            out.append((max(ask - BASKET_IMPROVE, math.ceil(r + BASKET_MIN_EDGE)), -min(BASKET_SIZE, BASKET_CAP + q)))
        return out

    @staticmethod
    def hedge_targets(q_basket):
        return {leg: -weight * q_basket for leg, weight in LEG_WEIGHTS.items()}

    def edge(self, mem):
        return mem.get("e", MARKOUT0[BASKET])

    def variance(self, mem):
        """Hedged residual variance per lot over one passive turnover of the position."""
        return (1.0 - BASKET_RESID_R2) * mem.get("v", SIGMA0[BASKET] ** 2) / TURNOVER[BASKET]


class LegMaker:
    """Passive quotes on a thin basket leg with a reservation-price skew around an anchor position (the basket
    hedge plus any trend lean). Beyond the Davis-Norman band it crosses back to the band edge."""

    def intent(self, state, product, mem, anchor=0):
        book = top_of_book(state.order_depths.get(product))
        if book is None:
            return []
        bid, _, ask, _ = book
        mid = (bid + ask) / 2.0
        sigma2, _, jumped = update_vol(mem, mid, SIGMA0[product])
        update_markout(mem, state, product, mid, passive_only=True)
        q = state.position.get(product, 0)
        dev = q - anchor
        c = HALF_SPREAD[product]
        band = no_trade_band(c, sigma2)
        out = []
        if abs(dev) > band:
            out += cross(book, -int(math.copysign(math.ceil(abs(dev) - band), dev)))
        if jumped:
            return out
        r = mid - dev * c / band  # indifferent between resting and crossing at the band edge
        if dev < band:
            out.append((min(bid, math.floor(r - LEG_MIN_EDGE)), LEG_SIZE))
        if dev > -band:
            out.append((max(ask, math.ceil(r + LEG_MIN_EDGE)), -LEG_SIZE))
        return out

    def edge(self, mem, product):
        return mem.get("e", MARKOUT0[product])

    def variance(self, mem, product):
        return mem.get("v", SIGMA0[product] ** 2) / TURNOVER[product]


class DragonfruitTrend:
    """Lean in the direction of the posterior DRAGONFRUIT drift (conjugate normal, prior = the EDA drift).
    Regime-flip guard: a fast EWMA drift whose t-statistic is FLIP_Z against the lean zeroes it."""

    def target(self, state, mem):
        book = top_of_book(state.order_depths.get("DRAGONFRUIT"))
        if book is None:
            return mem.get("t", 0)
        mid = (book[0] + book[2]) / 2.0
        last = mem.get("m")
        mem["m"] = mid
        prec0 = 1.0 / (TREND_TAU * TREND_TAU)
        prec, num = mem.get("pr", prec0), mem.get("nu", TREND_MU0 * prec0)
        fast, fast_n = mem.get("f", 0.0), mem.get("fn", 0.0)
        if last is not None:
            dmid = mid - last
            s2 = SIGMA0["DRAGONFRUIT"] ** 2
            if dmid * dmid <= JUMP_K * JUMP_K * s2:
                beta = ewma_beta(TREND_FORGET_HL)
                prec = beta * prec + (1 - beta) * prec0 + 1.0 / s2  # forget toward the prior
                num = beta * num + (1 - beta) * TREND_MU0 * prec0 + dmid / s2
                fb = ewma_beta(FLIP_HL)
                fast, fast_n = fb * fast + (1 - fb) * dmid, fb * fast_n + (1 - fb)
        mem["pr"], mem["nu"], mem["f"], mem["fn"] = prec, num, fast, fast_n
        mu = num / prec
        lean = max(-1.0, min(1.0, mu / TREND_MU0))
        fast_mu = fast / fast_n if fast_n > 0 else 0.0
        fast_se = SIGMA0["DRAGONFRUIT"] * math.sqrt((1 - ewma_beta(FLIP_HL)) / (1 + ewma_beta(FLIP_HL)))
        if lean * fast_mu < 0 and abs(fast_mu) > FLIP_Z * fast_se:
            lean = 0.0
        mem["mu"] = mu
        mem["t"] = int(round(TREND_MAX * lean))
        return mem["t"]

    def edge(self, mem):
        return mem.get("mu", TREND_MU0)  # expected PnL per lot per tick

    def variance(self, mem):
        return SIGMA0["DRAGONFRUIT"] ** 2


class PeanutWideMaker:
    """Avellaneda-Stoikov on PEANUT_BUTTER with live sigma: reservation r = mid - q * gamma * sigma^2, half quote
    width = half spread + gamma * sigma^2 / 2, never inside the touch, small size and a tight inventory cap."""

    def intent(self, state, product, mem):
        book = top_of_book(state.order_depths.get(PEANUT))
        if book is None:
            return []
        bid, _, ask, _ = book
        mid = (bid + ask) / 2.0
        sigma2, _, jumped = update_vol(mem, mid, SIGMA0[PEANUT])
        update_markout(mem, state, PEANUT, mid, passive_only=True)
        q = state.position.get(PEANUT, 0)
        skew = PB_RISK_GT * sigma2
        out = []
        if abs(q) > PB_CAP:
            out += cross(book, -int(math.copysign(abs(q) - PB_CAP, q)))
        if jumped:
            return out
        r = mid - q * skew
        half = HALF_SPREAD[PEANUT] + skew / 2.0
        if q < PB_CAP:
            out.append((min(bid, math.floor(r - half)), min(PB_SIZE, PB_CAP - q)))
        if q > -PB_CAP:
            out.append((max(ask, math.ceil(r + half)), -min(PB_SIZE, PB_CAP + q)))
        return out

    def edge(self, mem):
        return mem.get("e", MARKOUT0[PEANUT])

    def variance(self, mem):
        return mem.get("v", SIGMA0[PEANUT] ** 2) / TURNOVER[PEANUT]


class PearlGroupHedge:
    """Minimum-variance cross hedge of the book-wide WHITE/BLACK/BLUE exposure. With covariance S (EWMA) and
    book positions x, trading h lots of pearl i changes the variance by -(Sx)_i^2 / S_ii at h = -(Sx)_i / S_ii.
    It picks the pearl with the largest reduction among those where it does not unwind another strategy's
    position, and trades only the part of h beyond the Davis-Norman band."""

    def update_cov(self, state, mem):
        books = [top_of_book(state.order_depths.get(p)) for p in PEARLS]
        if any(b is None for b in books):
            return None
        mids = [(b[0] + b[2]) / 2.0 for b in books]
        cov = mem.get("c")
        if cov is None:
            s = [SIGMA0[p] for p in PEARLS]
            cov = [s[0] ** 2, s[1] ** 2, s[2] ** 2, PEARL_CORR0[(0, 1)] * s[0] * s[1],
                   PEARL_CORR0[(0, 2)] * s[0] * s[2], PEARL_CORR0[(1, 2)] * s[1] * s[2]]
        last = mem.get("m")
        if last is not None:
            d = [mids[i] - last[i] for i in range(3)]
            if all(d[i] ** 2 <= JUMP_K * JUMP_K * cov[i] for i in range(3)):
                b = ewma_beta(PEARL_COV_HL)
                prods = [d[0] * d[0], d[1] * d[1], d[2] * d[2], d[0] * d[1], d[0] * d[2], d[1] * d[2]]
                cov = [b * c + (1 - b) * x for c, x in zip(cov, prods)]
        mem["m"], mem["c"] = mids, cov
        return books

    @staticmethod
    def matrix(cov):
        return [[cov[0], cov[3], cov[4]], [cov[3], cov[1], cov[5]], [cov[4], cov[5], cov[2]]]

    def plan(self, state, mem):
        """Returns {pearl: [(price, qty)]} for at most one pearl."""
        books = self.update_cov(state, mem)
        mem["gain"] = 0.0
        if books is None:
            return {}
        book_pos = getattr(state, "book_position", None) or state.position
        x = [book_pos.get(p, 0) for p in PEARLS]
        own = [state.position.get(p, 0) for p in PEARLS]
        S = self.matrix(mem["c"])
        g = [sum(S[i][j] * x[j] for j in range(3)) for i in range(3)]
        best = None
        for i in range(3):
            h = -g[i] / S[i][i]
            others = x[i] - own[i]
            if h * others < 0:
                continue  # would unwind another strategy's position on this pearl
            band = no_trade_band(HALF_SPREAD[PEARLS[i]], S[i][i])
            excess = abs(h) - band
            if excess < 1:
                continue
            qty = int(math.copysign(math.floor(excess), h))
            limit = LIMITS[PEARLS[i]]
            qty = max(-limit - min(own[i], x[i]), min(limit - max(own[i], x[i]), qty))
            if qty == 0:
                continue
            reduction = -(2 * qty * g[i] + qty * qty * S[i][i])  # variance drop per tick, exact for this qty
            if best is None or reduction > best[2]:
                best = (i, qty, reduction)
        if best is None:
            return {}
        i, qty, reduction = best
        mem["gain"] = RISK_GT * reduction / abs(qty) - HALF_SPREAD[PEARLS[i]]
        return {PEARLS[i]: cross(books[i], qty)}

    def intent(self, state, product, mem):
        return self.plan(state, mem).get(product, [])

    def edge(self, mem):
        """Risk-adjusted benefit per lot of the last hedge: RISK_GT x variance removed per lot minus the spread."""
        return mem.get("gain", 0.0)

    def variance(self, mem):
        return 0.0  # it only ever reduces book variance


# ---------------------------------------------------------------- trader


class Trader:
    def __init__(self):
        self.basket = HedgedBasketMaker()
        self.leg = LegMaker()
        self.trend = DragonfruitTrend()
        self.peanut = PeanutWideMaker()
        self.pearls = PearlGroupHedge()

    @staticmethod
    def load(trader_data):
        try:
            mem = json.loads(trader_data) if trader_data else {}
            return mem if isinstance(mem, dict) else {}
        except (ValueError, TypeError):
            return {}

    def run(self, state):
        mem = self.load(state.traderData)
        intents = {}
        try:
            intents = self.collect(state, mem)
        except Exception:  # a bug must never take the submission down: trade nothing this tick, count it
            mem["err"] = mem.get("err", 0) + 1
            intents = {}
        orders = {}
        for product, wanted in intents.items():
            kept = clip_orders(wanted, state.position.get(product, 0), LIMITS[product])
            if kept:
                orders[product] = [Order(product, price, qty) for price, qty in kept]
        return orders, 0, json.dumps(mem, separators=(",", ":"))

    def collect(self, state, mem):
        intents = {BASKET: self.basket.intent(state, BASKET, mem.setdefault("B", {}))}
        hedge = self.basket.hedge_targets(state.position.get(BASKET, 0))
        trend = self.trend.target(state, mem.setdefault("T", {}))
        for leg in LEGS:
            room = LIMITS[leg] - LEG_SIZE
            anchor = hedge[leg] + (trend if leg == "DRAGONFRUIT" else 0)
            anchor = max(-room, min(room, anchor))
            intents[leg] = self.leg.intent(state, leg, mem.setdefault("L" + leg[0], {}), anchor)
        intents[PEANUT] = self.peanut.intent(state, PEANUT, mem.setdefault("P", {}))
        intents.update(self.pearls.plan(state, mem.setdefault("H", {})))
        return intents
