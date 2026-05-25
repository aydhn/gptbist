from datetime import datetime, UTC
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class CalibrationStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class OutcomeLabel(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    NEUTRAL = "NEUTRAL"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    NOT_EVALUATED = "NOT_EVALUATED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"

class CalibrationScoreType(str, Enum):
    SIGNAL_CONFIDENCE = "SIGNAL_CONFIDENCE"
    CONSENSUS_SCORE = "CONSENSUS_SCORE"
    ML_SCORE = "ML_SCORE"
    STRATEGY_SCORE = "STRATEGY_SCORE"
    RISK_ADJUSTED_SCORE = "RISK_ADJUSTED_SCORE"
    REVIEW_CONFIDENCE = "REVIEW_CONFIDENCE"
    CALIBRATED_CONFIDENCE = "CALIBRATED_CONFIDENCE"
    CUSTOM = "CUSTOM"

class OutcomeHorizon(str, Enum):
    NEXT_BAR = "NEXT_BAR"
    ONE_DAY = "ONE_DAY"
    THREE_DAYS = "THREE_DAYS"
    FIVE_DAYS = "FIVE_DAYS"
    TEN_DAYS = "TEN_DAYS"
    TWENTY_DAYS = "TWENTY_DAYS"
    CUSTOM = "CUSTOM"

class CalibrationMetricType(str, Enum):
    BRIER_SCORE = "BRIER_SCORE"
    EXPECTED_CALIBRATION_ERROR = "EXPECTED_CALIBRATION_ERROR"
    MAX_CALIBRATION_ERROR = "MAX_CALIBRATION_ERROR"
    RELIABILITY_SLOPE = "RELIABILITY_SLOPE"
    HIT_RATE = "HIT_RATE"
    FALSE_POSITIVE_RATE = "FALSE_POSITIVE_RATE"
    FALSE_NEGATIVE_RATE = "FALSE_NEGATIVE_RATE"
    PRECISION = "PRECISION"
    RECALL = "RECALL"
    F1 = "F1"
    AUC_LITE = "AUC_LITE"
    NET_RETURN_BY_BIN = "NET_RETURN_BY_BIN"
    COST_DRAG_BY_BIN = "COST_DRAG_BY_BIN"
    SAMPLE_SIZE = "SAMPLE_SIZE"
    CUSTOM = "CUSTOM"

class ErrorCaseType(str, Enum):
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    LATE_SIGNAL = "LATE_SIGNAL"
    EARLY_SIGNAL = "EARLY_SIGNAL"
    HIGH_CONFIDENCE_FAILURE = "HIGH_CONFIDENCE_FAILURE"
    LOW_CONFIDENCE_SUCCESS = "LOW_CONFIDENCE_SUCCESS"
    EXECUTION_COST_DRAG = "EXECUTION_COST_DRAG"
    LIQUIDITY_FAILURE = "LIQUIDITY_FAILURE"
    REGIME_MISMATCH = "REGIME_MISMATCH"
    DRIFT_RELATED = "DRIFT_RELATED"
    DATA_QUALITY_RELATED = "DATA_QUALITY_RELATED"
    UNKNOWN = "UNKNOWN"

class ThresholdPolicyStatus(str, Enum):
    ACTIVE_RESEARCH = "ACTIVE_RESEARCH"
    CANDIDATE = "CANDIDATE"
    WATCH = "WATCH"
    DEPRECATED = "DEPRECATED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"

def _clamp_score(v: float | None) -> float | None:
    if v is None:
        return None
    return max(0.0, min(100.0, float(v)))

class OutcomeRecord(BaseModel):
    outcome_id: str
    signal_id: str | None = None
    symbol: str
    strategy_name: str | None = None
    generated_at: datetime
    evaluated_at: datetime | None = None
    horizon: OutcomeHorizon = OutcomeHorizon.FIVE_DAYS
    raw_score: float | None = None
    confidence_score: float | None = None
    consensus_score: float | None = None
    ml_score: float | None = None
    strategy_score: float | None = None
    risk_adjusted_score: float | None = None
    review_confidence: float | None = None
    gross_return_pct: float | None = None
    net_return_pct: float | None = None
    max_favorable_excursion_pct: float | None = None
    max_adverse_excursion_pct: float | None = None
    cost_drag_pct: float | None = None
    slippage_bps: float | None = None
    fill_rate_pct: float | None = None
    outcome_label: OutcomeLabel = OutcomeLabel.NOT_EVALUATED
    regime_label: str | None = None
    sector: str | None = None
    liquidity_status: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol", mode="before")
    def normalize_symbol(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.upper().strip()
            if v.endswith(".IS"):
                v = v[:-3]
        return v

    @field_validator("raw_score", "confidence_score", "consensus_score", "ml_score", "strategy_score", "risk_adjusted_score", "review_confidence", mode="before")
    def clamp_scores(cls, v: float | None) -> float | None:
        return _clamp_score(v)

class CalibrationBin(BaseModel):
    bin_id: str
    score_type: CalibrationScoreType
    lower_bound: float
    upper_bound: float
    sample_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    neutral_count: int = 0
    average_score: float | None = None
    observed_success_rate: float | None = None
    average_gross_return_pct: float | None = None
    average_net_return_pct: float | None = None
    average_cost_drag_pct: float | None = None
    calibration_gap: float | None = None
    status: CalibrationStatus = CalibrationStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class CalibrationMetric(BaseModel):
    metric_id: str
    metric_type: CalibrationMetricType
    score_type: CalibrationScoreType
    name: str
    value: float | int | str | None = None
    status: CalibrationStatus = CalibrationStatus.UNKNOWN
    threshold_warn: float | None = None
    threshold_fail: float | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ReliabilityCurve(BaseModel):
    curve_id: str
    score_type: CalibrationScoreType
    horizon: OutcomeHorizon
    bins: list[CalibrationBin] = Field(default_factory=list)
    expected_calibration_error: float | None = None
    max_calibration_error: float | None = None
    sample_count: int = 0
    status: CalibrationStatus = CalibrationStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Reliability curve is research-only calibration output. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CalibratorMapping(BaseModel):
    mapping_id: str
    score_type: CalibrationScoreType
    method: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    bin_mappings: dict[str, float] = Field(default_factory=dict)
    min_samples: int = 0
    status: CalibrationStatus = CalibrationStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class CalibrationResult(BaseModel):
    calibration_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    score_type: CalibrationScoreType
    horizon: OutcomeHorizon
    strategy_name: str | None = None
    symbol: str | None = None
    sample_count: int = 0
    bins: list[CalibrationBin] = Field(default_factory=list)
    metrics: list[CalibrationMetric] = Field(default_factory=list)
    reliability_curve: ReliabilityCurve | None = None
    calibrator_mapping: CalibratorMapping | None = None
    status: CalibrationStatus = CalibrationStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Calibration result is research-only. Calibrated confidence does not guarantee future outcomes. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ThresholdPolicy(BaseModel):
    policy_id: str
    strategy_name: str | None = None
    score_type: CalibrationScoreType
    threshold_value: float
    min_sample_count: int = 0
    horizon: OutcomeHorizon
    status: ThresholdPolicyStatus = ThresholdPolicyStatus.CANDIDATE
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reason: str
    expected_signal_reduction_pct: float | None = None
    expected_quality_change: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Threshold policy is research-only. It does not authorize real orders. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ThresholdOptimizationResult(BaseModel):
    optimization_id: str
    score_type: CalibrationScoreType
    strategy_name: str | None = None
    horizon: OutcomeHorizon
    candidate_thresholds: list[ThresholdPolicy] = Field(default_factory=list)
    selected_threshold: ThresholdPolicy | None = None
    objective_name: str
    sample_count: int = 0
    status: CalibrationStatus = CalibrationStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Threshold optimization result is research-only. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class OutcomeCohort(BaseModel):
    cohort_id: str
    name: str
    filters: dict[str, Any] = Field(default_factory=dict)
    sample_count: int = 0
    success_rate: float | None = None
    average_net_return_pct: float | None = None
    average_score: float | None = None
    calibration_gap: float | None = None
    dominant_error_types: list[str] = Field(default_factory=list)
    status: CalibrationStatus = CalibrationStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ErrorCase(BaseModel):
    error_id: str
    outcome_id: str
    signal_id: str | None = None
    symbol: str
    strategy_name: str | None = None
    error_type: ErrorCaseType
    severity: str
    message: str
    score_at_signal: float | None = None
    net_return_pct: float | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class CalibrationReport(BaseModel):
    report_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    results: list[CalibrationResult] = Field(default_factory=list)
    threshold_results: list[ThresholdOptimizationResult] = Field(default_factory=list)
    cohorts: list[OutcomeCohort] = Field(default_factory=list)
    error_cases: list[ErrorCase] = Field(default_factory=list)
    overall_status: CalibrationStatus = CalibrationStatus.UNKNOWN
    key_findings: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Calibration report is research-only. It is not investment advice and does not authorize real orders. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
