from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

from bist_signal_bot.core.constants import DEFAULT_CURRENCY, DEFAULT_MARKET
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol


class AssetType(str, Enum):
    EQUITY = "EQUITY"
    INDEX = "INDEX"
    ETF = "ETF"
    UNKNOWN = "UNKNOWN"
    MOCK = "MOCK"

class Market(str, Enum):
    BIST = "BIST"

class SymbolGroup(str, Enum):
    BIST30 = "BIST30"
    BIST50 = "BIST50"
    BIST100 = "BIST100"
    LIQUID = "LIQUID"
    WATCHLIST = "WATCHLIST"
    CUSTOM = "CUSTOM"
    TEST = "TEST"

class DataVendor(str, Enum):
    INTERNAL = "INTERNAL"
    YFINANCE = "YFINANCE"
    LOCAL = "LOCAL"
    UNKNOWN = "UNKNOWN"
    MOCK = "MOCK"

class SymbolInfo(BaseModel):
    symbol: str
    name: str | None = None
    market: Market = Market(DEFAULT_MARKET)
    asset_type: AssetType = AssetType.EQUITY
    currency: str = DEFAULT_CURRENCY
    groups: set[SymbolGroup] = Field(default_factory=set)
    is_active: bool = True
    notes: str | None = None

    @field_validator("symbol", mode="before")
    def validate_symbol(cls, v):
        if not v:
            raise ValueError("Symbol cannot be empty.")
        return ensure_valid_internal_symbol(v)

from datetime import UTC, datetime, date
from typing import Any
from enum import Enum

import pandas as pd

from bist_signal_bot.core.exceptions import DataProviderValidationError


class Timeframe(str, Enum):
    DAILY = "1d"
    WEEKLY = "1wk"
    MONTHLY = "1mo"
    HOURLY = "1h"
    FIFTEEN_MIN = "15m"
    FIVE_MIN = "5m"

class OHLCVBar(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    timeframe: Timeframe
    source: DataVendor

    @field_validator("symbol", mode="before")
    def validate_symbol(cls, v):
        if not v:
            raise ValueError("Symbol cannot be empty.")
        return ensure_valid_internal_symbol(v)

    @field_validator("open", "high", "low", "close", "volume")
    def validate_positive(cls, v, info):
        if v < 0:
            raise ValueError(f"{info.field_name} cannot be negative.")
        return v

    def model_post_init(self, __context: Any) -> None:
        if self.high < self.low:
            raise ValueError("high cannot be less than low.")
        # Ensure timezone info exists
        from bist_signal_bot.core.time_utils import ensure_timezone
        self.timestamp = ensure_timezone(self.timestamp)

class MarketDataFrame(BaseModel):
    symbol: str
    timeframe: Timeframe
    source: DataVendor
    data: Any # Cannot use pd.DataFrame directly with Pydantic easily without arbitrary_types_allowed
    fetched_at: datetime
    adjusted: bool = True
    quality_report: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "arbitrary_types_allowed": True
    }

    @field_validator("symbol", mode="before")
    def validate_symbol(cls, v):
        if not v:
            raise ValueError("Symbol cannot be empty.")
        return ensure_valid_internal_symbol(v)

    def validate_schema(self) -> None:
        if not isinstance(self.data, pd.DataFrame):
            raise DataProviderValidationError("Data must be a pandas DataFrame.")
        if self.data.empty:
            return

        # Lowercase columns
        self.data.columns = [str(c).lower() for c in self.data.columns]

        required_cols = {"open", "high", "low", "close", "volume"}
        if not required_cols.issubset(self.data.columns):
            raise DataProviderValidationError(f"Missing required columns. Expected at least: {required_cols}")

        for col in ["open", "high", "low", "close", "volume"]:
            if not pd.api.types.is_numeric_dtype(self.data[col]):
                raise DataProviderValidationError(f"Column {col} must be numeric.")

    def is_empty(self) -> bool:
        if not isinstance(self.data, pd.DataFrame):
            return True
        return self.data.empty

    def row_count(self) -> int:
        if not isinstance(self.data, pd.DataFrame):
            return 0
        return len(self.data)

    def date_range(self) -> tuple[datetime | None, datetime | None]:
        if self.is_empty():
            return None, None
        if not isinstance(self.data.index, pd.DatetimeIndex):
            return None, None
        return self.data.index.min().to_pydatetime(), self.data.index.max().to_pydatetime()



class NormalizationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class NormalizationIssueType(str, Enum):
    COLUMN_RENAMED = "COLUMN_RENAMED"
    COLUMN_MISSING = "COLUMN_MISSING"
    COLUMN_DROPPED = "COLUMN_DROPPED"
    MULTIINDEX_FLATTENED = "MULTIINDEX_FLATTENED"
    TIMESTAMP_INDEX_CREATED = "TIMESTAMP_INDEX_CREATED"
    TIMEZONE_LOCALIZED = "TIMEZONE_LOCALIZED"
    TIMEZONE_CONVERTED = "TIMEZONE_CONVERTED"
    NUMERIC_CAST = "NUMERIC_CAST"
    DUPLICATE_TIMESTAMP_REMOVED = "DUPLICATE_TIMESTAMP_REMOVED"
    INDEX_SORTED = "INDEX_SORTED"
    SYMBOL_NORMALIZED = "SYMBOL_NORMALIZED"
    TIMEFRAME_NORMALIZED = "TIMEFRAME_NORMALIZED"
    EMPTY_DATA = "EMPTY_DATA"
    UNKNOWN = "UNKNOWN"
    MOCK = "MOCK"

class NormalizationIssue(BaseModel):
    issue_type: NormalizationIssueType
    message: str
    affected_columns: list[str] = Field(default_factory=list)
    affected_rows: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class NormalizationReport(BaseModel):
    symbol: str
    timeframe: str
    source: str
    status: NormalizationStatus
    input_rows: int
    output_rows: int
    input_columns: list[str] = Field(default_factory=list)
    output_columns: list[str] = Field(default_factory=list)
    issues: list[NormalizationIssue] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float

    def issue_count(self) -> int:
        return len(self.issues)

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "source": self.source,
            "status": self.status.value,
            "input_rows": self.input_rows,
            "output_rows": self.output_rows,
            "issue_count": self.issue_count(),
            "elapsed_seconds": self.elapsed_seconds,
        }


class NormalizedMarketData(BaseModel):
    market_data: MarketDataFrame
    report: NormalizationReport

class CleaningStatus(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class MissingValuePolicy(str, Enum):
    DROP_ROW = "DROP_ROW"
    FORWARD_FILL = "FORWARD_FILL"
    BACKWARD_FILL = "BACKWARD_FILL"
    INTERPOLATE = "INTERPOLATE"
    LEAVE_UNCHANGED = "LEAVE_UNCHANGED"
    FAIL = "FAIL"

class InvalidOhlcPolicy(str, Enum):
    DROP_ROW = "DROP_ROW"
    LEAVE_UNCHANGED = "LEAVE_UNCHANGED"
    FAIL = "FAIL"

class OutlierPolicy(str, Enum):
    FLAG_ONLY = "FLAG_ONLY"
    DROP_ROW = "DROP_ROW"
    WINSORIZE = "WINSORIZE"
    LEAVE_UNCHANGED = "LEAVE_UNCHANGED"
    FAIL = "FAIL"

class DuplicateTimestampPolicy(str, Enum):
    KEEP_LAST = "KEEP_LAST"
    KEEP_FIRST = "KEEP_FIRST"
    DROP_ALL = "DROP_ALL"
    FAIL = "FAIL"

class CleaningIssueType(str, Enum):
    MISSING_VALUE = "MISSING_VALUE"
    INVALID_OHLC = "INVALID_OHLC"
    NEGATIVE_PRICE = "NEGATIVE_PRICE"
    NEGATIVE_VOLUME = "NEGATIVE_VOLUME"
    ZERO_PRICE = "ZERO_PRICE"
    DUPLICATE_TIMESTAMP = "DUPLICATE_TIMESTAMP"
    EXTREME_RETURN = "EXTREME_RETURN"
    EXTREME_VOLUME = "EXTREME_VOLUME"
    EMPTY_ROW = "EMPTY_ROW"
    ROW_DROPPED = "ROW_DROPPED"
    VALUE_FILLED = "VALUE_FILLED"
    VALUE_WINSORIZED = "VALUE_WINSORIZED"
    INSUFFICIENT_ROWS_AFTER_CLEANING = "INSUFFICIENT_ROWS_AFTER_CLEANING"
    UNKNOWN = "UNKNOWN"

class CleaningIssue(BaseModel):
    issue_type: CleaningIssueType
    message: str
    affected_rows: int | None = None
    affected_columns: list[str] = Field(default_factory=list)
    sample_timestamps: list[str] = Field(default_factory=list)
    action_taken: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class CleaningReport(BaseModel):
    symbol: str
    timeframe: str
    source: str
    status: CleaningStatus
    input_rows: int
    output_rows: int
    dropped_rows: int = 0
    filled_values: int = 0
    flagged_outliers: int = 0
    winsorized_values: int = 0
    issues: list[CleaningIssue] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float
    usable_for_backtest: bool
    usable_for_ml: bool

    def issue_count(self) -> int:
        return len(self.issues)

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "source": self.source,
            "status": self.status.value,
            "input_rows": self.input_rows,
            "output_rows": self.output_rows,
            "dropped_rows": self.dropped_rows,
            "filled_values": self.filled_values,
            "flagged_outliers": self.flagged_outliers,
            "issue_count": self.issue_count(),
            "usable_for_backtest": self.usable_for_backtest,
            "usable_for_ml": self.usable_for_ml,
            "elapsed_seconds": self.elapsed_seconds,
        }

class CleanedMarketData(BaseModel):
    market_data: MarketDataFrame
    report: CleaningReport

class DataFetchRequest(BaseModel):
    symbols: list[str]
    timeframe: Timeframe = Timeframe.DAILY
    start: datetime | None = None
    end: datetime | None = None
    period: str | None = None
    adjusted: bool = True
    quality_report: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbols")
    def validate_symbols(cls, v):
        if not v:
            raise ValueError("symbols list cannot be empty.")
        return [ensure_valid_internal_symbol(s) for s in v]

from enum import Enum

class DownloadStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    PARTIAL = "PARTIAL"

class SymbolDownloadResult(BaseModel):

    symbol: str
    status: DownloadStatus
    row_count: int
    start: datetime | None = None
    end: datetime | None = None
    source: str
    timeframe: str
    saved: bool
    from_cache: bool
    quality_score: float | None = None
    quality_passed: bool | None = None
    error: str | None = None
    file_path: str | None = None
    elapsed_seconds: float


    normalization_status: str | None = None
    normalization_issue_count: int | None = None

    cleaning_status: str | None = None
    cleaning_issue_count: int | None = None
    dropped_rows: int | None = None
    usable_for_backtest: bool | None = None
    usable_for_ml: bool | None = None

    adjustment_status: str | None = None
    adjustment_policy: str | None = None
    actions_available: int | None = None
    actions_applied: int | None = None


    @field_validator("symbol")
    def validate_symbol(cls, v):
        from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
        return ensure_valid_internal_symbol(v)

    @field_validator("elapsed_seconds")
    def validate_elapsed(cls, v):
        if v < 0:
            raise ValueError("elapsed_seconds cannot be negative")
        return v

    @model_validator(mode='after')
    def validate_status(self) -> 'SymbolDownloadResult':
        if self.error and self.status != DownloadStatus.FAILED:
            self.status = DownloadStatus.FAILED
        return self

class BatchDownloadResult(BaseModel):
    requested_count: int
    success_count: int
    failed_count: int
    skipped_count: int
    partial_count: int
    results: list[SymbolDownloadResult]
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float
    provider: str
    timeframe: str
    period: str | None = None
    refresh: bool
    save: bool

    @field_validator("elapsed_seconds")
    def validate_elapsed(cls, v):
        if v < 0:
            raise ValueError("elapsed_seconds cannot be negative")
        return v

    @model_validator(mode='after')
    def validate_counts(self) -> 'BatchDownloadResult':
        success = sum(1 for r in self.results if r.status == DownloadStatus.SUCCESS)
        failed = sum(1 for r in self.results if r.status == DownloadStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == DownloadStatus.SKIPPED)
        partial = sum(1 for r in self.results if r.status == DownloadStatus.PARTIAL)

        # We allow overrides but if they are 0, we can calculate them
        if self.success_count == 0 and success > 0: self.success_count = success
        if self.failed_count == 0 and failed > 0: self.failed_count = failed
        if self.skipped_count == 0 and skipped > 0: self.skipped_count = skipped
        if self.partial_count == 0 and partial > 0: self.partial_count = partial

        return self

    def success_symbols(self) -> list[str]:
        return [r.symbol for r in self.results if r.status == DownloadStatus.SUCCESS]

    def failed_symbols(self) -> list[str]:
        return [r.symbol for r in self.results if r.status == DownloadStatus.FAILED]


    def summary(self) -> dict[str, Any]:
        warnings = sum(1 for r in self.results if r.normalization_status == "WARNING")
        cleaning_warnings = sum(1 for r in self.results if r.cleaning_status == "WARNING")
        total_dropped = sum(r.dropped_rows for r in self.results if r.dropped_rows is not None)
        unusable_backtest = sum(1 for r in self.results if r.usable_for_backtest is False)
        unusable_ml = sum(1 for r in self.results if r.usable_for_ml is False)

        adjusted_symbols = sum(1 for r in self.results if r.adjustment_status in ["SUCCESS", "FLAG_ONLY"])
        actions_total = sum(r.actions_applied for r in self.results if r.actions_applied is not None)
        adjustment_warnings = sum(1 for r in self.results if r.adjustment_status == "WARNING")

        return {
            "requested_count": self.requested_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "partial_count": self.partial_count,
            "normalization_warnings": warnings,
            "cleaning_warning_count": cleaning_warnings,
            "total_dropped_rows": total_dropped,
            "unusable_for_backtest_count": unusable_backtest,
            "unusable_for_ml_count": unusable_ml,

            "adjusted_symbol_count": adjusted_symbols,
            "actions_applied_total": actions_total,
            "adjustment_warning_count": adjustment_warnings,
            "elapsed_seconds": self.elapsed_seconds,
            "provider": self.provider,
            "timeframe": self.timeframe,
            "period": self.period,
            "refresh": self.refresh,
            "save": self.save
        }

class UniverseFileFormat(str, Enum):
    JSON = "json"
    CSV = "csv"

class UniverseUpdateAction(str, Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"
    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    SNAPSHOT = "SNAPSHOT"
    VALIDATE = "VALIDATE"
    WATCHLIST_ADD = "WATCHLIST_ADD"
    WATCHLIST_REMOVE = "WATCHLIST_REMOVE"

class UniverseValidationIssueType(str, Enum):
    INVALID_SYMBOL = "INVALID_SYMBOL"
    DUPLICATE_SYMBOL = "DUPLICATE_SYMBOL"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_GROUP = "INVALID_GROUP"
    INVALID_MARKET = "INVALID_MARKET"
    INVALID_ASSET_TYPE = "INVALID_ASSET_TYPE"
    EMPTY_UNIVERSE = "EMPTY_UNIVERSE"
    UNKNOWN = "UNKNOWN"
    MOCK = "MOCK"

class UniverseValidationIssue(BaseModel):
    issue_type: UniverseValidationIssueType
    severity: str
    symbol: str | None = None
    message: str
    row_number: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class UniverseValidationReport(BaseModel):
    total_symbols: int
    active_symbols: int
    inactive_symbols: int
    duplicate_count: int
    invalid_count: int
    issues: list[UniverseValidationIssue] = Field(default_factory=list)
    passed: bool
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def summary(self) -> dict[str, Any]:
        return {
            "total_symbols": self.total_symbols,
            "active_symbols": self.active_symbols,
            "inactive_symbols": self.inactive_symbols,
            "duplicate_count": self.duplicate_count,
            "invalid_count": self.invalid_count,
            "passed": self.passed,
            "generated_at": self.generated_at.isoformat(),
            "issues": [i.model_dump() for i in self.issues]
        }

class UniverseUpdateResult(BaseModel):
    action: UniverseUpdateAction
    success: bool
    symbols_affected: list[str] = Field(default_factory=list)
    message: str
    validation_report: UniverseValidationReport | None = None
    file_path: str | None = None
    snapshot_path: str | None = None
    error: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def summary(self) -> dict[str, Any]:
        res = {
            "action": self.action.value,
            "success": self.success,
            "symbols_affected": self.symbols_affected,
            "message": self.message,
            "file_path": self.file_path,
            "snapshot_path": self.snapshot_path,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }
        if self.validation_report:
            res["validation_passed"] = self.validation_report.passed
            res["issue_count"] = len(self.validation_report.issues)
        return res


class CorporateActionType(str, Enum):
    SPLIT = "SPLIT"
    REVERSE_SPLIT = "REVERSE_SPLIT"
    CASH_DIVIDEND = "CASH_DIVIDEND"
    BONUS_ISSUE = "BONUS_ISSUE"
    RIGHTS_ISSUE = "RIGHTS_ISSUE"
    CAPITAL_INCREASE = "CAPITAL_INCREASE"
    CAPITAL_DECREASE = "CAPITAL_DECREASE"
    MERGER = "MERGER"
    SPIN_OFF = "SPIN_OFF"
    SYMBOL_CHANGE = "SYMBOL_CHANGE"
    UNKNOWN = "UNKNOWN"

class AdjustmentPolicy(str, Enum):
    NONE = "NONE"
    USE_PROVIDER_ADJUSTED = "USE_PROVIDER_ADJUSTED"
    MANUAL_SPLIT_ADJUST = "MANUAL_SPLIT_ADJUST"
    MANUAL_DIVIDEND_ADJUST = "MANUAL_DIVIDEND_ADJUST"
    MANUAL_TOTAL_RETURN = "MANUAL_TOTAL_RETURN"
    FLAG_ONLY = "FLAG_ONLY"

class AdjustmentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class CorporateAction(BaseModel):
    symbol: str
    action_date: date
    action_type: CorporateActionType
    ratio: float | None = None
    cash_amount: float | None = None
    currency: str = "TRY"
    description: str | None = None
    source: str = "manual"
    verified: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol")
    def validate_symbol(cls, v):
        from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
        return ensure_valid_internal_symbol(v)

    @field_validator("ratio")
    def validate_ratio(cls, v):
        if v is not None and v <= 0:
            raise ValueError("ratio must be positive")
        return v

    @field_validator("cash_amount")
    def validate_cash_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError("cash_amount cannot be negative")
        return v

class CorporateActionValidationIssue(BaseModel):
    symbol: str | None = None
    action_date: date | None = None
    issue_type: str
    message: str
    severity: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class CorporateActionValidationReport(BaseModel):
    total_actions: int
    valid_actions: int
    invalid_actions: int
    duplicate_actions: int
    issues: list[CorporateActionValidationIssue] = Field(default_factory=list)
    passed: bool
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def summary(self) -> dict[str, Any]:
        return {
            "total_actions": self.total_actions,
            "valid_actions": self.valid_actions,
            "invalid_actions": self.invalid_actions,
            "duplicate_actions": self.duplicate_actions,
            "issue_count": len(self.issues),
            "passed": self.passed,
            "generated_at": self.generated_at.isoformat()
        }

class AdjustmentIssue(BaseModel):
    issue_type: str
    message: str
    affected_rows: int | None = None
    action_date: date | None = None
    action_type: CorporateActionType | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class AdjustmentReport(BaseModel):
    symbol: str
    timeframe: str
    source: str
    policy: AdjustmentPolicy
    status: AdjustmentStatus
    input_rows: int
    output_rows: int
    actions_applied: int = 0
    actions_available: int = 0
    adjusted_columns: list[str] = Field(default_factory=list)
    volume_adjusted: bool = False
    issues: list[AdjustmentIssue] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float

    def issue_count(self) -> int:
        return len(self.issues)

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "source": self.source,
            "policy": self.policy.value,
            "status": self.status.value,
            "input_rows": self.input_rows,
            "output_rows": self.output_rows,
            "actions_applied": self.actions_applied,
            "actions_available": self.actions_available,
            "adjusted_columns": self.adjusted_columns,
            "volume_adjusted": self.volume_adjusted,
            "issue_count": self.issue_count(),
            "elapsed_seconds": self.elapsed_seconds
        }

class AdjustedMarketData(BaseModel):
    market_data: MarketDataFrame
    report: AdjustmentReport
