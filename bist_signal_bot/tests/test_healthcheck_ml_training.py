import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_ml_training():
    res = run_healthcheck()
    assert "ml_training_enabled" in res
    assert "ml_training_estimators_capable" in res
    assert "ml_training_trainer_capable" in res
    assert "ml_training_registry_capable" in res
