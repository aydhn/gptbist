import pytest

from bist_signal_bot.core.exceptions import OperationalSafetyError
from bist_signal_bot.core.safety import (
    assert_no_forbidden_trading_claims,
    contains_sensitive_key,
    mask_token,
    sanitize_mapping,
    sanitize_text,
)


def test_contains_sensitive_key():
    assert contains_sensitive_key("api_key") is True
    assert contains_sensitive_key("TELEGRAM_TOKEN") is True
    assert contains_sensitive_key("chat_id") is True
    assert contains_sensitive_key("db_password") is True
    assert contains_sensitive_key("username") is False
    assert contains_sensitive_key("config_file") is False

def test_mask_token():
    assert mask_token("1234") == "***"
    assert mask_token("123456789") == "1234...6789"
    assert mask_token(None) == "None"

def test_sanitize_mapping():
    data = {
        "normal": "value",
        "my_token": "secret123456789",
        "nested": {
            "password": "pwd"
        },
        "list": [{"api_key": "abc123def456"}]
    }

    sanitized = sanitize_mapping(data)
    assert sanitized["normal"] == "value"
    assert sanitized["my_token"] == "secr...6789"
    assert sanitized["nested"]["password"] == "***"
    assert sanitized["list"][0]["api_key"] == "abc1...f456"

def test_sanitize_text():
    text1 = "Error fetching from api: token=abcdefghijklmnop"
    assert "token=ab...op" in sanitize_text(text1)

    text2 = "Using key: secret_key_123456789"
    assert "key: se...89" in sanitize_text(text2)

    text3 = "Normal error message without secrets"
    assert sanitize_text(text3) == text3

def test_assert_no_forbidden_trading_claims():
    valid_texts = [
        "Sinyal üretildi, yön yukarı olabilir.",
        "Tarihsel test sonuçlarına göre başarı oranı %60.",
        "Analiz tamamlandı."
    ]
    for text in valid_texts:
        # Should not raise
        assert_no_forbidden_trading_claims(text)

    forbidden_texts = [
        "Bu sistem ile garanti kazanç elde edeceksiniz.",
        "ASELS kesin yükselir, kaçırmayın.",
        "Tamamen risksiz getiri sağlayan bot.",
        "Bu sinyal ile kesin al yapın.",
        "Zarar etmez bir stratejidir.",
        "Yüzde yüz kazanır."
    ]

    for text in forbidden_texts:
        with pytest.raises(OperationalSafetyError):
            assert_no_forbidden_trading_claims(text)
