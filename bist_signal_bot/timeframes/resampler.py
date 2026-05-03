import logging
import time
from typing import Optional, Tuple
from datetime import datetime

import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame, Timeframe, DataVendor
from bist_signal_bot.core.exceptions import TimeframeResampleError
from bist_signal_bot.timeframes.models import TimeframeResampleReport, TimeframeIssue, ResampleRule

class TimeframeResampler:
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    def infer_resample_rule(self, target_timeframe: Timeframe) -> str:
        if target_timeframe == Timeframe.DAILY:
            return ResampleRule.DAILY.value
        elif target_timeframe == Timeframe.WEEKLY:
            return ResampleRule.WEEKLY.value
        elif target_timeframe == Timeframe.MONTHLY:
            return ResampleRule.MONTHLY.value
        else:
            raise TimeframeResampleError(f"Unsupported target timeframe for resample: {target_timeframe}")

    def drop_incomplete_periods(self, df: pd.DataFrame, target_timeframe: Timeframe) -> pd.DataFrame:
        if df.empty:
            return df
        return df.iloc[:-1]

    def resample_ohlcv(self, market_data: MarketDataFrame, target_timeframe: Timeframe, drop_incomplete: bool = True) -> Tuple[MarketDataFrame, TimeframeResampleReport]:
        return self.resample_dataframe(
            df=market_data.data,
            source_timeframe=market_data.timeframe,
            target_timeframe=target_timeframe,
            symbol=market_data.symbol,
            source=market_data.source,
            drop_incomplete=drop_incomplete
        )

    def resample_dataframe(self, df: pd.DataFrame, source_timeframe: Timeframe, target_timeframe: Timeframe, symbol: str, source: DataVendor | str, drop_incomplete: bool = True) -> Tuple[MarketDataFrame, TimeframeResampleReport]:
        start_time = time.time()
        issues = []

        if not isinstance(df.index, pd.DatetimeIndex):
            raise TimeframeResampleError("DataFrame must have a DatetimeIndex for resampling.")

        if df.empty:
            issues.append(TimeframeIssue(
                message="Input DataFrame is empty.",
                severity="WARNING",
                timeframe=target_timeframe.value
            ))
            report = TimeframeResampleReport(
                source_timeframe=source_timeframe.value,
                target_timeframe=target_timeframe.value,
                input_rows=0,
                output_rows=0,
                issues=issues,
                elapsed_seconds=time.time() - start_time
            )
            mdf = MarketDataFrame(
                symbol=symbol,
                timeframe=target_timeframe,
                source=source if isinstance(source, DataVendor) else DataVendor.UNKNOWN,
                data=df.copy(),
                fetched_at=datetime.utcnow(),
                metadata={'resampled': True}
            )
            return mdf, report

        rule = self.infer_resample_rule(target_timeframe)

        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }

        if 'adj_close' in df.columns:
            agg_dict['adj_close'] = 'last'
        if 'dividends' in df.columns:
            agg_dict['dividends'] = 'sum'
        if 'stock_splits' in df.columns:
            agg_dict['stock_splits'] = 'max'

        try:
            resampled_df = df.resample(rule, label='right', closed='right').agg(agg_dict)
            resampled_df = resampled_df.dropna(subset=['close'])

            if drop_incomplete:
                original_rows = len(resampled_df)
                resampled_df = self.drop_incomplete_periods(resampled_df, target_timeframe)
                dropped_rows = original_rows - len(resampled_df)
                if dropped_rows > 0:
                    issues.append(TimeframeIssue(
                        message=f"Dropped {dropped_rows} incomplete bar(s) for timeframe {target_timeframe.value}.",
                        severity="INFO",
                        affected_rows=dropped_rows
                    ))

            mdf = MarketDataFrame(
                symbol=symbol,
                timeframe=target_timeframe,
                source=source if isinstance(source, DataVendor) else DataVendor.UNKNOWN,
                data=resampled_df,
                fetched_at=datetime.utcnow(),
                metadata={'resampled': True, 'original_tf': source_timeframe.value}
            )

            report = TimeframeResampleReport(
                source_timeframe=source_timeframe.value,
                target_timeframe=target_timeframe.value,
                input_rows=len(df),
                output_rows=len(resampled_df),
                start=resampled_df.index.min().to_pydatetime() if not resampled_df.empty else None,
                end=resampled_df.index.max().to_pydatetime() if not resampled_df.empty else None,
                issues=issues,
                elapsed_seconds=time.time() - start_time
            )

            return mdf, report

        except Exception as e:
            raise TimeframeResampleError(f"Error during resampling: {e}")
