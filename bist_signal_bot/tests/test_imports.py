def test_core_imports():
    """Test that main modules can be imported without errors."""
    from bist_signal_bot.config.settings import settings
    from bist_signal_bot.core.exceptions import BistSignalBotError

    assert settings is not None
    assert issubclass(BistSignalBotError, Exception)
