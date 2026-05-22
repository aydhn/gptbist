import pytest
from bist_signal_bot.telegram_center.retry import TelegramRetryManager
from bist_signal_bot.telegram_center.inbox import NotificationInboxManager
from bist_signal_bot.telegram_center.storage import TelegramCenterStore
from bist_signal_bot.telegram_center.models import NotificationMessage
from bist_signal_bot.config.settings import Settings
import uuid
from datetime import datetime

def test_retry_transient_error(tmp_path):
    store = TelegramCenterStore(base_dir=tmp_path)
    settings = Settings(TELEGRAM_RETRY_ENABLED=True, TELEGRAM_MAX_RETRIES=3)
    inbox = NotificationInboxManager(store, settings)
    manager = TelegramRetryManager(inbox, settings)

    msg = NotificationMessage(
        notification_id=str(uuid.uuid4()),
        title="Test",
        body="Body",
        created_at=datetime.utcnow()
    )

    assert manager.should_retry(msg, "timeout error") is True

def test_retry_unauthorized(tmp_path):
    store = TelegramCenterStore(base_dir=tmp_path)
    settings = Settings(TELEGRAM_RETRY_ENABLED=True)
    inbox = NotificationInboxManager(store, settings)
    manager = TelegramRetryManager(inbox, settings)

    msg = NotificationMessage(
        notification_id=str(uuid.uuid4()),
        title="Test",
        body="Body",
        created_at=datetime.utcnow()
    )

    assert manager.should_retry(msg, "unauthorized access") is False
