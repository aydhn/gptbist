from bist_signal_bot.monitoring.models import MonitoringSnapshot, MonitoringStatus
from datetime import datetime

def test_monitoring_snapshot():
    snap = MonitoringSnapshot(
        snapshot_id="1",
        object_type="STRATEGY",
        object_id="S1",
        as_of=datetime.now(),
        status=MonitoringStatus.PASS
    )
    assert snap.status == MonitoringStatus.PASS
    assert "not investment advice" in snap.disclaimer
