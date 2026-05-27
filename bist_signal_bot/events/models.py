from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

class MarketEventType(str, Enum):
    EARNINGS = "EARNINGS"
    FINANCIAL_STATEMENT = "FINANCIAL_STATEMENT"
    DIVIDEND = "DIVIDEND"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    GENERAL_ASSEMBLY = "GENERAL_ASSEMBLY"
    MACRO_DATA = "MACRO_DATA"
    CENTRAL_BANK = "CENTRAL_BANK"
    INTEREST_RATE_DECISION = "INTEREST_RATE_DECISION"
    INFLATION_DATA = "INFLATION_DATA"
    POLICY_EVENT = "POLICY_EVENT"
    INDEX_REBALANCE = "INDEX_REBALANCE"
    TRADING_HALT = "TRADING_HALT"
    VOLATILITY_EVENT = "VOLATILITY_EVENT"
    SECTOR_EVENT = "SECTOR_EVENT"
    COMPANY_NEWS_PLACEHOLDER = "COMPANY_NEWS_PLACEHOLDER"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"

class MarketEventScope(str, Enum):
    SYMBOL = "SYMBOL"
    SECTOR = "SECTOR"
    INDEX = "INDEX"
    MARKET = "MARKET"
    MACRO = "MACRO"
    PORTFOLIO = "PORTFOLIO"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"

class MarketEventStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    ESTIMATED = "ESTIMATED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"

class EventSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class EventWindowType(str, Enum):
    PRE_EVENT = "PRE_EVENT"
    EVENT_DAY = "EVENT_DAY"
    POST_EVENT = "POST_EVENT"
    BLACKOUT = "BLACKOUT"
    COOL_DOWN = "COOL_DOWN"
    CUSTOM = "CUSTOM"

class EventRiskDecision(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    WATCH = "WATCH"
    REDUCE_CONFIDENCE = "REDUCE_CONFIDENCE"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"
    RESEARCH_BLOCK = "RESEARCH_BLOCK"
    SKIP = "SKIP"
    UNKNOWN = "UNKNOWN"

class MarketEvent(BaseModel):
    event_id: str
    event_type: MarketEventType
    scope: MarketEventScope
    status: MarketEventStatus
    title: str
    symbol: str | None = None
    sector: str | None = None
    index_name: str | None = None
    event_date: datetime
    start_at: datetime | None = None
    end_at: datetime | None = None
    severity: EventSeverity
    source: str
    source_ref: str | None = None
    confidence: float | None = None
    tags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Market event record is operational research metadata only. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class EventWindow(BaseModel):
    window_id: str
    event_id: str
    window_type: EventWindowType
    starts_at: datetime
    ends_at: datetime
    applies_to_symbols: list[str] = Field(default_factory=list)
    applies_to_sectors: list[str] = Field(default_factory=list)
    applies_to_market: bool = False
    severity: EventSeverity
    decision: EventRiskDecision
    reason: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class EventRiskAssessment(BaseModel):
    assessment_id: str
    symbol: str | None = None
    strategy_name: str | None = None
    signal_id: str | None = None
    assessed_at: datetime
    matching_events: list[MarketEvent] = Field(default_factory=list)
    matching_windows: list[EventWindow] = Field(default_factory=list)
    risk_score: float | None = None
    severity: EventSeverity
    decision: EventRiskDecision
    confidence_adjustment: float | None = None
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Event risk assessment is research-only. It does not predict price direction and is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class BlackoutPolicy(BaseModel):
    policy_id: str
    name: str
    enabled: bool = True
    event_types: list[MarketEventType] = Field(default_factory=list)
    pre_event_days: int = 0
    post_event_days: int = 0
    severity_threshold: EventSeverity
    decision: EventRiskDecision
    applies_to_scope: list[MarketEventScope] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Blackout policy is research-only guard metadata. It is not a real trading restriction or order policy. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class EventImportResult(BaseModel):
    import_id: str
    created_at: datetime
    source_path: str
    rows_seen: int = 0
    events_imported: int = 0
    events_skipped: int = 0
    duplicate_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Event import is local operational data processing only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class EventCalendarSnapshot(BaseModel):
    snapshot_id: str
    created_at: datetime
    events_count: int = 0
    upcoming_count: int = 0
    high_severity_count: int = 0
    symbols_with_events: list[str] = Field(default_factory=list)
    sectors_with_events: list[str] = Field(default_factory=list)
    event_type_counts: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Market event record is operational research metadata only. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class EventLink(BaseModel):
    link_id: str
    event_id: str
    linked_object_type: str
    linked_object_id: str
    symbol: str | None = None
    strategy_name: str | None = None
    relationship: str
    score: float | None = None
    message: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
