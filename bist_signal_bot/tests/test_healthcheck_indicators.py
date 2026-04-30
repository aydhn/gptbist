import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_includes_indicators():
    hc = run_healthcheck()
    assert "indicators" in hc
    assert hc["indicators"]["enabled"] is True
    assert hc["indicators"]["backend"] == "native"
    assert "default_set" in hc["indicators"]
