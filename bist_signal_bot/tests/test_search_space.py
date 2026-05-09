import pytest
from bist_signal_bot.optimization.search_space import SearchSpaceBuilder
from bist_signal_bot.optimization.models import ParameterSearchSpace, ParameterType
from bist_signal_bot.core.exceptions import OptimizationValidationError, SearchSpaceError

def test_parse_param_range_int_list():
    res = SearchSpaceBuilder.parse_param_range("fast=10, 20, 30")
    assert res.name == "fast"
    assert res.param_type == ParameterType.INT
    assert res.values == [10, 20, 30]

def test_parse_param_range_float_range():
    res = SearchSpaceBuilder.parse_param_range("thresh=0.1:0.5:0.1")
    assert res.name == "thresh"
    assert res.param_type == ParameterType.FLOAT
    assert res.min_value == 0.1
    assert res.max_value == 0.5
    assert res.step == 0.1

def test_parse_param_range_bool():
    res = SearchSpaceBuilder.parse_param_range("use_trend=true, false")
    assert res.name == "use_trend"
    assert res.param_type == ParameterType.BOOL
    assert res.values == [True, False]

def test_parse_param_range_categorical():
    res = SearchSpaceBuilder.parse_param_range("mode=a,b,c")
    assert res.name == "mode"
    assert res.param_type == ParameterType.CATEGORICAL
    assert res.choices == ["a", "b", "c"]

def test_expand_space_cartesian_product():
    spaces = [
        ParameterSearchSpace(name="a", param_type=ParameterType.INT, values=[1, 2]),
        ParameterSearchSpace(name="b", param_type=ParameterType.BOOL, values=[True, False])
    ]
    res = SearchSpaceBuilder.expand_space(spaces)
    assert len(res) == 4
    assert {"a": 1, "b": True} in res
    assert {"a": 2, "b": False} in res

def test_expand_space_max_combinations():
    spaces = [
        ParameterSearchSpace(name="a", param_type=ParameterType.INT, values=[1, 2, 3]),
        ParameterSearchSpace(name="b", param_type=ParameterType.INT, values=[1, 2, 3])
    ]
    with pytest.raises(OptimizationValidationError):
        SearchSpaceBuilder.expand_space(spaces, max_combinations=5)

def test_sample_space_deterministic():
    spaces = [
        ParameterSearchSpace(name="a", param_type=ParameterType.INT, min_value=1, max_value=10, step=1),
        ParameterSearchSpace(name="b", param_type=ParameterType.INT, min_value=1, max_value=10, step=1)
    ]
    # Total combinations = 100
    res1 = SearchSpaceBuilder.sample_space(spaces, n=5, seed=42)
    res2 = SearchSpaceBuilder.sample_space(spaces, n=5, seed=42)

    assert len(res1) == 5
    assert res1 == res2

def test_default_search_space():
    space = SearchSpaceBuilder.default_search_space_for_strategy("moving_average_trend")
    assert len(space) > 0
    names = [s.name for s in space]
    assert "fast_window" in names
    assert "slow_window" in names
