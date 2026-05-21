import pytest
from bist_signal_bot.review.decision import ReviewDecisionManager
from bist_signal_bot.review.models import ReviewDecisionType, ReviewItem, ReviewItemSource, ReviewItemStatus
from datetime import datetime, timezone

def test_decision_mapping():
    mgr = ReviewDecisionManager()
    assert mgr.map_decision_to_status(ReviewDecisionType.APPROVE_RESEARCH) == ReviewItemStatus.APPROVED_RESEARCH

def test_decision_validation():
    mgr = ReviewDecisionManager()
    item = ReviewItem(
        item_id="1", source=ReviewItemSource.MANUAL, symbol="A", title="T", summary="S",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        status=ReviewItemStatus.EXPIRED
    )
    warnings = mgr.validate_decision(item, ReviewDecisionType.APPROVE_RESEARCH, "Looks good")
    assert any("thesis" in w.lower() for w in warnings)
    assert any("expired" in w.lower() for w in warnings)

def test_decision_reason_unsafe():
    mgr = ReviewDecisionManager()
    item = ReviewItem(
        item_id="1", source=ReviewItemSource.MANUAL, symbol="A", title="T", summary="S",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    warnings = mgr.validate_decision(item, ReviewDecisionType.APPROVE_RESEARCH, "Kesin emir gönderilecek")
    assert any("unsafe" in w.lower() for w in warnings)

def test_archive_confirm():
    mgr = ReviewDecisionManager()
    with pytest.raises(ValueError):
        mgr.decide("1", ReviewDecisionType.ARCHIVE, "done")

    d = mgr.decide("1", ReviewDecisionType.ARCHIVE, "done", confirm=True)
    assert d.decision_type == ReviewDecisionType.ARCHIVE
