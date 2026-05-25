from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class ExplanationStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class ExplanationType(str, Enum):
    SIGNAL = "SIGNAL"
    STRATEGY = "STRATEGY"
    RULE_TRACE = "RULE_TRACE"
    INDICATOR_STATE = "INDICATOR_STATE"
    FEATURE_ATTRIBUTION = "FEATURE_ATTRIBUTION"
    ML_MODEL = "ML_MODEL"
    ENSEMBLE = "ENSEMBLE"
    RISK = "RISK"
    EXECUTION = "EXECUTION"
    HISTORY_CONTEXT = "HISTORY_CONTEXT"
    EVIDENCE_CARD = "EVIDENCE_CARD"
    DECISION_TRACE = "DECISION_TRACE"
    CUSTOM = "CUSTOM"

class ContributionDirection(str, Enum):
    SUPPORTS = "SUPPORTS"
    OPPOSES = "OPPOSES"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"

class ContributionStrength(str, Enum):
    VERY_WEAK = "VERY_WEAK"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"
    UNKNOWN = "UNKNOWN"

class EvidenceCardSectionType(str, Enum):
    SUMMARY = "SUMMARY"
    SIGNAL_RATIONALE = "SIGNAL_RATIONALE"
    INDICATORS = "INDICATORS"
    FEATURE_ATTRIBUTION = "FEATURE_ATTRIBUTION"
    STRATEGY_RULES = "STRATEGY_RULES"
    ENSEMBLE = "ENSEMBLE"
    RISK = "RISK"
    EXECUTION = "EXECUTION"
    VALIDATION = "VALIDATION"
    MONTE_CARLO = "MONTE_CARLO"
    STRATEGY_SCORECARD = "STRATEGY_SCORECARD"
    HISTORY_CONTEXT = "HISTORY_CONTEXT"
    REVIEW_NOTES = "REVIEW_NOTES"
    GOVERNANCE = "GOVERNANCE"
    WARNINGS = "WARNINGS"
    CUSTOM = "CUSTOM"

class FeatureContribution(BaseModel):
    contribution_id: str
    feature_name: str
    value: float | int | str | None = None
    normalized_value: float | None = None
    contribution_score: float | None = None
    contribution_direction: ContributionDirection
    strength: ContributionStrength
    message: str
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.contribution_score is not None:
            self.contribution_score = max(-100.0, min(100.0, self.contribution_score))

class IndicatorExplanation(BaseModel):
    indicator_id: str
    indicator_name: str
    value: float | int | str | None = None
    threshold: float | int | str | None = None
    state: str
    contribution_direction: ContributionDirection
    strength: ContributionStrength
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class RuleTraceStep(BaseModel):
    step_id: str
    rule_name: str
    condition: str
    observed_value: Any = None
    expected_value: Any = None
    passed: bool
    contribution_direction: ContributionDirection
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class StrategyRuleTrace(BaseModel):
    trace_id: str
    strategy_name: str
    symbol: str | None = None
    steps: list[RuleTraceStep] = Field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    final_direction: ContributionDirection
    status: ExplanationStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Strategy rule trace is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MLExplanation(BaseModel):
    explanation_id: str
    model_name: str | None = None
    symbol: str | None = None
    predicted_score: float | None = None
    top_features: list[FeatureContribution] = Field(default_factory=list)
    method: str
    status: ExplanationStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "ML explanation is approximate research metadata. It is not causal proof or investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class EnsembleExplanation(BaseModel):
    explanation_id: str
    symbol: str | None = None
    consensus_score: float | None = None
    component_explanations: list[FeatureContribution] = Field(default_factory=list)
    agreement_count: int = 0
    disagreement_count: int = 0
    conflict_score: float | None = None
    final_direction: ContributionDirection
    status: ExplanationStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

class RiskExplanation(BaseModel):
    explanation_id: str
    symbol: str | None = None
    risk_status: str
    risk_score: float | None = None
    risk_factors: list[FeatureContribution] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

class ExecutionExplanation(BaseModel):
    explanation_id: str
    symbol: str | None = None
    liquidity_status: str | None = None
    estimated_cost_bps: float | None = None
    estimated_slippage_bps: float | None = None
    fill_probability: float | None = None
    execution_factors: list[FeatureContribution] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

class HistoryContextExplanation(BaseModel):
    explanation_id: str
    symbol: str | None = None
    strategy_name: str | None = None
    similar_cases_count: int = 0
    relevant_memory: list[str] = Field(default_factory=list)
    repeated_patterns: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

class SignalExplanation(BaseModel):
    explanation_id: str
    signal_id: str | None = None
    symbol: str
    strategy_name: str | None = None
    generated_at: datetime
    summary: str
    indicator_explanations: list[IndicatorExplanation] = Field(default_factory=list)
    feature_contributions: list[FeatureContribution] = Field(default_factory=list)
    rule_trace: StrategyRuleTrace | None = None
    ml_explanation: MLExplanation | None = None
    ensemble_explanation: EnsembleExplanation | None = None
    risk_explanation: RiskExplanation | None = None
    execution_explanation: ExecutionExplanation | None = None
    history_context: HistoryContextExplanation | None = None
    confidence_breakdown: dict[str, Any] = Field(default_factory=dict)
    final_status: ExplanationStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Signal explanation is research-only. It is not investment advice or an order instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary_dict(self) -> dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "strategy_name": self.strategy_name,
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary,
            "final_status": self.final_status.value
        }

class EvidenceCardSection(BaseModel):
    section_id: str
    section_type: EvidenceCardSectionType
    title: str
    body: str
    score: float | None = None
    status: ExplanationStatus
    warnings: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class EvidenceCard(BaseModel):
    card_id: str
    symbol: str
    strategy_name: str | None = None
    signal_id: str | None = None
    created_at: datetime
    title: str
    summary: str
    sections: list[EvidenceCardSection] = Field(default_factory=list)
    overall_score: float | None = None
    overall_status: ExplanationStatus
    key_supporting_points: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Evidence card is research-only. It is not investment advice or permission for real orders. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DecisionTrace(BaseModel):
    trace_id: str
    symbol: str
    strategy_name: str | None = None
    signal_id: str | None = None
    created_at: datetime
    stages: list[dict[str, Any]] = Field(default_factory=list)
    final_decision: str
    final_confidence: float | None = None
    blocked: bool = False
    blocked_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Decision trace is operational research metadata only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
