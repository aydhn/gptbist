import logging
import time
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime

import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame, Timeframe
from bist_signal_bot.core.exceptions import TimeframeAlignmentError
from bist_signal_bot.timeframes.models import TimeframeAlignmentConfig, TimeframeAlignmentReport, TimeframeIssue, AlignmentMode

class TimeframeAligner:
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    def _get_prefix_for_timeframe(self, timeframe: Timeframe) -> str:
        if timeframe == Timeframe.WEEKLY:
            return "w_"
        elif timeframe == Timeframe.MONTHLY:
            return "m_"
        else:
            return f"tf_{timeframe.value}_"

    def prefix_higher_columns(self, df: pd.DataFrame, timeframe: Timeframe, exclude_columns: Optional[List[str]] = None) -> pd.DataFrame:
        exclude_columns = exclude_columns or []
        prefix = self._get_prefix_for_timeframe(timeframe)
        rename_map = {}
        for col in df.columns:
            if col not in exclude_columns:
                rename_map[col] = f"{prefix}{col}"
        return df.rename(columns=rename_map)

    def validate_alignment_inputs(self, base: MarketDataFrame, higher_data: Dict[Timeframe, MarketDataFrame], config: TimeframeAlignmentConfig) -> None:
        if not isinstance(base.data.index, pd.DatetimeIndex):
            raise TimeframeAlignmentError("Base DataFrame must have a DatetimeIndex.")
        for tf, mdf in higher_data.items():
            if not isinstance(mdf.data.index, pd.DatetimeIndex):
                raise TimeframeAlignmentError(f"Higher timeframe DataFrame ({tf.value}) must have a DatetimeIndex.")

    def calculate_alignment_coverage(self, output_df: pd.DataFrame, added_columns: List[str]) -> Dict[str, Any]:
        coverage = {}
        total_rows = len(output_df)
        if total_rows == 0:
            return coverage

        for col in added_columns:
            non_na_count = output_df[col].count()
            coverage[col] = {
                "non_na": int(non_na_count),
                "coverage_pct": round((non_na_count / total_rows) * 100, 2)
            }
        return coverage

    def align_higher_to_base(self, base: MarketDataFrame, higher_data: Dict[Timeframe, MarketDataFrame], config: TimeframeAlignmentConfig) -> Tuple[pd.DataFrame, TimeframeAlignmentReport]:
        start_time = time.time()
        self.validate_alignment_inputs(base, higher_data, config)

        output_df = base.data.copy()
        issues = []
        added_columns = []

        for tf in config.higher_timeframes:
            if tf not in higher_data:
                issues.append(TimeframeIssue(
                    message=f"Missing data for requested higher timeframe: {tf.value}",
                    severity="WARNING",
                    timeframe=tf.value
                ))
                continue

            h_mdf = higher_data[tf]
            h_df = h_mdf.data.copy()

            if h_df.empty:
                issues.append(TimeframeIssue(
                    message=f"Higher timeframe data is empty for {tf.value}",
                    severity="WARNING",
                    timeframe=tf.value
                ))
                continue

            if config.prefix_columns:
                h_df = self.prefix_higher_columns(h_df, tf)

            cols_to_add = list(h_df.columns)
            added_columns.extend(cols_to_add)

            if config.alignment_mode == AlignmentMode.CLOSED_BAR_ONLY and config.shift_higher_tf_by_one_bar:
                h_df = h_df.shift(1)

            aligned_h_df = pd.DataFrame(index=output_df.index, columns=h_df.columns)
            common_idx = output_df.index.intersection(h_df.index)
            aligned_h_df.loc[common_idx] = h_df.loc[common_idx]

            if config.forward_fill:
                aligned_h_df = aligned_h_df.ffill()

            output_df = pd.concat([output_df, aligned_h_df], axis=1)

        if config.drop_unaligned_rows and added_columns:
            original_rows = len(output_df)
            output_df = output_df.dropna(subset=added_columns)
            dropped = original_rows - len(output_df)
            if dropped > 0:
                issues.append(TimeframeIssue(
                    message=f"Dropped {dropped} rows with unaligned (NaN) higher timeframe data.",
                    severity="INFO",
                    affected_rows=dropped
                ))

        report = TimeframeAlignmentReport(
            base_timeframe=config.base_timeframe.value,
            higher_timeframes=[t.value for t in config.higher_timeframes],
            input_base_rows=len(base.data),
            output_rows=len(output_df),
            added_columns=added_columns,
            alignment_mode=config.alignment_mode,
            forward_fill=config.forward_fill,
            shift_higher_tf_by_one_bar=config.shift_higher_tf_by_one_bar,
            issues=issues,
            elapsed_seconds=time.time() - start_time
        )

        return output_df, report
