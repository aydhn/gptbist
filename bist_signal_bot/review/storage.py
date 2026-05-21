import json
import logging
from pathlib import Path
from typing import List, Optional

from .models import (
    ReviewItem, ReviewEvidence, ReviewChecklist, ReviewThesis,
    ReviewDecision, DecisionJournalEntry, ReviewItemStatus
)

class ReviewStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.items_path = base_dir / "items" / "review_items.jsonl"
        self.evidence_path = base_dir / "evidence" / "review_evidence.jsonl"
        self.checklists_path = base_dir / "checklists" / "review_checklists.jsonl"
        self.thesis_path = base_dir / "thesis" / "review_thesis.jsonl"
        self.decisions_path = base_dir / "decisions" / "review_decisions.jsonl"
        self.journal_path = base_dir / "journal" / "decision_journal.jsonl"

        for path in [self.items_path, self.evidence_path, self.checklists_path, self.thesis_path, self.decisions_path, self.journal_path]:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.touch()

        self.logger = logging.getLogger(__name__)

    def _append_jsonl(self, path: Path, obj: dict):
        # Basic secret redaction could be here, but assuming it's handled upstream
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj) + "\n")

    def append_item(self, item: ReviewItem) -> Path:
        self._append_jsonl(self.items_path, item.model_dump(mode="json"))
        return self.items_path

    def update_item(self, item: ReviewItem) -> ReviewItem:
        # Append-only update
        self.append_item(item)
        return item

    def load_items(self, status: Optional[ReviewItemStatus] = None, symbol: Optional[str] = None, limit: int = 1000) -> List[ReviewItem]:
        items_dict = {}
        if not self.items_path.exists():
            return []

        with open(self.items_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    item = ReviewItem(**data)
                    items_dict[item.item_id] = item
                except Exception as e:
                    self.logger.warning(f"Skipping malformed review item line: {e}")

        result = list(items_dict.values())
        if status:
            result = [i for i in result if i.status == status]
        if symbol:
            result = [i for i in result if i.symbol == symbol.upper()]

        return sorted(result, key=lambda x: x.updated_at, reverse=True)[:limit]

    def get_item(self, item_id: str) -> Optional[ReviewItem]:
        items = self.load_items()
        for item in items:
            if item.item_id == item_id:
                return item
        return None

    def append_evidence(self, evidence: ReviewEvidence) -> Path:
        self._append_jsonl(self.evidence_path, evidence.model_dump(mode="json"))
        return self.evidence_path

    def load_evidence(self, item_id: Optional[str] = None, limit: int = 1000) -> List[ReviewEvidence]:
        result = []
        if not self.evidence_path.exists():
            return []
        with open(self.evidence_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    ev = ReviewEvidence(**data)
                    if not item_id or ev.item_id == item_id:
                        result.append(ev)
                except Exception:
                    pass
        return result[:limit]

    def append_checklist(self, checklist: ReviewChecklist) -> Path:
        self._append_jsonl(self.checklists_path, checklist.model_dump(mode="json"))
        return self.checklists_path

    def get_checklist(self, checklist_id: str) -> Optional[ReviewChecklist]:
        checklists = {}
        if not self.checklists_path.exists(): return None
        with open(self.checklists_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    c = ReviewChecklist(**data)
                    checklists[c.checklist_id] = c
                except Exception:
                    pass
        return checklists.get(checklist_id)

    def append_thesis(self, thesis: ReviewThesis) -> Path:
        self._append_jsonl(self.thesis_path, thesis.model_dump(mode="json"))
        return self.thesis_path

    def get_thesis(self, thesis_id: str) -> Optional[ReviewThesis]:
        theses = {}
        if not self.thesis_path.exists(): return None
        with open(self.thesis_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    t = ReviewThesis(**data)
                    theses[t.thesis_id] = t
                except Exception:
                    pass
        return theses.get(thesis_id)

    def append_decision(self, decision: ReviewDecision) -> Path:
        self._append_jsonl(self.decisions_path, decision.model_dump(mode="json"))
        return self.decisions_path

    def load_decisions(self, item_id: Optional[str] = None, limit: int = 1000) -> List[ReviewDecision]:
        result = []
        if not self.decisions_path.exists(): return []
        with open(self.decisions_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    dec = ReviewDecision(**data)
                    if not item_id or dec.item_id == item_id:
                        result.append(dec)
                except Exception:
                    pass
        return result[:limit]

    def append_journal_entry(self, entry: DecisionJournalEntry) -> Path:
        self._append_jsonl(self.journal_path, entry.model_dump(mode="json"))
        return self.journal_path

    def load_journal(self, symbol: Optional[str] = None, limit: int = 1000) -> List[DecisionJournalEntry]:
        result = []
        if not self.journal_path.exists(): return []
        with open(self.journal_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    j = DecisionJournalEntry(**data)
                    if not symbol or j.symbol == symbol.upper():
                        result.append(j)
                except Exception:
                    pass
        return result[:limit]
