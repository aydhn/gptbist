from bist_signal_bot.monitoring.escalation import MonitoringEscalationEngine
from bist_signal_bot.monitoring.models import MonitoringAlert, MonitoringAlertType, MonitoringStatus
from datetime import datetime

def test_escalation():
    eng = MonitoringEscalationEngine()
    alert = MonitoringAlert(
        alert_id="a1", alert_type=MonitoringAlertType.STRATEGY_DEGRADED,
        object_type="STRATEGY", object_id="S1", severity="HIGH",
        status=MonitoringStatus.DEGRADED, created_at=datetime.now(),
        title="High Alert", message="Test"
    )
    case_id = eng.create_review_case_for_alert(alert)
    assert case_id is not None
