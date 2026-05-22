from typing import Any
import pandas as pd
from bist_signal_bot.telegram_center.models import TelegramCommand, TelegramCommandResult, NotificationMessage, DigestResult

def telegram_command_to_dict(command: TelegramCommand) -> dict[str, Any]:
    return command.model_dump()

def telegram_result_to_dict(result: TelegramCommandResult) -> dict[str, Any]:
    return result.model_dump()

def notification_to_dict(message: NotificationMessage) -> dict[str, Any]:
    return message.model_dump()

def digest_result_to_dict(result: DigestResult) -> dict[str, Any]:
    return result.model_dump()

def commands_to_dataframe(commands: list[TelegramCommand]) -> pd.DataFrame:
    if not commands:
        return pd.DataFrame()
    return pd.DataFrame([telegram_command_to_dict(c) for c in commands])

def notifications_to_dataframe(messages: list[NotificationMessage]) -> pd.DataFrame:
    if not messages:
        return pd.DataFrame()
    return pd.DataFrame([notification_to_dict(m) for m in messages])

def format_telegram_command_result_text(result: TelegramCommandResult) -> str:
    return f"[{result.status.value}] {result.response_text}\n{result.disclaimer}"

def format_notification_inbox_text(messages: list[NotificationMessage]) -> str:
    return "\n".join([f"[{m.status.value}] {m.title}: {m.body}" for m in messages])

def format_digest_text(result: DigestResult) -> str:
    return f"{result.title}\n{result.body}\n{result.disclaimer}"

def format_telegram_center_report_markdown(stats: dict[str, Any]) -> str:
    return f"# Telegram Center Report\n\nStatus: {stats.get('status')}"
