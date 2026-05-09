import logging
import pandas as pd
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.backtesting.engine import BacktestEngine
from bist_signal_bot.backtesting.performance import BacktestPerformanceAnalyzer
from bist_signal_bot.optimization.models import (
    OptimizationConfig, OptimizationResult, WalkForwardOptimizationResult,
    ParameterSearchSpace, OptimizationMethod, ObjectiveMetric
)
from bist_signal_bot.optimization.grid_search import GridSearchOptimizer
from bist_signal_bot.optimization.random_search import RandomSearchOptimizer
from bist_signal_bot.optimization.walk_forward_optimizer import WalkForwardOptimizer
from bist_signal_bot.optimization.objectives import ObjectiveScorer
from bist_signal_bot.optimization.search_space import SearchSpaceBuilder
from bist_signal_bot.core.exceptions import OptimizationError

class OptimizationEngine:
    def __init__(
        self,
        backtest_engine: BacktestEngine,
        performance_analyzer: BacktestPerformanceAnalyzer | None = None,
        objective_scorer: ObjectiveScorer | None = None,
        settings: Settings | None = None,
        logger: logging.Logger | None = None
    ):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger("bist_signal_bot.optimization.engine")
        self.backtest_engine = backtest_engine
        self.performance_analyzer = performance_analyzer or BacktestPerformanceAnalyzer(settings=self.settings)
        self.objective_scorer = objective_scorer or ObjectiveScorer(settings=self.settings)

    def optimize(
        self,
        strategy_name: str,
        symbol: str,
        data: pd.DataFrame,
        search_spaces: list[ParameterSearchSpace] | None = None,
        config: OptimizationConfig | None = None
    ) -> OptimizationResult | WalkForwardOptimizationResult:

        if search_spaces is None or len(search_spaces) == 0:
             search_spaces = SearchSpaceBuilder.default_search_space_for_strategy(strategy_name)
             if not search_spaces:
                 raise OptimizationError(f"No search space provided and no defaults found for strategy: {strategy_name}")

        config = config or self.build_default_config()

        self.logger.info(f"Starting {config.method.value} optimization for {strategy_name} on {symbol}")

        if config.method == OptimizationMethod.GRID_SEARCH:
             optimizer = GridSearchOptimizer(self.backtest_engine, self.performance_analyzer, self.objective_scorer, self.settings, self.logger)
             return optimizer.optimize(strategy_name, symbol, data, search_spaces, config)

        elif config.method == OptimizationMethod.RANDOM_SEARCH:
             optimizer = RandomSearchOptimizer(self.backtest_engine, self.performance_analyzer, self.objective_scorer, self.settings, self.logger)
             return optimizer.optimize(strategy_name, symbol, data, search_spaces, config)

        elif config.method in [OptimizationMethod.WALK_FORWARD_GRID, OptimizationMethod.WALK_FORWARD_RANDOM]:
             if not config.walk_forward_enabled:
                  self.logger.warning("Walk-forward method selected but walk_forward_enabled is false. Forcing to true.")
                  config.walk_forward_enabled = True

             optimizer = WalkForwardOptimizer(
                 backtest_engine=self.backtest_engine,
                 performance_analyzer=self.performance_analyzer,
                 objective_scorer=self.objective_scorer,
                 settings=self.settings,
                 logger=self.logger
             )
             return optimizer.optimize_walk_forward(strategy_name, symbol, data, search_spaces, config)

        else:
             raise OptimizationError(f"Unsupported optimization method: {config.method}")

    def build_default_config(self, method: OptimizationMethod | None = None) -> OptimizationConfig:
        method = method or OptimizationMethod(getattr(self.settings, "OPTIMIZATION_DEFAULT_METHOD", "GRID_SEARCH"))

        try:
            objective = ObjectiveMetric(getattr(self.settings, "OPTIMIZATION_DEFAULT_OBJECTIVE", "COMPOSITE"))
        except ValueError:
            objective = ObjectiveMetric.COMPOSITE

        from bist_signal_bot.optimization.models import OptimizationConstraints
        constraints = OptimizationConstraints(
            min_trades=getattr(self.settings, "OPTIMIZATION_MIN_TRADES", 3),
            max_drawdown_pct=getattr(self.settings, "OPTIMIZATION_MAX_DRAWDOWN_PCT", 40.0),
            min_profit_factor=getattr(self.settings, "OPTIMIZATION_MIN_PROFIT_FACTOR", 1.0),
            min_sharpe=getattr(self.settings, "OPTIMIZATION_MIN_SHARPE", -10.0),
            require_positive_return=getattr(self.settings, "OPTIMIZATION_REQUIRE_POSITIVE_RETURN", False),
            reject_same_close_research=getattr(self.settings, "OPTIMIZATION_REJECT_SAME_CLOSE_RESEARCH", True),
            max_cost_pct_of_profit=getattr(self.settings, "OPTIMIZATION_MAX_COST_PCT_OF_PROFIT", 50.0)
        )

        wf_enabled = getattr(self.settings, "OPTIMIZATION_WALK_FORWARD_ENABLED", False)
        if method in [OptimizationMethod.WALK_FORWARD_GRID, OptimizationMethod.WALK_FORWARD_RANDOM]:
            wf_enabled = True

        return OptimizationConfig(
            method=method,
            objective=objective,
            max_combinations=getattr(self.settings, "OPTIMIZATION_MAX_COMBINATIONS", 100),
            random_seed=getattr(self.settings, "OPTIMIZATION_RANDOM_SEED", 42),
            top_n=getattr(self.settings, "OPTIMIZATION_TOP_N", 10),
            constraints=constraints,
            walk_forward_enabled=wf_enabled,
            train_window_rows=getattr(self.settings, "OPTIMIZATION_WF_TRAIN_WINDOW_ROWS", 252),
            test_window_rows=getattr(self.settings, "OPTIMIZATION_WF_TEST_WINDOW_ROWS", 63),
            step_rows=getattr(self.settings, "OPTIMIZATION_WF_STEP_ROWS", 63),
            expanding=getattr(self.settings, "OPTIMIZATION_WF_EXPANDING", False),
            compare_benchmark=getattr(self.settings, "OPTIMIZATION_COMPARE_BENCHMARK", False),
            benchmark_name=getattr(self.settings, "OPTIMIZATION_BENCHMARK_NAME", "buy_and_hold"),
            save_report=getattr(self.settings, "OPTIMIZATION_SAVE_REPORT", False)
        )

    def parse_cli_search_spaces(self, raw_ranges: list[str] | None, strategy_name: str) -> list[ParameterSearchSpace]:
        if raw_ranges:
            return SearchSpaceBuilder.parse_param_ranges(raw_ranges)
        return SearchSpaceBuilder.default_search_space_for_strategy(strategy_name)

    def recommend_params(self, result: OptimizationResult | WalkForwardOptimizationResult) -> dict[str, Any] | None:
        if isinstance(result, OptimizationResult):
             return result.best_params()
        elif isinstance(result, WalkForwardOptimizationResult):
             # For walk-forward, picking the parameters from the last valid training split is a common approach
             if not result.split_results:
                 return None

             # Reverse iterate to find the last valid split
             for split in reversed(result.split_results):
                  if split.train_best_trial:
                       return split.train_best_trial.params
             return None
        return None
