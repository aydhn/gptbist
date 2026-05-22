from bist_signal_bot.telegram_center.models import NotificationMessage, NotificationStatus, NotificationPriority
from bist_signal_bot.telegram_center.storage import TelegramCenterStore
from bist_signal_bot.config.settings import Settings

class NotificationInboxManager:
    def __init__(self, store: TelegramCenterStore, settings: Settings):
        self.store = store
        self.settings = settings

    def add_message(self, message: NotificationMessage) -> NotificationMessage:
        self.store.append_notification(message)
        return message

    def list_messages(self, status: NotificationStatus | None = None, priority: NotificationPriority | None = None, limit: int = 100) -> list[NotificationMessage]:
        return self.store.load_notifications(status=status, limit=limit)

    def mark_sent(self, notification_id: str) -> NotificationMessage | None:
        return None

    def mark_failed(self, notification_id: str, reason: str) -> NotificationMessage | None:
        return None

    def mute(self, notification_id: str, reason: str) -> NotificationMessage | None:
        return None

    def archive(self, notification_id: str, confirm: bool = False) -> NotificationMessage | None:
        return None

    def dedupe_message(self, message: NotificationMessage) -> tuple[bool, str | None]:
        return False, None
