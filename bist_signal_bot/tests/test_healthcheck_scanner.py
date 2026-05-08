import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_scanner():
    summary = run_healthcheck()
    assert "scanner" in summary
    assert "enabled" in summary["scanner"]
