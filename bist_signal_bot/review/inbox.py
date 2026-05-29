import uuid
import re
from datetime import datetime, timezone
from typing import List, Optional, Any

from .models import (
    ReviewItem, ReviewItemSource, ReviewItemStatus, ReviewPriority,
    ReviewInboxSummary
)
from .evidence import ReviewEvidenceCollector
from .checklist import ReviewChecklistBuilder

# ContextFusion integrates with ReviewInboxManager
class ReviewInboxManager:
    def __init__(self, store=None, evidence_collector=None, checklist_builder=None, settings=None, logger=None):
        self.store = store
        self.evidence_collector = evidence_collector or ReviewEvidenceCollector(settings)
        self.checklist_builder = checklist_builder or ReviewChecklistBuilder(settings)
        self.settings = settings
        self.logger = logger

    def add_item_from_signal(self, signal: Any, source: ReviewItemSource = ReviewItemSource.SIGNAL_LIFECYCLE) -> ReviewItem:
        # Mocking creation
        now = datetime.now(timezone.utc)
        item = ReviewItem(
            item_id=str(uuid.uuid4()),
            source=source,
            symbol=getattr(signal, 'symbol', 'UNKNOWN'),
            strategy_name=getattr(signal, 'strategy_name', None),
            created_at=now,
            updated_at=now,
            title=f"Review {getattr(signal, 'symbol', 'UNKNOWN')}",
            summary="Auto-generated from signal"
        )
        if self.store:
            self.store.append_item(item)
        return item

    def add_item_from_consensus(self, consensus: Any) -> ReviewItem:
        return self.add_item_from_signal(consensus, ReviewItemSource.ENSEMBLE)

    def add_item_from_portfolio_item(self, portfolio_item: Any) -> ReviewItem:
        return self.add_item_from_signal(portfolio_item, ReviewItemSource.PORTFOLIO_RESEARCH)

    def add_manual_item(self, symbol: str, title: str, summary: str, tags: Optional[List[str]] = None) -> ReviewItem:

        # Check unsafe text in manual item
        unsafe_patterns = [r"kesin", r"garanti", r"yüzde yüz"]
        for p in unsafe_patterns:
            if re.search(p, title, flags=re.IGNORECASE) or re.search(p, summary, flags=re.IGNORECASE):
                raise ValueError("Manual item contains unsafe/guaranteed claims")

        now = datetime.now(timezone.utc)
        item = ReviewItem(
            item_id=str(uuid.uuid4()),
            source=ReviewItemSource.MANUAL,
            symbol=symbol.upper(),
            created_at=now,
            updated_at=now,
            title=title,
            summary=summary,
            tags=tags or []
        )
        if self.store:
            # check for existing
            items = self.store.load_items(symbol=symbol.upper())
            for existing in items:
                if existing.status in [ReviewItemStatus.NEW, ReviewItemStatus.IN_REVIEW] and existing.title == title:
                    existing.updated_at = now
                    existing.summary = summary
                    return self.store.update_item(existing)
            self.store.append_item(item)
        return item

    def list_items(self, status: Optional[ReviewItemStatus] = None, symbol: Optional[str] = None, limit: int = 100) -> List[ReviewItem]:
        if not self.store:
            return []
        return self.store.load_items(status=status, symbol=symbol, limit=limit)

    def get_item(self, item_id: str) -> Optional[ReviewItem]:
        if not self.store:
            return None
        return self.store.get_item(item_id)

    def update_item(self, item: ReviewItem) -> ReviewItem:
        if not self.store:
            return item
        return self.store.update_item(item)

    def archive_item(self, item_id: str, confirm: bool = False) -> ReviewItem:
        if not confirm:
            raise ValueError("Archive requires confirmation")

        item = self.get_item(item_id)
        if not item:
            raise ValueError("Item not found")

        item.status = ReviewItemStatus.ARCHIVED
        item.updated_at = datetime.now(timezone.utc)
        return self.update_item(item)

    def expire_stale_items(self, now: Optional[datetime] = None) -> List[ReviewItem]:
        if not self.store:
            return []

        dt = now or datetime.now(timezone.utc)
        items = self.store.load_items()
        expired = []

        for item in items:
            if item.status in [ReviewItemStatus.NEW, ReviewItemStatus.IN_REVIEW]:
                if item.expires_at and item.expires_at <= dt:
                    item.status = ReviewItemStatus.EXPIRED
                    item.updated_at = dt
                    self.update_item(item)
                    expired.append(item)

        return expired

    def summary(self) -> ReviewInboxSummary:
        if not self.store:
            return ReviewInboxSummary(generated_at=datetime.now(timezone.utc))

        items = self.store.load_items()
        summary = ReviewInboxSummary(generated_at=datetime.now(timezone.utc))
        summary.total_items = len(items)

        for item in items:
            if item.status == ReviewItemStatus.NEW:
                summary.new_count += 1
            elif item.status == ReviewItemStatus.IN_REVIEW:
                summary.in_review_count += 1
            elif item.status == ReviewItemStatus.APPROVED_RESEARCH:
                summary.approved_research_count += 1
            elif item.status == ReviewItemStatus.WATCH_ONLY:
                summary.watch_only_count += 1
            elif item.status == ReviewItemStatus.REJECTED_RESEARCH:
                summary.rejected_count += 1
            elif item.status == ReviewItemStatus.WAITING_FOLLOWUP:
                summary.waiting_followup_count += 1
            elif item.status == ReviewItemStatus.EXPIRED:
                summary.expired_count += 1

            if item.priority in [ReviewPriority.HIGH, ReviewPriority.URGENT] and item.status in [ReviewItemStatus.NEW, ReviewItemStatus.IN_REVIEW]:
                summary.high_priority_count += 1

        return summary