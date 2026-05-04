from bist_signal_bot.core.exceptions import SpreadModelError
from bist_signal_bot.costs.models import (
    LiquidityBucket,
    SpreadModelType,
    SpreadResult,
    TradeCostInput,
)


class SpreadModel:
    def __init__(
        self,
        model_type: SpreadModelType = SpreadModelType.LIQUIDITY_BUCKET,
        fixed_spread_bps: float = 5.0,
        high_liquidity_spread_bps: float = 3.0,
        medium_liquidity_spread_bps: float = 8.0,
        low_liquidity_spread_bps: float = 20.0,
    ):
        if fixed_spread_bps < 0:
            raise SpreadModelError("fixed_spread_bps cannot be negative")
        if high_liquidity_spread_bps < 0:
            raise SpreadModelError("high_liquidity_spread_bps cannot be negative")
        if medium_liquidity_spread_bps < 0:
            raise SpreadModelError("medium_liquidity_spread_bps cannot be negative")
        if low_liquidity_spread_bps < 0:
            raise SpreadModelError("low_liquidity_spread_bps cannot be negative")

        self.model_type = model_type
        self.fixed_spread_bps = fixed_spread_bps
        self.high_liquidity_spread_bps = high_liquidity_spread_bps
        self.medium_liquidity_spread_bps = medium_liquidity_spread_bps
        self.low_liquidity_spread_bps = low_liquidity_spread_bps

    def calculate(self, input_data: TradeCostInput) -> SpreadResult:
        spread_bps = self.fixed_spread_bps

        if self.model_type == SpreadModelType.FIXED_BPS:
            pass
        elif self.model_type == SpreadModelType.LIQUIDITY_BUCKET:
            bucket = input_data.liquidity_bucket
            if bucket == LiquidityBucket.HIGH:
                spread_bps = self.high_liquidity_spread_bps
            elif bucket == LiquidityBucket.LOW:
                spread_bps = self.low_liquidity_spread_bps
            else:
                spread_bps = self.medium_liquidity_spread_bps
        elif self.model_type == SpreadModelType.VOLUME_BASED:
            bucket = self.estimate_liquidity_bucket(
                average_daily_turnover=input_data.average_daily_turnover,
                average_daily_volume=input_data.average_daily_volume
            )
            if bucket == LiquidityBucket.HIGH:
                spread_bps = self.high_liquidity_spread_bps
            elif bucket == LiquidityBucket.LOW:
                spread_bps = self.low_liquidity_spread_bps
            else:
                spread_bps = self.medium_liquidity_spread_bps
        else:
            raise SpreadModelError(f"Unsupported spread model type: {self.model_type}")

        spread_amount_per_share = input_data.price * (spread_bps / 10000.0)
        spread_total_amount = spread_amount_per_share * input_data.quantity

        return SpreadResult(
            spread_bps=spread_bps,
            spread_amount_per_share=spread_amount_per_share,
            spread_total_amount=spread_total_amount,
            metadata={
                "model_type": self.model_type.value,
                "applied_bucket": getattr(bucket, 'value', "FIXED") if self.model_type != SpreadModelType.FIXED_BPS else "FIXED"
            }
        )

    def estimate_liquidity_bucket(
        self,
        average_daily_turnover: float | None,
        average_daily_volume: float | None = None,
    ) -> LiquidityBucket:
        if average_daily_turnover is not None and average_daily_turnover < 0:
             raise SpreadModelError("average_daily_turnover cannot be negative")
        if average_daily_volume is not None and average_daily_volume < 0:
             raise SpreadModelError("average_daily_volume cannot be negative")

        if average_daily_turnover is not None:
             if average_daily_turnover >= 100_000_000.0:
                 return LiquidityBucket.HIGH
             elif average_daily_turnover >= 10_000_000.0:
                 return LiquidityBucket.MEDIUM
             else:
                 return LiquidityBucket.LOW

        return LiquidityBucket.UNKNOWN
