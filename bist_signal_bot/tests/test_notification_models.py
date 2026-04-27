from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from bist_signal_bot.notifications.models import (
    NotificationLevel,
    NotificationMessage,
    NotificationType,
)


def test_notification_message_title_empty_raises_error():
    with pytest.raises(ValidationError):
        NotificationMessage(
            notification_type=NotificationType.SYSTEM,
            level=NotificationLevel.INFO,
            title="",
            body="Test body"
        )


def test_notification_message_normalizes_symbol():
    msg = NotificationMessage(
        notification_type=NotificationType.SYSTEM,
        level=NotificationLevel.INFO,
        title="Test",
        body="Test body",
        symbol=" asels "
    )
    assert msg.symbol == "ASELS"


def test_notification_message_defaults():
    msg = NotificationMessage(
        notification_type=NotificationType.SYSTEM,
        level=NotificationLevel.INFO,
        title="Test",
        body="Test body"
    )
    assert msg.symbol is None
    assert isinstance(msg.timestamp, datetime)
    assert msg.metadata == {}
    assert msg.dedup_key is None
