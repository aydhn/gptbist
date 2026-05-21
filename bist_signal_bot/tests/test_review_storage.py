import pytest
from bist_signal_bot.review.storage import ReviewStore
from bist_signal_bot.review.models import ReviewItem, ReviewItemSource
from datetime import datetime, timezone

def test_store_append_load(tmp_path):
    store = ReviewStore(base_dir=tmp_path)
    now = datetime.now(timezone.utc)
    item = ReviewItem(item_id="1", source=ReviewItemSource.MANUAL, symbol="A", title="T", summary="S", created_at=now, updated_at=now)

    store.append_item(item)
    items = store.load_items()
    assert len(items) == 1
    assert items[0].symbol == "A"

def test_store_skip_malformed(tmp_path):
    store = ReviewStore(base_dir=tmp_path)
    with open(store.items_path, "w") as f:
        f.write("{bad json}\n")
        f.write('{"item_id": "1", "source": "MANUAL", "symbol": "A", "title": "T", "summary": "S", "created_at": "2023-01-01T00:00:00Z", "updated_at": "2023-01-01T00:00:00Z"}\n')

    items = store.load_items()
    assert len(items) == 1
    assert items[0].item_id == "1"
