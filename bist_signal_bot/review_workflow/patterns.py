import uuid
from typing import Any, List, Optional
from datetime import datetime, timezone
from bist_signal_bot.review_workflow.models import ReviewPattern, ReviewCase, DecisionJournalEntry, ReviewCasePriority

class ReviewPatternDetector:
    def __init__(self, min_count: int = 3):
        self.min_count = min_count

    def detect_patterns(self, cases: List[ReviewCase], entries: Optional[List[DecisionJournalEntry]] = None) -> List[ReviewPattern]:
        patterns = []
        patterns.extend(self.repeated_conflict_patterns(cases))
        patterns.extend(self.repeated_evidence_gap_patterns(cases))
        # Additional patterns can be detected here
        return patterns

    def repeated_conflict_patterns(self, cases: List[ReviewCase]) -> List[ReviewPattern]:
        conflict_counts = {}
        for case in cases:
            for conflict in case.conflicts:
                key = (case.symbol, conflict)
                if key not in conflict_counts:
                    conflict_counts[key] = {"count": 0, "cases": []}
                conflict_counts[key]["count"] += 1
                conflict_counts[key]["cases"].append(case.case_id)

        patterns = []
        for (symbol, conflict), data in conflict_counts.items():
            if data["count"] >= self.min_count:
                patterns.append(ReviewPattern(
                    pattern_id=str(uuid.uuid4()),
                    pattern_type="REPEATED_CONFLICT",
                    count=data["count"],
                    message=f"Repeated conflict '{conflict}' detected for {symbol}",
                    symbol=symbol,
                    severity=ReviewCasePriority.HIGH if "CRITICAL" in conflict else ReviewCasePriority.MEDIUM,
                    related_case_ids=data["cases"]
                ))
        return patterns

    def repeated_evidence_gap_patterns(self, cases: List[ReviewCase]) -> List[ReviewPattern]:
        gap_counts = {}
        for case in cases:
            for gap in case.evidence_gaps:
                key = (case.symbol, gap)
                if key not in gap_counts:
                    gap_counts[key] = {"count": 0, "cases": []}
                gap_counts[key]["count"] += 1
                gap_counts[key]["cases"].append(case.case_id)

        patterns = []
        for (symbol, gap), data in gap_counts.items():
            if data["count"] >= self.min_count:
                patterns.append(ReviewPattern(
                    pattern_id=str(uuid.uuid4()),
                    pattern_type="REPEATED_GAP",
                    count=data["count"],
                    message=f"Repeated evidence gap '{gap}' detected for {symbol}",
                    symbol=symbol,
                    related_case_ids=data["cases"]
                ))
        return patterns
