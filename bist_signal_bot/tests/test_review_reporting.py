import pytest
from bist_signal_bot.review.reporting import format_review_item_text, format_review_inbox_summary
from bist_signal_bot.review.models import ReviewItem, ReviewItemSource, ReviewInboxSummary
from datetime import datetime, timezone

def test_format_item():
    item = ReviewItem(item_id="1", source=ReviewItemSource.MANUAL, symbol="A", title="T", summary="S", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    text = format_review_item_text(item)
    assert "Symbol: A" in text
    assert "Disclaimer:" in text

def test_format_summary():
    s = ReviewInboxSummary(generated_at=datetime.now(timezone.utc), total_items=5, new_count=2)
    text = format_review_inbox_summary(s)
    assert "Total: 5" in text
