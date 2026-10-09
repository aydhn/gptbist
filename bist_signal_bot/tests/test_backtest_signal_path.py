"""BacktestEngine obtains signals via StrategyEngine.run_strategy_on_data (no adapter). No real order sent."""
import numpy as np
import pandas as pd

from bist_signal_bot.backtesting.engine import BacktestEngine
from bist_signal_bot.costs.engine import TransactionCostEngine
from bist_signal_bot.strategies.engine import StrategyEngine


def _frame(n=420):
    idx = pd.bdate_range("2023-06-01", periods=n)
    t = np.arange(n)
    close = 100 + 0.08 * t + 12 * np.sin(t / 14)
    return pd.DataFrame({"open": np.r_[close[0], close[:-1]], "high": close + 1, "low": close - 1,
                         "close": close, "volume": np.full(n, 1e6)}, index=idx)


def _engine(settings_factory):
    s = settings_factory()
    return BacktestEngine(StrategyEngine(settings=s), TransactionCostEngine.from_settings(s), s), s


def test_default_statuses_accept_candidate_and_active(settings_factory):
    eng, _ = _engine(settings_factory)
    assert set(eng.build_default_config().trade_on_candidate_statuses) == {"ACTIVE", "CANDIDATE"}


def test_moving_average_trend_produces_trades_without_adapter(settings_factory):
    eng, s = _engine(settings_factory)
    s.RESEARCH_AUTO_LOG_BACKTEST = False
    res = eng.run_single_symbol("moving_average_trend", "AAA", _frame())
    assert len(res.trades) > 0
    assert res.metadata["signal_errors"] == 0
    assert not any("signal generation failed" in i for i in res.issues)


def test_failing_strategy_call_is_surfaced_not_swallowed(settings_factory):
    eng, s = _engine(settings_factory)
    s.RESEARCH_AUTO_LOG_BACKTEST = False

    def boom(**kw):
        raise RuntimeError("strategy exploded")
    eng.strategy_engine.run_strategy_on_data = boom
    res = eng.run_single_symbol("moving_average_trend", "AAA", _frame(60))
    assert res.metadata["signal_errors"] > 0
    assert any("signal generation failed" in i and "strategy exploded" in i for i in res.issues)
    assert len(res.trades) == 0
