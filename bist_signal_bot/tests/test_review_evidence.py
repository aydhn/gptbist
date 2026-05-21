import pytest
from bist_signal_bot.review.evidence import ReviewEvidenceCollector
from bist_signal_bot.review.models import ReviewItem, ReviewItemSource
from datetime import datetime, timezone

def test_evidence_collector():
    collector = ReviewEvidenceCollector()
    item = ReviewItem(item_id="1", source=ReviewItemSource.MANUAL, symbol="A", title="T", summary="S", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    evs = collector.collect_for_item(item)
    # Should create empty evidences for each type
    assert len(evs) == 5
    for e in evs:
        assert "Source data not found" in e.warnings
