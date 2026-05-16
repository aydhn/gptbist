import time
import logging
from typing import Callable, Any
from datetime import datetime, timezone

from bist_signal_bot.performance.models import (
    PerformanceBenchmarkResult, WorkloadType, PerformanceStatus, PerformanceMetric
)
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.timer import PerformanceTimer
from bist_signal_bot.performance.resources import ResourceMonitor

class PerformanceBenchmarkRunner:
    def __init__(self, settings: Settings | None = None, timer: PerformanceTimer | None = None, resource_monitor: ResourceMonitor | None = None, logger: logging.Logger | None = None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger("bist_signal_bot.performance.benchmarks")
        self.timer = timer or PerformanceTimer()
        self.resource_monitor = resource_monitor or ResourceMonitor(self.settings)

    def benchmark_callable(self, benchmark_id: str, workload_type: WorkloadType, func: Callable[[], Any], iterations: int = 3) -> PerformanceBenchmarkResult:
        if iterations <= 0:
            iterations = self.settings.PERFORMANCE_BENCHMARK_ITERATIONS

        times = []
        status = PerformanceStatus.PASS

        for i in range(iterations):
            start = time.perf_counter()
            try:
                func()
            except Exception as e:
                self.logger.error(f"Benchmark {benchmark_id} failed on iteration {i}: {e}")
                status = PerformanceStatus.ERROR
                break
            times.append(time.perf_counter() - start)

        if not times:
            return PerformanceBenchmarkResult(
                benchmark_id=benchmark_id,
                workload_type=workload_type,
                status=PerformanceStatus.ERROR,
                iterations=iterations,
                average_seconds=0.0,
                median_seconds=0.0,
                min_seconds=0.0,
                max_seconds=0.0
            )

        times.sort()
        avg = sum(times) / len(times)
        mid = len(times) // 2
        median = times[mid] if len(times) % 2 != 0 else (times[mid - 1] + times[mid]) / 2.0

        return PerformanceBenchmarkResult(
            benchmark_id=benchmark_id,
            workload_type=workload_type,
            status=status,
            iterations=len(times),
            average_seconds=avg,
            median_seconds=median,
            min_seconds=times[0],
            max_seconds=times[-1],
            throughput_per_second=1.0 / avg if avg > 0 else 0.0
        )

    def benchmark_scan_mock(self, symbols: list[str], strategy_name: str, iterations: int = 3) -> PerformanceBenchmarkResult:
        def _mock_scan():
            # In a real scenario, this would call scanner engine with mock provider
            import pandas as pd
            import numpy as np
            for sym in symbols:
                df = pd.DataFrame(np.random.randn(100, 5), columns=['Open', 'High', 'Low', 'Close', 'Volume'])
                df['Close'].rolling(20).mean() # Mock work

        return self.benchmark_callable(
            benchmark_id=f"scan_mock_{len(symbols)}_{strategy_name}",
            workload_type=WorkloadType.SCANNER,
            func=_mock_scan,
            iterations=iterations
        )

    def benchmark_backtest_mock(self, symbol: str, strategy_name: str, iterations: int = 3) -> PerformanceBenchmarkResult:
        def _mock_backtest():
            import pandas as pd
            import numpy as np
            df = pd.DataFrame(np.random.randn(500, 5), columns=['Open', 'High', 'Low', 'Close', 'Volume'])
            df['Close'].rolling(50).mean() # Mock work

        return self.benchmark_callable(
            benchmark_id=f"backtest_mock_{symbol}_{strategy_name}",
            workload_type=WorkloadType.BACKTEST,
            func=_mock_backtest,
            iterations=iterations
        )

    def benchmark_ml_dataset_mock(self, symbols: list[str], iterations: int = 3) -> PerformanceBenchmarkResult:
        def _mock_ml():
            import pandas as pd
            import numpy as np
            for sym in symbols:
                df = pd.DataFrame(np.random.randn(500, 10), columns=[f'feat_{i}' for i in range(10)])
                df.corr() # Mock work

        return self.benchmark_callable(
            benchmark_id=f"ml_dataset_mock_{len(symbols)}",
            workload_type=WorkloadType.ML_DATASET,
            func=_mock_ml,
            iterations=iterations
        )
