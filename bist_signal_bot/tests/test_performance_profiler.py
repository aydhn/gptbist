import pytest
from bist_signal_bot.performance.profiler import FunctionProfiler
from bist_signal_bot.performance.models import PerformanceStatus

def test_function_profiler_success():
    profiler = FunctionProfiler()

    def simple_work():
        for i in range(100):
            pass

    res = profiler.profile_callable("simple", simple_work)
    assert res.status == PerformanceStatus.PASS
    assert res.name == "simple"
    assert res.elapsed_seconds >= 0

def test_function_profiler_exception():
    profiler = FunctionProfiler()

    def failing_work():
        raise ValueError("Intentional fail")

    res = profiler.profile_callable("failing", failing_work)
    assert res.status == PerformanceStatus.ERROR
    assert len(res.issues) > 0
