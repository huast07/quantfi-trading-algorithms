"""S4 v1: TELLURIUM jump model, mean-variance target position, take/passive execution."""

import json
import math

from datamodel import Order, OrderDepth, TradingState

P = "TELLURIUM"
LIMIT = 40

# Post-jump response (params.json TELLURIUM.process.response, fitted on the 30 real jumps):
# E[move in jump direction, k ticks after] = drift(k) * scale + slope(k) * (size - REF * scale)
KNOTS = (0, 10, 50, 100, 200, 300, 400, 600)
DRIFT = (0.0, 0.90, 3.55, 11.97, 23.67, 1.39, -12.85, -23.77)
SLOPE = (0.0, -0.149, -0.592, -0.925, -1.162, -1.038, -0.991, -0.984)
REF = 170.13
WINDOW = KNOTS[-1]
# Real jump sizes (params.json jump_sizes): the support used for the size-scale posterior.
SIZES = (77.5, 106.5, 159.5, 126.5, 128.0, 260.5, 199.5, 190.0, 190.5, 126.0, 175.5, 216.0, 139.5, 170.5, 231.5,
         105.0, 194.0, 102.5, 282.5, 256.0, 107.0, 151.5, 96.5, 236.0, 157.0, 172.5, 300.5, 199.0, 103.0, 143.5)
SIZE_M2 = sum(s * s for s in SIZES) / len(SIZES)
SCALES = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0)
SCALE_PRIOR_SD = 0.5          # log-scale prior sd: the observed days all have scale 1
KDE_BW = 12.0                 # size kernel bandwidth (measured jump = true size +- book jitter)
# Direction persistence: day up-probability ~ Beta(c, c); c calibrated 0.55, 95% CI 0.07-5.1 (log sd ~1.1).
CGRID = (0.1, 0.25, 0.55, 1.2, 2.5, 5.0)
C_CENTER, C_LOG_SD = 0.55, 1.1
# Jump rate: Gamma prior worth PRIOR_TICKS ticks at 10 jumps / 10,000 ticks.
RATE0, PRIOR_TICKS = 0.001, 5000.0
# Jump detection: calm tick sd ~1.6 (max calm |d| 13.5 over 30k real ticks); smallest real jump 77.5.
JUMP_FLOOR = 77.5 / 2
JUMP_Z = 10.0
CALM_VAR0 = 2.6
CALM_ALPHA = 0.002
# Long-horizon diffusion variance per tick of the calibrated local trend (sigma .70, trend sd .31, phi .95):
# (c + tau / (1 - phi))^2 ~ 7.0, i.e. 7.0 / 2.6 times the one-tick variance.
LR_RATIO = 7.0 / 2.6
# Chase impact noise: ~0.54 per unexpected lot, ~860 variance over the 200-tick chase window.
IMPACT_VAR_WINDOW = 860.0
BETA0, BETA_V0 = 1.0, 0.25
BETA_NOISE = 25.0             # per-tick increment noise variance incl. trend persistence
HORIZONS = (10, 25, 50, 100, 150, 200, 300, 400, 600, 1000)
GAMMA = 0.0015                # mean-variance risk aversion (per lot per price^2)
MIN_TRADE = 3


def interp(k):
    """Index-free linear interpolation of the response at k ticks; returns (drift, slope)."""
    if k >= WINDOW:
        return DRIFT[-1], SLOPE[-1]
    if k <= 0:
        return 0.0, 0.0
    for i in range(1, len(KNOTS)):
        if k <= KNOTS[i]:
            w = (k - KNOTS[i - 1]) / (KNOTS[i] - KNOTS[i - 1])
            return (DRIFT[i - 1] + w * (DRIFT[i] - DRIFT[i - 1]), SLOPE[i - 1] + w * (SLOPE[i] - SLOPE[i - 1]))
    return DRIFT[-1], SLOPE[-1]


def response(k, size, scale):
    d, s = interp(k)
    return d * scale + s * (size - REF * scale)


def betaln(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def up_prob(nu, nd):
    """Posterior predictive P(next jump up) under a log-normal prior over the Beta(c, c) concentration."""
    logw, preds = [], []
    for c in CGRID:
        prior = -0.5 * ((math.log(c) - math.log(C_CENTER)) / C_LOG_SD) ** 2
        logw.append(prior + betaln(c + nu, c + nd) - betaln(c, c))
        preds.append((c + nu) / (2 * c + nu + nd))
    m = max(logw)
    w = [math.exp(x - m) for x in logw]
    return sum(wi * p for wi, p in zip(w, preds)) / sum(w)


def scale_update(logpost, size):
    out = []
    for g, lp in zip(SCALES, logpost):
        u = size / g
        dens = sum(math.exp(-0.5 * ((u - s) / KDE_BW) ** 2) for s in SIZES) / len(SIZES) / g + 1e-12
        out.append(lp + math.log(dens))
    m = max(out)
    return [x - m for x in out]


def scale_mean(logpost):
    w = [math.exp(x) for x in logpost]
    return sum(g * wi for g, wi in zip(SCALES, w)) / sum(w)


class Trader:
    def init_state(self):
        return {
            "t": 0, "m": None, "cv": CALM_VAR0, "J": [], "nu": 0, "nd": 0, "n": 0,
            "sc": [-0.5 * (math.log(g) / SCALE_PRIOR_SD) ** 2 for g in SCALES],
            "bm": BETA0, "bv": BETA_V0,
        }

    def run(self, state: TradingState):
        try:
            st = json.loads(state.traderData) if state.traderData else self.init_state()
        except Exception:
            st = self.init_state()
        orders = {}
        try:
            if P in state.order_depths:
                orders[P] = self.trade(state, st)
        except Exception:
            orders = {}
        return orders, 0, json.dumps(st, separators=(",", ":"))

    def update(self, st, mid):
        """Jump detection, posteriors, and the beta regression on non-jump increments."""
        st["t"] += 1
        t = st["t"]
        prev = st["m"]
        st["m"] = mid
        if prev is None:
            return
        d = mid - prev
        scale = scale_mean(st["sc"])
        thr = max(JUMP_FLOOR * min(scale, 1.0), JUMP_Z * math.sqrt(st["cv"]))
        if abs(d) > thr:
            sign = 1 if d > 0 else -1
            st["J"].append([t, sign, abs(d)])
            st["n"] += 1
            st["nu" if sign > 0 else "nd"] += 1
            st["sc"] = scale_update(st["sc"], abs(d))
            return
        # beta regression: increment explained by the unscaled response increments of active jumps
        x = 0.0
        for jt, sg, sz in st["J"]:
            k = t - jt
            x += sg * (response(k, sz, scale) - response(k - 1, sz, scale))
        if x != 0.0:
            prec = 1.0 / st["bv"] + x * x / BETA_NOISE
            st["bm"] = (st["bm"] / st["bv"] + x * d / BETA_NOISE) / prec
            st["bv"] = 1.0 / prec
        else:
            st["cv"] += CALM_ALPHA * (d * d - st["cv"])
        st["J"] = [j for j in st["J"] if t - j[0] < WINDOW]

    def forecast(self, st):
        """Best horizon's (mean, variance) of the price change, and the mean-variance target."""
        t = st["t"]
        scale = scale_mean(st["sc"])
        beta = min(max(st["bm"], 0.0), 1.5)
        rate = (RATE0 * PRIOR_TICKS + st["n"]) / (PRIOR_TICKS + t)
        p = up_prob(st["nu"], st["nd"])
        jump_mean = scale * (REF + beta * DRIFT[-1])
        bg = rate * (2 * p - 1) * jump_mean
        lr = st["cv"] * LR_RATIO
        best = (0.0, 1.0, 0.0)
        for h in HORIZONS:
            mu_r = 0.0
            dr0 = 0.0
            imp = 0.0
            for jt, sg, sz in st["J"]:
                k = t - jt
                delta = sg * (response(k + h, sz, scale) - response(k, sz, scale))
                dr0 += delta
                rem = max(0.0, 200.0 - k)
                imp += IMPACT_VAR_WINDOW * min(h, rem) / 200.0
            mu = beta * dr0 + bg * h
            var = lr * h + imp + rate * h * scale * scale * SIZE_M2 + st["bv"] * dr0 * dr0
            z = abs(mu) / math.sqrt(var)
            if z > best[2]:
                best = (mu, var, z)
        mu, var, _ = best
        q = mu / (GAMMA * var)
        return max(-LIMIT, min(LIMIT, q)), mu

    def trade(self, state, st):
        od: OrderDepth = state.order_depths[P]
        if not od.buy_orders or not od.sell_orders:
            return []
        bid = max(od.buy_orders)
        ask = min(od.sell_orders)
        mid = (bid + ask) / 2
        self.update(st, mid)
        pos = state.position.get(P, 0)
        q, mu = self.forecast(st)
        target = int(round(q))
        delta = target - pos
        out = []
        if abs(delta) < MIN_TRADE and not (target == 0 and pos != 0 and abs(delta) > 0):
            return out
        half = (ask - bid) / 2
        aggressive = abs(mu) > 2 * half
        if delta > 0:
            room = LIMIT - pos
            qty = min(delta, room)
            if aggressive:
                limit_px = mid + abs(mu) / 2
                for px in sorted(od.sell_orders):
                    if px > limit_px or qty <= 0:
                        break
                    v = min(qty, abs(od.sell_orders[px]))
                    out.append(Order(P, px, v))
                    qty -= v
            if qty > 0:
                px = bid + 1 if ask - bid > 2 else bid
                out.append(Order(P, px, qty))
        elif delta < 0:
            room = LIMIT + pos
            qty = min(-delta, room)
            if aggressive:
                limit_px = mid - abs(mu) / 2
                for px in sorted(od.buy_orders, reverse=True):
                    if px < limit_px or qty <= 0:
                        break
                    v = min(qty, od.buy_orders[px])
                    out.append(Order(P, px, -v))
                    qty -= v
            if qty > 0:
                px = ask - 1 if ask - bid > 2 else ask
                out.append(Order(P, px, -qty))
        return out
