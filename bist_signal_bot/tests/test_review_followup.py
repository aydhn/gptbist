import pytest
from bist_signal_bot.review.followup import ReviewFollowupManager
from bist_signal_bot.review.storage import ReviewStore
from bist_signal_bot.review.models import ReviewItem, ReviewItemSource
from datetime import datetime, timezone, timedelta

@pytest.fixture
def store(tmp_path):
    return ReviewStore(base_dir=tmp_path)

@pytest.fixture
def manager(store):
    return ReviewFollowupManager(store=store)

def test_followup(manager, store):
    item = ReviewItem(item_id="1", source=ReviewItemSource.MANUAL, symbol="A", title="T", summary="S", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    store.append_item(item)

    now = datetime.now(timezone.utc)
    manager.set_followup("1", now - timedelta(days=1), confirm=True)

    due = manager.list_due_followups(now)
    assert len(due) == 1

    with pytest.raises(ValueError):
        manager.clear_followup("1")

    manager.clear_followup("1", confirm=True)
    due2 = manager.list_due_followups(now)
    assert len(due2) == 0
