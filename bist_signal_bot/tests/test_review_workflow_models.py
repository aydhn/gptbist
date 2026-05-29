import pytest
from datetime import datetime, timedelta, timezone
from bist_signal_bot.review_workflow.models import (
    ReviewCase, ReviewCaseType, ReviewCaseStatus, ReviewCasePriority,
    ReviewPlaybook, ReviewPlaybookType, DecisionJournalEntry,
    ReviewSignoffRequest, SignoffStatus, ReviewDisposition
)

def test_review_case_symbol_normalization():
    case = ReviewCase(
        case_id="case-1",
        case_type=ReviewCaseType.SYMBOL_REVIEW,
        status=ReviewCaseStatus.OPEN,
        priority=ReviewCasePriority.MEDIUM,
        title="Test Case",
        summary="Test Summary",
        symbol="asels"
    )
    assert case.symbol == "ASELS"

def test_review_case_validation():
    with pytest.raises(ValueError, match="title cannot be empty"):
        ReviewCase(
            case_id="case-1",
            case_type=ReviewCaseType.SYMBOL_REVIEW,
            status=ReviewCaseStatus.OPEN,
            priority=ReviewCasePriority.MEDIUM,
            title="",
            summary="Test Summary"
        )

def test_review_case_closed_at_validation():
    with pytest.raises(ValueError, match="closed_at is set but status is OPEN"):
        ReviewCase(
            case_id="case-1",
            case_type=ReviewCaseType.SYMBOL_REVIEW,
            status=ReviewCaseStatus.OPEN,
            priority=ReviewCasePriority.MEDIUM,
            title="Test Case",
            summary="Test Summary",
            closed_at=datetime.now(timezone.utc)
        )

def test_playbook_disclaimer():
    playbook = ReviewPlaybook(
        playbook_id="pb-1",
        playbook_type=ReviewPlaybookType.STANDARD_SIGNAL_REVIEW,
        name="Standard Review",
        description="Standard playbook"
    )
    assert "research-only workflow metadata" in playbook.disclaimer

def test_journal_entry_disclaimer():
    entry = DecisionJournalEntry(
        entry_id="je-1",
        case_id="case-1",
        note="Test note"
    )
    assert "research-only and append-only" in entry.disclaimer

def test_signoff_request_disclaimer():
    signoff = ReviewSignoffRequest(
        signoff_id="so-1",
        case_id="case-1",
        reason="Test reason"
    )
    assert "research governance metadata only" in signoff.disclaimer
