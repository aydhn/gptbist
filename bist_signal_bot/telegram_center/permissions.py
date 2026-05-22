import uuid
from datetime import datetime
from bist_signal_bot.telegram_center.models import TelegramCommand, TelegramCommandType, TelegramCommandDecision, TelegramPermission
from bist_signal_bot.telegram_center.config import TelegramCenterConfigValidator
from bist_signal_bot.config.settings import Settings

class TelegramPermissionManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config_validator = TelegramCenterConfigValidator()
        self.permissions = self.default_permissions(settings)

        self.allowed_hash_set = set()
        for p in self.permissions:
            if p.active:
                self.allowed_hash_set.add(p.chat_id_hash)

    def is_authorized(self, command: TelegramCommand) -> bool:
        if not getattr(self.settings, 'TELEGRAM_BLOCK_UNKNOWN_CHAT', True):
            return True
        return command.chat_id_hash in self.allowed_hash_set

    def allowed_commands_for_chat(self, chat_id_hash: str) -> list[TelegramCommandType]:
        for p in self.permissions:
            if p.chat_id_hash == chat_id_hash and p.active:
                return p.allowed_commands
        return []

    def evaluate_permission(self, command: TelegramCommand) -> TelegramCommandDecision:
        if not self.is_authorized(command):
            return TelegramCommandDecision.BLOCK_UNAUTHORIZED

        allowed = self.allowed_commands_for_chat(command.chat_id_hash)
        if allowed and command.command_type not in allowed:
            if getattr(self.settings, 'TELEGRAM_BLOCK_UNKNOWN_CHAT', True):
                return TelegramCommandDecision.BLOCK_UNAUTHORIZED

        return TelegramCommandDecision.ALLOW

    def default_permissions(self, settings: Settings) -> list[TelegramPermission]:
        perms = []

        if not hasattr(settings, 'TELEGRAM_ALLOWED_CHAT_IDS'):
            return perms

        allowed_str = getattr(settings, 'TELEGRAM_ALLOWED_CHAT_IDS', "")
        admin_str = getattr(settings, 'TELEGRAM_ADMIN_CHAT_IDS', "")

        allowed_ids = [s.strip() for s in allowed_str.split(",") if s.strip()]
        admin_ids = [s.strip() for s in admin_str.split(",") if s.strip()]

        all_commands_str = getattr(settings, 'TELEGRAM_ALLOWED_COMMANDS', "")
        all_commands_list = []
        for c in all_commands_str.split(","):
            c = c.strip()
            if c:
                try:
                    all_commands_list.append(TelegramCommandType(c))
                except ValueError:
                    pass

        for chat_id in allowed_ids:
            is_admin = chat_id in admin_ids
            chat_id_hash = self.config_validator.chat_id_hash(chat_id)

            perms.append(TelegramPermission(
                permission_id=str(uuid.uuid4()),
                chat_id_hash=chat_id_hash,
                allowed_commands=all_commands_list,
                is_admin=is_admin,
                created_at=datetime.utcnow()
            ))

        return perms
