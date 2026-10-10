"""BIST daily/multi-day transaction-cost model (research/paper only; no real order is ever sent).

Same ``apply_costs(gross, price, order_value, bar_value_try)`` call shape as ``IntradayCostModel`` so it can be
passed as ``cost_model=`` to ``CandidateGate``. Differences: ``bar_value_try`` is the AVERAGE DAILY VALUE (ADV, TRY)
and the sqrt-impact coefficient is recalibrated for daily horizons (bps = coef*100*sqrt(order/ADV), coef 0.5 ->
~11 bps at 5% of ADV). LONG-ONLY: shorts are disallowed (NaN).

Per leg (bps of traded value): commission + BSMV (BSMV applies to the COMMISSION only, same as IntradayCostModel,
so it is 0 when commission is 0) + exchange fee + half spread (tick floor) + sqrt impact.
Two scenarios are always meant to be reported: ``zero_commission`` (broker commission 0) and
``placeholder_commission`` (DAILY_COST_COMMISSION_PLACEHOLDER_BPS per leg). Rates are unverified placeholders.
Holding cost = interest forgone on cash while invested (see ``holding_cost_bps``).

Spread proxy (price/ADV dependent, UNVERIFIED placeholder): half spread = max(tick floor, spread_proxy_bps,
``spread_base_bps + spread_k_bps / sqrt(ADV / 1e6 TRY)``). ``from_settings`` reads DAILY_COST_SPREAD_PROXY_BPS_BASE /
DAILY_COST_SPREAD_PROXY_K_BPS (defaults 1.0 / 3.0; 0 / 0 or DAILY_LEGACY_SEMANTICS reproduces the old behaviour; the
plain constructor keeps 0 / 0). ``price_limit_flags`` (events column ``price_limit_flag``) disallow the entry (NaN).
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.costs import CostBreakdown, IntradayCostModel, liquidity_ok, tick_size  # noqa: F401

SCENARIOS = ("zero_commission", "placeholder_commission")


class DailyCostModel:
    def __init__(self, commission_bps: float = 0.0, bsmv_rate: float = 0.05, exchange_fee_bps: float = 0.29,
                 impact_coef: float = 0.5, max_participation: float = 0.05, spread_proxy_bps: float = 0.0,
                 cash_annual_rate: float = 0.37, cash_withholding: float = 0.0, scenario: str = "custom",
                 spread_base_bps: float = 0.0, spread_k_bps: float = 0.0):
        self.commission_bps = commission_bps
        self.bsmv_rate = bsmv_rate
        self.exchange_fee_bps = exchange_fee_bps
        self.impact_coef = impact_coef
        self.max_participation = max_participation
        self.spread_proxy_bps = spread_proxy_bps
        self.cash_annual_rate = cash_annual_rate
        self.cash_withholding = cash_withholding
        self.scenario = scenario
        self.spread_base_bps = float(spread_base_bps)
        self.spread_k_bps = float(spread_k_bps)
        self.supports_price_limit_flags = True  # CandidateGate/nav_returns feed the events' price_limit_flag column
        self.allow_short = False  # long-only, no leverage
        # reuse the intraday semantics for spread/impact/participation, with the daily impact coef
        self._core = IntradayCostModel(commission_bps, bsmv_rate, exchange_fee_bps, impact_coef,
                                       max_participation, False, spread_proxy_bps)

    @classmethod
    def from_settings(cls, settings=None, scenario: str = "zero_commission") -> "DailyCostModel":
        if scenario not in SCENARIOS:
            raise ValueError(f"scenario must be one of {SCENARIOS}, got {scenario!r}")
        if settings is None:
            from bist_signal_bot.config.settings import get_settings
            settings = get_settings()
        g = lambda k: getattr(settings, k)  # noqa: E731
        legacy = bool(getattr(settings, "DAILY_LEGACY_SEMANTICS", False))
        sb = 0.0 if legacy else float(getattr(settings, "DAILY_COST_SPREAD_PROXY_BPS_BASE", 1.0))
        sk = 0.0 if legacy else float(getattr(settings, "DAILY_COST_SPREAD_PROXY_K_BPS", 3.0))
        comm = 0.0 if scenario == "zero_commission" else float(g("DAILY_COST_COMMISSION_PLACEHOLDER_BPS"))
        return cls(comm, float(g("DAILY_COST_BSMV_RATE")), float(g("DAILY_COST_EXCHANGE_FEE_BPS")),
                   float(g("DAILY_COST_IMPACT_COEF")), float(g("DAILY_COST_MAX_PARTICIPATION")), 0.0,
                   float(g("CASH_BENCHMARK_ANNUAL_RATE")), float(g("CASH_BENCHMARK_WITHHOLDING")), scenario, sb, sk)

    def spread_proxy_for(self, bar_value_try: float) -> float:
        """Half-spread proxy (bps) for an ADV (TRY): max(constant, base + k/sqrt(ADV/1e6)); constant if no ADV."""
        sp = self.spread_proxy_bps
        if (self.spread_base_bps > 0 or self.spread_k_bps > 0) and np.isfinite(bar_value_try) and bar_value_try > 0:
            sp = max(sp, self.spread_base_bps + self.spread_k_bps / float(np.sqrt(bar_value_try / 1e6)))
        return sp

    # ---- per leg ----
    def breakdown(self, price: float, order_value: float, bar_value_try: float, side: str = "buy",
                  at_price_limit: bool = False) -> CostBreakdown:
        self._core.spread_proxy_bps = self.spread_proxy_for(bar_value_try)
        b = self._core.breakdown(price, order_value, bar_value_try, side)
        if b.allowed and at_price_limit:
            return CostBreakdown(b.commission_bps, b.bsmv_bps, b.exchange_bps, b.half_spread_bps,
                                 b.impact_bps, b.participation, False, "price_limit")
        return b

    def breakdown_dict(self, price: float, order_value: float, bar_value_try: float, side: str = "buy",
                       at_price_limit: bool = False) -> dict:
        b = self.breakdown(price, order_value, bar_value_try, side, at_price_limit)
        return {"commission_bps": b.commission_bps, "bsmv_bps": b.bsmv_bps, "exchange_bps": b.exchange_bps,
                "half_spread_bps": b.half_spread_bps, "impact_bps": b.impact_bps,
                "participation": b.participation, "allowed": b.allowed, "reason": b.reason,
                "total_bps": b.total_bps if b.allowed else float("nan"), "scenario": self.scenario}

    def cost_bps(self, price, order_value, bar_value_try, side="buy", at_price_limit=False) -> float:
        b = self.breakdown(price, order_value, bar_value_try, side, at_price_limit)
        return b.total_bps if b.allowed else float("nan")

    def round_trip_bps(self, price, order_value, bar_value_try, exit_price=None, exit_bar_value_try=None,
                       at_price_limit=False) -> float:
        a = self.cost_bps(price, order_value, bar_value_try, "buy", at_price_limit)
        b = self.cost_bps(exit_price or price, order_value, exit_bar_value_try or bar_value_try, "sell")
        return a + b

    def apply_costs(self, gross_returns, entry_prices, order_values, bar_value_try, exit_prices=None,
                    exit_bar_value_try=None, price_limit_flags=None):
        """Gross -> net per-trade fractional returns (trading costs only). Disallowed trades -> NaN."""
        g = np.asarray(gross_returns, dtype=float)

        def bc(x):
            return np.broadcast_to(np.asarray(x, dtype=float), g.shape)

        ep, ov, bv = bc(entry_prices), bc(order_values), bc(bar_value_try)
        xp = ep if exit_prices is None else bc(exit_prices)
        xv = bv if exit_bar_value_try is None else bc(exit_bar_value_try)
        fl = np.zeros(g.shape, dtype=bool) if price_limit_flags is None else \
            np.broadcast_to(np.asarray(price_limit_flags, dtype=bool), g.shape)
        cost = np.array([self.round_trip_bps(a, b, c, d, e, bool(f)) for a, b, c, d, e, f in
                         zip(ep.ravel(), ov.ravel(), bv.ravel(), xp.ravel(), xv.ravel(), fl.ravel())],
                        dtype=float).reshape(g.shape)
        net = g - cost / 1e4
        if isinstance(gross_returns, pd.Series):
            return pd.Series(net, index=gross_returns.index, name=gross_returns.name)
        return net

    # ---- holding / cash ----
    def holding_cost_bps(self, days: float, annual_rate: Optional[float] = None,
                         withholding: Optional[float] = None, day_count: int = 365) -> float:
        """Opportunity cost (bps) of being invested for `days` calendar days instead of in cash
        (net-of-withholding compounded cash interest forgone)."""
        r = self.cash_annual_rate if annual_rate is None else annual_rate
        w = self.cash_withholding if withholding is None else withholding
        if days <= 0 or r <= 0:
            return 0.0
        gross = (1.0 + r) ** (days / day_count) - 1.0
        return gross * (1.0 - min(max(w, 0.0), 1.0)) * 1e4

    def net_vs_cash(self, gross, days, price=None, order_value=None, bar_value_try=None,
                    annual_rate=None, withholding=None, day_count: int = 365):
        """Excess-over-cash fractional return: gross - round-trip trading cost (if price info given) - cash
        interest forgone. NaN if the trade is disallowed."""
        hold = self.holding_cost_bps(days, annual_rate, withholding, day_count) / 1e4
        trade = 0.0
        if price is not None and order_value is not None and bar_value_try is not None:
            trade = self.round_trip_bps(price, order_value, bar_value_try) / 1e4
        return gross - trade - hold
