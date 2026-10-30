"""S3: LYCHEE voucher volatility relative value, delta-hedged with LYCHEE.

Each tick:
1. Invert Black-Scholes IV for the ten vouchers (Newton, warm-started from the last tick).
2. Fit the smile IV = a + b*m + c*m^2, m = ln(K/S)/sqrt(T), by closed-form weighted least squares; the shape
   (b, c) is smoothed by an EWMA, the level a is refit every tick.
3. Each strike's residual r = mid - BS(smile IV) is an AR(1) mispricing (phi ~0.993). Its value over a holding
   horizon is F + rho*r, F = smile price, rho = phi^H. A linear reservation curve (Avellaneda-Stoikov style)
   turns that value and the inventory into a target position for every price level.
4. Take levels priced through the reservation curve; rest only on the side the IV-rule takers do not hit.
5. Hedge the net voucher delta with LYCHEE inside a Whalley-Wilmott band, and make LYCHEE passively.
"""

import json
import math

import numpy as np

from datamodel import Order, OrderDepth, TradingState

UNDERLYING = "LYCHEE"
STRIKES = (6800, 7000, 7200, 7300, 7400, 7500, 7600, 7750, 7900, 8100)
VOUCHERS = tuple(f"VOUCHER_{k}" for k in STRIKES)
STRIKE_ARRAY = np.array(STRIKES, dtype=float)
N_STRIKES = len(STRIKES)
VOUCHER_LIMIT = 50
UNDERLYING_LIMIT = 200

# Time to expiry: the generator assumes 5 days at the day-1 open, one day per 1,000,000 timestamps.
# A wrong T rescales the fitted IVs but leaves residuals (price space) and deltas nearly unchanged.
DAYS_TO_EXPIRY_AT_OPEN = 5.0
TIMESTAMPS_PER_DAY = 1_000_000
MIN_DAYS_TO_EXPIRY = 0.25
TICKS_PER_DAY = 10_000

# Priors from params.json / EDA (residual sd per strike in price units, AR(1) phi, ATM IV per sqrt-day).
PRIOR_RESIDUAL_SD = np.array([2.23, 3.60, 4.75, 5.33, 5.10, 5.12, 4.94, 4.11, 3.36, 2.13])
PRIOR_PHI = 0.993
PRIOR_IV = 0.020
PRIOR_LYCHEE_TICK_VAR = 1.35**2  # EDA tick sigma ~1.35
ROUNDING_VAR = 1.0 / 12.0  # integer quotes: mid error ~ U(-0.5, 0.5)
IV_MIN, IV_MAX = 0.002, 0.2
NEWTON_STEPS = 3
MIN_VEGA = 1.0

# Estimator spans (ticks).
SHAPE_SPAN = 500  # smile shape b, c: constant in the generator, so smooth heavily
RESIDUAL_VAR_SPAN = 3000  # ~30 residual half-lives (ln2 / (1 - 0.993) ~ 100 ticks)
LYCHEE_VAR_SPAN = 500
RV_SAMPLE_TICKS = 10  # realised variance from 10-tick returns (LYCHEE ACF(1) ~ -0.10 biases 1-tick RV)
RV_SPAN = 300  # in samples, i.e. 3,000 ticks
PHI_BOUNDS = (0.95, 0.9995)

# Trading rule.
HOLD_HORIZON = 100  # ticks: rho = phi^H is the residual share still expected at the horizon
RISK_AVERSION = 1.0  # reservation price falls by RISK_AVERSION * residual sd at a full long position
TAKE_EDGE = 0.5  # minimum value minus price to take a level
PASSIVE_EDGE = 0.0
PASSIVE_MAX = 10
VEGA_PENALTY = 0.0  # price per unit of (net vega * own vega), portfolio vega aversion
NET_VEGA_SOFT = 3.0e5  # beyond this the vega penalty applies (about 45 ATM vouchers)

# Variance risk premium tilt (Carr & Wu 2009): value options below the smile by the expected
# delta-hedged bleed 0.5 * Gamma * S^2 * (IV^2 - RV^2) over VRP_HORIZON_DAYS.
VRP_HORIZON_DAYS = 0.0
VRP_KILL_RATIO = 1.10  # no tilt once IV / RV falls below this (vol-crush case)

# Hedge and LYCHEE making.
HEDGE_BAND = 15.0  # Whalley-Wilmott style no-trade band, in LYCHEE units of delta
DELTA_SOFT = 170.0  # net voucher delta the LYCHEE limit can still absorb
DELTA_PENALTY = 0.05  # price per unit delta beyond DELTA_SOFT, times own delta
SMILE_DELTA_WEIGHT = 1.0  # 1 = sticky-delta smile adjustment to BS delta, 0 = plain BS delta
MAKE_SIZE = 10
MAKE_SKEW = 0.5

# Jump / gap guard.
JUMP_Z = 6.0
COOLDOWN_TICKS = 50


def norm_pdf(x):
    return np.exp(-0.5 * x * x) * 0.3989422804014327


def norm_cdf(x):
    """Abramowitz & Stegun 26.2.17, |error| < 7.5e-8."""
    ax = np.abs(x)
    t = 1.0 / (1.0 + 0.2316419 * ax)
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    upper = norm_pdf(ax) * poly
    return np.where(x >= 0, 1.0 - upper, upper)


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


def best_prices(depth):
    if depth is None or not depth.buy_orders or not depth.sell_orders:
        return None
    return max(depth.buy_orders), min(depth.sell_orders)


def ewma(old, new, span):
    alpha = 2.0 / (span + 1.0)
    return old + alpha * (new - old)


class Trader:
    def run(self, state: TradingState):
        orders = {}
        try:
            memory = json.loads(state.traderData) if state.traderData else {}
        except (ValueError, TypeError):
            memory = {}
        try:
            memory = self._step(state, memory, orders)
        except Exception as error:  # never raise into the engine; log and trade nothing this tick
            print(f"S3 error: {error!r}")
            orders = {}
        return orders, 0, json.dumps(memory, separators=(",", ":"))

    # ---- per tick -------------------------------------------------------------------------------------------

    def _step(self, state, memory, orders):
        quote = best_prices(state.order_depths.get(UNDERLYING))
        if quote is None:
            return memory
        spot = 0.5 * (quote[0] + quote[1])
        memory = self._update_underlying(memory, spot, state.timestamp)
        days = max(DAYS_TO_EXPIRY_AT_OPEN - state.timestamp / TIMESTAMPS_PER_DAY, MIN_DAYS_TO_EXPIRY)

        surface = self._fit_surface(state, memory, spot, days)
        if surface is None:
            orders.update(self._underlying_orders(state, 0.0, quote, memory))
            return memory
        memory = surface["memory"]
        voucher_delta = self._voucher_orders(state, surface, memory, orders)
        orders.update(self._underlying_orders(state, voucher_delta, quote, memory))
        return memory

    def _update_underlying(self, memory, spot, timestamp):
        last = memory.get("S")
        var = memory.get("sv", PRIOR_LYCHEE_TICK_VAR)
        cooldown = max(memory.get("cd", 0) - 1, 0)
        if last is not None:
            move = spot - last
            if move * move > JUMP_Z * JUMP_Z * var:
                cooldown = COOLDOWN_TICKS
            var = ewma(var, min(move * move, 25.0 * var), LYCHEE_VAR_SPAN)
        sample_spot = memory.get("S10", spot)
        rv = memory.get("rv", PRIOR_LYCHEE_TICK_VAR * RV_SAMPLE_TICKS)
        ticks_since = memory.get("n10", 0) + 1
        if ticks_since >= RV_SAMPLE_TICKS:
            move = spot - sample_spot
            rv = ewma(rv, min(move * move, 25.0 * rv), RV_SPAN)
            sample_spot, ticks_since = spot, 0
        return {**memory, "S": spot, "sv": var, "cd": cooldown, "S10": sample_spot, "rv": rv, "n10": ticks_since}

    def _fit_surface(self, state, memory, spot, days):
        mids = np.full(N_STRIKES, np.nan)
        quotes = []
        for i, product in enumerate(VOUCHERS):
            quote = best_prices(state.order_depths.get(product))
            quotes.append(quote)
            if quote is not None:
                mids[i] = 0.5 * (quote[0] + quote[1])
        present = ~np.isnan(mids)
        if present.sum() < 4:
            return None

        guess = np.array(memory.get("iv", [PRIOR_IV] * N_STRIKES), dtype=float)
        safe_mids = np.where(present, mids, 1.0)
        iv, valid = implied_vol(safe_mids, spot, STRIKE_ARRAY, days, guess)
        valid &= present
        if valid.sum() < 4:
            return None
        _, _, vega, _ = bs_call(spot, STRIKE_ARRAY, days, iv)
        resid_var = np.array(memory.get("rv2", (PRIOR_RESIDUAL_SD**2).tolist()), dtype=float)
        weights = np.where(valid, vega * vega / (resid_var + ROUNDING_VAR), 0.0)
        moneyness = np.log(STRIKE_ARRAY / spot) / math.sqrt(days)

        beta = wls_quadratic(moneyness, iv, weights)
        if beta is None:
            return None
        shape_b = ewma(memory.get("b", beta[1]), beta[1], SHAPE_SPAN)
        shape_c = ewma(memory.get("c", beta[2]), beta[2], SHAPE_SPAN)
        level = float(np.sum(weights * (iv - shape_b * moneyness - shape_c * moneyness**2)) / np.sum(weights))
        fitted_iv = np.clip(level + shape_b * moneyness + shape_c * moneyness**2, IV_MIN, IV_MAX)
        fair, delta, fit_vega, d1 = bs_call(spot, STRIKE_ARRAY, days, fitted_iv)
        # Sticky-delta smile: dIV/dS = -(b + 2cm) / (S sqrt T), so delta gains vega * dIV/dS.
        delta = delta - SMILE_DELTA_WEIGHT * norm_pdf(d1) * (shape_b + 2.0 * shape_c * moneyness)
        residual = np.where(present, mids - fair, 0.0)

        prev_r = np.array(memory.get("r", residual.tolist()), dtype=float)
        lag_cov = np.array(memory.get("lc", (PRIOR_PHI * PRIOR_RESIDUAL_SD**2).tolist()), dtype=float)
        lag_var = np.array(memory.get("lv", (PRIOR_RESIDUAL_SD**2).tolist()), dtype=float)
        update = valid & np.array(memory.get("ok", [True] * N_STRIKES), dtype=bool)
        alpha = 2.0 / (RESIDUAL_VAR_SPAN + 1.0)
        resid_var = np.where(valid, resid_var + alpha * (residual * residual - resid_var), resid_var)
        lag_cov = np.where(update, lag_cov + alpha * (residual * prev_r - lag_cov), lag_cov)
        lag_var = np.where(update, lag_var + alpha * (prev_r * prev_r - lag_var), lag_var)
        phi = np.clip(lag_cov / np.maximum(lag_var, 1e-9), *PHI_BOUNDS)

        new_memory = {
            **memory,
            "iv": np.round(np.where(valid, iv, guess), 6).tolist(),
            "rv2": np.round(resid_var, 4).tolist(),
            "lc": np.round(lag_cov, 4).tolist(),
            "lv": np.round(lag_var, 4).tolist(),
            "r": np.round(residual, 3).tolist(),
            "ok": valid.tolist(),
            "b": shape_b,
            "c": shape_c,
        }
        return {
            "memory": new_memory,
            "quotes": quotes,
            "valid": valid,
            "fair": fair,
            "residual": residual,
            "sd": np.sqrt(resid_var),
            "phi": phi,
            "delta": delta,
            "vega": fit_vega,
            "gamma": norm_pdf(d1) / (spot * fitted_iv * math.sqrt(days)),
            "level": level,
            "spot": spot,
        }

    # ---- vouchers -------------------------------------------------------------------------------------------

    def _vrp_tilt(self, surface, memory):
        if VRP_HORIZON_DAYS <= 0:
            return np.zeros(N_STRIKES)
        spot = surface["spot"]
        rv_day = math.sqrt(memory["rv"] / RV_SAMPLE_TICKS * TICKS_PER_DAY) / spot
        iv_atm = surface["level"]
        if rv_day <= 0 or iv_atm / rv_day < VRP_KILL_RATIO:
            return np.zeros(N_STRIKES)
        bleed = 0.5 * surface["gamma"] * spot * spot * (iv_atm * iv_atm - rv_day * rv_day)
        return bleed * VRP_HORIZON_DAYS

    def _voucher_orders(self, state, surface, memory, orders):
        positions = np.array([state.position.get(p, 0) for p in VOUCHERS], dtype=float)
        net_vega = float(np.sum(positions * surface["vega"]))
        net_delta = float(np.sum(positions * surface["delta"]))
        excess_vega = math.copysign(max(abs(net_vega) - NET_VEGA_SOFT, 0.0), net_vega)
        excess_delta = math.copysign(max(abs(net_delta) - DELTA_SOFT, 0.0), net_delta)
        rho = surface["phi"] ** HOLD_HORIZON
        value = (
            surface["fair"]
            + rho * surface["residual"]
            - self._vrp_tilt(surface, memory)
            - VEGA_PENALTY * excess_vega * surface["vega"]
            - DELTA_PENALTY * excess_delta * surface["delta"]
        )
        cooling = memory.get("cd", 0) > 0
        expected_delta = 0.0
        for i, product in enumerate(VOUCHERS):
            quote = surface["quotes"][i]
            position = int(positions[i])
            if not surface["valid"][i] or quote is None:
                expected_delta += position * surface["delta"][i]
                continue
            slope = RISK_AVERSION * surface["sd"][i] / VOUCHER_LIMIT
            product_orders, taken = self._strike_orders(
                state.order_depths[product], product, position, value[i], slope, surface["residual"][i], cooling
            )
            if product_orders:
                orders[product] = product_orders
            expected_delta += (position + taken) * surface["delta"][i]
        return expected_delta

    def _strike_orders(self, depth, product, position, value, slope, residual, cooling):
        """Target position at price p is (value - edge - p) / slope for buys, (value + edge - p) / slope for sells."""
        out = []
        buy_room = VOUCHER_LIMIT - position
        sell_room = VOUCHER_LIMIT + position
        planned = position
        for price in sorted(depth.sell_orders):
            target = math.floor((value - TAKE_EDGE - price) / slope)
            if cooling:
                target = min(target, 0) if planned < 0 else planned  # only reduce a short
            qty = min(abs(depth.sell_orders[price]), target - planned, buy_room)
            if qty <= 0:
                break
            out.append(Order(product, price, qty))
            planned += qty
            buy_room -= qty
        for price in sorted(depth.buy_orders, reverse=True):
            target = math.ceil((value + TAKE_EDGE - price) / slope)
            if cooling:
                target = max(target, 0) if planned > 0 else planned  # only reduce a long
            qty = min(depth.buy_orders[price], planned - target, sell_room)
            if qty <= 0:
                break
            out.append(Order(product, price, -qty))
            planned -= qty
            sell_room -= qty
        taken = planned - position
        if cooling:
            return out, taken
        best_bid, best_ask = max(depth.buy_orders), min(depth.sell_orders)
        if residual < 0 and best_bid < best_ask:  # cheap: rule takers lift asks, so only rest bids
            target = math.floor((value - PASSIVE_EDGE - best_bid) / slope)
            qty = min(target - planned, PASSIVE_MAX, buy_room)
            if qty > 0:
                out.append(Order(product, best_bid, qty))
        elif residual > 0 and best_bid < best_ask:  # rich: rule takers hit bids, so only rest asks
            target = math.ceil((value + PASSIVE_EDGE - best_ask) / slope)
            qty = min(planned - target, PASSIVE_MAX, sell_room)
            if qty > 0:
                out.append(Order(product, best_ask, -qty))
        return out, taken

    # ---- LYCHEE ---------------------------------------------------------------------------------------------

    def _underlying_orders(self, state, voucher_delta, quote, memory):
        depth = state.order_depths[UNDERLYING]
        position = state.position.get(UNDERLYING, 0)
        target = max(-UNDERLYING_LIMIT, min(UNDERLYING_LIMIT, -voucher_delta))
        gap = target - position
        out = []
        buy_room = UNDERLYING_LIMIT - position
        sell_room = UNDERLYING_LIMIT + position
        if gap > HEDGE_BAND:
            need = int(math.floor(gap - HEDGE_BAND))
            for price in sorted(depth.sell_orders):
                qty = min(abs(depth.sell_orders[price]), need, buy_room)
                if qty <= 0:
                    break
                out.append(Order(UNDERLYING, price, qty))
                need -= qty
                buy_room -= qty
                position += qty
        elif gap < -HEDGE_BAND:
            need = int(math.floor(-gap - HEDGE_BAND))
            for price in sorted(depth.buy_orders, reverse=True):
                qty = min(depth.buy_orders[price], need, sell_room)
                if qty <= 0:
                    break
                out.append(Order(UNDERLYING, price, -qty))
                need -= qty
                sell_room -= qty
                position -= qty
        if memory.get("cd", 0) > 0:
            return {UNDERLYING: out} if out else {}
        best_bid, best_ask = quote
        lean = MAKE_SKEW * (target - position)
        bid_qty = int(min(max(MAKE_SIZE + lean, 0), buy_room))
        ask_qty = int(min(max(MAKE_SIZE - lean, 0), sell_room))
        if bid_qty > 0:
            out.append(Order(UNDERLYING, best_bid, bid_qty))
        if ask_qty > 0:
            out.append(Order(UNDERLYING, best_ask, -ask_qty))
        return {UNDERLYING: out} if out else {}
