from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator

class ExplanationStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    BLOCKED = "BLOCKED"
    DEGRADED = "DEGRADED"
    WARN = "WARN"
    FAIL = "FAIL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED_MODEL = "UNSUPPORTED_MODEL"

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
    UNSUPPORTED_MODEL = "UNSUPPORTED_MODEL"

class ContributionStrength(str, Enum):
    VERY_WEAK = "VERY_WEAK"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED_MODEL = "UNSUPPORTED_MODEL"

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

    @field_validator("contribution_score")
    @classmethod
    def _clamp_contribution_score(cls, v: float | None) -> float | None:
        if v is not None:
            return max(-100.0, min(100.0, v))
        return v

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
        return self.model_dump(
            include={
                "explanation_id",
                "signal_id",
                "symbol",
                "strategy_name",
                "generated_at",
                "summary",
                "final_status"
            },
            mode="json"
        )

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

class ExplanationObjectType(str, Enum):
    MODEL = "MODEL"
    STRATEGY = "STRATEGY"
    SIGNAL = "SIGNAL"
    FEATURE_SET = "FEATURE_SET"
    SCANNER_RESULT = "SCANNER_RESULT"
    BACKTEST_RESULT = "BACKTEST_RESULT"
    VALIDATION_RESULT = "VALIDATION_RESULT"
    CUSTOM = "CUSTOM"

class ExplanationMethod(str, Enum):
    FEATURE_ATTRIBUTION = "FEATURE_ATTRIBUTION"
    PERMUTATION_IMPORTANCE = "PERMUTATION_IMPORTANCE"
    SENSITIVITY_ANALYSIS = "SENSITIVITY_ANALYSIS"
    RULE_TRACE = "RULE_TRACE"
    DECISION_TRACE = "DECISION_TRACE"
    COUNTERFACTUAL_RESEARCH = "COUNTERFACTUAL_RESEARCH"
    COHORT_EXPLANATION = "COHORT_EXPLANATION"
    MODEL_INTROSPECTION = "MODEL_INTROSPECTION"
    FALLBACK_SIMPLE = "FALLBACK_SIMPLE"
    CUSTOM = "CUSTOM"

class AttributionDirection(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED_MODEL = "UNSUPPORTED_MODEL"

class ExplanationScope(str, Enum):
    LOCAL_ROW = "LOCAL_ROW"
    SYMBOL = "SYMBOL"
    COHORT = "COHORT"
    GLOBAL_MODEL = "GLOBAL_MODEL"
    STRATEGY = "STRATEGY"
    REPORT = "REPORT"
    CUSTOM = "CUSTOM"

class FeatureAttribution(BaseModel):
    attribution_id: str
    object_type: ExplanationObjectType
    object_id: str
    feature_name: str
    feature_value: float | int | str | bool | None = None
    contribution_score: float | None = None
    normalized_contribution: float | None = None
    direction: AttributionDirection
    rank: int | None = None
    method: ExplanationMethod
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("normalized_contribution")
    @classmethod
    def _clamp_normalized_contribution(cls, v: float | None) -> float | None:
        if v is not None:
            return max(-100.0, min(100.0, v))
        return v

    @field_validator("rank")
    @classmethod
    def _validate_rank(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            return None
        return v

class LocalExplanation(BaseModel):
    explanation_id: str
    object_type: ExplanationObjectType
    object_id: str
    scope: ExplanationScope
    symbol: str | None = None
    as_of: datetime | None = None
    method: ExplanationMethod
    prediction_value: float | None = None
    baseline_value: float | None = None
    attributions: list[FeatureAttribution] = Field(default_factory=list)
    key_drivers: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    status: ExplanationStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Local explanation is research-only interpretability metadata. It is not investment advice, a causal claim, or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class GlobalExplanation(BaseModel):
    explanation_id: str
    object_type: ExplanationObjectType
    object_id: str
    scope: ExplanationScope
    method: ExplanationMethod
    feature_importance: list[FeatureAttribution] = Field(default_factory=list)
    sample_count: int | None = None
    top_features: list[str] = Field(default_factory=list)
    stability_score: float | None = None
    status: ExplanationStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Global explanation summarizes local research metadata only. It is not investment advice or a guarantee of future model behavior. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class SensitivityPoint(BaseModel):
    point_id: str
    feature_name: str
    original_value: float | None = None
    perturbed_value: float | None = None
    output_value: float | None = None
    delta_output: float | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class SensitivityAnalysisResult(BaseModel):
    sensitivity_id: str
    object_type: ExplanationObjectType
    object_id: str
    feature_name: str
    symbol: str | None = None
    as_of: datetime | None = None
    points: list[SensitivityPoint] = Field(default_factory=list)
    monotonicity_hint: str | None = None
    max_abs_delta: float | None = None
    status: ExplanationStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Sensitivity analysis is local research diagnostics only. It is not a forecast, causal proof, or trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DecisionTraceStep(BaseModel):
    step_id: str
    step_name: str
    condition: str | None = None
    input_refs: dict[str, Any] = Field(default_factory=dict)
    output_value: Any | None = None
    passed: bool | None = None
    message: str = ""
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DecisionTrace(BaseModel):
    trace_id: str
    object_type: ExplanationObjectType = ExplanationObjectType.CUSTOM
    object_id: str = "unknown"
    symbol: str | None = None
    as_of: datetime | None = None
    steps: list[DecisionTraceStep] = Field(default_factory=list)
    final_output: dict[str, Any] = Field(default_factory=dict)
    status: ExplanationStatus = ExplanationStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Decision trace is local software evidence metadata only. It is not investment advice or an order instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Old fields for compatibility
    strategy_name: str | None = None
    signal_id: str | None = None
    created_at: datetime | None = None
    stages: list[dict[str, Any]] = Field(default_factory=list)
    final_decision: str = ""
    final_confidence: float | None = None
    blocked: bool = False
    blocked_reasons: list[str] = Field(default_factory=list)

class RuleTrace(BaseModel):
    rule_trace_id: str
    strategy_name: str
    symbol: str | None = None
    as_of: datetime | None = None
    rules_evaluated: list[DecisionTraceStep] = Field(default_factory=list)
    passed_rules: int = 0
    failed_rules: int = 0
    evidence_refs: list[str] = Field(default_factory=list)
    status: ExplanationStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Rule trace explains local research rule evaluation only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CounterfactualScenario(BaseModel):
    counterfactual_id: str
    object_type: ExplanationObjectType
    object_id: str
    symbol: str | None = None
    as_of: datetime | None = None
    changed_features: dict[str, Any] = Field(default_factory=dict)
    original_output: float | None = None
    counterfactual_output: float | None = None
    delta_output: float | None = None
    plausibility_status: ExplanationStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Counterfactual scenario is local research what-if metadata only. It is not a market prediction, investment advice, or trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ExplanationCohort(BaseModel):
    cohort_id: str
    name: str
    object_type: ExplanationObjectType
    object_ids: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    feature_names: list[str] = Field(default_factory=list)
    sample_count: int = 0
    created_at: datetime
    status: ExplanationStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ExplanationGovernanceAssessment(BaseModel):
    assessment_id: str
    object_type: ExplanationObjectType
    object_id: str
    created_at: datetime
    status: ExplanationStatus
    explainability_available: bool = False
    method_supported: bool = False
    feature_coverage_score: float | None = None
    attribution_stability_score: float | None = None
    unsafe_language_findings: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Explanation governance assessment is local software governance metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ExplainabilityReport(BaseModel):
    report_id: str
    generated_at: datetime
    local_explanations: list[LocalExplanation] = Field(default_factory=list)
    global_explanations: list[GlobalExplanation] = Field(default_factory=list)
    sensitivity_results: list[SensitivityAnalysisResult] = Field(default_factory=list)
    decision_traces: list[DecisionTrace] = Field(default_factory=list)
    rule_traces: list[RuleTrace] = Field(default_factory=list)
    counterfactuals: list[CounterfactualScenario] = Field(default_factory=list)
    governance_assessments: list[ExplanationGovernanceAssessment] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Explainability report is local interpretability reporting only. It is not investment advice, causal proof, or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
