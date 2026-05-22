import pytest
from bist_signal_bot.telegram_center.router import TelegramCommandRouter
from bist_signal_bot.telegram_center.parser import TelegramCommandParser
from bist_signal_bot.telegram_center.permissions import TelegramPermissionManager
from bist_signal_bot.telegram_center.safety import TelegramCommandSafetyGuard
from bist_signal_bot.telegram_center.handlers import TelegramCommandHandlers
from bist_signal_bot.telegram_center.storage import TelegramCenterStore
from bist_signal_bot.telegram_center.client import TelegramClient
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.telegram_center.models import TelegramCommandStatus

@pytest.fixture
def router(tmp_path):
    settings = Settings(ENABLE_TELEGRAM_CENTER=True, TELEGRAM_ALLOWED_CHAT_IDS="chat123", TELEGRAM_BLOCK_UNKNOWN_CHAT=True)
    parser = TelegramCommandParser()
    permission_manager = TelegramPermissionManager(settings)
    safety_guard = TelegramCommandSafetyGuard(settings)
    handlers = TelegramCommandHandlers()
    store = TelegramCenterStore(base_dir=tmp_path)
    client = TelegramClient(settings)
    return TelegramCommandRouter(parser, permission_manager, safety_guard, handlers, store, client, settings)

def test_router_unauthorized_chat(router):
    result = router.route_raw_message("/status", "unknown_chat", dry_run=True)
    assert result.status == TelegramCommandStatus.BLOCKED

def test_router_help_dry_run(router):
    result = router.route_raw_message("/help", "chat123", dry_run=True)
    assert result.status == TelegramCommandStatus.EXECUTED
    assert "Help information" in result.response_text

def test_router_status_dry_run(router):
    result = router.route_raw_message("/status", "chat123", dry_run=True)
    assert result.status == TelegramCommandStatus.EXECUTED
    assert "Status OK" in result.response_text
