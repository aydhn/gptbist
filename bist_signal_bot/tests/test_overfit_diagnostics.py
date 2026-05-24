import pytest
from bist_signal_bot.validation.overfit import OverfitDiagnosticsEngine
from bist_signal_bot.validation.models import ParameterStabilityResult

def test_calculate_oos_decay():
    engine = OverfitDiagnosticsEngine()
    decay = engine.calculate_oos_decay({"median_return": 10.0}, {"median_return": 5.0})
    assert decay == 50.0

def test_calculate_oos_decay_negative():
    engine = OverfitDiagnosticsEngine()
    decay = engine.calculate_oos_decay({"median_return": 10.0}, {"median_return": 15.0})
    assert decay == 0.0

def test_calculate_overfit_score():
    engine = OverfitDiagnosticsEngine()
    score = engine.calculate_overfit_score(50.0, 20.0, 20.0)
    assert score == 30.0

def test_classify_overfit():
    engine = OverfitDiagnosticsEngine()
    status, severity, actions = engine.classify_overfit(75.0)
    assert status.value == "FAIL"
    assert "AVOID_AUTO_SELECTION" in [a.value for a in actions]
