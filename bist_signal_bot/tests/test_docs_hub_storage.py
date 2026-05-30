import pytest
from bist_signal_bot.docs_hub.storage import DocsHubStore
from bist_signal_bot.docs_hub.models import DocsIndex
from datetime import datetime

def test_save_load_index(tmp_path):
    store = DocsHubStore(base_dir=tmp_path)

    index = DocsIndex(
        index_id="test1",
        created_at=datetime.utcnow(),
        pages=[],
        total_pages=0
    )

    store.save_index(index)

    loaded = store.load_index()
    assert loaded is not None
    assert loaded.index_id == "test1"

def test_load_nonexistent_index(tmp_path):
    store = DocsHubStore(base_dir=tmp_path)
    loaded = store.load_index()
    assert loaded is None
