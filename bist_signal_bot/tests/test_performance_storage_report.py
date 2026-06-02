import pytest
from bist_signal_bot.performance.storage import PerformanceStore
from bist_signal_bot.performance.models import PerformanceProfile, BenchmarkResult, ResourceBudget, BenchmarkScenario
from datetime import datetime, timezone
from bist_signal_bot.performance.reporting import format_performance_report_markdown, PerformanceReport

def test_performance_store_profiles(tmp_path):
    store = PerformanceStore(base_dir=tmp_path)
    prof = PerformanceProfile(profile_id="p1", created_at=datetime.now(timezone.utc), module_name="test")
    store.append_profile(prof)
    profs = store.load_profiles()
    assert len(profs) == 1
    assert profs[0].profile_id == "p1"

def test_performance_store_benchmarks(tmp_path):
    store = PerformanceStore(base_dir=tmp_path)
    res = BenchmarkResult(benchmark_id="b1", scenario=BenchmarkScenario.OFFLINE_DEMO, created_at=datetime.now(timezone.utc))
    store.append_benchmark(res)
    benchs = store.load_benchmarks()
    assert len(benchs) == 1
    assert benchs[0].benchmark_id == "b1"

def test_performance_store_budgets(tmp_path):
    store = PerformanceStore(base_dir=tmp_path)
    b = ResourceBudget(budget_id="b1", module_name="test")
    store.save_budgets([b])
    # Assuming load is implemented, but the test requirement is just to check write logic
    assert (tmp_path / "budgets" / "resource_budgets.json").exists()

def test_performance_reporting():
    report = PerformanceReport(report_id="r1", generated_at=datetime.now(timezone.utc))
    md = format_performance_report_markdown(report)
    assert "# Performance Report" in md
    assert "Disclaimer:" in md
