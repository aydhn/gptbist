"""Idle-cash interest in backtest / evidence replay / paper-vs-backtest. Offline. No real order sent."""
from datetime import date

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.backtesting.cash import CashAccrual, CashParams, cash_benchmark_curve
from bist_signal_bot.backtesting.engine import BacktestEngine
from bist_signal_bot.costs.engine import TransactionCostEngine
from bist_signal_bot.evidence.compare import compare_paper_backtest
from bist_signal_bot.evidence.replay import replay_paper
from bist_signal_bot.paper.cash_interest import accrue_cash_interest
from bist_signal_bot.strategies.engine import StrategyEngine

ANNUAL, WH = 0.365, 0.15


def _frame(n=120, flat=True, seed=0):
    idx = pd.bdate_range("2024-01-01", periods=n)
    t = np.arange(n)
    close = np.full(n, 100.0) if flat else 100 + 0.08 * t + 12 * np.sin(t / 14 + seed)
    return pd.DataFrame({"open": np.r_[close[0], close[:-1]], "high": close + 1, "low": close - 1,
                         "close": close, "volume": np.full(n, 1e6)}, index=idx)


def _engine(settings_factory, enabled=True):
    s = settings_factory()
    s.RESEARCH_AUTO_LOG_BACKTEST = False
    eng = BacktestEngine(StrategyEngine(settings=s), TransactionCostEngine.from_settings(s), s)
    eng.cash_interest_enabled, eng.cash_interest_annual, eng.cash_interest_withholding = enabled, ANNUAL, WH
    return eng, s


def _pure_cash(dates, cash0):
    cash, last = cash0, None
    for d in dates:
        d = pd.Timestamp(d).date()
        if last is not None:
            cash += accrue_cash_interest(cash, ANNUAL, (d - last).days, WH)
        last = d
    return cash


def test_flat_strategy_equals_pure_cash_compounding(settings_factory):
    eng, _ = _engine(settings_factory)
    res = eng.run_single_symbol("moving_average_trend", "AAA", _frame())
    assert len(res.trades) == 0
    expected = _pure_cash(_frame().index, res.config.initial_capital)
    assert res.final_equity() == pytest.approx(expected)
    assert res.cash_interest_total == pytest.approx(expected - res.config.initial_capital)
    assert res.cash_interest_total > 0
    # equity ex cash is flat; strategy return == cash benchmark -> zero alpha
    assert res.equity_curve_ex_cash.iloc[-1] == pytest.approx(res.config.initial_capital)
    assert res.excess_over_cash == pytest.approx(0.0, abs=1e-9)
    assert res.cash_benchmark_return_pct == pytest.approx(res.total_return_pct())


def test_weekend_gap_accrues_three_days():
    class P:  # minimal portfolio
        cash = 100_000.0
    acc = CashAccrual(CashParams(True, ANNUAL, 0.0))
    p = P()
    assert acc.step(p, pd.Timestamp("2024-01-05")) == 0.0          # Friday: stamps only
    amt = acc.step(p, pd.Timestamp("2024-01-08"))                   # Monday: 3 calendar days
    assert amt == pytest.approx(100_000 * ANNUAL * 3 / 365)
    amt2 = acc.step(p, pd.Timestamp("2024-01-09"))                  # Tuesday: 1 day, on compounded cash
    assert amt2 == pytest.approx(p.cash / (1 + amt2 / (p.cash - amt2)) * ANNUAL / 365, rel=1e-6)
    bench = cash_benchmark_curve(pd.to_datetime(["2024-01-05", "2024-01-08", "2024-01-09"]), 100_000.0, CashParams(True, ANNUAL, 0.0))
    assert bench.iloc[-1] == pytest.approx(p.cash)


def test_interest_off_leaves_results_unchanged(settings_factory):
    on_eng, _ = _engine(settings_factory, enabled=False)
    res = on_eng.run_single_symbol("moving_average_trend", "AAA", _frame(420, flat=False))
    assert len(res.trades) > 0
    assert res.cash_interest_total == 0.0
    assert res.excess_over_cash == pytest.approx(res.total_return_pct())
    assert res.cash_benchmark_return_pct == 0.0
    pd.testing.assert_series_equal(res.equity_curve_ex_cash, res.equity_curve["equity"], check_names=False)
    # same trades with interest on (interest never changes signals), but equity is higher
    eng2, _ = _engine(settings_factory, enabled=True)
    res2 = eng2.run_single_symbol("moving_average_trend", "AAA", _frame(420, flat=False))
    assert len(res2.trades) == len(res.trades)
    assert res2.final_equity() > res.final_equity()
    assert res2.final_equity() - res.final_equity() == pytest.approx(res2.cash_interest_total, rel=0.2)


def test_trade_from_skips_warmup_interest(settings_factory):
    eng, _ = _engine(settings_factory)
    df = _frame()
    eng.trade_from = df.index[60].date()
    res = eng.run_single_symbol("moving_average_trend", "AAA", df)
    assert res.cash_interest_total == pytest.approx(_pure_cash(df.index[60:], res.config.initial_capital) - res.config.initial_capital)


def test_replay_flat_equals_pure_cash(settings_factory):
    s = settings_factory()
    s.PAPER_CASH_INTEREST_ANNUAL, s.PAPER_CASH_INTEREST_WITHHOLDING = ANNUAL, WH
    st, en = date(2024, 2, 1), date(2024, 5, 31)
    r = replay_paper("moving_average_trend", ["AAA"], st, en, settings=s, frames={"AAA": _frame()}, cash_interest=True)
    assert not r.trades and r.cash_interest_enabled
    assert r.final_equity == pytest.approx(r.cash_benchmark.iloc[-1])
    assert r.cash_interest_total == pytest.approx(r.final_equity - r.initial_cash)
    assert r.excess_over_cash_pct == pytest.approx(0.0, abs=1e-9)
    off = replay_paper("moving_average_trend", ["AAA"], st, en, settings=s, frames={"AAA": _frame()}, cash_interest=False)
    assert off.final_equity == pytest.approx(off.initial_cash) and off.cash_interest_total == 0.0


def test_compare_includes_interest_on_both_sides(settings_factory, tmp_data_dir):
    s = settings_factory()
    s.PAPER_CASH_INTEREST_ANNUAL, s.PAPER_CASH_INTEREST_WITHHOLDING = ANNUAL, WH
    st, en = date(2024, 2, 1), date(2024, 5, 31)
    frames = {"AAA": _frame(), "BBB": _frame()}
    on = compare_paper_backtest("moving_average_trend", ["AAA", "BBB"], st, en, settings=s, frames=frames, cash_interest=True, save=True)
    assert on.cash_interest_enabled and on.paper_cash_interest_total > 0
    assert on.paper_cash_interest_total == pytest.approx(on.backtest_cash_interest_total, rel=1e-3)  # paper skips BIST holidays -> slightly fewer compounding steps
    assert abs(on.return_diff_pct_points) < 0.01
    assert on.paper_excess_over_cash_pct == pytest.approx(0.0, abs=0.01)
    assert any("cash interest" in a for a in on.attribution)
    assert "alpha over cash" in open(on.markdown_path, encoding="utf-8").read()
    assert "No real order sent." in on.disclaimer
    off = compare_paper_backtest("moving_average_trend", ["AAA", "BBB"], st, en, settings=s, frames=frames, cash_interest=False, save=False)
    assert off.paper_cash_interest_total == 0.0 and off.backtest_cash_interest_total == 0.0
    assert abs(off.paper_total_return_pct) < 1e-9
