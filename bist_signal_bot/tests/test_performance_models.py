import pytest
from datetime import datetime, timezone
from bist_signal_bot.performance.models import (
    TimingMeasurement, PerformanceStatus, ResourceKind,
    CacheStatus, BenchmarkScenario, ResourceMeasurement,
    ResourceBudget, CacheEntry, CacheLookupResult,
    PerformanceProfile, BenchmarkResult, BottleneckFinding,
    PerformanceRegressionFinding, PerformanceReport
)

def test_timing_measurement_validation():
    tm = TimingMeasurement(timing_id="t1", name="test", started_at=datetime.now(timezone.utc))
    assert tm.timing_id == "t1"
    assert tm.status == PerformanceStatus.UNKNOWN

def test_resource_measurement_validation():
    rm = ResourceMeasurement(measurement_id="rm1", resource_kind=ResourceKind.CPU, module_name="test", unit="pct", measured_at=datetime.now(timezone.utc))
    assert rm.resource_kind == ResourceKind.CPU

def test_resource_budget_validation():
    rb = ResourceBudget(budget_id="b1", module_name="test", max_runtime_seconds=10.0)
    assert rb.max_runtime_seconds > 0

def test_cache_entry_validation():
    ce = CacheEntry(cache_id="c1", key="k1", namespace="ns1", path="/fake", created_at=datetime.now(timezone.utc))
    assert ce.key == "k1"

def test_cache_lookup_result():
    cl = CacheLookupResult(lookup_id="l1", key="k1", namespace="ns1", status=CacheStatus.MISS)
    assert cl.status == CacheStatus.MISS

def test_performance_profile():
    pp = PerformanceProfile(profile_id="p1", created_at=datetime.now(timezone.utc), module_name="test")
    assert pp.module_name == "test"

def test_benchmark_result_disclaimer():
    br = BenchmarkResult(benchmark_id="b1", scenario=BenchmarkScenario.ORCHESTRATOR_DRY_RUN, created_at=datetime.now(timezone.utc))
    assert "not indicate financial performance" in br.disclaimer

def test_bottleneck_finding():
    bf = BottleneckFinding(finding_id="f1", module_name="core", resource_kind=ResourceKind.CPU, severity="HIGH", message="test")
    assert bf.severity == "HIGH"

def test_regression_finding():
    rf = PerformanceRegressionFinding(regression_id="r1", scenario=BenchmarkScenario.OFFLINE_DEMO, threshold_pct=10.0, message="test")
    assert rf.threshold_pct == 10.0

def test_performance_report():
    pr = PerformanceReport(report_id="rpt1", generated_at=datetime.now(timezone.utc))
    assert pr.report_id == "rpt1"
