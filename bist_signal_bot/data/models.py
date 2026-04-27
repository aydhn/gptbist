from enum import Enum
from pydantic import BaseModel, Field, field_validator
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
from bist_signal_bot.core.constants import DEFAULT_MARKET, DEFAULT_CURRENCY

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
