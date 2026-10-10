"""Pure daily-bar exit rules: fixed stop, trailing stop, time exit (long, reduce-only, paper/simulation only).

Daily semantics (no same-bar look-ahead): rules are evaluated on the CLOSE of bar t and the exit executes at the
OPEN of bar t+1. The trailing stop is the highest close since entry times (1 - trail_pct) and only ratchets up.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class DailyExit:
    reason: str            # FIXED_STOP | TRAILING_STOP | TIME_EXIT | NONE
    trigger_idx: int       # bar whose close triggered the rule (-1 if none)
    exec_idx: int          # bar whose open executes the exit (-1 if none / beyond data)
    exec_price: float | None
    stop_level: float | None   # effective stop at the last evaluated bar
    reduce_only: bool = True


def scan_daily_exit(opens: Sequence[float], closes: Sequence[float], entry_idx: int, *,
                    stop_price: float | None = None, trail_pct: float | None = None,
                    max_hold_sessions: int | None = None) -> DailyExit:
    """Entry is assumed filled at the open of ``entry_idx``; its own close is the first evaluated bar."""
    n = len(closes)
    if len(opens) != n:
        raise ValueError("opens and closes must have equal length")
    if trail_pct is not None and not 0 < trail_pct < 1:
        raise ValueError("trail_pct must be in (0, 1)")
    hw = -math.inf
    level: float | None = None
    for t in range(entry_idx, n):
        c = closes[t]
        if not math.isfinite(c):
            continue
        prev_level = level
        trail = None
        if trail_pct is not None:
            hw = max(hw, c)
            trail = hw * (1 - trail_pct)
        cands = [x for x in (stop_price, trail) if x is not None]
        new_level = max(cands) if cands else None
        if prev_level is not None and new_level is not None:
            new_level = max(new_level, prev_level)  # ratchet: never lower
        # test against the level in force BEFORE this close raised it
        test = prev_level if prev_level is not None else new_level
        if test is not None and c <= test:
            reason = "TRAILING_STOP" if (trail is not None and test > (stop_price or -math.inf)) else "FIXED_STOP"
            return _mk(reason, t, opens, n, test)
        level = new_level
        if max_hold_sessions is not None and (t - entry_idx + 1) >= max_hold_sessions:
            return _mk("TIME_EXIT", t, opens, n, level)
    return DailyExit("NONE", -1, -1, None, level)


def _mk(reason, t, opens, n, level) -> DailyExit:
    x = t + 1
    if x < n and math.isfinite(opens[x]) and opens[x] > 0:
        return DailyExit(reason, t, x, float(opens[x]), level)
    return DailyExit(reason, t, -1, None, level)
