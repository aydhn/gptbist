import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_contains_cleaning():
    res = run_healthcheck()
    assert "cleaning" in res
    assert "enabled" in res["cleaning"]
    assert "missing_value_policy" in res["cleaning"]
    assert res["cleaning"]["cleaner_instantiable"] is True
