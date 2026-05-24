from typing import Any
import logging
import uuid
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.execution_sim.models import (
    SimulatedOrder, SimulatedFill, SimulatedFillStatus,
    TransactionCostConfig, ExecutionScenario, SimulatedOrderType, SimulatedOrderSide,
    LiquiditySnapshot, LiquidityStatus
)
from bist_signal_bot.execution_sim.costs import TransactionCostModel
from bist_signal_bot.execution_sim.slippage import SlippageEstimator
from bist_signal_bot.execution_sim.liquidity import LiquidityAnalyzer

logger = logging.getLogger(__name__)

class FillSimulator:
    def __init__(self, cost_model: TransactionCostModel, slippage_estimator: SlippageEstimator, liquidity_analyzer: LiquidityAnalyzer, settings: Settings | None = None, logger_instance=None):
        self.cost_model = cost_model
        self.slippage_estimator = slippage_estimator
        self.liquidity_analyzer = liquidity_analyzer
        self.settings = settings or Settings()
        self.logger = logger_instance or logger

    def simulate_fill(self, order: SimulatedOrder, price_df: pd.DataFrame, config: TransactionCostConfig | None = None, scenario: ExecutionScenario | None = None) -> SimulatedFill:
        liquidity = self.liquidity_analyzer.analyze(order.symbol, price_df, order.requested_notional)
        prob = self.fill_probability(order, liquidity, scenario)
        filled_qty, unfilled_qty, status = self.determine_filled_quantity(order, prob, liquidity)

        if status in [SimulatedFillStatus.NOT_FILLED, SimulatedFillStatus.REJECTED_RESEARCH]:
            return SimulatedFill(
                fill_id=str(uuid.uuid4()), order_id=order.order_id, symbol=order.symbol, status=status,
                filled_quantity=0.0, unfilled_quantity=order.quantity, average_fill_price=None,
                reference_price=order.reference_price, gross_notional=0.0, net_notional=0.0,
                liquidity_snapshot=liquidity, fill_probability=prob, reason="Fill failed based on logic or liquidity."
            )

        ref_price = self.reference_fill_price(order, price_df) or order.reference_price

        slippage = self.slippage_estimator.estimate(order.symbol, order.side, ref_price, filled_qty, price_df, liquidity)
        if scenario:
            slippage.estimated_slippage_bps *= scenario.slippage_multiplier
            slippage_val = ref_price * (slippage.estimated_slippage_bps / 10000.0)
            slippage.estimated_fill_price = ref_price + slippage_val if order.side == SimulatedOrderSide.BUY else ref_price - slippage_val

        est_fill_price = slippage.estimated_fill_price

        if order.order_type == SimulatedOrderType.LIMIT:
            is_filled, reason = self.apply_limit_logic(order, est_fill_price, price_df)
            if not is_filled:
                return SimulatedFill(
                    fill_id=str(uuid.uuid4()), order_id=order.order_id, symbol=order.symbol, status=SimulatedFillStatus.NOT_FILLED,
                    filled_quantity=0.0, unfilled_quantity=order.quantity, average_fill_price=None,
                    reference_price=order.reference_price, gross_notional=0.0, net_notional=0.0,
                    liquidity_snapshot=liquidity, fill_probability=prob, reason=reason
                )

        cost_breakdown = self.cost_model.estimate_cost(order, est_fill_price, config)
        if scenario:
            cost_breakdown.total_cost *= scenario.cost_multiplier
            if order.side == SimulatedOrderSide.BUY:
                cost_breakdown.net_notional = cost_breakdown.notional + cost_breakdown.total_cost
            elif order.side == SimulatedOrderSide.SELL:
                cost_breakdown.net_notional = cost_breakdown.notional - cost_breakdown.total_cost

        return SimulatedFill(
            fill_id=str(uuid.uuid4()), order_id=order.order_id, symbol=order.symbol, status=status,
            filled_quantity=filled_qty, unfilled_quantity=unfilled_qty, average_fill_price=est_fill_price,
            reference_price=order.reference_price, gross_notional=cost_breakdown.notional, net_notional=cost_breakdown.net_notional,
            cost_breakdown=cost_breakdown, slippage_estimate=slippage, liquidity_snapshot=liquidity,
            fill_probability=prob, reason="Simulated successfully."
        )

    def fill_probability(self, order: SimulatedOrder, liquidity: LiquiditySnapshot, scenario: ExecutionScenario | None = None) -> float:
        prob = 1.0
        if liquidity.status == LiquidityStatus.ILLIQUID:
            prob = 0.0
        elif liquidity.status == LiquidityStatus.THIN:
            prob = 0.5
        elif liquidity.status == LiquidityStatus.WATCH:
            prob = 0.8

        if scenario:
            prob *= scenario.fill_probability_multiplier

        return max(0.0, min(1.0, prob))

    def determine_filled_quantity(self, order: SimulatedOrder, probability: float, liquidity: LiquiditySnapshot) -> tuple[float, float, SimulatedFillStatus]:
        min_prob = getattr(self.settings, "EXECUTION_MIN_FILL_PROBABILITY", 0.10)
        no_fill_prob = getattr(self.settings, "EXECUTION_NO_FILL_BELOW_PROBABILITY", 0.15)
        allow_partial = getattr(self.settings, "EXECUTION_ALLOW_PARTIAL_FILL", True)

        if probability < no_fill_prob:
            return 0.0, order.quantity, SimulatedFillStatus.NOT_FILLED

        if probability < 1.0 and allow_partial:
            filled = order.quantity * probability
            unfilled = order.quantity - filled
            return filled, unfilled, SimulatedFillStatus.PARTIAL_FILLED

        return order.quantity, 0.0, SimulatedFillStatus.FILLED

    def reference_fill_price(self, order: SimulatedOrder, price_df: pd.DataFrame) -> float | None:
        if price_df is None or price_df.empty:
            return None
        if order.order_type in [SimulatedOrderType.NEXT_CLOSE, SimulatedOrderType.MARKET]:
            return float(price_df['close'].iloc[-1]) if 'close' in price_df else None
        elif order.order_type == SimulatedOrderType.NEXT_OPEN:
            return float(price_df['open'].iloc[-1]) if 'open' in price_df else None
        return float(price_df['close'].iloc[-1]) if 'close' in price_df else None

    def apply_limit_logic(self, order: SimulatedOrder, estimated_fill_price: float, price_df: pd.DataFrame) -> tuple[bool, str | None]:
        if not order.limit_price:
            return False, "Limit order lacks limit_price"
        if order.side == SimulatedOrderSide.BUY and estimated_fill_price > order.limit_price:
            return False, "Estimated fill price exceeds buy limit"
        if order.side == SimulatedOrderSide.SELL and estimated_fill_price < order.limit_price:
            return False, "Estimated fill price below sell limit"
        return True, None
