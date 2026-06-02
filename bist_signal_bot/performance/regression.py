from bist_signal_bot.performance.models import PerformanceRegressionFinding, BenchmarkResult, PerformanceStatus
import datetime

class PerformanceRegressionDetector:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def detect_regressions(self, current: list[BenchmarkResult], baseline: list[BenchmarkResult] | None = None) -> list[PerformanceRegressionFinding]:
        if not baseline:
            return []

        baseline_map = {b.scenario: b for b in baseline}
        findings = []

        for c in current:
            if c.scenario in baseline_map:
                f = self.compare_result(c, baseline_map[c.scenario])
                if f:
                    findings.append(f)
        return findings

    def load_baseline(self) -> list[BenchmarkResult]:
        return []

    def compare_result(self, current: BenchmarkResult, baseline: BenchmarkResult) -> PerformanceRegressionFinding | None:
        delta = self.delta_pct(current.elapsed_seconds, baseline.elapsed_seconds)
        if delta is None:
            return None

        threshold = 25.0
        status = self.classify_regression(delta, threshold)

        return PerformanceRegressionFinding(
            regression_id=f"reg_{current.benchmark_id}",
            scenario=current.scenario,
            baseline_value=baseline.elapsed_seconds,
            current_value=current.elapsed_seconds,
            delta_pct=delta,
            threshold_pct=threshold,
            status=status,
            message=f"Performance delta: {delta}%"
        )

    def delta_pct(self, current: float | None, baseline: float | None) -> float | None:
        if current is None or baseline is None or baseline == 0:
            return None
        return ((current - baseline) / baseline) * 100.0

    def classify_regression(self, delta_pct: float | None, threshold_pct: float) -> PerformanceStatus:
        if delta_pct is None:
            return PerformanceStatus.UNKNOWN
        if delta_pct >= threshold_pct * 2:
            return PerformanceStatus.FAIL
        if delta_pct > threshold_pct:
            return PerformanceStatus.DEGRADED
        return PerformanceStatus.PASS
