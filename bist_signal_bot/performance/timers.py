import contextlib
import time
import uuid
from datetime import datetime, UTC
from typing import Any, Generator, Optional, Callable
from pydantic import BaseModel

from bist_signal_bot.performance.models import (
    PerformanceStatus,
    TimingMeasurement,
)
from bist_signal_bot.core.exceptions import BistSignalBotError

class PerformanceTimerError(BistSignalBotError):
    pass

class PerformanceTimer:
    def __init__(self, clock_fn: Optional[Callable[[], float]] = None):
        self._clock_fn = clock_fn or time.time
        self._dt_clock_fn = lambda: datetime.now(UTC)

    def start(self, name: str) -> TimingMeasurement:
        return TimingMeasurement(
            timing_id=str(uuid.uuid4()),
            name=name,
            started_at=self._dt_clock_fn(),
            status=PerformanceStatus.UNKNOWN,
            metadata={"_start_clock": self._clock_fn()}
        )

    def finish(self, measurement: TimingMeasurement, status: PerformanceStatus = PerformanceStatus.PASS) -> TimingMeasurement:
        finish_clock = self._clock_fn()
        finished_dt = self._dt_clock_fn()
        start_clock = measurement.metadata.get("_start_clock")

        elapsed = None
        if start_clock is not None:
            elapsed = max(0.0, finish_clock - start_clock)

        measurement.finished_at = finished_dt
        measurement.elapsed_seconds = elapsed
        measurement.status = status

        # Keep metadata but remove temporary internal variables
        measurement.metadata.pop("_start_clock", None)
        return measurement

    @contextlib.contextmanager
    def measure(self, name: str) -> Generator[TimingMeasurement, None, None]:
        measurement = self.start(name)
        try:
            yield measurement
        finally:
            self.finish(measurement)

    def elapsed(self, started_at: datetime, finished_at: Optional[datetime] = None) -> float:
        end = finished_at or self._dt_clock_fn()
        delta = end - started_at
        return max(0.0, delta.total_seconds())

    def classify_elapsed(self, elapsed_seconds: Optional[float], threshold_seconds: Optional[float] = None) -> PerformanceStatus:
        if elapsed_seconds is None:
            return PerformanceStatus.UNKNOWN
        if elapsed_seconds < 0:
            return PerformanceStatus.UNKNOWN
        if threshold_seconds is not None and elapsed_seconds > threshold_seconds:
            return PerformanceStatus.SLOW
        return PerformanceStatus.PASS
