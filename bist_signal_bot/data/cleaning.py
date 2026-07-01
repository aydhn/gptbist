import logging
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import DataCleaningError
from bist_signal_bot.data.models import (
    CleanedMarketData,
    CleaningIssue,
    CleaningIssueType,
    CleaningReport,
    CleaningConfig,
    CleaningStatus,
    DuplicateTimestampPolicy,
    InvalidOhlcPolicy,
    MarketDataFrame,
    MissingValuePolicy,
    OutlierPolicy,
)

logger = logging.getLogger("bist_signal_bot.data.cleaning")


class MarketDataCleaner:
    def __init__(
        self,
        config: CleaningConfig | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings
        self.config = config or CleaningConfig()

        if settings:
            self.config.missing_value_policy = MissingValuePolicy(settings.CLEANING_MISSING_VALUE_POLICY)
            self.config.invalid_ohlc_policy = InvalidOhlcPolicy(settings.CLEANING_INVALID_OHLC_POLICY)
            self.config.outlier_policy = OutlierPolicy(settings.CLEANING_OUTLIER_POLICY)
            self.config.duplicate_timestamp_policy = DuplicateTimestampPolicy(settings.CLEANING_DUPLICATE_TIMESTAMP_POLICY)
            self.config.max_daily_return_abs = settings.CLEANING_MAX_DAILY_RETURN_ABS
            self.config.max_volume_zscore = settings.CLEANING_MAX_VOLUME_ZSCORE
            self.config.min_rows_after_cleaning = settings.CLEANING_MIN_ROWS_AFTER_CLEANING
            self.config.strict = settings.CLEANING_STRICT

    def clean_market_data(self, market_data: MarketDataFrame) -> CleanedMarketData:
        start_time = datetime.now(UTC)
        symbol = market_data.symbol
        timeframe = market_data.timeframe.value

        logger.debug(f"Starting data cleaning for {symbol} ({timeframe})")

        input_rows = market_data.row_count()
        if input_rows == 0:
            report = self._build_report(symbol, timeframe, market_data.source.value, input_rows, 0, start_time, CleaningStatus.FAILED, [])
            report.issues.append(CleaningIssue(
                issue_type=CleaningIssueType.EMPTY_ROW,
                message=f"Input data is completely empty for {symbol}.",
                action_taken="FAIL"
            ))
            return CleanedMarketData(market_data=market_data, report=report)

        # Mutate copy, not original
        df = market_data.data.copy(deep=True)
        issues: list[CleaningIssue] = []

        df, dropped_by_duplicate = self._handle_duplicate_timestamps(df, symbol, issues)
        df, dropped_by_empty = self._drop_empty_rows(df, symbol, issues)

        # Ensure we still have data
        if df.empty:
            report = self._build_report(symbol, timeframe, market_data.source.value, input_rows, 0, start_time, CleaningStatus.FAILED, issues)
            report.dropped_rows = input_rows
            return CleanedMarketData(market_data=market_data, report=report)

        df = self._ensure_numeric(df)

        df, dropped_by_negative = self._handle_negative_values(df, symbol, issues)
        df, dropped_by_zero = self._handle_zero_prices(df, symbol, issues)
        df, dropped_by_invalid = self._handle_invalid_ohlc(df, symbol, issues)
        df, filled_values, dropped_by_missing = self._handle_missing_values(df, symbol, issues)

        flagged_outliers = 0
        df, flagged_returns = self._detect_extreme_returns(df, symbol, issues)
        df, flagged_volume = self._detect_extreme_volume(df, symbol, issues)
        flagged_outliers = flagged_returns + flagged_volume

        # index order
        df.sort_index(inplace=True)

        output_rows = len(df)
        dropped_rows = input_rows - output_rows

        usable_backtest, usable_ml = self._calculate_usability(df, output_rows)

        status = CleaningStatus.SUCCESS
        if self.config.strict and issues:
            status = CleaningStatus.FAILED
            if self.settings and self.settings.CLEANING_FAIL_ON_ERROR:
                raise DataCleaningError(f"Cleaning failed strictly for {symbol}")
        elif not usable_backtest:
            status = CleaningStatus.WARNING
        elif issues:
             status = CleaningStatus.WARNING

        report = self._build_report(symbol, timeframe, market_data.source.value, input_rows, output_rows, start_time, status, issues)
        report.dropped_rows = dropped_rows
        report.filled_values = filled_values
        report.flagged_outliers = flagged_outliers
        report.usable_for_backtest = usable_backtest
        report.usable_for_ml = usable_ml

        # new mdf
        cleaned_mdf = MarketDataFrame(
            symbol=market_data.symbol,
            timeframe=market_data.timeframe,
            source=market_data.source,
            data=df,
            fetched_at=market_data.fetched_at,
            metadata=market_data.metadata.copy()
        )

        cleaned_mdf.metadata.update({
            "cleaned": True,
            "cleaning_status": status.value,
            "cleaning_issue_count": report.issue_count(),
            "cleaning_elapsed_seconds": report.elapsed_seconds,
            "dropped_rows": dropped_rows,
            "filled_values": filled_values,
            "flagged_outliers": flagged_outliers,
            "usable_for_backtest": usable_backtest,
            "usable_for_ml": usable_ml
        })

        return CleanedMarketData(market_data=cleaned_mdf, report=report)

    def _build_report(self, symbol, timeframe, source, input_rows, output_rows, start_time, status, issues) -> CleaningReport:
        end_time = datetime.now(UTC)
        return CleaningReport(
            symbol=symbol,
            timeframe=timeframe,
            source=source,
            status=status,
            input_rows=input_rows,
            output_rows=output_rows,
            issues=issues,
            started_at=start_time,
            finished_at=end_time,
            elapsed_seconds=(end_time - start_time).total_seconds(),
            usable_for_backtest=False,
            usable_for_ml=False
        )

    def _ensure_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    def _handle_duplicate_timestamps(self, df: pd.DataFrame, symbol: str, issues: list) -> tuple[pd.DataFrame, int]:
        if not df.index.has_duplicates:
            return df, 0

        dups_count = df.index.duplicated(keep=False).sum()
        keep = False
        action = "DROP_ALL"

        if self.config.duplicate_timestamp_policy.value == "KEEP_LAST":
            keep = 'last'
            action = "KEEP_LAST"
        elif self.config.duplicate_timestamp_policy.value == "KEEP_FIRST":
            keep = 'first'
            action = "KEEP_FIRST"
        elif self.config.duplicate_timestamp_policy.value == "FAIL":
            raise DataCleaningError(f"Duplicate timestamps found for {symbol} and policy is FAIL")

        before_len = len(df)
        df = df[~df.index.duplicated(keep=keep)]
        dropped = before_len - len(df)

        issues.append(CleaningIssue(
            issue_type=CleaningIssueType.DUPLICATE_TIMESTAMP,
            message=f"Found {dups_count} duplicated timestamp rows.",
            affected_rows=dropped,
            action_taken=action
        ))
        return df, dropped

    def _drop_empty_rows(self, df: pd.DataFrame, symbol: str, issues: list) -> tuple[pd.DataFrame, int]:
        # Drop rows where all elements are NaN
        before_len = len(df)
        df = df.dropna(how='all')
        dropped = before_len - len(df)

        if dropped > 0:
            issues.append(CleaningIssue(
                issue_type=CleaningIssueType.EMPTY_ROW,
                message=f"Dropped {dropped} completely empty rows.",
                affected_rows=dropped,
                action_taken="DROP_ROW"
            ))
        return df, dropped

    def _handle_negative_values(self, df: pd.DataFrame, symbol: str, issues: list) -> tuple[pd.DataFrame, int]:
        dropped_total = 0

        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                neg_mask = df[col] < 0
                neg_count = neg_mask.sum()
                if neg_count > 0:
                    df = df[~neg_mask]
                    dropped_total += neg_count
                    issues.append(CleaningIssue(
                        issue_type=CleaningIssueType.NEGATIVE_PRICE,
                        message=f"Found {neg_count} negative prices in {col}.",
                        affected_rows=neg_count,
                        affected_columns=[col],
                        action_taken="DROP_ROW"
                    ))

        if "volume" in df.columns:
            neg_mask = df["volume"] < 0
            neg_count = neg_mask.sum()
            if neg_count > 0:
                df = df[~neg_mask]
                dropped_total += neg_count
                issues.append(CleaningIssue(
                    issue_type=CleaningIssueType.NEGATIVE_VOLUME,
                    message=f"Found {neg_count} negative volume rows.",
                    affected_rows=neg_count,
                    affected_columns=["volume"],
                    action_taken="DROP_ROW"
                ))

        return df, dropped_total

    def _handle_zero_prices(self, df: pd.DataFrame, symbol: str, issues: list) -> tuple[pd.DataFrame, int]:
        dropped_total = 0
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                zero_mask = df[col] == 0
                zero_count = zero_mask.sum()
                if zero_count > 0:
                    df = df[~zero_mask]
                    dropped_total += zero_count
                    issues.append(CleaningIssue(
                        issue_type=CleaningIssueType.ZERO_PRICE,
                        message=f"Found {zero_count} zero prices in {col}.",
                        affected_rows=zero_count,
                        affected_columns=[col],
                        action_taken="DROP_ROW"
                    ))
        return df, dropped_total

    def _handle_invalid_ohlc(self, df: pd.DataFrame, symbol: str, issues: list) -> tuple[pd.DataFrame, int]:
        if df.empty or not set(["open", "high", "low", "close"]).issubset(df.columns):
            return df, 0

        mask = (df["high"] < df["low"]) | \
               (df["high"] < df["open"]) | \
               (df["high"] < df["close"]) | \
               (df["low"] > df["open"]) | \
               (df["low"] > df["close"])

        invalid_count = mask.sum()
        if invalid_count == 0:
            return df, 0

        action = "DROP_ROW"
        if self.config.invalid_ohlc_policy == InvalidOhlcPolicy.LEAVE_UNCHANGED:
            action = "LEAVE_UNCHANGED"
        elif self.config.invalid_ohlc_policy == InvalidOhlcPolicy.FAIL:
            raise DataCleaningError(f"Invalid OHLC relations found for {symbol}")
        elif self.config.invalid_ohlc_policy == InvalidOhlcPolicy.DROP_ROW:
            df = df[~mask]

        issues.append(CleaningIssue(
            issue_type=CleaningIssueType.INVALID_OHLC,
            message=f"Found {invalid_count} rows with invalid OHLC relations.",
            affected_rows=invalid_count,
            action_taken=action
        ))

        return df, invalid_count if action == "DROP_ROW" else 0

    def _handle_missing_values(self, df: pd.DataFrame, symbol: str, issues: list) -> tuple[pd.DataFrame, int, int]:
        total_missing = df.isna().sum().sum()
        if total_missing == 0:
            return df, 0, 0

        if self.config.missing_value_policy == MissingValuePolicy.FAIL:
            raise DataCleaningError(f"Missing values found in {symbol} and policy is FAIL")

        if self.config.missing_value_policy == MissingValuePolicy.LEAVE_UNCHANGED:
            issues.append(CleaningIssue(
                issue_type=CleaningIssueType.MISSING_VALUE,
                message=f"Found {total_missing} missing values. Policy LEAVE_UNCHANGED.",
                action_taken="LEAVE_UNCHANGED"
            ))
            return df, 0, 0

        action = self.config.missing_value_policy.value
        filled = 0
        before_nas = df.isna().sum().sum()

        if self.config.missing_value_policy == MissingValuePolicy.FORWARD_FILL:
            df = df.ffill()
        elif self.config.missing_value_policy == MissingValuePolicy.BACKWARD_FILL:
            df = df.bfill()
        elif self.config.missing_value_policy == MissingValuePolicy.INTERPOLATE:
            df = df.interpolate()

        after_fill_nas = df.isna().sum().sum()
        filled = before_nas - after_fill_nas

        if filled > 0:
            issues.append(CleaningIssue(
                issue_type=CleaningIssueType.MISSING_VALUE,
                message=f"Filled {filled} missing values.",
                action_taken=action
            ))

        dropped = 0
        # If policy is DROP_ROW or there are still NaNs after fill
        if self.config.missing_value_policy == MissingValuePolicy.DROP_ROW or after_fill_nas > 0:
            before_len = len(df)
            df = df.dropna()
            dropped = before_len - len(df)

            if dropped > 0:
                issues.append(CleaningIssue(
                    issue_type=CleaningIssueType.MISSING_VALUE,
                    message=f"Dropped {dropped} rows containing NaNs.",
                    affected_rows=dropped,
                    action_taken="DROP_ROW"
                ))

        return df, filled, dropped

    def _detect_extreme_returns(self, df: pd.DataFrame, symbol: str, issues: list) -> tuple[pd.DataFrame, int]:
        if len(df) < 2 or "close" not in df.columns:
            return df, 0

        returns = df["close"].pct_change().abs()
        mask = returns > self.config.max_daily_return_abs
        extreme_count = mask.sum()

        if extreme_count == 0:
            return df, 0

        df, count = self._apply_outlier_policy(df, mask, symbol, CleaningIssueType.EXTREME_RETURN, f"extreme returns > {self.config.max_daily_return_abs}", issues)
        return df, count

    def _detect_extreme_volume(self, df: pd.DataFrame, symbol: str, issues: list) -> tuple[pd.DataFrame, int]:
        if len(df) < 2 or "volume" not in df.columns:
            return df, 0

        vol = df["volume"]
        std = vol.std()
        if std == 0 or pd.isna(std):
            return df, 0

        zscores = ((vol - vol.mean()) / std).abs()
        mask = zscores > self.config.max_volume_zscore
        extreme_count = mask.sum()

        if extreme_count == 0:
            return df, 0

        df, count = self._apply_outlier_policy(df, mask, symbol, CleaningIssueType.EXTREME_VOLUME, f"extreme volume z-score > {self.config.max_volume_zscore}", issues)
        return df, count

    def _apply_outlier_policy(self, df: pd.DataFrame, mask: pd.Series, symbol: str, issue_type: CleaningIssueType, reason: str, issues: list) -> tuple[pd.DataFrame, int]:
        count = mask.sum()

        if self.config.outlier_policy.value == "FAIL":
            raise DataCleaningError(f"Outliers found for {symbol}: {reason} and policy is FAIL")

        action = self.config.outlier_policy.value

        if self.config.outlier_policy.value == "DROP_ROW":
            df = df[~mask]
        elif self.config.outlier_policy.value == "WINSORIZE":
             # simple implementation skips for now, acts like FLAG_ONLY
             action = "SKIPPED_WINSORIZE"

        issues.append(CleaningIssue(
            issue_type=issue_type,
            message=f"Found {count} {reason}.",
            affected_rows=count,
            action_taken=action
        ))

        return df, count

    def _calculate_usability(self, df: pd.DataFrame, output_rows: int) -> tuple[bool, bool]:
        if output_rows < self.config.min_rows_after_cleaning:
            return False, False

        usable_backtest = True
        usable_ml = True

        if df.isna().any().any():
            usable_ml = False

        return usable_backtest, usable_ml
