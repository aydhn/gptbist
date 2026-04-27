def test_core_imports():
    """Test that main modules can be imported without errors."""
    import bist_signal_bot
    from bist_signal_bot.config.settings import settings
    from bist_signal_bot.core.exceptions import BistSignalBotError
    from bist_signal_bot.data.base_provider import BaseDataProvider
    from bist_signal_bot.strategies.base_strategy import BaseStrategy

    assert settings is not None
    assert issubclass(BistSignalBotError, Exception)
