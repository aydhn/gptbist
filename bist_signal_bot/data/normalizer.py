import re
import time
from datetime import datetime, UTC
from typing import Any  # noqa: F401
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import DataNormalizationError
from bist_signal_bot.data.models import (
    DataVendor,
    MarketDataFrame,
    NormalizationIssue,
    NormalizationIssueType,
    NormalizationReport,
    NormalizationStatus,
    NormalizedMarketData,
    Timeframe,
)
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol


class MarketDataNormalizer:
    """
    Normalizes OHLCV data coming from various providers or local storage into a standard internal schema.
    """

    # Column aliases to map to internal standard names
    COLUMN_ALIASES = {
        "open": ["open", "price_open", "o"],
        "high": ["high", "price_high", "h"],
        "low": ["low", "price_low", "l"],
        "close": ["close", "price_close", "c", "last"],
        "volume": ["volume", "vol", "işlem hacmi", "islem_hacmi"],
        "adj_close": ["adj close", "adj_close", "adjusted_close"],
        "dividends": ["dividends"],
        "stock_splits": ["stock splits", "stock_splits"]
    }

    TIMESTAMP_ALIASES = ["date", "datetime", "timestamp", "time", "tarih"]

    STANDARD_COLUMN_ORDER = ["open", "high", "low", "close", "volume", "adj_close", "dividends", "stock_splits"]
    REQUIRED_COLUMNS = {"open", "high", "low", "close", "volume"}

    def __init__(
        self,
        settings: Settings | None = None,
        target_timezone: str = "Europe/Istanbul",
        drop_unknown_columns: bool = False,
        deduplicate_index: bool = True,
        sort_index: bool = True,
        strict: bool = False
    ):
        self.settings = settings
        self.target_timezone = target_timezone
        self.drop_unknown_columns = drop_unknown_columns
        self.deduplicate_index = deduplicate_index
        self.sort_index = sort_index
        self.strict = strict

        if settings:
            self.target_timezone = settings.MARKET_TIMEZONE
            if hasattr(settings, "NORMALIZATION_DROP_UNKNOWN_COLUMNS"):
                self.drop_unknown_columns = settings.NORMALIZATION_DROP_UNKNOWN_COLUMNS
            if hasattr(settings, "NORMALIZATION_DEDUPLICATE_INDEX"):
                self.deduplicate_index = settings.NORMALIZATION_DEDUPLICATE_INDEX
            if hasattr(settings, "NORMALIZATION_SORT_INDEX"):
                self.sort_index = settings.NORMALIZATION_SORT_INDEX
            if hasattr(settings, "NORMALIZATION_STRICT"):
                self.strict = settings.NORMALIZATION_STRICT
            if hasattr(settings, "NORMALIZATION_TARGET_TIMEZONE") and settings.NORMALIZATION_TARGET_TIMEZONE:
                self.target_timezone = settings.NORMALIZATION_TARGET_TIMEZONE

    def _normalize_symbol_with_issues(self, symbol: str) -> tuple[str, list[NormalizationIssue]]:
        issues = []
        try:
            symbol = ensure_valid_internal_symbol(symbol)
        except Exception as e:
            if self.strict:
                raise DataNormalizationError(f"Invalid symbol format: {e}")
            issues.append(NormalizationIssue(
                issue_type=NormalizationIssueType.SYMBOL_NORMALIZED,
                message=f"Failed to normalize symbol {symbol}: {e}"
            ))
        return symbol, issues

    def _apply_dataframe_transformations(
        self, df: pd.DataFrame, symbol: str
    ) -> tuple[pd.DataFrame, list[NormalizationIssue], NormalizationStatus]:
        issues = []
        status = NormalizationStatus.SUCCESS

        if df.empty:
            issues.append(NormalizationIssue(
                issue_type=NormalizationIssueType.EMPTY_DATA,
                message="Input DataFrame is empty."
            ))
            return df.copy(), issues, NormalizationStatus.WARNING

        df_norm = df.copy()

        df_norm, mi_issues = self.flatten_multiindex_columns(df_norm)
        issues.extend(mi_issues)

        df_norm, col_issues = self.normalize_columns(df_norm)
        issues.extend(col_issues)

        df_norm, idx_issues = self.normalize_index(df_norm)
        issues.extend(idx_issues)

        df_norm, num_issues = self.normalize_numeric_columns(df_norm)
        issues.extend(num_issues)

        missing_cols = self.REQUIRED_COLUMNS - set(df_norm.columns)
        if missing_cols:
            issues.append(NormalizationIssue(
                issue_type=NormalizationIssueType.COLUMN_MISSING,
                message=f"Missing required columns: {missing_cols}",
                affected_columns=list(missing_cols)
            ))
            status = NormalizationStatus.FAILED
            if self.strict:
                raise DataNormalizationError(f"[{symbol}] Missing required columns: {missing_cols}")

        df_norm = self.standardize_column_order(df_norm)
        return df_norm, issues, status

    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: Timeframe | str,
        source: DataVendor | str,
        adjusted: bool = True
    ) -> NormalizedMarketData:
        start_time = time.time()

        symbol, sym_issues = self._normalize_symbol_with_issues(symbol)

        timeframe_obj = timeframe if isinstance(timeframe, Timeframe) else Timeframe(timeframe)
        source_obj = source if isinstance(source, DataVendor) else DataVendor(source)

        input_rows = len(df)
        input_columns = [str(c) for c in df.columns]

        df_norm, df_issues, status = self._apply_dataframe_transformations(df, symbol)

        issues = sym_issues + df_issues

        output_rows = len(df_norm)
        output_columns = list(df_norm.columns)
        elapsed = time.time() - start_time

        if status != NormalizationStatus.FAILED and issues:
            status = NormalizationStatus.WARNING

        report = NormalizationReport(
            symbol=symbol,
            timeframe=timeframe_obj.value,
            source=source_obj.value,
            status=status,
            input_rows=input_rows,
            output_rows=output_rows,
            input_columns=input_columns,
            output_columns=output_columns,
            issues=issues,
            started_at=datetime.fromtimestamp(start_time, UTC),
            finished_at=datetime.fromtimestamp(start_time + elapsed, UTC),
            elapsed_seconds=elapsed
        )

        metadata = {
            "normalized": True,
            "normalization_status": status.value,
            "normalization_issue_count": len(issues),
            "normalization_elapsed_seconds": elapsed,
            "original_columns": input_columns,
            "normalized_columns": output_columns,
            "target_timezone": self.target_timezone
        }

        mdf = MarketDataFrame(
            symbol=symbol,
            timeframe=timeframe_obj,
            source=source_obj,
            data=df_norm,
            fetched_at=datetime.now(UTC),
            adjusted=adjusted,
            metadata=metadata
        )

        return NormalizedMarketData(market_data=mdf, report=report)

    def normalize_market_data(self, market_data: MarketDataFrame) -> NormalizedMarketData:
        res = self.normalize_dataframe(
            df=market_data.data,
            symbol=market_data.symbol,
            timeframe=market_data.timeframe,
            source=market_data.source,
            adjusted=market_data.adjusted
        )

        # Merge original metadata with normalization metadata
        orig_meta = market_data.metadata.copy()
        orig_meta.update(res.market_data.metadata)
        res.market_data.metadata = orig_meta

        # Preserve quality report if any
        res.market_data.quality_report = market_data.quality_report

        return res

    def flatten_multiindex_columns(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[NormalizationIssue]]:
        issues = []
        if isinstance(df.columns, pd.MultiIndex):
            # typically provider sends tuples like ('Open', 'ASELS.IS')
            # we just take the first level assuming it represents the OHLCV field
            try:
                new_cols = [str(col[0]) for col in df.columns]
                df.columns = new_cols
                issues.append(NormalizationIssue(
                    issue_type=NormalizationIssueType.MULTIINDEX_FLATTENED,
                    message="MultiIndex columns were flattened to single level."
                ))
            except Exception as e:
                if self.strict:
                    raise DataNormalizationError(f"Failed to flatten MultiIndex columns: {e}")
                issues.append(NormalizationIssue(
                    issue_type=NormalizationIssueType.UNKNOWN,
                    message=f"Failed to flatten MultiIndex: {e}"
                ))
        return df, issues

    def _clean_column_name(self, col: str) -> str:
        c = str(col).strip().lower()
        # Tr translations
        c = c.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
        c = re.sub(r'[\s\-/\\]+', '_', c)
        c = re.sub(r'_+', '_', c)
        return c.strip('_')

    def normalize_columns(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[NormalizationIssue]]:
        issues = []
        rename_map = {}
        drop_cols = []

        # Build reverse lookup for aliases
        alias_to_std = {}
        for std, aliases in self.COLUMN_ALIASES.items():
            for alias in aliases:
                alias_to_std[self._clean_column_name(alias)] = std

        for ts_alias in self.TIMESTAMP_ALIASES:
            alias_to_std[self._clean_column_name(ts_alias)] = "timestamp"

        for orig_col in df.columns:
            cleaned = self._clean_column_name(orig_col)

            if cleaned in alias_to_std:
                std_col = alias_to_std[cleaned]
                if orig_col != std_col:
                    rename_map[orig_col] = std_col
            else:
                if self.drop_unknown_columns:
                    drop_cols.append(orig_col)
                elif orig_col != cleaned:
                    rename_map[orig_col] = cleaned

        if rename_map:
            df.rename(columns=rename_map, inplace=True)
            issues.append(NormalizationIssue(
                issue_type=NormalizationIssueType.COLUMN_RENAMED,
                message=f"Columns renamed: {rename_map}",
                affected_columns=list(rename_map.values())
            ))

        if drop_cols:
            df.drop(columns=drop_cols, inplace=True)
            issues.append(NormalizationIssue(
                issue_type=NormalizationIssueType.COLUMN_DROPPED,
                message=f"Unknown columns dropped: {drop_cols}",
                affected_columns=drop_cols
            ))

        return df, issues

    def normalize_index(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[NormalizationIssue]]:
        issues = []

        if not isinstance(df.index, pd.DatetimeIndex):
            if "timestamp" in df.columns:
                try:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df.set_index("timestamp", inplace=True)
                    issues.append(NormalizationIssue(
                        issue_type=NormalizationIssueType.TIMESTAMP_INDEX_CREATED,
                        message="Created DatetimeIndex from timestamp column."
                    ))
                except Exception as e:
                    if self.strict:
                        raise DataNormalizationError(f"Failed to parse timestamp column: {e}")
                    issues.append(NormalizationIssue(
                        issue_type=NormalizationIssueType.UNKNOWN,
                        message=f"Failed to parse timestamp: {e}"
                    ))
            else:
                if self.strict:
                    raise DataNormalizationError("DataFrame index is not DatetimeIndex and no timestamp column found.")

        if isinstance(df.index, pd.DatetimeIndex):
            df.index.name = "timestamp"

            if df.index.tz is None:
                df.index = df.index.tz_localize(self.target_timezone)
                issues.append(NormalizationIssue(
                    issue_type=NormalizationIssueType.TIMEZONE_LOCALIZED,
                    message=f"Localized naive index to {self.target_timezone}"
                ))
            elif str(df.index.tz) != self.target_timezone:
                df.index = df.index.tz_convert(self.target_timezone)
                issues.append(NormalizationIssue(
                    issue_type=NormalizationIssueType.TIMEZONE_CONVERTED,
                    message=f"Converted index timezone to {self.target_timezone}"
                ))

            if self.sort_index and not df.index.is_monotonic_increasing:
                df.sort_index(inplace=True)
                issues.append(NormalizationIssue(
                    issue_type=NormalizationIssueType.INDEX_SORTED,
                    message="Index was sorted."
                ))

            if df.index.has_duplicates:
                dups = df.index.duplicated(keep="last").sum()
                if self.deduplicate_index:
                    df = df[~df.index.duplicated(keep="last")]
                    issues.append(NormalizationIssue(
                        issue_type=NormalizationIssueType.DUPLICATE_TIMESTAMP_REMOVED,
                        message=f"Removed {dups} duplicate timestamps, keeping last.",
                        affected_rows=dups
                    ))
                else:
                    msg = f"Found {dups} duplicate timestamps."
                    if self.strict:
                        raise DataNormalizationError(msg)
                    issues.append(NormalizationIssue(
                        issue_type=NormalizationIssueType.WARNING,
                        message=msg,
                        affected_rows=dups
                    ))

        return df, issues

    def normalize_numeric_columns(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[NormalizationIssue]]:
        issues = []
        num_cols = ["open", "high", "low", "close", "volume", "adj_close", "dividends", "stock_splits"]

        affected = []
        for col in num_cols:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        # Attempt comma to dot replacement for strings before parsing
                        if df[col].dtype == object:
                            df[col] = df[col].astype(str).str.replace(',', '.')
                        elif pd.api.types.is_string_dtype(df[col]):
                            df[col] = df[col].str.replace(',', '.')
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        affected.append(col)
                    except Exception as e:
                        if self.strict:
                            raise DataNormalizationError(f"Failed to cast column {col} to numeric: {e}")

        if affected:
            issues.append(NormalizationIssue(
                issue_type=NormalizationIssueType.NUMERIC_CAST,
                message=f"Cast columns to numeric: {affected}",
                affected_columns=affected
            ))

        return df, issues

    def standardize_column_order(self, df: pd.DataFrame) -> pd.DataFrame:
        ordered_cols = []
        for col in self.STANDARD_COLUMN_ORDER:
            if col in df.columns:
                ordered_cols.append(col)

        for col in df.columns:
            if col not in ordered_cols:
                ordered_cols.append(col)

        return df[ordered_cols]
