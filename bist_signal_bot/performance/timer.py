import time
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Any, Generator
import logging

from bist_signal_bot.performance.models import TimerResult
from bist_signal_bot.core.exceptions import PerformanceError

class PerformanceTimer:
    def __init__(self, logger: logging.Logger | None = None):
        self._logger = logger or logging.getLogger("bist_signal_bot.performance.timer")
        self._active_timers: dict[str, dict[str, Any]] = {}
        self._results: list[TimerResult] = []

    def start(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        if name in self._active_timers:
            raise PerformanceError(f"Timer '{name}' is already active.")

        self._active_timers[name] = {
            "started_at": datetime.now(timezone.utc),
            "start_time": time.perf_counter(),
            "metadata": metadata or {}
        }
        self._logger.debug(f"Timer started: {name}")

    def stop(self, name: str) -> TimerResult:
        if name not in self._active_timers:
            self._logger.warning(f"Timer '{name}' was not active.")
            raise PerformanceError(f"Timer '{name}' was not active.")

        active = self._active_timers.pop(name)
        finished_at = datetime.now(timezone.utc)
        end_time = time.perf_counter()

        result = TimerResult(
            name=name,
            started_at=active["started_at"],
            finished_at=finished_at,
            elapsed_seconds=end_time - active["start_time"],
            metadata=active["metadata"]
        )
        self._results.append(result)
        self._logger.debug(f"Timer stopped: {name} ({result.elapsed_seconds:.4f}s)")
        return result

    @contextmanager
    def time_block(self, name: str, metadata: dict[str, Any] | None = None) -> Generator[None, None, None]:
        self.start(name, metadata)
        try:
            yield
        finally:
            if name in self._active_timers:
                self.stop(name)

    def results(self) -> list[TimerResult]:
        # Handle warning for active unstopped timers
        for name in list(self._active_timers.keys()):
            self._logger.warning(f"Timer '{name}' was never stopped.")
        return list(self._results)

    def clear(self) -> None:
        self._active_timers.clear()
        self._results.clear()
