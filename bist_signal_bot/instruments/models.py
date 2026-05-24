from enum import Enum
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, model_validator, field_validator

class InstrumentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DELISTED = "DELISTED"
    RENAMED = "RENAMED"
    UNKNOWN = "UNKNOWN"

class InstrumentType(str, Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    INDEX = "INDEX"
    WARRANT = "WARRANT"
    FUND = "FUND"
    RIGHTS_COUPON = "RIGHTS_COUPON"
    UNKNOWN = "UNKNOWN"

class MarketSegment(str, Enum):
    YILDIZ_PAZAR = "YILDIZ_PAZAR"
    ANA_PAZAR = "ANA_PAZAR"
    ALT_PAZAR = "ALT_PAZAR"
    YAKIN_IZLEME = "YAKIN_IZLEME"
    ETF_PAZARI = "ETF_PAZARI"
    VARANT = "VARANT"
    UNKNOWN = "UNKNOWN"

class SymbolLifecycleEventType(str, Enum):
    LISTED = "LISTED"
    DELISTED = "DELISTED"
    RENAMED = "RENAMED"
    SUSPENDED = "SUSPENDED"
    RESUMED = "RESUMED"
    MERGED = "MERGED"
    SPIN_OFF = "SPIN_OFF"
    MARKET_SEGMENT_CHANGED = "MARKET_SEGMENT_CHANGED"
    SECTOR_CHANGED = "SECTOR_CHANGED"
    UNKNOWN = "UNKNOWN"

class IndexMembershipStatus(str, Enum):
    MEMBER = "MEMBER"
    REMOVED = "REMOVED"
    UNKNOWN = "UNKNOWN"

class InstrumentRecord(BaseModel):
    symbol: str
    isin: str | None = None
    name: str
    instrument_type: InstrumentType
    status: InstrumentStatus
    market_segment: MarketSegment | None = None
    sector: str | None = None
    industry: str | None = None
    sub_industry: str | None = None
    index_memberships: list[str] = Field(default_factory=list)
    first_seen_at: datetime | None = None
    listed_at: datetime | None = None
    delisted_at: datetime | None = None
    previous_symbols: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    lot_size: float | None = None
    currency: str = "TRY"
    source: str = "unknown"
    updated_at: datetime = Field(default_factory=datetime.now)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol")
    def validate_symbol(cls, v):
        return v.upper().strip()

    @field_validator("currency")
    def validate_currency(cls, v):
        if not v:
            return "TRY"
        return v.upper().strip()

    @field_validator("previous_symbols", "aliases")
    def validate_symbol_lists(cls, v):
        return [s.upper().strip() for s in v]

    @field_validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v

    @model_validator(mode="after")
    def validate_delisted(self):
        if self.status == InstrumentStatus.DELISTED and not self.delisted_at:
            self.warnings.append("Status is DELISTED but delisted_at is None")
        return self

class SymbolLifecycleEvent(BaseModel):
    event_id: str
    symbol: str
    event_type: SymbolLifecycleEventType
    effective_date: datetime
    old_value: str | None = None
    new_value: str | None = None
    source: str
    confidence: float | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class UniverseFilter(BaseModel):
    include_statuses: list[InstrumentStatus] = Field(default_factory=list)
    include_types: list[InstrumentType] = Field(default_factory=list)
    include_segments: list[MarketSegment] = Field(default_factory=list)
    include_sectors: list[str] = Field(default_factory=list)
    exclude_symbols: list[str] = Field(default_factory=list)
    include_symbols: list[str] = Field(default_factory=list)
    require_recent_data: bool = False
    require_liquidity: bool = False
    min_average_volume: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class InstrumentUniverse(BaseModel):
    universe_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    name: str
    symbols: list[str] = Field(default_factory=list)
    filter: UniverseFilter
    included_count: int = 0
    excluded_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Instrument universe is operational market-data metadata only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
