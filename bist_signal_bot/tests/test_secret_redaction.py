from bist_signal_bot.security.redaction import SecretRedactor
from bist_signal_bot.security.secrets import SecretHygieneScanner
from bist_signal_bot.core.exceptions import SecretLeakError
import pytest

def test_secret_redactor_masks_token():
    text = "Here is my token: 123456789:ABCDefghIJKLmnopQRSTuvwxyz123456789."
    redacted = SecretRedactor.redact_text(text)
    assert "123456789:ABCDefghIJKLmnopQRSTuvwxyz123456789" not in redacted
    assert "***" in redacted or "123..." in redacted or "mask" in redacted

def test_secret_redactor_does_not_mask_normal_symbols():
    text = "We are trading ASELS and THYAO today."
    redacted = SecretRedactor.redact_text(text)
    assert "ASELS" in redacted
    assert "THYAO" in redacted

def test_secret_redactor_nested_dict():
    data = {
        "normal": "value",
        "api_key": "mysecretkey",
        "nested": {
            "password": "mypassword123",
            "bot_token": "123456789:ABCDefghIJKLmnopQRSTuvwxyz123456789"
        },
        "lst": [
            "123456789:ABCDefghIJKLmnopQRSTuvwxyz123456789",
            {"chat_id": "1234567"}
        ]
    }
    redacted = SecretRedactor.redact_dict(data)
    assert redacted["normal"] == "value"
    assert redacted["api_key"] != "mysecretkey"
    assert "123456789:ABCDefghIJKLmnopQRSTuvwxyz123456789" not in str(redacted)
    assert redacted["nested"]["password"] != "mypassword123"
    assert redacted["lst"][1]["chat_id"] != "1234567"

def test_contains_secret_finds_token_like_string():
    data = {"nested": ["123456789:ABCDefghIJKLmnopQRSTuvwxyz123456789"]}
    assert SecretRedactor.contains_secret(data) is True

    data_safe = {"nested": ["ASELS", "12345"]}
    assert SecretRedactor.contains_secret(data_safe) is False

def test_validate_no_secret_leak_raises_error():
    payload = {"bot_token": "123456789:ABCDefghIJKLmnopQRSTuvwxyz123456789"}
    with pytest.raises(SecretLeakError):
        SecretHygieneScanner.validate_no_secret_leak(payload, "test")

def test_validate_no_secret_leak_passes_safe_payload():
    payload = {"symbol": "ASELS", "score": 85.5}
    SecretHygieneScanner.validate_no_secret_leak(payload, "test") # Should not raise
