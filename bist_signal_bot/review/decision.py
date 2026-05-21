import uuid
import re
from datetime import datetime, timezone
from typing import List, Optional

from .models import (
    ReviewItem, ReviewDecision, ReviewDecisionType, ReviewItemStatus
)

class ReviewDecisionManager:
    def __init__(self, store=None, settings=None):
        self.store = store
        self.settings = settings

    def map_decision_to_status(self, decision_type: ReviewDecisionType) -> ReviewItemStatus:
        mapping = {
            ReviewDecisionType.APPROVE_RESEARCH: ReviewItemStatus.APPROVED_RESEARCH,
            ReviewDecisionType.WATCH_ONLY: ReviewItemStatus.WATCH_ONLY,
            ReviewDecisionType.REJECT_RESEARCH: ReviewItemStatus.REJECTED_RESEARCH,
            ReviewDecisionType.NEEDS_MORE_DATA: ReviewItemStatus.WAITING_DATA,
            ReviewDecisionType.WAIT_FOR_FOLLOWUP: ReviewItemStatus.WAITING_FOLLOWUP,
            ReviewDecisionType.ARCHIVE: ReviewItemStatus.ARCHIVED,
            ReviewDecisionType.REOPEN: ReviewItemStatus.IN_REVIEW,
            ReviewDecisionType.NO_DECISION: ReviewItemStatus.IN_REVIEW,
        }
        return mapping.get(decision_type, ReviewItemStatus.IN_REVIEW)

    def validate_decision(self, item: ReviewItem, decision_type: ReviewDecisionType, reason: str) -> List[str]:
        warnings = []
        if decision_type == ReviewDecisionType.APPROVE_RESEARCH:
            if not item.thesis_id:
                warnings.append("Approval missing thesis")
            if item.status == ReviewItemStatus.EXPIRED:
                warnings.append("Cannot approve expired item directly; must reopen first")

        # Unsafe phrase checks
        unsafe_patterns = [
            r"kesin(lik)?\s?(al|sat|emir)",
            r"garanti",
        ]
        for p in unsafe_patterns:
            if re.search(p, reason, flags=re.IGNORECASE):
                warnings.append("Reason contains unsafe/financial advice language")

        return warnings

    def decide(self, item_id: str, decision_type: ReviewDecisionType, reason: str,
               confidence: Optional[float] = None, followup_at: Optional[datetime] = None,
               decided_by: Optional[str] = None, confirm: bool = False) -> ReviewDecision:

        # This needs a store to get the item, but we'll return the decision object
        # The inbox manager will typically call this

        if decision_type == ReviewDecisionType.ARCHIVE and not confirm:
            raise ValueError("Archive requires confirmation")

        now = datetime.now(timezone.utc)

        decision = ReviewDecision(
            decision_id=str(uuid.uuid4()),
            item_id=item_id,
            decision_type=decision_type,
            new_status=self.map_decision_to_status(decision_type),
            decided_at=now,
            decided_by=decided_by,
            reason=reason,
            confidence=confidence,
            followup_at=followup_at
        )
        return decision
