from datetime import date
from types import SimpleNamespace

import pytest

from bist_signal_bot.paper.cash_interest import accrue_cash_interest, apply_cash_interest


def test_simple_interest_with_withholding():
    assert accrue_cash_interest(100000, 0.365, 10, withholding=0.15) == pytest.approx(100000 * 0.365 * 10 / 365 * 0.85)


def test_no_interest_on_nonpositive_cash_or_rate():
    assert accrue_cash_interest(0, 0.3, 5) == 0
    assert accrue_cash_interest(-5, 0.3, 5) == 0
    assert accrue_cash_interest(1000, 0.0, 5) == 0


def test_apply_stamps_first_then_credits_and_is_idempotent_per_day():
    acc = SimpleNamespace(cash=100000.0, equity=100000.0, metadata={})
    assert apply_cash_interest(acc, date(2026, 1, 1), 0.365) == 0
    amt = apply_cash_interest(acc, date(2026, 1, 11), 0.365)
    assert amt == pytest.approx(1000.0)
    assert acc.cash == pytest.approx(101000.0) and acc.equity == pytest.approx(101000.0)
    assert apply_cash_interest(acc, date(2026, 1, 11), 0.365) == 0
