import pytest
from datetime import datetime, UTC
import pandas as pd
from bist_signal_bot.costs.models import CostScenario
from bist_signal_bot.backtesting.models import (
    BacktestConfig, ExecutionPriceMode, BacktestResult, BacktestMode
)
from bist_signal_bot.core.exceptions import BacktestValidationError

def test_backtest_config_validation():
    # Should work
    config = BacktestConfig(
        initial_capital=1000.0,
        execution_price_mode=ExecutionPriceMode.NEXT_OPEN,
        commission_enabled=True,
        slippage_enabled=True,
        allow_short=False,
        max_position_size_pct=0.5,
        min_trade_notional=10.0,
        trade_on_candidate_statuses=["ACTIVE"],
        close_on_opposite_signal=True,
        close_on_flat_signal=False,
        one_position_per_symbol=True,
        use_fractional_shares=False,
        close_open_positions_at_end=True,
        scenario=CostScenario.BASE
    )
    assert config.initial_capital == 1000.0

def test_backtest_config_invalid_capital():
    with pytest.raises(BacktestValidationError, match="initial_capital must be > 0"):
        BacktestConfig(
            initial_capital=-100.0,
            execution_price_mode=ExecutionPriceMode.NEXT_OPEN,
            commission_enabled=True,
            slippage_enabled=True,
            allow_short=False,
            max_position_size_pct=0.5,
            min_trade_notional=10.0,
            trade_on_candidate_statuses=["ACTIVE"],
            close_on_opposite_signal=True,
            close_on_flat_signal=False,
            one_position_per_symbol=True,
            use_fractional_shares=False,
            close_open_positions_at_end=True,
            scenario=CostScenario.BASE
        )

def test_backtest_config_invalid_position_size():
    with pytest.raises(BacktestValidationError, match="max_position_size_pct must be between 0.0 and 1.0"):
        BacktestConfig(
            initial_capital=1000.0,
            execution_price_mode=ExecutionPriceMode.NEXT_OPEN,
            commission_enabled=True,
            slippage_enabled=True,
            allow_short=False,
            max_position_size_pct=1.5,
            min_trade_notional=10.0,
            trade_on_candidate_statuses=["ACTIVE"],
            close_on_opposite_signal=True,
            close_on_flat_signal=False,
            one_position_per_symbol=True,
            use_fractional_shares=False,
            close_open_positions_at_end=True,
            scenario=CostScenario.BASE
        )

def test_backtest_result_return_pct():
    config = BacktestConfig(
        initial_capital=100.0,
        execution_price_mode=ExecutionPriceMode.NEXT_OPEN,
        commission_enabled=True,
        slippage_enabled=True,
        allow_short=False,
        max_position_size_pct=0.5,
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
        portfolio_snapshots=[], # Empty -> returns initial_capital
        orders=[],
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        elapsed_seconds=1.0,
        issues=[]
    )
    assert res.total_return_pct() == 0.0
