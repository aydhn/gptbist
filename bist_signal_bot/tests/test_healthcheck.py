import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_returns_dict():
    """Test that the healthcheck returns a dictionary with expected keys."""
    health_status = run_healthcheck()
    assert isinstance(health_status, dict)
    assert "status" in health_status
