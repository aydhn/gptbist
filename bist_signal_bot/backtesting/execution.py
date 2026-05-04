from datetime import datetime
import pandas as pd
import math

from bist_signal_bot.backtesting.models import (
    ExecutionPriceMode,
    BacktestOrder,
    BacktestFill,
    BacktestConfig,
)
from bist_signal_bot.costs.engine import TransactionCostEngine
from bist_signal_bot.costs.models import TradeCostInput

class BacktestExecutionModel:
    def __init__(self, cost_engine: TransactionCostEngine, config: BacktestConfig):
        self.cost_engine = cost_engine
        self.config = config

    def get_execution_price(self, data: pd.DataFrame, signal_index: int, mode: ExecutionPriceMode) -> tuple[datetime, float]:
        if mode == ExecutionPriceMode.SAME_CLOSE_FOR_RESEARCH_ONLY:
            row = data.iloc[signal_index]
            return row.name, float(row['close'])

        if signal_index + 1 >= len(data):
            raise ValueError("No next bar available for execution")

        next_row = data.iloc[signal_index + 1]
        timestamp = next_row.name

        if mode == ExecutionPriceMode.NEXT_OPEN:
            price = float(next_row['open'])
        elif mode == ExecutionPriceMode.NEXT_CLOSE:
            price = float(next_row['close'])
        else:
            raise ValueError(f"Unsupported execution mode: {mode}")

        return timestamp, price

    def create_fill(self, order: BacktestOrder, price: float, timestamp: datetime, average_daily_volume: float | None = None, average_daily_turnover: float | None = None, volatility: float | None = None) -> BacktestFill:
        cost_input = TradeCostInput(
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=price,
            average_daily_volume=average_daily_volume,
            average_daily_turnover=average_daily_turnover,
            volatility=volatility
        )
        self.cost_engine.scenario = self.config.scenario
        cost_breakdown = self.cost_engine.calculate_trade_cost(cost_input)

        fill = BacktestFill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=price,
            effective_price=cost_breakdown.effective_price,
            gross_notional=cost_breakdown.gross_notional,
            total_cost=cost_breakdown.total_cost,
            total_cost_bps=cost_breakdown.total_cost_bps,
            filled_at=timestamp,
            order_id=f"fill_{timestamp.timestamp()}_{order.symbol}",
            metadata={"cost_breakdown": cost_breakdown.summary()}
        )
        return fill

    def quantity_from_notional(self, notional: float, price: float, use_fractional: bool) -> float:
        if price <= 0: return 0.0
        qty = notional / price
        if not use_fractional: qty = math.floor(qty)
        return float(qty)
