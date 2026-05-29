from bist_signal_bot.review_workflow.signoff import ReviewSignoffManager
from bist_signal_bot.review_workflow.models import ReviewCase, ReviewCaseType, ReviewCaseStatus, ReviewCasePriority

def test_request_signoff():
    manager = ReviewSignoffManager()
    case = ReviewCase(
        case_id="case-1",
        case_type=ReviewCaseType.SYMBOL_REVIEW,
        status=ReviewCaseStatus.OPEN,
        priority=ReviewCasePriority.CRITICAL,
        title="Test",
        summary="Summary"
    )
    req = manager.request_signoff(case, "Need review")
    assert req.case_id == "case-1"
    assert req.reason == "Need review"

def test_is_signoff_required():
    manager = ReviewSignoffManager()
    case1 = ReviewCase(
        case_id="case-1",
        case_type=ReviewCaseType.SYMBOL_REVIEW,
        status=ReviewCaseStatus.OPEN,
        priority=ReviewCasePriority.CRITICAL,
        title="Test",
        summary="Summary"
    )
    case2 = ReviewCase(
        case_id="case-2",
        case_type=ReviewCaseType.SYMBOL_REVIEW,
        status=ReviewCaseStatus.OPEN,
        priority=ReviewCasePriority.LOW,
        title="Test",
        summary="Summary",
        playbook_ids=["pb-event-blackout"]
    )
    case3 = ReviewCase(
        case_id="case-3",
        case_type=ReviewCaseType.SYMBOL_REVIEW,
        status=ReviewCaseStatus.OPEN,
        priority=ReviewCasePriority.LOW,
        title="Test",
        summary="Summary"
    )
    assert manager.is_signoff_required(case1) == True
    assert manager.is_signoff_required(case2) == True
    assert manager.is_signoff_required(case3) == False

def test_approve_reject_signoff():
    manager = ReviewSignoffManager()
    appr = manager.approve_signoff("so-1", "lead")
    assert appr.status.name == "APPROVED_RESEARCH"

    rej = manager.reject_signoff("so-2", "Not enough evidence")
    assert rej.status.name == "REJECTED_RESEARCH"
    assert rej.rejection_reason == "Not enough evidence"
