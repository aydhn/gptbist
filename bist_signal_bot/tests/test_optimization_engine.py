import pytest
import pandas as pd

from bist_signal_bot.optimization.engine import OptimizationEngine
from bist_signal_bot.optimization.models import (
    OptimizationConfig, OptimizationMethod, ParameterSearchSpace, ParameterType
)
from bist_signal_bot.tests.test_grid_search_optimizer import MockBacktestEngine
from bist_signal_bot.config.settings import Settings

def test_optimization_engine_default_config():
    engine = OptimizationEngine(backtest_engine=MockBacktestEngine(), settings=Settings())
    config = engine.build_default_config()

    assert config.method == OptimizationMethod.GRID_SEARCH
    assert config.max_combinations == 100

def test_optimization_engine_parse_cli_spaces():
    engine = OptimizationEngine(backtest_engine=MockBacktestEngine(), settings=Settings())

    # Custom
    res1 = engine.parse_cli_search_spaces(["a=1,2", "b=10:20:5"], "test")
    assert len(res1) == 2
    assert res1[0].name == "a"
    assert res1[1].name == "b"

    # Default
    res2 = engine.parse_cli_search_spaces(None, "moving_average_trend")
    assert len(res2) > 0
