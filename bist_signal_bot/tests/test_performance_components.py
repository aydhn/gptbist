import pytest
from datetime import datetime, timezone, timedelta
from bist_signal_bot.performance.resource_budget import ResourceBudgetManager
from bist_signal_bot.performance.models import ResourceBudget, CacheStatus
from bist_signal_bot.performance.cache import LocalCacheManager
from bist_signal_bot.performance.benchmark import PerformanceBenchmarkRunner
from bist_signal_bot.performance.models import BenchmarkScenario
from bist_signal_bot.performance.bottlenecks import BottleneckAnalyzer
from bist_signal_bot.performance.models import PerformanceProfile, TimingMeasurement
from bist_signal_bot.performance.regression import PerformanceRegressionDetector
from bist_signal_bot.performance.models import BenchmarkResult

def test_resource_budget_manager():
    mgr = ResourceBudgetManager()
    budgets = mgr.default_budgets()
    assert len(budgets) > 0
    assert any(b.module_name == "bootstrap" for b in budgets)

def test_local_cache_manager():
    mgr = LocalCacheManager()
    key = mgr.build_key("ns", {"a": 1})
    assert len(key) == 32
    res = mgr.get("ns", key)
    assert res.status == CacheStatus.MISS

    # put without confirm
    mgr.put("ns", key, {"res": "ok"}, confirm=False)
    assert mgr.get("ns", key).status == CacheStatus.MISS

    # put with confirm
    entry = mgr.put("ns", key, {"res": "ok"}, confirm=True)
    assert mgr.get("ns", key).status == CacheStatus.HIT

    # stale check
    entry.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert mgr.is_stale(entry)

def test_performance_benchmark_runner():
    runner = PerformanceBenchmarkRunner()
    cmd = runner.scenario_command(BenchmarkScenario.BOOTSTRAP_VALIDATE)
    assert cmd is not None
    res = runner.run_benchmark(BenchmarkScenario.ORCHESTRATOR_DRY_RUN)
    assert res.scenario == BenchmarkScenario.ORCHESTRATOR_DRY_RUN
    all_b = runner.run_all_benchmarks()
    assert len(all_b) > 0

def test_bottleneck_analyzer():
    analyzer = BottleneckAnalyzer()
    tm = TimingMeasurement(timing_id="t1", name="long", started_at=datetime.now(timezone.utc), elapsed_seconds=120.0)
    prof = PerformanceProfile(profile_id="p1", created_at=datetime.now(timezone.utc), module_name="test", timings=[tm])
    finding = analyzer.detect_runtime_bottleneck(prof)
    assert finding is not None
    assert finding.message == "Runtime exceeds 60s"

def test_performance_regression_detector():
    detector = PerformanceRegressionDetector()
    current = BenchmarkResult(benchmark_id="c1", scenario=BenchmarkScenario.OFFLINE_DEMO, created_at=datetime.now(timezone.utc), elapsed_seconds=20.0)
    baseline = BenchmarkResult(benchmark_id="b1", scenario=BenchmarkScenario.OFFLINE_DEMO, created_at=datetime.now(timezone.utc), elapsed_seconds=10.0)

    delta = detector.delta_pct(20.0, 10.0)
    assert delta == 100.0

    finding = detector.compare_result(current, baseline)
    assert finding.delta_pct == 100.0
    assert finding.status.value == "DEGRADED"

    regs = detector.detect_regressions([current], None)
    assert len(regs) == 1
    assert regs[0].message == "No baseline available"
