import logging
import pandas as pd
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.backtesting.engine import BacktestEngine
from bist_signal_bot.backtesting.performance import BacktestPerformanceAnalyzer
from bist_signal_bot.optimization.models import (
    OptimizationConfig, WalkForwardOptimizationResult, WalkForwardOptimizationSplitResult,
    ParameterSearchSpace, OptimizationStatus, OptimizationMethod
)
from bist_signal_bot.optimization.grid_search import GridSearchOptimizer
from bist_signal_bot.optimization.random_search import RandomSearchOptimizer
from bist_signal_bot.optimization.objectives import ObjectiveScorer
from bist_signal_bot.validation.splits import TimeSeriesSplitGenerator
from bist_signal_bot.core.exceptions import WalkForwardOptimizationError

class WalkForwardOptimizer:
    def __init__(
        self,
        grid_optimizer: GridSearchOptimizer | None = None,
        random_optimizer: RandomSearchOptimizer | None = None,
        backtest_engine: BacktestEngine | None = None,
        performance_analyzer: BacktestPerformanceAnalyzer | None = None,
        split_generator: TimeSeriesSplitGenerator | None = None,
        objective_scorer: ObjectiveScorer | None = None,
        settings: Settings | None = None,
        logger: logging.Logger | None = None
    ):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger("bist_signal_bot.optimization.walk_forward")

        # Instantiate dependencies if not provided
        if not backtest_engine or not performance_analyzer or not objective_scorer:
             from bist_signal_bot.costs.engine import TransactionCostEngine
             from bist_signal_bot.strategies.engine import StrategyEngine
             ce = TransactionCostEngine.from_settings(settings=self.settings)
             se = StrategyEngine(settings=self.settings)
             self.backtest_engine = backtest_engine or BacktestEngine(strategy_engine=se, cost_engine=ce, settings=self.settings)
             self.performance_analyzer = performance_analyzer or BacktestPerformanceAnalyzer(settings=self.settings)
             self.objective_scorer = objective_scorer or ObjectiveScorer(settings=self.settings)
        else:
             self.backtest_engine = backtest_engine
             self.performance_analyzer = performance_analyzer
             self.objective_scorer = objective_scorer

        self.grid_optimizer = grid_optimizer or GridSearchOptimizer(
            self.backtest_engine, self.performance_analyzer, self.objective_scorer, self.settings, self.logger
        )
        self.random_optimizer = random_optimizer or RandomSearchOptimizer(
            self.backtest_engine, self.performance_analyzer, self.objective_scorer, self.settings, self.logger
        )
        self.split_generator = split_generator or TimeSeriesSplitGenerator()

    def optimize_walk_forward(self, strategy_name: str, symbol: str, data: pd.DataFrame, search_spaces: list[ParameterSearchSpace], config: OptimizationConfig) -> WalkForwardOptimizationResult:
        started_at = datetime.now(timezone.utc)

        if config.train_window_rows is None or config.test_window_rows is None or config.step_rows is None:
             raise WalkForwardOptimizationError("Train, test, and step window rows must be specified for walk-forward optimization.")

        try:
            max_splits = getattr(self.settings, "OPTIMIZATION_WF_MAX_SPLITS", None)
            splits = self.split_generator.walk_forward_splits(
                data=data,
                train_window_rows=config.train_window_rows,
                test_window_rows=config.test_window_rows,
                step_rows=config.step_rows,
                expanding=config.expanding,
                max_splits=max_splits
            )
        except Exception as e:
            raise WalkForwardOptimizationError(f"Failed to generate splits: {e}")

        self.logger.info(f"Starting walk-forward for {strategy_name} on {symbol} with {len(splits)} splits.")

        split_results = []
        status = OptimizationStatus.SUCCESS

        for split in splits:
             train_data, test_data = self.split_generator.slice_split_data(data, split)

             # Sub-optimize on train
             if config.method == OptimizationMethod.WALK_FORWARD_RANDOM:
                 sub_res = self.random_optimizer.optimize(strategy_name, symbol, train_data, search_spaces, config)
             else:
                 sub_res = self.grid_optimizer.optimize(strategy_name, symbol, train_data, search_spaces, config)

             train_best = sub_res.best_trial

             if not train_best:
                 self.logger.warning(f"Split {split.split_id}: No valid parameters found in training.")
                 split_results.append(WalkForwardOptimizationSplitResult(
                     split_id=split.split_id,
                     train_start=split.train_start, train_end=split.train_end,
                     test_start=split.test_start, test_end=split.test_end,
                     issues=["No valid parameters found during training"]
                 ))
                 status = OptimizationStatus.PARTIAL_SUCCESS
                 continue

             # Test OOS
             test_trial = self.grid_optimizer.run_trial(
                 trial_id=train_best.trial_id,
                 strategy_name=strategy_name,
                 symbol=symbol,
                 data=test_data,
                 params=train_best.params,
                 config=config
             )

             split_results.append(WalkForwardOptimizationSplitResult(
                 split_id=split.split_id,
                 train_best_trial=train_best,
                 test_trial=test_trial,
                 train_start=split.train_start, train_end=split.train_end,
                 test_start=split.test_start, test_end=split.test_end
             ))

        if not split_results:
             status = OptimizationStatus.FAILED

        agg_metrics = self.aggregate_oos_results(split_results)
        stability = self.calculate_parameter_stability(split_results)
        warnings = self.build_overfit_warnings(split_results, agg_metrics, stability)

        finished_at = datetime.now(timezone.utc)
        elapsed = (finished_at - started_at).total_seconds()

        return WalkForwardOptimizationResult(
            strategy_name=strategy_name,
            symbol=symbol,
            config=config,
            split_results=split_results,
            aggregate_oos_score=agg_metrics.get("mean_oos_score"),
            mean_oos_return_pct=agg_metrics.get("mean_oos_return_pct"),
            mean_oos_sharpe=agg_metrics.get("mean_oos_sharpe"),
            positive_oos_split_pct=agg_metrics.get("positive_oos_split_pct"),
            parameter_stability_score=stability,
            overfit_warnings=warnings,
            status=status,
            elapsed_seconds=elapsed,
            started_at=started_at,
            finished_at=finished_at
        )

    def calculate_parameter_stability(self, split_results: list[WalkForwardOptimizationSplitResult]) -> float:
        valid_splits = [s for s in split_results if s.train_best_trial]
        if len(valid_splits) <= 1:
            return 100.0 # Perfectly stable if only 1 split

        param_changes = 0
        total_params = 0

        for i in range(1, len(valid_splits)):
             prev_params = valid_splits[i-1].train_best_trial.params
             curr_params = valid_splits[i].train_best_trial.params

             for k, v in curr_params.items():
                 total_params += 1
                 if prev_params.get(k) != v:
                      param_changes += 1

        if total_params == 0:
             return 100.0

        change_ratio = param_changes / total_params
        return max(0.0, min(100.0, (1.0 - change_ratio) * 100.0))

    def aggregate_oos_results(self, split_results: list[WalkForwardOptimizationSplitResult]) -> dict[str, Any]:
        valid_tests = [s.test_trial for s in split_results if s.test_trial and s.test_trial.status == OptimizationStatus.SUCCESS]

        if not valid_tests:
            return {
                "split_count": len(split_results),
                "mean_oos_return_pct": None,
                "median_oos_return_pct": None,
                "mean_oos_sharpe": None,
                "mean_oos_max_drawdown_pct": None,
                "positive_oos_split_pct": None,
                "mean_oos_score": None
            }

        returns = [t.performance_report.return_metrics.total_return_pct for t in valid_tests if t.performance_report and t.performance_report.return_metrics.total_return_pct is not None]
        sharpes = [t.performance_report.risk_adjusted_metrics.sharpe_ratio for t in valid_tests if t.performance_report and t.performance_report.risk_adjusted_metrics.sharpe_ratio is not None]
        dds = [t.performance_report.risk_metrics.max_drawdown_pct for t in valid_tests if t.performance_report and t.performance_report.risk_metrics.max_drawdown_pct is not None]
        scores = [t.objective_score for t in valid_tests if t.objective_score is not None]

        mean_ret = sum(returns) / len(returns) if returns else None

        median_ret = None
        if returns:
            s_ret = sorted(returns)
            mid = len(s_ret) // 2
            median_ret = (s_ret[mid] + s_ret[~mid]) / 2.0

        positive_count = sum(1 for r in returns if r > 0)
        positive_pct = (positive_count / len(returns)) * 100.0 if returns else None

        return {
            "split_count": len(valid_tests),
            "mean_oos_return_pct": mean_ret,
            "median_oos_return_pct": median_ret,
            "mean_oos_sharpe": sum(sharpes) / len(sharpes) if sharpes else None,
            "mean_oos_max_drawdown_pct": sum(dds) / len(dds) if dds else None,
            "positive_oos_split_pct": positive_pct,
            "mean_oos_score": sum(scores) / len(scores) if scores else None
        }

    def build_overfit_warnings(self, split_results: list[WalkForwardOptimizationSplitResult], agg_metrics: dict[str, Any], stability: float) -> list[str]:
        warnings = []

        if len(split_results) < 3:
            warnings.append(f"Only {len(split_results)} walk-forward splits. Optimization may not be robust.")

        if stability < 40.0:
            warnings.append(f"Low parameter stability ({stability:.1f}%). Strategy may be over-sensitive to specific market conditions.")

        pos_pct = agg_metrics.get("positive_oos_split_pct")
        if pos_pct is not None and pos_pct < 50.0:
             warnings.append(f"Less than half ({pos_pct:.1f}%) of out-of-sample periods were profitable.")

        mean_dd = agg_metrics.get("mean_oos_max_drawdown_pct")
        if mean_dd is not None and abs(mean_dd) > 20.0:
             warnings.append(f"High average out-of-sample drawdown ({mean_dd:.1f}%).")

        degradations = 0
        for sr in split_results:
             if sr.train_best_trial and sr.test_trial and sr.test_trial.status == OptimizationStatus.SUCCESS:
                 train_ret = sr.train_best_trial.performance_report.return_metrics.total_return_pct or 0.0
                 test_ret = sr.test_trial.performance_report.return_metrics.total_return_pct or 0.0
                 if train_ret > 0 and test_ret < 0:
                     degradations += 1

        if len(split_results) > 0 and degradations / len(split_results) > 0.5:
             warnings.append("Significant performance degradation in OOS testing. High risk of curve fitting.")

        return warnings
