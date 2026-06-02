import pytest
from bist_signal_bot.performance.profiler import LocalPerformanceProfiler

def test_local_performance_profiler_callable():
    profiler = LocalPerformanceProfiler()
    def dummy_func():
        return 42
    profile = profiler.profile_callable("dummy", dummy_func)
    assert profile.module_name == "callable"
    assert len(profile.timings) == 1
    assert profile.timings[0].name == "dummy"

def test_local_performance_profiler_command():
    profiler = LocalPerformanceProfiler()
    profile = profiler.profile_command("test command", dry_run=True)
    assert profile.command == "test command"
    assert len(profile.timings) == 1
