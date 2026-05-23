from typing import Optional
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.resources import ResourceSampler
from bist_signal_bot.performance.profiler import LocalProfiler
from bist_signal_bot.performance.benchmark import BenchmarkRunner
from bist_signal_bot.performance.baseline import PerformanceBaselineManager
from bist_signal_bot.performance.regression import PerformanceRegressionChecker
from bist_signal_bot.performance.bottlenecks import BottleneckAnalyzer
from bist_signal_bot.performance.storage import PerformanceStore

def create_resource_sampler(settings: Optional[Settings] = None) -> ResourceSampler:
    return ResourceSampler(settings=settings)

def create_local_profiler(settings: Optional[Settings] = None) -> LocalProfiler:
    sampler = create_resource_sampler(settings)
    return LocalProfiler(sampler=sampler, settings=settings)

def create_benchmark_runner(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> BenchmarkRunner:
    profiler = create_local_profiler(settings)
    return BenchmarkRunner(profiler=profiler, settings=settings)

def create_baseline_manager(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> PerformanceBaselineManager:
    return PerformanceBaselineManager(settings=settings, base_dir=base_dir)

def create_regression_checker(settings: Optional[Settings] = None) -> PerformanceRegressionChecker:
    return PerformanceRegressionChecker(settings=settings)

def create_bottleneck_analyzer(settings: Optional[Settings] = None) -> BottleneckAnalyzer:
    return BottleneckAnalyzer(settings=settings)

def create_performance_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> PerformanceStore:
    return PerformanceStore(settings=settings, base_dir=base_dir)

