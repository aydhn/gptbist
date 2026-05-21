import enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field

class DriftStatus(str, enum.Enum):
    STABLE = "STABLE"
    WATCH = "WATCH"
    DRIFTING = "DRIFTING"
    SEVERE_DRIFT = "SEVERE_DRIFT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class DriftSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class DriftTestType(str, enum.Enum):
    PSI = "PSI"
    KS_TEST = "KS_TEST"
    WASSERSTEIN = "WASSERSTEIN"
    MEAN_SHIFT = "MEAN_SHIFT"
    STD_SHIFT = "STD_SHIFT"
    QUANTILE_SHIFT = "QUANTILE_SHIFT"
    CATEGORY_SHIFT = "CATEGORY_SHIFT"
    RATE_CHANGE = "RATE_CHANGE"
    CALIBRATION_ERROR = "CALIBRATION_ERROR"
    CUSTOM = "CUSTOM"

class DriftDomain(str, enum.Enum):
    FEATURE = "FEATURE"
    MODEL_SCORE = "MODEL_SCORE"
    MODEL_CALIBRATION = "MODEL_CALIBRATION"
    SIGNAL_RATE = "SIGNAL_RATE"
    SIGNAL_OUTCOME = "SIGNAL_OUTCOME"
    STRATEGY_PERFORMANCE = "STRATEGY_PERFORMANCE"
    ENSEMBLE_CONSENSUS = "ENSEMBLE_CONSENSUS"
    PAPER_SIMULATION = "PAPER_SIMULATION"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    STRESS = "STRESS"
    DATA_QUALITY = "DATA_QUALITY"
    CUSTOM = "CUSTOM"

class ReferenceWindowType(str, enum.Enum):
    FIXED_DATE_RANGE = "FIXED_DATE_RANGE"
    ROLLING = "ROLLING"
    LAST_N_RUNS = "LAST_N_RUNS"
    LAST_N_DAYS = "LAST_N_DAYS"
    MODEL_TRAINING_WINDOW = "MODEL_TRAINING_WINDOW"
    CUSTOM = "CUSTOM"

class DriftAction(str, enum.Enum):
    NO_ACTION = "NO_ACTION"
    WATCH = "WATCH"
    REFRESH_FEATURES = "REFRESH_FEATURES"
    RETRAIN_MODEL = "RETRAIN_MODEL"
    RUN_BACKTEST = "RUN_BACKTEST"
    RUN_OPTIMIZATION = "RUN_OPTIMIZATION"
    REDUCE_CONFIDENCE = "REDUCE_CONFIDENCE"
    MARK_WATCH_ONLY = "MARK_WATCH_ONLY"
    REVIEW_MANUALLY = "REVIEW_MANUALLY"
    DISABLE_RESEARCH_CANDIDATE = "DISABLE_RESEARCH_CANDIDATE"
    UPDATE_REFERENCE = "UPDATE_REFERENCE"

class DriftReferenceWindow(BaseModel):
    reference_id: str
    window_type: ReferenceWindowType
    domain: DriftDomain
    start_date: datetime | None = None
    end_date: datetime | None = None
    sample_count: int
    source_path: str | None = None
    feature_names: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DriftMetric(BaseModel):
    metric_name: str
    test_type: DriftTestType
    domain: DriftDomain
    value: float | None = None
    threshold_warn: float | None = None
    threshold_fail: float | None = None
    status: DriftStatus = DriftStatus.UNKNOWN
    severity: DriftSeverity = DriftSeverity.UNKNOWN
    sample_count_reference: int = 0
    sample_count_current: int = 0
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureDriftResult(BaseModel):
    feature_name: str
    metrics: list[DriftMetric] = Field(default_factory=list)
    status: DriftStatus = DriftStatus.UNKNOWN
    severity: DriftSeverity = DriftSeverity.UNKNOWN
    reference_summary: dict[str, Any] = Field(default_factory=dict)
    current_summary: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ModelDriftResult(BaseModel):
    model_id: str | None = None
    model_type: str | None = None
    score_distribution_metrics: list[DriftMetric] = Field(default_factory=list)
    prediction_rate_metrics: list[DriftMetric] = Field(default_factory=list)
    feature_drift_results: list[FeatureDriftResult] = Field(default_factory=list)
    calibration_result: dict[str, Any] | None = None
    status: DriftStatus = DriftStatus.UNKNOWN
    severity: DriftSeverity = DriftSeverity.UNKNOWN
    recommended_actions: list[DriftAction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class CalibrationBin(BaseModel):
    bin_id: str
    lower_bound: float
    upper_bound: float
    sample_count: int
    average_prediction: float | None = None
    observed_rate: float | None = None
    calibration_error: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class CalibrationReport(BaseModel):
    report_id: str
    model_id: str | None = None
    bins: list[CalibrationBin] = Field(default_factory=list)
    expected_calibration_error: float | None = None
    maximum_calibration_error: float | None = None
    brier_score: float | None = None
    status: DriftStatus = DriftStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Calibration report is research-only. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class SignalDecayReport(BaseModel):
    report_id: str
    domain: DriftDomain
    signal_count_reference: int = 0
    signal_count_current: int = 0
    alert_rate_change_pct: float | None = None
    outcome_rate_change_pct: float | None = None
    muted_alert_rate_change_pct: float | None = None
    invalidation_rate_change_pct: float | None = None
    average_score_change: float | None = None
    average_confidence_change: float | None = None
    metrics: list[DriftMetric] = Field(default_factory=list)
    status: DriftStatus = DriftStatus.UNKNOWN
    severity: DriftSeverity = DriftSeverity.UNKNOWN
    recommended_actions: list[DriftAction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Signal decay report is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class StrategyDecayReport(BaseModel):
    report_id: str
    strategy_name: str
    reference_metrics: dict[str, Any] = Field(default_factory=dict)
    current_metrics: dict[str, Any] = Field(default_factory=dict)
    metric_changes: dict[str, float | None] = Field(default_factory=dict)
    decay_score: float = 0.0
    status: DriftStatus = DriftStatus.UNKNOWN
    severity: DriftSeverity = DriftSeverity.UNKNOWN
    recommended_actions: list[DriftAction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Strategy decay report is research-only. Past results do not guarantee future performance. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class PortfolioDriftReport(BaseModel):
    report_id: str
    reference_snapshot_id: str | None = None
    current_snapshot_id: str | None = None
    exposure_drift_metrics: list[DriftMetric] = Field(default_factory=list)
    concentration_change: float | None = None
    correlation_change: float | None = None
    stress_rating_change: str | None = None
    status: DriftStatus = DriftStatus.UNKNOWN
    severity: DriftSeverity = DriftSeverity.UNKNOWN
    recommended_actions: list[DriftAction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Portfolio drift report is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DriftAnalysisRequest(BaseModel):
    domains: list[DriftDomain] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    strategies: list[str] = Field(default_factory=list)
    model_id: str | None = None
    reference_window: DriftReferenceWindow | None = None
    current_start: datetime | None = None
    current_end: datetime | None = None
    min_samples: int = 30
    save_output: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

class DriftAnalysisResult(BaseModel):
    drift_id: str
    request: DriftAnalysisRequest
    status: DriftStatus = DriftStatus.UNKNOWN
    severity: DriftSeverity = DriftSeverity.UNKNOWN
    reference_window: DriftReferenceWindow | None = None
    feature_results: list[FeatureDriftResult] = Field(default_factory=list)
    model_results: list[ModelDriftResult] = Field(default_factory=list)
    calibration_reports: list[CalibrationReport] = Field(default_factory=list)
    signal_decay_reports: list[SignalDecayReport] = Field(default_factory=list)
    strategy_decay_reports: list[StrategyDecayReport] = Field(default_factory=list)
    portfolio_drift_reports: list[PortfolioDriftReport] = Field(default_factory=list)
    overall_drift_score: float | None = None
    recommended_actions: list[DriftAction] = Field(default_factory=list)
    output_files: dict[str, str] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    elapsed_seconds: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Drift analysis output is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "drift_id": self.drift_id,
            "status": self.status.value,
            "severity": self.severity.value,
            "overall_drift_score": self.overall_drift_score,
            "recommended_actions": [a.value for a in self.recommended_actions],
            "feature_drift_count": len([r for r in self.feature_results if r.status in [DriftStatus.DRIFTING, DriftStatus.SEVERE_DRIFT]]),
            "model_drift_status": [r.status.value for r in self.model_results] if self.model_results else None,
            "generated_at": self.generated_at.isoformat(),
            "disclaimer": self.disclaimer
        }

    def safe_public_dict(self) -> dict[str, Any]:
        d = self.summary()
        d["warnings"] = self.warnings
        return d
