import uuid
import re
from datetime import datetime
from typing import Any
from bist_signal_bot.telegram_center.models import TelegramCommand, TelegramCommandType, TelegramCommandStatus, TelegramCommandDecision
from bist_signal_bot.telegram_center.config import TelegramCenterConfigValidator

class TelegramCommandParser:
    def __init__(self):
        self.config_validator = TelegramCenterConfigValidator()

    def parse(self, raw_text: str, chat_id: str, user_id: str | None = None) -> TelegramCommand:
        chat_id_hash = self.config_validator.chat_id_hash(chat_id)
        user_id_hash = self.config_validator.chat_id_hash(user_id) if user_id else None

        normalized_text = self.normalize_command(raw_text)
        command_type = TelegramCommandType.UNKNOWN

        parts = normalized_text.split()
        if not parts:
            pass
        elif parts[0] == '/help':
            command_type = TelegramCommandType.HELP
        elif parts[0] == '/status':
            command_type = TelegramCommandType.STATUS
        elif parts[0] == '/health':
            command_type = TelegramCommandType.HEALTH
        elif parts[0] == '/signals':
            command_type = TelegramCommandType.SIGNALS
        elif parts[0] == '/review':
            command_type = TelegramCommandType.REVIEW
        elif parts[0] == '/portfolio':
            command_type = TelegramCommandType.PORTFOLIO
        elif parts[0] == '/stress':
            command_type = TelegramCommandType.STRESS
        elif parts[0] == '/drift':
            command_type = TelegramCommandType.DRIFT
        elif parts[0] == '/kb':
            command_type = TelegramCommandType.KB_SEARCH
        elif parts[0] == '/report':
            command_type = TelegramCommandType.REPORT
        elif parts[0] == '/lab':
            command_type = TelegramCommandType.LAB
        elif parts[0] == '/maintenance':
            command_type = TelegramCommandType.MAINTENANCE
        elif parts[0] == '/governance':
            command_type = TelegramCommandType.GOVERNANCE
        elif parts[0] == '/digest':
            command_type = TelegramCommandType.DIGEST
        elif parts[0] == '/settings':
            command_type = TelegramCommandType.SETTINGS

        args = self.parse_args(command_type, normalized_text)

        return TelegramCommand(
            command_id=str(uuid.uuid4()),
            raw_text=raw_text,
            command_type=command_type,
            args=args,
            chat_id_hash=chat_id_hash,
            user_id_hash=user_id_hash,
            received_at=datetime.utcnow(),
            status=TelegramCommandStatus.PARSED,
            decision=TelegramCommandDecision.ALLOW
        )

    def normalize_command(self, raw_text: str) -> str:
        return raw_text.strip()

    def parse_args(self, command_type: TelegramCommandType, text: str) -> dict[str, Any]:
        parts = text.split(maxsplit=1)
        args_text = parts[1] if len(parts) > 1 else ""

        args = {}
        if args_text:
            if command_type in [TelegramCommandType.SIGNALS, TelegramCommandType.REVIEW]:
                args['symbol'] = args_text.strip().upper()
            elif command_type == TelegramCommandType.KB_SEARCH:
                args['query'] = args_text.strip()
            elif command_type in [TelegramCommandType.REPORT, TelegramCommandType.DIGEST]:
                args['type'] = args_text.strip().lower()
            elif command_type == TelegramCommandType.LAB:
                args['subcommand'] = args_text.strip().lower()
            elif command_type == TelegramCommandType.MAINTENANCE:
                args['subcommand'] = args_text.strip().lower()
            elif command_type == TelegramCommandType.GOVERNANCE:
                args['subcommand'] = args_text.strip().lower()
            else:
                args['text'] = args_text
        return args

    def help_text(self) -> str:
        return """
BIST Signal Bot - Research Command Center
Research-only. No real orders are sent.

/help - Show this message
/status - System status
/health - Healthcheck summary
/signals [symbol] - Signal summary
/review [symbol] - Review inbox
/portfolio - Portfolio snapshot
/stress - Stress test results
/drift - Drift status
/kb <query> - Search Knowledge Base
/report <daily|weekly> - Generate report
/lab jobs - Research lab jobs
/maintenance doctor - Doctor summary
/governance latest - Governance gate status
/digest <daily|weekly|runtime> - Generate digest
/settings - Configuration summary
"""
