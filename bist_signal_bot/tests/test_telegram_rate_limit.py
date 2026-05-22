import pytest
from bist_signal_bot.telegram_center.rate_limit import TelegramRateLimiter
from bist_signal_bot.telegram_center.storage import TelegramCenterStore
from bist_signal_bot.config.settings import Settings

def test_rate_limiter_allow(tmp_path):
    store = TelegramCenterStore(base_dir=tmp_path)
    settings = Settings()
    limiter = TelegramRateLimiter(store, settings)

    allowed, state = limiter.allow("chat123", limit=10, window_seconds=60)
    assert allowed is True
