import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict

from .models import DecisionJournalEntry, ReviewDecision, ReviewItem, ReviewThesis

class DecisionJournal:
    def __init__(self, store=None, settings=None):
        self.store = store
        self.settings = settings

    def append_from_decision(self, decision: ReviewDecision, item: ReviewItem, thesis: Optional[ReviewThesis] = None) -> DecisionJournalEntry:
        entry = DecisionJournalEntry(
            journal_id=str(uuid.uuid4()),
            item_id=item.item_id,
            symbol=item.symbol,
            strategy_name=item.strategy_name,
            decision_id=decision.decision_id,
            created_at=datetime.now(timezone.utc),
            decision_type=decision.decision_type,
            status_after_decision=decision.new_status,
            thesis_summary=thesis.main_thesis if thesis else None
        )
        if self.store:
            self.store.append_journal_entry(entry)
        return entry

    def list_entries(self, symbol: Optional[str] = None, strategy_name: Optional[str] = None, limit: int = 100) -> List[DecisionJournalEntry]:
        if not self.store:
            return []
        return self.store.load_journal(symbol=symbol, limit=limit)

    def add_lesson(self, journal_id: str, lesson: str, confirm: bool = False) -> DecisionJournalEntry:
        # Requires store logic
        pass

    def link_outcome(self, journal_id: str, outcome_ref: str, confirm: bool = False) -> DecisionJournalEntry:
        # Requires store logic
        pass

    def summarize_history(self, symbol: Optional[str] = None, strategy_name: Optional[str] = None) -> Dict[str, Any]:
        entries = self.list_entries(symbol, strategy_name)
        return {
            "total_entries": len(entries),
            "symbol": symbol
        }
