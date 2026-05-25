from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

class StrategyRegistryStatus(str, Enum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    CANDIDATE = "CANDIDATE"
    VALIDATED_RESEARCH = "VALIDATED_RESEARCH"
    WATCH = "WATCH"
    DEGRADED = "DEGRADED"
    DEPRECATED = "DEPRECATED"
    BLOCKED = "BLOCKED"
    ARCHIVED = "ARCHIVED"
    UNKNOWN = "UNKNOWN"

class StrategyLifecycleEventType(str, Enum):
    REGISTERED = "REGISTERED"
    UPDATED = "UPDATED"
    SCORED = "SCORED"
    PROMOTED = "PROMOTED"
    DEMOTED = "DEMOTED"
    BLOCKED = "BLOCKED"
    UNBLOCKED = "UNBLOCKED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"
    EVIDENCE_LINKED = "EVIDENCE_LINKED"
    CONFIG_CHANGED = "CONFIG_CHANGED"
    UNKNOWN = "UNKNOWN"

class StrategyFamily(str, Enum):
    TREND = "TREND"
    MOMENTUM = "MOMENTUM"
    MEAN_REVERSION = "MEAN_REVERSION"
    BREAKOUT = "BREAKOUT"
    VOLATILITY = "VOLATILITY"
    VOLUME = "VOLUME"
    PAIR_RELATIVE = "PAIR_RELATIVE"
    FACTOR = "FACTOR"
    ML = "ML"
    ENSEMBLE = "ENSEMBLE"
    HYBRID = "HYBRID"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"

class StrategyEvidenceType(str, Enum):
    BACKTEST = "BACKTEST"
    WALK_FORWARD = "WALK_FORWARD"
    PURGED_CV = "PURGED_CV"
    PARAMETER_STABILITY = "PARAMETER_STABILITY"
    OVERFIT_DIAGNOSTICS = "OVERFIT_DIAGNOSTICS"
    MONTE_CARLO = "MONTE_CARLO"
    EXECUTION_QUALITY = "EXECUTION_QUALITY"
    DRIFT = "DRIFT"
    PERFORMANCE_BENCHMARK = "PERFORMANCE_BENCHMARK"
    ANALYST_REVIEW = "ANALYST_REVIEW"
    GOVERNANCE = "GOVERNANCE"
    RESEARCH_LEDGER = "RESEARCH_LEDGER"
    KNOWLEDGE = "KNOWLEDGE"
    CUSTOM = "CUSTOM"

class StrategyGateDecision(str, Enum):
    ALLOW = "ALLOW"
    WATCH = "WATCH"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"
    REQUIRE_MORE_EVIDENCE = "REQUIRE_MORE_EVIDENCE"
    BLOCK = "BLOCK"
    SKIP = "SKIP"
    UNKNOWN = "UNKNOWN"

@dataclass
class StrategyScoreComponent:
    component_id: str
    name: str
    evidence_type: StrategyEvidenceType
    score: float | None
    weight: float
    status: StrategyRegistryStatus | None
    message: str
    evidence_refs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.score is not None:
            self.score = max(0.0, min(100.0, self.score))
        if self.weight < 0:
            raise ValueError("weight cannot be negative")

@dataclass
class StrategyDefinition:
    strategy_id: str
    strategy_name: str
    display_name: str
    version: str
    family: StrategyFamily
    status: StrategyRegistryStatus
    module_path: str | None = None
    class_name: str | None = None
    default_parameters: dict[str, Any] = field(default_factory=dict)
    parameter_schema: dict[str, Any] = field(default_factory=dict)
    supported_timeframes: list[str] = field(default_factory=list)
    supported_order_sides: list[str] = field(default_factory=list)
    supported_universes: list[str] = field(default_factory=list)
    requires_adjusted_prices: bool = False
    supports_short: bool = False
    supports_cost_model: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    owner: str | None = None
    tags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Strategy definition is research metadata only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.strategy_name:
            raise ValueError("strategy_name cannot be empty")
        if not self.version:
            raise ValueError("version cannot be empty")

        # Check for forbidden patterns
        forbidden_keys = ["broker", "live_trading", "order_routing", "real_money"]
        if self.metadata:
            for key in self.metadata:
                if any(f in key.lower() for f in forbidden_keys):
                    self.warnings.append(f"Forbidden metadata key detected: {key}. Marking as BLOCKED.")
                    self.status = StrategyRegistryStatus.BLOCKED

@dataclass
class StrategyEvidenceRef:
    evidence_id: str
    strategy_id: str
    evidence_type: StrategyEvidenceType
    source_ref: str | None = None
    symbol: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    title: str = ""
    summary: str = ""
    score: float | None = None
    status: str | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class StrategyScorecard:
    scorecard_id: str
    strategy_id: str
    strategy_name: str
    version: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    components: list[StrategyScoreComponent] = field(default_factory=list)
    aggregate_score: float | None = None
    confidence_score: float | None = None
    robustness_score: float | None = None
    overfit_risk_score: float | None = None
    execution_penalty_score: float | None = None
    drift_risk_score: float | None = None
    status: StrategyRegistryStatus = StrategyRegistryStatus.UNKNOWN
    gate_decision: StrategyGateDecision = StrategyGateDecision.UNKNOWN
    recommended_actions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Strategy scorecard is research-only. It does not approve real trading. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "scorecard_id": self.scorecard_id,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "aggregate_score": self.aggregate_score,
            "status": self.status.value,
            "gate_decision": self.gate_decision.value,
            "warnings_count": len(self.warnings),
            "generated_at": self.generated_at.isoformat()
        }

@dataclass
class StrategyLifecycleEvent:
    event_id: str
    strategy_id: str
    strategy_name: str
    event_type: StrategyLifecycleEventType
    previous_status: StrategyRegistryStatus | None = None
    new_status: StrategyRegistryStatus | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    reason: str = ""
    actor: str | None = None
    evidence_refs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Strategy lifecycle event is research metadata only. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class StrategyPromotionRequest:
    strategy_id: str
    target_status: StrategyRegistryStatus
    reason: str
    require_scorecard: bool = True
    require_validation: bool = True
    require_monte_carlo: bool = True
    require_governance_pass: bool = True
    confirm: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class StrategyPromotionResult:
    promotion_id: str
    request: StrategyPromotionRequest
    decision: StrategyGateDecision
    previous_status: StrategyRegistryStatus
    new_status: StrategyRegistryStatus | None = None
    scorecard: StrategyScorecard | None = None
    event: StrategyLifecycleEvent | None = None
    blocked_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Strategy promotion result is research-only. It is not permission for real orders. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class StrategyRegistrySnapshot:
    snapshot_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    strategies_count: int = 0
    status_counts: dict[str, int] = field(default_factory=dict)
    scorecards_count: int = 0
    blocked_strategies: list[str] = field(default_factory=list)
    candidate_strategies: list[str] = field(default_factory=list)
    validated_research_strategies: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checksum_sha256: str | None = None
    disclaimer: str = "Strategy registry snapshot is operational research metadata only. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)
