import pytest
from bist_signal_bot.performance.regression import PerformanceRegressionChecker
from bist_signal_bot.performance.models import BenchmarkRunResult, BenchmarkRequest, BenchmarkType, PerformanceBaseline, PerformanceStatus

def test_regression_elapsed():
    checker = PerformanceRegressionChecker()
    req = BenchmarkRequest(benchmark_type=BenchmarkType.SCANNER)
    bench = BenchmarkRunResult(benchmark_id="1", request=req, status=PerformanceStatus.PASS, median_elapsed_seconds=2.0)
    base = PerformanceBaseline(baseline_id="2", created_at="2020-01-01T00:00:00Z", benchmark_type=BenchmarkType.SCANNER, environment_hash="hash")
    base.metrics["median_elapsed_seconds"] = 1.0 # 100% increase

    res = checker.compare(bench, base)
    assert res.status == PerformanceStatus.FAIL # Because > 50%
    assert any("degraded" in r for r in res.regressions)
