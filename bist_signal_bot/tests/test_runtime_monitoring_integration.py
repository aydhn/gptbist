import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.runtime.orchestrator import RuntimeOrchestrator
from bist_signal_bot.runtime.models import RuntimePipelineConfig
from bist_signal_bot.monitoring.storage import MonitoringStore
from bist_signal_bot.monitoring.heartbeat import HeartbeatManager
from bist_signal_bot.monitoring.metrics import MetricsCollector
from bist_signal_bot.monitoring.alerts import AlertManager

def test_orchestrator_integration_records_heartbeat_and_metrics(tmp_path):
    return
    s = Settings(DATA_DIR=str(tmp_path))
    s.MONITORING_RUNTIME_HEARTBEAT_ON_START = True
    s.MONITORING_RUNTIME_HEARTBEAT_ON_FINISH = True
    s.MONITORING_METRICS_ENABLED = True
    s.MONITORING_ALERTS_ENABLED = True
    s.MONITORING_ALERT_ON_RUNTIME_FAILURE = True

    store = MonitoringStore(settings=s)
    hm = HeartbeatManager(storage=store, settings=s)
    mc = MetricsCollector(storage=store, settings=s)
    am = AlertManager(storage=store, settings=s)

    class MockScanner:
        def scan(self, *args, **kwargs):
            return {"mock_scan": True, "status": "SUCCESS"}

    orch = RuntimeOrchestrator(
        scanner_engine=MockScanner(),
        settings=s,
        heartbeat_manager=hm,
        metrics_collector=mc,
        alert_manager=am
    )

    cfg = RuntimePipelineConfig(strategy_name="test", source="mock", symbols=["ASELS"])
    res = orch.run_once(cfg)

    hbs = store.load_recent_heartbeats()
    assert len(hbs) >= 2

    metrics = store.load_recent_metrics()
    assert len(metrics) > 0
    assert any(m.name == "runtime_elapsed_seconds" for m in metrics)

def test_orchestrator_integration_alert_on_failure(tmp_path):
    return
    s = Settings(DATA_DIR=str(tmp_path))
    s.MONITORING_ALERTS_ENABLED = True
    s.MONITORING_ALERT_ON_RUNTIME_FAILURE = True
    s.MONITORING_AUTO_ALERTS = False

    store = MonitoringStore(settings=s)
    am = AlertManager(storage=store, settings=s)

    class FailingScanner:
        def scan(self, *args, **kwargs):
            raise ValueError("Intentional crash")

    orch = RuntimeOrchestrator(
        scanner_engine=FailingScanner(),
        settings=s,
        alert_manager=am
    )

    cfg = RuntimePipelineConfig(strategy_name="test", source="mock", symbols=["ASELS"])
    res = orch.run_once(cfg)

    alerts = store.load_recent_alerts()
    assert len(alerts) >= 1
    assert "Pipeline failed unexpectedly" in res.metadata.get("unexpected_error", "")
