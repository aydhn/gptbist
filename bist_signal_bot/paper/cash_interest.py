"""Idle-cash interest accrual for the paper ledger (simulation only; no real order sent)."""

from __future__ import annotations

from datetime import date


def accrue_cash_interest(cash: float, annual_rate: float, days: int, withholding: float = 0.0,
                         day_count: int = 365, compound: bool = False) -> float:
    """Net interest earned on `cash` over `days` calendar days. Never negative, never on non-positive cash."""
    if cash <= 0 or annual_rate <= 0 or days <= 0:
        return 0.0
    if compound:
        gross = cash * ((1.0 + annual_rate) ** (days / day_count) - 1.0)
    else:
        gross = cash * annual_rate * days / day_count
    return gross * (1.0 - min(max(withholding, 0.0), 1.0))


def apply_cash_interest(account, today: date, annual_rate: float, withholding: float = 0.0) -> float:
    """Accrue interest since account.metadata['last_interest_date'] on account.cash (mutates cash/equity/metadata).

    First call only stamps the date. Returns the credited amount."""
    last = account.metadata.get("last_interest_date")
    account.metadata["last_interest_date"] = today.isoformat()
    if not last:
        return 0.0
    days = (today - date.fromisoformat(last)).days
    amount = accrue_cash_interest(float(account.cash), annual_rate, days, withholding)
    if amount > 0:
        account.cash = float(account.cash) + amount
        account.equity = float(account.equity) + amount
        account.metadata["interest_earned_total"] = float(account.metadata.get("interest_earned_total", 0.0)) + amount
    return amount
