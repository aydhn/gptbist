import uuid
from typing import Any, List, Optional
from datetime import datetime, timezone
from bist_signal_bot.review_workflow.models import ReviewDataAction, ReviewCasePriority

class ReviewDataActionQueue:
    def __init__(self, store: Any = None):
        self.store = store

    def create_actions_from_gaps(self, case_id: str, gaps: List[Any]) -> List[ReviewDataAction]:
        actions = []
        for gap in gaps:
            action = self.create_action(
                case_id=case_id,
                description=f"Resolve missing evidence gap: {gap}",
                evidence_gap_id=str(gap)
            )
            actions.append(action)
        return actions

    def create_action(self, case_id: Optional[str], description: str, layer: Optional[str] = None,
                      symbol: Optional[str] = None, priority: ReviewCasePriority = ReviewCasePriority.MEDIUM, evidence_gap_id: Optional[str] = None) -> ReviewDataAction:
        action = ReviewDataAction(
            action_id=str(uuid.uuid4()),
            case_id=case_id,
            action_type="FETCH_DATA",
            description=description,
            layer=layer,
            symbol=symbol,
            priority=priority,
            evidence_gap_id=evidence_gap_id
        )
        if self.store:
            self.store.append_data_actions([action])
        return action

    def list_actions(self, status: Optional[str] = None, limit: int = 1000) -> List[ReviewDataAction]:
        if self.store:
            return self.store.load_data_actions(status, limit)
        return []

    def resolve_action(self, action_id: str, note: Optional[str] = None) -> ReviewDataAction:
        # Without store lookup, mock resolution
        action = ReviewDataAction(
            action_id=action_id,
            action_type="UNKNOWN",
            description="Resolved action",
            status="RESOLVED",
            resolved_at=datetime.now(timezone.utc)
        )
        if note:
            action.metadata["resolution_note"] = note

        # if store: update or append new state
        return action

    def actions_for_case(self, case_id: str) -> List[ReviewDataAction]:
        if self.store:
            actions = self.store.load_data_actions()
            return [a for a in actions if a.case_id == case_id]
        return []
