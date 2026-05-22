import uuid
import time
from bist_signal_bot.telegram_center.models import TelegramCommand, TelegramCommandResult, TelegramCommandStatus, TelegramCommandDecision, TelegramCommandType
from bist_signal_bot.telegram_center.parser import TelegramCommandParser
from bist_signal_bot.telegram_center.permissions import TelegramPermissionManager
from bist_signal_bot.telegram_center.safety import TelegramCommandSafetyGuard
from bist_signal_bot.telegram_center.handlers import TelegramCommandHandlers
from bist_signal_bot.telegram_center.storage import TelegramCenterStore
from bist_signal_bot.telegram_center.client import TelegramClient
from bist_signal_bot.config.settings import Settings

class TelegramCommandRouter:
    def __init__(self, parser: TelegramCommandParser, permission_manager: TelegramPermissionManager, safety_guard: TelegramCommandSafetyGuard, handlers: TelegramCommandHandlers, store: TelegramCenterStore, client: TelegramClient, settings: Settings, logger=None):
        self.parser = parser
        self.permission_manager = permission_manager
        self.safety_guard = safety_guard
        self.handlers = handlers
        self.store = store
        self.client = client
        self.settings = settings
        self.logger = logger

    def route_raw_message(self, raw_text: str, chat_id: str, user_id: str | None = None, dry_run: bool = False) -> TelegramCommandResult:
        command = self.parser.parse(raw_text, chat_id, user_id)
        return self.route_command(command, dry_run)

    def route_command(self, command: TelegramCommand, dry_run: bool = False) -> TelegramCommandResult:
        start_time = time.time()

        perm_decision = self.permission_manager.evaluate_permission(command)
        if perm_decision != TelegramCommandDecision.ALLOW:
            return self._build_result(command, TelegramCommandStatus.BLOCKED, perm_decision, "Blocked by permission manager", start_time)

        safe_decision, warnings = self.safety_guard.evaluate(command)
        if safe_decision != TelegramCommandDecision.ALLOW:
            return self._build_result(command, TelegramCommandStatus.BLOCKED, safe_decision, "Blocked by safety guard", start_time, warnings)

        try:
            response_text = self.dispatch(command)
            sanitized = self.safety_guard.sanitize_response(response_text)
            disclaimed = self.safety_guard.ensure_disclaimer(sanitized)
            chunks = self.safety_guard.chunk_message(disclaimed)

            result = self._build_result(command, TelegramCommandStatus.EXECUTED, TelegramCommandDecision.ALLOW, disclaimed, start_time)
            result.chunks = chunks

            self.store.append_command(command)
            self.store.append_result(result)

            if not dry_run and getattr(self.settings, 'TELEGRAM_SEND_ENABLED', False):
                self.client.send_chunks(chunks)

            return result
        except Exception as e:
            return self._build_result(command, TelegramCommandStatus.FAILED, TelegramCommandDecision.ALLOW, f"Error executing command: {str(e)}", start_time)

    def dispatch(self, command: TelegramCommand) -> str:
        if command.command_type == TelegramCommandType.HELP:
            return self.handlers.handle_help(command)
        if command.command_type == TelegramCommandType.STATUS:
            return self.handlers.handle_status(command)
        if command.command_type == TelegramCommandType.HEALTH:
            return self.handlers.handle_health(command)
        if command.command_type == TelegramCommandType.SIGNALS:
            return self.handlers.handle_signals(command)
        if command.command_type == TelegramCommandType.REVIEW:
            return self.handlers.handle_review(command)
        if command.command_type == TelegramCommandType.PORTFOLIO:
            return self.handlers.handle_portfolio(command)
        if command.command_type == TelegramCommandType.STRESS:
            return self.handlers.handle_stress(command)
        if command.command_type == TelegramCommandType.DRIFT:
            return self.handlers.handle_drift(command)
        if command.command_type == TelegramCommandType.KB_SEARCH:
            return self.handlers.handle_kb_search(command)
        if command.command_type == TelegramCommandType.REPORT:
            return self.handlers.handle_report(command)
        if command.command_type == TelegramCommandType.LAB:
            return self.handlers.handle_lab(command)
        if command.command_type == TelegramCommandType.MAINTENANCE:
            return self.handlers.handle_maintenance(command)
        if command.command_type == TelegramCommandType.GOVERNANCE:
            return self.handlers.handle_governance(command)
        if command.command_type == TelegramCommandType.DIGEST:
            return self.handlers.handle_digest(command)
        if command.command_type == TelegramCommandType.SETTINGS:
            return self.handlers.handle_settings(command)
        return "Unknown command"

    def _build_result(self, command: TelegramCommand, status: TelegramCommandStatus, decision: TelegramCommandDecision, text: str, start_time: float, warnings: list[str] = None) -> TelegramCommandResult:
        return TelegramCommandResult(
            result_id=str(uuid.uuid4()),
            command_id=command.command_id,
            status=status,
            decision=decision,
            response_text=text,
            elapsed_seconds=time.time() - start_time,
            warnings=warnings or []
        )
