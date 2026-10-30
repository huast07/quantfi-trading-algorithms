"""S3: LYCHEE voucher volatility relative value, delta-hedged with LYCHEE.

Shared estimator:
  SmileModel   Newton IV inversion (warm-started), closed-form WLS smile IV = a + b*m + c*m^2 with
               m = ln(K/S)/sqrt(T), EWMA-smoothed shape (b, c), per-strike AR(1) residual statistics.
Sub-strategies (each exposes intent / edge / variance and keeps its state in its own `mem` dict):
  VoucherRV    one per strike: trade the AR(1) residual on the IV-rule takers' side via a linear
               reservation curve (Avellaneda & Stoikov 2008), resting only on the side the takers do not hit.
  VegaTilt     net short vega for the variance risk premium (Carr & Wu 2009), with a kill switch at IV ~ RV.
  DeltaHedger  hedges the book delta with LYCHEE inside a Whalley-Wilmott no-trade band.
  LycheeMaker  passive LYCHEE quotes at the touch, leaning toward the hedge target.
Trader.run is a thin shell: it runs the sub-strategies, clips every product to its limit and stores the book's
net delta in traderData ("bd") for an orchestrator.
"""

import json
import math

import numpy as np

from datamodel import Order, OrderDepth, TradingState  # noqa: F401  (OrderDepth/TradingState: contract types)

UNDERLYING = "LYCHEE"
STRIKES = (6800, 7000, 7200, 7300, 7400, 7500, 7600, 7750, 7900, 8100)
VOUCHERS = tuple(f"VOUCHER_{k}" for k in STRIKES)
STRIKE_ARRAY = np.array(STRIKES, dtype=float)
N_STRIKES = len(STRIKES)
VOUCHER_LIMIT = 50
UNDERLYING_LIMIT = 200

# Time to expiry: the generator assumes 5 days at the day-1 open, one day per 1,000,000 timestamps.
# A wrong T rescales the fitted IVs but leaves price-space residuals and deltas nearly unchanged.
DAYS_TO_EXPIRY_AT_OPEN = 5.0
TIMESTAMPS_PER_DAY = 1_000_000
MIN_DAYS_TO_EXPIRY = 0.25
TICKS_PER_DAY = 10_000

# Priors from params.json / EDA: residual sd per strike (price units), AR(1) phi, ATM IV per sqrt-day.
PRIOR_RESIDUAL_SD = np.array([2.23, 3.60, 4.75, 5.33, 5.10, 5.12, 4.94, 4.11, 3.36, 2.13])
PRIOR_PHI = 0.993
PRIOR_IV = 0.020
PRIOR_LYCHEE_TICK_VAR = 1.35**2  # EDA tick sigma ~1.35
IV_FACTOR_SD = 0.0015  # params.json factor_sd: sd of the shared IV level, per sqrt-day
ROUNDING_VAR = 1.0 / 12.0  # integer quotes: mid error ~ U(-0.5, 0.5)
IV_MIN, IV_MAX = 0.002, 0.2
NEWTON_STEPS = 3
MIN_VEGA = 1.0
MIN_FIT_STRIKES = 4

# Estimator spans (ticks).
SHAPE_SPAN = 1000  # smile shape b, c: constant in the generator, so smooth heavily
RESIDUAL_VAR_SPAN = 3000  # ~30 residual half-lives (ln2 / (1 - 0.993) ~ 100 ticks)
LYCHEE_VAR_SPAN = 500
RV_SAMPLE_TICKS = 10  # realised variance from 10-tick returns (LYCHEE ACF(1) ~ -0.10 biases 1-tick RV)
RV_SPAN = 300  # in samples, i.e. 3,000 ticks
MARKOUT_SPAN = 200  # fills, for the LYCHEE maker's edge estimate
PHI_BOUNDS = (0.95, 0.9995)
OUTLIER_CAP = 25.0  # winsorise squared moves at 25 x the current variance (5 sigma)

# VoucherRV.
HOLD_HORIZON = 120  # ticks: rho = phi^H is the residual share still expected at the horizon
RISK_AVERSION = 0.35  # reservation price falls by RISK_AVERSION * residual sd at a full long position
TAKE_EDGE = 1.5  # minimum value minus price to take a level
PASSIVE_EDGE = 0.0
PASSIVE_MAX = 10
DELTA_SOFT = 170.0  # net voucher delta the LYCHEE limit can still absorb
DELTA_PENALTY = 0.05  # price per unit delta beyond DELTA_SOFT, times own delta

# VegaTilt: value options below the smile by the expected delta-hedged bleed
# 0.5 * Gamma * S^2 * (IV^2 - RV^2) per day over VRP_HORIZON_DAYS.
VRP_HORIZON_DAYS = 0.0
VRP_KILL_RATIO = 1.10  # no tilt once IV / RV falls below this (vol-crush case)

# DeltaHedger and LycheeMaker.
HEDGE_BAND = 50.0  # Whalley-Wilmott style no-trade band, in LYCHEE units of delta
SMILE_DELTA_WEIGHT = 0.0  # 1 = sticky-delta smile adjustment to BS delta, 0 = plain BS delta
MAKE_SIZE = 10
MAKE_SKEW = 0.5

# Jump / gap guard.
JUMP_Z = 6.0
COOLDOWN_TICKS = 50


# ---- maths ----------------------------------------------------------------------------------------------------


def norm_pdf(x):
    return np.exp(-0.5 * x * x) * 0.3989422804014327


def norm_cdf(x):
    """Exact normal CDF via math.erf; a list comprehension beats numpy's overhead on 10 strikes."""
    return np.array([0.5 * (1.0 + math.erf(v * 0.7071067811865476)) for v in np.asarray(x).tolist()])


def bs_call(spot, strikes, days, vol):
    """Price, delta, vega (per unit vol per sqrt-day) and d1."""
    root_t = math.sqrt(days)
    st = vol * root_t
    d1 = (np.log(spot / strikes) + 0.5 * st * st) / st
    nd1 = norm_cdf(d1)
    price = spot * nd1 - strikes * norm_cdf(d1 - st)
    vega = spot * root_t * norm_pdf(d1)
    return price, nd1, vega, d1


def implied_vol(prices, spot, strikes, days, guess):
    vol = np.clip(guess, IV_MIN, IV_MAX)
    for _ in range(NEWTON_STEPS):
        model, _, vega, _ = bs_call(spot, strikes, days, vol)
        vol = np.clip(vol - (model - prices) / np.maximum(vega, MIN_VEGA), IV_MIN, IV_MAX)
    model, _, vega, _ = bs_call(spot, strikes, days, vol)
    valid = (np.abs(model - prices) < 0.5) & (vega > MIN_VEGA) & (prices > np.maximum(spot - strikes, 0.0))
    return vol, valid


def wls_quadratic(m, y, w):
    """Closed-form weighted least squares for y = a + b*m + c*m^2."""
    x = np.stack([np.ones_like(m), m, m * m], axis=1)
    xtw = x.T * w
    gram = xtw @ x
    if abs(np.linalg.det(gram)) < 1e-18:
        return None
    return np.linalg.solve(gram, xtw @ y)


def ewma(old, new, span):
    return old + 2.0 / (span + 1.0) * (new - old)


def best_prices(depth):
    if depth is None or not depth.buy_orders or not depth.sell_orders:
        return None
    return max(depth.buy_orders), min(depth.sell_orders)


def mid_price(depth):
    quote = best_prices(depth)
    return None if quote is None else 0.5 * (quote[0] + quote[1])


def take_levels(depth, side, quantity):
    """(price, signed qty) taking up to `quantity` from the book; side +1 buys asks, -1 sells bids."""
    out = []
    levels = sorted(depth.sell_orders) if side > 0 else sorted(depth.buy_orders, reverse=True)
    book = depth.sell_orders if side > 0 else depth.buy_orders
    for price in levels:
        if quantity <= 0:
            break
        qty = min(abs(book[price]), quantity)
        out.append((price, side * qty))
        quantity -= qty
    return out


# ---- shared estimator -----------------------------------------------------------------------------------------


class UnderlyingModel:
    """LYCHEE tick variance (jump guard), 10-tick realised variance (VRP) and the gap/jump cooldown."""

    @staticmethod
    def update(mem, spot):
        var = mem.get("sv", PRIOR_LYCHEE_TICK_VAR)
        cooldown = max(mem.get("cd", 0) - 1, 0)
        last = mem.get("S")
        if last is not None:
            move = spot - last
            if move * move > JUMP_Z * JUMP_Z * var:
                cooldown = COOLDOWN_TICKS
            var = ewma(var, min(move * move, OUTLIER_CAP * var), LYCHEE_VAR_SPAN)
        rv = mem.get("rv", PRIOR_LYCHEE_TICK_VAR * RV_SAMPLE_TICKS)
        sample_spot, since = mem.get("S10", spot), mem.get("n10", 0) + 1
        if since >= RV_SAMPLE_TICKS:
            move = spot - sample_spot
            rv = ewma(rv, min(move * move, OUTLIER_CAP * rv), RV_SPAN)
            sample_spot, since = spot, 0
        return {"S": spot, "sv": var, "cd": cooldown, "S10": sample_spot, "rv": rv, "n10": since}

    @staticmethod
    def realised_vol_per_day(mem, spot):
        return math.sqrt(mem["rv"] / RV_SAMPLE_TICKS * TICKS_PER_DAY) / spot


class SmileModel:
    """Fits the smile and tracks each strike's residual: r = mid - BS(S, K, T, smile IV)."""

    @staticmethod
    def update(state, mem, spot, days):
        quotes = [best_prices(state.order_depths.get(p)) for p in VOUCHERS]
        mids = np.array([np.nan if q is None else 0.5 * (q[0] + q[1]) for q in quotes])
        present = ~np.isnan(mids)
        if present.sum() < MIN_FIT_STRIKES:
            return None, mem
        guess = np.array(mem.get("iv", [PRIOR_IV] * N_STRIKES), dtype=float)
        iv, valid = implied_vol(np.where(present, mids, 1.0), spot, STRIKE_ARRAY, days, guess)
        valid &= present
        if valid.sum() < MIN_FIT_STRIKES:
            return None, mem
        _, _, vega, _ = bs_call(spot, STRIKE_ARRAY, days, iv)
        resid_var = np.array(mem.get("rv2", (PRIOR_RESIDUAL_SD**2).tolist()), dtype=float)
        weights = np.where(valid, vega * vega / (resid_var + ROUNDING_VAR), 0.0)
        moneyness = np.log(STRIKE_ARRAY / spot) / math.sqrt(days)
        beta = wls_quadratic(moneyness, iv, weights)
        if beta is None:
            return None, mem
        shape_b = ewma(mem.get("b", beta[1]), beta[1], SHAPE_SPAN)
        shape_c = ewma(mem.get("c", beta[2]), beta[2], SHAPE_SPAN)
        level = float(np.sum(weights * (iv - shape_b * moneyness - shape_c * moneyness**2)) / np.sum(weights))
        fitted_iv = np.clip(level + shape_b * moneyness + shape_c * moneyness**2, IV_MIN, IV_MAX)
        fair, delta, fit_vega, d1 = bs_call(spot, STRIKE_ARRAY, days, fitted_iv)
        # Sticky-delta smile: dIV/dS = -(b + 2cm) / (S sqrt T), so delta gains vega * dIV/dS.
        delta = delta - SMILE_DELTA_WEIGHT * norm_pdf(d1) * (shape_b + 2.0 * shape_c * moneyness)
        residual = np.where(present, mids - fair, 0.0)

        prev_r = np.array(mem.get("r", residual.tolist()), dtype=float)
        lag_cov = np.array(mem.get("lc", (PRIOR_PHI * PRIOR_RESIDUAL_SD**2).tolist()), dtype=float)
        lag_var = np.array(mem.get("lv", (PRIOR_RESIDUAL_SD**2).tolist()), dtype=float)
        both = valid & np.array(mem.get("ok", [True] * N_STRIKES), dtype=bool)
        alpha = 2.0 / (RESIDUAL_VAR_SPAN + 1.0)
        resid_var = np.where(valid, resid_var + alpha * (residual * residual - resid_var), resid_var)
        lag_cov = np.where(both, lag_cov + alpha * (residual * prev_r - lag_cov), lag_cov)
        lag_var = np.where(both, lag_var + alpha * (prev_r * prev_r - lag_var), lag_var)

        new_mem = {
            "iv": np.round(np.where(valid, iv, guess), 6).tolist(),
            "rv2": np.round(resid_var, 4).tolist(),
            "lc": np.round(lag_cov, 4).tolist(),
            "lv": np.round(lag_var, 4).tolist(),
            "r": np.round(residual, 3).tolist(),
            "ok": valid.tolist(),
            "b": shape_b,
            "c": shape_c,
        }
        surface = {
            "quotes": quotes,
            "mids": mids,
            "valid": valid,
            "fair": fair,
            "residual": residual,
            "sd": np.sqrt(resid_var),
            "phi": np.clip(lag_cov / np.maximum(lag_var, 1e-9), *PHI_BOUNDS),
            "delta": delta,
            "vega": fit_vega,
            "gamma": norm_pdf(d1) / (spot * fitted_iv * math.sqrt(days)),
            "level": level,
            "spot": spot,
        }
        return surface, new_mem


# ---- sub-strategies -------------------------------------------------------------------------------------------


class VegaTilt:
    """Variance risk premium: expected delta-hedged bleed per lot of a short option over the horizon."""

    def __init__(self):
        self.shift = np.zeros(N_STRIKES)
        self.sd = np.ones(N_STRIKES)

    def update(self, surface, underlying_mem):
        self.sd = surface["vega"] * IV_FACTOR_SD
        if VRP_HORIZON_DAYS <= 0:
            self.shift = np.zeros(N_STRIKES)
            return self.shift
        spot = surface["spot"]
        rv_day = UnderlyingModel.realised_vol_per_day(underlying_mem, spot)
        iv_atm = surface["level"]
        if rv_day <= 0 or iv_atm / rv_day < VRP_KILL_RATIO:
            self.shift = np.zeros(N_STRIKES)
            return self.shift
        bleed = 0.5 * surface["gamma"] * spot * spot * (iv_atm * iv_atm - rv_day * rv_day)
        self.shift = bleed * VRP_HORIZON_DAYS
        return self.shift

    def intent(self, state, product, mem):
        """Target short position per strike, Kelly-style edge / variance, as if alone on the limit."""
        i = VOUCHERS.index(product)
        target = -VOUCHER_LIMIT * min(1.0, self.shift[i] / max(RISK_AVERSION * self.sd[i], 1e-9))
        return int(round(target))

    def edge(self, product):
        return float(self.shift[VOUCHERS.index(product)])

    def variance(self, product):
        return float(self.sd[VOUCHERS.index(product)] ** 2)


class VoucherRV:
    """One strike's residual trade.

    Value over the horizon: v = F + rho * r - tilt - delta penalty, with F the smile price and rho = phi^H.
    The reservation price falls linearly with inventory, v(q) = v - slope * q, slope = RISK_AVERSION * sd / limit,
    so the target position at price p is (v - TAKE_EDGE - p) / slope for buys and (v + TAKE_EDGE - p) / slope
    for sells. Rest bids only when the strike is cheap (r < 0) and asks only when it is rich: the IV-rule takers
    lift asks of cheap strikes and hit bids of rich ones.
    """

    def __init__(self, index):
        self.index = index
        self.product = VOUCHERS[index]
        self._edge = 0.0
        self._variance = PRIOR_RESIDUAL_SD[index] ** 2
        self.value = None
        self.slope = None
        self.residual = 0.0

    def prepare(self, surface, value):
        i = self.index
        self.value = float(value[i])
        self.slope = RISK_AVERSION * float(surface["sd"][i]) / VOUCHER_LIMIT
        self.residual = float(surface["residual"][i])
        rho = float(surface["phi"][i]) ** HOLD_HORIZON
        quote = surface["quotes"][i]
        half_spread = 0.5 * (quote[1] - quote[0]) if quote else 0.0
        self._edge = abs(self.residual) * (1.0 - rho) - half_spread
        self._variance = float(surface["sd"][i]) ** 2 * (1.0 - rho * rho)

    def intent(self, state, product, mem, position=None, cooling=False):
        """(price, signed qty) orders for the whole limit given position q; also returns the taken quantity."""
        depth = state.order_depths[product]
        q = state.position.get(product, 0) if position is None else position
        planned = q
        out = []
        for price in sorted(depth.sell_orders):
            target = math.floor((self.value - TAKE_EDGE - price) / self.slope)
            if cooling:
                target = min(target, 0) if planned < 0 else planned  # only reduce a short
            qty = min(abs(depth.sell_orders[price]), target - planned, VOUCHER_LIMIT - planned)
            if qty <= 0:
                break
            out.append((price, qty))
            planned += qty
        for price in sorted(depth.buy_orders, reverse=True):
            target = math.ceil((self.value + TAKE_EDGE - price) / self.slope)
            if cooling:
                target = max(target, 0) if planned > 0 else planned  # only reduce a long
            qty = min(depth.buy_orders[price], planned - target, VOUCHER_LIMIT + planned)
            if qty <= 0:
                break
            out.append((price, -qty))
            planned -= qty
        taken = planned - q
        if cooling:
            return out, taken
        best_bid, best_ask = max(depth.buy_orders), min(depth.sell_orders)
        if self.residual < 0 and best_bid < best_ask:
            target = math.floor((self.value - PASSIVE_EDGE - best_bid) / self.slope)
            qty = min(target - planned, PASSIVE_MAX)
            if qty > 0:
                out.append((best_bid, qty))
        elif self.residual > 0 and best_bid < best_ask:
            target = math.ceil((self.value + PASSIVE_EDGE - best_ask) / self.slope)
            qty = min(planned - target, PASSIVE_MAX)
            if qty > 0:
                out.append((best_ask, -qty))
        return out, taken

    def edge(self):
        """Expected residual reversion over the horizon minus the half spread, per lot."""
        return self._edge

    def variance(self):
        """Residual variance not yet reverted at the horizon, per lot (delta-hedged)."""
        return self._variance


class DeltaHedger:
    """Trade LYCHEE back to the edge of a +/-HEDGE_BAND band around -book delta (Whalley & Wilmott 1997)."""

    def __init__(self):
        self.target = 0.0

    def intent(self, state, product, mem, voucher_delta):
        depth = state.order_depths[product]
        q = state.position.get(product, 0)
        self.target = max(-UNDERLYING_LIMIT, min(UNDERLYING_LIMIT, -voucher_delta))
        gap = self.target - q
        if abs(gap) <= HEDGE_BAND:
            return []
        side = 1 if gap > 0 else -1
        return take_levels(depth, side, int(math.floor(abs(gap) - HEDGE_BAND)))

    def edge(self, depth):
        quote = best_prices(depth)
        return -0.5 * (quote[1] - quote[0]) if quote else 0.0  # hedging pays the half spread

    def variance(self, mem):
        return mem.get("sv", PRIOR_LYCHEE_TICK_VAR)


class LycheeMaker:
    """Passive LYCHEE quotes at the touch (a passive fill at the touch beats one behind it in this engine)."""

    def intent(self, state, product, mem, hedge_target, position_after_hedge):
        if mem.get("cd", 0) > 0:
            return []
        quote = best_prices(state.order_depths[product])
        if quote is None:
            return []
        lean = MAKE_SKEW * (hedge_target - position_after_hedge)
        bid_qty = int(max(MAKE_SIZE + lean, 0))
        ask_qty = int(max(MAKE_SIZE - lean, 0))
        out = []
        if bid_qty > 0:
            out.append((quote[0], bid_qty))
        if ask_qty > 0:
            out.append((quote[1], -ask_qty))
        return out

    @staticmethod
    def update_markout(state, mem, mid):
        """EWMA of the 1-tick markout per lot of our LYCHEE fills: the maker's live edge estimate."""
        markout = mem.get("mk", 0.0)
        for trade in state.own_trades.get(UNDERLYING, []) if state.own_trades else []:
            sign = 1 if trade.buyer == "SUBMISSION" else -1
            for _ in range(min(int(trade.quantity), 5)):
                markout = ewma(markout, sign * (mid - trade.price), MARKOUT_SPAN)
        return markout

    def edge(self, mem):
        return mem.get("mk", 0.0)

    def variance(self, mem):
        return mem.get("sv", PRIOR_LYCHEE_TICK_VAR)


# ---- shell ----------------------------------------------------------------------------------------------------


def clip_to_limit(product, intents, position, limit):
    """Orders whose buys and sells each fit inside the limit on their own, as the engine requires."""
    buy_room, sell_room = limit - position, limit + position
    out = []
    for price, qty in intents:
        if qty > 0:
            qty = min(qty, buy_room)
            buy_room -= max(qty, 0)
        else:
            qty = -min(-qty, sell_room)
            sell_room -= max(-qty, 0)
        if qty != 0:
            out.append(Order(product, int(price), int(qty)))
    return out


class Trader:
    def __init__(self):
        self.rv = [VoucherRV(i) for i in range(N_STRIKES)]
        self.tilt = VegaTilt()
        self.hedger = DeltaHedger()
        self.maker = LycheeMaker()
        self.book_delta = 0.0

    def run(self, state: TradingState):
        orders = {}
        try:
            mem = json.loads(state.traderData) if state.traderData else {}
        except (ValueError, TypeError):
            mem = {}
        try:
            mem = self._step(state, mem, orders)
        except Exception as error:  # never raise into the engine; log and trade nothing this tick
            print(f"S3 error: {error!r}")
            orders = {}
        return orders, 0, json.dumps(mem, separators=(",", ":"))

    def _step(self, state, mem, orders):
        depth = state.order_depths.get(UNDERLYING)
        spot = mid_price(depth)
        if spot is None:
            return mem
        und = UnderlyingModel.update(mem.get("u", {}), spot)
        und["mk"] = LycheeMaker.update_markout(state, mem.get("u", {}), spot)
        days = max(DAYS_TO_EXPIRY_AT_OPEN - state.timestamp / TIMESTAMPS_PER_DAY, MIN_DAYS_TO_EXPIRY)
        surface, smile_mem = SmileModel.update(state, mem.get("s", {}), spot, days)
        if surface is None:  # keep the last hedge target rather than unhedging
            voucher_delta = mem.get("vd", 0.0)
        else:
            voucher_delta = self._vouchers(state, surface, und, orders)
        position = state.position.get(UNDERLYING, 0)
        hedge = self.hedger.intent(state, UNDERLYING, und, voucher_delta)
        after_hedge = position + sum(q for _, q in hedge)
        make = self.maker.intent(state, UNDERLYING, und, self.hedger.target, after_hedge)
        lychee = clip_to_limit(UNDERLYING, hedge + make, position, UNDERLYING_LIMIT)
        if lychee:
            orders[UNDERLYING] = lychee
        self.book_delta = voucher_delta + after_hedge
        return {"u": und, "s": smile_mem, "vd": round(voucher_delta, 2), "bd": round(self.book_delta, 2)}

    def _vouchers(self, state, surface, und, orders):
        positions = np.array([state.position.get(p, 0) for p in VOUCHERS], dtype=float)
        net_delta = float(np.sum(positions * surface["delta"]))
        excess_delta = math.copysign(max(abs(net_delta) - DELTA_SOFT, 0.0), net_delta)
        rho = surface["phi"] ** HOLD_HORIZON
        value = (
            surface["fair"]
            + rho * surface["residual"]
            - self.tilt.update(surface, und)
            - DELTA_PENALTY * excess_delta * surface["delta"]
        )
        cooling = und.get("cd", 0) > 0
        expected_delta = 0.0
        for strategy in self.rv:
            i, product = strategy.index, strategy.product
            position = int(positions[i])
            if not surface["valid"][i] or surface["quotes"][i] is None:
                expected_delta += position * surface["delta"][i]
                continue
            strategy.prepare(surface, value)
            intents, taken = strategy.intent(state, product, None, position, cooling)
            clipped = clip_to_limit(product, intents, position, VOUCHER_LIMIT)
            if clipped:
                orders[product] = clipped
            expected_delta += (position + taken) * surface["delta"][i]
        return expected_delta
