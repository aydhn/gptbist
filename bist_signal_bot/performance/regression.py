import uuid
from typing import Optional, Dict, List

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.models import (
    BenchmarkRunResult, PerformanceBaseline, PerformanceRegressionResult, PerformanceStatus
)

class PerformanceRegressionChecker:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def metric_change_pct(self, current: float, baseline: float) -> Optional[float]:
        if baseline == 0.0:
            return None
        return ((current - baseline) / baseline) * 100.0

    def detect_regressions(self, changes: Dict[str, float], thresholds: Optional[Dict[str, float]] = None) -> List[str]:
        regressions = []
        if not thresholds:
            thresholds = {
                "median_elapsed_seconds": getattr(self.settings, 'PERFORMANCE_ELAPSED_WARN_PCT', 25.0),
                "p95_elapsed_seconds": getattr(self.settings, 'PERFORMANCE_ELAPSED_WARN_PCT', 25.0),
                "max_memory_peak_mb": getattr(self.settings, 'PERFORMANCE_MEMORY_WARN_PCT', 25.0)
            }

        for metric, pct in changes.items():
            if pct > 0:  # Increase in time or memory is bad
                thresh = thresholds.get(metric)
                if thresh is not None and pct > thresh:
                    regressions.append(f"{metric} degraded by {pct:.1f}% (threshold: {thresh:.1f}%)")
        return regressions

    def detect_improvements(self, changes: Dict[str, float]) -> List[str]:
        improvements = []
        for metric, pct in changes.items():
            # A negative percentage for time/memory is an improvement
            if pct < -10.0: # Arbitrary small threshold to ignore noise
                improvements.append(f"{metric} improved by {abs(pct):.1f}%")
        return improvements

    def compare(self, result: BenchmarkRunResult, baseline: PerformanceBaseline) -> PerformanceRegressionResult:
        changes = {}

        # Current metrics
        c_median = result.median_elapsed_seconds or 0.0
        c_p95 = result.p95_elapsed_seconds or 0.0
        c_mem = result.max_memory_peak_mb or 0.0
        c_tps = result.throughput_items_per_second or 0.0

        # Baseline metrics
        b_median = baseline.metrics.get("median_elapsed_seconds", 0.0)
        b_p95 = baseline.metrics.get("p95_elapsed_seconds", 0.0)
        b_mem = baseline.metrics.get("max_memory_peak_mb", 0.0)
        b_tps = baseline.metrics.get("throughput_items_per_second", 0.0)

        c1 = self.metric_change_pct(c_median, b_median)
        if c1 is not None: changes["median_elapsed_seconds"] = c1

        c2 = self.metric_change_pct(c_p95, b_p95)
        if c2 is not None: changes["p95_elapsed_seconds"] = c2

        c3 = self.metric_change_pct(c_mem, b_mem)
        if c3 is not None: changes["max_memory_peak_mb"] = c3

        c4 = self.metric_change_pct(c_tps, b_tps)
        if c4 is not None:
            # TPS increase is good, so we invert the sign for the regression logic
            # (where positive = bad)
            changes["throughput_items_per_second_inverted"] = -c4

        thresholds = {
            "median_elapsed_seconds": getattr(self.settings, 'PERFORMANCE_ELAPSED_WARN_PCT', 25.0),
            "p95_elapsed_seconds": getattr(self.settings, 'PERFORMANCE_ELAPSED_WARN_PCT', 25.0),
            "max_memory_peak_mb": getattr(self.settings, 'PERFORMANCE_MEMORY_WARN_PCT', 25.0),
            "throughput_items_per_second_inverted": getattr(self.settings, 'PERFORMANCE_ELAPSED_WARN_PCT', 25.0)
        }

        fail_thresholds = {
            "median_elapsed_seconds": getattr(self.settings, 'PERFORMANCE_ELAPSED_FAIL_PCT', 50.0),
            "p95_elapsed_seconds": getattr(self.settings, 'PERFORMANCE_ELAPSED_FAIL_PCT', 50.0),
            "max_memory_peak_mb": getattr(self.settings, 'PERFORMANCE_MEMORY_FAIL_PCT', 50.0),
            "throughput_items_per_second_inverted": getattr(self.settings, 'PERFORMANCE_ELAPSED_FAIL_PCT', 50.0)
        }

        regressions = self.detect_regressions(changes, thresholds)
        improvements = self.detect_improvements(changes)

        # Check fail conditions
        fails = self.detect_regressions(changes, fail_thresholds)

        status = PerformanceStatus.PASS
        if fails:
            status = PerformanceStatus.FAIL
        elif regressions:
            status = PerformanceStatus.WARN

        return PerformanceRegressionResult(
            regression_id=str(uuid.uuid4()),
            benchmark_id=result.benchmark_id,
            baseline_id=baseline.baseline_id,
            status=status,
            metric_changes_pct=changes,
            regressions=regressions,
            improvements=improvements
        )
