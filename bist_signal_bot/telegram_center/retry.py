from bist_signal_bot.telegram_center.models import NotificationMessage
from bist_signal_bot.telegram_center.inbox import NotificationInboxManager
from bist_signal_bot.config.settings import Settings

class TelegramRetryManager:
    def __init__(self, inbox: NotificationInboxManager, settings: Settings):
        self.inbox = inbox
        self.settings = settings

    def should_retry(self, message: NotificationMessage, error: str) -> bool:
        if not getattr(self.settings, 'TELEGRAM_RETRY_ENABLED', True):
            return False

        unauthorized_errors = ["unauthorized", "forbidden", "governance block", "token missing"]
        for u in unauthorized_errors:
            if u in error.lower():
                return False

        return message.retry_count < getattr(self.settings, 'TELEGRAM_MAX_RETRIES', 2)

    def next_retry_message(self, message: NotificationMessage, error: str) -> NotificationMessage:
        message.retry_count += 1
        return message

    def retry_failed(self, limit: int = 10, dry_run: bool = False) -> list[NotificationMessage]:
        return []
