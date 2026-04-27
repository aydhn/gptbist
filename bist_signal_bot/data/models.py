from enum import Enum

from pydantic import BaseModel, Field, field_validator

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

from datetime import datetime
from typing import Any

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

    @field_validator("symbols")
    def validate_symbols(cls, v):
        if not v:
            raise ValueError("symbols list cannot be empty.")
        return [ensure_valid_internal_symbol(s) for s in v]
