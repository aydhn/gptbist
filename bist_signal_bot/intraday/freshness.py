"""Freshness check for the latest intraday bar."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel

from bist_signal_bot.intraday.sessions import (
    expected_bar_starts, last_completed_bar_start, to_istanbul,
)


class FreshnessResult(BaseModel):
    ok: bool
    reason: str
    lag_bars: int = 0


def check_freshness(last_bar_start: Optional[datetime], now: datetime, minutes: int,
                    data_delay_minutes: int = 15, max_lag_bars: int = 2,
                    vendor: str = "yahoo") -> FreshnessResult:
    if last_bar_start is None:
        return FreshnessResult(ok=False, reason="no_bars", lag_bars=-1)
    last = to_istanbul(last_bar_start)
    now = to_istanbul(now)
    target = last_completed_bar_start(now, minutes, data_delay_minutes, vendor=vendor)
    if target is None:
        return FreshnessResult(ok=False, reason="no_expected_bar", lag_bars=-1)
    if last >= target:
        return FreshnessResult(ok=True, reason="up_to_date", lag_bars=0)
    lag = 0
    d = last.date()
    while d <= target.date():
        lag += sum(1 for s in expected_bar_starts(d, minutes, vendor=vendor) if last < s <= target)
        d += timedelta(days=1)
    if lag > max_lag_bars:
        return FreshnessResult(ok=False, reason=f"stale: lag {lag} bars > {max_lag_bars}", lag_bars=lag)
    return FreshnessResult(ok=True, reason=f"within_tolerance: lag {lag} bars", lag_bars=lag)
