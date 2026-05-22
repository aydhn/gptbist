from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.telegram_center.client import TelegramClient
from bist_signal_bot.telegram_center.storage import TelegramCenterStore
from bist_signal_bot.telegram_center.inbox import NotificationInboxManager
from bist_signal_bot.telegram_center.digest import DigestOrchestrator
from bist_signal_bot.telegram_center.parser import TelegramCommandParser
from bist_signal_bot.telegram_center.permissions import TelegramPermissionManager
from bist_signal_bot.telegram_center.safety import TelegramCommandSafetyGuard
from bist_signal_bot.telegram_center.handlers import TelegramCommandHandlers
from bist_signal_bot.telegram_center.router import TelegramCommandRouter

def create_telegram_client(settings: Settings | None = None) -> TelegramClient:
    settings = settings or Settings()
    return TelegramClient(settings)

def create_telegram_store(settings: Settings | None = None, base_dir: Path | None = None) -> TelegramCenterStore:
    return TelegramCenterStore(base_dir=base_dir)

def create_notification_inbox(settings: Settings | None = None, base_dir: Path | None = None) -> NotificationInboxManager:
    settings = settings or Settings()
    store = create_telegram_store(settings, base_dir)
    return NotificationInboxManager(store, settings)

def create_digest_orchestrator(settings: Settings | None = None, base_dir: Path | None = None) -> DigestOrchestrator:
    settings = settings or Settings()
    store = create_telegram_store(settings, base_dir)
    client = create_telegram_client(settings)
    return DigestOrchestrator(store, client, settings)

def create_telegram_router(settings: Settings | None = None, base_dir: Path | None = None) -> TelegramCommandRouter:
    settings = settings or Settings()
    parser = TelegramCommandParser()
    permission_manager = TelegramPermissionManager(settings)
    safety_guard = TelegramCommandSafetyGuard(settings)
    handlers = TelegramCommandHandlers()
    store = create_telegram_store(settings, base_dir)
    client = create_telegram_client(settings)
    return TelegramCommandRouter(parser, permission_manager, safety_guard, handlers, store, client, settings)
