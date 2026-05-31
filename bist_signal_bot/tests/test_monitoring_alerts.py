from bist_signal_bot.monitoring.alerts import MonitoringAlertRouter
from bist_signal_bot.monitoring.models import PerformanceDecayFinding, MonitoringStatus, DecayType

def test_alert_from_decay():
    router = MonitoringAlertRouter()
    f = PerformanceDecayFinding(
        decay_id="d1", object_type="STRATEGY", object_id="S1", decay_type=DecayType.PERFORMANCE_DECAY,
        metric_name="win_rate", status=MonitoringStatus.DEGRADED, message="Bad decay"
    )
    alert = router.alert_from_decay(f)
    assert alert.severity == "HIGH"

def test_alert_routing():
    router = MonitoringAlertRouter()
    f = PerformanceDecayFinding(
        decay_id="d1", object_type="STRATEGY", object_id="S1", decay_type=DecayType.PERFORMANCE_DECAY,
        metric_name="win_rate", status=MonitoringStatus.WATCH, message="Watch decay"
    )
    alert = router.alert_from_decay(f)
    alert = router.route_alert(alert)
    assert "reports" in alert.routed_to
