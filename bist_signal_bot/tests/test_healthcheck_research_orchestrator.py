import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_orchestrator():
    settings = Settings()
    res = run_healthcheck(settings, as_json=False)
    assert "research_orchestrator" in res
    assert res["research_orchestrator"]["enabled"] is True
    assert res["research_orchestrator"]["dag_capable"] is True
