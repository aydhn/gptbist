import logging
from typing import Optional, List, Dict
from datetime import datetime

import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.data.models import MarketDataFrame, Timeframe
from bist_signal_bot.indicators.engine import IndicatorEngine
from bist_signal_bot.indicators.models import IndicatorRequest
from bist_signal_bot.timeframes.resampler import TimeframeResampler
from bist_signal_bot.timeframes.alignment import TimeframeAligner
from bist_signal_bot.timeframes.models import (
    MultiTimeframeResult, TimeframeAlignmentConfig, AlignmentMode, TimeframeResampleReport
)
from bist_signal_bot.core.exceptions import MultiTimeframeError

class MultiTimeframeEngine:
    def __init__(
        self,
        data_service: Optional[MarketDataService] = None,
        indicator_engine: Optional[IndicatorEngine] = None,
        resampler: Optional[TimeframeResampler] = None,
        aligner: Optional[TimeframeAligner] = None,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)
        self.data_service = data_service
        self.indicator_engine = indicator_engine or IndicatorEngine(settings=self.settings)
        self.resampler = resampler or TimeframeResampler(settings=self.settings, logger=self.logger)
        self.aligner = aligner or TimeframeAligner(settings=self.settings, logger=self.logger)

    def default_higher_timeframes(self) -> List[Timeframe]:
        tfs = []
        for tf_str in self.settings.MTF_HIGHER_TIMEFRAMES.split(","):
            try:
                tfs.append(Timeframe(tf_str.strip()))
            except ValueError:
                self.logger.warning(f"Invalid higher timeframe in settings: {tf_str}")
        return tfs if tfs else [Timeframe.WEEKLY, Timeframe.MONTHLY]

    def default_indicator_requests_for_timeframe(self, timeframe: Timeframe) -> List[IndicatorRequest]:
        if timeframe == Timeframe.WEEKLY:
            return [
                IndicatorRequest(name="sma", params={"window": 20}),
                IndicatorRequest(name="sma", params={"window": 50}),
                IndicatorRequest(name="rsi", params={"window": 14}),
                IndicatorRequest(name="atr_pct", params={"window": 14})
            ]
        elif timeframe == Timeframe.MONTHLY:
            return [
                IndicatorRequest(name="sma", params={"window": 10}),
                IndicatorRequest(name="rsi", params={"window": 14}),
                IndicatorRequest(name="historical_volatility", params={"window": 12})
            ]
        return []

    def build_alignment_config(self, base_timeframe: Timeframe, higher_timeframes: List[Timeframe]) -> TimeframeAlignmentConfig:
        return TimeframeAlignmentConfig(
            base_timeframe=base_timeframe,
            higher_timeframes=higher_timeframes,
            alignment_mode=AlignmentMode(self.settings.MTF_ALIGNMENT_MODE),
            forward_fill=self.settings.MTF_FORWARD_FILL,
            shift_higher_tf_by_one_bar=self.settings.MTF_SHIFT_HIGHER_TF_BY_ONE_BAR,
            prefix_columns=self.settings.MTF_PREFIX_COLUMNS,
            drop_unaligned_rows=self.settings.MTF_DROP_UNALIGNED_ROWS
        )

    def build_from_base_data(
        self,
        base_data: MarketDataFrame,
        higher_timeframes: List[Timeframe],
        indicator_requests_by_timeframe: Optional[Dict[Timeframe, List[IndicatorRequest]]] = None
    ) -> MultiTimeframeResult:
        if indicator_requests_by_timeframe is None:
            indicator_requests_by_timeframe = {tf: self.default_indicator_requests_for_timeframe(tf) for tf in higher_timeframes}

        resample_reports = []
        higher_data = {}

        for tf in higher_timeframes:
            # 1. Resample
            resampled_mdf, rep = self.resampler.resample_ohlcv(
                base_data,
                target_timeframe=tf,
                drop_incomplete=self.settings.MTF_DROP_INCOMPLETE_HIGHER_TF_BAR
            )
            resample_reports.append(rep)

            # 2. Add indicators
            requests = indicator_requests_by_timeframe.get(tf, [])
            if requests and not resampled_mdf.data.empty:
                batch_res = self.indicator_engine.calculate_many(resampled_mdf, requests, continue_on_error=True)
                resampled_mdf.data = batch_res.output_data

            higher_data[tf] = resampled_mdf

        # 3. Align
        config = self.build_alignment_config(base_data.timeframe, higher_timeframes)
        output_df, align_report = self.aligner.align_higher_to_base(base_data, higher_data, config)

        return MultiTimeframeResult(
            output_data=output_df,
            resample_reports=resample_reports,
            alignment_report=align_report,
            symbol=base_data.symbol,
            base_timeframe=base_data.timeframe.value,
            generated_at=datetime.utcnow()
        )

    def build_for_symbol(
        self,
        symbol: str,
        base_timeframe: Timeframe = Timeframe.DAILY,
        higher_timeframes: Optional[List[Timeframe]] = None,
        period: Optional[str] = None,
        refresh: bool = False
    ) -> MultiTimeframeResult:
        if not self.data_service:
            raise MultiTimeframeError("MarketDataService is required when building by symbol.")

        period = period or "2y"
        higher_timeframes = higher_timeframes or self.default_higher_timeframes()

        base_mdf = self.data_service.get_ohlcv(symbol, timeframe=base_timeframe, period=period, refresh=refresh)

        return self.build_from_base_data(
            base_data=base_mdf,
            higher_timeframes=higher_timeframes
        )
