import pytest
from datetime import datetime, UTC
import pandas as pd
from bist_signal_bot.backtesting.models import (
    BacktestTrade,
    PortfolioSnapshot,
    BacktestResult,
    BacktestConfig,
    ExecutionPriceMode,
    BacktestMode
)
from bist_signal_bot.costs.models import CostScenario
from bist_signal_bot.signals.models import SignalDirection
from bist_signal_bot.backtesting.reports import (
    build_equity_curve_dataframe,
    build_trades_dataframe,
    basic_backtest_summary
)

def test_build_equity_curve_dataframe():
    snapshots = [
        PortfolioSnapshot(timestamp=datetime(2023, 1, 1, tzinfo=UTC), cash=100.0, position_value=0.0, equity=100.0, gross_exposure=0.0, net_exposure=0.0, open_positions=0),
        PortfolioSnapshot(timestamp=datetime(2023, 1, 2, tzinfo=UTC), cash=50.0, position_value=60.0, equity=110.0, gross_exposure=60.0, net_exposure=60.0, open_positions=1)
    ]
    df = build_equity_curve_dataframe(snapshots)
    assert not df.empty
    assert "equity" in df.columns
    assert len(df) == 2
    assert df.iloc[1]["equity"] == 110.0

def test_build_trades_dataframe():
    trades = [
        BacktestTrade(
            symbol="ASELS",
            entry_time=datetime(2023, 1, 1, tzinfo=UTC),
            exit_time=datetime(2023, 1, 2, tzinfo=UTC),
            side=SignalDirection.LONG,
            quantity=10.0,
            entry_price=10.0,
            exit_price=11.0,
            entry_cost=1.0,
            exit_cost=1.0,
            gross_pnl=10.0,
            net_pnl=8.0,
            return_pct=8.0,
            bars_held=1,
            entry_reason="TEST_IN",
            exit_reason="TEST_OUT"
        )
    ]
    df = build_trades_dataframe(trades)
    assert not df.empty
    assert "symbol" in df.columns
    assert len(df) == 1
    assert df.iloc[0]["net_pnl"] == 8.0

def test_basic_backtest_summary():
    config = BacktestConfig(
        initial_capital=1000.0,
        execution_price_mode=ExecutionPriceMode.NEXT_OPEN,
        commission_enabled=False,
        slippage_enabled=False,
        allow_short=False,
        max_position_size_pct=1.0,
        min_trade_notional=10.0,
        trade_on_candidate_statuses=["ACTIVE"],
        close_on_opposite_signal=True,
        close_on_flat_signal=False,
        one_position_per_symbol=True,
        use_fractional_shares=False,
        close_open_positions_at_end=True,
        scenario=CostScenario.BASE
    )
    res = BacktestResult(
        strategy_name="test",
        mode=BacktestMode.SINGLE_SYMBOL,
        config=config,
        trades=[],
        fills=[],
        portfolio_snapshots=[],
        orders=[],
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        elapsed_seconds=1.0,
        issues=[]
    )
    summary = basic_backtest_summary(res)
    assert summary["strategy_name"] == "test"
    assert summary["initial_capital"] == 1000.0
    assert summary["final_equity"] == 1000.0
    assert summary["execution_mode"] == "NEXT_OPEN"
