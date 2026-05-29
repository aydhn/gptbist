import uuid
from typing import Any, List, Optional
from bist_signal_bot.review_workflow.models import DecisionJournalEntry, ReviewCaseStatus, ReviewDisposition

class DecisionJournal:
    def __init__(self, store: Any = None):
        self.store = store
        self.block_trade_language = True

    def _check_trade_language(self, text: str) -> str:
        if not self.block_trade_language:
            return text
        lower_text = text.lower()
        blocked_phrases = ["trade approved", "buy approved", "sell approved", "execute order"]
        for phrase in blocked_phrases:
            if phrase in lower_text:
                text = text.replace(phrase, "[REDACTED_UNSAFE_CLAIM]")
                # We can also raise an exception or log a warning, but redacting is safe
        return text

    def append_entry(self, case_id: str, note: str, actor: Optional[str] = None, entry_type: str = "NOTE",
                     disposition: Optional[ReviewDisposition] = None, new_status: Optional[ReviewCaseStatus] = None,
                     correction_of: Optional[str] = None) -> DecisionJournalEntry:

        safe_note = self._check_trade_language(note)

        entry = DecisionJournalEntry(
            entry_id=str(uuid.uuid4()),
            case_id=case_id,
            actor=actor,
            entry_type=entry_type,
            disposition=disposition,
            new_status=new_status,
            note=safe_note,
            correction_of=correction_of
        )

        if self.store:
            self.store.append_journal_entry(entry)

        return entry

    def entries_for_case(self, case_id: str, limit: int = 1000) -> List[DecisionJournalEntry]:
        if self.store:
            return self.store.load_journal(case_id, limit)
        return []

    def correct_entry(self, entry_id: str, correction_note: str, actor: Optional[str] = None) -> DecisionJournalEntry:
        # In an append-only journal, correcting means adding a new entry pointing to the old one
        # To do this cleanly, we need the case_id, which we'd typically get from the store.
        # For simplicity in this logic-only class without a store:
        return self.append_entry(
            case_id="UNKNOWN", # Should be looked up via store
            note=f"CORRECTION: {correction_note}",
            actor=actor,
            entry_type="CORRECTION",
            correction_of=entry_id
        )

    def summarize_case_journal(self, case_id: str) -> List[str]:
        entries = self.entries_for_case(case_id)
        return [e.note for e in entries if e.note]
