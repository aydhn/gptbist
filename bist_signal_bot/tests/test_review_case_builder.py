from bist_signal_bot.review_workflow.case_builder import ReviewCaseBuilder
from bist_signal_bot.review_workflow.playbooks import ReviewPlaybookRegistry
from bist_signal_bot.review_workflow.priority import ReviewPriorityEngine
from bist_signal_bot.review_workflow.models import ReviewCaseStatus

class MockSnapshot:
    symbol = "ASELS"
    conflicts = ["MACRO_PRESSURE"]
    evidence_gaps = []
    composite_score = 45

def test_create_case_from_snapshot():
    builder = ReviewCaseBuilder(ReviewPlaybookRegistry(), ReviewPriorityEngine())
    case = builder.create_case_from_snapshot(MockSnapshot())
    assert case.symbol == "ASELS"
    assert case.status == ReviewCaseStatus.OPEN
    assert "MACRO_PRESSURE" in case.conflicts
    assert "pb-macro-pressure" in case.playbook_ids

def test_create_case_missing_snapshot():
    builder = ReviewCaseBuilder(ReviewPlaybookRegistry(), ReviewPriorityEngine())
    case = builder.create_case_for_symbol("THYAO")
    assert case.symbol == "THYAO"
    assert case.status == ReviewCaseStatus.NEEDS_DATA
    assert "pb-missing-data" in case.playbook_ids
