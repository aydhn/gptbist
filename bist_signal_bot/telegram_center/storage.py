import json
from pathlib import Path
from bist_signal_bot.telegram_center.models import TelegramCommand, TelegramCommandResult, NotificationMessage, DigestResult, TelegramRateLimitState, NotificationStatus
from bist_signal_bot.storage.paths import get_telegram_center_dir

class TelegramCenterStore:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or get_telegram_center_dir()
        self.commands_file = self.base_dir / "commands" / "telegram_commands.jsonl"
        self.results_file = self.base_dir / "results" / "telegram_command_results.jsonl"
        self.inbox_file = self.base_dir / "inbox" / "notification_inbox.jsonl"

        self.commands_file.parent.mkdir(parents=True, exist_ok=True)
        self.results_file.parent.mkdir(parents=True, exist_ok=True)
        self.inbox_file.parent.mkdir(parents=True, exist_ok=True)

    def append_command(self, command: TelegramCommand) -> Path:
        with open(self.commands_file, "a") as f:
            f.write(command.model_dump_json() + "\n")
        return self.commands_file

    def append_result(self, result: TelegramCommandResult) -> Path:
        with open(self.results_file, "a") as f:
            f.write(result.model_dump_json() + "\n")
        return self.results_file

    def load_commands(self, limit: int = 1000) -> list[TelegramCommand]:
        return []

    def load_results(self, limit: int = 1000) -> list[TelegramCommandResult]:
        return []

    def append_notification(self, message: NotificationMessage) -> Path:
        with open(self.inbox_file, "a") as f:
            f.write(message.model_dump_json() + "\n")
        return self.inbox_file

    def load_notifications(self, status: NotificationStatus | None = None, limit: int = 1000) -> list[NotificationMessage]:
        return []

    def update_notification(self, message: NotificationMessage) -> Path:
        return self.inbox_file

    def save_digest(self, result: DigestResult) -> dict[str, Path]:
        return {"path": self.base_dir}

    def load_latest_digest(self) -> DigestResult | None:
        return None

    def save_rate_limit_state(self, states: list[TelegramRateLimitState]) -> Path:
        return self.base_dir

    def load_rate_limit_states(self) -> list[TelegramRateLimitState]:
        return []
