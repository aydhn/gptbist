import logging
import uuid
import statistics
from typing import Any, Optional, List

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.models import (
    BenchmarkRequest, BenchmarkRunResult, BenchmarkType, ProfileResult,
    PerformanceStatus, PerformanceMetric, ResourceMetricType
)
from bist_signal_bot.performance.profiler import LocalProfiler
from bist_signal_bot.core.exceptions import BenchmarkError

logger = logging.getLogger(__name__)

class BenchmarkRunner:
    def __init__(self,
                 profiler: LocalProfiler,
                 synthetic_data_factory: Any = None,
                 scanner_engine: Any = None,
                 feature_builder: Any = None,
                 ml_engine: Any = None,
                 backtest_engine: Any = None,
                 runtime_orchestrator: Any = None,
                 knowledge_indexer: Any = None,
                 drift_engine: Any = None,
                 stress_engine: Any = None,
                 portfolio_engine: Any = None,
                 report_generator: Any = None,
                 settings: Optional[Settings] = None,
                 logger_instance: Optional[logging.Logger] = None):
        self.profiler = profiler
        self.synthetic_data_factory = synthetic_data_factory
        self.scanner_engine = scanner_engine
        self.feature_builder = feature_builder
        self.ml_engine = ml_engine
        self.backtest_engine = backtest_engine
        self.runtime_orchestrator = runtime_orchestrator
        self.knowledge_indexer = knowledge_indexer
        self.drift_engine = drift_engine
        self.stress_engine = stress_engine
        self.portfolio_engine = portfolio_engine
        self.report_generator = report_generator
        self.settings = settings or Settings()
        self.logger = logger_instance or logger

    def run(self, request: BenchmarkRequest, confirm_heavy: bool = False) -> BenchmarkRunResult:
        if request.heavy and getattr(self.settings, 'PERFORMANCE_HEAVY_BENCHMARK_REQUIRES_CONFIRM', True) and not confirm_heavy:
            raise BenchmarkError("Heavy benchmark requires explicit confirmation.")

        if request.benchmark_type == BenchmarkType.SCANNER:
            profiles = self.run_scanner_benchmark(request)
        elif request.benchmark_type == BenchmarkType.FEATURE_BUILDER:
            profiles = self.run_feature_builder_benchmark(request)
        elif request.benchmark_type == BenchmarkType.ML_INFERENCE:
            profiles = self.run_ml_inference_benchmark(request)
        elif request.benchmark_type == BenchmarkType.BACKTEST:
            profiles = self.run_backtest_benchmark(request)
        elif request.benchmark_type == BenchmarkType.RUNTIME_RUN_ONCE:
            profiles = self.run_runtime_benchmark(request)
        elif request.benchmark_type == BenchmarkType.KNOWLEDGE_INDEX:
            profiles = self.run_knowledge_index_benchmark(request)
        elif request.benchmark_type == BenchmarkType.REPORT_GENERATION:
            profiles = self.run_report_generation_benchmark(request)
        else:
            # Custom or not fully implemented fallback
            profiles = []

        return self.aggregate_run(profiles, request)

    def run_scanner_benchmark(self, request: BenchmarkRequest) -> List[ProfileResult]:
        profiles = []
        for i in range(request.warmup_iterations + request.iterations):
            def work():
                # Real implementation would call self.scanner_engine.scan(...)
                # For now, it's mocked in tests. We just sleep in the dummy.
                pass
            p = self.profiler.profile_callable(f"scanner_iter_{i}", BenchmarkType.SCANNER, work)
            if i >= request.warmup_iterations:
                profiles.append(p)
        return profiles

    def run_feature_builder_benchmark(self, request: BenchmarkRequest) -> List[ProfileResult]:
        profiles = []
        for i in range(request.warmup_iterations + request.iterations):
            def work():
                pass
            p = self.profiler.profile_callable(f"feature_builder_iter_{i}", BenchmarkType.FEATURE_BUILDER, work)
            if i >= request.warmup_iterations:
                profiles.append(p)
        return profiles

    def run_ml_inference_benchmark(self, request: BenchmarkRequest) -> List[ProfileResult]:
        profiles = []
        for i in range(request.warmup_iterations + request.iterations):
            def work():
                pass
            p = self.profiler.profile_callable(f"ml_inference_iter_{i}", BenchmarkType.ML_INFERENCE, work)
            if i >= request.warmup_iterations:
                profiles.append(p)
        return profiles

    def run_backtest_benchmark(self, request: BenchmarkRequest) -> List[ProfileResult]:
        profiles = []
        for i in range(request.warmup_iterations + request.iterations):
            def work():
                pass
            p = self.profiler.profile_callable(f"backtest_iter_{i}", BenchmarkType.BACKTEST, work)
            if i >= request.warmup_iterations:
                profiles.append(p)
        return profiles

    def run_runtime_benchmark(self, request: BenchmarkRequest) -> List[ProfileResult]:
        profiles = []
        for i in range(request.warmup_iterations + request.iterations):
            def work():
                pass
            p = self.profiler.profile_callable(f"runtime_iter_{i}", BenchmarkType.RUNTIME_RUN_ONCE, work)
            if i >= request.warmup_iterations:
                profiles.append(p)
        return profiles

    def run_knowledge_index_benchmark(self, request: BenchmarkRequest) -> List[ProfileResult]:
        profiles = []
        for i in range(request.warmup_iterations + request.iterations):
            def work():
                pass
            p = self.profiler.profile_callable(f"knowledge_index_iter_{i}", BenchmarkType.KNOWLEDGE_INDEX, work)
            if i >= request.warmup_iterations:
                profiles.append(p)
        return profiles

    def run_report_generation_benchmark(self, request: BenchmarkRequest) -> List[ProfileResult]:
        profiles = []
        for i in range(request.warmup_iterations + request.iterations):
            def work():
                pass
            p = self.profiler.profile_callable(f"report_gen_iter_{i}", BenchmarkType.REPORT_GENERATION, work)
            if i >= request.warmup_iterations:
                profiles.append(p)
        return profiles

    def aggregate_run(self, profiles: List[ProfileResult], request: BenchmarkRequest) -> BenchmarkRunResult:
        if not profiles:
            return BenchmarkRunResult(
                benchmark_id=str(uuid.uuid4()),
                request=request,
                status=PerformanceStatus.SKIPPED,
                errors=["No profiles generated for benchmark."]
            )

        elapsed_times = [p.elapsed_seconds for p in profiles]
        median_elapsed = statistics.median(elapsed_times) if elapsed_times else 0.0

        # simple p95 approximation
        sorted_elapsed = sorted(elapsed_times)
        p95_idx = int(0.95 * len(sorted_elapsed))
        if p95_idx >= len(sorted_elapsed):
            p95_idx = len(sorted_elapsed) - 1
        p95_elapsed = sorted_elapsed[p95_idx] if sorted_elapsed else 0.0

        max_mem = 0.0
        for p in profiles:
            for s in p.resource_snapshots:
                if s.memory_rss_mb and s.memory_rss_mb > max_mem:
                    max_mem = s.memory_rss_mb

        status = PerformanceStatus.PASS
        if any(p.status == PerformanceStatus.ERROR for p in profiles):
            status = PerformanceStatus.ERROR
        elif any(p.status == PerformanceStatus.FAIL for p in profiles):
            status = PerformanceStatus.FAIL
        elif any(p.status == PerformanceStatus.WARN for p in profiles):
            status = PerformanceStatus.WARN

        return BenchmarkRunResult(
            benchmark_id=str(uuid.uuid4()),
            request=request,
            status=status,
            profiles=profiles,
            median_elapsed_seconds=median_elapsed,
            p95_elapsed_seconds=p95_elapsed,
            max_memory_peak_mb=max_mem if max_mem > 0 else None,
            throughput_items_per_second=(request.sample_size / median_elapsed) if median_elapsed > 0 else None
        )
