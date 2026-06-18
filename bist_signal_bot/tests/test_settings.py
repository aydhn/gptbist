from bist_signal_bot.config.settings import Settings


def test_settings_defaults():
    """Test that Settings loads with expected defaults."""
    settings = Settings(_env_file=None) # ignore .env file for default test
    assert settings.APP_NAME == "BIST Signal Bot"
    assert settings.DEFAULT_MARKET == "BIST"
    assert settings.DRY_RUN is True
    assert settings.ENABLE_TELEGRAM is False
    assert settings.RUN_MODE == "research"
    assert settings.APP_ENV == "development"

def test_settings_repr_hides_secrets():
    settings = Settings(_env_file=None)
    settings.TELEGRAM_BOT_TOKEN = "123456789:ABCDefghIJKLmnopQRSTuvwxYZ"
    repr_str = repr(settings)
    assert "123456789:ABCDefghIJKLmnopQRSTuvwxYZ" not in repr_str
    assert "1234...wxYZ" in repr_str

def test_regime_defaults_are_typed_and_complete():
    settings = Settings(_env_file=None)

    assert settings.REGIME_SCORE_MODE == "FILTER_AND_SCORE"
    assert settings.REGIME_TREND_WINDOW == 50
    assert settings.REGIME_MIN_SCORE == 40.0
    assert settings.REGIME_USE_MTF is False
    assert "No real order sent." in settings.STRATEGY_CANDIDATE_DISCLAIMER
    assert settings.RISK_DEFAULT_EQUITY == 100_000.0
    assert settings.RISK_POSITION_SIZING_METHOD == "EQUITY_PERCENT"
