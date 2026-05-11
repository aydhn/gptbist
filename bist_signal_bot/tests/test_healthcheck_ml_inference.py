from bist_signal_bot.app.healthcheck import run_healthcheck
import pytest

def test_healthcheck_includes_ml_inference():
    res = run_healthcheck()
    assert "ml_inference" in res
    assert "enabled" in res["ml_inference"] or "status" in res["ml_inference"] # Can be unhealthy if no model ID default
