from typing import Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, field_validator

class AdaptiveMode(str, Enum):
    DISABLED = "DISABLED"
    RECOMMEND_ONLY = "RECOMMEND_ONLY"
    METADATA_ONLY = "METADATA_ONLY"
    APPLY_WITH_CONFIRM = "APPLY_WITH_CONFIRM"
    RUNTIME_SELECT = "RUNTIME_SELECT"

class AdaptiveDecisionStatus(str, Enum):
    APPROVED_RESEARCH = "APPROVED_RESEARCH"
    REJECTED = "REJECTED"
    WATCH_ONLY = "WATCH_ONLY"
    NEEDS_REFRESH = "NEEDS_REFRESH"
    NEEDS_RETRAIN = "NEEDS_RETRAIN"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"

class AdaptiveEvidenceType(str, Enum):
    BACKTEST = "BACKTEST"
    WALK_FORWARD = "WALK_FORWARD"
    OPTIMIZATION = "OPTIMIZATION"
    PAPER_TRADING = "PAPER_TRADING"
    SCANNER_HISTORY = "SCANNER_HISTORY"
    ML_MODEL = "ML_MODEL"
    REGIME = "REGIME"
    RUNTIME_PERFORMANCE = "RUNTIME_PERFORMANCE"
    MONITORING = "MONITORING"
    MANUAL = "MANUAL"

class AdaptiveRefreshAction(str, Enum):
    NO_ACTION = "NO_ACTION"
    RUN_BACKTEST = "RUN_BACKTEST"
    RUN_OPTIMIZATION = "RUN_OPTIMIZATION"
    RUN_WALK_FORWARD = "RUN_WALK_FORWARD"
    REFRESH_PARAMETERS = "REFRESH_PARAMETERS"
    RETRAIN_MODEL = "RETRAIN_MODEL"
    REDUCE_UNIVERSE = "REDUCE_UNIVERSE"
    LOWER_RISK = "LOWER_RISK"
    DISABLE_STRATEGY_RESEARCH = "DISABLE_STRATEGY_RESEARCH"
    WATCH_ONLY = "WATCH_ONLY"

class AdaptiveConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"

class AdaptivePolicy(BaseModel):
    mode: AdaptiveMode = Field(default=AdaptiveMode.RECOMMEND_ONLY)
    min_evidence_count: int = Field(default=2)
    min_backtest_trades: int = Field(default=10)
    min_walk_forward_splits: int = Field(default=3)
    min_oos_positive_split_pct: float = Field(default=50.0)
    max_allowed_drawdown_pct: float = Field(default=35.0)
    min_profit_factor: float = Field(default=1.0)
    min_sharpe: float = Field(default=-5.0)
    min_paper_trades: int = Field(default=5)
    max_recent_paper_drawdown_pct: float = Field(default=20.0)
    max_model_age_days: int = Field(default=30)
    min_ml_score: float = Field(default=50.0)
    require_regime_match: bool = Field(default=False)
    reject_high_overfit_warning: bool = Field(default=True)
    auto_apply_requires_confirm: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_policy(self) -> 'AdaptivePolicy':
        if self.min_evidence_count < 0: raise ValueError("min_evidence_count must be >= 0")
        if self.min_backtest_trades < 0: raise ValueError("min_backtest_trades must be >= 0")
        if self.min_walk_forward_splits < 0: raise ValueError("min_walk_forward_splits must be >= 0")
        if self.min_paper_trades < 0: raise ValueError("min_paper_trades must be >= 0")
        if self.max_model_age_days <= 0: raise ValueError("max_model_age_days must be positive")
        if not (0 <= self.min_oos_positive_split_pct <= 100): raise ValueError("min_oos_positive_split_pct 0-100")
        if not (0 <= self.max_allowed_drawdown_pct <= 100): raise ValueError("max_allowed_drawdown_pct 0-100")
        if not (0 <= self.max_recent_paper_drawdown_pct <= 100): raise ValueError("max_recent_paper_drawdown_pct 0-100")
        if not (0 <= self.min_ml_score <= 100): raise ValueError("min_ml_score 0-100")
        return self

class AdaptiveEvidence(BaseModel):
    evidence_id: str
    evidence_type: AdaptiveEvidenceType
    symbol: str | None = None
    strategy_name: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    score: float | None = None
    confidence: float | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    source_path: str | None = None
    generated_at: datetime
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("score", "confidence")
    @classmethod
    def validate_score(cls, v: float | None) -> float | None:
        if v is not None:
            return max(0.0, min(100.0, v))
        return v

class AdaptiveStrategyCandidate(BaseModel):
    symbol: str
    strategy_name: str
    params: dict[str, Any]
    regime_tags: list[str] = Field(default_factory=list)
    evidence_items: list[AdaptiveEvidence] = Field(default_factory=list)
    composite_score: float = Field(default=0.0)
    confidence: AdaptiveConfidenceLevel = Field(default=AdaptiveConfidenceLevel.UNKNOWN)
    status: AdaptiveDecisionStatus = Field(default=AdaptiveDecisionStatus.SKIPPED)
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    breadth_regime_alignment: str | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy_name,
            "status": self.status.value,
            "score": round(self.composite_score, 2),
            "confidence": self.confidence.value,
            "evidence_count": len(self.evidence_items),
            "reasons": self.reasons,
            "warnings": self.warnings
        }

class AdaptiveParameterSet(BaseModel):
    parameter_set_id: str
    strategy_name: str
    symbol: str | None = None
    params: dict[str, Any]
    source: str
    score: float
    active: bool = True
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class AdaptiveRefreshPlanItem(BaseModel):
    action: AdaptiveRefreshAction
    symbol: str | None = None
    strategy_name: str | None = None
    reason: str
    priority: int = 0
    command_preview: list[str] = Field(default_factory=list)
    requires_confirm: bool = True
    safe_to_auto_run: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

class AdaptiveRefreshPlan(BaseModel):
    plan_id: str
    items: list[AdaptiveRefreshPlanItem] = Field(default_factory=list)
    generated_at: datetime
    status: AdaptiveDecisionStatus = Field(default=AdaptiveDecisionStatus.SKIPPED)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Adaptive refresh plan is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "status": self.status.value,
            "item_count": len(self.items),
            "warnings": self.warnings
        }

class ModelRefreshRecommendation(BaseModel):
    model_id: str | None = None
    model_type: str | None = None
    target_col: str | None = None
    should_retrain: bool = False
    reason: str
    model_age_days: float | None = None
    feature_mismatch_count: int | None = None
    drift_score: float | None = None
    recommended_command: list[str] | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class AdaptiveRecommendation(BaseModel):
    recommendation_id: str
    mode: AdaptiveMode
    candidates: list[AdaptiveStrategyCandidate] = Field(default_factory=list)
    selected_candidates: list[AdaptiveStrategyCandidate] = Field(default_factory=list)
    refresh_plan: AdaptiveRefreshPlan | None = None
    model_refresh_recommendations: list[ModelRefreshRecommendation] = Field(default_factory=list)
    policy: AdaptivePolicy
    status: AdaptiveDecisionStatus
    generated_at: datetime
    elapsed_seconds: float = 0.0
    output_files: dict[str, str] = Field(default_factory=dict)
    disclaimer: str = "Adaptive recommendation output only. Past results do not guarantee future performance. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "status": self.status.value,
            "mode": self.mode.value,
            "candidates": len(self.candidates),
            "selected_candidates": len(self.selected_candidates),
            "refresh_items": len(self.refresh_plan.items) if self.refresh_plan else 0,
            "model_refresh_items": len(self.model_refresh_recommendations)
        }

    def safe_public_dict(self) -> dict[str, Any]:
        d = self.model_dump()
        d["policy"] = "REDACTED"
        return d
