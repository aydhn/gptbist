import pytest
from bist_signal_bot.telegram_center.safety import TelegramCommandSafetyGuard
from bist_signal_bot.telegram_center.models import TelegramCommand, TelegramCommandType, TelegramCommandDecision
from bist_signal_bot.config.settings import Settings
import uuid
from datetime import datetime

@pytest.fixture
def safety_guard():
    settings = Settings(TELEGRAM_APPEND_DISCLAIMER=True)
    return TelegramCommandSafetyGuard(settings)

def test_safety_guard_real_order(safety_guard):
    cmd = TelegramCommand(
        command_id=str(uuid.uuid4()),
        raw_text="ASELS al",
        command_type=TelegramCommandType.UNKNOWN,
        chat_id_hash="hash",
        received_at=datetime.utcnow()
    )
    decision, _ = safety_guard.evaluate(cmd)
    assert decision == TelegramCommandDecision.BLOCK_UNKNOWN_COMMAND

def test_safety_guard_disclaimer(safety_guard):
    text = "Some text"
    res = safety_guard.ensure_disclaimer(text)
    assert "Not investment advice" in res

def test_safety_guard_chunking(safety_guard):
    text = "a" * 4000
    chunks = safety_guard.chunk_message(text, max_chars=3500)
    assert len(chunks) > 1
