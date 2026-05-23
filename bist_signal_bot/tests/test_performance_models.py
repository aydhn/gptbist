import pytest
from datetime import datetime, timezone
from bist_signal_bot.performance.models import (
    PerformanceMetric, ResourceSnapshot, ProfileSpan, ProfileResult, BenchmarkType, PerformanceStatus, ResourceMetricType
)

def test_performance_metric_validation():
    m = PerformanceMetric(
        metric_id="m1",
        metric_type=ResourceMetricType.CPU_PERCENT,
        name="test",
        value=50.0,
        unit="%",
        status=PerformanceStatus.PASS
    )
    assert m.value == 50.0

def test_resource_snapshot_graceful():
    s = ResourceSnapshot(
        snapshot_id="s1",
        captured_at=datetime.now(timezone.utc)
    )
    assert s.gpu_available is False
    assert s.cpu_percent is None

def test_profile_span_elapsed():
    s = ProfileSpan(
        span_id="sp1",
        name="test",
        started_at=datetime.now(timezone.utc),
        elapsed_seconds=1.5
    )
    assert s.elapsed_seconds == 1.5
