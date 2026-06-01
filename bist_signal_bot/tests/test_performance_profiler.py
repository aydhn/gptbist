import pytest

from bist_signal_bot.performance.profiler import LocalPerformanceProfiler
from bist_signal_bot.performance.models import PerformanceStatus

def test_local_performance_profiler_callable():
    profiler = LocalPerformanceProfiler()

    def dummy_func():
        return 42

    profile = profiler.profile_callable("dummy", dummy_func)

    assert profile.module_name == "dummy"
    assert profile.status in [PerformanceStatus.PASS, PerformanceStatus.WATCH]
    assert len(profile.timings) == 1
    assert profile.timings[0].name == "callable:dummy"

def test_local_performance_profiler_command_dry_run():
    profiler = LocalPerformanceProfiler()
    profile = profiler.profile_command("test --dry-run")

    assert profile.module_name == "cli_command"
    assert profile.command == "test --dry-run"
    assert profile.status in [PerformanceStatus.PASS, PerformanceStatus.WATCH]

    # We should have resource measurements (even if psutil isn't available, they default to WATCH)
    assert len(profile.resources) == 2
