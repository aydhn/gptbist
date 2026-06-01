from typing import Any, Optional
from pathlib import Path

from bist_signal_bot.performance.storage import PerformanceStore
from bist_signal_bot.performance.timers import PerformanceTimer
from bist_signal_bot.performance.profiler import LocalPerformanceProfiler
from bist_signal_bot.performance.resource_budget import ResourceBudgetManager
from bist_signal_bot.performance.cache import LocalCacheManager
from bist_signal_bot.performance.benchmark import PerformanceBenchmarkRunner
from bist_signal_bot.performance.bottlenecks import BottleneckAnalyzer
from bist_signal_bot.performance.regression import PerformanceRegressionDetector

def create_performance_store(settings: Any = None, base_dir: Optional[Path] = None) -> PerformanceStore:
    return PerformanceStore(settings=settings, base_dir=base_dir)

def create_performance_timer(settings: Any = None) -> PerformanceTimer:
    return PerformanceTimer()

def create_local_performance_profiler(settings: Any = None, base_dir: Optional[Path] = None) -> LocalPerformanceProfiler:
    return LocalPerformanceProfiler(settings=settings, base_dir=base_dir)

def create_resource_budget_manager(settings: Any = None, base_dir: Optional[Path] = None) -> ResourceBudgetManager:
    return ResourceBudgetManager(settings=settings, base_dir=base_dir)

def create_local_cache_manager(settings: Any = None, base_dir: Optional[Path] = None) -> LocalCacheManager:
    return LocalCacheManager(settings=settings, base_dir=base_dir)

def create_performance_benchmark_runner(settings: Any = None, base_dir: Optional[Path] = None) -> PerformanceBenchmarkRunner:
    return PerformanceBenchmarkRunner(settings=settings, base_dir=base_dir)

def create_bottleneck_analyzer(settings: Any = None, base_dir: Optional[Path] = None) -> BottleneckAnalyzer:
    return BottleneckAnalyzer(settings=settings, base_dir=base_dir)

def create_performance_regression_detector(settings: Any = None, base_dir: Optional[Path] = None) -> PerformanceRegressionDetector:
    return PerformanceRegressionDetector(settings=settings, base_dir=base_dir)

