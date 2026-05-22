from datetime import datetime
from bist_signal_bot.telegram_center.models import TelegramRateLimitState
from bist_signal_bot.telegram_center.storage import TelegramCenterStore
from bist_signal_bot.config.settings import Settings

class TelegramRateLimiter:
    def __init__(self, store: TelegramCenterStore, settings: Settings):
        self.store = store
        self.settings = settings

    def allow(self, key: str, limit: int, window_seconds: int) -> tuple[bool, TelegramRateLimitState | None]:
        if not getattr(self.settings, 'TELEGRAM_RATE_LIMIT_ENABLED', True):
            return True, None
        return True, None

    def record(self, key: str) -> TelegramRateLimitState | None:
        return None

    def reset(self, key: str) -> None:
        pass

    def state(self, key: str) -> TelegramRateLimitState | None:
        return None
