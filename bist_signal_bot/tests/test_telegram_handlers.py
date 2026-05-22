import pytest
from bist_signal_bot.telegram_center.handlers import TelegramCommandHandlers
from bist_signal_bot.telegram_center.models import TelegramCommand, TelegramCommandType
import uuid
from datetime import datetime

@pytest.fixture
def handlers():
    return TelegramCommandHandlers()

def create_cmd(cmd_type, args=None):
    return TelegramCommand(
        command_id=str(uuid.uuid4()),
        raw_text=f"/{cmd_type.value.lower()}",
        command_type=cmd_type,
        args=args or {},
        chat_id_hash="hash",
        received_at=datetime.utcnow()
    )

def test_handler_signals(handlers):
    cmd = create_cmd(TelegramCommandType.SIGNALS, {"symbol": "ASELS"})
    res = handlers.handle_signals(cmd)
    assert "ASELS" in res

def test_handler_lab(handlers):
    cmd = create_cmd(TelegramCommandType.LAB)
    res = handlers.handle_lab(cmd)
    assert "Lab status" in res

def test_handler_maintenance(handlers):
    cmd = create_cmd(TelegramCommandType.MAINTENANCE)
    res = handlers.handle_maintenance(cmd)
    assert "Maintenance doctor" in res
