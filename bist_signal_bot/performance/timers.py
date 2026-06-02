import datetime
import contextlib
import time
from typing import Generator
from bist_signal_bot.performance.models import TimingMeasurement, PerformanceStatus

class PerformanceTimer:
    def __init__(self, settings=None, clock=None):
        self.settings = settings
        self.clock = clock or time.time

    def start(self, name: str) -> TimingMeasurement:
        now = datetime.datetime.now(datetime.timezone.utc)
        return TimingMeasurement(
            timing_id=f"timing_{int(self.clock() * 1000)}",
            name=name,
            started_at=now,
            status=PerformanceStatus.UNKNOWN,
            metadata={"start_time_unix": self.clock()}
        )

    def finish(self, measurement: TimingMeasurement, status: PerformanceStatus = PerformanceStatus.PASS) -> TimingMeasurement:
        now = datetime.datetime.now(datetime.timezone.utc)
        measurement.finished_at = now
        start_time_unix = measurement.metadata.get("start_time_unix")
        if start_time_unix is not None:
            measurement.elapsed_seconds = max(0.0, self.clock() - start_time_unix)
        else:
            measurement.elapsed_seconds = max(0.0, (now - measurement.started_at).total_seconds())
        measurement.status = status
        return measurement

    @contextlib.contextmanager
    def measure(self, name: str) -> Generator[TimingMeasurement, None, None]:
        measurement = self.start(name)
        try:
            yield measurement
            self.finish(measurement, status=PerformanceStatus.PASS)
        except Exception as e:
            measurement.warnings.append(f"Error during execution: {str(e)}")
            self.finish(measurement, status=PerformanceStatus.FAIL)
            raise

    def elapsed(self, started_at: datetime.datetime, finished_at: datetime.datetime | None = None) -> float:
        end = finished_at or datetime.datetime.now(datetime.timezone.utc)
        return max(0.0, (end - started_at).total_seconds())

    def classify_elapsed(self, elapsed_seconds: float | None, threshold_seconds: float | None = None) -> PerformanceStatus:
        if elapsed_seconds is None or elapsed_seconds < 0:
            return PerformanceStatus.UNKNOWN
        if threshold_seconds is None:
            return PerformanceStatus.PASS
        if elapsed_seconds > threshold_seconds * 2:
            return PerformanceStatus.FAIL
        if elapsed_seconds > threshold_seconds:
            return PerformanceStatus.SLOW
        return PerformanceStatus.PASS
