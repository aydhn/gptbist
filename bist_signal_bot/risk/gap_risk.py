"""Gap / daily price-limit risk for protective exits (pure, paper/simulation only - no orders are sent).

Reuses the BIST tick/limit logic of ``intraday.sessions.daily_price_limits_array``; nothing is duplicated.
Long-only semantics for the sell-stop (exits are reduce-only); SHORT is mirrored for completeness.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..intraday.sessions import daily_price_limits_array

FILLED = "FILLED"
DEFERRED = "DEFERRED"          # locked limit move: exit cannot fill this session
NOT_TRIGGERED = "NOT_TRIGGERED"


@dataclass(frozen=True)
class GapExitResult:
    status: str
    price: float | None
    gapped_through: bool
    reason: str


def gap_exit_fill(prev_close: float, open: float, stop_price: float, limit_pct: float,  # noqa: A002
                  side: str = "LONG") -> GapExitResult:
    """Realistic fill of a protective stop at the session open.

    * open gaps THROUGH the stop (LONG: open <= stop) -> FILLED at the open (worse than the stop);
    * open locked at the limit in the exit direction (LONG: open <= limit-down floor) -> DEFERRED (no counterparty);
    * otherwise open did not breach the stop -> NOT_TRIGGERED at the open (caller keeps intraday/normal stop logic,
      a stop reached later in the session fills at ``stop_price``: see ``price`` = stop_price, gapped_through False).
    """
    s = str(getattr(side, "value", side)).upper()
    if s not in ("LONG", "SHORT"):
        raise ValueError(f"side must be LONG or SHORT, got {side!r}")
    vals = (prev_close, open, stop_price, limit_pct)
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in vals) or min(prev_close, open, stop_price) <= 0:
        return GapExitResult(DEFERRED, None, False, "invalid_prices")
    lo, hi = daily_price_limits_array(prev_close, limit_pct)
    lo, hi = float(lo), float(hi)
    eps = 1e-9
    if s == "LONG":
        if open <= lo * (1 + eps):
            return GapExitResult(DEFERRED, None, True, "locked_limit_down")
        if open <= stop_price:
            return GapExitResult(FILLED, float(open), True, "gap_through_stop")
    else:
        if open >= hi * (1 - eps):
            return GapExitResult(DEFERRED, None, True, "locked_limit_up")
        if open >= stop_price:
            return GapExitResult(FILLED, float(open), True, "gap_through_stop")
    return GapExitResult(NOT_TRIGGERED, float(stop_price), False, "no_gap")
