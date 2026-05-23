import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.profiler import LocalProfiler
from bist_signal_bot.performance.models import BenchmarkType, PerformanceStatus

def test_profiler_callable_success():
    profiler = LocalProfiler()
    res = profiler.profile_callable("test", BenchmarkType.CUSTOM, lambda: True)
    assert res.status in [PerformanceStatus.PASS, PerformanceStatus.WARN]
    assert len(res.spans) == 1

def test_profiler_callable_error():
    profiler = LocalProfiler()
    def fail(): raise ValueError("test")
    with pytest.raises(ValueError):
        profiler.profile_callable("test", BenchmarkType.CUSTOM, fail)
