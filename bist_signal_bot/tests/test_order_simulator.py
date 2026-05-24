import pytest
from bist_signal_bot.execution_sim.orders import OrderSimulator
from bist_signal_bot.execution_sim.models import SimulatedOrderType

class MockSignal:
    def __init__(self):
        self.action = "LONG"
        self.symbol = "ASELS"
        self.close_price = 100.0
        self.signal_id = "s1"
        self.strategy = "strat"

def test_order_simulator_build():
    sim = OrderSimulator()
    sig = MockSignal()
    order = sim.build_order_from_signal(sig, notional=1000.0)
    assert order.symbol == "ASELS"
    assert order.order_type == SimulatedOrderType.NEXT_CLOSE
    assert order.quantity == 10.0
