"""Idle-cash interest for backtests (simulation only; no real order sent).

Reuses ``paper.cash_interest.accrue_cash_interest`` so the backtest and the paper ledger share ONE formula and
the same date semantics as ``apply_cash_interest``: the first call only stamps the date, later calls credit
interest for the calendar-day gap (weekends/holidays included) on the cash held at that moment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Iterable, Optional

import pandas as pd

from bist_signal_bot.paper.cash_interest import accrue_cash_interest

NO_ORDER = "No real order sent."


def _d(ts: Any) -> date:
    return pd.Timestamp(ts).date()


@dataclass
class CashParams:
    enabled: bool = True
    annual: float = 0.0
    withholding: float = 0.0

    @classmethod
    def from_settings(cls, settings: Any, enabled: Optional[bool] = None, annual: Optional[float] = None,
                      withholding: Optional[float] = None) -> "CashParams":
        g = lambda k, dflt: getattr(settings, k, dflt)  # noqa: E731
        return cls(
            enabled=bool(g("BACKTEST_CASH_INTEREST_ENABLED", True)) if enabled is None else bool(enabled),
            annual=float(g("BACKTEST_CASH_INTEREST_ANNUAL", g("PAPER_CASH_INTEREST_ANNUAL", 0.0))) if annual is None else float(annual),
            withholding=float(g("BACKTEST_CASH_INTEREST_WITHHOLDING", g("PAPER_CASH_INTEREST_WITHHOLDING", 0.0))) if withholding is None else float(withholding),
        )


@dataclass
class CashAccrual:
    """Stateful per-portfolio accrual: call ``step(portfolio, ts)`` once per bar (after fills, before mark)."""
    params: CashParams
    start_date: Optional[date] = None   # bars before this date (warm-up) neither stamp nor accrue
    last_date: Optional[date] = None
    total: float = 0.0
    history: list[tuple[Any, float]] = field(default_factory=list)  # (timestamp, cumulative interest)

    def step(self, portfolio: Any, ts: Any) -> float:
        day = _d(ts)
        amt = 0.0
        if self.params.enabled and (self.start_date is None or day >= self.start_date):
            if self.last_date is not None and day > self.last_date:
                amt = accrue_cash_interest(float(portfolio.cash), self.params.annual, (day - self.last_date).days,
                                           self.params.withholding)
                if amt > 0:
                    portfolio.cash = float(portfolio.cash) + amt
                    self.total += amt
            if self.last_date is None or day > self.last_date:
                self.last_date = day
        self.history.append((ts, self.total))
        return amt


def cash_benchmark_curve(dates: Iterable[Any], initial: float, params: CashParams) -> pd.Series:
    """Cash-only compounding of ``initial`` over the same dates (first date stamps, then per-gap credit)."""
    out, last, cash = {}, None, float(initial)
    for ts in dates:
        day = _d(ts)
        if last is not None and day > last and params.enabled:
            cash += accrue_cash_interest(cash, params.annual, (day - last).days, params.withholding)
        if last is None or day > last:
            last = day
        out[ts] = cash
    return pd.Series(out, dtype=float)


def excess_over_cash_pct(final_equity: float, initial: float, benchmark_final: float) -> float:
    """Strategy total return minus cash-only total return (percentage points)."""
    if not initial:
        return 0.0
    return (final_equity / initial - 1.0) * 100.0 - (benchmark_final / initial - 1.0) * 100.0
