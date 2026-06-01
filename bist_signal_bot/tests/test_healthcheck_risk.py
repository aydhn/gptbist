import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_risk_engine():
    settings = Settings()
    settings.ENABLE_RISK_ENGINE = True

    status = run_healthcheck()

    assert "risk_engine" in status
    risk_info = status["risk_engine"]
    assert risk_info["enabled"] is True
    assert "default_equity" in risk_info
    assert risk_info["risk_engine_instantiable"] is True
    assert risk_info["mock_risk_decision_capable"] is True
