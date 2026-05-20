from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime

class PortfolioResearchMode(str, Enum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    PAPER_SYNC = "PAPER_SYNC"
    WATCHLIST_ONLY = "WATCHLIST_ONLY"
    SIGNALS_ONLY = "SIGNALS_ONLY"
    CUSTOM = "CUSTOM"

class AllocationMethod(str, Enum):
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    SCORE_WEIGHTED = "SCORE_WEIGHTED"
    RISK_PARITY_LITE = "RISK_PARITY_LITE"
    VOLATILITY_ADJUSTED = "VOLATILITY_ADJUSTED"
    CONSENSUS_WEIGHTED = "CONSENSUS_WEIGHTED"
    HYBRID = "HYBRID"

class RebalanceDecision(str, Enum):
    NO_CHANGE = "NO_CHANGE"
    ADD_RESEARCH = "ADD_RESEARCH"
    REMOVE_RESEARCH = "REMOVE_RESEARCH"
    INCREASE_RESEARCH_WEIGHT = "INCREASE_RESEARCH_WEIGHT"
    DECREASE_RESEARCH_WEIGHT = "DECREASE_RESEARCH_WEIGHT"
    WATCH_ONLY = "WATCH_ONLY"
    BLOCKED_BY_CONSTRAINT = "BLOCKED_BY_CONSTRAINT"
    SKIPPED = "SKIPPED"

class PortfolioConstraintStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"
    UNKNOWN = "UNKNOWN"

class ExposureGroup(str, Enum):
    SYMBOL = "SYMBOL"
    SECTOR = "SECTOR"
    INDUSTRY = "INDUSTRY"
    STRATEGY = "STRATEGY"
    SIGNAL_SOURCE = "SIGNAL_SOURCE"
    RISK_BUCKET = "RISK_BUCKET"
    REGIME = "REGIME"
    BREADTH_STATUS = "BREADTH_STATUS"
    FUNDAMENTAL_BUCKET = "FUNDAMENTAL_BUCKET"
    CONSENSUS_BUCKET = "CONSENSUS_BUCKET"
    CUSTOM = "CUSTOM"

class ResearchPortfolioItem(BaseModel):
    item_id: str
    symbol: str
    proposed_weight: float
    capped_weight: float
    final_weight: float
    strategy_name: Optional[str] = None
    signal_id: Optional[str] = None
    consensus_id: Optional[str] = None
    source_type: Optional[str] = None
    score: Optional[float] = None
    confidence: Optional[float] = None
    risk_score: Optional[float] = None
    consensus_score: Optional[float] = None
    fundamental_score: Optional[float] = None
    breadth_score: Optional[float] = None
    relative_strength_score: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    state: Optional[str] = None
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        self.symbol = self.symbol.upper().strip()
        self.proposed_weight = max(0.0, min(1.0, self.proposed_weight))
        self.capped_weight = max(0.0, min(1.0, self.capped_weight))
        self.final_weight = max(0.0, min(1.0, self.final_weight))
        if self.score is not None:
            self.score = max(0.0, min(100.0, self.score))
        if self.confidence is not None:
            self.confidence = max(0.0, min(100.0, self.confidence))

class PortfolioConstraint(BaseModel):
    constraint_id: str
    name: str
    status: PortfolioConstraintStatus
    message: str
    limit_value: Optional[float] = None
    actual_value: Optional[float] = None
    affected_symbols: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

class PortfolioExposureBucket(BaseModel):
    group: ExposureGroup
    key: str
    weight: float
    item_count: int
    symbols: List[str] = Field(default_factory=list)
    status: PortfolioConstraintStatus = PortfolioConstraintStatus.UNKNOWN
    warnings: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

class CorrelationPair(BaseModel):
    symbol_a: str
    symbol_b: str
    correlation: float
    lookback_days: int
    status: PortfolioConstraintStatus = PortfolioConstraintStatus.UNKNOWN
    warning: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

class ResearchPortfolioSnapshot(BaseModel):
    snapshot_id: str
    created_at: datetime
    mode: PortfolioResearchMode
    allocation_method: AllocationMethod
    items: List[ResearchPortfolioItem] = Field(default_factory=list)
    constraints: List[PortfolioConstraint] = Field(default_factory=list)
    exposures: List[PortfolioExposureBucket] = Field(default_factory=list)
    correlations: List[CorrelationPair] = Field(default_factory=list)
    total_weight: float = 0.0
    cash_weight: float = 0.0
    item_count: int = 0
    valid_item_count: int = 0
    blocked_item_count: int = 0
    portfolio_score: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Research portfolio snapshot only. Not investment advice. No real order was sent."
    metadata: dict = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at.isoformat(),
            "mode": self.mode.value,
            "allocation_method": self.allocation_method.value,
            "total_weight": self.total_weight,
            "item_count": self.item_count,
            "warnings_count": len(self.warnings),
            "disclaimer": self.disclaimer
        }

    def safe_public_dict(self) -> dict[str, Any]:
        d = self.model_dump()
        if "created_at" in d:
            d["created_at"] = d["created_at"].isoformat()
        if "metadata" in d:
            d["metadata"] = {k: "REDACTED" if "secret" in k.lower() or "token" in k.lower() else v for k, v in d["metadata"].items()}
        return d

class RebalancePlanItem(BaseModel):
    plan_item_id: str
    symbol: str
    current_weight: float
    target_weight: float
    delta_weight: float
    decision: RebalanceDecision
    reason: str
    blocked: bool = False
    warnings: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

class RebalancePlan(BaseModel):
    plan_id: str
    created_at: datetime
    target_snapshot_id: str
    current_snapshot_id: Optional[str] = None
    items: List[RebalancePlanItem] = Field(default_factory=list)
    turnover_estimate: float = 0.0
    add_count: int = 0
    remove_count: int = 0
    increase_count: int = 0
    decrease_count: int = 0
    no_change_count: int = 0
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Rebalance plan is research-only. It is not an order instruction. No real order was sent."
    metadata: dict = Field(default_factory=dict)

class BasketSimulationResult(BaseModel):
    simulation_id: str
    created_at: datetime
    snapshot_id: str
    start_date: datetime
    end_date: datetime
    initial_value: float
    final_value: float
    simulated_return_pct: float
    max_drawdown_pct: Optional[float] = None
    volatility_pct: Optional[float] = None
    sharpe_like: Optional[float] = None
    item_returns: dict = Field(default_factory=dict)
    equity_curve: List[dict] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Basket simulation is historical research-only. Past results do not guarantee future performance. No real order was sent."
    metadata: dict = Field(default_factory=dict)

class PortfolioResearchRequest(BaseModel):
    symbols: List[str] = Field(default_factory=list)
    mode: PortfolioResearchMode = PortfolioResearchMode.RESEARCH_ONLY
    allocation_method: AllocationMethod = AllocationMethod.HYBRID
    include_active_signals: bool = True
    include_watchlist: bool = True
    include_ensemble: bool = True
    include_fundamentals: bool = True
    include_breadth: bool = True
    include_paper_positions: bool = False
    max_items: int = 10
    max_symbol_weight: float = 0.20
    max_sector_weight: float = 0.35
    max_strategy_weight: float = 0.40
    min_score: float = 45.0
    target_gross_exposure: float = 1.00
    source: str = "local"
    timeframe: str = "1D"
    save_snapshot: bool = True
    metadata: dict = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.max_items <= 0:
            self.max_items = 10
        self.max_symbol_weight = max(0.0, min(1.0, self.max_symbol_weight))
        self.max_sector_weight = max(0.0, min(1.0, self.max_sector_weight))
        self.max_strategy_weight = max(0.0, min(1.0, self.max_strategy_weight))
        self.min_score = max(0.0, min(100.0, self.min_score))
        self.target_gross_exposure = max(0.0, min(1.0, self.target_gross_exposure))
