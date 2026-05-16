import json
import logging
from pydantic import BaseModel

from pathlib import Path
from typing import Any
from datetime import datetime

from ..config.settings import Settings, get_settings
from ..storage.paths import get_research_dir, get_research_ledger_dir, get_research_reports_dir
from .models import (
    ResearchLedgerEntry, SignalJournalEntry, ResearchNote,
    ResearchComparisonReport, AttributionReport
)
from ..core.exceptions import ResearchStorageError

logger = logging.getLogger(__name__)

class ResearchStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir or get_research_dir(self.settings)
        self.ledger_dir = get_research_ledger_dir(self.settings)
        self.reports_dir = get_research_reports_dir(self.settings)
        self.journal_dir = self.base_dir / "journal"
        self.notes_dir = self.base_dir / "notes"
        self.index_dir = self.base_dir / "index"

        self.ledger_file = self.ledger_dir / "research_ledger.jsonl"
        self.journal_file = self.journal_dir / "signal_journal.jsonl"
        self.notes_file = self.notes_dir / "research_notes.jsonl"
        self.index_file = self.index_dir / "research_index.json"

        for d in [self.journal_dir, self.notes_dir, self.index_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def get_research_dir(self) -> Path:
        return self.base_dir

    def _append_jsonl(self, file_path: Path, data: BaseModel) -> Path:
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(data.model_dump_json() + "\n")
            return file_path
        except Exception as e:
            logger.error(f"Failed to append to JSONL {file_path}: {e}")
            raise ResearchStorageError(f"Failed to write to {file_path}") from e

    def _load_jsonl(self, file_path: Path, model_cls: type[BaseModel], limit: int) -> list[BaseModel]:
        if not file_path.exists():
            return []
        entries = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Read backwards if limit applies or read all and tail
                for line in reversed(lines):
                    if not line.strip():
                        continue
                    if len(entries) >= limit:
                        break
                    try:
                        obj = model_cls.model_validate_json(line)
                        entries.append(obj)
                    except Exception as e:
                        logger.warning(f"Skipping malformed JSONL line in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to load JSONL {file_path}: {e}")
            raise ResearchStorageError(f"Failed to read from {file_path}") from e
        return entries

    def append_ledger_entry(self, entry: ResearchLedgerEntry) -> Path:
        return self._append_jsonl(self.ledger_file, entry)

    def load_ledger_entries(self, limit: int = 1000) -> list[ResearchLedgerEntry]:
        return self._load_jsonl(self.ledger_file, ResearchLedgerEntry, limit)

    def append_journal_entry(self, entry: SignalJournalEntry) -> Path:
        return self._append_jsonl(self.journal_file, entry)

    def load_journal_entries(self, limit: int = 1000) -> list[SignalJournalEntry]:
        return self._load_jsonl(self.journal_file, SignalJournalEntry, limit)

    def append_note(self, note: ResearchNote) -> Path:
        return self._append_jsonl(self.notes_file, note)

    def load_notes(self, limit: int = 1000) -> list[ResearchNote]:
        return self._load_jsonl(self.notes_file, ResearchNote, limit)

    def save_comparison_report(self, report: ResearchComparisonReport) -> dict[str, Path]:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        report_dir = self.reports_dir / date_str / report.comparison_id
        report_dir.mkdir(parents=True, exist_ok=True)

        file_path = report_dir / "comparison_report.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
        except Exception as e:
             raise ResearchStorageError(f"Failed to save comparison report: {e}") from e
        return {"json": file_path}

    def save_attribution_report(self, report: AttributionReport) -> dict[str, Path]:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        report_dir = self.reports_dir / date_str / report.attribution_id
        report_dir.mkdir(parents=True, exist_ok=True)

        file_path = report_dir / "attribution_report.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
        except Exception as e:
             raise ResearchStorageError(f"Failed to save attribution report: {e}") from e
        return {"json": file_path}

    def save_markdown_report(self, report_id: str, markdown: str) -> Path:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        report_dir = self.reports_dir / date_str / report_id
        report_dir.mkdir(parents=True, exist_ok=True)

        file_path = report_dir / "research_report.md"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown)
        except Exception as e:
             raise ResearchStorageError(f"Failed to save markdown report: {e}") from e
        return file_path

    def save_index(self, entries: list[ResearchLedgerEntry]) -> Path:
        index_data = [{"entry_id": e.entry_id, "run_id": e.run.run_id, "timestamp": e.timestamp.isoformat()} for e in entries]
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
            return self.index_file
        except Exception as e:
            raise ResearchStorageError(f"Failed to save index: {e}") from e

    def list_recent_reports(self, limit: int = 20) -> list[dict[str, Any]]:
        reports = []
        if not self.reports_dir.exists():
            return reports
        for date_dir in sorted(self.reports_dir.iterdir(), reverse=True):
            if not date_dir.is_dir(): continue
            for report_dir in date_dir.iterdir():
                if not report_dir.is_dir(): continue
                reports.append({"report_id": report_dir.name, "date": date_dir.name, "path": str(report_dir)})
                if len(reports) >= limit:
                    break
            if len(reports) >= limit:
                 break
        return reports
