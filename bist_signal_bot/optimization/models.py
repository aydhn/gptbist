from enum import Enum
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

from bist_signal_bot.backtesting.models import BacktestPerformanceReport

class OptimizationMethod(str, Enum):
    GRID_SEARCH = "GRID_SEARCH"
    RANDOM_SEARCH = "RANDOM_SEARCH"
    WALK_FORWARD_GRID = "WALK_FORWARD_GRID"
    WALK_FORWARD_RANDOM = "WALK_FORWARD_RANDOM"

class ObjectiveMetric(str, Enum):
    TOTAL_RETURN = "TOTAL_RETURN"
    ANNUALIZED_RETURN = "ANNUALIZED_RETURN"
    SHARPE = "SHARPE"
    SORTINO = "SORTINO"
    CALMAR = "CALMAR"
    PROFIT_FACTOR = "PROFIT_FACTOR"
    MAX_DRAWDOWN = "MAX_DRAWDOWN"
    WIN_RATE = "WIN_RATE"
    EXPECTANCY = "EXPECTANCY"
    COMPOSITE = "COMPOSITE"

class OptimizationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    EMPTY = "EMPTY"

class ParameterType(str, Enum):
    INT = "INT"
    FLOAT = "FLOAT"
    BOOL = "BOOL"
    CATEGORICAL = "CATEGORICAL"

class ParameterSearchSpace(BaseModel):
    name: str
    param_type: ParameterType
    values: list[Any] | None = None
    min_value: float | int | None = None
    max_value: float | int | None = None
    step: float | int | None = None
    choices: list[Any] | None = None

    @validator("name")
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            from bist_signal_bot.core.exceptions import OptimizationValidationError
            raise OptimizationValidationError("Parameter name cannot be empty")
        return v

    @validator("values")
    def validate_values(cls, v: list[Any] | None, values: dict[str, Any]) -> list[Any] | None:
        if v is not None and len(v) == 0:
            from bist_signal_bot.core.exceptions import OptimizationValidationError
            raise OptimizationValidationError("If 'values' is provided, it cannot be empty")

        param_type = values.get("param_type")
        if param_type == ParameterType.BOOL and v is not None:
            if any(not isinstance(val, bool) for val in v):
                from bist_signal_bot.core.exceptions import OptimizationValidationError
                raise OptimizationValidationError("BOOL parameter requires boolean values")
        return v

    @validator("max_value")
    def validate_range(cls, v: float | int | None, values: dict[str, Any]) -> float | int | None:
        min_v = values.get("min_value")
        if min_v is not None and v is not None:
            if min_v > v:
                from bist_signal_bot.core.exceptions import OptimizationValidationError
                raise OptimizationValidationError(f"min_value ({min_v}) cannot be greater than max_value ({v})")
        return v

    @validator("step")
    def validate_step(cls, v: float | int | None) -> float | int | None:
        if v is not None and v <= 0:
            from bist_signal_bot.core.exceptions import OptimizationValidationError
            raise OptimizationValidationError("step must be positive")
        return v

    @validator("choices")
    def validate_choices(cls, v: list[Any] | None, values: dict[str, Any]) -> list[Any] | None:
        param_type = values.get("param_type")
        if param_type == ParameterType.CATEGORICAL and (v is None or len(v) == 0):
            from bist_signal_bot.core.exceptions import OptimizationValidationError
            raise OptimizationValidationError("CATEGORICAL parameter requires non-empty 'choices'")
        if param_type == ParameterType.BOOL and v is not None:
             if any(not isinstance(val, bool) for val in v):
                 from bist_signal_bot.core.exceptions import OptimizationValidationError
                 raise OptimizationValidationError("BOOL parameter requires boolean choices")
        return v

class OptimizationConstraints(BaseModel):
    min_trades: int = Field(default=0)
    max_drawdown_pct: float | None = None
    min_profit_factor: float | None = None
    min_sharpe: float | None = None
    min_total_return_pct: float | None = None
    max_cost_pct_of_profit: float | None = None
    require_positive_return: bool = Field(default=False)
    reject_same_close_research: bool = Field(default=False)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @validator("min_trades")
    def validate_min_trades(cls, v: int) -> int:
        if v < 0:
            from bist_signal_bot.core.exceptions import OptimizationValidationError
            raise OptimizationValidationError("min_trades cannot be negative")
        return v

    @validator("max_drawdown_pct")
    def validate_max_dd(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            from bist_signal_bot.core.exceptions import OptimizationValidationError
            raise OptimizationValidationError("max_drawdown_pct cannot be negative")
        return v

    @validator("max_cost_pct_of_profit")
    def validate_max_cost(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            from bist_signal_bot.core.exceptions import OptimizationValidationError
            raise OptimizationValidationError("max_cost_pct_of_profit cannot be negative")
        return v

class OptimizationConfig(BaseModel):
    method: OptimizationMethod = OptimizationMethod.GRID_SEARCH
    objective: ObjectiveMetric = ObjectiveMetric.COMPOSITE
    max_combinations: int = Field(default=100)
    random_seed: int = Field(default=42)
    top_n: int = Field(default=10)
    constraints: OptimizationConstraints = Field(default_factory=OptimizationConstraints)
    walk_forward_enabled: bool = Field(default=False)
    train_window_rows: int | None = None
    test_window_rows: int | None = None
    step_rows: int | None = None
    expanding: bool = Field(default=False)
    compare_benchmark: bool = Field(default=False)
    benchmark_name: str | None = None
    save_report: bool = Field(default=False)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @validator("max_combinations", "top_n")
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            from bist_signal_bot.core.exceptions import OptimizationValidationError
            raise OptimizationValidationError("Value must be positive")
        return v

    @validator("train_window_rows", "test_window_rows", "step_rows")
    def wf_must_be_positive(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            from bist_signal_bot.core.exceptions import OptimizationValidationError
            raise OptimizationValidationError("Walk-forward parameters must be positive")
        return v

class OptimizationTrial(BaseModel):
    trial_id: int
    params: dict[str, Any]
    status: OptimizationStatus
    performance_report: BacktestPerformanceReport | None = None
    backtest_summary: dict[str, Any] = Field(default_factory=dict)
    objective_score: float | None = None
    constraint_passed: bool = False
    constraint_violations: list[str] = Field(default_factory=list)
    benchmark_excess_return_pct: float | None = None
    elapsed_seconds: float = 0.0
    issues: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def summary(self) -> dict[str, Any]:
        ret = {
            "trial_id": self.trial_id,
            "params": self.params,
            "status": self.status.value,
            "objective_score": self.objective_score,
            "constraint_passed": self.constraint_passed,
            "elapsed_seconds": round(self.elapsed_seconds, 3)
        }

        if self.performance_report:
            ret["total_return"] = self.performance_report.return_metrics.total_return_pct
            ret["sharpe"] = self.performance_report.risk_adjusted_metrics.sharpe_ratio
            ret["max_drawdown"] = self.performance_report.risk_metrics.max_drawdown_pct
            ret["trade_count"] = self.performance_report.trade_metrics.trade_count
            ret["profit_factor"] = self.performance_report.trade_metrics.profit_factor

        return ret

class OptimizationResult(BaseModel):
    strategy_name: str
    symbol: str
    method: OptimizationMethod
    objective: ObjectiveMetric
    config: OptimizationConfig
    search_spaces: list[ParameterSearchSpace]
    trials: list[OptimizationTrial] = Field(default_factory=list)
    best_trial: OptimizationTrial | None = None
    top_trials: list[OptimizationTrial] = Field(default_factory=list)
    status: OptimizationStatus = OptimizationStatus.EMPTY
    total_combinations_planned: int = 0
    total_trials_run: int = 0
    failed_trials: int = 0
    elapsed_seconds: float = 0.0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime = Field(default_factory=datetime.utcnow)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Optimization research output only. Past optimized parameters do not guarantee future results. Not investment advice. No order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy_name,
            "symbol": self.symbol,
            "method": self.method.value,
            "objective": self.objective.value,
            "status": self.status.value,
            "total_trials_run": self.total_trials_run,
            "failed_trials": self.failed_trials,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "best_params": self.best_params(),
            "best_score": self.best_trial.objective_score if self.best_trial else None,
            "warnings_count": len(self.warnings),
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat()
        }

    def best_params(self) -> dict[str, Any] | None:
        return self.best_trial.params if self.best_trial else None

class WalkForwardOptimizationSplitResult(BaseModel):
    split_id: int
    train_best_trial: OptimizationTrial | None = None
    test_trial: OptimizationTrial | None = None
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    issues: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class WalkForwardOptimizationResult(BaseModel):
    strategy_name: str
    symbol: str
    config: OptimizationConfig
    split_results: list[WalkForwardOptimizationSplitResult] = Field(default_factory=list)
    aggregate_oos_score: float | None = None
    mean_oos_return_pct: float | None = None
    mean_oos_sharpe: float | None = None
    positive_oos_split_pct: float | None = None
    parameter_stability_score: float = 0.0
    overfit_warnings: list[str] = Field(default_factory=list)
    status: OptimizationStatus = OptimizationStatus.EMPTY
    elapsed_seconds: float = 0.0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime = Field(default_factory=datetime.utcnow)
    disclaimer: str = "Optimization research output only. Past optimized parameters do not guarantee future results. Not investment advice. No order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy_name,
            "symbol": self.symbol,
            "status": self.status.value,
            "splits": len(self.split_results),
            "mean_oos_return_pct": self.mean_oos_return_pct,
            "positive_oos_split_pct": self.positive_oos_split_pct,
            "parameter_stability_score": round(self.parameter_stability_score, 2),
            "overfit_warnings_count": len(self.overfit_warnings),
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat()
        }
