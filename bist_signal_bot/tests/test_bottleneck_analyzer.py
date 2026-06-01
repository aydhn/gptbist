import pytest
from datetime import datetime, UTC
import uuid

from bist_signal_bot.performance.bottlenecks import BottleneckAnalyzer
from bist_signal_bot.performance.models import (
    PerformanceProfile,
    PerformanceStatus,
    ResourceKind,
    ResourceMeasurement,
    TimingMeasurement,
    CacheLookupResult,
    CacheStatus
)

def test_bottleneck_runtime():
    analyzer = BottleneckAnalyzer()

    profile = PerformanceProfile(
        profile_id="p1",
        created_at=datetime.now(UTC),
        module_name="test",
        timings=[
            TimingMeasurement(
                timing_id="t1",
                name="slow_task",
                started_at=datetime.now(UTC),
                status=PerformanceStatus.SLOW,
                elapsed_seconds=100.0
            )
        ],
        resources=[],
        cache_results=[],
        status=PerformanceStatus.SLOW
    )

    findings = analyzer.analyze_profile(profile)
    assert len(findings) == 1
    assert findings[0].resource_kind == ResourceKind.RUNTIME
    assert "sampling" in (findings[0].suggested_action or "").lower()

def test_bottleneck_cache():
    analyzer = BottleneckAnalyzer()

    profile = PerformanceProfile(
        profile_id="p1",
        created_at=datetime.now(UTC),
        module_name="test",
        timings=[],
        resources=[],
        cache_results=[
            CacheLookupResult(lookup_id="c1", key="1", namespace="ns", status=CacheStatus.MISS),
            CacheLookupResult(lookup_id="c2", key="2", namespace="ns", status=CacheStatus.MISS)
        ],
        status=PerformanceStatus.DEGRADED
    )

    findings = analyzer.analyze_profile(profile)
    assert len(findings) == 1
    assert findings[0].resource_kind == ResourceKind.CACHE
