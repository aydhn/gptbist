from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field


class DataQualitySeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class DataQualityIssueType(str, Enum):
    EMPTY_DATA = "EMPTY_DATA"
    MISSING_COLUMNS = "MISSING_COLUMNS"
    NON_DATETIME_INDEX = "NON_DATETIME_INDEX"
    UNSORTED_INDEX = "UNSORTED_INDEX"
    DUPLICATE_TIMESTAMPS = "DUPLICATE_TIMESTAMPS"
    MISSING_VALUES = "MISSING_VALUES"
    NON_NUMERIC_VALUES = "NON_NUMERIC_VALUES"
    NEGATIVE_PRICE = "NEGATIVE_PRICE"
    NEGATIVE_VOLUME = "NEGATIVE_VOLUME"
    INVALID_OHLC_RELATION = "INVALID_OHLC_RELATION"
    ZERO_VOLUME_SERIES = "ZERO_VOLUME_SERIES"
    LARGE_DATE_GAP = "LARGE_DATE_GAP"
    EXTREME_RETURN = "EXTREME_RETURN"
    INSUFFICIENT_ROWS = "INSUFFICIENT_ROWS"
    UNKNOWN = "UNKNOWN"

class DataQualityIssue(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    issue_type: DataQualityIssueType
    severity: DataQualitySeverity
    symbol: str | None = None
    timeframe: str | None = None
    message: str
    affected_rows: int | None = None
    affected_columns: list[str] = Field(default_factory=list)
    sample_timestamps: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DataQualityReport(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    symbol: str
    timeframe: str
    source: str
    row_count: int
    start: datetime | None = None
    end: datetime | None = None
    issues: list[DataQualityIssue] = Field(default_factory=list)
    score: float = 100.0
    passed: bool = True
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    def has_errors(self) -> bool:
        return any(issue.severity == DataQualitySeverity.ERROR for issue in self.issues)

    def has_critical(self) -> bool:
        return any(issue.severity == DataQualitySeverity.CRITICAL for issue in self.issues)

    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == DataQualitySeverity.WARNING)

    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == DataQualitySeverity.ERROR)

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "score": self.score,
            "passed": self.passed,
            "total_issues": len(self.issues),
            "critical": self.has_critical(),
            "errors": self.error_count(),
            "warnings": self.warning_count()
        }

class DataQualityChecker:
    def __init__(
        self,
        min_rows: int = 100,
        max_daily_return_abs: float = 0.35,
        max_allowed_gap_days: int = 10,
        fail_on_error: bool = False
    ):
        self.min_rows = min_rows
        self.max_daily_return_abs = max_daily_return_abs
        self.max_allowed_gap_days = max_allowed_gap_days
        self.fail_on_error = fail_on_error

        self.required_columns = {"open", "high", "low", "close", "volume"}

    def check(self, market_data: Any) -> DataQualityReport:
        # Avoid circular imports by duck-typing or using Any
        symbol = getattr(market_data, "symbol", "UNKNOWN")
        timeframe = getattr(market_data, "timeframe", "UNKNOWN")
        source = getattr(market_data, "source", "UNKNOWN")

        if hasattr(timeframe, 'value'):
            timeframe = timeframe.value
        if hasattr(source, 'value'):
            source = source.value

        start, end = None, None
        if hasattr(market_data, 'date_range'):
            start, end = market_data.date_range()

        row_count = 0
        if hasattr(market_data, 'row_count'):
            row_count = market_data.row_count()

        df = getattr(market_data, 'data', pd.DataFrame())

        report = DataQualityReport(
            symbol=symbol,
            timeframe=timeframe,
            source=source,
            row_count=row_count,
            start=start,
            end=end,
        )

        self._check_empty(df, report)
        if report.has_critical():
            # If empty, no further checks make sense
            self._calculate_score(report)
            return report

        self._check_required_columns(df, report)
        if report.has_critical():
            # If missing columns, many other checks will crash
            self._calculate_score(report)
            return report

        self._check_datetime_index(df, report)
        self._check_sorted_index(df, report)
        self._check_duplicate_timestamps(df, report)
        self._check_missing_values(df, report)
        self._check_numeric_columns(df, report)

        # Following checks assume numeric columns exist and are mostly well-formed
        self._check_negative_values(df, report)
        self._check_ohlc_relations(df, report)
        self._check_zero_volume_series(df, report)

        if timeframe == '1d' or str(timeframe).lower() == '1d':
            self._check_large_date_gaps(df, report)

        self._check_extreme_returns(df, report)
        self._check_minimum_rows(df, report)

        self._calculate_score(report)
        return report

    def _add_issue(self, report: DataQualityReport, issue_type: DataQualityIssueType, severity: DataQualitySeverity, message: str, **kwargs):
        issue = DataQualityIssue(
            issue_type=issue_type,
            severity=severity,
            symbol=report.symbol,
            timeframe=report.timeframe,
            message=message,
            **kwargs
        )
        report.issues.append(issue)

    def _check_empty(self, df: pd.DataFrame, report: DataQualityReport):
        if df is None or df.empty:
            self._add_issue(
                report,
                DataQualityIssueType.EMPTY_DATA,
                DataQualitySeverity.CRITICAL,
                f"Data is empty for symbol {report.symbol}."
            )

    def _check_required_columns(self, df: pd.DataFrame, report: DataQualityReport):
        missing = [col for col in self.required_columns if col not in df.columns]
        if missing:
            self._add_issue(
                report,
                DataQualityIssueType.MISSING_COLUMNS,
                DataQualitySeverity.CRITICAL,
                f"Missing required columns: {missing}",
                affected_columns=missing
            )

    def _check_datetime_index(self, df: pd.DataFrame, report: DataQualityReport):
        if not isinstance(df.index, pd.DatetimeIndex):
            self._add_issue(
                report,
                DataQualityIssueType.NON_DATETIME_INDEX,
                DataQualitySeverity.ERROR,
                "Index is not a DatetimeIndex."
            )

    def _check_sorted_index(self, df: pd.DataFrame, report: DataQualityReport):
        if isinstance(df.index, pd.DatetimeIndex):
            if not df.index.is_monotonic_increasing:
                self._add_issue(
                    report,
                    DataQualityIssueType.UNSORTED_INDEX,
                    DataQualitySeverity.ERROR,
                    "Index is not sorted in increasing order."
                )

    def _check_duplicate_timestamps(self, df: pd.DataFrame, report: DataQualityReport):
        if df.index.has_duplicates:
            dups = df.index[df.index.duplicated()].unique()
            self._add_issue(
                report,
                DataQualityIssueType.DUPLICATE_TIMESTAMPS,
                DataQualitySeverity.ERROR,
                f"Found {len(dups)} duplicate timestamps.",
                affected_rows=df.index.duplicated().sum(),
                sample_timestamps=[str(t) for t in dups[:5]]
            )

    def _check_missing_values(self, df: pd.DataFrame, report: DataQualityReport):
        for col in self.required_columns:
            if col in df.columns:
                na_count = df[col].isna().sum()
                if na_count > 0:
                    self._add_issue(
                        report,
                        DataQualityIssueType.MISSING_VALUES,
                        DataQualitySeverity.ERROR,
                        f"Found {na_count} missing values in column '{col}'.",
                        affected_rows=int(na_count),
                        affected_columns=[col]
                    )

    def _check_numeric_columns(self, df: pd.DataFrame, report: DataQualityReport):
        for col in self.required_columns:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    self._add_issue(
                        report,
                        DataQualityIssueType.NON_NUMERIC_VALUES,
                        DataQualitySeverity.CRITICAL,
                        f"Column '{col}' is not numeric.",
                        affected_columns=[col]
                    )

    def _check_negative_values(self, df: pd.DataFrame, report: DataQualityReport):
        for col in ["open", "high", "low", "close"]:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                neg_count = (df[col] < 0).sum()
                if neg_count > 0:
                    self._add_issue(
                        report,
                        DataQualityIssueType.NEGATIVE_PRICE,
                        DataQualitySeverity.ERROR,
                        f"Found {neg_count} negative values in price column '{col}'.",
                        affected_rows=int(neg_count),
                        affected_columns=[col]
                    )

        if "volume" in df.columns and pd.api.types.is_numeric_dtype(df["volume"]):
            neg_vol = (df["volume"] < 0).sum()
            if neg_vol > 0:
                self._add_issue(
                    report,
                    DataQualityIssueType.NEGATIVE_VOLUME,
                    DataQualitySeverity.ERROR,
                    f"Found {neg_vol} negative volume values.",
                    affected_rows=int(neg_vol),
                    affected_columns=["volume"]
                )

    def _check_ohlc_relations(self, df: pd.DataFrame, report: DataQualityReport):
        if all(col in df.columns and pd.api.types.is_numeric_dtype(df[col]) for col in ["open", "high", "low", "close"]):
            high_low = (df["high"] < df["low"]).sum()
            if high_low > 0:
                self._add_issue(
                    report,
                    DataQualityIssueType.INVALID_OHLC_RELATION,
                    DataQualitySeverity.ERROR,
                    f"Found {high_low} rows where high < low.",
                    affected_rows=int(high_low)
                )

            high_open = (df["high"] < df["open"]).sum()
            if high_open > 0:
                self._add_issue(
                    report,
                    DataQualityIssueType.INVALID_OHLC_RELATION,
                    DataQualitySeverity.ERROR,
                    f"Found {high_open} rows where high < open.",
                    affected_rows=int(high_open)
                )

            high_close = (df["high"] < df["close"]).sum()
            if high_close > 0:
                self._add_issue(
                    report,
                    DataQualityIssueType.INVALID_OHLC_RELATION,
                    DataQualitySeverity.ERROR,
                    f"Found {high_close} rows where high < close.",
                    affected_rows=int(high_close)
                )

            low_open = (df["low"] > df["open"]).sum()
            if low_open > 0:
                self._add_issue(
                    report,
                    DataQualityIssueType.INVALID_OHLC_RELATION,
                    DataQualitySeverity.ERROR,
                    f"Found {low_open} rows where low > open.",
                    affected_rows=int(low_open)
                )

            low_close = (df["low"] > df["close"]).sum()
            if low_close > 0:
                self._add_issue(
                    report,
                    DataQualityIssueType.INVALID_OHLC_RELATION,
                    DataQualitySeverity.ERROR,
                    f"Found {low_close} rows where low > close.",
                    affected_rows=int(low_close)
                )

    def _check_zero_volume_series(self, df: pd.DataFrame, report: DataQualityReport):
        if "volume" in df.columns and pd.api.types.is_numeric_dtype(df["volume"]):
            if len(df) > 0 and (df["volume"] == 0).all():
                self._add_issue(
                    report,
                    DataQualityIssueType.ZERO_VOLUME_SERIES,
                    DataQualitySeverity.WARNING,
                    "Volume is zero for the entire series.",
                    affected_columns=["volume"]
                )

    def _check_large_date_gaps(self, df: pd.DataFrame, report: DataQualityReport):
        # TODO: Phase 6 sonrası, market calendar ile entegre edilerek hafta sonları ve tatiller gap hesabından düşülebilir.
        if isinstance(df.index, pd.DatetimeIndex) and len(df) > 1:
            gaps = df.index.to_series().diff()
            large_gaps = gaps[gaps > pd.Timedelta(days=self.max_allowed_gap_days)]
            if not large_gaps.empty:
                self._add_issue(
                    report,
                    DataQualityIssueType.LARGE_DATE_GAP,
                    DataQualitySeverity.WARNING,
                    f"Found {len(large_gaps)} date gaps larger than {self.max_allowed_gap_days} days.",
                    affected_rows=len(large_gaps),
                    sample_timestamps=[str(t) for t in large_gaps.index[:5]]
                )

    def _check_extreme_returns(self, df: pd.DataFrame, report: DataQualityReport):
        if "close" in df.columns and pd.api.types.is_numeric_dtype(df["close"]) and len(df) > 1:
            returns = df["close"].pct_change().abs()
            extreme = returns[returns > self.max_daily_return_abs]
            if not extreme.empty:
                self._add_issue(
                    report,
                    DataQualityIssueType.EXTREME_RETURN,
                    DataQualitySeverity.WARNING,
                    f"Found {len(extreme)} extreme daily returns > {self.max_daily_return_abs * 100}%.",
                    affected_rows=len(extreme),
                    sample_timestamps=[str(t) for t in extreme.index[:5]]
                )

    def _check_minimum_rows(self, df: pd.DataFrame, report: DataQualityReport):
        if len(df) < self.min_rows:
            self._add_issue(
                report,
                DataQualityIssueType.INSUFFICIENT_ROWS,
                DataQualitySeverity.WARNING,
                f"Row count ({len(df)}) is less than minimum required ({self.min_rows}).",
                affected_rows=len(df)
            )

    def _calculate_score(self, report: DataQualityReport):
        score = 100.0

        if report.has_critical():
            score = min(score, 20.0)
            report.passed = False

        for issue in report.issues:
            if issue.severity == DataQualitySeverity.CRITICAL:
                pass # Already handled
            elif issue.severity == DataQualitySeverity.ERROR:
                score -= 10.0
            elif issue.severity == DataQualitySeverity.WARNING:
                score -= 2.0

        report.score = max(0.0, score)

        if report.has_critical() or report.has_errors():
            report.passed = False
