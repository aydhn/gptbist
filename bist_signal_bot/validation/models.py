from enum import Enum
from typing import Any, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

class ValidationStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class ValidationSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ValidationSplitType(str, Enum):
    ROLLING = "ROLLING"
    ANCHORED = "ANCHORED"
    EXPANDING = "EXPANDING"
    PURGED_K_FOLD = "PURGED_K_FOLD"
    WALK_FORWARD = "WALK_FORWARD"
    CUSTOM = "CUSTOM"

class ValidationMetricType(str, Enum):
    TOTAL_RETURN = "TOTAL_RETURN"
    NET_TOTAL_RETURN = "NET_TOTAL_RETURN"
    SHARPE = "SHARPE"
    SORTINO = "SORTINO"
    MAX_DRAWDOWN = "MAX_DRAWDOWN"
    WIN_RATE = "WIN_RATE"
    PROFIT_FACTOR = "PROFIT_FACTOR"
    TRADE_COUNT = "TRADE_COUNT"
    TURNOVER = "TURNOVER"
    COST_DRAG = "COST_DRAG"
    SLIPPAGE_BPS = "SLIPPAGE_BPS"
    FILL_RATE = "FILL_RATE"
    PARAMETER_STABILITY = "PARAMETER_STABILITY"
    REGIME_STABILITY = "REGIME_STABILITY"
    OOS_DECAY = "OOS_DECAY"
    OVERFIT_SCORE = "OVERFIT_SCORE"
    CUSTOM = "CUSTOM"

class ValidationAction(str, Enum):
    NO_ACTION = "NO_ACTION"
    WATCH = "WATCH"
    REVIEW_MANUALLY = "REVIEW_MANUALLY"
    RUN_MORE_DATA = "RUN_MORE_DATA"
    RUN_COST_STRESS = "RUN_COST_STRESS"
    RUN_REGIME_TEST = "RUN_REGIME_TEST"
    REDUCE_CONFIDENCE = "REDUCE_CONFIDENCE"
    REQUIRE_WALK_FORWARD = "REQUIRE_WALK_FORWARD"
    REQUIRE_PURGED_CV = "REQUIRE_PURGED_CV"
    MARK_STRATEGY_RESEARCH_ONLY = "MARK_STRATEGY_RESEARCH_ONLY"
    AVOID_AUTO_SELECTION = "AVOID_AUTO_SELECTION"
    CUSTOM = "CUSTOM"

class ValidationSplit(BaseModel):
    split_id: str
    split_type: ValidationSplitType
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    purge_days: int = 0
    embargo_days: int = 0
    fold_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    breadth_context: str | None = None

    @model_validator(mode='after')
    def validate_split_dates(self) -> 'ValidationSplit':
        if self.train_start >= self.train_end:
            raise ValueError("train_start must be before train_end")
        if self.test_start >= self.test_end:
            raise ValueError("test_start must be before test_end")
        return self

class ValidationMetric(BaseModel):
    metric_id: str
    metric_type: ValidationMetricType
    name: str
    value: Any = None
    benchmark_value: Any = None
    status: ValidationStatus = ValidationStatus.UNKNOWN
    severity: ValidationSeverity = ValidationSeverity.INFO
    threshold_warn: float | None = None
    threshold_fail: float | None = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FoldValidationResult(BaseModel):
    fold_id: str
    split: ValidationSplit
    strategy_name: str
    symbol: str | None = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    train_metrics: List[ValidationMetric] = Field(default_factory=list)
    test_metrics: List[ValidationMetric] = Field(default_factory=list)
    gross_return_pct: float | None = None
    net_return_pct: float | None = None
    cost_drag_pct: float | None = None
    trade_count: int = 0
    status: ValidationStatus = ValidationStatus.UNKNOWN
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WalkForwardResult(BaseModel):
    walk_forward_id: str
    strategy_name: str
    symbol: str | None = None
    split_type: ValidationSplitType = ValidationSplitType.WALK_FORWARD
    folds: List[FoldValidationResult] = Field(default_factory=list)
    aggregate_metrics: List[ValidationMetric] = Field(default_factory=list)
    median_oos_return_pct: float | None = None
    oos_positive_fold_rate_pct: float | None = None
    median_cost_drag_pct: float | None = None
    stability_score: float | None = None
    status: ValidationStatus = ValidationStatus.UNKNOWN
    recommended_actions: List[ValidationAction] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Walk-forward validation is research-only. Past results do not guarantee future performance. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PurgedCVResult(BaseModel):
    cv_id: str
    strategy_name: str
    symbol: str | None = None
    folds: List[FoldValidationResult] = Field(default_factory=list)
    purge_days: int = 0
    embargo_days: int = 0
    aggregate_metrics: List[ValidationMetric] = Field(default_factory=list)
    leakage_warnings: List[str] = Field(default_factory=list)
    status: ValidationStatus = ValidationStatus.UNKNOWN
    recommended_actions: List[ValidationAction] = Field(default_factory=list)
    disclaimer: str = "Purged CV output is research-only. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ParameterStabilityResult(BaseModel):
    stability_id: str
    strategy_name: str
    symbol: str | None = None
    parameter_grid_summary: Dict[str, Any] = Field(default_factory=dict)
    best_parameters_by_fold: List[Dict[str, Any]] = Field(default_factory=list)
    parameter_variance: Dict[str, float | None] = Field(default_factory=dict)
    performance_surface_summary: Dict[str, Any] = Field(default_factory=dict)
    stability_score: float | None = None
    status: ValidationStatus = ValidationStatus.UNKNOWN
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Parameter stability output is research-only. It is not a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OverfitDiagnosticsResult(BaseModel):
    diagnostics_id: str
    strategy_name: str
    symbol: str | None = None
    in_sample_metrics: Dict[str, Any] = Field(default_factory=dict)
    out_of_sample_metrics: Dict[str, Any] = Field(default_factory=dict)
    oos_decay_pct: float | None = None
    parameter_instability_score: float | None = None
    performance_concentration_score: float | None = None
    overfit_score: float | None = None
    status: ValidationStatus = ValidationStatus.UNKNOWN
    severity: ValidationSeverity = ValidationSeverity.INFO
    recommended_actions: List[ValidationAction] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Overfit diagnostics are research-only. They do not prove future success or failure. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RegimeRobustnessResult(BaseModel):
    regime_result_id: str
    strategy_name: str
    symbol: str | None = None
    regime_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    weakest_regime: str | None = None
    strongest_regime: str | None = None
    regime_stability_score: float | None = None
    status: ValidationStatus = ValidationStatus.UNKNOWN
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Regime robustness output is research-only. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CostRobustnessResult(BaseModel):
    cost_result_id: str
    strategy_name: str
    symbol: str | None = None
    scenario_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    base_net_return_pct: float | None = None
    stress_net_return_pct: float | None = None
    cost_sensitivity_score: float | None = None
    status: ValidationStatus = ValidationStatus.UNKNOWN
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Cost robustness output is research-only. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class StrategyValidationRequest(BaseModel):
    strategy_name: str
    symbols: List[str] = Field(default_factory=list)
    split_type: ValidationSplitType = ValidationSplitType.WALK_FORWARD
    start_date: datetime | None = None
    end_date: datetime | None = None
    train_window_days: int = 252
    test_window_days: int = 63
    step_days: int = 63
    folds: int = 3
    purge_days: int = 0
    embargo_days: int = 0
    include_costs: bool = True
    include_slippage: bool = True
    include_regime_tests: bool = True
    include_parameter_stability: bool = True
    include_overfit_diagnostics: bool = True
    save_output: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_req(self) -> 'StrategyValidationRequest':
        if not self.strategy_name: raise ValueError("empty strategy")
        self.symbols = [s.upper().strip() for s in self.symbols if s.strip()]
        return self

class StrategyValidationResult(BaseModel):
    validation_id: str
    request: StrategyValidationRequest
    status: ValidationStatus = ValidationStatus.UNKNOWN
    severity: ValidationSeverity = ValidationSeverity.INFO
    walk_forward_results: List[WalkForwardResult] = Field(default_factory=list)
    purged_cv_results: List[PurgedCVResult] = Field(default_factory=list)
    parameter_stability_results: List[ParameterStabilityResult] = Field(default_factory=list)
    overfit_diagnostics: List[OverfitDiagnosticsResult] = Field(default_factory=list)
    regime_robustness_results: List[RegimeRobustnessResult] = Field(default_factory=list)
    cost_robustness_results: List[CostRobustnessResult] = Field(default_factory=list)
    aggregate_score: float | None = None
    recommended_actions: List[ValidationAction] = Field(default_factory=list)
    output_files: Dict[str, str] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    elapsed_seconds: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Strategy validation result is research-only. Not investment advice. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "validation_id": self.validation_id,
            "strategy_name": self.request.strategy_name,
            "status": self.status.value,
            "aggregate_score": self.aggregate_score
        }
    def safe_public_dict(self) -> Dict[str, Any]:
        return self.summary()
