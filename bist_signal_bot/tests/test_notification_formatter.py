from datetime import datetime, timezone
import pytest

from bist_signal_bot.notifications.formatter import NotificationFormatter
from bist_signal_bot.notifications.models import (
    NotificationLevel,
    NotificationMessage,
    NotificationType,
)

@pytest.fixture
def formatter():
    return NotificationFormatter(parse_mode="HTML")

def test_formatter_formats_message(formatter):
    msg = NotificationMessage(
        title="Test Title",
        body="Test Body",
        level=NotificationLevel.INFO,
        notification_type=NotificationType.SYSTEM,
        timestamp=datetime(2026, 4, 25, 18, 30, tzinfo=timezone.utc),
        symbol="ASELS",
        metadata={"key": "value"}
    )
    res = formatter.format_message(msg)
    assert "<b>[INFO] Test Title</b>" in res
    assert "Sembol: ASELS" in res
    assert "Tip: SYSTEM" in res
    assert "Zaman: 2026-04-25 18:30:00 UTC" in res
    assert "Detay:" in res
    assert "Test Body" in res
    assert "Ek:" in res
    assert "key=value" in res

def test_formatter_escapes_html(formatter):
    msg = NotificationMessage(
        title="Test <Title>",
        body="Test & Body",
        level=NotificationLevel.INFO,
        notification_type=NotificationType.SYSTEM
    )
    res = formatter.format_message(msg)
    assert "<b>[INFO] Test &lt;Title&gt;</b>" in res
    assert "Test &amp; Body" in res

def test_formatter_split_message_no_split_needed(formatter):
    text = "Short text"
    parts = formatter.split_message(text, max_length=100)
    assert len(parts) == 1
    assert parts[0] == text

def test_formatter_split_message_splits_long_lines(formatter):
    text = "A" * 50 + "\n" + "B" * 50
    parts = formatter.split_message(text, max_length=40)
    assert len(parts) == 4
    assert parts[0] == "A" * 40
    assert parts[1] == "A" * 10
    assert parts[2] == "B" * 40
    assert parts[3] == "B" * 10

def test_formatter_split_message_keeps_words(formatter):
    text = "Line 1\nLine 2\nLine 3"
    parts = formatter.split_message(text, max_length=15)
    assert len(parts) == 2
    assert parts[0] == "Line 1\nLine 2"
    assert parts[1] == "Line 3"

def test_formatter_mask_secret(formatter):
    assert formatter.mask_secret("1234567890123") == "1234***0123"
    assert formatter.mask_secret("short") == "***"
    assert formatter.mask_secret("") == ""

def test_formatter_format_healthcheck(formatter):
    summary = {
        "app_name": "Test App",
        "environment": "test",
        "features": {
            "telegram_enabled": True
        }
    }
    res = formatter.format_healthcheck(summary)
    assert "<b>[INFO] Healthcheck Raporu</b>" in res
    assert "App: Test App" in res
    assert "Env: test" in res
    assert "- telegram_enabled: True" in res

def test_formatter_format_error(formatter):
    error = ValueError("Something <bad> happened")
    res = formatter.format_error(error, context={"a": 1})
    assert "<b>[ERROR] Sistem Hatası</b>" in res
    assert "Tip: ValueError" in res
    assert "Mesaj: Something &lt;bad&gt; happened" in res
    assert "Bağlam:" in res
    assert "a=1" in res
