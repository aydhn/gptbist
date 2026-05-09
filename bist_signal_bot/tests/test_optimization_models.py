import pytest
from bist_signal_bot.optimization.models import (
    ParameterSearchSpace, ParameterType, OptimizationConstraints, OptimizationConfig
)
from bist_signal_bot.core.exceptions import OptimizationValidationError

def test_parameter_search_space_values_validation():
    # Empty values should fail
    with pytest.raises(OptimizationValidationError):
        ParameterSearchSpace(name="test", param_type=ParameterType.INT, values=[])

    # Invalid bool values
    with pytest.raises(OptimizationValidationError):
        ParameterSearchSpace(name="test", param_type=ParameterType.BOOL, values=[True, 1])

def test_parameter_search_space_range_validation():
    # min > max
    with pytest.raises(OptimizationValidationError):
        ParameterSearchSpace(name="test", param_type=ParameterType.INT, min_value=10, max_value=5, step=1)

    # step <= 0
    with pytest.raises(OptimizationValidationError):
        ParameterSearchSpace(name="test", param_type=ParameterType.INT, min_value=1, max_value=5, step=-1)

def test_optimization_config_validation():
    with pytest.raises(OptimizationValidationError):
        OptimizationConfig(max_combinations=0)

    with pytest.raises(OptimizationValidationError):
        OptimizationConfig(train_window_rows=-10)

def test_optimization_constraints_validation():
    with pytest.raises(OptimizationValidationError):
        OptimizationConstraints(min_trades=-5)

    with pytest.raises(OptimizationValidationError):
        OptimizationConstraints(max_drawdown_pct=-10.0)
