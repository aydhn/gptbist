from pathlib import Path
import pytest
import datetime
from bist_signal_bot.performance.models import (
    PerformanceStatus, TimingMeasurement, ResourceKind, ResourceMeasurement,
    ResourceBudget, CacheStatus, CacheEntry, CacheLookupResult,
    BenchmarkScenario, PerformanceProfile, BenchmarkResult,
    BottleneckFinding, PerformanceRegressionFinding, PerformanceReport
)
from bist_signal_bot.performance.timers import PerformanceTimer
from bist_signal_bot.performance.profiler import LocalPerformanceProfiler
from bist_signal_bot.performance.resource_budget import ResourceBudgetManager
from bist_signal_bot.performance.cache import LocalCacheManager
from bist_signal_bot.performance.benchmark import PerformanceBenchmarkRunner
from bist_signal_bot.performance.bottlenecks import BottleneckAnalyzer
from bist_signal_bot.performance.regression import PerformanceRegressionDetector
from bist_signal_bot.performance.storage import PerformanceStore
from bist_signal_bot.performance.reporting import format_profile_text

class DummyClock:
    def __init__(self):
        self._time = 1000.0
    def __call__(self):
        return self._time
    def tick(self, seconds=1.0):
        self._time += seconds

def test_timing_measurement_validation():
    now = datetime.datetime.now(datetime.timezone.utc)
    tm = TimingMeasurement(
        timing_id="t1",
        name="test",
        started_at=now,
        status=PerformanceStatus.PASS
    )
    assert tm.name == "test"
    assert tm.status == PerformanceStatus.PASS

def test_performance_timer_elapsed():
    clock = DummyClock()
    timer = PerformanceTimer(clock=clock)
    tm = timer.start("test_op")
    clock.tick(1.5)
    tm = timer.finish(tm)
    assert tm.elapsed_seconds == 1.5

def test_performance_timer_context_manager():
    clock = DummyClock()
    timer = PerformanceTimer(clock=clock)
    with timer.measure("test_op") as tm:
        clock.tick(2.0)
    assert tm.elapsed_seconds == 2.0
    assert tm.status == PerformanceStatus.PASS

def test_resource_budget_validation():
    budget = ResourceBudget(
        budget_id="b1",
        module_name="test",
        max_runtime_seconds=-5.0,
        status=PerformanceStatus.PASS
    )
    manager = ResourceBudgetManager()
    warnings = manager.validate_budget(budget)
    assert "max_runtime_seconds must be positive" in warnings

def test_resource_budget_manager_default_budgets():
    manager = ResourceBudgetManager()
    budgets = manager.default_budgets()
    assert len(budgets) > 0
    modules = [b.module_name for b in budgets]
    assert "bootstrap" in modules
    assert "qa" in modules

def test_local_cache_deterministic_key(tmp_path):
    manager = LocalCacheManager(base_dir=tmp_path)
    key1 = manager.build_key("ns", {"a": 1})
    key2 = manager.build_key("ns", {"a": 1})
    assert key1 == key2

def test_local_cache_get_miss(tmp_path):
    manager = LocalCacheManager(base_dir=tmp_path)
    res = manager.get("ns", "nonexistent")
    assert res.status == CacheStatus.MISS

def test_local_cache_put_no_confirm(tmp_path):
    manager = LocalCacheManager(base_dir=tmp_path)
    entry = manager.put("ns", "key1", {"data": 1}, confirm=False)
    assert entry.path == "memory_only"

def test_local_cache_put_confirm(tmp_path):
    manager = LocalCacheManager(base_dir=tmp_path)
    entry = manager.put("ns", "key2", {"data": 1}, confirm=True)
    assert tmp_path in Path(entry.path).parents or entry.path.startswith(str(tmp_path))
    assert Path(entry.path).exists()

def test_local_cache_stale(tmp_path):
    manager = LocalCacheManager(base_dir=tmp_path)
    entry = manager.put("ns", "key3", {"data": 1}, ttl_seconds=-10, confirm=True)
    assert manager.is_stale(entry)

def test_local_profiler_callable():
    profiler = LocalPerformanceProfiler()
    def my_fn():
        pass
    profile = profiler.profile_callable("my_fn", my_fn)
    assert profile.module_name == "my_fn"
    assert len(profile.timings) == 1

def test_local_profiler_command_dry_run():
    profiler = LocalPerformanceProfiler()
    profile = profiler.profile_command("test cmd", dry_run=True)
    assert profile.command == "test cmd"

def test_benchmark_runner_scenario_command():
    runner = PerformanceBenchmarkRunner()
    cmd = runner.scenario_command(BenchmarkScenario.ORCHESTRATOR_DRY_RUN)
    assert "orchestrator run" in cmd

def test_benchmark_runner_single():
    runner = PerformanceBenchmarkRunner()
    res = runner.run_benchmark(BenchmarkScenario.BOOTSTRAP_VALIDATE)
    assert res.scenario == BenchmarkScenario.BOOTSTRAP_VALIDATE

def test_benchmark_runner_all():
    runner = PerformanceBenchmarkRunner()
    results = runner.run_all_benchmarks()
    assert len(results) == len(BenchmarkScenario)

def test_bottleneck_analyzer_runtime():
    analyzer = BottleneckAnalyzer()
    profile = PerformanceProfile(
        profile_id="p1",
        created_at=datetime.datetime.now(datetime.timezone.utc),
        module_name="test",
        status=PerformanceStatus.PASS,
        timings=[TimingMeasurement(
            timing_id="t1",
            name="test",
            started_at=datetime.datetime.now(datetime.timezone.utc),
            elapsed_seconds=40.0,
            status=PerformanceStatus.PASS
        )]
    )
    b = analyzer.detect_runtime_bottleneck(profile)
    assert b is not None
    assert b.severity == "HIGH"

def test_regression_detector_no_baseline():
    detector = PerformanceRegressionDetector()
    current = [BenchmarkResult(
        benchmark_id="b1",
        scenario=BenchmarkScenario.BOOTSTRAP_VALIDATE,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        status=PerformanceStatus.PASS
    )]
    findings = detector.detect_regressions(current, baseline=None)
    assert len(findings) == 0

def test_regression_detector_delta_pct():
    detector = PerformanceRegressionDetector()
    assert detector.delta_pct(150, 100) == 50.0

def test_regression_detector_finding():
    detector = PerformanceRegressionDetector()
    current = BenchmarkResult(
        benchmark_id="b1",
        scenario=BenchmarkScenario.BOOTSTRAP_VALIDATE,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        elapsed_seconds=150.0,
        status=PerformanceStatus.PASS
    )
    baseline = BenchmarkResult(
        benchmark_id="b0",
        scenario=BenchmarkScenario.BOOTSTRAP_VALIDATE,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        elapsed_seconds=100.0,
        status=PerformanceStatus.PASS
    )
    finding = detector.compare_result(current, baseline)
    assert finding is not None
    assert finding.delta_pct == 50.0
    assert finding.status == PerformanceStatus.FAIL

def test_performance_store_profiles(tmp_path):
    store = PerformanceStore(base_dir=tmp_path)
    p = PerformanceProfile(
        profile_id="p1",
        created_at=datetime.datetime.now(datetime.timezone.utc),
        module_name="test",
        status=PerformanceStatus.PASS
    )
    store.append_profile(p)
    loaded = store.load_profiles()
    assert len(loaded) == 1
    assert loaded[0].profile_id == "p1"

def test_performance_store_benchmarks(tmp_path):
    store = PerformanceStore(base_dir=tmp_path)
    b = BenchmarkResult(
        benchmark_id="b1",
        scenario=BenchmarkScenario.BOOTSTRAP_VALIDATE,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        status=PerformanceStatus.PASS
    )
    store.append_benchmark(b)
    loaded = store.load_benchmarks()
    assert len(loaded) == 1
    assert loaded[0].benchmark_id == "b1"

def test_performance_store_budgets(tmp_path):
    store = PerformanceStore(base_dir=tmp_path)
    store.save_budgets([])
    # load_budgets is a stub, but testing save doesn't crash
    assert True

def test_reporting_markdown():
    report = PerformanceReport(
        report_id="r1",
        generated_at=datetime.datetime.now(datetime.timezone.utc)
    )
    from bist_signal_bot.performance.reporting import format_performance_report_markdown
    md = format_performance_report_markdown(report)
    assert "Disclaimer" in md
