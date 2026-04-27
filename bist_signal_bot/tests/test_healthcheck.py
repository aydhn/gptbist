from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_returns_dict():
    """Test that the healthcheck returns a dictionary with expected keys."""
    health_status = run_healthcheck()
    assert isinstance(health_status, dict)
    assert "app_name" in health_status
    assert "environment" in health_status
    assert "directories" in health_status
