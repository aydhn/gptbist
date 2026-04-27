from bist_signal_bot.config.settings import Settings


def test_settings_defaults():
    """Test that Settings loads with expected defaults."""
    settings = Settings(_env_file=None) # ignore .env file for default test
    assert settings.APP_NAME == "BIST Signal Bot"
    assert settings.DEFAULT_MARKET == "BIST"
    assert settings.DRY_RUN is True
    assert settings.ENABLE_TELEGRAM is False
