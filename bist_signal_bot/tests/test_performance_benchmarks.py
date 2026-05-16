import pytest
from bist_signal_bot.performance.benchmarks import PerformanceBenchmarkRunner

def test_benchmark_runner():
    runner = PerformanceBenchmarkRunner()

    def my_work():
        pass

    res = runner.benchmark_callable("test", "CUSTOM", my_work, iterations=3)
    assert res.iterations == 3
    assert res.average_seconds >= 0

def test_mock_scanner_benchmark():
    runner = PerformanceBenchmarkRunner()
    res = runner.benchmark_scan_mock(["ASELS"], "ma", 2)
    assert res.status.value == "PASS"
    assert res.iterations == 2
