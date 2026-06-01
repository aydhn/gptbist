import pytest
from datetime import datetime, timedelta, UTC

from bist_signal_bot.performance.timers import PerformanceTimer
from bist_signal_bot.performance.models import PerformanceStatus

def test_performance_timer_elapsed():
    now = datetime.now(UTC)
    later = now + timedelta(seconds=2.5)

    timer = PerformanceTimer()
    elapsed = timer.elapsed(now, later)

    assert elapsed == 2.5

def test_performance_timer_context_manager():
    timer = PerformanceTimer()

    with timer.measure("test_block") as m:
        # Simulate work
        pass

    assert m.status == PerformanceStatus.PASS
    assert m.elapsed_seconds is not None
    assert m.elapsed_seconds >= 0.0

def test_performance_timer_classification():
    timer = PerformanceTimer()
    assert timer.classify_elapsed(None) == PerformanceStatus.UNKNOWN
    assert timer.classify_elapsed(-1.0) == PerformanceStatus.UNKNOWN
    assert timer.classify_elapsed(10.0, 5.0) == PerformanceStatus.SLOW
    assert timer.classify_elapsed(2.0, 5.0) == PerformanceStatus.PASS
