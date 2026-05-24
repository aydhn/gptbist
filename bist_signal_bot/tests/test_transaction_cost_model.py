import pytest
from datetime import datetime
from bist_signal_bot.execution_sim.costs import TransactionCostModel
from bist_signal_bot.execution_sim.models import SimulatedOrder, SimulatedOrderSide, SimulatedOrderType

def test_transaction_cost_buy_side():
    model = TransactionCostModel()
    order = SimulatedOrder(order_id="1", symbol="ASELS", side=SimulatedOrderSide.BUY, order_type=SimulatedOrderType.NEXT_CLOSE, quantity=100, reference_price=10.0, limit_price=None, requested_notional=1000, created_at=datetime.now())
    config = model.default_config()
    config.commission_bps = 5.0 # 5 bps

    breakdown = model.estimate_cost(order, fill_price=10.0, config=config)
    assert breakdown.total_cost == pytest.approx(0.5) # 1000 * 5 / 10000
    assert breakdown.net_notional == 1000.5

def test_transaction_cost_sell_side():
    model = TransactionCostModel()
    order = SimulatedOrder(order_id="1", symbol="ASELS", side=SimulatedOrderSide.SELL, order_type=SimulatedOrderType.NEXT_CLOSE, quantity=100, reference_price=10.0, limit_price=None, requested_notional=1000, created_at=datetime.now())
    config = model.default_config()
    config.commission_bps = 5.0

    breakdown = model.estimate_cost(order, fill_price=10.0, config=config)
    assert breakdown.total_cost == pytest.approx(0.5)
    assert breakdown.net_notional == 999.5
