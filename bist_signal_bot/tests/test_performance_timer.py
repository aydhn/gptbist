import pytest
import time
from bist_signal_bot.performance.timer import PerformanceTimer
from bist_signal_bot.performance.models import BenchmarkType

def test_timer_context_manager():
    timer = PerformanceTimer()
    with timer.span("test_span") as span:
        time.sleep(0.01)

    assert span.elapsed_seconds > 0
    assert span.finished_at is not None
    assert len(timer.current_spans()) == 1

def test_timer_exception_closes_span():
    timer = PerformanceTimer()
    try:
        with timer.span("fail_span") as span:
            raise ValueError("test")
    except ValueError:
        pass

    spans = timer.current_spans()
    assert len(spans) == 1
    assert spans[0].finished_at is not None

