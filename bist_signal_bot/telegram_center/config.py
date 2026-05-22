import hashlib
from typing import Any
from bist_signal_bot.config.settings import Settings

class TelegramCenterConfigValidator:
    def validate_settings(self, settings: Settings) -> list[str]:
        errors = []
        if not hasattr(settings, 'ENABLE_TELEGRAM_CENTER'):
            return errors

        if getattr(settings, 'ENABLE_TELEGRAM_CENTER', False):
            if not getattr(settings, 'ENABLE_TELEGRAM', False):
                errors.append("ENABLE_TELEGRAM must be True if ENABLE_TELEGRAM_CENTER is True")
            if not getattr(settings, 'TELEGRAM_BOT_TOKEN', ''):
                errors.append("TELEGRAM_BOT_TOKEN is required when Telegram Center is enabled")
            if not getattr(settings, 'TELEGRAM_ALLOWED_CHAT_IDS', ''):
                errors.append("TELEGRAM_ALLOWED_CHAT_IDS is empty but Telegram Center is enabled")
        return errors

    def redacted_config_summary(self, settings: Settings) -> dict[str, Any]:
        if not hasattr(settings, 'ENABLE_TELEGRAM_CENTER'):
            return {"status": "not_configured"}

        return {
            "enabled": getattr(settings, 'ENABLE_TELEGRAM_CENTER', False),
            "commands_enabled": getattr(settings, 'TELEGRAM_COMMANDS_ENABLED', False),
            "send_enabled": getattr(settings, 'TELEGRAM_SEND_ENABLED', False),
            "dry_run_default": getattr(settings, 'TELEGRAM_DRY_RUN_DEFAULT', True),
            "research_only_mode": getattr(settings, 'TELEGRAM_RESEARCH_ONLY_MODE', True),
            "has_token": bool(getattr(settings, 'TELEGRAM_BOT_TOKEN', '')),
            "has_allowlist": bool(getattr(settings, 'TELEGRAM_ALLOWED_CHAT_IDS', '')),
        }

    def chat_id_hash(self, chat_id: str) -> str:
        return hashlib.sha256(str(chat_id).encode()).hexdigest()
