import pytest
from bist_signal_bot.telegram_center.permissions import TelegramPermissionManager
from bist_signal_bot.telegram_center.models import TelegramCommand, TelegramCommandType, TelegramCommandDecision
from bist_signal_bot.config.settings import Settings
import uuid
from datetime import datetime

def test_permission_manager_unknown_chat():
    settings = Settings(TELEGRAM_ALLOWED_CHAT_IDS="chat123", TELEGRAM_BLOCK_UNKNOWN_CHAT=True)
    pm = TelegramPermissionManager(settings)

    cmd = TelegramCommand(
        command_id=str(uuid.uuid4()),
        raw_text="/status",
        command_type=TelegramCommandType.STATUS,
        chat_id_hash="unknown_hash",
        received_at=datetime.utcnow()
    )

    assert pm.evaluate_permission(cmd) == TelegramCommandDecision.BLOCK_UNAUTHORIZED

def test_permission_manager_allowed_chat():
    settings = Settings(TELEGRAM_ALLOWED_CHAT_IDS="chat123", TELEGRAM_BLOCK_UNKNOWN_CHAT=True)
    pm = TelegramPermissionManager(settings)

    from bist_signal_bot.telegram_center.config import TelegramCenterConfigValidator
    v = TelegramCenterConfigValidator()
    hash_val = v.chat_id_hash("chat123")

    cmd = TelegramCommand(
        command_id=str(uuid.uuid4()),
        raw_text="/status",
        command_type=TelegramCommandType.STATUS,
        chat_id_hash=hash_val,
        received_at=datetime.utcnow()
    )

    assert pm.evaluate_permission(cmd) == TelegramCommandDecision.ALLOW
