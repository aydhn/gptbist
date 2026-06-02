import pytest
from datetime import datetime, timezone
from bist_signal_bot.performance.timers import PerformanceTimer
from bist_signal_bot.performance.models import PerformanceStatus

def test_performance_timer_elapsed():
    timer = PerformanceTimer()
    t1 = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2023, 1, 1, 12, 0, 10, tzinfo=timezone.utc)
    assert timer.elapsed(t1, t2) == 10.0

def test_performance_timer_context_manager():
    timer = PerformanceTimer()
    with timer.measure("test") as tm:
        pass
    assert tm.finished_at is not None
    assert tm.elapsed_seconds is not None
    assert tm.elapsed_seconds >= 0

def test_performance_timer_classify():
    timer = PerformanceTimer()
    assert timer.classify_elapsed(5.0, 10.0) == PerformanceStatus.PASS
    assert timer.classify_elapsed(15.0, 10.0) == PerformanceStatus.SLOW
    assert timer.classify_elapsed(None) == PerformanceStatus.UNKNOWN
