import uuid
from typing import Any, List, Optional
from bist_signal_bot.review_workflow.models import (
    ReviewCase, ReviewCaseType, ReviewCaseStatus, ReviewCasePriority, ReviewDisposition
)
from bist_signal_bot.review_workflow.playbooks import ReviewPlaybookRegistry
from bist_signal_bot.review_workflow.priority import ReviewPriorityEngine

class ReviewCaseBuilder:
    def __init__(self, playbook_registry: ReviewPlaybookRegistry, priority_engine: ReviewPriorityEngine):
        self.playbook_registry = playbook_registry
        self.priority_engine = priority_engine

    def create_case_from_snapshot(self, snapshot: Any, case_type: ReviewCaseType = ReviewCaseType.SIGNAL_REVIEW, save: bool = False) -> ReviewCase:
        conflicts = getattr(snapshot, "conflicts", [])
        gaps = getattr(snapshot, "evidence_gaps", [])
        symbol = getattr(snapshot, "symbol", None)
        signal_id = getattr(snapshot, "signal_id", None)
        strategy_name = getattr(snapshot, "strategy_name", None)
        snapshot_id = getattr(snapshot, "snapshot_id", None)

        priority = self.priority_engine.calculate_priority(snapshot, conflicts, gaps)
        status = self.initial_status(priority, gaps)
        disposition = self.initial_disposition(snapshot)

        playbooks = self.playbook_registry.select_playbooks(snapshot, conflicts, gaps)
        playbook_ids = [pb.playbook_id for pb in playbooks]

        title = self.case_title(snapshot, symbol, signal_id)
        summary = self.case_summary(snapshot)

        case = ReviewCase(
            case_id=str(uuid.uuid4()),
            case_type=case_type,
            status=status,
            priority=priority,
            title=title,
            summary=summary,
            symbol=symbol,
            strategy_name=strategy_name,
            signal_id=signal_id,
            snapshot_id=snapshot_id,
            playbook_ids=playbook_ids,
            conflicts=[str(c) for c in conflicts],
            evidence_gaps=[str(g) for g in gaps],
            disposition=disposition
        )

        if save:
            pass # Storage will be injected in the app factory

        return case

    def create_case_for_symbol(self, symbol: str, strategy_name: Optional[str] = None, save: bool = False) -> ReviewCase:
        title = f"Review Symbol: {symbol}"
        if strategy_name:
            title += f" for Strategy: {strategy_name}"

        case = ReviewCase(
            case_id=str(uuid.uuid4()),
            case_type=ReviewCaseType.SYMBOL_REVIEW,
            status=ReviewCaseStatus.NEEDS_DATA,
            priority=ReviewCasePriority.MEDIUM,
            title=title,
            summary="Created without a snapshot. Needs data to proceed.",
            symbol=symbol,
            strategy_name=strategy_name,
            playbook_ids=["pb-missing-data"],
            evidence_gaps=["NO_SNAPSHOT"]
        )

        return case

    def create_case_for_signal(self, signal_payload: dict[str, Any], save: bool = False) -> ReviewCase:
        symbol = signal_payload.get("symbol", "UNKNOWN")
        strategy_name = signal_payload.get("strategy_name", "UNKNOWN")
        signal_id = signal_payload.get("signal_id", "UNKNOWN")

        case = ReviewCase(
            case_id=str(uuid.uuid4()),
            case_type=ReviewCaseType.SIGNAL_REVIEW,
            status=ReviewCaseStatus.OPEN,
            priority=ReviewCasePriority.MEDIUM,
            title=f"Review Signal {signal_id} for {symbol}",
            summary=f"Signal review triggered for {symbol} by {strategy_name}",
            symbol=symbol,
            strategy_name=strategy_name,
            signal_id=signal_id,
            playbook_ids=["pb-standard-signal-review"]
        )

        return case

    def case_title(self, snapshot: Any = None, symbol: Optional[str] = None, signal_id: Optional[str] = None) -> str:
        if symbol and signal_id:
            return f"Review Signal {signal_id} for {symbol}"
        if symbol:
            return f"Review Symbol: {symbol}"
        return "Review Case"

    def case_summary(self, snapshot: Any = None) -> str:
        if snapshot:
            score = getattr(snapshot, "composite_score", None)
            if score is not None:
                return f"Review based on Unified Context Snapshot. Composite Score: {score}"
        return "Review case created from workflow."

    def initial_status(self, priority: ReviewCasePriority, gaps: List[Any]) -> ReviewCaseStatus:
        if gaps:
            return ReviewCaseStatus.NEEDS_DATA
        return ReviewCaseStatus.OPEN

    def initial_disposition(self, snapshot: Any = None) -> ReviewDisposition:
        if snapshot:
            score = getattr(snapshot, "composite_score", None)
            if score is not None and score < 50:
                return ReviewDisposition.RESEARCH_WATCH
        return ReviewDisposition.UNKNOWN
