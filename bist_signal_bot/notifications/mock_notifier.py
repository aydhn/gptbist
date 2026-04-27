from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.notifications.formatter import NotificationFormatter
from bist_signal_bot.notifications.models import (
    NotificationLevel,
    NotificationMessage,
    NotificationType,
    TelegramSendResult,
)


class MockNotifier:
    def __init__(self, formatter: NotificationFormatter | None = None):
        self.formatter = formatter or NotificationFormatter()
        self.messages: list[NotificationMessage] = []
        self.sent_texts: list[str] = []

    def clear(self) -> None:
        self.messages.clear()
        self.sent_texts.clear()

    def send(self, message: NotificationMessage) -> TelegramSendResult:
        self.messages.append(message)
        formatted_text = self.formatter.format_message(message)
        parts = self.formatter.split_message(formatted_text)
        self.sent_texts.extend(parts)

        return TelegramSendResult(
            success=True,
            message_id=len(self.sent_texts),
            sent_at=datetime.now(timezone.utc),
            dry_run=True
        )

    def send_text(
        self,
        title: str,
        body: str,
        level: NotificationLevel = NotificationLevel.INFO,
        notification_type: NotificationType = NotificationType.SYSTEM
    ) -> TelegramSendResult:
        msg = NotificationMessage(
            title=title,
            body=body,
            level=level,
            notification_type=notification_type
        )
        return self.send(msg)

    def send_healthcheck(self, summary: dict[str, Any]) -> TelegramSendResult:
        body = self.formatter.format_healthcheck(summary)
        msg = NotificationMessage(
            title="Healthcheck Raporu",
            body=body,
            level=NotificationLevel.INFO,
            notification_type=NotificationType.HEALTHCHECK
        )
        return self.send(msg)

    def send_error(self, error: Exception, context: dict[str, Any] | None = None) -> TelegramSendResult:
        body = self.formatter.format_error(error, context)
        dedup_key = type(error).__name__
        msg = NotificationMessage(
            title="Sistem Hatası",
            body=body,
            level=NotificationLevel.ERROR,
            notification_type=NotificationType.ERROR,
            dedup_key=dedup_key
        )
        return self.send(msg)
