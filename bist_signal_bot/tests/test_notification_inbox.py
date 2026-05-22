import pytest
from bist_signal_bot.telegram_center.inbox import NotificationInboxManager
from bist_signal_bot.telegram_center.storage import TelegramCenterStore
from bist_signal_bot.telegram_center.models import NotificationMessage, NotificationStatus
from bist_signal_bot.config.settings import Settings
import uuid
from datetime import datetime

def test_notification_inbox_add(tmp_path):
    store = TelegramCenterStore(base_dir=tmp_path)
    settings = Settings()
    inbox = NotificationInboxManager(store, settings)

    msg = NotificationMessage(
        notification_id=str(uuid.uuid4()),
        title="Test",
        body="Body",
        created_at=datetime.utcnow()
    )
    inbox.add_message(msg)

    assert (tmp_path / "inbox" / "notification_inbox.jsonl").exists()

def test_notification_inbox_dedupe(tmp_path):
    store = TelegramCenterStore(base_dir=tmp_path)
    settings = Settings()
    inbox = NotificationInboxManager(store, settings)
    msg = NotificationMessage(
        notification_id=str(uuid.uuid4()),
        title="Test",
        body="Body",
        created_at=datetime.utcnow(),
        dedupe_key="key1"
    )
    is_dupe, reason = inbox.dedupe_message(msg)
    assert is_dupe is False
