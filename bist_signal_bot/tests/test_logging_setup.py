import pytest
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.logging_setup import (
    setup_logging,
    get_logger,
    mask_sensitive_value,
    sanitize_for_logging
)

def test_mask_sensitive_value():
    assert mask_sensitive_value("123") == "***"
    assert mask_sensitive_value("12345678") == "***"
    assert mask_sensitive_value("123456789") == "1234...6789"
    assert mask_sensitive_value("some-long-token-value") == "some...alue"
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
    assert sanitized["api_key"] == "secr...7890"
    assert sanitized["nested"]["token"] == "my-s...oken"
    assert sanitized["nested"]["other"] == 123
    assert sanitized["list"][0]["password"] == "mypa...d123"
    assert sanitized["list"][1] == "plain_text"

def test_sanitize_for_logging_disabled():
    data = {"token": "secret1234567890"}
    assert sanitize_for_logging(data, mask_secrets=False)["token"] == "secret1234567890"

def test_setup_logging(tmp_path):
    settings = Settings(LOG_DIR=str(tmp_path), LOG_TO_FILE=True, LOG_LEVEL="DEBUG")
    logger = setup_logging(settings)

    assert logger.name == "bist_signal_bot"
    assert logger.level == 10  # DEBUG
    assert len(logger.handlers) == 2  # Stream and File

    # Check if duplicate handlers are avoided
    logger2 = setup_logging(settings)
    assert len(logger2.handlers) == 2

def test_get_logger():
    logger = get_logger("my_module")
    assert logger.name == "bist_signal_bot.my_module"

    logger2 = get_logger("bist_signal_bot.other_module")
    assert logger2.name == "bist_signal_bot.other_module"
