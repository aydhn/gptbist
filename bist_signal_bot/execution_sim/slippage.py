from typing import Any
import uuid
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.execution_sim.models import (
    SlippageEstimate,
    SimulatedOrderSide,
    SlippageModelType,
    LiquiditySnapshot,
    LiquidityStatus,
)

class SlippageEstimator:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def estimate(
        self,
        symbol: str,
        side: SimulatedOrderSide,
        reference_price: float,
        quantity: float,
        price_df: pd.DataFrame | None = None,
        liquidity: LiquiditySnapshot | None = None,
        model_type: SlippageModelType | None = None
    ) -> SlippageEstimate:
        model = model_type or SlippageModelType(getattr(self.settings, "EXECUTION_SLIPPAGE_MODEL", "HYBRID"))

        if model == SlippageModelType.FIXED_BPS:
            return self.fixed_bps_estimate(symbol, side, reference_price, quantity, liquidity)
        elif model == SlippageModelType.SPREAD_BASED:
            return self.spread_based_estimate(symbol, side, reference_price, quantity, price_df, liquidity)
        elif model == SlippageModelType.VOLUME_PARTICIPATION:
            return self.volume_participation_estimate(symbol, side, reference_price, quantity, price_df, liquidity)
        elif model == SlippageModelType.VOLATILITY_ADJUSTED:
            return self.volatility_adjusted_estimate(symbol, side, reference_price, quantity, price_df, liquidity)
        elif model == SlippageModelType.HYBRID:
            return self.hybrid_estimate(symbol, side, reference_price, quantity, price_df, liquidity)
        else:
            return self.fixed_bps_estimate(symbol, side, reference_price, quantity, liquidity)

    def fixed_bps_estimate(
        self, symbol: str, side: SimulatedOrderSide, reference_price: float, quantity: float, liquidity: LiquiditySnapshot | None = None
    ) -> SlippageEstimate:
        bps = getattr(self.settings, "EXECUTION_FIXED_SLIPPAGE_BPS", 10.0)
        status = liquidity.status if liquidity else LiquidityStatus.UNKNOWN
        if status in [LiquidityStatus.THIN, LiquidityStatus.WATCH]:
            bps *= 2
        elif status == LiquidityStatus.ILLIQUID:
            bps *= 3

        # Apply event risk multiplier if active event window
        event_multiplier = 1.0
        if getattr(self.settings, "ENABLE_EVENT_CALENDAR", False):
            from bist_signal_bot.app.events_app import create_event_risk_engine
            engine = create_event_risk_engine(self.settings)
            assessment = engine.assess_symbol(symbol)
            if assessment.matching_windows:
                event_multiplier = getattr(self.settings, "EVENT_EXECUTION_SLIPPAGE_MULTIPLIER", 1.25)

        bps *= event_multiplier

        bps = min(bps, getattr(self.settings, "EXECUTION_MAX_SLIPPAGE_BPS", 250.0))
        slippage_val = reference_price * (bps / 10000.0)

        fill_price = reference_price + slippage_val if side == SimulatedOrderSide.BUY else reference_price - slippage_val

        return SlippageEstimate(
            estimate_id=str(uuid.uuid4()),
            symbol=symbol,
            model_type=SlippageModelType.FIXED_BPS,
            side=side,
            reference_price=reference_price,
            estimated_slippage_bps=bps,
            estimated_fill_price=fill_price,
            spread_bps=None,
            participation_rate_pct=None,
            volatility_pct=None,
            liquidity_status=status
        )

    def spread_based_estimate(self, symbol: str, side: SimulatedOrderSide, reference_price: float, quantity: float, price_df: pd.DataFrame | None, liquidity: LiquiditySnapshot | None = None) -> SlippageEstimate:
        # Fallback to fixed
        return self.fixed_bps_estimate(symbol, side, reference_price, quantity, liquidity)

    def volume_participation_estimate(self, symbol: str, side: SimulatedOrderSide, reference_price: float, quantity: float, price_df: pd.DataFrame | None, liquidity: LiquiditySnapshot | None = None) -> SlippageEstimate:
        return self.fixed_bps_estimate(symbol, side, reference_price, quantity, liquidity)

    def volatility_adjusted_estimate(self, symbol: str, side: SimulatedOrderSide, reference_price: float, quantity: float, price_df: pd.DataFrame | None, liquidity: LiquiditySnapshot | None = None) -> SlippageEstimate:
        return self.fixed_bps_estimate(symbol, side, reference_price, quantity, liquidity)

    def hybrid_estimate(self, symbol: str, side: SimulatedOrderSide, reference_price: float, quantity: float, price_df: pd.DataFrame | None, liquidity: LiquiditySnapshot | None = None) -> SlippageEstimate:
        # Simplistic hybrid implementation for V1
        bps = getattr(self.settings, "EXECUTION_FIXED_SLIPPAGE_BPS", 10.0)
        status = liquidity.status if liquidity else LiquidityStatus.UNKNOWN

        if liquidity and liquidity.average_turnover and reference_price > 0:
            notional = reference_price * quantity
            part_pct = (notional / liquidity.average_turnover) * 100
            mult = getattr(self.settings, "EXECUTION_VOLUME_PARTICIPATION_MULTIPLIER", 0.25)
            bps += part_pct * mult

        if status in [LiquidityStatus.THIN, LiquidityStatus.WATCH]:
            bps *= 1.5
        elif status == LiquidityStatus.ILLIQUID:
            bps *= 2.5

        # Apply event risk multiplier if active event window
        event_multiplier = 1.0
        if getattr(self.settings, "ENABLE_EVENT_CALENDAR", False):
            try:
                from bist_signal_bot.app.events_app import create_event_risk_engine
                engine = create_event_risk_engine(self.settings)
                assessment = engine.assess_symbol(symbol)
                if assessment.matching_windows:
                    event_multiplier = getattr(self.settings, "EVENT_EXECUTION_SLIPPAGE_MULTIPLIER", 1.25)
            except Exception:
                pass

        bps *= event_multiplier

        bps = min(bps, getattr(self.settings, "EXECUTION_MAX_SLIPPAGE_BPS", 250.0))
        slippage_val = reference_price * (bps / 10000.0)
        fill_price = reference_price + slippage_val if side == SimulatedOrderSide.BUY else reference_price - slippage_val

        spread_bps = getattr(self.settings, "EXECUTION_SPREAD_BPS_FALLBACK", 15.0)
        # Apply spread multiplier
        if event_multiplier > 1.0:
            spread_bps *= getattr(self.settings, "EVENT_EXECUTION_SPREAD_MULTIPLIER", 1.20)

        return SlippageEstimate(
            estimate_id=str(uuid.uuid4()),
            symbol=symbol,
            model_type=SlippageModelType.HYBRID,
            side=side,
            reference_price=reference_price,
            estimated_slippage_bps=bps,
            estimated_fill_price=fill_price,
            spread_bps=spread_bps,
            participation_rate_pct=None,
            volatility_pct=None,
            liquidity_status=status
        )
