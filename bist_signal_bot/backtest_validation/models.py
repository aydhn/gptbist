from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from bist_signal_bot.backtesting.comparison import BenchmarkComparisonReport
from bist_signal_bot.backtesting.models import BacktestPerformanceReport, BacktestResult


class ValidationMode(StrEnum):
    TRAIN_TEST_SPLIT = "TRAIN_TEST_SPLIT"
    WALK_FORWARD = "WALK_FORWARD"
    EXPANDING_WINDOW = "EXPANDING_WINDOW"
    ROLLING_WINDOW = "ROLLING_WINDOW"
    ROBUSTNESS = "ROBUSTNESS"
    UNKNOWN = "UNKNOWN"


class SplitType(StrEnum):
    HOLDOUT = "HOLDOUT"
    WALK_FORWARD = "WALK_FORWARD"
    EXPANDING = "EXPANDING"
    ROLLING = "ROLLING"


class WindowMode(StrEnum):
    EXPANDING = "EXPANDING"
    ROLLING = "ROLLING"


class OverfitRiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


@dataclass
class TimeSeriesSplit:
    split_id: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    train_rows: int
    test_rows: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.train_start >= self.train_end:
            raise ValueError("train_start must be before train_end")
        if self.test_start >= self.test_end:
            raise ValueError("test_start must be before test_end")
        if self.train_rows <= 0:
            raise ValueError("train_rows must be positive")
        if self.test_rows <= 0:
            raise ValueError("test_rows must be positive")


@dataclass
class ValidationConfig:
    mode: ValidationMode = ValidationMode.WALK_FORWARD
    train_ratio: float = 0.7
    min_train_rows: int = 150
    min_test_rows: int = 50
    train_window_rows: int | None = 252
    test_window_rows: int = 63
    step_rows: int = 63
    gap_rows: int = 0
    expanding: bool = False
    max_splits: int | None = 10
    benchmark_name: str | None = "buy_and_hold"
    compare_benchmark: bool = False
    save_reports: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not 0 < self.train_ratio < 1:
            raise ValueError("train_ratio must be between 0 and 1")
        if self.min_train_rows <= 0:
            raise ValueError("min_train_rows must be positive")
        if self.min_test_rows <= 0:
            raise ValueError("min_test_rows must be positive")
        if self.test_window_rows <= 0:
            raise ValueError("test_window_rows must be positive")
        if self.step_rows <= 0:
            raise ValueError("step_rows must be positive")
        if self.gap_rows < 0:
            raise ValueError("gap_rows cannot be negative")
        if self.max_splits is not None and self.max_splits <= 0:
            raise ValueError("max_splits must be positive")


@dataclass
class SplitBacktestResult:
    split: TimeSeriesSplit
    test_result: BacktestResult
    test_report: BacktestPerformanceReport
    train_result: BacktestResult | None = None
    train_report: BacktestPerformanceReport | None = None
    benchmark_comparison: BenchmarkComparisonReport | None = None
    issues: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        res = {
            "split_id": self.split.split_id,
            "test_return_pct": self.test_report.return_metrics.total_return_pct,
            "test_sharpe": self.test_report.risk_adjusted_metrics.sharpe_ratio,
            "test_max_drawdown_pct": self.test_report.risk_metrics.max_drawdown_pct,
            "test_trades": self.test_report.trade_metrics.trade_count,
            "test_win_rate": self.test_report.trade_metrics.win_rate_pct,
        }
        if self.train_report:
            res.update(
                {
                    "train_return_pct": self.train_report.return_metrics.total_return_pct,
                    "train_sharpe": self.train_report.risk_adjusted_metrics.sharpe_ratio,
                    "train_max_drawdown_pct": self.train_report.risk_metrics.max_drawdown_pct,
                }
            )
        return res


@dataclass
class WalkForwardResult:
    strategy_name: str
    symbol: str
    config: ValidationConfig
    splits: list[TimeSeriesSplit]
    split_results: list[SplitBacktestResult]
    aggregate_report: dict[str, Any]
    overfit_risk_level: OverfitRiskLevel
    overfit_warnings: list[str]
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float
    disclaimer: str = "Walk-forward research output only. Past performance does not guarantee future results. Not investment advice. No order was sent."  # noqa: E501
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "mode": self.config.mode.value,
            "split_count": len(self.splits),
            "aggregate_report": self.aggregate_report,
            "overfit_risk_level": self.overfit_risk_level.value,
            "overfit_warnings": self.overfit_warnings,
            "disclaimer": self.disclaimer,
        }

    def test_total_returns(self) -> list[float]:
        return [r.test_report.return_metrics.total_return_pct for r in self.split_results]

    def test_sharpes(self) -> list[float]:
        return [r.test_report.risk_adjusted_metrics.sharpe_ratio for r in self.split_results]

    def positive_test_split_count(self) -> int:
        return sum(1 for r in self.test_total_returns() if r > 0)


@dataclass
class RobustnessParameterRange:
    name: str
    values: list[Any]

    def __post_init__(self):
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.values:
            raise ValueError("values cannot be empty")


@dataclass
class RobustnessRunResult:
    params: dict[str, Any]
    backtest_result: BacktestResult
    performance_report: BacktestPerformanceReport
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RobustnessResult:
    strategy_name: str
    symbol: str
    parameter_ranges: list[RobustnessParameterRange]
    run_results: list[RobustnessRunResult]
    best_params: dict[str, Any] | None
    worst_params: dict[str, Any] | None
    stability_score: float
    overfit_risk_level: OverfitRiskLevel
    warnings: list[str]
    generated_at: datetime
    elapsed_seconds: float
    disclaimer: str = "Walk-forward research output only. Past performance does not guarantee future results. Not investment advice. No order was sent."  # noqa: E501

    def summary(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "runs": len(self.run_results),
            "stability_score": self.stability_score,
            "best_params": self.best_params,
            "worst_params": self.worst_params,
            "overfit_risk_level": self.overfit_risk_level.value,
            "warnings": self.warnings,
            "disclaimer": self.disclaimer,
        }
