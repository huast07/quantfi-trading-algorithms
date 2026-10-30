"""S4 v2: TELLURIUM jump specialist built from separate sub-strategies over one shared jump model.

Shared estimator: JumpModel (jump detector, size-scale / direction / rate posteriors, response-factor regression).
Sub-strategies (each with intent, edge, variance and its own mem):
  DriftRider     (b) post-jump response: ride the follow-through, fade oversized jumps' give-back.
  DirectionTilt  (a) jump-direction persistence: hold the day's posterior jump direction.
  ChaserSeller   (c) rest quotes on the chased side at the touch; hold the fill to a fixed exit horizon.
  CalmMaker      (d) tiny wide quotes in calm regimes, pulled on a jump.
"""

import json
import math

from datamodel import Order, OrderDepth, TradingState

P = "TELLURIUM"
LIMIT = 40
ENABLE = ("drift", "direction", "chaser", "calm")

# ---- calibrated constants (params.json TELLURIUM; EDA Prices p.13, Trades p.24-25) ----
KNOTS = (0, 10, 50, 100, 200, 300, 400, 600)
DRIFT = (0.0, 0.90, 3.55, 11.97, 23.67, 1.39, -12.85, -23.77)
SLOPE = (0.0, -0.149, -0.592, -0.925, -1.162, -1.038, -0.991, -0.984)
REF = 170.13
WINDOW = KNOTS[-1]
SIZES = (77.5, 106.5, 159.5, 126.5, 128.0, 260.5, 199.5, 190.0, 190.5, 126.0, 175.5, 216.0, 139.5, 170.5, 231.5,
         105.0, 194.0, 102.5, 282.5, 256.0, 107.0, 151.5, 96.5, 236.0, 157.0, 172.5, 300.5, 199.0, 103.0, 143.5)
SIZE_M2 = sum(s * s for s in SIZES) / len(SIZES)
SCALES = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0)
SCALE_PRIOR_SD = 0.5
KDE_BW = 12.0
CGRID = (0.1, 0.25, 0.55, 1.2, 2.5, 5.0)
C_CENTER, C_LOG_SD = 0.55, 1.1
RATE0, PRIOR_TICKS = 0.001, 5000.0
JUMP_FLOOR = 77.5 / 2
JUMP_Z = 10.0
CALM_VAR0 = 2.6
CALM_ALPHA = 0.002
LR_RATIO = 7.0 / 2.6
IMPACT_VAR_WINDOW = 860.0
CHASE_TICKS = 200             # chaser window (87% of prints within 200 ticks of a jump)
WIDEN_TICKS = 400             # market maker widens / thins for ~400 ticks
BETA0, BETA_V0 = 1.0, 0.25
BETA_NOISE = 25.0
DRIFT_H = (10, 25, 50, 100, 150, 200, 300, 400, 600)
DIR_H = (1000, 2000)
GAMMA = 0.00005
MIN_TRADE = 3
# ChaserSeller
CHASE_CAP = 20
CHASE_EXIT = 600              # hold to the end of the response window
CHASE_STOP = 60.0             # per-lot adverse move that closes the inventory
# CalmMaker
CALM_SIZE = 2
CALM_CAP = 6
CALM_EDGE = 4                 # quote half width beyond mid (touch half width is ~4.9)


def interp(k):
    if k >= WINDOW:
        return DRIFT[-1], SLOPE[-1]
    if k <= 0:
        return 0.0, 0.0
    for i in range(1, len(KNOTS)):
        if k <= KNOTS[i]:
            w = (k - KNOTS[i - 1]) / (KNOTS[i] - KNOTS[i - 1])
            return DRIFT[i - 1] + w * (DRIFT[i] - DRIFT[i - 1]), SLOPE[i - 1] + w * (SLOPE[i] - SLOPE[i - 1])
    return DRIFT[-1], SLOPE[-1]


def response(k, size, scale):
    d, s = interp(k)
    return d * scale + s * (size - REF * scale)


def betaln(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


class JumpModel:
    """Shared online estimator; all state in mem."""

    @staticmethod
    def init():
        return {"t": 0, "m": None, "cv": CALM_VAR0, "J": [], "nu": 0, "nd": 0, "n": 0, "lj": -10 ** 9,
                "sc": [-0.5 * (math.log(g) / SCALE_PRIOR_SD) ** 2 for g in SCALES], "bm": BETA0, "bv": BETA_V0}

    def __init__(self, mem):
        self.mem = mem

    def scale(self):
        w = [math.exp(x) for x in self.mem["sc"]]
        return sum(g * wi for g, wi in zip(SCALES, w)) / sum(w)

    def beta(self):
        return min(max(self.mem["bm"], 0.0), 1.5)

    def rate(self):
        return (RATE0 * PRIOR_TICKS + self.mem["n"]) / (PRIOR_TICKS + self.mem["t"])

    def up_prob(self):
        nu, nd = self.mem["nu"], self.mem["nd"]
        logw, preds = [], []
        for c in CGRID:
            prior = -0.5 * ((math.log(c) - math.log(C_CENTER)) / C_LOG_SD) ** 2
            logw.append(prior + betaln(c + nu, c + nd) - betaln(c, c))
            preds.append((c + nu) / (2 * c + nu + nd))
        m = max(logw)
        w = [math.exp(x - m) for x in logw]
        return sum(wi * p for wi, p in zip(w, preds)) / sum(w)

    def since_jump(self):
        return self.mem["t"] - self.mem["lj"]

    def last_sign(self):
        return self.mem["J"][-1][1] if self.mem["J"] else 0

    def update(self, mid):
        m = self.mem
        m["t"] += 1
        t, prev = m["t"], m["m"]
        m["m"] = mid
        if prev is None:
            return False
        d = mid - prev
        scale = self.scale()
        thr = max(JUMP_FLOOR * min(scale, 1.0), JUMP_Z * math.sqrt(m["cv"]))
        if abs(d) > thr:
            sign = 1 if d > 0 else -1
            m["J"].append([t, sign, abs(d)])
            m["n"] += 1
            m["lj"] = t
            m["nu" if sign > 0 else "nd"] += 1
            out = []
            for g, lp in zip(SCALES, m["sc"]):
                u = abs(d) / g
                dens = sum(math.exp(-0.5 * ((u - s) / KDE_BW) ** 2) for s in SIZES) / len(SIZES) / g + 1e-12
                out.append(lp + math.log(dens))
            top = max(out)
            m["sc"] = [x - top for x in out]
            return True
        x = 0.0
        for jt, sg, sz in m["J"]:
            k = t - jt
            x += sg * (response(k, sz, scale) - response(k - 1, sz, scale))
        if x != 0.0:
            prec = 1.0 / m["bv"] + x * x / BETA_NOISE
            m["bm"] = (m["bm"] / m["bv"] + x * d / BETA_NOISE) / prec
            m["bv"] = 1.0 / prec
        else:
            m["cv"] += CALM_ALPHA * (d * d - m["cv"])
        m["J"] = [j for j in m["J"] if t - j[0] < WINDOW]
        return False

    def response_move(self, h):
        """(mean, unscaled mean) of the summed active-jump responses over the next h ticks."""
        t, scale = self.mem["t"], self.scale()
        dr0 = 0.0
        imp = 0.0
        for jt, sg, sz in self.mem["J"]:
            k = t - jt
            dr0 += sg * (response(k + h, sz, scale) - response(k, sz, scale))
            imp += IMPACT_VAR_WINDOW * min(h, max(0.0, CHASE_TICKS - k)) / CHASE_TICKS
        return self.beta() * dr0, dr0, imp

    def base_var(self, h):
        """Diffusion plus future-jump variance over h ticks."""
        s = self.scale()
        return self.mem["cv"] * LR_RATIO * h + self.rate() * h * s * s * SIZE_M2

    def direction_drift(self):
        """Per-tick expected move from future jumps: rate * (2p - 1) * mean net jump move."""
        s = self.scale()
        return self.rate() * (2 * self.up_prob() - 1) * s * (REF + self.beta() * DRIFT[-1])


class DriftRider:
    """(b) E[response | sizes, ticks since] over the best horizon, mean-variance sized."""

    def __init__(self, model):
        self.model = model
        self._edge, self._var = 0.0, 1.0

    def target(self):
        best = (0.0, 1.0, 0.0)
        for h in DRIFT_H:
            mu, dr0, imp = self.model.response_move(h)
            if mu == 0.0:
                continue
            var = self.model.base_var(h) + imp + self.model.mem["bv"] * dr0 * dr0
            z = abs(mu) / math.sqrt(var)
            if z > best[2]:
                best = (mu, var, z)
        self._edge, self._var = best[0], best[1]
        return max(-LIMIT, min(LIMIT, best[0] / (GAMMA * best[1])))

    def edge(self):
        return self._edge

    def variance(self):
        return self._var


class DirectionTilt:
    """(a) the day's jump-direction persistence (Beta-Binomial over a concentration grid)."""

    def __init__(self, model):
        self.model = model
        self._edge, self._var = 0.0, 1.0

    def target(self):
        mu1 = self.model.direction_drift()
        best = (0.0, 1.0, 0.0)
        for h in DIR_H:
            mu, var = mu1 * h, self.model.base_var(h)
            z = abs(mu) / math.sqrt(var)
            if z > best[2]:
                best = (mu, var, z)
        self._edge, self._var = best[0], best[1]
        return max(-LIMIT, min(LIMIT, best[0] / (GAMMA * best[1])))

    def edge(self):
        return self._edge

    def variance(self):
        return self._var


class ChaserSeller:
    """(c) rest the chased side at the touch while chasers sweep; hold the fills to CHASE_EXIT ticks."""

    @staticmethod
    def init():
        return {"q": 0, "px": 0.0, "t0": 0, "quote": None}

    def __init__(self, model, mem):
        self.model, self.mem = model, mem
        self._edge, self._var = 0.0, 1.0

    def on_fills(self, fills):
        quote = self.mem["quote"]
        if not quote:
            return
        px, side = quote
        for fpx, fq in fills:
            if fpx == px and (fq > 0) == (side > 0):
                old = self.mem["q"]
                new = old + fq
                self.mem["px"] = (self.mem["px"] * abs(old) + fpx * abs(fq)) / max(abs(new), 1)
                self.mem["q"] = new
                self.mem["t0"] = self.model.mem["t"]

    def step(self, bid, ask):
        """Exit rule, then the quote to rest this tick (price, signed qty)."""
        m, mid, t = self.mem, (bid + ask) / 2, self.model.mem["t"]
        self.mem["quote"] = None
        if m["q"] != 0:
            adverse = (mid - m["px"]) * (1 if m["q"] < 0 else -1)
            if t - m["t0"] >= CHASE_EXIT or adverse > CHASE_STOP:
                m["q"] = 0
        k = self.model.since_jump()
        sign = self.model.last_sign()
        if k >= CHASE_TICKS or sign == 0:
            return None
        px = ask if sign > 0 else bid
        premium = abs(px - mid)
        mu, _, imp = self.model.response_move(CHASE_EXIT - k)
        edge = premium - sign * mu
        self._edge = edge
        self._var = self.model.base_var(CHASE_EXIT - k) + imp
        room = CHASE_CAP - abs(m["q"])
        if edge <= 0 or room <= 0:
            return None
        self.mem["quote"] = [px, -sign]
        return px, -sign * room

    def edge(self):
        return self._edge

    def variance(self):
        return self._var


class CalmMaker:
    """(d) tiny two-sided quotes beyond the touch while no jump is recent; inventory dropped on a jump."""

    @staticmethod
    def init():
        return {"q": 0, "quote": None}

    def __init__(self, model, mem):
        self.model, self.mem = model, mem

    def on_fills(self, fills):
        quote = self.mem["quote"]
        if not quote:
            return
        for fpx, fq in fills:
            if (fq > 0 and fpx == quote[0]) or (fq < 0 and fpx == quote[1]):
                self.mem["q"] += fq

    def step(self, bid, ask, jumped):
        self.mem["quote"] = None
        if jumped or self.model.since_jump() < WIDEN_TICKS:
            self.mem["q"] = 0
            return []
        mid = (bid + ask) / 2
        q = self.mem["q"]
        bpx = min(bid, math.floor(mid - CALM_EDGE)) - (1 if q > 0 else 0)
        apx = max(ask, math.ceil(mid + CALM_EDGE)) + (1 if q < 0 else 0)
        self.mem["quote"] = [bpx, apx]
        out = []
        if q < CALM_CAP:
            out.append((bpx, min(CALM_SIZE, CALM_CAP - q)))
        if q > -CALM_CAP:
            out.append((apx, -min(CALM_SIZE, CALM_CAP + q)))
        return out

    def edge(self):
        return 0.0

    def variance(self):
        return 0.0


class Trader:
    def run(self, state: TradingState):
        try:
            mem = json.loads(state.traderData) if state.traderData else {}
        except Exception:
            mem = {}
        orders = {}
        try:
            if P in state.order_depths:
                orders[P] = self.trade(state, mem)
        except Exception:
            orders = {}
        return orders, 0, json.dumps(mem, separators=(",", ":"))

    def trade(self, state, mem):
        od: OrderDepth = state.order_depths[P]
        if not od.buy_orders or not od.sell_orders:
            return []
        mem.setdefault("jm", JumpModel.init())
        mem.setdefault("cs", ChaserSeller.init())
        mem.setdefault("mm", CalmMaker.init())
        model = JumpModel(mem["jm"])
        chaser = ChaserSeller(model, mem["cs"])
        calm = CalmMaker(model, mem["mm"])
        fills = [(tr.price, tr.quantity if tr.buyer == "SUBMISSION" else -tr.quantity)
                 for tr in state.own_trades.get(P, []) if "SUBMISSION" in (tr.buyer, tr.seller)]
        chaser.on_fills(fills)
        calm.on_fills(fills)
        bid, ask = max(od.buy_orders), min(od.sell_orders)
        mid = (bid + ask) / 2
        jumped = model.update(mid)
        pos = state.position.get(P, 0)

        target, urgent = 0.0, 0.0
        if "drift" in ENABLE:
            dr = DriftRider(model)
            target += dr.target()
            urgent = dr.edge()
        if "direction" in ENABLE:
            target += DirectionTilt(model).target()
        quotes = []
        if "chaser" in ENABLE:
            cq = chaser.step(bid, ask)
            target += mem["cs"]["q"]
            if cq:
                quotes.append(cq)
        else:
            mem["cs"]["q"] = 0
        if "calm" in ENABLE:
            quotes += calm.step(bid, ask, jumped)
            target += mem["mm"]["q"]
        else:
            mem["mm"]["q"] = 0
        target = int(round(max(-LIMIT, min(LIMIT, target))))
        return self.execute(od, bid, ask, pos, target, urgent, quotes)

    def execute(self, od, bid, ask, pos, target, urgent, quotes):
        """Move toward the net target (take if the drift edge beats the round trip, else join inside), then add
        the component quotes within the remaining limit room."""
        out = []
        buy_room, sell_room = LIMIT - pos, LIMIT + pos
        delta = target - pos
        mid, half = (bid + ask) / 2, (ask - bid) / 2
        if abs(delta) >= MIN_TRADE or (target == 0 and pos != 0):
            aggressive = abs(urgent) > 2 * half and (urgent > 0) == (delta > 0)
            if delta > 0:
                qty = min(delta, buy_room)
                if aggressive:
                    for px in sorted(od.sell_orders):
                        if px > mid + abs(urgent) / 2 or qty <= 0:
                            break
                        v = min(qty, abs(od.sell_orders[px]))
                        out.append(Order(P, px, v))
                        qty -= v
                        buy_room -= v
                if qty > 0:
                    px = bid + 1 if ask - bid > 2 else bid
                    out.append(Order(P, px, qty))
                    buy_room -= qty
            elif delta < 0:
                qty = min(-delta, sell_room)
                if aggressive:
                    for px in sorted(od.buy_orders, reverse=True):
                        if px < mid - abs(urgent) / 2 or qty <= 0:
                            break
                        v = min(qty, od.buy_orders[px])
                        out.append(Order(P, px, -v))
                        qty -= v
                        sell_room -= v
                if qty > 0:
                    px = ask - 1 if ask - bid > 2 else ask
                    out.append(Order(P, px, -qty))
                    sell_room -= qty
        for px, q in quotes:
            if q > 0 and buy_room > 0:
                v = min(q, buy_room)
                out.append(Order(P, int(px), v))
                buy_room -= v
            elif q < 0 and sell_room > 0:
                v = min(-q, sell_room)
                out.append(Order(P, int(px), -v))
                sell_room -= v
        return out
