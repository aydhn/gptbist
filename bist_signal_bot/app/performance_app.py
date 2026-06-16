from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.storage import PerformanceStore
from bist_signal_bot.performance.timers import PerformanceTimer
from bist_signal_bot.performance.profiler import LocalPerformanceProfiler
from bist_signal_bot.performance.resource_budget import ResourceBudgetManager
from bist_signal_bot.performance.cache import LocalCacheManager
from bist_signal_bot.performance.benchmark import PerformanceBenchmarkRunner
from bist_signal_bot.performance.bottlenecks import BottleneckAnalyzer
from bist_signal_bot.performance.regression import PerformanceRegressionDetector

def create_performance_store(settings: Settings | None = None, base_dir: Path | None = None) -> PerformanceStore:
    return PerformanceStore(settings=settings, base_dir=base_dir)

def create_performance_timer(settings: Settings | None = None) -> PerformanceTimer:
    return PerformanceTimer(settings=settings)

def create_local_performance_profiler(settings: Settings | None = None, base_dir: Path | None = None) -> LocalPerformanceProfiler:
    return LocalPerformanceProfiler(settings=settings, base_dir=base_dir)

# Backwards-compatible alias: backtesting/runtime/knowledge/ml/cli import this name.
create_local_profiler = create_local_performance_profiler

def create_resource_budget_manager(settings: Settings | None = None, base_dir: Path | None = None) -> ResourceBudgetManager:
    return ResourceBudgetManager(settings=settings, base_dir=base_dir)

def create_local_cache_manager(settings: Settings | None = None, base_dir: Path | None = None) -> LocalCacheManager:
    return LocalCacheManager(settings=settings, base_dir=base_dir)

def create_performance_benchmark_runner(settings: Settings | None = None, base_dir: Path | None = None) -> PerformanceBenchmarkRunner:
    return PerformanceBenchmarkRunner(settings=settings, base_dir=base_dir)

def create_bottleneck_analyzer(settings: Settings | None = None, base_dir: Path | None = None) -> BottleneckAnalyzer:
    return BottleneckAnalyzer(settings=settings, base_dir=base_dir)

def create_performance_regression_detector(settings: Settings | None = None, base_dir: Path | None = None) -> PerformanceRegressionDetector:
    return PerformanceRegressionDetector(settings=settings, base_dir=base_dir)
