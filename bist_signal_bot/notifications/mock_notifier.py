from datetime import UTC, datetime

from bist_signal_bot.notifications.formatter import NotificationFormatter
from bist_signal_bot.notifications.models import (
    NotificationMessage,
    TelegramSendResult,
)


from bist_signal_bot.notifications.base import BaseNotifier

class MockNotifier(BaseNotifier):
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
            sent_at=datetime.now(UTC),
            dry_run=True
        )

