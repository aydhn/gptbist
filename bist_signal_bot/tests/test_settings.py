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
