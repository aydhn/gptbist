import pytest
import time
from bist_signal_bot.performance.timer import PerformanceTimer
from bist_signal_bot.core.exceptions import PerformanceError

def test_timer_start_stop():
    timer = PerformanceTimer()
    timer.start("test_task")
    time.sleep(0.01)
    res = timer.stop("test_task")
    assert res.elapsed_seconds >= 0.01
    assert res.name == "test_task"

def test_timer_context_manager():
    timer = PerformanceTimer()
    with timer.time_block("block_task"):
        time.sleep(0.01)

    results = timer.results()
    assert len(results) == 1
    assert results[0].name == "block_task"
    assert results[0].elapsed_seconds >= 0.01

def test_timer_duplicate_start_raises():
    timer = PerformanceTimer()
    timer.start("task")
    with pytest.raises(PerformanceError):
        timer.start("task")

def test_timer_stop_without_start_raises():
    timer = PerformanceTimer()
    with pytest.raises(PerformanceError):
        timer.stop("nonexistent")
