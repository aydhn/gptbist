import pytest
from bist_signal_bot.performance.benchmark import PerformanceBenchmarkRunner
from bist_signal_bot.performance.models import BenchmarkScenario

def test_benchmark_scenario_command():
    runner = PerformanceBenchmarkRunner()
    cmd = runner.scenario_command(BenchmarkScenario.ORCHESTRATOR_DRY_RUN)
    assert cmd == "orchestrator run --campaign QUICK_RESEARCH_SCAN --dry-run"

def test_benchmark_single_run():
    runner = PerformanceBenchmarkRunner()
    res = runner.run_benchmark(BenchmarkScenario.FEATURE_COMPUTE)
    assert res.scenario == BenchmarkScenario.FEATURE_COMPUTE
    assert res.elapsed_seconds is not None

def test_benchmark_all_deterministic():
    runner = PerformanceBenchmarkRunner()
    results = runner.run_all_benchmarks()
    # Excluding CUSTOM
    assert len(results) == len(BenchmarkScenario) - 1
