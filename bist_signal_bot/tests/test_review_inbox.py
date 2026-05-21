import pytest
from datetime import datetime, timezone
import json
from pathlib import Path

from bist_signal_bot.review.models import ReviewItemSource, ReviewItemStatus, ReviewPriority
from bist_signal_bot.review.inbox import ReviewInboxManager
from bist_signal_bot.review.storage import ReviewStore

@pytest.fixture
def store(tmp_path):
    return ReviewStore(base_dir=tmp_path)

@pytest.fixture
def manager(store):
    return ReviewInboxManager(store=store)

def test_add_manual_item(manager):
    item = manager.add_manual_item("ASELS", "Manual check", "Need to check breadth")
    assert item.symbol == "ASELS"
    assert item.status == ReviewItemStatus.NEW
    assert item.title == "Manual check"

def test_add_manual_unsafe(manager):
    with pytest.raises(ValueError):
        manager.add_manual_item("ASELS", "Kesin getiri fırsatı", "100% kazanç")

def test_no_duplicate_active_item(manager):
    i1 = manager.add_manual_item("THYAO", "Test 1", "Summary 1")
    i2 = manager.add_manual_item("THYAO", "Test 1", "Summary 2")
    assert i1.item_id == i2.item_id
    assert i2.summary == "Summary 2"

    items = manager.list_items()
    assert len(items) == 1

def test_expire_stale_items(manager):
    item = manager.add_manual_item("GARAN", "Test", "Sum")
    # Make it expired
    dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
    item.expires_at = dt
    manager.update_item(item)

    expired = manager.expire_stale_items(now=datetime(2020, 1, 2, tzinfo=timezone.utc))
    assert len(expired) == 1
    assert expired[0].status == ReviewItemStatus.EXPIRED

def test_archive_requires_confirm(manager):
    item = manager.add_manual_item("SISE", "Test", "Sum")
    with pytest.raises(ValueError):
        manager.archive_item(item.item_id, confirm=False)

    arch = manager.archive_item(item.item_id, confirm=True)
    assert arch.status == ReviewItemStatus.ARCHIVED

def test_summary(manager):
    manager.add_manual_item("KCHOL", "Test", "Sum")
    s = manager.summary()
    assert s.total_items == 1
    assert s.new_count == 1
