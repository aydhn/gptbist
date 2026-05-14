import pytest
from datetime import datetime
from bist_signal_bot.monitoring.models import (
    HeartbeatRecord, MonitoringComponent, HealthLevel,
    MonitoringMetric, MetricType, MonitoringAlert,
    AlertSeverity, AlertStatus, MonitoringSnapshot,
    SelfHealingAction, SelfHealingActionType
)

def test_heartbeat_record_validation():
    record = HeartbeatRecord(
        heartbeat_id="hb_1",
        timestamp=datetime.utcnow(),
        component=MonitoringComponent.RUNTIME,
        status=HealthLevel.HEALTHY,
        message="OK"
    )
    assert record.heartbeat_id == "hb_1"
    assert record.scheduler_active is False

    with pytest.raises(ValueError):
        HeartbeatRecord(
            heartbeat_id="",
            timestamp=datetime.utcnow(),
            component=MonitoringComponent.RUNTIME,
            status=HealthLevel.HEALTHY,
            message="OK"
        )

def test_monitoring_metric_validation():
    metric = MonitoringMetric(
        metric_id="m_1",
        timestamp=datetime.utcnow(),
        component=MonitoringComponent.RUNTIME,
        name="test_metric",
        metric_type=MetricType.COUNTER,
        value=1
    )
    assert metric.name == "test_metric"
    assert metric.value == 1

    with pytest.raises(ValueError):
        MonitoringMetric(
            metric_id="m_1",
            timestamp=datetime.utcnow(),
            component=MonitoringComponent.RUNTIME,
            name="",
            metric_type=MetricType.COUNTER,
            value=1
        )

def test_monitoring_alert_validation():
    alert = MonitoringAlert(
        alert_id="a_1",
        timestamp=datetime.utcnow(),
        component=MonitoringComponent.RUNTIME,
        severity=AlertSeverity.ERROR,
        status=AlertStatus.NEW,
        title="Error",
        message="Bad thing happened",
        fingerprint="hash123",
        first_seen_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow()
    )
    assert alert.count == 1

    with pytest.raises(ValueError):
        MonitoringAlert(
            alert_id="a_1",
            timestamp=datetime.utcnow(),
            component=MonitoringComponent.RUNTIME,
            severity=AlertSeverity.ERROR,
            status=AlertStatus.NEW,
            title="",
            message="Bad thing happened",
            fingerprint="hash123",
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow()
        )

def test_monitoring_snapshot_summary():
    snapshot = MonitoringSnapshot(
        generated_at=datetime.utcnow(),
        overall_health=HealthLevel.HEALTHY,
        heartbeats=[],
        metrics=[],
        active_alerts=[],
        diagnostics=[],
        runtime_state_summary={}
    )
    summary = snapshot.summary()
    assert summary["overall_health"] == "HEALTHY"
    assert "disclaimer" in summary

def test_self_healing_action_validation():
    action = SelfHealingAction(
        action_id="sh_1",
        action_type=SelfHealingActionType.CLEAR_STALE_LOCK,
        component=MonitoringComponent.LOCK,
        description="Clear lock",
        requires_confirm=False,
        safe_to_auto_run=True,
        generated_at=datetime.utcnow()
    )
    assert action.executed is False
    assert action.success is None
