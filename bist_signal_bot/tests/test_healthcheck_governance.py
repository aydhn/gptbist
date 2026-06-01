import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
from bist_signal_bot.app.healthcheck import get_health

def test_healthcheck_includes_governance():
    health = get_health()
    assert "governance_enabled" in health["details"]
    assert "governance_policy_valid" in health["details"]
