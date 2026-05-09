import pytest
from bist_signal_bot.optimization.reporting import (
    optimization_result_to_dict, format_optimization_markdown
)
from bist_signal_bot.optimization.models import (
    OptimizationResult, OptimizationConfig, OptimizationMethod, ObjectiveMetric, OptimizationStatus
)
from datetime import datetime

def test_optimization_result_to_dict():
    res = OptimizationResult(
        strategy_name="test", symbol="TST", method=OptimizationMethod.GRID_SEARCH,
        objective=ObjectiveMetric.TOTAL_RETURN, config=OptimizationConfig(),
        search_spaces=[], status=OptimizationStatus.SUCCESS,
        started_at=datetime.utcnow(), finished_at=datetime.utcnow()
    )
    d = optimization_result_to_dict(res)
    assert d["summary"]["strategy"] == "test"
    assert d["summary"]["status"] == "SUCCESS"

def test_format_optimization_markdown():
    res = OptimizationResult(
        strategy_name="test", symbol="TST", method=OptimizationMethod.GRID_SEARCH,
        objective=ObjectiveMetric.TOTAL_RETURN, config=OptimizationConfig(),
        search_spaces=[], status=OptimizationStatus.SUCCESS,
        started_at=datetime.utcnow(), finished_at=datetime.utcnow()
    )
    md = format_optimization_markdown(res)
    assert "# Optimization Report" in md
    assert "test on TST" in md
    assert "Disclaimer" in md
