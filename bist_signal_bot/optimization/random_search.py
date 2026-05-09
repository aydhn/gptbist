import logging
import pandas as pd
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.backtesting.engine import BacktestEngine
from bist_signal_bot.backtesting.performance import BacktestPerformanceAnalyzer
from bist_signal_bot.optimization.models import (
    OptimizationConfig, OptimizationResult, OptimizationTrial,
    ParameterSearchSpace, OptimizationStatus
)
from bist_signal_bot.optimization.search_space import SearchSpaceBuilder
from bist_signal_bot.optimization.objectives import ObjectiveScorer
from bist_signal_bot.core.exceptions import OptimizationError

class RandomSearchOptimizer:
    def __init__(self, backtest_engine: BacktestEngine, performance_analyzer: BacktestPerformanceAnalyzer, objective_scorer: ObjectiveScorer, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.backtest_engine = backtest_engine
        self.performance_analyzer = performance_analyzer
        self.objective_scorer = objective_scorer
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger("bist_signal_bot.optimization.random")

    def optimize(self, strategy_name: str, symbol: str, data: pd.DataFrame, search_spaces: list[ParameterSearchSpace], config: OptimizationConfig) -> OptimizationResult:
        started_at = datetime.now(timezone.utc)

        try:
            # Random search samples up to max_combinations
            combinations = SearchSpaceBuilder.sample_space(search_spaces, n=config.max_combinations, seed=config.random_seed)
        except Exception as e:
            self.logger.error(f"Failed to sample search space: {e}")
            raise OptimizationError(f"Search space sampling failed: {e}")

        total_planned = len(combinations)
        self.logger.info(f"Starting random search for {strategy_name} on {symbol} with {total_planned} combinations (seed: {config.random_seed}).")

        trials = []
        failed_count = 0

        for idx, params in enumerate(combinations):
            trial = self.run_trial(idx + 1, strategy_name, symbol, data, params, config)
            trials.append(trial)
            if trial.status == OptimizationStatus.FAILED:
                failed_count += 1

        top_trials = self.select_top_trials(trials, config.top_n)
        best_trial = top_trials[0] if top_trials and top_trials[0].constraint_passed else None

        if not best_trial and top_trials:
            best_trial = top_trials[0]

        status = OptimizationStatus.SUCCESS
        if failed_count == total_planned:
             status = OptimizationStatus.FAILED
        elif failed_count > 0:
             status = OptimizationStatus.PARTIAL_SUCCESS

        finished_at = datetime.now(timezone.utc)
        elapsed = (finished_at - started_at).total_seconds()

        warnings = []
        if not best_trial or not best_trial.constraint_passed:
             warnings.append("No parameter combination passed all constraints.")

        return OptimizationResult(
            strategy_name=strategy_name,
            symbol=symbol,
            method=config.method,
            objective=config.objective,
            config=config,
            search_spaces=search_spaces,
            trials=trials,
            best_trial=best_trial,
            top_trials=top_trials,
            status=status,
            total_combinations_planned=total_planned,
            total_trials_run=len(trials),
            failed_trials=failed_count,
            elapsed_seconds=elapsed,
            started_at=started_at,
            finished_at=finished_at,
            warnings=warnings
        )

    def run_trial(self, trial_id: int, strategy_name: str, symbol: str, data: pd.DataFrame, params: dict[str, Any], config: OptimizationConfig) -> OptimizationTrial:
        start_time = datetime.now(timezone.utc)
        issues = []

        try:
             bt_result = self.backtest_engine.run_single_symbol(
                 strategy_name=strategy_name,
                 symbol=symbol,
                 data=data,
                 params=params
             )

             report = self.performance_analyzer.analyze(bt_result)

             score, violations = self.objective_scorer.score(
                 report=report,
                 objective=config.objective,
                 constraints=config.constraints,
                 benchmark_excess_return_pct=None
             )

             passed = len(violations) == 0
             elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

             return OptimizationTrial(
                 trial_id=trial_id,
                 params=params,
                 status=OptimizationStatus.SUCCESS,
                 performance_report=report,
                 backtest_summary=bt_result.summary(),
                 objective_score=score,
                 constraint_passed=passed,
                 constraint_violations=violations,
                 elapsed_seconds=elapsed,
                 issues=issues
             )

        except Exception as e:
             self.logger.debug(f"Trial {trial_id} failed: {e}")
             elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
             return OptimizationTrial(
                 trial_id=trial_id,
                 params=params,
                 status=OptimizationStatus.FAILED,
                 issues=[str(e)],
                 elapsed_seconds=elapsed
             )

    def select_top_trials(self, trials: list[OptimizationTrial], top_n: int) -> list[OptimizationTrial]:
        successful = [t for t in trials if t.status == OptimizationStatus.SUCCESS]
        if not successful:
            return []

        def sort_key(t: OptimizationTrial):
            return (
                t.constraint_passed,
                t.objective_score or -float('inf'),
                (t.performance_report.return_metrics.total_return_pct if t.performance_report and t.performance_report.return_metrics.total_return_pct else -float('inf')),
                -(abs(t.performance_report.risk_metrics.max_drawdown_pct) if t.performance_report and t.performance_report.risk_metrics.max_drawdown_pct else float('inf')),
                -t.trial_id
            )

        sorted_trials = sorted(successful, key=sort_key, reverse=True)
        return sorted_trials[:top_n]
