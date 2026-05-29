from bist_signal_bot.review_workflow.patterns import ReviewPatternDetector
from bist_signal_bot.review_workflow.models import ReviewCase, ReviewCaseType, ReviewCaseStatus, ReviewCasePriority

def test_repeated_conflict_patterns():
    cases = [
        ReviewCase(case_id="1", title="A", summary="A", case_type=ReviewCaseType.SYMBOL_REVIEW, status=ReviewCaseStatus.OPEN, priority=ReviewCasePriority.LOW, symbol="ASELS", conflicts=["MACRO_PRESSURE"]),
        ReviewCase(case_id="2", title="A", summary="A", case_type=ReviewCaseType.SYMBOL_REVIEW, status=ReviewCaseStatus.OPEN, priority=ReviewCasePriority.LOW, symbol="ASELS", conflicts=["MACRO_PRESSURE"]),
        ReviewCase(case_id="3", title="A", summary="A", case_type=ReviewCaseType.SYMBOL_REVIEW, status=ReviewCaseStatus.OPEN, priority=ReviewCasePriority.LOW, symbol="ASELS", conflicts=["MACRO_PRESSURE"]),
        ReviewCase(case_id="4", title="A", summary="A", case_type=ReviewCaseType.SYMBOL_REVIEW, status=ReviewCaseStatus.OPEN, priority=ReviewCasePriority.LOW, symbol="THYAO", conflicts=["MACRO_PRESSURE"])
    ]
    detector = ReviewPatternDetector(min_count=3)
    patterns = detector.repeated_conflict_patterns(cases)
    assert len(patterns) == 1
    assert patterns[0].symbol == "ASELS"
    assert patterns[0].count == 3

def test_repeated_gap_patterns():
    cases = [
        ReviewCase(case_id="1", title="A", summary="A", case_type=ReviewCaseType.SYMBOL_REVIEW, status=ReviewCaseStatus.OPEN, priority=ReviewCasePriority.LOW, symbol="ASELS", evidence_gaps=["NO_FUNDAMENTALS"]),
        ReviewCase(case_id="2", title="A", summary="A", case_type=ReviewCaseType.SYMBOL_REVIEW, status=ReviewCaseStatus.OPEN, priority=ReviewCasePriority.LOW, symbol="ASELS", evidence_gaps=["NO_FUNDAMENTALS"]),
        ReviewCase(case_id="3", title="A", summary="A", case_type=ReviewCaseType.SYMBOL_REVIEW, status=ReviewCaseStatus.OPEN, priority=ReviewCasePriority.LOW, symbol="ASELS", evidence_gaps=["NO_FUNDAMENTALS"])
    ]
    detector = ReviewPatternDetector(min_count=3)
    patterns = detector.repeated_evidence_gap_patterns(cases)
    assert len(patterns) == 1
    assert patterns[0].pattern_type == "REPEATED_GAP"
