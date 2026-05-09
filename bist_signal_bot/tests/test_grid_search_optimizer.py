import pytest
import pandas as pd
from datetime import datetime, timedelta

from bist_signal_bot.optimization.grid_search import GridSearchOptimizer
from bist_signal_bot.optimization.models import (
    OptimizationConfig, ParameterSearchSpace, ParameterType, OptimizationMethod, ObjectiveMetric
)
from bist_signal_bot.backtesting.engine import BacktestEngine
from bist_signal_bot.backtesting.performance import BacktestPerformanceAnalyzer
from bist_signal_bot.optimization.objectives import ObjectiveScorer
from bist_signal_bot.config.settings import Settings

class MockBacktestEngine:
    def run_single_symbol(self, strategy_name, symbol, data, params, config=None):
        # We don't care about the real engine here, just return something fake
        from bist_signal_bot.tests.test_objective_functions import build_mock_report
        from bist_signal_bot.backtesting.models import BacktestResult, BacktestMode, BacktestConfig, CostScenario, ExecutionPriceMode
        import pandas as pd

        cfg = BacktestConfig(
            initial_capital=100000, execution_price_mode=ExecutionPriceMode.NEXT_OPEN,
            commission_enabled=False, slippage_enabled=False, allow_short=False, max_position_size_pct=1.0,
            min_trade_notional=100, trade_on_candidate_statuses=["ACTIVE"], close_on_opposite_signal=False,
            close_on_flat_signal=False, one_position_per_symbol=False, use_fractional_shares=False,
            close_open_positions_at_end=False, scenario=CostScenario.BASE
        )

        # Make performance depend on a param
        fake_ret = float(params.get("val", 10.0))
        fake_dd = -abs(fake_ret / 2)

        res = BacktestResult(
            strategy_name=strategy_name, mode=BacktestMode.SINGLE_SYMBOL, config=cfg,
            trades=[], fills=[], portfolio_snapshots=[], orders=[],
            started_at=datetime.utcnow(), finished_at=datetime.utcnow(), elapsed_seconds=0.1,
            issues=[], symbol=symbol, metadata={"fake_ret": fake_ret, "fake_dd": fake_dd}
        )
        return res

class MockPerformanceAnalyzer:
    def analyze(self, bt_result):
        from bist_signal_bot.tests.test_objective_functions import build_mock_report
        ret = bt_result.metadata["fake_ret"]
        dd = bt_result.metadata["fake_dd"]
        return build_mock_report(ret=ret, dd=dd, trades=10)

def test_grid_search_runs_all_combinations():
    be = MockBacktestEngine()
    pa = MockPerformanceAnalyzer()
    os = ObjectiveScorer()
    optimizer = GridSearchOptimizer(backtest_engine=be, performance_analyzer=pa, objective_scorer=os, settings=Settings())

    df = pd.DataFrame()
    spaces = [
        ParameterSearchSpace(name="val", param_type=ParameterType.INT, values=[5, 10, 15])
    ]
    config = OptimizationConfig(method=OptimizationMethod.GRID_SEARCH, objective=ObjectiveMetric.TOTAL_RETURN)

    res = optimizer.optimize("mock_strat", "MOCK", df, spaces, config)

    assert res.total_combinations_planned == 3
    assert res.total_trials_run == 3
    assert res.best_trial is not None
    assert res.best_trial.params["val"] == 15
    assert res.best_trial.objective_score == 15.0

def test_grid_search_failed_trial_handling():
    class FailingBacktestEngine(MockBacktestEngine):
         def run_single_symbol(self, strategy_name, symbol, data, params, config=None):
              if params["val"] == 10:
                   raise ValueError("Simulated failure")
              return super().run_single_symbol(strategy_name, symbol, data, params, config)

    be = FailingBacktestEngine()
    pa = MockPerformanceAnalyzer()
    os = ObjectiveScorer()
    optimizer = GridSearchOptimizer(backtest_engine=be, performance_analyzer=pa, objective_scorer=os, settings=Settings())

    df = pd.DataFrame()
    spaces = [
        ParameterSearchSpace(name="val", param_type=ParameterType.INT, values=[5, 10, 15])
    ]
    config = OptimizationConfig(method=OptimizationMethod.GRID_SEARCH, objective=ObjectiveMetric.TOTAL_RETURN)

    res = optimizer.optimize("mock_strat", "MOCK", df, spaces, config)

    assert res.total_combinations_planned == 3
    assert res.total_trials_run == 3
    assert res.failed_trials == 1
    assert res.best_trial.params["val"] == 15
