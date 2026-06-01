import pytest
from bist_signal_bot.app.healthcheck import append_final_handoff_health
from bist_signal_bot.config.settings import Settings

def test_healthcheck_final_handoff_enabled():
    settings = Settings(ENABLE_FINAL_HANDOFF=True)
    report = {}
    append_final_handoff_health(report, settings)
    assert "final_handoff" in report
    assert report["final_handoff"]["enabled"] is True

def test_healthcheck_final_handoff_disabled():
    settings = Settings(ENABLE_FINAL_HANDOFF=False)
    report = {}
    append_final_handoff_health(report, settings)
    assert "final_handoff" not in report
