import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.maintenance.doctor import run_doctor

def test_healthcheck_performance_flag():
    res = run_healthcheck(performance=True)
    assert "performance" in res
    assert "performance_enabled" in res["performance"]

def test_doctor_performance_flag():
    res = run_doctor(performance=True)
    assert "performance" in res
    assert "stale_cache" in res["performance"]

