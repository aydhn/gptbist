from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ResearchPortfolioStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE_RESEARCH = "ACTIVE_RESEARCH"
    WATCH = "WATCH"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class PortfolioLedgerEventType(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    VALUED = "VALUED"
    REBALANCED_RESEARCH = "REBALANCED_RESEARCH"
    OUTCOME_EVALUATED = "OUTCOME_EVALUATED"
    ATTRIBUTION_CALCULATED = "ATTRIBUTION_CALCULATED"
    NAV_UPDATED = "NAV_UPDATED"
    WATCH_FLAGGED = "WATCH_FLAGGED"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"
    CORRECTED = "CORRECTED"
    ARCHIVED = "ARCHIVED"
    UNKNOWN = "UNKNOWN"


class PortfolioValuationStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class AttributionType(str, Enum):
    SYMBOL = "SYMBOL"
    SECTOR = "SECTOR"
    STRATEGY = "STRATEGY"
    SIGNAL = "SIGNAL"
    RISK_BUDGET = "RISK_BUDGET"
    COST = "COST"
    TURNOVER = "TURNOVER"
    CORRELATION_CLUSTER = "CORRELATION_CLUSTER"
    CUSTOM = "CUSTOM"


class PortfolioOutcomeLabel(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    NOT_EVALUATED = "NOT_EVALUATED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"


class ResearchPortfolioPosition(BaseModel):
    position_id: str
    symbol: str
    sector: str | None = None
    strategy_name: str | None = None
    signal_id: str | None = None
    target_weight: float
    current_weight: float
    entry_research_price: float | None = None
    latest_price: float | None = None
    quantity_simulated: float | None = None
    gross_return_pct: float | None = None
    net_return_pct: float | None = None
    estimated_cost_bps: float | None = None
    estimated_slippage_bps: float | None = None
    contribution_to_return_pct: float | None = None
    contribution_to_risk_pct: float | None = None
    calibrated_confidence: float | None = None
    candidate_score: float | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("target_weight", "current_weight")
    @classmethod
    def validate_weights(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Weight cannot be negative.")
        return v

    @field_validator("calibrated_confidence", "candidate_score")
    @classmethod
    def validate_scores(cls, v: float | None) -> float | None:
        if v is not None:
            return max(0.0, min(100.0, v))
        return v


class ResearchPortfolio(BaseModel):
    portfolio_id: str
    name: str
    status: ResearchPortfolioStatus
    created_at: datetime
    updated_at: datetime
    construction_result_id: str | None = None
    initial_notional: float
    current_simulated_nav: float | None = None
    base_currency: str = "TRY"
    positions: list[ResearchPortfolioPosition] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Research portfolio is simulated research metadata only. "
        "It is not investment advice, portfolio management, or a real account. No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        return v

    @field_validator("initial_notional")
    @classmethod
    def validate_notional(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Initial notional must be positive.")
        return v

    @field_validator("base_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            return "TRY"
        return v


class PortfolioLedgerEvent(BaseModel):
    event_id: str
    portfolio_id: str
    event_type: PortfolioLedgerEventType
    created_at: datetime
    actor: str | None = None
    message: str
    previous_status: ResearchPortfolioStatus | None = None
    new_status: ResearchPortfolioStatus | None = None
    refs: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Portfolio ledger event is research-only and append-only. No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class PortfolioValuationSnapshot(BaseModel):
    valuation_id: str
    portfolio_id: str
    generated_at: datetime
    status: PortfolioValuationStatus
    simulated_nav: float
    gross_return_pct: float | None = None
    net_return_pct: float | None = None
    total_cost_drag_pct: float | None = None
    total_turnover_pct: float | None = None
    positions: list[ResearchPortfolioPosition] = Field(default_factory=list)
    missing_prices: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Portfolio valuation snapshot is simulated research output only. "
        "It is not a real account valuation. No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class PortfolioAttributionItem(BaseModel):
    attribution_id: str
    portfolio_id: str
    attribution_type: AttributionType
    key: str
    gross_contribution_pct: float | None = None
    net_contribution_pct: float | None = None
    risk_contribution_pct: float | None = None
    cost_contribution_pct: float | None = None
    weight: float | None = None
    rank: int | None = None
    message: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PortfolioAttributionResult(BaseModel):
    result_id: str
    portfolio_id: str
    generated_at: datetime
    items: list[PortfolioAttributionItem] = Field(default_factory=list)
    top_positive_contributors: list[str] = Field(default_factory=list)
    top_negative_contributors: list[str] = Field(default_factory=list)
    total_gross_return_pct: float | None = None
    total_net_return_pct: float | None = None
    total_cost_drag_pct: float | None = None
    status: PortfolioValuationStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Portfolio attribution is simulated research analysis only. "
        "It is not investment advice. No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class PortfolioOutcomeResult(BaseModel):
    outcome_id: str
    portfolio_id: str
    generated_at: datetime
    horizon_days: int
    label: PortfolioOutcomeLabel
    gross_return_pct: float | None = None
    net_return_pct: float | None = None
    benchmark_return_pct: float | None = None
    excess_return_pct: float | None = None
    max_drawdown_pct: float | None = None
    hit_rate_positions_pct: float | None = None
    cost_drag_pct: float | None = None
    turnover_pct: float | None = None
    constraint_violations_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Portfolio outcome result is research-only. "
        "Past simulated performance does not guarantee future outcomes. No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    breadth_regime_at_entry: str | None = None
    breadth_score_bucket: str | None = None
    divergence_active: bool | None = None


class RebalanceTrackingResult(BaseModel):
    tracking_id: str
    portfolio_id: str
    rebalance_id: str | None = None
    generated_at: datetime
    before_nav: float | None = None
    after_nav: float | None = None
    estimated_turnover_pct: float | None = None
    realized_simulated_turnover_pct: float | None = None
    estimated_cost_bps: float | None = None
    simulated_cost_bps: float | None = None
    before_score: float | None = None
    after_score: float | None = None
    quality_delta: float | None = None
    violations_before: int = 0
    violations_after: int = 0
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Rebalance tracking result is research-only. It is not investment advice or real account reporting. "
        "No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class PortfolioNavPoint(BaseModel):
    nav_id: str
    portfolio_id: str
    timestamp: datetime
    simulated_nav: float
    gross_return_pct: float | None = None
    net_return_pct: float | None = None
    drawdown_pct: float | None = None
    cost_drag_pct: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PortfolioLedgerReport(BaseModel):
    report_id: str
    portfolio_id: str | None = None
    generated_at: datetime
    portfolios: list[ResearchPortfolio] = Field(default_factory=list)
    valuations: list[PortfolioValuationSnapshot] = Field(default_factory=list)
    attributions: list[PortfolioAttributionResult] = Field(default_factory=list)
    outcomes: list[PortfolioOutcomeResult] = Field(default_factory=list)
    rebalance_tracking: list[RebalanceTrackingResult] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Portfolio ledger report is research-only. It is not investment advice or real account reporting. "
        "No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
