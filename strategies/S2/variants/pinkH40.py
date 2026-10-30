"""S2 - structural alpha on the QuantiFi delta-one products.

Base layer: an inventory-aware touch quoter (Ho & Stoll 1981; Avellaneda & Stoikov 2008) on the 15 benign
products. Each tick, product p gets a reservation price
    r = fair + alpha - k * (position - target),      k = half_spread / limit
where `fair` is the EDA's best real-time fair value, `alpha` a short-horizon conditional expected move and `target`
the position a structural signal wants. Noise takers in this market hit the same-tick touch, and the engine fills a
resting order at or better than the trade price, so we post at the touch (maximal edge, same fill odds) whenever the
touch is at least MIN_EDGE from r, and cross the book only when the expected edge clears the touch cost.

Structural signals (each switchable in CONFIG, each an online estimate of a conditional expectation):
  PINK_PEARLS   plug: hazard (Beta-Bernoulli per |dev| bucket) x jump size (recursive LS slope on dev).
  GOLDEN_PEARLS steps: two-sided CUSUM changepoint on mid vs plateau; ramp speed gives step size; WHITE/BLACK ride
                the absorption.
  BLUE_PEARLS   trend: Bayesian drift (prior from the three real days) with a fast/slow sign guard; momentum lean.
  TOFFEE_CAKE   OU: slow-EWMA anchor, EWMA-moment kappa estimate shrunk to the EDA prior, lean ~ (m - x).
  PAPER_LANTERNS EWMA span 5 fair value (quote-noise filter: fades one-tick jumps).
  FRUIT_BASKET  2D + 3G + 1M + Kalman random-walk premium, for quoting only.
TELLURIUM and the vouchers are not traded.
"""

import json
import math

from datamodel import Order, TradingState

CONFIG = {
    "pink": True,
    "golden": True,
    "blue": True,
    "toffee": True,
    "lantern_ewma": False,
    "basket_fv": True,
    "pink_kill": True,
    "pink_band_kill": False,
    "inventory_skew": True,
}

LIMITS = {
    "AMETHYST": 50, "TOFFEE_CAKE": 50, "PAPER_LANTERNS": 50, "JELLY": 50, "PEANUT_BUTTER": 50,
    "DRAGONFRUIT": 40, "GRANADILLA": 40, "MANGOSTEEN": 40, "FRUIT_BASKET": 40, "LYCHEE": 200,
    "WHITE_PEARLS": 20, "BLACK_PEARLS": 20, "GOLDEN_PEARLS": 20, "PINK_PEARLS": 20, "BLUE_PEARLS": 20,
}
PEARLS = ("WHITE_PEARLS", "BLACK_PEARLS", "GOLDEN_PEARLS", "PINK_PEARLS", "BLUE_PEARLS")
BASKET_LEGS = {"DRAGONFRUIT": 2, "GRANADILLA": 3, "MANGOSTEEN": 1}

MIN_EDGE = 1.0            # a resting quote must sit at least this far from the reservation price (1 tick)
SKEW_SHARE = 1.0          # k * limit = this many half spreads: at the limit the adding side is fully suppressed
# Avellaneda-Stoikov: the reservation shift is gamma*tau*sigma^2*q. We set it to one half spread at the "soft"
# position soft = SOFT_C * half_spread / sigma^2 (sigma^2 = live EWMA tick variance), clipped to [SOFT_MIN, limit].
SOFT_C = 40.0
SOFT_MIN = 4
VAR_ALPHA = 1.0 / 500.0
VAR_PRIOR = 2.0

# AMETHYST: constant 10,000 (EDA), tracked by a span-200 EWMA (EDA's best span) so an anchor break is followed.
AMETHYST_PRIOR = 10000.0
AMETHYST_ALPHA = 2.0 / 201.0

# PINK_PEARLS plug (EDA page 5 and 20; params hazard edges 0/5/10)
PEARL_TOTAL = 50000.0
HAZ_EDGES = (5.0, 10.0)
HAZ_PRIOR = (0.0004, 0.0097, 0.064)      # per-tick jump probability by |dev| bucket
HAZ_PRIOR_N = 2000.0                       # prior strength in ticks per bucket
SLOPE_PRIOR = -1.10                        # jump = slope * dev, EDA slope -1.10 to -1.12
SLOPE_PRIOR_SXX = 3000.0                   # prior weight, equivalent to ~30 jumps at |dev| 10
SLOPE_FORGET = 0.97                        # per-jump forgetting of the slope RLS
JUMP_DETECT = 3.5                          # PINK mid moves > 3.5 are jumps (quote jitter moves at most ~1-2)
PINK_HORIZON = 20                          # ticks; EDA conditions the 20-tick move
PINK_ENTRY = 1.0                           # enter when E[move] exceeds this many half spreads (the taking cost)
RESTORE_PRIOR = (19.0, 1.0)                # Beta prior on P(jump restores the sum); EDA: 100%
RESTORE_KILL = 0.75                        # kill the plug below this posterior mean hit rate
SUM_BAND = 30.0                            # plan sec. 4: no plug trading while |sum - total| > 30
TOTAL_ALPHA = 0.3                          # post-jump sums re-estimate the total
TOTAL_RESET = 6.0                          # a post-jump sum this far (~4 sd) from the estimate resets it
SLOPE_KILL = 0.3                           # kill if |slope| falls below this (plug no longer restores)

# GOLDEN_PEARLS steps (params: sizes -100/-100/-50 over an 85-tick ramp; absorbed 45%/46% by WHITE/BLACK)
GOLD_PLATEAU_ALPHA = 0.05
CUSUM_K = 1.0                              # 2 x the 0.5 tick noise sd
CUSUM_H = 5.0
RAMP_TICKS = 85
STEP_SIZES = (100.0, 50.0)                 # |size| per params; 100 drawn 2/3 of the time
STEP_PRIORS = (2.0 / 3.0, 1.0 / 3.0)
STEP_SLACK = 5.0
STEP_SPEED_ALPHA = 0.1                     # EWMA of mid changes; noise sd ~0.16 at the 0.7 tick noise
STEP_SPEED_SD = 0.2
STEP_CALM_SPEED = 0.2                      # below a 50-step's 0.59/tick ramp speed by > 2 sd
STEP_SETTLE = 5
MAX_STEP_SPEED = 3.0                       # a step moves ~1.2/tick; faster is a crash, not a step
ABSORB = {"WHITE_PEARLS": 0.447, "BLACK_PEARLS": 0.457}
CRASH_COOLDOWN = 300
ABSORB_CHECK = 10.0                        # GOLDEN move after which WHITE+BLACK must have moved against it

# BLUE_PEARLS trend (params drift 0.0198/tick; EDA +72/+247/+277 per day; momentum corr +0.23)
BLUE_DRIFT_PRIOR = 0.02
BLUE_DRIFT_PRIOR_SD = 0.015
BLUE_TICK_VAR = 2.0                        # tick sigma ~1.41
BLUE_SLOW_ALPHA = 1.0 / 2000.0
BLUE_FAST_ALPHA = 1.0 / 300.0
BLUE_HOLD = 400                            # ticks over which the drift is harvested
BLUE_MOM_BETA = 0.23
BLUE_MOM_ALPHA = 2.0 / 11.0
BLUE_FAST_Z = 1.0                          # one standard error of the fast EWMA mean

# TOFFEE_CAKE OU (params mean 5003.3, kappa 0.0046, sigma 2.24; EDA variance ratio 0.11 at 1,000 ticks)
TOFFEE_MEAN_PRIOR = 5003.3
TOFFEE_ANCHOR_ALPHA = 1.0 / 3000.0
TOFFEE_FAST_ALPHA = 0.5                    # EWMA span 3 (EDA)
TOFFEE_KAPPA_PRIOR = 0.0046
TOFFEE_KAPPA_PRIOR_N = 3000.0
TOFFEE_MOM_ALPHA = 1.0 / 2000.0
TOFFEE_HORIZON = 100
TOFFEE_TARGET_SCALE = 2.0                  # target = limit * alpha / (scale * half spread)

LANTERN_ALPHA = 2.0 / 6.0                  # EWMA span 5 (EDA: 16% lower RMSE than mid)

BASKET_Q = 4.15 ** 2                       # premium random-walk variance per tick (params)
BASKET_R = 3.0                             # basket quote noise 1.14^2 + leg mid noise


def best(depth):
    if not depth.buy_orders or not depth.sell_orders:
        return None
    return max(depth.buy_orders), min(depth.sell_orders)


def clip(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


class Trader:
    def run(self, state: TradingState):
        try:
            mem = json.loads(state.traderData) if state.traderData else {}
        except (ValueError, TypeError):
            mem = {}
        books = {}
        for p in LIMITS:
            d = state.order_depths.get(p)
            b = best(d) if d is not None else None
            if b is not None:
                books[p] = (d, b[0], b[1], (b[0] + b[1]) / 2.0)
        plans = {p: {"fair": books[p][3], "alpha": 0.0, "target": None, "take": False} for p in books}
        self.variances(mem, books, plans)

        self.amethyst(mem, books, plans)
        self.lanterns(mem, books, plans)
        self.toffee(mem, books, plans)
        self.basket(mem, books, plans)
        self.golden(mem, books, plans)
        self.pink(mem, books, plans)
        self.blue(mem, books, plans)

        orders = {}
        for p, plan in plans.items():
            o = self.quote(p, books[p], state.position.get(p, 0), plan)
            if o:
                orders[p] = o
        return orders, 0, json.dumps(mem, separators=(",", ":"))

    # ---------------------------------------------------------------- base quoter
    def quote(self, p, book, pos, plan):
        depth, bid, ask, mid = book
        limit = LIMITS[p]
        half = max((ask - bid) / 2.0, 0.5)
        target = plan["target"]
        soft = clip(SOFT_C * half / max(plan["var"], 1e-3), SOFT_MIN, limit)
        k = SKEW_SHARE * half / soft if CONFIG["inventory_skew"] else 0.0
        if target is None or plan.get("hold"):
            r = plan["fair"] + plan["alpha"] - (0.0 if plan.get("hold") else k * pos)
        else:
            r = plan["fair"] + plan["alpha"] - k * (pos - target)
        buy_cap, sell_cap = limit - pos, limit + pos
        out = []
        if plan["take"]:
            # cross only towards the target, and only where the price still beats r by the exit cost
            want = (target - pos) if target is not None else 0
            if want > 0:
                for price in sorted(depth.sell_orders):
                    if price > r - plan.get("take_edge", half) or want <= 0 or buy_cap <= 0:
                        break
                    q = min(abs(depth.sell_orders[price]), want, buy_cap)
                    out.append(Order(p, price, q))
                    want -= q
                    buy_cap -= q
            elif want < 0:
                for price in sorted(depth.buy_orders, reverse=True):
                    if price < r + plan.get("take_edge", half) or want >= 0 or sell_cap <= 0:
                        break
                    q = min(depth.buy_orders[price], -want, sell_cap)
                    out.append(Order(p, price, -q))
                    want += q
                    sell_cap -= q
        if buy_cap > 0 and r - bid >= MIN_EDGE:
            out.append(Order(p, int(bid), buy_cap))
        if sell_cap > 0 and ask - r >= MIN_EDGE:
            out.append(Order(p, int(ask), -sell_cap))
        return out

    # ---------------------------------------------------------------- fair values
    def variances(self, mem, books, plans):
        """EWMA of squared one-tick mid changes per product (RiskMetrics-style), O(1)."""
        st = mem.get("v", {})
        for p in books:
            mid = books[p][3]
            last, var = st.get(p, (mid, VAR_PRIOR))
            var += VAR_ALPHA * ((mid - last) ** 2 - var)
            st[p] = (mid, round(var, 4))
            plans[p]["var"] = var
        mem["v"] = st

    def amethyst(self, mem, books, plans):
        p = "AMETHYST"
        if p not in books:
            return
        f = mem.get("am", AMETHYST_PRIOR)
        f += AMETHYST_ALPHA * (books[p][3] - f)
        mem["am"] = round(f, 4)
        plans[p]["fair"] = f

    def lanterns(self, mem, books, plans):
        p = "PAPER_LANTERNS"
        if p not in books or not CONFIG["lantern_ewma"]:
            return
        mid = books[p][3]
        f = mem.get("pl", mid)
        f += LANTERN_ALPHA * (mid - f)
        mem["pl"] = round(f, 4)
        plans[p]["fair"] = f

    def basket(self, mem, books, plans):
        p = "FRUIT_BASKET"
        if p not in books or not CONFIG["basket_fv"] or any(leg not in books for leg in BASKET_LEGS):
            return
        synth = sum(w * books[leg][3] for leg, w in BASKET_LEGS.items())
        y = books[p][3] - synth
        st = mem.get("fb")
        if st is None:
            st = [y, BASKET_R]
        prem, var = st[0], st[1] + BASKET_Q
        gain = var / (var + BASKET_R)
        prem += gain * (y - prem)
        var *= 1.0 - gain
        mem["fb"] = [round(prem, 3), round(var, 4)]
        plans[p]["fair"] = synth + prem

    def toffee(self, mem, books, plans):
        p = "TOFFEE_CAKE"
        if p not in books:
            return
        mid = books[p][3]
        st = mem.get("tc")
        if st is None:
            # fast EWMA, anchor, previous fast, E[dev*dx], E[dev^2]
            st = [mid, TOFFEE_MEAN_PRIOR, mid, -TOFFEE_KAPPA_PRIOR * 500.0, 500.0]
        fast, anchor, prev, cxy, cxx = st
        fast += TOFFEE_FAST_ALPHA * (mid - fast)
        dev_prev = prev - anchor
        dx = fast - prev
        cxy += TOFFEE_MOM_ALPHA * (dev_prev * dx - cxy)
        cxx += TOFFEE_MOM_ALPHA * (dev_prev * dev_prev - cxx)
        anchor += TOFFEE_ANCHOR_ALPHA * (fast - anchor)
        mem["tc"] = [round(fast, 3), round(anchor, 3), round(fast, 3), round(cxy, 5), round(cxx, 3)]
        plans[p]["fair"] = fast
        if not CONFIG["toffee"]:
            return
        # kappa: EWMA moment estimate shrunk to the prior (precision ~ effective sample size)
        n_eff = 1.0 / TOFFEE_MOM_ALPHA
        k_hat = -cxy / cxx if cxx > 1e-6 else TOFFEE_KAPPA_PRIOR
        kappa = (TOFFEE_KAPPA_PRIOR_N * TOFFEE_KAPPA_PRIOR + n_eff * k_hat) / (TOFFEE_KAPPA_PRIOR_N + n_eff)
        kappa = clip(kappa, 0.0, 0.05)
        expected = (anchor - fast) * (1.0 - (1.0 - kappa) ** TOFFEE_HORIZON)
        half = (books[p][2] - books[p][1]) / 2.0
        plans[p]["target"] = LIMITS[p] * clip(expected / (TOFFEE_TARGET_SCALE * max(half, 1.0)), -1.0, 1.0)

    # ---------------------------------------------------------------- GOLDEN steps
    def golden(self, mem, books, plans):
        p = "GOLDEN_PEARLS"
        if p not in books:
            return
        mid = books[p][3]
        st = mem.get("gp")
        if st is None:
            # plateau, cusum+, cusum-, mode (0 flat, +-1 step), start level, EWMA speed, calm count, cooldown, last
            st = [mid, 0.0, 0.0, 0, mid, 0.0, 0, 0, mid]
        plateau, gp, gn, mode, start, speed, calm, cool, last = st[:9]
        st_wb = st[9] if len(st) > 9 else 0.0
        wb = sum(books[q][3] for q in ABSORB if q in books)
        cool = max(cool - 1, 0)
        dx = mid - last
        speed += STEP_SPEED_ALPHA * (dx - speed)
        if abs(dx) > MAX_STEP_SPEED * 4:
            cool = CRASH_COOLDOWN  # a crash or flash move, not a step ramp
        if mode == 0:
            e = mid - plateau
            gp = max(0.0, gp + e - CUSUM_K)
            gn = max(0.0, gn - e - CUSUM_K)
            if gp > CUSUM_H or gn > CUSUM_H:
                mode, start, calm, gp, gn = (1 if gp > CUSUM_H else -1), plateau, 0, 0.0, 0.0
                st_wb = wb
            else:
                plateau += GOLD_PLATEAU_ALPHA * (mid - plateau)
        else:
            calm = calm + 1 if abs(speed) < STEP_CALM_SPEED else 0
            # a real step is absorbed by WHITE + BLACK moving the other way (~0.9x); a market-wide shock moves
            # them the same way
            moved_g, moved_wb = mid - start, wb - st_wb
            if abs(moved_g) > ABSORB_CHECK and moved_g * moved_wb > 0:
                cool, mode, plateau = CRASH_COOLDOWN, 0, mid
            if calm >= STEP_SETTLE or abs(mid - start) > 1.3 * max(STEP_SIZES):
                mode, plateau, gp, gn = 0, mid, 0.0, 0.0
        plans[p]["fair"] = plateau if mode == 0 else mid
        mem["gp"] = [round(plateau, 3), round(gp, 3), round(gn, 3), mode, round(start, 2), round(speed, 4), calm,
                     cool, mid, round(st_wb, 2)]
        if not CONFIG["golden"] or mode == 0 or cool > 0:
            return
        remaining = mode * self.step_remaining(abs(mid - start), abs(speed))
        if remaining == 0.0:
            return
        half = (books[p][2] - books[p][1]) / 2.0
        if abs(remaining) > 2.0 * half + 1.0:
            plans[p].update(alpha=remaining, target=mode * LIMITS[p], take=True, take_edge=half)
        for q, share in ABSORB.items():
            if q not in books:
                continue
            rem_q = -share * remaining
            hq = (books[q][2] - books[q][1]) / 2.0
            if abs(rem_q) > 2.0 * hq + 1.0:
                sign = 1 if rem_q > 0 else -1
                plans[q].update(alpha=rem_q, target=sign * LIMITS[q], take=True, take_edge=hq)

    @staticmethod
    def step_remaining(moved, speed):
        """E[remaining step size | distance moved, ramp speed]: a posterior over the step sizes, whose ramp speed is
        size / RAMP_TICKS, with a Gaussian likelihood on the EWMA speed."""
        num = den = 0.0
        for size, prior in zip(STEP_SIZES, STEP_PRIORS):
            if size + STEP_SLACK < moved:
                continue
            like = prior * math.exp(-0.5 * ((speed - size / RAMP_TICKS) / STEP_SPEED_SD) ** 2)
            num += like * max(size - moved, 0.0)
            den += like
        return num / den if den > 0 else 0.0

    # ---------------------------------------------------------------- PINK plug
    def pink(self, mem, books, plans):
        p = "PINK_PEARLS"
        if any(q not in books for q in PEARLS):
            return
        total_sum = sum(books[q][3] for q in PEARLS)
        pink_mid = books[p][3]
        st = mem.get("pk")
        if st is None:
            st = {"tot": PEARL_TOTAL, "dev": None, "mid": pink_mid,
                  "h": [[HAZ_PRIOR[i] * HAZ_PRIOR_N, HAZ_PRIOR_N] for i in range(3)],
                  "sxy": SLOPE_PRIOR * SLOPE_PRIOR_SXX, "sxx": SLOPE_PRIOR_SXX,
                  "ra": RESTORE_PRIOR[0], "rb": RESTORE_PRIOR[1]}
        dev_prev = st["dev"]
        jump = pink_mid - st["mid"]
        if dev_prev is not None:
            bucket = 0 if abs(dev_prev) < HAZ_EDGES[0] else 1 if abs(dev_prev) < HAZ_EDGES[1] else 2
            is_jump = abs(jump) > JUMP_DETECT
            h = st["h"][bucket]
            h[0] = h[0] + (1.0 if is_jump else 0.0)
            h[1] = h[1] + 1.0
            if h[1] > 2.0 * HAZ_PRIOR_N:  # keep the posterior adaptive: cap its effective size
                h[0] *= 2.0 * HAZ_PRIOR_N / h[1]
                h[1] = 2.0 * HAZ_PRIOR_N
            if is_jump:
                if abs(dev_prev) < SUM_BAND:
                    st["sxy"] = SLOPE_FORGET * st["sxy"] + dev_prev * jump
                    st["sxx"] = SLOPE_FORGET * st["sxx"] + dev_prev * dev_prev
                    if abs(dev_prev) > HAZ_EDGES[0]:
                        if jump * dev_prev < 0:
                            st["ra"] += 1.0
                        else:
                            st["rb"] += 1.0
                # the sum right after a jump is a fresh reading of the conserved total
                miss = total_sum - st["tot"]
                st["tot"] = total_sum if abs(miss) > TOTAL_RESET else st["tot"] + TOTAL_ALPHA * miss
        dev = total_sum - st["tot"]
        st["dev"] = round(dev, 3)
        st["mid"] = pink_mid
        st["h"] = [[round(a, 4), round(b, 2)] for a, b in st["h"]]
        st["sxy"], st["sxx"] = round(st["sxy"], 3), round(st["sxx"], 3)
        mem["pk"] = st
        if not CONFIG["pink"] or p not in plans:
            return
        slope = st["sxy"] / st["sxx"]
        hit = st["ra"] / (st["ra"] + st["rb"])
        if CONFIG["pink_kill"] and (hit < RESTORE_KILL or abs(slope) < SLOPE_KILL):
            return
        if CONFIG["pink_band_kill"] and abs(dev) > SUM_BAND:
            return
        bucket = 0 if abs(dev) < HAZ_EDGES[0] else 1 if abs(dev) < HAZ_EDGES[1] else 2
        hz = st["h"][bucket][0] / st["h"][bucket][1]
        expected = (1.0 - (1.0 - hz) ** PINK_HORIZON) * slope * dev
        half = (books[p][2] - books[p][1]) / 2.0
        plan = plans[p]
        plan["alpha"] = expected
        if abs(expected) > PINK_ENTRY * half:
            plan.update(target=LIMITS[p] if expected > 0 else -LIMITS[p], take=True, take_edge=0.0)
        else:
            # hold whatever we carry between signals: PINK is flat between jumps, so holding is free
            plan["target"] = 0.0
            plan["hold"] = True

    # ---------------------------------------------------------------- BLUE trend
    def blue(self, mem, books, plans):
        p = "BLUE_PEARLS"
        if p not in books:
            return
        mid = books[p][3]
        st = mem.get("bl")
        if st is None:
            st = [mid, BLUE_DRIFT_PRIOR, BLUE_DRIFT_PRIOR, 0.0]
        last, slow, fast, mom = st
        dx = mid - last
        slow += BLUE_SLOW_ALPHA * (dx - slow)
        fast += BLUE_FAST_ALPHA * (dx - fast)
        mom += BLUE_MOM_ALPHA * (dx - mom)
        mem["bl"] = [mid, round(slow, 6), round(fast, 6), round(mom, 5)]
        if not CONFIG["blue"]:
            return
        # Bayesian drift: prior N(0.02, 0.015^2), data = slow EWMA mean with n_eff = 2/alpha observations
        n_eff = 2.0 / BLUE_SLOW_ALPHA
        prec_prior = 1.0 / BLUE_DRIFT_PRIOR_SD ** 2
        prec_data = n_eff / BLUE_TICK_VAR
        drift = (prec_prior * BLUE_DRIFT_PRIOR + prec_data * slow) / (prec_prior + prec_data)
        fast_z = fast / math.sqrt(BLUE_TICK_VAR * BLUE_FAST_ALPHA / 2.0)
        if drift * fast_z < 0 and abs(fast_z) > BLUE_FAST_Z:
            drift = 0.0  # guard: the recent trend contradicts the drift estimate (momentum crash, regime flip)
        momentum = BLUE_MOM_BETA * mom * 10.0
        half = (books[p][2] - books[p][1]) / 2.0
        plans[p]["alpha"] = momentum
        plans[p]["target"] = LIMITS[p] * clip(drift * BLUE_HOLD / max(half, 1.0), -1.0, 1.0)


# ---- variant overrides
PINK_HORIZON = 40
