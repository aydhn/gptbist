from bist_signal_bot.monitoring.watchlist import MonitoringWatchlistManager
from bist_signal_bot.monitoring.models import MonitoringSnapshot, MonitoringStatus
from datetime import datetime

def test_watchlist_add_from_snapshot():
    wm = MonitoringWatchlistManager()
    snap = MonitoringSnapshot(
        snapshot_id="1", object_type="STRATEGY", object_id="S1",
        as_of=datetime.now(), status=MonitoringStatus.DEGRADED
    )
    item = wm.update_from_snapshot(snap)
    assert item is not None
    assert item.status == MonitoringStatus.WATCH
