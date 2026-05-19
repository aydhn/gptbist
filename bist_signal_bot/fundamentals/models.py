from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

class FinancialStatementType(str, Enum):
    BALANCE_SHEET = "BALANCE_SHEET"
    INCOME_STATEMENT = "INCOME_STATEMENT"
    CASH_FLOW = "CASH_FLOW"
    EQUITY_STATEMENT = "EQUITY_STATEMENT"
    RATIOS = "RATIOS"
    UNKNOWN = "UNKNOWN"

class FinancialPeriodType(str, Enum):
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"
    TTM = "TTM"
    UNKNOWN = "UNKNOWN"

class CorporateEventType(str, Enum):
    DIVIDEND = "DIVIDEND"
    BONUS_ISSUE = "BONUS_ISSUE"
    RIGHTS_ISSUE = "RIGHTS_ISSUE"
    STOCK_SPLIT = "STOCK_SPLIT"
    REVERSE_SPLIT = "REVERSE_SPLIT"
    EARNINGS_RELEASE = "EARNINGS_RELEASE"
    GENERAL_ASSEMBLY = "GENERAL_ASSEMBLY"
    INDEX_CHANGE = "INDEX_CHANGE"
    OTHER = "OTHER"

class FundamentalDataStatus(str, Enum):
    VALID = "VALID"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    MISSING = "MISSING"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"

class FactorGroup(str, Enum):
    VALUE = "VALUE"
    QUALITY = "QUALITY"
    GROWTH = "GROWTH"
    PROFITABILITY = "PROFITABILITY"
    LEVERAGE = "LEVERAGE"
    LIQUIDITY = "LIQUIDITY"
    MOMENTUM_FUNDAMENTAL = "MOMENTUM_FUNDAMENTAL"
    DIVIDEND = "DIVIDEND"
    COMPOSITE = "COMPOSITE"

class FundamentalFilterDecision(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    REDUCE = "REDUCE"
    REJECT = "REJECT"
    SKIP = "SKIP"
    UNKNOWN = "UNKNOWN"

@dataclass
class FinancialStatementRecord:
    record_id: str
    symbol: str
    statement_type: FinancialStatementType
    period_type: FinancialPeriodType
    fiscal_year: int
    period_end_date: datetime
    currency: str
    values: dict[str, Optional[float]]
    imported_at: datetime
    fiscal_period: Optional[int] = None
    announced_at: Optional[datetime] = None
    source_path: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self): self.symbol = self.symbol.upper()

@dataclass
class CorporateEvent:
    event_id: str
    symbol: str
    event_type: CorporateEventType
    event_date: datetime
    description: str
    imported_at: datetime
    announced_at: Optional[datetime] = None
    amount: Optional[float] = None
    ratio: Optional[float] = None
    currency: Optional[str] = None
    source_path: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class SectorClassification:
    symbol: str
    updated_at: datetime
    sector: Optional[str] = None
    industry: Optional[str] = None
    market: Optional[str] = None
    index_memberships: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class FundamentalRatioSnapshot:
    symbol: str
    as_of_date: datetime
    available_at: datetime
    ratios: dict[str, Optional[float]]
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class FactorScore:
    symbol: str
    as_of_date: datetime
    available_at: datetime
    factor_group: FactorGroup
    score: float
    percentile: Optional[float] = None
    components: dict[str, Optional[float]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class FundamentalScorecard:
    symbol: str
    as_of_date: datetime
    available_at: datetime
    composite_score: float
    data_status: FundamentalDataStatus
    ratios: Optional[FundamentalRatioSnapshot] = None
    factor_scores: list[FactorScore] = field(default_factory=list)
    sector: Optional[SectorClassification] = None
    upcoming_events: list[CorporateEvent] = field(default_factory=list)
    recent_events: list[CorporateEvent] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Fundamental scorecard is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)
    def summary(self) -> dict[str, Any]:
        return {"symbol": self.symbol, "as_of_date": self.as_of_date.isoformat(), "composite_score": self.composite_score, "data_status": self.data_status.value, "warnings": self.warnings}
    def safe_public_dict(self) -> dict[str, Any]: return self.summary()

@dataclass
class FundamentalImportRequest:
    input_path: str
    import_type: str
    symbol: Optional[str] = None
    statement_type: Optional[FinancialStatementType] = None
    period_type: Optional[FinancialPeriodType] = None
    delimiter: Optional[str] = None
    sheet_name: Optional[str] = None
    column_mapping: dict[str, str] = field(default_factory=dict)
    overwrite: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class FundamentalImportResult:
    request: FundamentalImportRequest
    status: FundamentalDataStatus
    records_imported: int
    events_imported: int
    sectors_imported: int
    output_paths: dict[str, str]
    warnings: list[str]
    errors: list[str]
    generated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class FundamentalFreshnessReport:
    symbols: list[str]
    stale_symbols: list[str]
    missing_symbols: list[str]
    fresh_symbols: list[str]
    max_age_days: int
    generated_at: datetime
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
