import pytest
import pandas as pd
import numpy as np

from bist_signal_bot.optimization.walk_forward_optimizer import WalkForwardOptimizer
from bist_signal_bot.optimization.models import (
    OptimizationConfig, ParameterSearchSpace, ParameterType, OptimizationMethod, ObjectiveMetric
)
from bist_signal_bot.tests.test_grid_search_optimizer import MockBacktestEngine, MockPerformanceAnalyzer
from bist_signal_bot.optimization.objectives import ObjectiveScorer
from bist_signal_bot.config.settings import Settings

def test_walk_forward_optimizer_runs():
    be = MockBacktestEngine()
    pa = MockPerformanceAnalyzer()
    os = ObjectiveScorer()
    optimizer = WalkForwardOptimizer(backtest_engine=be, performance_analyzer=pa, objective_scorer=os, settings=Settings())

    # Create 300 days of fake data
    dates = pd.date_range(start="2020-01-01", periods=300, freq="B")
    df = pd.DataFrame({"close": np.random.randn(300).cumsum() + 100}, index=dates)

    spaces = [
        ParameterSearchSpace(name="val", param_type=ParameterType.INT, values=[5, 10])
    ]
    config = OptimizationConfig(
        method=OptimizationMethod.WALK_FORWARD_GRID,
        objective=ObjectiveMetric.TOTAL_RETURN,
        train_window_rows=100,
        test_window_rows=30,
        step_rows=30,
        walk_forward_enabled=True
    )

    res = optimizer.optimize_walk_forward("mock_strat", "MOCK", df, spaces, config)

    assert res.status.value in ["SUCCESS", "PARTIAL_SUCCESS"]
    assert len(res.split_results) > 0
    # ~ (300 - 100) / 30 = ~6 splits
    assert len(res.split_results) >= 5

    # Check OOS metrics exist
    assert res.mean_oos_return_pct is not None
    assert 0.0 <= res.parameter_stability_score <= 100.0

def test_walk_forward_optimizer_stability_score():
    optimizer = WalkForwardOptimizer()
    from bist_signal_bot.optimization.models import WalkForwardOptimizationSplitResult, OptimizationTrial, OptimizationStatus
    from datetime import datetime

    # Mock some split results with varying params
    t1 = OptimizationTrial(trial_id=1, params={"a": 1, "b": 2}, status=OptimizationStatus.SUCCESS)
    t2 = OptimizationTrial(trial_id=1, params={"a": 1, "b": 3}, status=OptimizationStatus.SUCCESS)
    t3 = OptimizationTrial(trial_id=1, params={"a": 2, "b": 3}, status=OptimizationStatus.SUCCESS)

    dt = datetime.now()
    sr1 = WalkForwardOptimizationSplitResult(split_id=1, train_best_trial=t1, train_start=dt, train_end=dt, test_start=dt, test_end=dt)
    sr2 = WalkForwardOptimizationSplitResult(split_id=2, train_best_trial=t2, train_start=dt, train_end=dt, test_start=dt, test_end=dt)
    sr3 = WalkForwardOptimizationSplitResult(split_id=3, train_best_trial=t3, train_start=dt, train_end=dt, test_start=dt, test_end=dt)

    splits = [sr1, sr2, sr3]
    score = optimizer.calculate_parameter_stability(splits)

    # 2 transitions, 2 params each = 4 total param comparisons
    # 1 -> 2: 'a' same, 'b' changed (1 change)
    # 2 -> 3: 'a' changed, 'b' same (1 change)
    # 2 changes / 4 total = 50% change ratio -> 50% stability
    assert score == 50.0
