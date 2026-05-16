from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.resources import ResourceMonitor
from bist_signal_bot.performance.cache import CacheInspector
from bist_signal_bot.performance.benchmarks import PerformanceBenchmarkRunner
from bist_signal_bot.performance.storage import PerformanceReportStore
from bist_signal_bot.performance.batch import BatchTuner
from bist_signal_bot.performance.profiler import FunctionProfiler
from bist_signal_bot.performance.recommendations import PerformanceRecommendationEngine
from bist_signal_bot.performance.timer import PerformanceTimer

def create_resource_monitor(settings: Settings | None = None) -> ResourceMonitor:
    return ResourceMonitor(settings)

def create_cache_inspector(settings: Settings | None = None, base_dir: Path | None = None) -> CacheInspector:
    return CacheInspector(settings, base_dir)

def create_performance_benchmark_runner(settings: Settings | None = None) -> PerformanceBenchmarkRunner:
    return PerformanceBenchmarkRunner(settings)

def create_performance_report_store(settings: Settings | None = None, base_dir: Path | None = None) -> PerformanceReportStore:
    return PerformanceReportStore(settings, base_dir)

def create_batch_tuner(settings: Settings | None = None) -> BatchTuner:
    return BatchTuner(settings)

def create_function_profiler(settings: Settings | None = None) -> FunctionProfiler:
    return FunctionProfiler(settings)

def create_recommendation_engine() -> PerformanceRecommendationEngine:
    return PerformanceRecommendationEngine()

def create_performance_timer() -> PerformanceTimer:
    return PerformanceTimer()
