import pytest
from datetime import datetime, timedelta
from bist_signal_bot.monitoring.models import MonitoringComponent, HealthLevel, HeartbeatRecord
from bist_signal_bot.monitoring.heartbeat import HeartbeatManager

class MockStorage:
    def __init__(self):
        self.records = []
    def append_heartbeat(self, record):
        self.records.append(record)
    def load_recent_heartbeats(self, limit):
        return sorted(self.records, key=lambda r: r.timestamp, reverse=True)[:limit]

def test_heartbeat_manager_record():
    storage = MockStorage()
    hm = HeartbeatManager(storage=storage)

    record = hm.record(MonitoringComponent.RUNTIME, HealthLevel.HEALTHY, "test")
    assert record.component == MonitoringComponent.RUNTIME
    assert record.status == HealthLevel.HEALTHY
    assert len(storage.records) == 1

def test_heartbeat_manager_stale():
    hm = HeartbeatManager()

    r1 = HeartbeatRecord(
        heartbeat_id="1", timestamp=datetime.utcnow(), component=MonitoringComponent.RUNTIME,
        status=HealthLevel.HEALTHY, message="ok"
    )
    assert not hm.is_stale(r1, 300)

    r2 = HeartbeatRecord(
        heartbeat_id="2", timestamp=datetime.utcnow() - timedelta(minutes=10),
        component=MonitoringComponent.RUNTIME, status=HealthLevel.HEALTHY, message="ok"
    )
    assert hm.is_stale(r2, 300)

def test_component_health_from_heartbeat():
    storage = MockStorage()
    hm = HeartbeatManager(storage=storage)

    assert hm.component_health_from_heartbeat(MonitoringComponent.RUNTIME, 300) == HealthLevel.UNKNOWN

    hm.record(MonitoringComponent.RUNTIME, HealthLevel.HEALTHY, "ok")
    assert hm.component_health_from_heartbeat(MonitoringComponent.RUNTIME, 300) == HealthLevel.HEALTHY

    storage.records[0].timestamp = datetime.utcnow() - timedelta(minutes=10)
    assert hm.component_health_from_heartbeat(MonitoringComponent.RUNTIME, 300) == HealthLevel.DEGRADED
