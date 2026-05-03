from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.app.bootstrap import bootstrap_app

def test_healthcheck_contains_multi_timeframe():

    summary = run_healthcheck()

    assert "multi_timeframe" in summary
    assert "enabled" in summary["multi_timeframe"]
    assert "feature_level" in summary["multi_timeframe"]
    assert "base_timeframe" in summary["multi_timeframe"]
