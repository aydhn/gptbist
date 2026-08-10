from bist_signal_bot.config.settings import Settings, get_settings, reload_settings

def test_settings_defaults():
    """Test that Settings loads with expected defaults."""
    settings = Settings(_env_file=None) # ignore .env file for default test
    assert settings.APP_NAME == "bist-signal-bot"
    assert settings.DRY_RUN is True
    assert settings.RUN_MODE == "research"
    assert settings.APP_ENV == "development"

def test_settings_repr_hides_secrets():
    settings = Settings(_env_file=None)
    settings.TELEGRAM_BOT_TOKEN = "123456789:ABCDefghIJKLmnopQRSTuvwxYZ"
    # Settings class doesn't override __repr__, so it will just show memory address
    repr_str = repr(settings)
    assert "123456789:ABCDefghIJKLmnopQRSTuvwxYZ" not in repr_str

def test_regime_defaults_are_typed_and_complete():
    settings = Settings(_env_file=None)

    assert settings.REGIME_SCORE_MODE == "FILTER_AND_SCORE"
    assert settings.REGIME_TREND_WINDOW == 50
    assert settings.REGIME_MIN_SCORE == 40.0
    assert settings.REGIME_USE_MTF is False
    assert "No real order sent." in settings.STRATEGY_CANDIDATE_DISCLAIMER
    assert settings.RISK_DEFAULT_EQUITY == 100_000.0
    assert settings.RISK_POSITION_SIZING_METHOD == "EQUITY_PERCENT"

def test_reload_settings(monkeypatch):
    """Test that reload_settings drops the cache and recreates the singleton."""
    original_settings = get_settings()

    monkeypatch.setenv("APP_NAME", "test-reloaded-app")

    new_settings = reload_settings()

    assert new_settings is not original_settings
    assert new_settings.APP_NAME == "test-reloaded-app"

    # Restore the singleton for other tests
    monkeypatch.undo()
    reload_settings()
