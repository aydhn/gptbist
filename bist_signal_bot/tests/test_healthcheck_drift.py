import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_drift():
    s = Settings()
    s.ENABLE_DRIFT_MONITORING = True
    res = run_healthcheck(s)
    assert res["drift_monitoring"]["enabled"] is True
    assert res["drift_monitoring"]["engine_importable"] is True

    s.ENABLE_DRIFT_MONITORING = False
    res2 = run_healthcheck(s)
    assert res2["drift_monitoring"]["enabled"] is False
