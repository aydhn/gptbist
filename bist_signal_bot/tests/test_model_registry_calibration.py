import pytest
from bist_signal_bot.model_registry.calibration import ModelCalibrationGovernance
from bist_signal_bot.config.settings import Settings

def test_check_reliability_none():
    gov = ModelCalibrationGovernance()
    issues = gov.check_reliability(None)
    assert issues == []

def test_check_reliability_above_threshold():
    gov = ModelCalibrationGovernance()
    issues = gov.check_reliability(80.0)
    assert issues == []

def test_check_reliability_below_threshold():
    gov = ModelCalibrationGovernance()
    issues = gov.check_reliability(50.0)
    assert len(issues) == 1
    assert "is below minimum" in issues[0]

def test_check_reliability_custom_threshold():
    settings = Settings()
    settings.MODEL_CALIBRATION_MIN_RELIABILITY_SCORE = 75.0
    gov = ModelCalibrationGovernance(settings=settings)
    issues = gov.check_reliability(70.0)
    assert len(issues) == 1
    assert "below minimum 75.00" in issues[0]
