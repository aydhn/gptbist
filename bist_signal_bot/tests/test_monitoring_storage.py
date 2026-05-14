import pytest
from pathlib import Path
from datetime import datetime, timedelta
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.monitoring.storage import MonitoringStore
from bist_signal_bot.monitoring.models import (
    HeartbeatRecord, MonitoringComponent, HealthLevel,
    MonitoringMetric, MetricType, MonitoringSnapshot,
    DiagnosticCheckResult, DiagnosticCheckStatus, AlertSeverity
)

@pytest.fixture
def tmp_settings(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    return s

def test_monitoring_store_append_load_heartbeat(tmp_settings):
    store = MonitoringStore(settings=tmp_settings)

    hb = HeartbeatRecord(
        heartbeat_id="1", timestamp=datetime.utcnow(),
        component=MonitoringComponent.RUNTIME, status=HealthLevel.HEALTHY, message="test"
    )

    store.append_heartbeat(hb)

    loaded = store.load_recent_heartbeats()
    assert len(loaded) == 1
    assert loaded[0].heartbeat_id == "1"

def test_monitoring_store_append_load_metric(tmp_settings):
    store = MonitoringStore(settings=tmp_settings)

    metric = MonitoringMetric(
        metric_id="1", timestamp=datetime.utcnow(),
        component=MonitoringComponent.RUNTIME, name="test", metric_type=MetricType.COUNTER, value=1
    )

    store.append_metric(metric)

    loaded = store.load_recent_metrics()
    assert len(loaded) == 1
    assert loaded[0].name == "test"

def test_monitoring_store_save_snapshot(tmp_settings):
    store = MonitoringStore(settings=tmp_settings)

    snap = MonitoringSnapshot(
        generated_at=datetime.utcnow(), overall_health=HealthLevel.HEALTHY,
        heartbeats=[], metrics=[], active_alerts=[], diagnostics=[], runtime_state_summary={}
    )

    path = store.save_snapshot(snap)
    assert path.exists()

def test_monitoring_store_cleanup(tmp_settings):
    store = MonitoringStore(settings=tmp_settings)

    snap = MonitoringSnapshot(
        generated_at=datetime.utcnow() - timedelta(days=40), overall_health=HealthLevel.HEALTHY,
        heartbeats=[], metrics=[], active_alerts=[], diagnostics=[], runtime_state_summary={}
    )
    path = store.save_snapshot(snap)
    import os
    import time
    old_time = time.time() - (40 * 86400)
    os.utime(path, (old_time, old_time))

    res = store.cleanup_old_monitoring_files(retention_days=30)
    assert res["removed_files"] == 1
    assert not path.exists()
