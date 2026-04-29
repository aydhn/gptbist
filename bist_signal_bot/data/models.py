from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

from bist_signal_bot.core.constants import DEFAULT_CURRENCY, DEFAULT_MARKET
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol


class AssetType(str, Enum):
    EQUITY = "EQUITY"
    INDEX = "INDEX"
    ETF = "ETF"
    UNKNOWN = "UNKNOWN"

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

from datetime import UTC, datetime
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
        return {
            "requested_count": self.requested_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "partial_count": self.partial_count,
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
