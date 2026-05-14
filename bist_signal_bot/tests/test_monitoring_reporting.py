import pytest
from datetime import datetime
from bist_signal_bot.monitoring.models import (
    MonitoringSnapshot, HealthLevel, MonitoringAlert,
    MonitoringComponent, AlertSeverity, AlertStatus,
    SelfHealingResult, SelfHealingAction, SelfHealingActionType
)
from bist_signal_bot.monitoring.reporting import (
    monitoring_snapshot_to_dict, alerts_to_dataframe,
    format_monitoring_report_markdown, format_self_healing_result_text
)

def test_alerts_to_dataframe():
    alerts = [
        MonitoringAlert(
            alert_id="1", timestamp=datetime.utcnow(), component=MonitoringComponent.RUNTIME,
            severity=AlertSeverity.ERROR, status=AlertStatus.NEW, title="t1", message="m1",
            fingerprint="f1", first_seen_at=datetime.utcnow(), last_seen_at=datetime.utcnow()
        )
    ]
    df = alerts_to_dataframe(alerts)
    assert not df.empty
    assert len(df) == 1
    assert df.iloc[0]["title"] == "t1"

def test_format_report_markdown():
    snap = MonitoringSnapshot(
        generated_at=datetime.utcnow(), overall_health=HealthLevel.HEALTHY,
        heartbeats=[], metrics=[], active_alerts=[], diagnostics=[], runtime_state_summary={}
    )
    md = format_monitoring_report_markdown(snap)
    assert "BIST Signal Bot Monitoring Report" in md
    assert "HEALTHY" in md
    assert "No real order was sent" in md

def test_format_self_healing_result():
    res = SelfHealingResult(
        actions=[
            SelfHealingAction(
                action_id="1", action_type=SelfHealingActionType.CLEAR_STALE_LOCK,
                component=MonitoringComponent.LOCK, description="desc", requires_confirm=False,
                safe_to_auto_run=True, generated_at=datetime.utcnow(), executed=True, success=True
            )
        ],
        executed_count=1, success_count=1, failed_count=0, skipped_count=0,
        generated_at=datetime.utcnow()
    )

    txt = format_self_healing_result_text(res)
    assert "Actions Executed: 1" in txt
    assert "CLEAR_STALE_LOCK" in txt
