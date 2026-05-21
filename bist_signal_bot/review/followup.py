from datetime import datetime, timezone
from typing import List, Optional

from .models import ReviewItem

class ReviewFollowupManager:
    def __init__(self, store=None, settings=None):
        self.store = store
        self.settings = settings

    def set_followup(self, item_id: str, followup_at: datetime, note: Optional[str] = None, confirm: bool = False) -> ReviewItem:
        if not self.store:
            raise ValueError("Store not configured")

        item = self.store.get_item(item_id)
        if not item:
            raise ValueError("Item not found")

        item.followup_at = followup_at
        if note:
            item.metadata["followup_note"] = note

        return self.store.update_item(item)

    def list_due_followups(self, now: Optional[datetime] = None, limit: int = 100) -> List[ReviewItem]:
        if not self.store:
            return []

        dt = now or datetime.now(timezone.utc)
        items = self.store.load_items(limit=1000)
        due = []

        for item in items:
            if item.followup_at and item.followup_at <= dt:
                due.append(item)

        return due[:limit]

    def clear_followup(self, item_id: str, confirm: bool = False) -> ReviewItem:
        if not confirm:
            raise ValueError("Confirm required to clear followup")

        if not self.store:
            raise ValueError("Store not configured")

        item = self.store.get_item(item_id)
        if not item:
            raise ValueError("Item not found")

        item.followup_at = None
        return self.store.update_item(item)

    def mark_followup_done(self, item_id: str, note: Optional[str] = None, confirm: bool = False):
        pass # Normally would create a decision
