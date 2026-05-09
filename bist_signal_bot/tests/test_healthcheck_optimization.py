import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_optimization_fields():
    settings = Settings()
    status = run_healthcheck(settings)
    assert "optimization" in status
    assert status["optimization"]["enabled"] == settings.ENABLE_OPTIMIZATION
    assert "default_method" in status["optimization"]
    assert status["optimization"]["mock_tiny_optimization_capable"] == True
