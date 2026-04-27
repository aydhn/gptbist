from datetime import datetime, timezone
import pytest

from bist_signal_bot.notifications.mock_notifier import MockNotifier
from bist_signal_bot.notifications.models import (
    NotificationLevel,
    NotificationMessage,
    NotificationType,
)

@pytest.fixture
def mock_notifier():
    return MockNotifier()

def test_mock_notifier_sends_and_stores_messages(mock_notifier):
    msg = NotificationMessage(
        title="Test Title",
        body="Test Body",
        level=NotificationLevel.INFO,
        notification_type=NotificationType.SYSTEM
    )

    result = mock_notifier.send(msg)
    assert result.success is True
    assert result.dry_run is True
    assert len(mock_notifier.messages) == 1
    assert mock_notifier.messages[0].title == "Test Title"
    assert len(mock_notifier.sent_texts) == 1
    assert "<b>[INFO] Test Title</b>" in mock_notifier.sent_texts[0]

def test_mock_notifier_send_text(mock_notifier):
    mock_notifier.send_text("Title", "Body")
    assert len(mock_notifier.messages) == 1
    assert mock_notifier.messages[0].title == "Title"

def test_mock_notifier_send_healthcheck(mock_notifier):
    mock_notifier.send_healthcheck({"app_name": "Test"})
    assert len(mock_notifier.messages) == 1
    assert mock_notifier.messages[0].notification_type == NotificationType.HEALTHCHECK

def test_mock_notifier_send_error(mock_notifier):
    mock_notifier.send_error(ValueError("Ouch"))
    assert len(mock_notifier.messages) == 1
    assert mock_notifier.messages[0].level == NotificationLevel.ERROR
    assert mock_notifier.messages[0].dedup_key == "ValueError"

def test_mock_notifier_clear(mock_notifier):
    mock_notifier.send_text("Title", "Body")
    assert len(mock_notifier.messages) == 1
    mock_notifier.clear()
    assert len(mock_notifier.messages) == 0
    assert len(mock_notifier.sent_texts) == 0
