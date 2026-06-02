import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.local_ui.safety import LocalUISafetyGuard

def test_detect_unsafe_text():
    guard = LocalUISafetyGuard(Settings(LOCAL_UI_SAFE_LANGUAGE_REQUIRED=True))
    findings = guard.detect_unsafe_text("This signal is trade ready.")
    assert findings
    assert any("trade ready" in f for f in findings)

def test_detect_unsafe_command():
    guard = LocalUISafetyGuard(Settings(LOCAL_UI_BLOCK_UNSAFE_COMMANDS=True))
    findings = guard.detect_unsafe_command("execute --live")
    assert findings
    assert any("live" in f for f in findings)

def test_sanitize_text():
    guard = LocalUISafetyGuard(Settings(LOCAL_UI_SECRET_REDACTION_ENABLED=True))
    text = "Here is my token: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1"
    sanitized = guard.sanitize_text(text)
    assert "REDACTED_SECRET" in sanitized
    assert "a1b2c3d4" not in sanitized

def test_status_from_findings():
    guard = LocalUISafetyGuard(Settings())
    assert guard.status_from_findings([]) == "PASS"
    assert guard.status_from_findings(["Unsafe command detected"]) == "BLOCKED"
    assert guard.status_from_findings(["Unsafe text detected"]) == "WATCH"
