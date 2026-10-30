"""S1: diversified, inventory-aware market maker on the 15 benign delta-one products.

Structure (one class per job, so S2/S5 can reuse the engine):
  * `MidStats`          online EWMA variance and lag-1 autocovariance of mid changes, which split the mid's
                        variance into fair-value innovation q and quote noise r (local-level identities
                        Var(dm) = q + 2r, Cov(dm_t, dm_t-1) = -r).
  * Fair-value archetypes, each `update(st, mid) -> (fair, fair_for_inventory)`:
      - `PlateauFair`   AMETHYST, GOLDEN_PEARLS, PINK_PEARLS: a long-EWMA plateau with a change-point test on a
                        fast EWMA; on a confirmed break it tracks the mid and re-forms the plateau once calm.
                        AMETHYST starts with a strong 10,000 prior (the anchor-break guard is the same test).
      - `LevelFair`     PAPER_LANTERNS (gain fixed to EWMA span 5) and the random walks: a local-level Kalman
                        filter whose steady-state gain comes from the online q and r (raw mid when r ~ 0).
      - `MeanRevertFair` TOFFEE_CAKE: OU Kalman filter around a slowly learned anchor; inventory is valued at the
                        expected fair value over the holding horizon, so the book leans against deviations.
  * `AdverseSelection`  O(1) markout estimator: exponentially decayed fill inventory times later fair changes.
  * `OffsetBandit`      Beta-Bernoulli fill rate per quote offset (touch / improve 1), chosen by Thompson
                        sampling on expected value = P(fill) x edge.
  * `Quoter`            Avellaneda-Stoikov reservation price r = fair - kappa q with kappa = gamma sigma^2 H
                        (floored), linear size-by-edge, value takes and inventory flattening.
"""

import json
import math
import random

from datamodel import Order, TradingState

LIMITS = {
    "AMETHYST": 50, "TOFFEE_CAKE": 50, "PAPER_LANTERNS": 50, "JELLY": 50, "PEANUT_BUTTER": 50,
    "DRAGONFRUIT": 40, "GRANADILLA": 40, "MANGOSTEEN": 40, "FRUIT_BASKET": 40, "LYCHEE": 200,
    "WHITE_PEARLS": 20, "BLACK_PEARLS": 20, "GOLDEN_PEARLS": 20, "PINK_PEARLS": 20, "BLUE_PEARLS": 20,
}

# Per-product archetype and priors (all from the EDA pages).
PLATEAU = "plateau"
LEVEL = "level"
MEAN_REVERT = "ou"
CONFIG = {
    "AMETHYST": {"kind": PLATEAU, "anchor": 10_000.0},          # mid never left 9,999.5-10,000.5
    "GOLDEN_PEARLS": {"kind": PLATEAU, "lookahead": 10.0},      # steps ramp ~1.2/tick and keep falling ~33/20 ticks
    "PINK_PEARLS": {"kind": PLATEAU},                           # flat noise (sigma 0.5) between instant jumps
    "PAPER_LANTERNS": {"kind": LEVEL, "gain": 2.0 / (5 + 1)},   # best fair = EWMA span 5 (RMSE -16%)
    "TOFFEE_CAKE": {"kind": MEAN_REVERT, "anchor": 5_000.0, "kappa": 0.0046, "gain": 2.0 / (3 + 1)},
}
DEFAULT_CONFIG = {"kind": LEVEL}

# Estimator spans (ticks).
VOL_SPAN = 500              # mid-change variance / autocovariance
SPREAD_SPAN = 200
PLATEAU_SPAN = 200          # EDA: best AMETHYST/GOLDEN fair is EWMA span 200
FAST_SPAN = 5               # change-point statistic
DRIFT_SPAN = 10             # drift while tracking a break
ANCHOR_PRIOR_TICKS = 200    # AMETHYST 10,000 prior worth this many observations
OU_ANCHOR_SPAN = 3_000      # TOFFEE anchor learning (half-life ~150 ticks, so many cycles per anchor update)
OU_HOLD_TICKS = 50          # inventory horizon used to value TOFFEE positions at E[fair_{t+H}]
MARKOUT_SPAN = 20           # EDA markout horizon
ADVERSE_MEMORY = 3_000
ADVERSE_PRIOR_LOTS = 50.0   # shrink markout estimate towards 0 (Normal prior worth 50 lots)

# Tests (in standard deviations of the statistic under the no-change null).
STEP_Z = 5.0
CALM_Z = 2.0
CALM_TICKS = 20
JUMP_Z = 5.0
JUMP_MIN_MOVE = 2.0         # ticks; below this a "5 sigma" move is just price discreteness
GUARD_TICKS = 50
TAKE_Z = 2.0              # value takes need edge > TAKE_Z standard errors of the fair-value estimate

# Inventory / sizing.
RISK_GAMMA = 0.03           # gamma * H in kappa = gamma * H * q_var
SOFT_CAP = 0.8              # passive inventory never targets beyond 80% of the limit
TAKE_BAND_MULT = 2.0        # flattening takes use kappa / 2: cross only well beyond the passive band
MIN_IMPROVE_SPREAD = 3      # improving needs room to stay strictly inside the spread
BETA_PRIOR = (1.0, 50.0)
FILL_MEMORY = 0.999


def ewma(old, new, alpha):
    return old + alpha * (new - old)


class MidStats:
    """EWMA Var(dm), lag-1 Cov(dm), fast drift; q = fair innovation variance, r = quote-noise variance."""

    @staticmethod
    def update(st, mid):
        n = st["n"] = st.get("n", 0) + 1
        prev = st.get("m")
        st["m"] = mid
        if prev is None:
            st.update(v=1.0, c=0.0, dm=0.0, d=0.0)
            return 0.0, False
        dm = mid - prev
        alpha = max(1.0 / n, 1.0 / VOL_SPAN)
        sd = math.sqrt(max(st["v"], 0.25))
        jump = n > 20 and abs(dm) >= JUMP_MIN_MOVE and abs(dm) > JUMP_Z * sd
        st["c"] = ewma(st["c"], dm * st["dm"], alpha)
        st["v"] = ewma(st["v"], dm * dm, alpha)
        st["dm"] = dm
        a_fast = 2.0 / (FAST_SPAN + 1)
        st["d"] = ewma(st["d"], dm, a_fast)
        sd_drift = sd * math.sqrt(a_fast / (2.0 - a_fast))
        trending = n > 20 and abs(st["d"]) > JUMP_Z * sd_drift and abs(st["d"]) * FAST_SPAN >= JUMP_MIN_MOVE
        return dm, jump or trending

    @staticmethod
    def noise_var(st):
        return max(-st["c"], 0.0)

    @staticmethod
    def fair_var(st):
        return max(st["v"] + 2.0 * st["c"], 0.0)


class PlateauFair:
    """Piecewise-constant fair value: plateau P (EWMA span 200) plus a CUSUM-like test on a fast EWMA."""

    @staticmethod
    def update(st, mid, cfg):
        if "P" not in st:
            anchor = cfg.get("anchor")
            st.update(P=anchor if anchor is not None else mid, nP=ANCHOR_PRIOR_TICKS if anchor else 1,
                      F=mid, md=0, cl=0, s2=0.25, td=0.0)
        a_fast = 2.0 / (FAST_SPAN + 1)
        prev_fast = st["F"]
        st["F"] = ewma(st["F"], mid, a_fast)
        if st["md"] == 0:
            sd_fast = math.sqrt(max(st["s2"], 0.0625) * a_fast / (2.0 - a_fast))
            if abs(st["F"] - st["P"]) > STEP_Z * sd_fast:
                st.update(md=1, cl=0, td=st["F"] - prev_fast)
            else:
                st["nP"] = st["nP"] + 1
                st["P"] = ewma(st["P"], mid, max(1.0 / st["nP"], 1.0 / PLATEAU_SPAN))
                st["s2"] = ewma(st["s2"], (mid - st["P"]) ** 2, 1.0 / PLATEAU_SPAN)
                return st["P"], st["P"], False
        st["td"] = ewma(st["td"], st["F"] - prev_fast, 2.0 / (DRIFT_SPAN + 1))
        calm = abs(mid - st["F"]) < CALM_Z * math.sqrt(max(st["s2"], 0.0625)) + 0.5
        st["cl"] = st["cl"] + 1 if calm else 0
        if st["cl"] >= CALM_TICKS:
            st.update(md=0, P=st["F"], nP=CALM_TICKS)
            return st["P"], st["P"], False
        fair = mid + st["td"] * cfg.get("lookahead", 0.0)
        return fair, fair, True


class LevelFair:
    """Local-level Kalman filter; gain fixed by config or from the online q/r split. Resets on outliers."""

    @staticmethod
    def gain(st, cfg):
        if "gain" in cfg:
            return cfg["gain"]
        q, r = MidStats.fair_var(st), MidStats.noise_var(st)
        if r <= 1e-9 or st["n"] < 50:
            return 1.0
        x = 0.5 * (q + math.sqrt(q * q + 4.0 * q * r))
        return min(max(x / (x + r), 0.3), 1.0)

    @staticmethod
    def update(st, mid, cfg):
        if "f" not in st:
            st["f"] = mid
            return mid, mid, False
        k = LevelFair.gain(st, cfg)
        innovation = mid - st["f"]
        if abs(innovation) > JUMP_Z * math.sqrt(max(st["v"], 0.25)):
            st["f"] = mid
        else:
            st["f"] += k * innovation
        return st["f"], st["f"], False


class MeanRevertFair:
    """OU Kalman filter: predict mu + phi (f - mu), correct with the mid; inventory valued at E[f_{t+H}]."""

    @staticmethod
    def update(st, mid, cfg):
        if "f" not in st:
            st.update(f=mid, mu=cfg["anchor"], nmu=OU_ANCHOR_SPAN)
        phi = 1.0 - cfg["kappa"]
        st["nmu"] += 1
        st["mu"] = ewma(st["mu"], mid, max(1.0 / st["nmu"], 1.0 / OU_ANCHOR_SPAN))
        pred = st["mu"] + phi * (st["f"] - st["mu"])
        innovation = mid - pred
        if abs(innovation) > JUMP_Z * math.sqrt(max(st["v"], 1.0)):
            st["f"] = mid
        else:
            st["f"] = pred + cfg["gain"] * innovation
        lean = 1.0 - phi ** OU_HOLD_TICKS
        return st["f"], st["f"] + lean * (st["mu"] - st["f"]), False


FAIR_MODELS = {PLATEAU: PlateauFair, LEVEL: LevelFair, MEAN_REVERT: MeanRevertFair}


class AdverseSelection:
    """E[markout loss per passive lot]: decayed fill inventory X times subsequent fair changes, shrunk to 0."""

    @staticmethod
    def update(st, fair_change, passive_signed_qty, passive_lots):
        decay = 1.0 - 1.0 / ADVERSE_MEMORY
        st["A"] = st.get("A", 0.0) * decay + st.get("X", 0.0) * fair_change
        st["N"] = st.get("N", 0.0) * decay + passive_lots
        st["X"] = st.get("X", 0.0) * (1.0 - 1.0 / MARKOUT_SPAN) + passive_signed_qty

    @staticmethod
    def cost(st):
        return max(-st.get("A", 0.0) / (st.get("N", 0.0) + ADVERSE_PRIOR_LOTS), 0.0)


class OffsetBandit:
    """Beta-Bernoulli fill probability per offset (0 = touch, 1 = improve by one), pooled over sides."""

    @staticmethod
    def record(st, offset, filled):
        stats = st.setdefault("fb", [0.0, 0.0, 0.0, 0.0])
        i = 2 * offset
        stats[i] = stats[i] * FILL_MEMORY + (1.0 if filled else 0.0)
        stats[i + 1] = stats[i + 1] * FILL_MEMORY + 1.0

    @staticmethod
    def choose(st, edges, rng):
        """edges[o] = expected edge per lot at offset o (None if not allowed). Thompson sampling with a normal
        approximation to each Beta posterior; offset 0 when it is the only choice (no sampling needed)."""
        if edges[1] is None or edges[1] <= 0:
            return 0
        if edges[0] is None or edges[0] <= 0:
            return 1
        stats = st.get("fb", [0.0, 0.0, 0.0, 0.0])
        values = []
        for offset in (0, 1):
            a = BETA_PRIOR[0] + stats[2 * offset]
            b = BETA_PRIOR[1] + max(stats[2 * offset + 1] - stats[2 * offset], 0.0)
            mean = a / (a + b)
            sd = math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1.0)))
            values.append(max(mean + sd * rng.gauss(0.0, 1.0), 0.0) * edges[offset])
        return 0 if values[0] >= values[1] else 1


class Quoter:
    """Reservation-price market making with size proportional to edge / kappa."""

    @staticmethod
    def kappa(st, limit, cfg):
        half_spread = max(st.get("sp", 2.0) / 2.0, 0.5)
        floor = half_spread / (SOFT_CAP * limit)
        return max(floor, RISK_GAMMA * MidStats.fair_var(st))

    @staticmethod
    def orders(product, depth, position, limit, fair_inv, kappa, adverse, hurdle, guard_dir, st, rng):
        bids = sorted(depth.buy_orders.items(), reverse=True)
        asks = sorted((p, abs(v)) for p, v in depth.sell_orders.items())
        best_bid, best_ask = bids[0][0], asks[0][0]
        out = []
        buy_room, sell_room = limit - position, limit + position
        take_kappa = kappa / TAKE_BAND_MULT

        bought = 0
        for price, volume in asks:
            target = (fair_inv - price - hurdle) / take_kappa
            want = min(volume, int(math.floor(target - position - bought)), buy_room - bought)
            if want <= 0:
                break
            out.append(Order(product, price, want))
            bought += want
        sold = 0
        for price, volume in bids:
            target = -(price - fair_inv - hurdle) / take_kappa
            want = min(volume, int(math.floor(position - sold - target)), sell_room - sold)
            if want <= 0:
                break
            out.append(Order(product, price, -want))
            sold += want

        spread = best_ask - best_bid
        can_improve = spread >= MIN_IMPROVE_SPREAD
        reservation = fair_inv - kappa * position
        cap = SOFT_CAP * limit
        quotes = {"b": None, "a": None}

        if guard_dir >= 0 and bought == 0:
            edges = [reservation - (best_bid + o) - adverse if (o == 0 or can_improve) else None for o in (0, 1)]
            offset = OffsetBandit.choose(st, edges, rng)
            price = best_bid + offset
            edge = reservation - price - adverse
            if edge > 0 and price < best_ask:
                target = min((fair_inv - price - adverse) / kappa, cap)
                size = min(int(math.floor(target - position)), buy_room - bought)
                if size > 0:
                    out.append(Order(product, price, size))
                    quotes["b"] = [price, offset]
        if guard_dir <= 0 and sold == 0:
            edges = [(best_ask - o) - reservation - adverse if (o == 0 or can_improve) else None for o in (0, 1)]
            offset = OffsetBandit.choose(st, edges, rng)
            price = best_ask - offset
            edge = price - reservation - adverse
            if edge > 0 and price > best_bid:
                target = min((price - fair_inv - adverse) / kappa, cap)
                size = min(int(math.floor(position + target)), sell_room - sold)
                if size > 0:
                    out.append(Order(product, price, -size))
                    quotes["a"] = [price, offset]
        st["lq"] = [quotes["b"], quotes["a"]]
        return out


def passive_fills(st, trades):
    """Split last tick's own trades into passive fills (at our resting quote price) and update the bandit."""
    last_bid, last_ask = st.get("lq", [None, None])
    signed, lots, bid_hit, ask_hit = 0, 0, False, False
    for trade in trades:
        if trade.buyer == "SUBMISSION" and last_bid and trade.price == last_bid[0]:
            signed += trade.quantity
            lots += trade.quantity
            bid_hit = True
        elif trade.seller == "SUBMISSION" and last_ask and trade.price == last_ask[0]:
            signed -= trade.quantity
            lots += trade.quantity
            ask_hit = True
    if last_bid:
        OffsetBandit.record(st, last_bid[1], bid_hit)
    if last_ask:
        OffsetBandit.record(st, last_ask[1], ask_hit)
    return signed, lots


def fair_sd(st, cfg, tracking):
    """Standard error of the fair-value estimate: posterior sd of the Kalman filter (K r), or the plateau's
    standard error s / sqrt(n); while tracking a break, the raw mid-change sd."""
    if cfg["kind"] == PLATEAU:
        if tracking:
            return math.sqrt(st["v"])
        return math.sqrt(st["s2"] / min(st["nP"], PLATEAU_SPAN))
    gain = cfg.get("gain") or LevelFair.gain(st, cfg)
    return math.sqrt(gain * MidStats.noise_var(st) + 0.01)


def trade_product(product, depth, position, own_trades, st, rng):
    limit = LIMITS[product]
    cfg = CONFIG.get(product, DEFAULT_CONFIG)
    best_bid, best_ask = max(depth.buy_orders), min(depth.sell_orders)
    mid = 0.5 * (best_bid + best_ask)
    st["sp"] = ewma(st.get("sp", best_ask - best_bid), best_ask - best_bid, 1.0 / SPREAD_SPAN)

    prev_fair = st.get("fv")
    _, shocked = MidStats.update(st, mid)
    fair, fair_inv, tracking = FAIR_MODELS[cfg["kind"]].update(st, mid, cfg)
    st["fv"] = fair

    signed, lots = passive_fills(st, own_trades)
    AdverseSelection.update(st, 0.0 if prev_fair is None else fair - prev_fair, signed, lots)

    guard_dir = 0
    if cfg["kind"] != PLATEAU:
        if shocked:
            st["g"] = GUARD_TICKS
        if st.get("g", 0) > 0:
            st["g"] -= 1
            guard_dir = 1 if st["d"] > 0 else -1   # quote only the side the move favours; no value takes
    elif tracking:
        guard_dir = 1 if st["td"] > 0 else -1 if st["td"] < 0 else 0

    kappa = Quoter.kappa(st, limit, cfg)
    if tracking:
        kappa = max(kappa, RISK_GAMMA * st["v"])
    hurdle = math.inf if guard_dir and not tracking else TAKE_Z * fair_sd(st, cfg, tracking)
    return Quoter.orders(product, depth, position, limit, fair_inv, kappa,
                         AdverseSelection.cost(st), hurdle, guard_dir, st, rng)


class Trader:
    def run(self, state: TradingState):
        memory = self._load(state.traderData)
        rng = random.Random(state.timestamp)
        result = {}
        for product, depth in state.order_depths.items():
            if product not in LIMITS or not depth.buy_orders or not depth.sell_orders:
                continue
            st = memory.setdefault(product, {})
            try:
                orders = trade_product(product, depth, state.position.get(product, 0),
                                       state.own_trades.get(product, []), st, rng)
            except Exception:  # never let one product's numerical edge case kill the whole tick
                orders = []
            if orders:
                result[product] = orders
        data = json.dumps(memory, separators=(",", ":"))
        self._cache = (data, memory)
        return result, 0, data

    def _load(self, data):
        """traderData is the source of truth; the parsed copy is reused only when it is byte-identical."""
        cache = getattr(self, "_cache", None)
        if cache is not None and cache[0] == data:
            return cache[1]
        try:
            memory = json.loads(data) if data else {}
        except (ValueError, TypeError):
            memory = {}
        return memory if isinstance(memory, dict) else {}
