import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest

def test_healthcheck_execution_sim_components():
    from bist_signal_bot.app.healthcheck import SystemHealthcheck
    checker = SystemHealthcheck()
    res = checker.check_execution_sim()
    assert res["status"] in ["healthy", "disabled"]
    if res["status"] == "healthy":
        assert "cost_model" in res["components"]
