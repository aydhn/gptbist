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


# --- secret hygiene: value-type awareness and source tracking (synthetic values only) ---
from bist_signal_bot.security.redaction import SecretRedactor as _SR


def test_bool_numeric_empty_flags_are_not_secrets():
    data = {
        "MASK_SECRETS_IN_LOGS": True,
        "SECURITY_FAIL_ON_SECRET_LEAK": "true",
        "TELEGRAM_HASH_CHAT_IDS_IN_LOGS": False,
        "TELEGRAM_ADMIN_CHAT_IDS": "",
        "TELEGRAM_ALLOWED_CHAT_IDS": "[]",
        "SOME_TOKEN_LIMIT": 5,
        "OTHER_SECRET": "none",
    }
    assert _SR.find_secret_like_values(data) == []


def test_filled_secret_still_found():
    assert _SR.find_secret_like_values({"EVDS_API_KEY": "synthetic" + "Key" * 6})


def test_telegram_token_pattern_still_fails():
    tok = "123456789" + ":" + "A" * 35
    assert _SR.find_secret_like_values({"note": tok})
    assert _SR.contains_secret(tok)


def _scan(tmp_path, env_text, example_text):
    from bist_signal_bot.security.secrets import SecretHygieneScanner
    env, ex = tmp_path / ".env", tmp_path / ".env.example"
    env.write_text(env_text, encoding="utf-8")
    ex.write_text(example_text, encoding="utf-8")
    return SecretHygieneScanner, env, ex


def test_secret_from_local_env_passes(tmp_path):
    S, env, ex = _scan(tmp_path, "EVDS_API_KEY=synthetic_local_key_value\n", "EVDS_API_KEY=\n")
    settings = {"EVDS_API_KEY": "synthetic_local_key_value"}
    assert S.scan_settings(settings, env_file=env, example_file=ex, environ={}) == []


def test_secret_from_os_environ_passes(tmp_path):
    S, env, ex = _scan(tmp_path, "", "FRED_API_KEY=\n")
    settings = {"FRED_API_KEY": "synthetic_env_key_value"}
    assert S.scan_settings(settings, env_file=env, example_file=ex,
                           environ={"FRED_API_KEY": "synthetic_env_key_value"}) == []


def test_secret_in_tracked_template_fails(tmp_path):
    S, env, ex = _scan(tmp_path, "", "EVDS_API_KEY=synthetic_template_key_value\n")
    settings = {"EVDS_API_KEY": "synthetic_template_key_value"}
    assert S.scan_settings(settings, env_file=env, example_file=ex, environ={})
    assert S.scan_template_file(ex, include_defaults=False)


def test_env_copy_of_template_secret_still_fails(tmp_path):
    line = "EVDS_API_KEY=synthetic_template_key_value\n"
    S, env, ex = _scan(tmp_path, line, line)
    assert S.scan_settings({"EVDS_API_KEY": "synthetic_template_key_value"},
                           env_file=env, example_file=ex, environ={})


def test_real_template_and_defaults_are_clean():
    from bist_signal_bot.security.secrets import SecretHygieneScanner
    assert SecretHygieneScanner.scan_template_file() == []


@pytest.mark.parametrize("key,value", [
    ("SOME_TOKEN", "1234567890123456789012"),
    ("SOME_API_KEY", "12345678901234567890"),
    ("SOME_TOKEN", "abc***realtail"),
    ("SOME_API_KEY", "dummyRealLookingKey9f8e7d6c"),
    ("SOME_PASSWORD", "1e5"),
    ("SOME_PASSWORD", "nan"),
    ("TELEGRAM_CHAT_ID", "555111222"),
    ("TELEGRAM_CHAT_ID", 555111222),
    ("TELEGRAM_ALLOWED_CHAT_IDS", "555111222,123456789"),
])
def test_tightened_exemptions_still_report(key, value):
    assert not SecretRedactor.is_non_secret_value(value, key)
    assert SecretRedactor.find_secret_like_values({key: value})


@pytest.mark.parametrize("key,value", [
    ("X_TOKEN", ""), ("X_TOKEN", None), ("X_TOKEN", 123456789), ("X_TOKEN", "12345"),
    ("X_API_KEY", "your_api_key_here"), ("X_API_KEY", "YOUR-API-KEY"), ("X_API_KEY", "***"),
    ("X_API_KEY", "***REDACTED***"), ("TELEGRAM_CHAT_ID", "123456789"), ("TELEGRAM_CHAT_ID", ""),
    ("TELEGRAM_ALLOWED_CHAT_IDS", "123456789,987654321"), ("X_PASSWORD", "changeme"),
])
def test_placeholders_and_short_numbers_exempt(key, value):
    assert SecretRedactor.is_non_secret_value(value, key)


def test_template_with_filled_chat_id_is_reported(tmp_path):
    ex = tmp_path / ".env.example"
    ex.write_text("TELEGRAM_CHAT_ID=555111222\n", encoding="utf-8")
    assert SecretHygieneScanner.scan_template_file(ex, include_defaults=False)
