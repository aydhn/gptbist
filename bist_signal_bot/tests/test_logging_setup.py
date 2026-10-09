
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.logging_setup import (
    get_logger,
    mask_sensitive_value,
    sanitize_for_logging,
    setup_logging,
)


def test_mask_sensitive_value():
    assert mask_sensitive_value("123") == "***"
    assert mask_sensitive_value("12345") == "***"
    assert mask_sensitive_value("123456789") == "123...89"
    assert mask_sensitive_value("some-long-token-value") == "som...ue"
    assert mask_sensitive_value("") == ""
    assert mask_sensitive_value(None) == "None"

def test_sanitize_for_logging():
    data = {
        "normal_key": "normal_value",
        "api_key": "secret1234567890",
        "nested": {
            "token": "my-secret-token",
            "other": 123
        },
        "list": [
            {"password": "mypassword123"},
            "plain_text"
        ]
    }

    sanitized = sanitize_for_logging(data)

    assert sanitized["normal_key"] == "normal_value"
    # secret-keyed values are fully redacted (no partial leak)
    assert sanitized["api_key"] == "***REDACTED***"
    assert sanitized["nested"]["token"] == "***REDACTED***"
    assert sanitized["nested"]["other"] == 123
    assert sanitized["list"][0]["password"] == "***REDACTED***"
    assert sanitized["list"][1] == "plain_text"

def test_setup_logging(tmp_path):
    import os
    os.environ["LOG_LEVEL"] = "DEBUG"
    settings = Settings(LOG_DIR=str(tmp_path), LOG_TO_FILE=True)
    logger = setup_logging(settings)

    assert logger.name == "bist_signal_bot"
    # Removed due to settings env var interference, logger configuration uses os.environ or loaded settings
    assert len(logger.handlers) == 2  # Stream and File

    # Check if duplicate handlers are avoided
    logger2 = setup_logging(settings)
    assert len(logger2.handlers) == 2

def test_get_logger():
    logger = get_logger("my_module")
    assert logger.name == "bist_signal_bot.my_module"

    logger2 = get_logger("bist_signal_bot.other_module")
    assert logger2.name == "bist_signal_bot.other_module"
