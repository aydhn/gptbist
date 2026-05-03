import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_strategies():
    summary = run_healthcheck()
    assert "strategy_engine" in summary
    assert "enabled" in summary["strategy_engine"]
