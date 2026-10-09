"""Intraday position sizing: fractional Kelly, vol targeting, liquidity and participation caps.

Research / paper only. No real order is ever sent; a SizingDecision is advisory.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence

from bist_signal_bot.edge_validation.costs import tick_size

NO_ORDER_NOTE = "No real order sent."


def _get(obj: Any, name: str, default: Any = None) -> Any:
    """Read `name` from a dict, mapping-like, or attribute object."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _cfg(settings: Any, name: str, default: Any) -> Any:
    val = _get(settings, name, None)
    return default if val is None else val


def _finite(x: Any) -> bool:
    try:
        return x is not None and math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def position_notional(pos: Any) -> float:
    """Absolute notional of a position-like object (notional, else qty*price)."""
    n = _get(pos, "notional", None)
    if _finite(n):
        return abs(float(n))
    q = _get(pos, "qty", _get(pos, "quantity", 0.0)) or 0.0
    p = _get(pos, "price", _get(pos, "current_price", _get(pos, "entry_price", 0.0))) or 0.0
    return abs(float(q) * float(p))


def fractional_kelly(p_win: float, avg_win: float, avg_loss: float, fraction: float = 0.25,
                     cap: float = 0.10, n_obs: int | None = None,
                     prior_strength: float = 200.0) -> float:
    """Fractional Kelly equity fraction. f* = p - (1-p)/b, b = avg_win/avg_loss.

    If n_obs is given, p is shrunk toward 0.5 with weight n/(n+prior_strength), so small
    samples lower the size. Returns 0.0 for invalid inputs or no edge; result in [0, cap].
    """
    if not all(_finite(v) for v in (p_win, avg_win, avg_loss, fraction, cap)):
        return 0.0
    p, w, l = float(p_win), float(avg_win), float(avg_loss)
    if not (0.0 < p < 1.0) or w <= 0.0 or l <= 0.0 or fraction <= 0.0 or cap <= 0.0:
        return 0.0
    if n_obs is not None:
        if n_obs <= 0:
            return 0.0
        wt = n_obs / (n_obs + max(0.0, float(prior_strength)))
        p = 0.5 + (p - 0.5) * wt
    b = w / l
    full = p - (1.0 - p) / b
    if full <= 0.0:
        return 0.0
    return float(min(full * fraction, cap))


def vol_target_fraction(asset_vol_annual: float, target_vol_annual: float,
                        max_leverage: float = 1.0) -> float:
    """Equity fraction so that fraction*asset_vol == target vol, capped at max_leverage."""
    if not (_finite(asset_vol_annual) and _finite(target_vol_annual) and _finite(max_leverage)):
        return 0.0
    if asset_vol_annual <= 0 or target_vol_annual <= 0 or max_leverage <= 0:
        return 0.0
    return float(min(target_vol_annual / asset_vol_annual, max_leverage))


def liquidity_filter(adv_value_try: float, spread_bps: float, min_adv_try: float,
                     max_spread_bps: float) -> tuple[bool, list[str]]:
    """(ok, reasons). Missing / non-finite data fails closed."""
    reasons: list[str] = []
    if not _finite(adv_value_try) or adv_value_try < min_adv_try:
        reasons.append("illiquid")
    if not _finite(spread_bps) or spread_bps > max_spread_bps:
        reasons.append("wide_spread")
    return (not reasons), reasons


def max_order_value(adv_value_try: float, bar_value_try: float, max_participation: float) -> float:
    """Max order value (TRY): participation cap of both bar traded value and ADV."""
    if not (_finite(adv_value_try) and _finite(bar_value_try) and _finite(max_participation)):
        return 0.0
    if adv_value_try <= 0 or bar_value_try <= 0 or max_participation <= 0:
        return 0.0
    return float(max_participation * min(adv_value_try, bar_value_try))


@dataclass
class SizingDecision:
    allowed: bool
    qty: int = 0
    notional: float = 0.0
    risk_bps: float = 0.0
    reasons: list[str] = field(default_factory=list)
    method: str = ""  # name of the binding constraint (or "rejected")
    constraints: dict[str, float] = field(default_factory=dict)  # candidate notionals
    note: str = NO_ORDER_NOTE


class IntradaySizer:
    """Min-of-constraints sizer. Binding constraint is reported in `method` and `reasons`."""

    def __init__(self, settings: Any = None):
        self.settings = settings

    def _reject(self, reasons: list[str], constraints: dict | None = None) -> SizingDecision:
        return SizingDecision(False, 0, 0.0, 0.0, reasons, "rejected", constraints or {})

    def size(self, signal_confidence: float, price: float, equity: float,
             asset_vol_annual: float, adv_value_try: float, bar_value_try: float,
             spread_bps: float, edge_stats: Any = None,
             open_positions: Sequence[Any] | None = None, settings: Any = None, *,
             stop_distance: float | None = None, side: str = "LONG",
             cash: float | None = None,
             daily_limits: tuple[float, float] | None = None) -> SizingDecision:
        """Size a trade.

        edge_stats: dict/obj with p_win, avg_win, avg_loss, optional n_obs (None disables Kelly).
        stop_distance: absolute price distance to stop; default RISK_FIXED_STOP_PCT * price.
        cash: available cash (defaults to unconstrained beyond the gross exposure budget).
        daily_limits: (floor, ceiling) from intraday.sessions.daily_price_limits.
        signal_confidence only gates (must be > 0); it does not scale the size.
        """
        s = settings if settings is not None else self.settings
        open_positions = list(open_positions or [])
        lot = max(1, int(_cfg(s, "RISK_LOT_SIZE", 1)))
        reasons: list[str] = []

        # --- hard rejections ---
        if str(side).upper() in ("SHORT", "SELL") and not bool(_cfg(s, "INTRADAY_ALLOW_SHORT", False)):
            return self._reject(["long_only_violation"])
        if not _finite(price) or price < 0.01 or price > 1_000_000:
            return self._reject(["price_outside_tick_sanity"])
        if not _finite(equity) or equity <= 0:
            return self._reject(["invalid_equity"])
        if not _finite(signal_confidence) or signal_confidence <= 0:
            return self._reject(["no_signal_confidence"])
        tick = tick_size(float(price))
        if daily_limits is not None:
            lo, hi = daily_limits
            if price >= hi - tick:
                return self._reject(["price_at_upper_limit"])
            if price <= lo + tick:
                return self._reject(["price_at_lower_limit"])
        ok, liq_reasons = liquidity_filter(adv_value_try, spread_bps,
                                           float(_cfg(s, "RISK_MIN_ADV_TRY", 5_000_000.0)),
                                           float(_cfg(s, "RISK_MAX_SPREAD_BPS", 40.0)))
        if not ok:
            return self._reject(liq_reasons)

        # --- constraint candidates (notional TRY) ---
        cands: dict[str, float] = {}
        kelly_required = bool(_cfg(s, "RISK_KELLY_REQUIRED", False))
        if edge_stats is not None:
            f = fractional_kelly(
                _get(edge_stats, "p_win", 0.0), _get(edge_stats, "avg_win", 0.0),
                _get(edge_stats, "avg_loss", 0.0),
                fraction=float(_cfg(s, "RISK_KELLY_FRACTION", 0.25)),
                cap=float(_cfg(s, "RISK_KELLY_CAP", 0.10)),
                n_obs=_get(edge_stats, "n_obs", None),
                prior_strength=float(_cfg(s, "RISK_KELLY_PRIOR_STRENGTH", 200)))
            if f <= 0.0:
                return self._reject(["no_edge"])
            cands["kelly"] = f * equity
        elif kelly_required:
            return self._reject(["no_edge_stats"])

        vf = vol_target_fraction(asset_vol_annual, float(_cfg(s, "RISK_TARGET_VOL_ANNUAL", 0.15)),
                                 float(_cfg(s, "RISK_MAX_LEVERAGE", 1.0)))
        if vf <= 0:
            return self._reject(["invalid_volatility"])
        cands["vol_target"] = vf * equity

        sd = stop_distance if _finite(stop_distance) and stop_distance > 0 else \
            float(_cfg(s, "RISK_FIXED_STOP_PCT", 0.05)) * price
        risk_budget = float(_cfg(s, "RISK_MAX_RISK_PER_TRADE_BPS", 25.0)) / 1e4 * equity
        cands["risk_budget"] = risk_budget / sd * price

        cands["max_position"] = float(_cfg(s, "RISK_MAX_POSITION_PCT", 0.10)) * equity
        cands["participation"] = max_order_value(
            adv_value_try, bar_value_try, float(_cfg(s, "RISK_MAX_PARTICIPATION", 0.05)))
        gross_open = sum(position_notional(p) for p in open_positions)
        cands["gross_budget"] = max(0.0, float(_cfg(s, "RISK_MAX_GROSS_EXPOSURE_PCT", 1.0)) * equity - gross_open)
        if cash is not None:
            cands["cash"] = max(0.0, float(cash))

        binding = min(cands, key=lambda k: cands[k])
        notional = cands[binding]
        qty = int(math.floor(notional / price / lot + 1e-9)) * lot
        if qty < 1:
            return SizingDecision(False, 0, 0.0, 0.0, [f"qty_below_one_lot(binding={binding})"],
                                  "rejected", cands)
        final_notional = qty * price
        risk_bps = qty * sd / equity * 1e4
        reasons.append(f"binding_constraint={binding}")
        return SizingDecision(True, qty, float(final_notional), float(risk_bps), reasons, binding, cands)
