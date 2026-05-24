from typing import Any
import uuid
from datetime import datetime
import pandas as pd

from bist_signal_bot.execution_sim.models import SimulatedOrder, SimulatedOrderSide, SimulatedOrderType, SimulatedFill
from bist_signal_bot.execution_sim.fill import FillSimulator

class OrderSimulator:
    def __init__(self, settings: Any | None = None):
        self.settings = settings

    def build_order_from_signal(self, signal: Any, quantity: float | None = None, notional: float | None = None, order_type: SimulatedOrderType = SimulatedOrderType.NEXT_CLOSE) -> SimulatedOrder:
        side = SimulatedOrderSide.BUY if signal.action == "LONG" else SimulatedOrderSide.SELL # simplified
        ref_price = signal.close_price # Assuming signal has this
        q = quantity or (notional / ref_price if notional else 1.0)
        n = notional or (q * ref_price)

        return SimulatedOrder(
            order_id=str(uuid.uuid4()),
            symbol=signal.symbol,
            side=side,
            order_type=order_type,
            quantity=q,
            reference_price=ref_price,
            limit_price=None,
            requested_notional=n,
            signal_id=signal.signal_id,
            strategy_name=signal.strategy,
            created_at=datetime.now()
        )

    def build_order(self, symbol: str, side: SimulatedOrderSide, notional: float, reference_price: float, order_type: SimulatedOrderType, limit_price: float | None = None) -> SimulatedOrder:
        q = notional / reference_price if reference_price > 0 else 0
        return SimulatedOrder(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=q,
            reference_price=reference_price,
            limit_price=limit_price,
            requested_notional=notional,
            created_at=datetime.now()
        )

    def simulate_orders(self, orders: list[SimulatedOrder], data_by_symbol: dict[str, pd.DataFrame], fill_simulator: FillSimulator) -> list[SimulatedFill]:
        fills = []
        for order in orders:
            df = data_by_symbol.get(order.symbol, pd.DataFrame())
            fill = fill_simulator.simulate_fill(order, df)
            fills.append(fill)
        return fills

    def validate_order(self, order: SimulatedOrder) -> list[str]:
        errors = []
        if order.quantity <= 0:
            errors.append("Quantity must be positive.")
        if order.reference_price <= 0:
            errors.append("Reference price must be positive.")
        if order.order_type == SimulatedOrderType.LIMIT and order.limit_price is None:
            errors.append("Limit order requires limit price.")
        return errors
