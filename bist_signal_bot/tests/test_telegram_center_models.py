import pytest
from datetime import datetime
import uuid
from bist_signal_bot.telegram_center.models import TelegramCommand, TelegramCommandType, TelegramCommandStatus, TelegramCommandDecision, NotificationMessage, NotificationPriority, NotificationStatus, DigestRequest, DigestResult, DigestType

def test_telegram_command_validation():
    cmd = TelegramCommand(
        command_id=str(uuid.uuid4()),
        raw_text="/status",
        command_type=TelegramCommandType.STATUS,
        chat_id_hash="hash123",
        received_at=datetime.utcnow()
    )
    assert cmd.raw_text == "/status"
    assert cmd.status == TelegramCommandStatus.RECEIVED

def test_notification_message_validation():
    msg = NotificationMessage(
        notification_id=str(uuid.uuid4()),
        title="Test",
        body="Test body",
        created_at=datetime.utcnow()
    )
    assert msg.priority == NotificationPriority.NORMAL
    assert msg.status == NotificationStatus.PENDING

def test_digest_request_validation():
    req = DigestRequest(digest_type=DigestType.DAILY)
    assert req.include_signals is True
    assert req.include_review is True
    assert req.max_items_per_section == 10
