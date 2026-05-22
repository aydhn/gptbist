import pytest
from bist_signal_bot.telegram_center.storage import TelegramCenterStore
from bist_signal_bot.telegram_center.models import TelegramCommand, TelegramCommandType, TelegramCommandStatus
import uuid
from datetime import datetime

def test_store_append_command(tmp_path):
    store = TelegramCenterStore(base_dir=tmp_path)
    cmd = TelegramCommand(
        command_id=str(uuid.uuid4()),
        raw_text="/status",
        command_type=TelegramCommandType.STATUS,
        chat_id_hash="hash",
        received_at=datetime.utcnow()
    )
    path = store.append_command(cmd)
    assert path.exists()
