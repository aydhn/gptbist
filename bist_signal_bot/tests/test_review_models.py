import pytest
from datetime import datetime, timezone
from bist_signal_bot.review.models import (
    ReviewItem, ReviewItemSource, ReviewItemStatus, ReviewPriority,
    ReviewChecklist, ReviewChecklistItem, ChecklistItemStatus,
    ReviewThesis, ThesisStrength, ReviewDecision, ReviewDecisionType,
    DecisionJournalEntry, ReviewInboxSummary
)

def test_review_item_defaults():
    now = datetime.now(timezone.utc)
    item = ReviewItem(
        item_id="item_1",
        source=ReviewItemSource.MANUAL,
        symbol="ASELS",
        created_at=now,
        updated_at=now,
        title="Test Item",
        summary="Test Summary"
    )
    assert item.status == ReviewItemStatus.NEW
    assert item.priority == ReviewPriority.NORMAL
    assert "No real order was sent" in item.disclaimer

def test_checklist_overall_status():
    checklist = ReviewChecklist(
        checklist_id="c1",
        item_id="i1",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    assert checklist.overall_status == ChecklistItemStatus.UNKNOWN

def test_thesis_disclaimer():
    now = datetime.now(timezone.utc)
    t = ReviewThesis(
        thesis_id="t1",
        item_id="i1",
        symbol="THYAO",
        created_at=now,
        updated_at=now,
        main_thesis="Test"
    )
    assert "research-only" in t.disclaimer
