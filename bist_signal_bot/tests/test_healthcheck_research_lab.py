import pytest
from bist_signal_bot.app.healthcheck import HealthChecker
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_research_lab():
    s = Settings(ENABLE_RESEARCH_LAB=True)
    hc = HealthChecker(s)
    res = hc.run()
    assert "research_lab" in res["components"]
    assert res["components"]["research_lab"] == "OK"
