from bist_signal_bot.monitoring.storage import MonitoringStore
from pathlib import Path
from bist_signal_bot.monitoring.models import MonitoringSnapshot, MonitoringStatus
from datetime import datetime

def test_storage(tmp_path):
    store = MonitoringStore(tmp_path)
    snap = MonitoringSnapshot(
        snapshot_id="1", object_type="STRATEGY", object_id="S1",
        as_of=datetime.now(), status=MonitoringStatus.PASS
    )
    p = store.append_snapshot(snap)
    assert "snapshots.jsonl" in str(p)
