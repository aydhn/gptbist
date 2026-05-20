from bist_signal_bot.signals.watchlist import SignalWatchlistManager
from bist_signal_bot.signals.storage import SignalStore
from bist_signal_bot.signals.models import TrackedSignal
from datetime import datetime, timezone

def test_watchlist_add(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)
    s = TrackedSignal(signal_id="sig1", fingerprint_id="fp1", symbol="ASELS", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s)

    wm = SignalWatchlistManager(store)
    entry = wm.add("sig1", tags=["test"])

    assert entry.symbol == "ASELS"
    assert "test" in entry.tags
    assert store.get_signal("sig1").watchlist is True
