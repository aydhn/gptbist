import pytest
from bist_signal_bot.validation.parameter_stability import ParameterStabilityAnalyzer

def test_parameter_variance():
    analyzer = ParameterStabilityAnalyzer()
    params = [
        {"window": 10, "threshold": 0.5},
        {"window": 12, "threshold": 0.5},
        {"window": 11, "threshold": 0.6}
    ]
    var = analyzer.parameter_variance(params)
    assert "window" in var
    assert "threshold" in var
    assert var["window"] > 0

def test_parameter_variance_empty():
    analyzer = ParameterStabilityAnalyzer()
    var = analyzer.parameter_variance([])
    assert len(var) == 0
