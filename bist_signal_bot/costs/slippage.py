import math

from bist_signal_bot.core.exceptions import SlippageModelError
from bist_signal_bot.costs.models import (
    OrderSide,
    SlippageModelType,
    SlippageResult,
    TradeCostInput,
)


class SlippageModel:
    def __init__(
        self,
        model_type: SlippageModelType = SlippageModelType.HYBRID,
        fixed_slippage_bps: float = 5.0,
        volume_impact_factor: float = 10.0,
        volatility_impact_factor: float = 0.25,
        max_slippage_bps: float = 100.0,
        min_slippage_bps: float = 0.0,
    ):
        if min_slippage_bps < 0:
            raise SlippageModelError("min_slippage_bps cannot be negative")
        if max_slippage_bps < min_slippage_bps:
            raise SlippageModelError("max_slippage_bps must be >= min_slippage_bps")

        self.model_type = model_type
        self.fixed_slippage_bps = fixed_slippage_bps
        self.volume_impact_factor = volume_impact_factor
        self.volatility_impact_factor = volatility_impact_factor
        self.max_slippage_bps = max_slippage_bps
        self.min_slippage_bps = min_slippage_bps

    def calculate(self, input_data: TradeCostInput) -> SlippageResult:
        slippage_bps = self.fixed_slippage_bps

        if self.model_type == SlippageModelType.FIXED_BPS:
            pass # Keep fixed

        elif self.model_type == SlippageModelType.VOLUME_BASED:
            if input_data.average_daily_volume and input_data.average_daily_volume > 0:
                participation = input_data.quantity / input_data.average_daily_volume
                slippage_bps += self.volume_impact_factor * math.sqrt(participation) * 100

        elif self.model_type == SlippageModelType.VOLATILITY_BASED:
            if input_data.volatility is not None and input_data.volatility >= 0:
                slippage_bps += input_data.volatility * self.volatility_impact_factor * 10000

        elif self.model_type == SlippageModelType.HYBRID:
            if input_data.average_daily_volume and input_data.average_daily_volume > 0:
                participation = input_data.quantity / input_data.average_daily_volume
                slippage_bps += self.volume_impact_factor * math.sqrt(participation) * 100
            if input_data.volatility is not None and input_data.volatility >= 0:
                slippage_bps += input_data.volatility * self.volatility_impact_factor * 10000
        else:
             raise SlippageModelError(f"Unsupported slippage model type: {self.model_type}")

        # Clamp
        slippage_bps = max(self.min_slippage_bps, min(slippage_bps, self.max_slippage_bps))

        # Amounts
        slippage_amount_per_share = input_data.price * (slippage_bps / 10000.0)
        slippage_total_amount = slippage_amount_per_share * input_data.quantity
        adjusted_price = self.adjust_price(input_data.price, input_data.side, slippage_bps)

        return SlippageResult(
            slippage_bps=slippage_bps,
            slippage_amount_per_share=slippage_amount_per_share,
            slippage_total_amount=slippage_total_amount,
            adjusted_price=adjusted_price,
            metadata={
                "model_type": self.model_type.value
            }
        )

    def adjust_price(self, price: float, side: OrderSide, slippage_bps: float) -> float:
        if price <= 0:
            raise SlippageModelError("Price must be > 0 to adjust")
        if slippage_bps < 0:
            raise SlippageModelError("slippage_bps cannot be negative")

        slippage_bps = min(slippage_bps, self.max_slippage_bps)

        if side == OrderSide.BUY:
            adjusted = price * (1 + (slippage_bps / 10000.0))
        elif side == OrderSide.SELL:
            adjusted = price * (1 - (slippage_bps / 10000.0))
        else:
            raise SlippageModelError(f"Unsupported OrderSide: {side}")

        if adjusted <= 0:
             raise SlippageModelError("Adjusted price resulted in a non-positive value")

        return adjusted
