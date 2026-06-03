from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class MarketStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WATCH = "WATCH"
    DISABLED = "DISABLED"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"

class MarketType(str, Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    INDEX = "INDEX"
    FUTURES = "FUTURES"
    FX = "FX"
    CRYPTO_RESEARCH = "CRYPTO_RESEARCH"
    MACRO = "MACRO"
    FUND = "FUND"
    CUSTOM = "CUSTOM"

class ExchangeRegion(str, Enum):
    TURKIYE = "TURKIYE"
    US = "US"
    EUROPE = "EUROPE"
    GLOBAL = "GLOBAL"
    SYNTHETIC = "SYNTHETIC"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"

class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    INDEX = "INDEX"
    FUTURE = "FUTURE"
    CURRENCY_PAIR = "CURRENCY_PAIR"
    CRYPTO_ASSET_RESEARCH = "CRYPTO_ASSET_RESEARCH"
    MACRO_INDICATOR = "MACRO_INDICATOR"
    FUND = "FUND"
    CASH = "CASH"
    CUSTOM = "CUSTOM"

class QuoteConvention(str, Enum):
    PRICE = "PRICE"
    POINTS = "POINTS"
    PERCENT = "PERCENT"
    RATE = "RATE"
    RATIO = "RATIO"
    INDEX_LEVEL = "INDEX_LEVEL"
    UNKNOWN = "UNKNOWN"

class MarketSessionStatus(str, Enum):
    REGULAR = "REGULAR"
    PRE_MARKET = "PRE_MARKET"
    AFTER_HOURS = "AFTER_HOURS"
    CLOSED = "CLOSED"
    HOLIDAY = "HOLIDAY"
    HALF_DAY = "HALF_DAY"
    UNKNOWN = "UNKNOWN"

class MarketDefinition(BaseModel):
    market_id: str
    name: str
    market_type: MarketType
    region: ExchangeRegion
    default_currency: str
    timezone: str
    exchange_code: Optional[str] = None
    quote_convention: QuoteConvention
    status: MarketStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Market definition is local research metadata only. It is not investment advice, live market status, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class InstrumentDefinition(BaseModel):
    instrument_id: str
    market_id: str
    symbol: str
    canonical_symbol: str
    display_name: Optional[str] = None
    asset_class: AssetClass
    currency: str
    exchange_code: Optional[str] = None
    isin: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    active: bool
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Instrument definition is local research metadata only. It is not a tradable instruction, recommendation, or broker instrument mapping. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class SymbolMapping(BaseModel):
    mapping_id: str
    raw_symbol: str
    canonical_symbol: str
    market_id: str
    exchange_code: Optional[str] = None
    normalized: bool
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class MarketCalendarDay(BaseModel):
    day_id: str
    market_id: str
    date: str
    session_status: MarketSessionStatus
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    timezone: str
    reason: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class MarketSession(BaseModel):
    session_id: str
    market_id: str
    date: str
    status: MarketSessionStatus
    session_name: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: str
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Market session is local calendar metadata only. It does not guarantee live market status or trading availability. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CurrencyDefinition(BaseModel):
    currency_code: str
    name: str
    symbol: Optional[str] = None
    precision: Optional[int] = None
    status: MarketStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class MarketUniverse(BaseModel):
    universe_id: str
    name: str
    market_id: str
    instrument_ids: list[str]
    symbols: list[str]
    created_at: datetime
    filters: dict[str, Any]
    status: MarketStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Market universe is local research grouping metadata only. It is not a trading universe recommendation or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MarketNormalizationResult(BaseModel):
    normalization_id: str
    market_id: Optional[str] = None
    source_ref: Optional[str] = None
    input_rows: int
    output_rows: int
    normalized_symbols: int
    rejected_rows: int
    warnings: list[str] = Field(default_factory=list)
    status: MarketStatus
    disclaimer: str = "Market normalization result is local data processing metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MarketValidationResult(BaseModel):
    validation_id: str
    market_id: Optional[str] = None
    created_at: datetime
    status: MarketStatus
    findings: list[str]
    missing_instruments: list[str]
    invalid_symbols: list[str]
    calendar_warnings: list[str]
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Market validation result is local software validation metadata only. It does not certify live trading availability or financial correctness. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MarketGovernanceAssessment(BaseModel):
    assessment_id: str
    market_id: str
    created_at: datetime
    status: MarketStatus
    registry_complete: bool
    calendar_available: bool
    instruments_available: bool
    currency_valid: bool
    unsafe_language_findings: list[str]
    caveats: list[str]
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Market governance assessment is local research software metadata only. It is not investment advice, broker approval, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MarketRegistryReport(BaseModel):
    report_id: str
    generated_at: datetime
    markets: list[MarketDefinition]
    instruments: list[InstrumentDefinition]
    universes: list[MarketUniverse]
    calendars: list[MarketCalendarDay]
    validations: list[MarketValidationResult]
    governance_assessments: list[MarketGovernanceAssessment]
    key_findings: list[str]
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Market registry report is local research metadata reporting only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
