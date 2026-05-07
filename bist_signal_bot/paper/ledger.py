import json
import logging
import pandas as pd
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import PaperLedgerError
from bist_signal_bot.paper.models import (
    PaperAccount,
    PaperLedgerState,
    PaperLedgerEvent,
    PaperLedgerEventType
)
from bist_signal_bot.storage.paths import get_paper_dir, get_paper_account_dir


class PaperLedgerStore:
    def __init__(self, settings: Settings, base_dir: Optional[Path] = None):
        self.settings = settings
        self.base_dir = base_dir
        self.logger = logging.getLogger("bist_signal_bot.paper.ledger")

    def get_paper_dir(self) -> Path:
        if self.base_dir:
            dir_path = self.base_dir / self.settings.PAPER_ACCOUNTS_DIR_NAME
            dir_path.mkdir(parents=True, exist_ok=True)
            return dir_path
        return get_paper_dir(self.settings)

    def get_account_dir(self, account_id: str) -> Path:
        if self.base_dir:
            dir_path = self.get_paper_dir() / account_id
            dir_path.mkdir(parents=True, exist_ok=True)
            return dir_path
        return get_paper_account_dir(account_id, self.settings)

    def get_ledger_path(self, account_id: str) -> Path:
        return self.get_account_dir(account_id) / "ledger.json"

    def exists(self, account_id: str) -> bool:
        return self.get_ledger_path(account_id).exists()

    def initialize_ledger(self, account: PaperAccount, overwrite: bool = False) -> PaperLedgerState:
        ledger_path = self.get_ledger_path(account.account_id)
        if ledger_path.exists() and not overwrite:
            raise PaperLedgerError(f"Ledger already exists for account: {account.account_id}")

        state = PaperLedgerState(account=account)
        self.save(state)
        return state

    def load(self, account_id: str) -> PaperLedgerState:
        ledger_path = self.get_ledger_path(account_id)
        if not ledger_path.exists():
            raise PaperLedgerError(f"Ledger not found for account: {account_id}")

        try:
            with open(ledger_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PaperLedgerState.model_validate(data)
        except json.JSONDecodeError as e:
            raise PaperLedgerError(f"Corrupted ledger JSON for account {account_id}: {e}")
        except Exception as e:
            raise PaperLedgerError(f"Failed to load ledger for account {account_id}: {e}")

    def save(self, state: PaperLedgerState) -> Path:
        ledger_path = self.get_ledger_path(state.account.account_id)
        temp_path = ledger_path.with_suffix(".json.tmp")

        state.updated_at = datetime.now(UTC)

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))
            temp_path.replace(ledger_path)
            return ledger_path
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise PaperLedgerError(f"Failed to save ledger: {e}")

    def append_event(self, state: PaperLedgerState, event: PaperLedgerEvent) -> PaperLedgerState:
        state.events.append(event)
        state.updated_at = datetime.now(UTC)
        return state

    def export_csv(self, state: PaperLedgerState) -> dict[str, Path]:
        account_dir = self.get_account_dir(state.account.account_id)
        paths = {}

        exports = {
            "orders": [o.model_dump() for o in state.orders],
            "fills": [f.model_dump() for f in state.fills],
            "positions": [p.model_dump() for p in state.positions],
            "trades": [t.model_dump() for t in state.trades],
            "events": [e.model_dump() for e in state.events]
        }

        for name, data in exports.items():
            file_path = account_dir / f"{name}.csv"
            if data:
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False)
            else:
                # Write empty CSV with just headers if possible, or just empty file
                pd.DataFrame().to_csv(file_path, index=False)
            paths[name] = file_path

        return paths

    def backup_ledger(self, account_id: str) -> Path:
        ledger_path = self.get_ledger_path(account_id)
        if not ledger_path.exists():
            raise PaperLedgerError(f"Cannot backup, ledger not found: {account_id}")

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_path = ledger_path.with_name(f"ledger_backup_{timestamp}.json")

        try:
            import shutil
            shutil.copy2(ledger_path, backup_path)
            return backup_path
        except Exception as e:
            raise PaperLedgerError(f"Failed to create ledger backup: {e}")
