import pytest
from datetime import datetime, UTC
import pandas as pd
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategies.engine import StrategyEngine
from bist_signal_bot.costs.engine import TransactionCostEngine
from bist_signal_bot.backtesting.engine import BacktestEngine
from bist_signal_bot.backtesting.models import ExecutionPriceMode
from bist_signal_bot.data.models import MarketDataFrame
from bist_signal_bot.data.mock_provider import MockMarketDataProvider

def test_backtest_engine_moving_average_trend():
    # Setup
    settings = Settings()
    strategy_engine = StrategyEngine(settings)
    cost_engine = TransactionCostEngine.from_settings(settings)

    engine = BacktestEngine(strategy_engine, cost_engine, settings)

    provider = MockMarketDataProvider(rows=100)
    mdf = provider.fetch_one("ASELS", "1d")

    config = engine.build_default_config()
    config.commission_enabled = False
    config.slippage_enabled = False
    config.execution_price_mode = ExecutionPriceMode.NEXT_OPEN

    params = {"fast_window": 5, "slow_window": 10}

    res = engine.run_single_symbol("moving_average_trend", "ASELS", mdf, params, config)

    assert res.symbol == "ASELS"
    assert res.strategy_name == "moving_average_trend"
    assert not res.equity_curve.empty
    assert "equity" in res.equity_curve.columns
    assert res.final_equity() > 0

def test_backtest_batch_symbols():
    settings = Settings()
    strategy_engine = StrategyEngine(settings)
    cost_engine = TransactionCostEngine.from_settings(settings)
    engine = BacktestEngine(strategy_engine, cost_engine, settings)

    provider = MockMarketDataProvider(rows=50)
    data_dict = {
        "ASELS": provider.fetch_one("ASELS", "1d"),
        "THYAO": provider.fetch_one("THYAO", "1d")
    }

    config = engine.build_default_config()
    res_dict = engine.run_batch_symbols("moving_average_trend", data_dict, {}, config)

    assert len(res_dict) == 2
    assert "ASELS" in res_dict
    assert "THYAO" in res_dict
    assert res_dict["ASELS"].symbol == "ASELS"
    assert res_dict["THYAO"].symbol == "THYAO"
