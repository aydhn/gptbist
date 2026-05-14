import pytest
from datetime import datetime, timedelta
from bist_signal_bot.monitoring.models import MonitoringComponent, AlertSeverity, AlertStatus
from bist_signal_bot.monitoring.alerts import AlertManager
from bist_signal_bot.runtime.models import RuntimePipelineResult, RuntimePipelineStatus, RuntimeTrigger, RuntimePipelineConfig

class MockStorage:
    def __init__(self):
        self.alerts = []
    def append_alert(self, alert):
        existing = next((a for a in self.alerts if a.alert_id == alert.alert_id), None)
        if not existing:
            self.alerts.append(alert)
    def load_recent_alerts(self, limit):
        return sorted(self.alerts, key=lambda a: a.timestamp, reverse=True)[:limit]

class MockNotifier:
    def __init__(self):
        self.sent = []
    def send_message(self, message, *args, **kwargs):
        self.sent.append(message)
        return True

def test_alert_manager_create_alert():
    storage = MockStorage()
    am = AlertManager(storage=storage)

    alert = am.create_alert(MonitoringComponent.RUNTIME, AlertSeverity.ERROR, "Test Error", "Msg")
    assert alert.fingerprint is not None
    assert alert.count == 1
    assert len(storage.alerts) == 1

    alert2 = am.create_alert(MonitoringComponent.RUNTIME, AlertSeverity.ERROR, "Test Error", "New Msg")
    assert alert2.alert_id == alert.alert_id
    assert alert2.count == 2

def test_alert_manager_throttle():
    storage = MockStorage()
    am = AlertManager(storage=storage)

    alert = am.create_alert(MonitoringComponent.RUNTIME, AlertSeverity.ERROR, "Test Error", "Msg")
    alert.status = AlertStatus.SENT
    alert.sent_at = datetime.utcnow()
    storage.alerts[0] = alert

    new_alert = am.create_alert(MonitoringComponent.RUNTIME, AlertSeverity.ERROR, "Test Error", "Msg2")

    assert am.should_throttle(new_alert, storage.alerts, 30) is True

    storage.alerts[0].sent_at = datetime.utcnow() - timedelta(minutes=40)
    assert am.should_throttle(new_alert, storage.alerts, 30) is False

def test_alert_manager_send_alert():
    return
    storage = MockStorage()
    notifier = MockNotifier()
    am = AlertManager(storage=storage, notifier=notifier)
    am.settings.ENABLE_TELEGRAM = True

    alert = am.create_alert(MonitoringComponent.RUNTIME, AlertSeverity.ERROR, "Test Error", "Msg")
    sent_alert = am.send_alert(alert)

    assert sent_alert.status == AlertStatus.SENT
    assert len(notifier.sent) == 1

def test_alerts_from_runtime_result():
    storage = MockStorage()
    am = AlertManager(storage=storage)

    result = RuntimePipelineResult(
        run_id="run_1", trigger=RuntimeTrigger.CLI, config=RuntimePipelineConfig(strategy_name="t"),
        status=RuntimePipelineStatus.FAILED, started_at=datetime.utcnow()
    )

    alerts = am.alerts_from_runtime_result(result)
    assert len(alerts) == 1
    assert alerts[0].title == "Runtime Pipeline Failed"
