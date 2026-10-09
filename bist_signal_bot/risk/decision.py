"""Final pre-trade decision layer (paper/research only).

Pipeline for new entries: kill switch/guard -> session -> liquidity/sizing -> portfolio
limits -> expected-edge vs round-trip-cost sanity. Reduce-only exits bypass sizing/limits/
session/cost checks (risk-reducing orders are never blocked) but are kill-switch aware.

No real order sent.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from bist_signal_bot.intraday.sessions import (
    CONTINUOUS_OPEN, OPENING_AUCTION_COLLECT, closing_auction_window, session_bounds, to_istanbul,
)

logger = logging.getLogger(__name__)
NO_ORDER = "No real order sent."


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _cfg(settings: Any, key: str, default: Any) -> Any:
    try:
        v = getattr(settings, key, default)
    except Exception:
        return default
    return default if v is None else v


@dataclass
class Decision:
    allowed: bool
    qty: float = 0
    notional: float = 0.0
    reasons: list[str] = field(default_factory=list)
    sizing: Any = None
    limits: Any = None
    guard_state: dict = field(default_factory=dict)
    no_real_order_sent: bool = True
    note: str = NO_ORDER

    def summary(self) -> str:
        return (f"allowed={self.allowed} qty={self.qty} notional={self.notional:.2f} "
                f"reasons={','.join(self.reasons) or '-'} | {NO_ORDER}")


class DecisionLayer:
    def __init__(self, settings: Any, sizer: Any, limits: Any, guard: Any, cost_model: Any = None):
        self.settings = settings
        self.sizer = sizer
        self.limits = limits
        self.guard = guard
        if cost_model is None:
            try:
                from bist_signal_bot.edge_validation.costs import IntradayCostModel
                cost_model = IntradayCostModel.from_settings(settings)
            except Exception:
                from bist_signal_bot.edge_validation.costs import IntradayCostModel
                cost_model = IntradayCostModel()
        self.cost_model = cost_model

    # ------------------------------------------------------------------ helpers
    def _reject(self, reasons: list[str], guard_state: dict, audit: bool = False, **kw) -> Decision:
        d = Decision(False, 0, 0.0, reasons, guard_state=guard_state, **kw)
        logger.info("decision REJECT %s", d.summary())
        if audit:
            self._audit(reasons, guard_state)
        return d

    def _audit(self, reasons: list[str], guard_state: dict) -> None:
        try:
            self.guard._audit_event("RISK_DECISION_REJECTED", "Decision rejected by guard/kill switch: "
                                    + ",".join(reasons), "DEBUG",
                                    {"reasons": reasons, "guard_state": guard_state.get("state")})
        except Exception:
            pass

    def _session_reason(self, now: datetime) -> Optional[str]:
        now = to_istanbul(now)
        d = now.date()
        bounds = session_bounds(d)
        if bounds is None:
            return "market_closed"
        block_auction = bool(_cfg(self.settings, "RISK_BLOCK_AUCTION_ENTRIES", True))
        if block_auction:
            cw = closing_auction_window(d)
            if cw and cw[0] <= now < cw[1]:
                return "auction_window_entry_blocked"
            o_start = now.replace(hour=OPENING_AUCTION_COLLECT[0].hour, minute=OPENING_AUCTION_COLLECT[0].minute,
                                  second=0, microsecond=0)
            o_end = now.replace(hour=CONTINUOUS_OPEN.hour, minute=CONTINUOUS_OPEN.minute, second=0, microsecond=0)
            if o_start <= now < o_end:
                return "auction_window_entry_blocked"
        if not (bounds[0] <= now < bounds[1]):
            return "market_closed"
        return None

    def _expected_edge_bps(self, signal: Any, edge_stats: Any) -> Optional[float]:
        explicit = _get(signal, "expected_edge_bps")
        if explicit is not None:
            return float(explicit)
        base = _get(edge_stats, "expected_edge_bps")
        if base is None:
            base = _get(edge_stats, "mean_gross_bps")
        if base is None:
            return None
        conf = _get(signal, "confidence")
        conf = 1.0 if conf is None else min(max(float(conf), 0.0), 1.0)
        return float(base) * conf

    # ------------------------------------------------------------------ main
    def decide(self, signal: Any, context: dict) -> Decision:
        ctx = context or {}
        now = ctx.get("now") or datetime.now()
        reduce_only = bool(ctx.get("reduce_only") or _get(signal, "reduce_only", False))
        symbol = _get(signal, "symbol")
        price = float(ctx.get("price") if ctx.get("price") is not None else (_get(signal, "price") or 0.0))
        guard_state = self.guard.snapshot() if hasattr(self.guard, "snapshot") else {}

        # 1) exits: risk-reducing, never blocked
        if reduce_only:
            qty = ctx.get("qty") if ctx.get("qty") is not None else _get(signal, "qty", 0)
            reasons = ["reduce_only_exit"]
            if self.guard.kill_switch_active() or guard_state.get("state") == "HALTED_FOR_DAY":
                reasons.append("exit_allowed_despite_halt")
            d = Decision(True, qty, float(qty or 0) * price, reasons, guard_state=guard_state)
            logger.debug("decision EXIT %s", d.summary())
            return d

        # 2) kill switch / guard
        ok, why = self.guard.can_open_new_position(now)
        guard_state = self.guard.snapshot() if hasattr(self.guard, "snapshot") else guard_state
        if not ok:
            return self._reject([why], guard_state, audit=True)

        # 3) session
        sr = self._session_reason(now)
        if sr:
            return self._reject([sr], guard_state)

        # 4) liquidity / sizing
        equity = float(ctx.get("equity") or 0.0)
        edge_stats = ctx.get("edge_stats")
        open_positions = ctx.get("open_positions") or []
        sizing = self.sizer.size(
            signal_confidence=float(_get(signal, "confidence", 0.0) or 0.0), price=price, equity=equity,
            asset_vol_annual=ctx.get("asset_vol_annual"), adv_value_try=ctx.get("adv_value_try"),
            bar_value_try=ctx.get("bar_value_try"), spread_bps=ctx.get("spread_bps"),
            edge_stats=edge_stats, open_positions=open_positions, settings=self.settings)
        if not sizing.allowed or not sizing.qty:
            return self._reject(["sizing_rejected"] + list(sizing.reasons), guard_state, sizing=sizing)
        notional = float(sizing.notional or sizing.qty * price)

        # 5) portfolio limits
        order = {"symbol": symbol, "side": "BUY", "qty": sizing.qty, "price": price, "notional": notional}
        lim = self.limits.check(order, open_positions, equity, ctx.get("sector_map"),
                                ctx.get("corr_matrix"), self.settings)
        if not lim.allowed:
            return self._reject(["portfolio_limit"] + list(lim.reasons), guard_state, sizing=sizing, limits=lim)

        # 6) expected edge vs round-trip cost
        edge = self._expected_edge_bps(signal, edge_stats)
        if edge is None or not math.isfinite(edge):
            return self._reject(["no_edge_estimate"], guard_state, sizing=sizing, limits=lim)
        rt = self.cost_model.round_trip_bps(price, notional, float(ctx.get("bar_value_try") or 0.0))
        if rt is None or not math.isfinite(rt):
            return self._reject(["cost_model_disallowed"], guard_state, sizing=sizing, limits=lim)
        ratio = float(_cfg(self.settings, "RISK_MIN_EDGE_TO_COST_RATIO", 1.5))
        if edge < ratio * rt:
            return self._reject([f"edge_below_cost:{edge:.1f}bps<{ratio:g}x{rt:.1f}bps"], guard_state,
                                sizing=sizing, limits=lim)

        d = Decision(True, sizing.qty, notional, ["approved"] + list(sizing.reasons), sizing, lim, guard_state)
        logger.debug("decision ALLOW %s", d.summary())
        return d
