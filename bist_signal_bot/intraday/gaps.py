"""Intraday bar gap detection against the expected session grid (no archive dependency)."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable

from pydantic import BaseModel, Field

from bist_signal_bot.intraday.sessions import expected_bar_starts, is_trading_day, to_istanbul

HALT_MIN_RUN = 3


class GapReport(BaseModel):
    day: date
    minutes: int
    expected_count: int = 0
    present_count: int = 0
    missing: list[datetime] = Field(default_factory=list)
    coverage: float = 1.0
    suspected_halt_runs: list[list[datetime]] = Field(default_factory=list)


def detect_gaps(bars_ts: Iterable[datetime], day: date, minutes: int,
                midday_single_price: bool = False, vendor: str = "yahoo") -> GapReport:
    expected = expected_bar_starts(day, minutes, midday_single_price, vendor=vendor)
    present = {to_istanbul(t) for t in bars_ts} & set(expected)
    missing = [s for s in expected if s not in present]
    idx = [i for i, s in enumerate(expected) if s in present]
    runs: list[list[datetime]] = []
    cur: list[datetime] = []
    if idx:
        for i in range(idx[0], idx[-1] + 1):
            s = expected[i]
            if s in present:
                if len(cur) >= HALT_MIN_RUN:
                    runs.append(cur)
                cur = []
            else:
                cur.append(s)
    coverage = (len(present) / len(expected)) if expected else 1.0
    return GapReport(day=day, minutes=minutes, expected_count=len(expected),
                     present_count=len(present), missing=missing,
                     coverage=coverage, suspected_halt_runs=runs)


def detect_gaps_range(bars_ts: Iterable[datetime], start: date, end: date, minutes: int,
                      midday_single_price: bool = False, vendor: str = "yahoo") -> list[GapReport]:
    """One report per trading day in [start, end]; non-trading days are skipped."""
    by_day: dict[date, list[datetime]] = {}
    for t in bars_ts:
        t = to_istanbul(t)
        by_day.setdefault(t.date(), []).append(t)
    out: list[GapReport] = []
    d = start
    while d <= end:
        if is_trading_day(d):
            out.append(detect_gaps(by_day.get(d, []), d, minutes, midday_single_price, vendor))
        d += timedelta(days=1)
    return out
