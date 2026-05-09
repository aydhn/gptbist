import pytest
import pandas as pd

from bist_signal_bot.optimization.random_search import RandomSearchOptimizer
from bist_signal_bot.optimization.models import (
    OptimizationConfig, ParameterSearchSpace, ParameterType, OptimizationMethod, ObjectiveMetric
)
from bist_signal_bot.tests.test_grid_search_optimizer import MockBacktestEngine, MockPerformanceAnalyzer
from bist_signal_bot.optimization.objectives import ObjectiveScorer
from bist_signal_bot.config.settings import Settings

def test_random_search_runs_limited_combinations():
    be = MockBacktestEngine()
    pa = MockPerformanceAnalyzer()
    os = ObjectiveScorer()
    optimizer = RandomSearchOptimizer(backtest_engine=be, performance_analyzer=pa, objective_scorer=os, settings=Settings())

    df = pd.DataFrame()
    spaces = [
        ParameterSearchSpace(name="val", param_type=ParameterType.INT, min_value=1, max_value=100, step=1)
    ]
    # Search space size is 100, we limit to 5
    config = OptimizationConfig(
        method=OptimizationMethod.RANDOM_SEARCH,
        objective=ObjectiveMetric.TOTAL_RETURN,
        max_combinations=5,
        random_seed=42
    )

    res = optimizer.optimize("mock_strat", "MOCK", df, spaces, config)

    assert res.total_combinations_planned == 5
    assert res.total_trials_run == 5
    assert res.best_trial is not None

def test_random_search_deterministic():
    be = MockBacktestEngine()
    pa = MockPerformanceAnalyzer()
    os = ObjectiveScorer()
    optimizer = RandomSearchOptimizer(backtest_engine=be, performance_analyzer=pa, objective_scorer=os, settings=Settings())

    df = pd.DataFrame()
    spaces = [
        ParameterSearchSpace(name="val", param_type=ParameterType.INT, min_value=1, max_value=100, step=1)
    ]
    config = OptimizationConfig(
        method=OptimizationMethod.RANDOM_SEARCH,
        objective=ObjectiveMetric.TOTAL_RETURN,
        max_combinations=5,
        random_seed=42
    )

    res1 = optimizer.optimize("mock_strat", "MOCK", df, spaces, config)
    res2 = optimizer.optimize("mock_strat", "MOCK", df, spaces, config)

    trials1_params = [t.params for t in res1.trials]
    trials2_params = [t.params for t in res2.trials]

    assert trials1_params == trials2_params
