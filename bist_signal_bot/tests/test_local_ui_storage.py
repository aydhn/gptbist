import pytest
from datetime import datetime, timezone
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.local_ui.storage import LocalUIStore
from bist_signal_bot.local_ui.models import LocalUIRunResult, LocalUIBackend

def test_store_append_and_load_latest_run(tmp_path):
    settings = Settings(DATA_DIR=str(tmp_path), LOCAL_UI_DIR_NAME="local_ui")
    store = LocalUIStore(settings)

    result = LocalUIRunResult(
        run_id="run_123",
        backend=LocalUIBackend.PLAIN_TEXT,
        started_at=datetime.now(timezone.utc)
    )

    store.append_run(result)
    loaded = store.load_latest_run()

    assert loaded is not None
    assert loaded.run_id == "run_123"

def test_store_load_missing_run(tmp_path):
    settings = Settings(DATA_DIR=str(tmp_path), LOCAL_UI_DIR_NAME="local_ui")
    store = LocalUIStore(settings)
    loaded = store.load_latest_run()
    assert loaded is None
