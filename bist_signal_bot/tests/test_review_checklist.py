import pytest
from bist_signal_bot.review.models import ReviewItem, ReviewItemSource, ChecklistItemStatus, ReviewChecklistItem
from bist_signal_bot.review.checklist import ReviewChecklistBuilder
from datetime import datetime, timezone

def test_default_checklist():
    builder = ReviewChecklistBuilder()
    item = ReviewItem(
        item_id="1", source=ReviewItemSource.MANUAL, symbol="A", title="T", summary="S",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    c = builder.build_default_checklist(item, [])
    assert len(c.items) == 12
    assert c.items[0].name == "data_quality_checked"
    assert c.items[0].required is True

def test_checklist_overall_status_fail():
    builder = ReviewChecklistBuilder()
    items = [
        ReviewChecklistItem(item_id="1", name="a", status=ChecklistItemStatus.PASS, required=True),
        ReviewChecklistItem(item_id="1", name="b", status=ChecklistItemStatus.FAIL, required=True)
    ]
    assert builder.overall_status(items) == ChecklistItemStatus.FAIL

def test_checklist_overall_status_warn():
    builder = ReviewChecklistBuilder()
    items = [
        ReviewChecklistItem(item_id="1", name="a", status=ChecklistItemStatus.PASS, required=True),
        ReviewChecklistItem(item_id="1", name="b", status=ChecklistItemStatus.FAIL, required=False)
    ]
    assert builder.overall_status(items) == ChecklistItemStatus.WARN
