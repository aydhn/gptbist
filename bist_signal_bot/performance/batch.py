import math
import logging
from typing import Any

from bist_signal_bot.performance.models import (
    BatchTuningRecommendation, WorkloadType, ResourceSnapshot, ConcurrencyMode
)
from bist_signal_bot.config.settings import Settings

class BatchTuner:
    def __init__(self, settings: Settings | None = None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()
        self.logger = logging.getLogger("bist_signal_bot.performance.batch")

    def safe_max_workers(self, cpu_count: int | None, memory_available_mb: float | None) -> int:
        if not cpu_count:
            return 1

        workers = 1
        if cpu_count >= 4:
            workers = max(1, cpu_count // 2)

        if memory_available_mb is not None:
            # Assume each worker needs 250MB
            memory_bound_workers = max(1, int(memory_available_mb // 250))
            workers = min(workers, memory_bound_workers)

        # Hard limit from settings
        max_allowed = getattr(self.settings, "PERFORMANCE_MAX_WORKERS", 4)
        return min(workers, max_allowed)

    def recommend_for_workload(self, workload_type: WorkloadType, resource_snapshot: ResourceSnapshot, symbol_count: int) -> BatchTuningRecommendation:
        warnings = []
        batch_size = getattr(self.settings, "PERFORMANCE_DEFAULT_BATCH_SIZE", 10)
        max_batch_size = getattr(self.settings, "PERFORMANCE_MAX_BATCH_SIZE", 50)
        workers = self.safe_max_workers(resource_snapshot.cpu_count, resource_snapshot.memory_available_mb)
        mode = ConcurrencyMode.SERIAL

        if resource_snapshot.memory_percent is not None and resource_snapshot.memory_percent >= self.settings.PERFORMANCE_MEMORY_WARN_PCT:
            batch_size = max(1, batch_size // 2)
            workers = 1
            warnings.append("Memory usage is high, reducing batch size and forcing SERIAL mode.")

        if workload_type in [WorkloadType.SCANNER]:
            batch_size = min(max_batch_size, max(1, min(symbol_count, batch_size)))
            if workers > 1:
                mode = ConcurrencyMode.THREADS

        elif workload_type in [WorkloadType.BACKTEST, WorkloadType.OPTIMIZATION]:
            batch_size = 1 # Backtest usually runs per symbol
            if workload_type == WorkloadType.OPTIMIZATION:
                if workers > 1:
                    mode = ConcurrencyMode.PROCESSES # Computation heavy

        elif workload_type in [WorkloadType.ML_TRAINING, WorkloadType.ML_DATASET]:
            batch_size = max(1, batch_size // 2)
            workers = 1
            mode = ConcurrencyMode.SERIAL
            warnings.append("ML workloads are memory intensive, forcing SERIAL mode and small batch size.")

        reason = f"Recommended based on {resource_snapshot.cpu_count} CPUs and {resource_snapshot.memory_available_mb or 'unknown'}MB available memory."

        return BatchTuningRecommendation(
            workload_type=workload_type,
            recommended_batch_size=batch_size,
            recommended_max_workers=workers,
            recommended_concurrency_mode=mode,
            reason=reason,
            warnings=warnings
        )

    def chunk_symbols(self, symbols: list[str], batch_size: int) -> list[list[str]]:
        if batch_size <= 0:
            return [symbols]
        return [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]

    def validate_concurrency_settings(self, mode: ConcurrencyMode, max_workers: int) -> None:
        if max_workers <= 0:
            raise ValueError("max_workers must be positive")
        if mode == ConcurrencyMode.SERIAL and max_workers > 1:
            self.logger.warning("Concurrency mode is SERIAL but max_workers > 1. Workers will be ignored.")
