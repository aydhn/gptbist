import logging
from datetime import datetime

import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.costs.commission import CommissionModel
from bist_signal_bot.costs.models import (
    CostScenario,
    LiquidityBucket,
    OrderSide,
    RoundTripCostBreakdown,
    TradeCostInput,
    TransactionCostBreakdown,
)
from bist_signal_bot.costs.slippage import SlippageModel
from bist_signal_bot.costs.spread import SpreadModel
from bist_signal_bot.signals.models import SignalCandidate


class TransactionCostEngine:
    def __init__(
        self,
        commission_model: CommissionModel | None = None,
        slippage_model: SlippageModel | None = None,
        spread_model: SpreadModel | None = None,
        settings: Settings | None = None,
        scenario: CostScenario = CostScenario.BASE,
        logger: logging.Logger | None = None,
    ):
        self.commission_model = commission_model or CommissionModel()
        self.slippage_model = slippage_model or SlippageModel()
        self.spread_model = spread_model or SpreadModel()
        self.settings = settings
        self.scenario = scenario
        self.logger = logger or logging.getLogger(__name__)

    def calculate_trade_cost(self, input_data: TradeCostInput) -> TransactionCostBreakdown:
        gross_notional = input_data.computed_notional()

        commission_result = self.commission_model.calculate(input_data)
        tax_amount = self.commission_model.calculate_tax(input_data)
        other_fees = self.commission_model.calculate_other_fees(input_data)

        slippage_result = self.slippage_model.calculate(input_data)
        spread_result = self.spread_model.calculate(input_data)

        total_cost = (
            commission_result.commission_amount
            + tax_amount
            + other_fees
            + slippage_result.slippage_total_amount
            + spread_result.spread_total_amount
        )

        if gross_notional > 0:
            total_cost_bps = (total_cost / gross_notional) * 10000.0
        else:
            total_cost_bps = 0.0

        if input_data.side == OrderSide.BUY:
            effective_price = input_data.price + slippage_result.slippage_amount_per_share + (spread_result.spread_amount_per_share / 2.0)
        else:
            effective_price = input_data.price - slippage_result.slippage_amount_per_share - (spread_result.spread_amount_per_share / 2.0)

        return TransactionCostBreakdown(
            input=input_data,
            commission=commission_result,
            slippage=slippage_result,
            spread=spread_result,
            tax_amount=tax_amount,
            other_fees=other_fees,
            gross_notional=gross_notional,
            total_cost=total_cost,
            total_cost_bps=total_cost_bps,
            effective_price=effective_price,
            side=input_data.side,
            scenario=self.scenario,
        )

    def calculate_round_trip(self, entry: TradeCostInput, exit_price: float, exit_timestamp: datetime | None = None) -> RoundTripCostBreakdown:
        entry_breakdown = self.calculate_trade_cost(entry)

        exit_side = OrderSide.SELL if entry.side == OrderSide.BUY else OrderSide.BUY

        exit_input = TradeCostInput(
            symbol=entry.symbol,
            side=exit_side,
            order_type=entry.order_type,
            quantity=entry.quantity,
            price=exit_price,
            notional=entry.quantity * exit_price,
            average_daily_volume=entry.average_daily_volume,
            average_daily_turnover=entry.average_daily_turnover,
            volatility=entry.volatility,
            liquidity_bucket=entry.liquidity_bucket,
            timestamp=exit_timestamp,
            metadata=entry.metadata.copy()
        )

        exit_breakdown = self.calculate_trade_cost(exit_input)

        total_cost = entry_breakdown.total_cost + exit_breakdown.total_cost

        gross_notional = entry_breakdown.gross_notional
        if gross_notional > 0:
            total_cost_bps = (total_cost / gross_notional) * 10000.0
            breakeven_move_pct = (total_cost / gross_notional) * 100.0
        else:
            total_cost_bps = 0.0
            breakeven_move_pct = 0.0

        return RoundTripCostBreakdown(
            entry_cost=entry_breakdown,
            exit_cost=exit_breakdown,
            total_cost=total_cost,
            total_cost_bps=total_cost_bps,
            breakeven_move_pct=breakeven_move_pct
        )

    def estimate_liquidity_bucket_from_data(self, data: pd.DataFrame, price_col: str = "close", volume_col: str = "volume", window: int = 20) -> LiquidityBucket:
        if len(data) < window:
            window = len(data)

        if window == 0:
             return LiquidityBucket.UNKNOWN

        recent_data = data.iloc[-window:]
        avg_vol = recent_data[volume_col].mean()
        avg_price = recent_data[price_col].mean()
        avg_turnover = avg_vol * avg_price

        return self.spread_model.estimate_liquidity_bucket(average_daily_turnover=avg_turnover, average_daily_volume=avg_vol)

    def build_input_from_signal_candidate(
        self,
        candidate: SignalCandidate,
        quantity: float,
        average_daily_volume: float | None = None,
        average_daily_turnover: float | None = None,
        volatility: float | None = None
    ) -> TradeCostInput:
        side = OrderSide.BUY if candidate.direction.value == "LONG" else OrderSide.SELL
        from bist_signal_bot.costs.models import OrderType

        liquidity_bucket = LiquidityBucket.UNKNOWN
        if average_daily_turnover is not None:
             liquidity_bucket = self.spread_model.estimate_liquidity_bucket(average_daily_turnover)

        return TradeCostInput(
            symbol=candidate.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=candidate.entry_reference_price if candidate.entry_reference_price is not None else 0.0,
            average_daily_volume=average_daily_volume,
            average_daily_turnover=average_daily_turnover,
            volatility=volatility,
            liquidity_bucket=liquidity_bucket,
            timestamp=candidate.signal_bar_timestamp,
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "TransactionCostEngine":
        from bist_signal_bot.costs.models import CommissionModelType, SlippageModelType, SpreadModelType

        commission = CommissionModel(
            model_type=CommissionModelType(getattr(settings, "COMMISSION_MODEL_TYPE", "BPS")),
            commission_bps=getattr(settings, "COMMISSION_BPS", 5.0),
            flat_fee=getattr(settings, "COMMISSION_FLAT_FEE", 0.0),
            minimum_commission=getattr(settings, "COMMISSION_MINIMUM", 0.0),
            tax_bps=getattr(settings, "TRANSACTION_TAX_BPS", 0.0),
            other_fee_bps=getattr(settings, "OTHER_FEE_BPS", 0.0),
        )

        slippage = SlippageModel(
            model_type=SlippageModelType(getattr(settings, "SLIPPAGE_MODEL_TYPE", "HYBRID")),
            fixed_slippage_bps=getattr(settings, "FIXED_SLIPPAGE_BPS", 5.0),
            volume_impact_factor=getattr(settings, "VOLUME_IMPACT_FACTOR", 10.0),
            volatility_impact_factor=getattr(settings, "VOLATILITY_IMPACT_FACTOR", 0.25),
            min_slippage_bps=getattr(settings, "MIN_SLIPPAGE_BPS", 0.0),
            max_slippage_bps=getattr(settings, "MAX_SLIPPAGE_BPS", 100.0),
        )

        spread = SpreadModel(
            model_type=SpreadModelType(getattr(settings, "SPREAD_MODEL_TYPE", "LIQUIDITY_BUCKET")),
            fixed_spread_bps=getattr(settings, "FIXED_SPREAD_BPS", 5.0),
            high_liquidity_spread_bps=getattr(settings, "HIGH_LIQUIDITY_SPREAD_BPS", 3.0),
            medium_liquidity_spread_bps=getattr(settings, "MEDIUM_LIQUIDITY_SPREAD_BPS", 8.0),
            low_liquidity_spread_bps=getattr(settings, "LOW_LIQUIDITY_SPREAD_BPS", 20.0),
        )

        scenario = CostScenario(getattr(settings, "COST_SCENARIO", "BASE"))

        # apply scenarios modifications correctly:
        from bist_signal_bot.costs.scenarios import build_cost_engine_for_scenario

        return build_cost_engine_for_scenario(settings, scenario)
