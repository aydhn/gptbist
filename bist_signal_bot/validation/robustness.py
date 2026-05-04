import itertools
import logging
from datetime import datetime
from typing import Any

import pandas as pd

from bist_signal_bot.backtesting.engine import BacktestEngine
from bist_signal_bot.backtesting.performance import BacktestPerformanceAnalyzer
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import RobustnessAnalysisError
from bist_signal_bot.validation.models import (
    OverfitRiskLevel,
    RobustnessParameterRange,
    RobustnessResult,
    RobustnessRunResult,
)
from bist_signal_bot.validation.overfit import OverfitRiskAnalyzer


class RobustnessAnalyzer:
    def __init__(
        self,
        backtest_engine: BacktestEngine,
        performance_analyzer: BacktestPerformanceAnalyzer | None = None,
        settings: Settings | None = None,
        logger: logging.Logger | None = None,
    ):
        self.backtest_engine = backtest_engine
        self.performance_analyzer = performance_analyzer or BacktestPerformanceAnalyzer(
            settings=settings
        )
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)
        self.overfit_analyzer = OverfitRiskAnalyzer()

    def run_parameter_robustness(
        self,
        strategy_name: str,
        symbol: str,
        data: pd.DataFrame,
        base_params: dict[str, Any],
        parameter_ranges: list[RobustnessParameterRange],
        max_runs: int | None = None,
    ) -> RobustnessResult:
        started_at = datetime.now()

        param_grid = self.generate_param_grid(parameter_ranges, max_runs)
        if not param_grid:
            raise RobustnessAnalysisError("Generated parameter grid is empty")

        run_results = []

        for param_updates in param_grid:
            current_params = base_params.copy()
            current_params.update(param_updates)

            try:
                result = self.backtest_engine.run_single_symbol(
                    strategy_name=strategy_name, symbol=symbol, data=data, params=current_params
                )
                report = self.performance_analyzer.analyze(result)

                run_results.append(
                    RobustnessRunResult(
                        params=current_params, backtest_result=result, performance_report=report
                    )
                )
            except Exception as e:
                self.logger.warning(f"Robustness run failed for params {current_params}: {e}")

        if not run_results:
            raise RobustnessAnalysisError("All robustness runs failed")

        best_params, worst_params = self.find_best_worst_params(run_results)
        stability_score = self.calculate_stability_score(run_results)

        finished_at = datetime.now()
        elapsed_seconds = (finished_at - started_at).total_seconds()

        result = RobustnessResult(
            strategy_name=strategy_name,
            symbol=symbol,
            parameter_ranges=parameter_ranges,
            run_results=run_results,
            best_params=best_params,
            worst_params=worst_params,
            stability_score=stability_score,
            overfit_risk_level=OverfitRiskLevel.UNKNOWN,
            warnings=[],
            generated_at=finished_at,
            elapsed_seconds=elapsed_seconds,
        )

        risk_level, warnings = self.overfit_analyzer.assess_robustness(result)
        result.overfit_risk_level = risk_level
        result.warnings = warnings

        return result

    def generate_param_grid(
        self, parameter_ranges: list[RobustnessParameterRange], max_runs: int | None = None
    ) -> list[dict[str, Any]]:
        keys = [pr.name for pr in parameter_ranges]
        values = [pr.values for pr in parameter_ranges]

        combinations = list(itertools.product(*values))
        grid = [dict(zip(keys, combo, strict=False)) for combo in combinations]

        if max_runs is not None and len(grid) > max_runs:
            grid = grid[:max_runs]

        return grid

    def calculate_stability_score(self, run_results: list[RobustnessRunResult]) -> float:
        if not run_results:
            return 0.0

        returns = [r.performance_report.return_metrics.total_return_pct or 0.0 for r in run_results]

        positive_runs = sum(1 for r in returns if r > 0)
        positive_pct = (positive_runs / len(returns)) * 100.0

        mean_ret = sum(returns) / len(returns)
        variance = sum((x - mean_ret) ** 2 for x in returns) / len(returns)
        std_dev = variance**0.5

        score = positive_pct - (std_dev * 0.5)
        return max(0.0, min(100.0, score))

    def find_best_worst_params(
        self, run_results: list[RobustnessRunResult]
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        if not run_results:
            return None, None

        sorted_results = sorted(
            run_results, key=lambda x: x.performance_report.return_metrics.total_return_pct or 0.0
        )
        worst_params = sorted_results[0].params
        best_params = sorted_results[-1].params

        return best_params, worst_params
