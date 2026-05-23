import logging
import uuid
import datetime
import inspect
import copy
from typing import Any, Callable, Dict, List, Optional
from contextlib import contextmanager

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.models import (
    BenchmarkType, PerformanceMetric, PerformanceStatus, ProfileResult, ProfileSpan, ResourceMetricType
)
from bist_signal_bot.performance.timer import PerformanceTimer
from bist_signal_bot.performance.resources import ResourceSampler
from bist_signal_bot.security.redaction import SecretRedactor

logger = logging.getLogger(__name__)

class LocalProfiler:
    def __init__(self, timer: Optional[PerformanceTimer] = None, sampler: Optional[ResourceSampler] = None, settings: Optional[Settings] = None, logger_instance: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.timer = timer or PerformanceTimer()
        self.sampler = sampler or ResourceSampler(self.settings)
        self.logger = logger_instance or logger
        self.redactor = SecretRedactor()

    def profile_callable(self, name: str, benchmark_type: BenchmarkType, func: Callable, *args, **kwargs) -> ProfileResult:
        module = inspect.getmodule(func).__name__ if inspect.getmodule(func) else None

        def wrapped_func():
            with self.timer.span(name, module=module) as span:
                mem_before = self.sampler.memory_rss_mb()
                span.memory_before_mb = mem_before
                try:
                    result = func(*args, **kwargs)
                    span.metadata["status"] = "success"
                    return result
                except Exception as e:
                    span.metadata["status"] = "error"
                    span.metadata["error"] = str(e)
                    raise
                finally:
                    mem_after = self.sampler.memory_rss_mb()
                    span.memory_after_mb = mem_after
                    if mem_before is not None and mem_after is not None:
                        span.memory_delta_mb = mem_after - mem_before

        interval = getattr(self.settings, 'PERFORMANCE_RESOURCE_SAMPLE_INTERVAL_SECONDS', 0.5)

        try:
            _, snapshots = self.sampler.sample_during(wrapped_func, interval_seconds=interval)
            status = PerformanceStatus.PASS
        except Exception:
            # We don't have a specific way to get snapshots if it blows up instantly, but sample_during returns them anyway?
            # Actually sample_during returns a tuple, so if it raises, we don't get the snapshots.
            # We can grab one manually.
            snapshots = [self.sampler.snapshot()]
            status = PerformanceStatus.ERROR

        result = self.timer.build_profile_result(benchmark_type)
        result.resource_snapshots = snapshots
        result.status = status

        if status == PerformanceStatus.ERROR:
            result.errors.append("Profiled callable raised an exception.")

        result.metrics = self.aggregate_metrics(result)
        if status != PerformanceStatus.ERROR:
            result.status = self.status_from_metrics(result.metrics)

        return self.redact_profile(result)

    @contextmanager
    def profile_context(self, name: str, benchmark_type: BenchmarkType):
        # Starts a timing context and returns the profile result upon exit via a callback or just capturing.
        # It's a bit tricky to return a full ProfileResult while yielding, so we store it in a dict they can read.
        context_result = {"profile": None}

        mem_before = self.sampler.memory_rss_mb()
        snapshots = [self.sampler.snapshot()]

        with self.timer.span(name) as span:
            span.memory_before_mb = mem_before
            try:
                yield context_result
                span.metadata["status"] = "success"
                status = PerformanceStatus.PASS
            except Exception as e:
                span.metadata["status"] = "error"
                span.metadata["error"] = str(e)
                status = PerformanceStatus.ERROR
                raise
            finally:
                mem_after = self.sampler.memory_rss_mb()
                span.memory_after_mb = mem_after
                if mem_before is not None and mem_after is not None:
                    span.memory_delta_mb = mem_after - mem_before
                snapshots.append(self.sampler.snapshot())

                profile = self.timer.build_profile_result(benchmark_type)
                profile.resource_snapshots = snapshots
                profile.status = status
                profile.metrics = self.aggregate_metrics(profile)
                if status != PerformanceStatus.ERROR:
                    profile.status = self.status_from_metrics(profile.metrics)

                context_result["profile"] = self.redact_profile(profile)

    def aggregate_metrics(self, profile: ProfileResult) -> List[PerformanceMetric]:
        metrics = []

        metrics.append(PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            metric_type=ResourceMetricType.WALL_TIME_SECONDS,
            name="Total Elapsed Time",
            value=profile.elapsed_seconds,
            unit="s",
            status=PerformanceStatus.UNKNOWN
        ))

        if profile.resource_snapshots:
            rss_values = [s.memory_rss_mb for s in profile.resource_snapshots if s.memory_rss_mb is not None]
            if rss_values:
                peak_mb = max(rss_values)
                metrics.append(PerformanceMetric(
                    metric_id=str(uuid.uuid4()),
                    metric_type=ResourceMetricType.MEMORY_PEAK_MB,
                    name="Peak Memory Usage",
                    value=peak_mb,
                    unit="MB",
                    status=PerformanceStatus.UNKNOWN
                ))

            cpu_values = [s.cpu_percent for s in profile.resource_snapshots if s.cpu_percent is not None]
            if cpu_values:
                metrics.append(PerformanceMetric(
                    metric_id=str(uuid.uuid4()),
                    metric_type=ResourceMetricType.CPU_PERCENT,
                    name="Average CPU Usage",
                    value=sum(cpu_values) / len(cpu_values),
                    unit="%",
                    status=PerformanceStatus.UNKNOWN
                ))

        return metrics

    def status_from_metrics(self, metrics: List[PerformanceMetric]) -> PerformanceStatus:
        # Simplistic logic: if we set a threshold_fail and it crossed it, FAIL. If threshold_warn, WARN.
        # But this method might just check span times against settings

        has_warn = False
        # Currently metrics don't have thresholds populated by default in aggregate_metrics.
        # We can just return PASS for now, BottleneckAnalyzer handles deep logic.
        for m in metrics:
            if m.status == PerformanceStatus.FAIL:
                return PerformanceStatus.FAIL
            if m.status == PerformanceStatus.WARN:
                has_warn = True

        return PerformanceStatus.WARN if has_warn else PerformanceStatus.PASS

    def redact_profile(self, profile: ProfileResult) -> ProfileResult:
        # Redact any secrets in metadata using SecretRedactor
        redacted = copy.deepcopy(profile)
        redacted.metadata = self.redactor.redact_dict(redacted.metadata)
        for span in redacted.spans:
            span.metadata = self.redactor.redact_dict(span.metadata)
        for snap in redacted.resource_snapshots:
            snap.metadata = self.redactor.redact_dict(snap.metadata)
        return redacted

