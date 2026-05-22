import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.telegram_center.config import TelegramCenterConfigValidator

def test_config_validator_summary():
    settings = Settings(ENABLE_TELEGRAM_CENTER=True, TELEGRAM_BOT_TOKEN="fake_token", TELEGRAM_ALLOWED_CHAT_IDS="123")
    validator = TelegramCenterConfigValidator()
    summary = validator.redacted_config_summary(settings)
    assert summary["has_token"] is True
    assert summary["has_allowlist"] is True
    assert "fake_token" not in summary.values()
