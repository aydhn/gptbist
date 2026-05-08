import pytest
from pydantic import BaseModel

from bist_signal_bot.config.secrets import (
    is_secret_field,
    mask_secret,
    sanitize_config_dict,
    settings_safe_dump,
    validate_telegram_secrets,
)
from bist_signal_bot.core.exceptions import TelegramConfigurationError


class MockSettings(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    TELEGRAM_BOT_TOKEN: str = "secret123"
    TELEGRAM_CHAT_ID: str = "12345"
    ENABLE_TELEGRAM: bool = True
    TELEGRAM_DRY_RUN: bool = False

def test_is_secret_field():
    assert is_secret_field("token") is True
    assert is_secret_field("TELEGRAM_BOT_TOKEN") is True
    assert is_secret_field("app_name") is False

def test_mask_secret():
    assert mask_secret("short") == "***"
    assert mask_secret("verylongsecretvalue") == "very...alue"

def test_sanitize_config_dict():
    data = {
        "app_name": "Test",
        "api_key": "secret12345",
        "nested": {"token": "123456789"}
    }
    sanitized = sanitize_config_dict(data)
    assert sanitized["app_name"] == "Test"
    assert sanitized["api_key"] == "secr...2345"
    assert sanitized["nested"]["token"] == "1234...6789"

def test_settings_safe_dump():
    settings = MockSettings()
    dumped = settings_safe_dump(settings)
    assert dumped["ENABLE_TELEGRAM"] is True
    assert dumped["TELEGRAM_BOT_TOKEN"] == "secr...t123"

def test_validate_telegram_secrets():
    settings = MockSettings()
    # Should pass because both are set
    validate_telegram_secrets(settings)

    settings.TELEGRAM_BOT_TOKEN = ""
    with pytest.raises(TelegramConfigurationError):
        validate_telegram_secrets(settings)
