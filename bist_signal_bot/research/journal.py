import logging
import uuid
from typing import Any
from datetime import datetime

from ..config.settings import Settings, get_settings
from .models import SignalJournalEntry, ResearchSignalOutcome
from .storage import ResearchStore
from ..core.exceptions import SignalJournalError

class SignalJournal:
    def __init__(self, storage: ResearchStore, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.storage = storage
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)

    def append_signal(self, entry: SignalJournalEntry) -> SignalJournalEntry:
        self.storage.append_journal_entry(entry)
        return entry

    def from_signal_candidate(self, signal: Any, run_id: str | None = None, metadata: dict[str, Any] | None = None) -> SignalJournalEntry:
        entry = SignalJournalEntry(
            journal_id=f"jou_{uuid.uuid4().hex[:8]}",
            signal_id=getattr(signal, "id", None) or getattr(signal, "signal_id", None),
            run_id=run_id,
            symbol=getattr(signal, "symbol", "UNKNOWN"),
            strategy_name=getattr(signal, "strategy_name", "UNKNOWN"),
            direction=getattr(signal, "direction", None),
            signal_score=getattr(signal, "score", None),
            metadata=metadata or {}
        )
        return self.append_signal(entry)

    def from_scan_report(self, report: Any) -> list[SignalJournalEntry]:
        entries = []
        signals = getattr(report, "signals", [])
        run_id = getattr(report, "run_id", None)
        for sig in signals:
            entries.append(self.from_signal_candidate(sig, run_id=run_id))
        return entries

    def from_paper_result(self, result: Any) -> list[SignalJournalEntry]:
        # Typically paper results just reference signals, we might log them if they generated new explicit signals
        return []

    def load_entries(self, limit: int = 100, symbol: str | None = None, strategy_name: str | None = None) -> list[SignalJournalEntry]:
        entries = self.storage.load_journal_entries(limit=10000)
        filtered = []
        for e in entries:
            if symbol and e.symbol != symbol: continue
            if strategy_name and e.strategy_name != strategy_name: continue
            filtered.append(e)
            if len(filtered) >= limit: break
        return filtered

    def update_outcome(self, journal_id: str, outcome: ResearchSignalOutcome, outcome_return_pct: float | None = None, horizon_bars: int | None = None, confirm: bool = False) -> SignalJournalEntry:
        if self.settings.RESEARCH_JOURNAL_REQUIRE_CONFIRM_FOR_OUTCOME_UPDATE and not confirm:
            raise SignalJournalError("Confirm is required to update outcome.")

        entries = self.storage.load_journal_entries(limit=5000)
        for e in entries:
            if e.journal_id == journal_id:
                e.outcome = outcome
                e.outcome_return_pct = outcome_return_pct
                e.outcome_horizon_bars = horizon_bars
                self.append_signal(e) # Append-only update
                return e
        raise SignalJournalError(f"Journal entry {journal_id} not found.")

    def summarize_by_symbol(self) -> dict[str, Any]:
        entries = self.storage.load_journal_entries()
        summary = {}
        for e in entries:
            if e.symbol not in summary:
                summary[e.symbol] = {"total": 0, "positive": 0, "negative": 0}
            summary[e.symbol]["total"] += 1
            if e.outcome == ResearchSignalOutcome.POSITIVE: summary[e.symbol]["positive"] += 1
            if e.outcome == ResearchSignalOutcome.NEGATIVE: summary[e.symbol]["negative"] += 1
        return summary

    def summarize_by_strategy(self) -> dict[str, Any]:
        entries = self.storage.load_journal_entries()
        summary = {}
        for e in entries:
            if e.strategy_name not in summary:
                summary[e.strategy_name] = {"total": 0, "positive": 0, "negative": 0}
            summary[e.strategy_name]["total"] += 1
            if e.outcome == ResearchSignalOutcome.POSITIVE: summary[e.strategy_name]["positive"] += 1
            if e.outcome == ResearchSignalOutcome.NEGATIVE: summary[e.strategy_name]["negative"] += 1
        return summary
