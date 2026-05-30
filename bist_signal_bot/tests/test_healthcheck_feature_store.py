def test_healthcheck_feature_store():
    from bist_signal_bot.app.healthcheck import run_healthcheck
    from bist_signal_bot.config.settings import Settings
    res = run_healthcheck(Settings())
    assert "feature_store" in res
    assert res["feature_store"]["enabled"] is True
