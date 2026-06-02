
import uuid
from typing import Optional
from bist_signal_bot.performance.models import PerformanceRegressionFinding, BenchmarkResult, PerformanceStatus, BenchmarkScenario

class PerformanceRegressionDetector:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def detect_regressions(self, current: list[BenchmarkResult], baseline: Optional[list[BenchmarkResult]] = None) -> list[PerformanceRegressionFinding]:
        if not baseline:
            return [PerformanceRegressionFinding(
                regression_id=uuid.uuid4().hex,
                scenario=BenchmarkScenario.CUSTOM,
                threshold_pct=10.0,
                message="No baseline available",
                status=PerformanceStatus.WATCH
            )]
        regressions = []
        for c in current:
            for b in baseline:
                if c.scenario == b.scenario:
                    regressions.append(self.compare_result(c, b))
        return regressions

    def load_baseline(self) -> list[BenchmarkResult]:
        return []

    def compare_result(self, current: BenchmarkResult, baseline: BenchmarkResult) -> PerformanceRegressionFinding:
        delta = self.delta_pct(current.elapsed_seconds, baseline.elapsed_seconds)
        status = self.classify_regression(delta, 25.0)
        return PerformanceRegressionFinding(
            regression_id=uuid.uuid4().hex,
            scenario=current.scenario,
            baseline_value=baseline.elapsed_seconds,
            current_value=current.elapsed_seconds,
            delta_pct=delta,
            threshold_pct=25.0,
            status=status,
            message="Comparison complete"
        )

    def delta_pct(self, current: Optional[float], baseline: Optional[float]) -> Optional[float]:
        if current is None or baseline is None or baseline == 0:
            return None
        return ((current - baseline) / baseline) * 100.0

    def classify_regression(self, delta_pct: Optional[float], threshold_pct: float) -> PerformanceStatus:
        if delta_pct is None:
            return PerformanceStatus.UNKNOWN
        if delta_pct > threshold_pct:
            return PerformanceStatus.DEGRADED
        return PerformanceStatus.PASS
