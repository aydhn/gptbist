from bist_signal_bot.signals.storage import SignalStore
from bist_signal_bot.signals.models import TrackedSignal
from datetime import datetime, timezone

def test_signal_storage_append_load(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s1)

    loaded = store.load_signals()
    assert len(loaded) == 1
    assert loaded[0].signal_id == "1"

def test_signal_storage_latest_by_id(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=10.0)
    store.append_signal(s1)

    s1.current_score = 20.0
    s1.updated_at = datetime.now(timezone.utc)
    store.update_signal(s1)

    loaded = store.load_signals()
    assert len(loaded) == 1
    assert loaded[0].current_score == 20.0
