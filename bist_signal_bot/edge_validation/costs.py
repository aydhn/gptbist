"""BIST intraday transaction-cost model (research/paper only; no orders are ever sent).

One-way cost in bps of traded value:
  commission * (1 + BSMV)    BSMV (banking & insurance transaction tax) applies to the COMMISSION only
  + exchange fee             borsa + takas share (placeholder; verify with broker tariff)
  + half-spread              max(spread_proxy_bps, 0.5 * tick / price)  (tick = floor on the spread)
  + sqrt impact              impact_coef * sqrt(order_value / bar_volume_value), in PERCENT
                             (coef 0.1, participation 4% -> 0.1 * 0.2 = 0.02% = 2 bps)

Orders whose participation exceeds max_participation (or any short when allow_short is False)
are flagged not allowed; cost_bps then returns NaN.

Notes: the sell side carries NO stock transaction tax on BIST equities (VERIFY against current
legislation/broker tariff). Short selling is disabled by default (INTRADAY_ALLOW_SHORT=False).
All rates are placeholders configurable via config/defaults.py INTRADAY_* keys.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import numpy as np
import pandas as pd

from bist_signal_bot.core.logging_setup import get_logger

logger = get_logger(__name__)

_LOCAL_TICKS = ((20, 0.01), (50, 0.02), (100, 0.05), (250, 0.10), (500, 0.25), (1000, 0.50), (2500, 1.0))

try:  # reuse the shared BIST tick table when exposed
    from bist_signal_bot.intraday.sessions import _tick_for as _sess_tick_for
except Exception:  # pragma: no cover
    _sess_tick_for = None


def tick_size(price: float) -> float:
    """BIST equity tick for a price band (intraday.sessions table when available)."""
    if _sess_tick_for is not None:
        return float(_sess_tick_for(Decimal(str(price))))
    for upper, tick in _LOCAL_TICKS:
        if price < upper:
            return tick
    return 2.5


@dataclass(frozen=True)
class CostBreakdown:
    commission_bps: float
    bsmv_bps: float
    exchange_bps: float
    half_spread_bps: float
    impact_bps: float
    participation: float
    allowed: bool
    reason: str = ""

    @property
    def total_bps(self) -> float:
        return (self.commission_bps + self.bsmv_bps + self.exchange_bps
                + self.half_spread_bps + self.impact_bps)


class IntradayCostModel:
    def __init__(self, commission_bps: float = 5.0, bsmv_rate: float = 0.05,
                 exchange_fee_bps: float = 0.3, impact_coef: float = 0.1,
                 max_participation: float = 0.05, allow_short: bool = False,
                 spread_proxy_bps: float = 0.0):
        self.commission_bps = commission_bps
        self.bsmv_rate = bsmv_rate
        self.exchange_fee_bps = exchange_fee_bps
        self.impact_coef = impact_coef
        self.max_participation = max_participation
        self.allow_short = allow_short
        self.spread_proxy_bps = spread_proxy_bps

    @classmethod
    def from_settings(cls, settings=None) -> "IntradayCostModel":
        if settings is None:
            from bist_signal_bot.config.settings import get_settings
            settings = get_settings()
        g = lambda k: getattr(settings, k)  # noqa: E731
        return cls(float(g("INTRADAY_COMMISSION_BPS")), float(g("INTRADAY_BSMV_RATE")),
                   float(g("INTRADAY_EXCHANGE_FEE_BPS")), float(g("INTRADAY_SLIPPAGE_IMPACT_COEF")),
                   float(g("INTRADAY_MAX_PARTICIPATION")), bool(g("INTRADAY_ALLOW_SHORT")))

    def half_spread_bps(self, price: float) -> float:
        if not (price and price > 0 and math.isfinite(price)):
            return float("nan")
        return max(self.spread_proxy_bps, 0.5 * tick_size(price) / price * 1e4)

    def breakdown(self, price: float, order_value: float, bar_volume_value: float,
                  side: str = "buy") -> CostBreakdown:
        side = str(side).lower()
        comm = self.commission_bps
        bsmv = comm * self.bsmv_rate
        hs = self.half_spread_bps(price)
        if bar_volume_value is None or not bar_volume_value > 0:
            return CostBreakdown(comm, bsmv, self.exchange_fee_bps, hs, float("nan"),
                                 float("nan"), False, "no_bar_volume")
        part = float(order_value) / float(bar_volume_value)
        impact = self.impact_coef * math.sqrt(max(part, 0.0)) * 100.0
        allowed, reason = True, ""
        if side in ("short", "sell_short") and not self.allow_short:
            allowed, reason = False, "short_disabled"
        elif part > self.max_participation:
            allowed, reason = False, "participation_cap"
        return CostBreakdown(comm, bsmv, self.exchange_fee_bps, hs, impact, part, allowed, reason)

    def cost_bps(self, price: float, order_value: float, bar_volume_value: float,
                 side: str = "buy") -> float:
        """One-way total cost in bps; NaN if the order is not allowed."""
        b = self.breakdown(price, order_value, bar_volume_value, side)
        return b.total_bps if b.allowed else float("nan")

    def round_trip_bps(self, price: float, order_value: float, bar_volume_value: float,
                       exit_price: Optional[float] = None,
                       exit_bar_volume_value: Optional[float] = None) -> float:
        """Buy + sell cost in bps of notional; NaN if either leg is disallowed."""
        a = self.cost_bps(price, order_value, bar_volume_value, "buy")
        b = self.cost_bps(exit_price or price, order_value,
                          exit_bar_volume_value or bar_volume_value, "sell")
        return a + b

    def apply_costs(self, gross_returns, entry_prices, order_values, bar_volume_values,
                    exit_prices=None, exit_bar_volume_values=None):
        """Gross -> net per-trade fractional returns. Disallowed trades become NaN.

        Scalars broadcast. A pandas Series input returns a Series with the same index.
        """
        g = np.asarray(gross_returns, dtype=float)

        def bc(x):
            return np.broadcast_to(np.asarray(x, dtype=float), g.shape)

        ep, ov, bv = bc(entry_prices), bc(order_values), bc(bar_volume_values)
        xp = ep if exit_prices is None else bc(exit_prices)
        xv = bv if exit_bar_volume_values is None else bc(exit_bar_volume_values)
        cost = np.array([self.round_trip_bps(a, b, c, d, e) for a, b, c, d, e in
                         zip(ep.ravel(), ov.ravel(), bv.ravel(), xp.ravel(), xv.ravel())],
                        dtype=float).reshape(g.shape)
        net = g - cost / 1e4
        if isinstance(gross_returns, pd.Series):
            return pd.Series(net, index=gross_returns.index, name=gross_returns.name)
        return net


def liquidity_ok(avg_daily_value_try: float, min_value: float) -> bool:
    """True if average daily traded value (TRY) meets the minimum."""
    try:
        return bool(np.isfinite(avg_daily_value_try) and avg_daily_value_try >= min_value)
    except TypeError:
        return False
