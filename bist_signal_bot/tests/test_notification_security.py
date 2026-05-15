import pytest
from unittest.mock import MagicMock
from bist_signal_bot.notifications.formatter import _sanitize_output
from bist_signal_bot.config.settings import Settings

def test_formatter_sanitizes_unsafe_claims():
    text = "Bu kesin al sinyalidir."
    sanitized = _sanitize_output(text)
    assert "kesin al" not in sanitized.lower()
    assert "araştırma amaçlı alım adayı" in sanitized.lower()

def test_formatter_redacts_secrets():
    text = "Error with token 123456789:ABCDefghIJKLmnopQRSTuvwxyz123456789."
    sanitized = _sanitize_output(text)
    assert "123456789:ABCDefghIJKLmnopQRSTuvwxyz123456789" not in sanitized
    assert "***" in sanitized or "..." in sanitized
