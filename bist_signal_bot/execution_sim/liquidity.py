from typing import Any
import uuid
import pandas as pd
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.execution_sim.models import LiquiditySnapshot, LiquidityStatus

class LiquidityAnalyzer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def analyze(self, symbol: str, price_df: pd.DataFrame, requested_notional: float | None = None) -> LiquiditySnapshot:
        if price_df is None or price_df.empty:
            return LiquiditySnapshot(
                snapshot_id=str(uuid.uuid4()),
                symbol=symbol,
                generated_at=datetime.now(),
                average_volume=None,
                average_turnover=None,
                last_volume=None,
                last_close=None,
                median_volume=None,
                volume_percentile=None,
                estimated_spread_bps=None,
                max_research_notional=None,
                status=LiquidityStatus.INSUFFICIENT_DATA
            )

        window = getattr(self.settings, "EXECUTION_LIQUIDITY_WINDOW", 20)
        avg_vol = self.average_volume(price_df, window)
        avg_turnover = self.average_turnover(price_df, window)
        spread_bps = self.estimate_spread_bps(price_df)

        last_close = float(price_df['close'].iloc[-1]) if 'close' in price_df else None
        last_volume = float(price_df['volume'].iloc[-1]) if 'volume' in price_df else None

        snapshot = LiquiditySnapshot(
            snapshot_id=str(uuid.uuid4()),
            symbol=symbol,
            generated_at=datetime.now(),
            average_volume=avg_vol,
            average_turnover=avg_turnover,
            last_volume=last_volume,
            last_close=last_close,
            median_volume=None,
            volume_percentile=None,
            estimated_spread_bps=spread_bps,
            max_research_notional=None,
            status=LiquidityStatus.UNKNOWN
        )

        snapshot.max_research_notional = self.max_research_notional(snapshot)
        snapshot.status = self.classify_liquidity(snapshot, requested_notional)
        return snapshot

    def average_volume(self, price_df: pd.DataFrame, window: int) -> float | None:
        if 'volume' not in price_df or price_df.empty:
            return None
        return float(price_df['volume'].tail(window).mean())

    def average_turnover(self, price_df: pd.DataFrame, window: int) -> float | None:
        if 'volume' not in price_df or 'close' not in price_df or price_df.empty:
            return None
        recent = price_df.tail(window)
        turnovers = recent['volume'] * recent['close']
        return float(turnovers.mean())

    def estimate_spread_bps(self, price_df: pd.DataFrame) -> float | None:
        return getattr(self.settings, "EXECUTION_SPREAD_BPS_FALLBACK", 15.0)

    def max_research_notional(self, snapshot: LiquiditySnapshot, participation_limit_pct: float | None = None) -> float | None:
        if not snapshot.average_turnover:
            return None
        limit_pct = participation_limit_pct or getattr(self.settings, "EXECUTION_MAX_PARTICIPATION_PCT", 5.0)
        return snapshot.average_turnover * (limit_pct / 100.0)

    def classify_liquidity(self, snapshot: LiquiditySnapshot, requested_notional: float | None = None) -> LiquidityStatus:
        if not snapshot.average_turnover:
            return LiquidityStatus.INSUFFICIENT_DATA

        if requested_notional:
            participation = (requested_notional / snapshot.average_turnover) * 100.0
            fail_pct = getattr(self.settings, "EXECUTION_LIQUIDITY_FAIL_PARTICIPATION_PCT", 10.0)
            warn_pct = getattr(self.settings, "EXECUTION_LIQUIDITY_WARN_PARTICIPATION_PCT", 3.0)

            if participation > fail_pct:
                return LiquidityStatus.ILLIQUID
            elif participation > warn_pct:
                return LiquidityStatus.WATCH

        min_turnover = getattr(self.settings, "EXECUTION_MIN_AVERAGE_TURNOVER", 0.0)
        if snapshot.average_turnover < min_turnover:
            return LiquidityStatus.THIN

        return LiquidityStatus.LIQUID
