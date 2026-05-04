import pytest
from datetime import datetime, UTC
import pandas as pd
from bist_signal_bot.backtesting.models import ExecutionPriceMode, BacktestConfig, BacktestOrder, BacktestOrderType
from bist_signal_bot.costs.models import CostScenario, OrderSide
from bist_signal_bot.costs.engine import TransactionCostEngine
from bist_signal_bot.backtesting.execution import BacktestExecutionModel

def get_dummy_data():
    dates = pd.date_range("2023-01-01", periods=3)
    df = pd.DataFrame({
        "open": [10.0, 11.0, 12.0],
        "close": [10.5, 11.5, 12.5]
    }, index=dates)
    return df

def test_execution_next_open():
    df = get_dummy_data()
    # Mocking cost engine / config
    class DummyCostEngine:
        pass

    class DummyConfig:
        scenario = CostScenario.BASE

    model = BacktestExecutionModel(DummyCostEngine(), DummyConfig())
    timestamp, price = model.get_execution_price(df, 0, ExecutionPriceMode.NEXT_OPEN)

    assert timestamp == df.index[1]
    assert price == 11.0

def test_execution_next_close():
    df = get_dummy_data()
    class DummyCostEngine:
        pass
    class DummyConfig:
        scenario = CostScenario.BASE

    model = BacktestExecutionModel(DummyCostEngine(), DummyConfig())
    timestamp, price = model.get_execution_price(df, 0, ExecutionPriceMode.NEXT_CLOSE)

    assert timestamp == df.index[1]
    assert price == 11.5

def test_execution_same_close():
    df = get_dummy_data()
    class DummyCostEngine:
        pass
    class DummyConfig:
        scenario = CostScenario.BASE

    model = BacktestExecutionModel(DummyCostEngine(), DummyConfig())
    timestamp, price = model.get_execution_price(df, 0, ExecutionPriceMode.SAME_CLOSE_FOR_RESEARCH_ONLY)

    assert timestamp == df.index[0]
    assert price == 10.5

def test_execution_no_next_bar():
    df = get_dummy_data()
    class DummyCostEngine:
        pass
    class DummyConfig:
        scenario = CostScenario.BASE

    model = BacktestExecutionModel(DummyCostEngine(), DummyConfig())
    with pytest.raises(ValueError, match="No next bar available for execution"):
        model.get_execution_price(df, 2, ExecutionPriceMode.NEXT_OPEN)

def test_quantity_from_notional():
    class DummyCostEngine:
        pass
    class DummyConfig:
        scenario = CostScenario.BASE

    model = BacktestExecutionModel(DummyCostEngine(), DummyConfig())
    qty1 = model.quantity_from_notional(notional=105.0, price=10.0, use_fractional=False)
    assert qty1 == 10.0 # Floor behavior

    qty2 = model.quantity_from_notional(notional=105.0, price=10.0, use_fractional=True)
    assert qty2 == 10.5

def test_create_fill():
    from bist_signal_bot.costs.models import TransactionCostBreakdown
    class DummyCostEngine:
        scenario = CostScenario.BASE
        def calculate_trade_cost(self, input_data):
                                    return TransactionCostBreakdown(
                input=input_data,
                effective_price=10.1,
                gross_notional=1000.0,
                commission=10.0,
                slippage=0.0,
                spread=0.0,
                transaction_tax=0.0,
                other_fees=0.0,
                total_cost=10.0,
                total_cost_bps=100.0,
                side=input_data.side,
                scenario=self.scenario
            )

    class DummyConfig:
        scenario = CostScenario.BASE

    model = BacktestExecutionModel(DummyCostEngine(), DummyConfig())
    order = BacktestOrder(
        symbol="ASELS",
        side=OrderSide.BUY,
        order_type=BacktestOrderType.MARKET,
        quantity=100.0,
        requested_price=10.0,
        requested_at=datetime.now(UTC),
        reason="TEST"
    )

    fill = model.create_fill(order, 10.0, datetime.now(UTC))
    assert fill.symbol == "ASELS"
    assert fill.price == 10.0
    assert fill.total_cost == 10.0
