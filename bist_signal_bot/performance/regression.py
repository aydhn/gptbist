import uuid
from typing import Any, Optional

from bist_signal_bot.performance.models import (
    BenchmarkResult,
    PerformanceRegressionFinding,
    PerformanceStatus,
)
from bist_signal_bot.core.exceptions import BistSignalBotError

class PerformanceRegressionError(BistSignalBotError):
    pass

class PerformanceRegressionDetector:
    def __init__(self, settings: Any = None, base_dir: Any = None):
        self.settings = settings
        self.base_dir = base_dir

        self.enabled = True
        self.warn_pct = 20.0
        self.fail_pct = 50.0
        self.baseline_required = False

        if self.settings:
            self.enabled = getattr(self.settings, "PERFORMANCE_REGRESSION_ENABLED", self.enabled)
            self.warn_pct = getattr(self.settings, "PERFORMANCE_REGRESSION_WARN_PCT", self.warn_pct)
            self.fail_pct = getattr(self.settings, "PERFORMANCE_REGRESSION_FAIL_PCT", self.fail_pct)
            self.baseline_required = getattr(self.settings, "PERFORMANCE_BENCHMARK_BASELINE_REQUIRED", self.baseline_required)

    def detect_regressions(self, current: list[BenchmarkResult], baseline: Optional[list[BenchmarkResult]] = None) -> list[PerformanceRegressionFinding]:
        if not self.enabled:
            return []

        findings = []
        baseline_map = {b.scenario: b for b in (baseline or [])}

        for c in current:
            b = baseline_map.get(c.scenario)
            if not b:
                if self.baseline_required:
                    findings.append(
                        PerformanceRegressionFinding(
                            regression_id=str(uuid.uuid4()),
                            scenario=c.scenario,
                            threshold_pct=self.fail_pct,
                            status=PerformanceStatus.FAIL,
                            message=f"Baseline required but not found for scenario {c.scenario.value}"
                        )
                    )
                else:
                    findings.append(
                        PerformanceRegressionFinding(
                            regression_id=str(uuid.uuid4()),
                            scenario=c.scenario,
                            threshold_pct=self.warn_pct,
                            status=PerformanceStatus.WATCH,
                            message=f"Insufficient data: No baseline found for scenario {c.scenario.value}"
                        )
                    )
                continue

            finding = self.compare_result(c, b)
            findings.append(finding)

        return findings

    def load_baseline(self) -> list[BenchmarkResult]:
        # Typically this would load from a store.
        # Returning an empty list for now.
        return []

    def compare_result(self, current: BenchmarkResult, baseline: BenchmarkResult) -> PerformanceRegressionFinding:
        c_elapsed = current.elapsed_seconds
        b_elapsed = baseline.elapsed_seconds

        delta = self.delta_pct(c_elapsed, b_elapsed)
        status = self.classify_regression(delta, self.fail_pct if delta is not None and delta > self.fail_pct else self.warn_pct)

        msg = f"Runtime changed by {delta:.1f}% compared to baseline" if delta is not None else "Could not calculate delta"

        return PerformanceRegressionFinding(
            regression_id=str(uuid.uuid4()),
            scenario=current.scenario,
            baseline_value=b_elapsed,
            current_value=c_elapsed,
            delta_pct=delta,
            threshold_pct=self.fail_pct if status == PerformanceStatus.FAIL else self.warn_pct,
            status=status,
            message=msg
        )

    def delta_pct(self, current: Optional[float], baseline: Optional[float]) -> Optional[float]:
        if current is None or baseline is None or baseline == 0:
            return None
        return ((current - baseline) / baseline) * 100.0

    def classify_regression(self, delta_pct: Optional[float], threshold_pct: float) -> PerformanceStatus:
        if delta_pct is None:
            return PerformanceStatus.WATCH
        if delta_pct > self.fail_pct:
            return PerformanceStatus.FAIL
        if delta_pct > self.warn_pct:
            return PerformanceStatus.DEGRADED
        return PerformanceStatus.PASS
