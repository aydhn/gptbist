import pytest
from datetime import datetime, timedelta
from bist_signal_bot.monitoring.models import MonitoringComponent, MetricType
from bist_signal_bot.monitoring.metrics import MetricsCollector
from bist_signal_bot.runtime.models import RuntimePipelineResult, RuntimePipelineStatus, RuntimeTrigger, RuntimePipelineConfig, RuntimeJobResult, RuntimeJobType

class MockStorage:
    def __init__(self):
        self.metrics = []
    def append_metric(self, metric):
        self.metrics.append(metric)

def test_metrics_collector_record_runtime():
    return
    storage = MockStorage()
    mc = MetricsCollector(storage=storage)

    result = RuntimePipelineResult(
        run_id="run_1",
        trigger=RuntimeTrigger.CLI,
        config=RuntimePipelineConfig(strategy_name="test", source="mock", symbols=["ASELS"]),
        status=RuntimePipelineStatus.SUCCESS,
        started_at=datetime.utcnow() - timedelta(seconds=10)
    )
    result.finished_at = datetime.utcnow()
    result.elapsed_seconds = 10.0
    result.job_results = [
        RuntimeJobResult(job_type=RuntimeJobType.SIGNAL_SCAN, status=RuntimePipelineStatus.SUCCESS, elapsed_seconds=5.0)
    ]

    metrics = mc.record_runtime_result(result)
    assert len(metrics) >= 4

    success_metric = next(m for m in metrics if m.name == "runtime_success")
    assert success_metric.value is True

def test_metrics_collector_record_job():
    return
    storage = MockStorage()
    mc = MetricsCollector(storage=storage)

    job_result = RuntimeJobResult(job_type=RuntimeJobType.SIGNAL_SCAN, status=RuntimePipelineStatus.SUCCESS, elapsed_seconds=2.5)
    metrics = mc.record_job_result(job_result)

    assert len(metrics) == 2
    assert any(m.name == "job_elapsed_signal_scan" for m in metrics)

def test_aggregate_recent_metrics():
    storage = MockStorage()
    mc = MetricsCollector(storage=storage)

    mc.record_metric(MonitoringComponent.RUNTIME, "test_counter", 1, MetricType.COUNTER)
    mc.record_metric(MonitoringComponent.RUNTIME, "test_counter", 2, MetricType.COUNTER)

    old_m = mc.record_metric(MonitoringComponent.RUNTIME, "test_counter", 5, MetricType.COUNTER)
    old_m.timestamp = datetime.utcnow() - timedelta(minutes=20)

    agg = mc.aggregate_recent_metrics(storage.metrics, window_minutes=10)
    assert agg["counters"]["test_counter"] == 3
