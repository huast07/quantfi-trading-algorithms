"""S4 v3: TELLURIUM jump specialist built from separate sub-strategies over one shared jump model.

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
ENABLE = ("drift", "direction")

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
SHOCK_MERGE = 5               # outsized ticks this close together form one ramp (shock), not jumps
SHOCK_COOL = 1000             # crash liquidity windows last 500-1,500 ticks
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

    def commit(self, t, sign, size):
        m = self.mem
        m["J"].append([t, sign, size])
        m["n"] += 1
        m["lj"] = t
        m["nu" if sign > 0 else "nd"] += 1
        out = []
        for g, lp in zip(SCALES, m["sc"]):
            u = size / g
            dens = sum(math.exp(-0.5 * ((u - s) / KDE_BW) ** 2) for s in SIZES) / len(SIZES) / g + 1e-12
            out.append(lp + math.log(dens))
        top = max(out)
        m["sc"] = [x - top for x in out]

    def in_shock(self):
        return self.mem["t"] - self.mem.get("sh", -10 ** 9) < SHOCK_COOL

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
        pend = m.get("pj")
        if abs(d) > thr:
            # the generator's jumps are one-tick; two outsized ticks in a row are a ramp (crash/shock), not a jump
            if pend is not None or t - m.get("sh", -10 ** 9) < SHOCK_MERGE:
                m["pj"] = None
                m["sh"] = t
                m["J"] = []
                return True
            m["pj"] = [t, 1 if d > 0 else -1, abs(d)]
            return True
        if pend is not None:
            m["pj"] = None
            self.commit(*pend)
            d = 0.0
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


HORIZONS = (10, 25, 50, 100, 150, 200, 300, 400, 600, 1000, 2000)
URGENT_H = 400                 # horizon whose expected move decides taking vs joining inside
# FlowLead: chase flow vs calm background flow (params.json flow: base_rate .0076, order_prob bin0 ~.5, lean .87)
LEAD_RATE, BASE_RATE, LEAD_LEAN = 0.40, 0.0076, 0.87
LEAD_PRIOR = 0.002            # jump rate .001 x 100-tick lead x 2% prior belief that flow leads jumps
LEAD_CAP = 20.0               # cap on the CUSUM so evidence fades within ~50 quiet ticks after a burst
LEAD_HORIZON = 90.0           # expected ticks from detection to the jump


class DriftRider:
    """(b) E[response | jump sizes, ticks since jump], from the calibrated response scaled by the online beta."""

    def __init__(self, model):
        self.model = model

    def mean_var(self, h):
        mu, dr0, imp = self.model.response_move(h)
        return mu, imp + self.model.mem["bv"] * dr0 * dr0


class DirectionTilt:
    """(a) the day's jump-direction persistence: rate * (2p - 1) * mean net jump move per tick."""

    def __init__(self, model):
        self.model = model
        self.mu1 = model.direction_drift()

    def mean_var(self, h):
        return self.mu1 * h, 0.0


class FlowLead:
    """(e) a burst of one-sided prints with no recent jump: log-likelihood ratio of chase vs background flow."""

    @staticmethod
    def init():
        return {"U": 0.0, "D": 0.0}

    def __init__(self, model, mem):
        self.model, self.mem = model, mem

    def update(self, signs):
        """Page CUSUM of the log-likelihood ratio, lead-up and lead-down vs background, one taker order per tick
        at most (signs: +1 buy above the previous mid, -1 sell below)."""
        m = self.mem
        n = len(signs)
        up = sum(1 for s in signs if s > 0)
        dn = n - up
        count = n * math.log(LEAD_RATE / BASE_RATE) - (LEAD_RATE - BASE_RATE)
        with_, against = math.log(LEAD_LEAN / 0.5), math.log((1 - LEAD_LEAN) / 0.5)
        m["U"] = min(LEAD_CAP, max(0.0, m["U"] + count + up * with_ + dn * against))
        m["D"] = min(LEAD_CAP, max(0.0, m["D"] + count + dn * with_ + up * against))
        if self.model.since_jump() < WIDEN_TICKS or self.model.in_shock():
            m["U"] = m["D"] = 0.0

    def prob(self):
        L = max(self.mem["U"], self.mem["D"])
        lo = math.log(LEAD_PRIOR / (1 - LEAD_PRIOR)) + L
        return 1 / (1 + math.exp(-lo)), (1 if self.mem["U"] >= self.mem["D"] else -1)

    def mean_var(self, h):
        p, sgn = self.prob()
        s = self.model.scale()
        return p * sgn * s * REF * min(1.0, h / LEAD_HORIZON), 0.0


class ChaserSeller:
    """(c) rest the chased side at the touch while chasers sweep, if premium beats the full expected path
    (response + direction) to the exit horizon; hold fills to CHASE_EXIT ticks or a stop."""

    @staticmethod
    def init():
        return {"q": 0, "px": 0.0, "t0": 0, "quote": None}

    def __init__(self, model, mem, mean_fn):
        self.model, self.mem, self.mean_fn = model, mem, mean_fn
        self.edge = 0.0

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
        m, mid, t = self.mem, (bid + ask) / 2, self.model.mem["t"]
        m["quote"] = None
        if m["q"] != 0:
            adverse = (mid - m["px"]) * (1 if m["q"] < 0 else -1)
            if t - m["t0"] >= CHASE_EXIT or adverse > CHASE_STOP or self.model.in_shock():
                m["q"] = 0
        k = self.model.since_jump()
        sign = self.model.last_sign()
        if k >= CHASE_TICKS or sign == 0 or self.model.in_shock():
            return None
        px = ask if sign > 0 else bid
        mu, _ = self.mean_fn(CHASE_EXIT)
        self.edge = abs(px - mid) - sign * mu
        room = CHASE_CAP - abs(m["q"])
        if self.edge <= 0 or room <= 0:
            return None
        m["quote"] = [px, -sign]
        return px, -sign * room


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
        mem.setdefault("fl", FlowLead.init())
        model = JumpModel(mem["jm"])
        prev_mid = model.mem["m"]
        bid, ask = max(od.buy_orders), min(od.sell_orders)
        mid = (bid + ask) / 2
        model.update(mid)
        comps = []
        if "drift" in ENABLE:
            comps.append(DriftRider(model))
        if "direction" in ENABLE:
            comps.append(DirectionTilt(model))
        if "lead" in ENABLE:
            lead = FlowLead(model, mem["fl"])
            if prev_mid is not None:
                stamps = {}
                for tr in state.market_trades.get(P, []):
                    stamps.setdefault(tr.timestamp, []).append(1 if tr.price > prev_mid else -1)
                lead.update([1 if sum(v) > 0 else -1 for v in stamps.values() if sum(v) != 0])
            comps.append(lead)

        def mean_var(h):
            mu, var = 0.0, model.base_var(h)
            for c in comps:
                a, b = c.mean_var(h)
                mu += a
                var += b
            return mu, var

        best = (0.0, 1.0, 0.0)
        for h in HORIZONS:
            mu, var = mean_var(h)
            z = abs(mu) / math.sqrt(var)
            if z > best[2]:
                best = (mu, var, z)
        target = best[0] / (GAMMA * best[1])
        quotes = []
        if "chaser" in ENABLE:
            chaser = ChaserSeller(model, mem["cs"], mean_var)
            chaser.on_fills([(tr.price, tr.quantity if tr.buyer == "SUBMISSION" else -tr.quantity)
                             for tr in state.own_trades.get(P, []) if "SUBMISSION" in (tr.buyer, tr.seller)])
            cq = chaser.step(bid, ask)
            target = max(-LIMIT, min(LIMIT, target)) + mem["cs"]["q"]
            if cq:
                quotes.append(cq)
        target = int(round(max(-LIMIT, min(LIMIT, target))))
        urgent, _ = mean_var(URGENT_H)
        pos = state.position.get(P, 0)
        return self.execute(od, bid, ask, pos, target, urgent, quotes)

    def execute(self, od, bid, ask, pos, target, urgent, quotes):
        """Take toward the target when the short-horizon expected move beats the spread, else join inside."""
        out = []
        buy_room, sell_room = LIMIT - pos, LIMIT + pos
        delta = target - pos
        mid, half = (bid + ask) / 2, (ask - bid) / 2
        if abs(delta) >= MIN_TRADE or (target == 0 and pos != 0):
            aggressive = abs(urgent) > half and (urgent > 0) == (delta > 0)
            if delta > 0:
                qty = min(delta, buy_room)
                if aggressive:
                    for px in sorted(od.sell_orders):
                        if px > mid + abs(urgent) or qty <= 0:
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
                        if px < mid - abs(urgent) or qty <= 0:
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
