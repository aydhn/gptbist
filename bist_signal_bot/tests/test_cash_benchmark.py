import math

import pandas as pd
import pytest

from bist_signal_bot.edge_validation.cash_benchmark import (
    alpha_over_cash, cash_equity_curve, daily_cash_returns, real_return)


def test_weekend_compounding():
    idx = pd.to_datetime(["2026-10-08", "2026-10-09", "2026-10-12"])  # Thu Fri Mon
    r = daily_cash_returns(idx, 0.37)
    assert math.isclose(r.iloc[2], 1.37 ** (3 / 365) - 1)
    assert r.iloc[2] > r.iloc[1]
    c = cash_equity_curve(idx, 0.37)
    assert math.isclose(c.iloc[-1], 1.37 ** (5 / 365))  # 1+1+3 days


def test_withholding():
    idx = pd.date_range("2026-01-01", periods=3)
    a = daily_cash_returns(idx, 0.30)
    b = daily_cash_returns(idx, 0.30, withholding=0.15)
    assert ((b / a) - 0.85).abs().max() < 1e-12


def test_alpha_over_cash():
    idx = pd.date_range("2026-01-01", periods=50, freq="B")
    cash = daily_cash_returns(idx, 0.37)
    s = cash + pd.Series([0.002, -0.0005] * 25, index=idx)
    out = alpha_over_cash(s, cash)
    assert out["n"] == 50 and out["excess_mean"] > 0 and out["excess_sharpe_annual"] > 0


def test_real_return_fails_without_cpi():
    idx = pd.date_range("2026-01-01", periods=3)
    with pytest.raises(ValueError):
        real_return(pd.Series([0.01] * 3, index=idx))
    cpi = pd.Series([0.03], index=pd.to_datetime(["2026-01-01"]))
    out = real_return(pd.Series([0.01] * 3, index=idx), cpi)
    assert (out < 0.01).all()
