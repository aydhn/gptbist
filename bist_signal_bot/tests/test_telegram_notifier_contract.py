from datetime import datetime, timezone

import pytest

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.notifications.models import NotificationLevel, NotificationMessage, NotificationType
from bist_signal_bot.notifications.telegram_notifier import TelegramNotifier

@pytest.fixture
def settings():
    s = Settings(
        ENABLE_TELEGRAM=True,
        TELEGRAM_BOT_TOKEN="test_token",
        TELEGRAM_CHAT_ID="test_chat_id",
        DRY_RUN=False,
        TELEGRAM_RATE_LIMIT_SECONDS=0.0,
        TELEGRAM_ERROR_COOLDOWN_SECONDS=0.0
    )
    return s

@pytest.fixture
def notifier(settings):
    return TelegramNotifier.from_settings(settings)

def test_telegram_notifier_is_configured(notifier, settings):
    assert notifier.is_configured() is True

    settings.TELEGRAM_BOT_TOKEN = ""
    assert notifier.is_configured() is False

def test_telegram_notifier_dry_run(settings, monkeypatch):
    settings.DRY_RUN = True
    notifier = TelegramNotifier.from_settings(settings)

    sent_texts = []
    def mock_send_raw(self, text):
        sent_texts.append(text)
        from bist_signal_bot.notifications.models import TelegramSendResult
        return TelegramSendResult(success=True, dry_run=True, sent_at=datetime.now(timezone.utc))

    monkeypatch.setattr(TelegramNotifier, "_send_raw_text", mock_send_raw)

    msg = NotificationMessage(
        title="Test",
        body="Body",
        level=NotificationLevel.INFO,
        notification_type=NotificationType.SYSTEM
    )
    res = notifier.send(msg)

    assert res.success is True
    assert res.dry_run is True
    assert len(sent_texts) == 0

def test_telegram_notifier_sends_actual_text_when_not_dry_run(notifier, monkeypatch):
    sent_texts = []
    def mock_send_raw(self, text):
        from bist_signal_bot.notifications.models import TelegramSendResult
        sent_texts.append(text)
        return TelegramSendResult(success=True, message_id="123", dry_run=False, sent_at=datetime.now(timezone.utc))

    monkeypatch.setattr(TelegramNotifier, "_send_raw_text", mock_send_raw)

    msg = NotificationMessage(
        title="Test",
        body="Body",
        level=NotificationLevel.INFO,
        notification_type=NotificationType.SYSTEM
    )
    res = notifier.send(msg)

    assert res.success is True
    assert res.dry_run is False
    assert len(sent_texts) == 1
    assert "Test" in sent_texts[0]

def test_telegram_notifier_handles_network_error(notifier, monkeypatch):
    def mock_send_raw(self, text):
        raise ValueError("Network error")

    monkeypatch.setattr(TelegramNotifier, "_send_raw_text", mock_send_raw)

    msg = NotificationMessage(
        title="Test",
        body="Body",
        level=NotificationLevel.INFO,
        notification_type=NotificationType.SYSTEM
    )
    res = notifier.send(msg)

    assert res.success is False
    assert "Network error" in res.error

def test_telegram_notifier_send_healthcheck_uses_formatter(notifier, monkeypatch):
    sent_texts = []
    def mock_send_raw(self, text):
        from bist_signal_bot.notifications.models import TelegramSendResult
        sent_texts.append(text)
        return TelegramSendResult(success=True)

    monkeypatch.setattr(TelegramNotifier, "_send_raw_text", mock_send_raw)

    res = notifier.send_healthcheck({"app_name": "Test App"})
    assert res.success is True
    assert len(sent_texts) == 1
    assert "Healthcheck Raporu" in sent_texts[0]
    assert "Test App" in sent_texts[0]

def test_telegram_notifier_send_error_hides_secrets(notifier, monkeypatch):
    sent_texts = []
    def mock_send_raw(self, text):
        from bist_signal_bot.notifications.models import TelegramSendResult
        sent_texts.append(text)
        return TelegramSendResult(success=True)

    monkeypatch.setattr(TelegramNotifier, "_send_raw_text", mock_send_raw)

    res = notifier.send_error(ValueError("Ouch"))
    assert res.success is True
    assert len(sent_texts) == 1
    assert "ValueError" in sent_texts[0]
