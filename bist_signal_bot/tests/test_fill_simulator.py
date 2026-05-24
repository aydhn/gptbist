import pytest
import pandas as pd
from datetime import datetime
from bist_signal_bot.execution_sim.fill import FillSimulator
from bist_signal_bot.execution_sim.costs import TransactionCostModel
from bist_signal_bot.execution_sim.slippage import SlippageEstimator
from bist_signal_bot.execution_sim.liquidity import LiquidityAnalyzer
from bist_signal_bot.execution_sim.models import SimulatedOrder, SimulatedOrderSide, SimulatedOrderType, SimulatedFillStatus

@pytest.fixture
def fill_sim():
    return FillSimulator(TransactionCostModel(), SlippageEstimator(), LiquidityAnalyzer())

def test_fill_simulator_market_order(fill_sim):
    df = pd.DataFrame({"close": [10.0, 10.0], "volume": [100000, 100000]})
    order = SimulatedOrder(order_id="1", symbol="ASELS", side=SimulatedOrderSide.BUY, order_type=SimulatedOrderType.MARKET, quantity=100, reference_price=10.0, limit_price=None, requested_notional=1000, created_at=datetime.now())
    fill = fill_sim.simulate_fill(order, df)
    assert fill.status == SimulatedFillStatus.FILLED
    assert fill.filled_quantity == 100

def test_fill_simulator_limit_order_not_filled(fill_sim):
    df = pd.DataFrame({"close": [10.0, 10.0], "volume": [100000, 100000]})
    order = SimulatedOrder(order_id="1", symbol="ASELS", side=SimulatedOrderSide.BUY, order_type=SimulatedOrderType.LIMIT, quantity=100, reference_price=10.0, limit_price=9.0, requested_notional=1000, created_at=datetime.now())
    fill = fill_sim.simulate_fill(order, df)
    assert fill.status == SimulatedFillStatus.NOT_FILLED

def test_fill_simulator_partial_fill_low_liquidity(fill_sim):
    df = pd.DataFrame({"close": [10.0, 10.0], "volume": [10, 10]}) # turnover 100
    order = SimulatedOrder(order_id="1", symbol="ASELS", side=SimulatedOrderSide.BUY, order_type=SimulatedOrderType.MARKET, quantity=10, reference_price=10.0, limit_price=None, requested_notional=100, created_at=datetime.now())
    # ILLIQUID triggers no-fill logic
    fill = fill_sim.simulate_fill(order, df)
    assert fill.status == SimulatedFillStatus.NOT_FILLED
    assert fill.filled_quantity == 0.0

def test_fill_simulator_no_mutate_df(fill_sim):
    df = pd.DataFrame({"close": [10.0, 10.0], "volume": [100000, 100000]})
    df_copy = df.copy()
    order = SimulatedOrder(order_id="1", symbol="ASELS", side=SimulatedOrderSide.BUY, order_type=SimulatedOrderType.MARKET, quantity=100, reference_price=10.0, limit_price=None, requested_notional=1000, created_at=datetime.now())
    fill_sim.simulate_fill(order, df)
    pd.testing.assert_frame_equal(df, df_copy)
