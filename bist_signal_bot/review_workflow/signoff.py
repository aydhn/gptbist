import uuid
from typing import Any, List, Optional
from datetime import datetime, timezone
from bist_signal_bot.review_workflow.models import ReviewSignoffRequest, SignoffStatus, ReviewCase, ReviewCasePriority

class ReviewSignoffManager:
    def __init__(self, store: Any = None):
        self.store = store

    def request_signoff(self, case: ReviewCase, reason: str, requested_by: Optional[str] = None) -> ReviewSignoffRequest:
        request = ReviewSignoffRequest(
            signoff_id=str(uuid.uuid4()),
            case_id=case.case_id,
            reason=reason,
            requested_by=requested_by
        )
        if self.store:
            self.store.append_signoff(request)
        return request

    def approve_signoff(self, signoff_id: str, approved_by: Optional[str] = None, note: Optional[str] = None) -> ReviewSignoffRequest:
        # In a real impl with store, we would fetch the signoff first.
        # Since this is an append-only/event-sourced system, we create a new record or update state if we have a stateful store.
        request = ReviewSignoffRequest(
            signoff_id=signoff_id,
            case_id="UNKNOWN", # Needs lookup
            reason="APPROVAL",
            status=SignoffStatus.APPROVED_RESEARCH,
            approved_by=approved_by,
            approved_at=datetime.now(timezone.utc)
        )
        if self.store:
            # We would typically fetch, mutate, and save or append an event
            pass
        return request

    def reject_signoff(self, signoff_id: str, rejection_reason: str, rejected_by: Optional[str] = None) -> ReviewSignoffRequest:
        request = ReviewSignoffRequest(
            signoff_id=signoff_id,
            case_id="UNKNOWN",
            reason="REJECTION",
            status=SignoffStatus.REJECTED_RESEARCH,
            rejection_reason=rejection_reason
        )
        if self.store:
            pass
        return request

    def signoffs_for_case(self, case_id: str) -> List[ReviewSignoffRequest]:
        if self.store:
            return self.store.load_signoffs(case_id)
        return []

    def is_signoff_required(self, case: ReviewCase) -> bool:
        if case.priority == ReviewCasePriority.CRITICAL:
            return True
        for playbook_id in case.playbook_ids:
            # Depending on configuration, certain playbooks require signoff.
            # E.g. EVENT_BLACKOUT or DISCLOSURE_HIGH_SEVERITY
            if playbook_id in ["pb-event-blackout", "pb-disclosure-high-severity"]:
                return True
        return False
