import pytest
from datetime import datetime
from bist_signal_bot.execution_sim.models import (
    TransactionCostConfig, SimulatedOrder, SimulatedOrderType, SimulatedOrderSide
)

def test_transaction_cost_config_validation():
    with pytest.raises(ValueError):
        TransactionCostConfig(config_id="1", commission_bps=-1.0, min_commission=0, tax_bps_placeholder=0, exchange_fee_bps_placeholder=0, include_spread_cost=True, include_slippage_cost=True, include_market_impact=True)

def test_simulated_order_validation():
    with pytest.raises(ValueError):
        SimulatedOrder(order_id="1", symbol="ASELS", side=SimulatedOrderSide.BUY, order_type=SimulatedOrderType.LIMIT, quantity=10, reference_price=10, limit_price=None, requested_notional=100, created_at=datetime.now())

    order = SimulatedOrder(order_id="1", symbol="asels ", side=SimulatedOrderSide.BUY, order_type=SimulatedOrderType.NEXT_CLOSE, quantity=10, reference_price=10, limit_price=None, requested_notional=100, created_at=datetime.now())
    assert order.symbol == "ASELS"
