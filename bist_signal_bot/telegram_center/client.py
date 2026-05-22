from typing import Any
from bist_signal_bot.config.settings import Settings

class TelegramClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send_message(self, text: str, chat_id: str | None = None, parse_mode: str | None = None, dry_run: bool = False) -> dict[str, Any]:
        return {"status": "success", "dry_run": dry_run, "message": "mocked send"}

    def send_chunks(self, chunks: list[str], chat_id: str | None = None, dry_run: bool = False) -> list[dict[str, Any]]:
        return [{"status": "success", "dry_run": dry_run} for _ in chunks]

    def get_updates(self, offset: int | None = None, limit: int = 10, dry_run: bool = False) -> list[dict[str, Any]]:
        return []

    def is_configured(self) -> bool:
        return bool(getattr(self.settings, 'TELEGRAM_BOT_TOKEN', '')) and getattr(self.settings, 'ENABLE_TELEGRAM_CENTER', False)
