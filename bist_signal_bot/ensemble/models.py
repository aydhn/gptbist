from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, model_validator


class EnsembleMode(str, Enum):
    METADATA_ONLY = "METADATA_ONLY"
    SCORE_ONLY = "SCORE_ONLY"
    FILTER_ONLY = "FILTER_ONLY"
    SCORE_AND_FILTER = "SCORE_AND_FILTER"
    RESEARCH_SELECT = "RESEARCH_SELECT"


class SignalVoteDirection(str, Enum):
    LONG_BIAS = "LONG_BIAS"
    SHORT_BIAS = "SHORT_BIAS"
    NEUTRAL = "NEUTRAL"
    WATCH = "WATCH"
    REJECT = "REJECT"
    UNKNOWN = "UNKNOWN"


class SignalSourceType(str, Enum):
    STRATEGY = "STRATEGY"
    INDICATOR = "INDICATOR"
    PATTERN = "PATTERN"
    DIVERGENCE = "DIVERGENCE"
    ML = "ML"
    REGIME = "REGIME"
    RISK = "RISK"
    PORTFOLIO_RISK = "PORTFOLIO_RISK"
    FUNDAMENTAL = "FUNDAMENTAL"
    BREADTH = "BREADTH"
    RELATIVE_STRENGTH = "RELATIVE_STRENGTH"
    SECTOR_ROTATION = "SECTOR_ROTATION"
    ADAPTIVE = "ADAPTIVE"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"


class EnsembleDecision(str, Enum):
    APPROVED_RESEARCH = "APPROVED_RESEARCH"
    WATCH_ONLY = "WATCH_ONLY"
    REDUCE_CONFIDENCE = "REDUCE_CONFIDENCE"
    REJECTED = "REJECTED"
    INSUFFICIENT_AGREEMENT = "INSUFFICIENT_AGREEMENT"
    CONFLICTED = "CONFLICTED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class ConflictType(str, Enum):
    DIRECTIONAL_CONFLICT = "DIRECTIONAL_CONFLICT"
    SCORE_CONFLICT = "SCORE_CONFLICT"
    REGIME_CONFLICT = "REGIME_CONFLICT"
    RISK_CONFLICT = "RISK_CONFLICT"
    ML_TECHNICAL_CONFLICT = "ML_TECHNICAL_CONFLICT"
    FUNDAMENTAL_TECHNICAL_CONFLICT = "FUNDAMENTAL_TECHNICAL_CONFLICT"
    BREADTH_SIGNAL_CONFLICT = "BREADTH_SIGNAL_CONFLICT"
    LOW_AGREEMENT = "LOW_AGREEMENT"
    DATA_QUALITY_CONFLICT = "DATA_QUALITY_CONFLICT"
    UNKNOWN = "UNKNOWN"


class SignalVote(BaseModel):
    vote_id: str
    source_type: SignalSourceType
    source_name: str
    symbol: str
    direction: SignalVoteDirection
    score: float | None = None
    confidence: float | None = None
    weight: float = 1.0
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_fields(self):
        self.symbol = self.symbol.upper()
        if self.score is not None:
            self.score = max(0.0, min(100.0, self.score))
        if self.confidence is not None:
            self.confidence = max(0.0, min(100.0, self.confidence))
        if self.weight < 0:
            raise ValueError("weight must be >= 0")
        if not self.source_name:
            raise ValueError("source_name cannot be empty")
        return self


class EnsembleWeights(BaseModel):
    strategy_weight: float = 0.25
    indicator_weight: float = 0.10
    pattern_weight: float = 0.05
    divergence_weight: float = 0.05
    ml_weight: float = 0.15
    regime_weight: float = 0.10
    risk_weight: float = 0.15
    fundamental_weight: float = 0.05
    breadth_weight: float = 0.05
    relative_strength_weight: float = 0.03
    sector_rotation_weight: float = 0.01
    adaptive_weight: float = 0.01
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_weights(self):
        fields = [
            self.strategy_weight, self.indicator_weight, self.pattern_weight,
            self.divergence_weight, self.ml_weight, self.regime_weight,
            self.risk_weight, self.fundamental_weight, self.breadth_weight,
            self.relative_strength_weight, self.sector_rotation_weight, self.adaptive_weight
        ]
        if any(w < 0 for w in fields):
            raise ValueError("Negative weights are not allowed")
        return self

    def normalized(self) -> "EnsembleWeights":
        total = (
            self.strategy_weight + self.indicator_weight + self.pattern_weight +
            self.divergence_weight + self.ml_weight + self.regime_weight +
            self.risk_weight + self.fundamental_weight + self.breadth_weight +
            self.relative_strength_weight + self.sector_rotation_weight + self.adaptive_weight
        )
        if total == 0:
            raise ValueError("Total weight cannot be zero")

        return EnsembleWeights(
            strategy_weight=self.strategy_weight / total,
            indicator_weight=self.indicator_weight / total,
            pattern_weight=self.pattern_weight / total,
            divergence_weight=self.divergence_weight / total,
            ml_weight=self.ml_weight / total,
            regime_weight=self.regime_weight / total,
            risk_weight=self.risk_weight / total,
            fundamental_weight=self.fundamental_weight / total,
            breadth_weight=self.breadth_weight / total,
            relative_strength_weight=self.relative_strength_weight / total,
            sector_rotation_weight=self.sector_rotation_weight / total,
            adaptive_weight=self.adaptive_weight / total,
            metadata=self.metadata
        )

    def to_source_weight_map(self) -> dict[SignalSourceType, float]:
        norm = self.normalized()
        return {
            SignalSourceType.STRATEGY: norm.strategy_weight,
            SignalSourceType.INDICATOR: norm.indicator_weight,
            SignalSourceType.PATTERN: norm.pattern_weight,
            SignalSourceType.DIVERGENCE: norm.divergence_weight,
            SignalSourceType.ML: norm.ml_weight,
            SignalSourceType.REGIME: norm.regime_weight,
            SignalSourceType.RISK: norm.risk_weight,
            SignalSourceType.PORTFOLIO_RISK: norm.risk_weight,
            SignalSourceType.FUNDAMENTAL: norm.fundamental_weight,
            SignalSourceType.BREADTH: norm.breadth_weight,
            SignalSourceType.RELATIVE_STRENGTH: norm.relative_strength_weight,
            SignalSourceType.SECTOR_ROTATION: norm.sector_rotation_weight,
            SignalSourceType.ADAPTIVE: norm.adaptive_weight,
            SignalSourceType.MANUAL: 0.0,
            SignalSourceType.UNKNOWN: 0.0,
        }


class EnsembleConflict(BaseModel):
    conflict_id: str
    conflict_type: ConflictType
    symbol: str
    severity: str
    message: str
    involved_votes: list[str]
    recommended_action: EnsembleDecision
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnsembleExplanation(BaseModel):
    symbol: str
    headline: str
    positive_factors: list[str]
    negative_factors: list[str]
    neutral_factors: list[str]
    conflicts: list[str]
    score_breakdown: dict[str, float]
    confidence_notes: list[str]
    disclaimer: str = "Explanation is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConsensusSignal(BaseModel):
    consensus_id: str
    symbol: str
    as_of_date: datetime
    mode: EnsembleMode
    decision: EnsembleDecision
    direction: SignalVoteDirection
    consensus_score: float
    confidence: float
    agreement_ratio: float
    conflict_score: float
    votes: list[SignalVote]
    conflicts: list[EnsembleConflict]
    explanation: EnsembleExplanation
    final_metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Consensus signal is research-only. Not investment advice. No real order was sent."

    def summary(self) -> dict[str, Any]:
        return {
            "consensus_id": self.consensus_id,
            "symbol": self.symbol,
            "decision": self.decision.value,
            "direction": self.direction.value,
            "score": self.consensus_score,
            "confidence": self.confidence,
            "agreement": self.agreement_ratio,
            "conflict": self.conflict_score
        }

    def safe_public_dict(self) -> dict[str, Any]:
        d = self.summary()
        d["disclaimer"] = self.disclaimer
        d["warnings"] = self.warnings
        return d


class EnsembleRequest(BaseModel):
    symbols: list[str]
    strategy_names: list[str] = Field(default_factory=list)
    source: str = "local"
    timeframe: str
    as_of_date: datetime | None = None
    mode: EnsembleMode = EnsembleMode.METADATA_ONLY
    weights: EnsembleWeights | None = None
    include_ml: bool = True
    include_regime: bool = True
    include_risk: bool = True
    include_fundamentals: bool = True
    include_breadth: bool = True
    include_adaptive: bool = True
    save_output: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_request(self):
        self.symbols = [s.upper() for s in self.symbols]
        if not self.timeframe:
            raise ValueError("timeframe cannot be empty")
        return self


class EnsembleResult(BaseModel):
    request: EnsembleRequest
    consensus_signals: list[ConsensusSignal]
    ranked_signals: list[ConsensusSignal]
    rejected_signals: list[ConsensusSignal]
    output_files: dict[str, str] = Field(default_factory=dict)
    elapsed_seconds: float
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Ensemble result is research-only. Past results do not guarantee future performance. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "mode": self.request.mode.value,
            "total_symbols": len(self.request.symbols),
            "consensus_count": len(self.consensus_signals),
            "ranked_count": len(self.ranked_signals),
            "rejected_count": len(self.rejected_signals),
            "elapsed_seconds": self.elapsed_seconds,
            "warnings": self.warnings
        }
