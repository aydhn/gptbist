from enum import Enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class PortfolioConstructionStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class PortfolioWeightingMethod(str, Enum):
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    CONFIDENCE_WEIGHTED = "CONFIDENCE_WEIGHTED"
    SCORE_WEIGHTED = "SCORE_WEIGHTED"
    RISK_PARITY_LITE = "RISK_PARITY_LITE"
    VOLATILITY_TARGETED = "VOLATILITY_TARGETED"
    LIQUIDITY_ADJUSTED = "LIQUIDITY_ADJUSTED"
    COST_ADJUSTED = "COST_ADJUSTED"
    HYBRID = "HYBRID"
    CUSTOM = "CUSTOM"

class ConstraintType(str, Enum):
    MAX_SYMBOL_WEIGHT = "MAX_SYMBOL_WEIGHT"
    MAX_SECTOR_WEIGHT = "MAX_SECTOR_WEIGHT"
    MAX_STRATEGY_WEIGHT = "MAX_STRATEGY_WEIGHT"
    MAX_CORRELATION_CLUSTER_WEIGHT = "MAX_CORRELATION_CLUSTER_WEIGHT"
    MIN_LIQUIDITY_STATUS = "MIN_LIQUIDITY_STATUS"
    MAX_TURNOVER = "MAX_TURNOVER"
    MAX_COST_DRAG = "MAX_COST_DRAG"
    MAX_SINGLE_SIGNAL_CONTRIBUTION = "MAX_SINGLE_SIGNAL_CONTRIBUTION"
    MIN_DIVERSIFICATION_SCORE = "MIN_DIVERSIFICATION_SCORE"
    CUSTOM = "CUSTOM"

class ConstraintSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RebalanceActionType(str, Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    HOLD = "HOLD"
    SKIP = "SKIP"
    UNKNOWN = "UNKNOWN"

class PortfolioCandidate(BaseModel):
    candidate_id: str
    symbol: str
    strategy_name: str | None = None
    signal_id: str | None = None
    sector: str | None = None
    calibrated_confidence: float | None = None
    raw_confidence: float | None = None
    strategy_score: float | None = None
    validation_score: float | None = None
    monte_carlo_score: float | None = None
    liquidity_score: float | None = None
    execution_penalty_score: float | None = None
    risk_score: float | None = None
    final_candidate_score: float | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("calibrated_confidence", "raw_confidence", "strategy_score",
                     "validation_score", "monte_carlo_score", "liquidity_score",
                     "execution_penalty_score", "risk_score", "final_candidate_score")
    @classmethod
    def clamp_scores(cls, v: float | None) -> float | None:
        if v is not None:
            return max(0.0, min(100.0, v))
        return v

    @model_validator(mode="after")
    def add_research_disclaimer(self) -> "PortfolioCandidate":
        self.metadata["is_research_only"] = True
        return self

class PortfolioPositionResearch(BaseModel):
    position_id: str
    symbol: str
    sector: str | None = None
    current_weight: float
    target_weight: float
    weight_delta: float
    estimated_notional: float | None = None
    estimated_cost_bps: float | None = None
    estimated_slippage_bps: float | None = None
    liquidity_status: str | None = None
    contribution_to_risk_pct: float | None = None
    candidate_score: float | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.upper().strip()

class PortfolioConstraint(BaseModel):
    constraint_id: str
    constraint_type: ConstraintType
    name: str
    limit_value: float | str | None = None
    enabled: bool = True
    severity: ConstraintSeverity
    metadata: dict[str, Any] = Field(default_factory=dict)

class PortfolioConstraintViolation(BaseModel):
    violation_id: str
    constraint_type: ConstraintType
    symbol: str | None = None
    sector: str | None = None
    observed_value: float | str | None = None
    limit_value: float | str | None = None
    severity: ConstraintSeverity
    message: str
    recommended_action: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class CorrelationCluster(BaseModel):
    cluster_id: str
    symbols: list[str]
    average_correlation: float | None = None
    max_pair_correlation: float | None = None
    cluster_weight: float | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class RiskBudgetItem(BaseModel):
    item_id: str
    symbol: str
    target_weight: float
    volatility_pct: float | None = None
    marginal_risk: float | None = None
    contribution_to_risk_pct: float | None = None
    risk_budget_pct: float | None = None
    budget_gap_pct: float | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class PortfolioConstructionRequest(BaseModel):
    request_id: str
    universe_name: str | None = None
    symbols: list[str]
    strategy_names: list[str]
    weighting_method: PortfolioWeightingMethod
    max_positions: int
    portfolio_notional: float
    current_weights: dict[str, float]
    apply_constraints: bool = True
    include_execution_costs: bool = True
    include_liquidity_penalty: bool = True
    include_calibration: bool = True
    include_strategy_scorecard: bool = True
    include_monte_carlo: bool = True
    save_output: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, v: list[str]) -> list[str]:
        return [s.upper().strip() for s in v]

    @field_validator("max_positions")
    @classmethod
    def validate_max_positions(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_positions must be positive")
        return v

    @field_validator("portfolio_notional")
    @classmethod
    def validate_portfolio_notional(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("portfolio_notional must be positive")
        return v

    @field_validator("current_weights")
    @classmethod
    def validate_current_weights(cls, v: dict[str, float]) -> dict[str, float]:
        for weight in v.values():
            if weight < 0:
                raise ValueError("weights cannot be negative")
        return v

class PortfolioConstructionResult(BaseModel):
    result_id: str
    request: PortfolioConstructionRequest
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    status: PortfolioConstructionStatus
    weighting_method: PortfolioWeightingMethod
    candidates: list[PortfolioCandidate] = Field(default_factory=list)
    positions: list[PortfolioPositionResearch] = Field(default_factory=list)
    constraints: list[PortfolioConstraint] = Field(default_factory=list)
    violations: list[PortfolioConstraintViolation] = Field(default_factory=list)
    correlation_clusters: list[CorrelationCluster] = Field(default_factory=list)
    risk_budget: list[RiskBudgetItem] = Field(default_factory=list)
    diversification_score: float | None = None
    portfolio_score: float | None = None
    estimated_turnover_pct: float | None = None
    estimated_total_cost_bps: float | None = None
    estimated_net_quality_score: float | None = None
    recommended_actions: list[str] = Field(default_factory=list)
    output_files: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Portfolio construction result is research-only. It is not investment advice, portfolio management instruction, or an order. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "generated_at": self.generated_at.isoformat(),
            "status": self.status.value,
            "weighting_method": self.weighting_method.value,
            "positions_count": len(self.positions),
            "diversification_score": self.diversification_score,
            "portfolio_score": self.portfolio_score,
            "violation_count": len(self.violations),
            "estimated_turnover_pct": self.estimated_turnover_pct,
            "estimated_total_cost_bps": self.estimated_total_cost_bps,
        }

    def safe_public_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        # Ensure metadata is safe
        data["metadata"].pop("secret", None)
        return data

class RebalanceSimulation(BaseModel):
    rebalance_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    current_weights: dict[str, float]
    target_weights: dict[str, float]
    actions: list[dict[str, Any]]
    estimated_turnover_pct: float
    estimated_cost_bps: float | None = None
    estimated_slippage_bps: float | None = None
    before_score: float | None = None
    after_score: float | None = None
    violations_before: list[PortfolioConstraintViolation] = Field(default_factory=list)
    violations_after: list[PortfolioConstraintViolation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Rebalance simulation is research-only. It is not an order list or portfolio advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
