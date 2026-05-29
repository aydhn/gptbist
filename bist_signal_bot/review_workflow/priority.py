from typing import Any, List
from bist_signal_bot.review_workflow.models import ReviewCasePriority

class ReviewPriorityEngine:
    def calculate_priority(self, snapshot: Any = None, conflicts: List[Any] = None, gaps: List[Any] = None) -> ReviewCasePriority:
        priority = ReviewCasePriority.LOW

        if conflicts:
            conflict_priority = self.priority_from_conflicts(conflicts)
            priority = max(priority, conflict_priority, key=lambda p: list(ReviewCasePriority).index(p))

        if gaps:
            gap_priority = self.priority_from_gaps(gaps)
            priority = max(priority, gap_priority, key=lambda p: list(ReviewCasePriority).index(p))

        if snapshot:
            score_priority = self.priority_from_score(
                getattr(snapshot, "composite_score", None),
                getattr(snapshot, "context_status", None)
            )
            priority = max(priority, score_priority, key=lambda p: list(ReviewCasePriority).index(p))

        return priority

    def priority_from_conflicts(self, conflicts: List[Any]) -> ReviewCasePriority:
        for conflict in conflicts:
            severity = getattr(conflict, "severity", None)
            if severity == "CRITICAL" or conflict == "CRITICAL":
                return ReviewCasePriority.CRITICAL
            if severity == "HIGH" or conflict == "HIGH":
                return ReviewCasePriority.HIGH

        return ReviewCasePriority.MEDIUM if conflicts else ReviewCasePriority.LOW

    def priority_from_gaps(self, gaps: List[Any]) -> ReviewCasePriority:
        if len(gaps) > 3:
            return ReviewCasePriority.HIGH
        elif len(gaps) > 0:
            return ReviewCasePriority.MEDIUM
        return ReviewCasePriority.LOW

    def priority_from_score(self, composite_score: float | None, context_status: str | None) -> ReviewCasePriority:
        if context_status == "CRITICAL_CONFLICT":
            return ReviewCasePriority.CRITICAL
        if composite_score is not None:
            if composite_score < 30:
                return ReviewCasePriority.HIGH
            elif composite_score < 50:
                return ReviewCasePriority.MEDIUM
        return ReviewCasePriority.LOW

    def requires_signoff(self, priority: ReviewCasePriority, conflicts: List[Any] = None) -> bool:
        if priority == ReviewCasePriority.CRITICAL:
            return True
        if conflicts:
            for conflict in conflicts:
                if getattr(conflict, "severity", None) == "CRITICAL" or conflict == "CRITICAL":
                    return True
        return False
