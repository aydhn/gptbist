from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_includes_divergence():
    health = run_healthcheck()
    assert "divergence_engine" in health

    div_info = health["divergence_engine"]
    assert "enabled" in div_info
    assert "feature_level" in div_info
    assert "pivot_mode" in div_info
    assert "lookback" in div_info
    assert "confirmation_bars" in div_info
    assert "engine_instantiable" in div_info
    assert "mock_capable" in div_info

    # Check default values are reasonable types
    assert isinstance(div_info["enabled"], bool)
    assert isinstance(div_info["lookback"], int)
    assert isinstance(div_info["engine_instantiable"], bool)
