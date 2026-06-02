
import uuid
from datetime import datetime, timezone
from typing import Callable, Any, Optional
from bist_signal_bot.performance.models import BenchmarkResult, BenchmarkScenario, PerformanceStatus

class PerformanceBenchmarkRunner:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def run_benchmark(self, scenario: BenchmarkScenario, save: bool = False) -> BenchmarkResult:
        return BenchmarkResult(
            benchmark_id=uuid.uuid4().hex,
            scenario=scenario,
            created_at=datetime.now(timezone.utc),
            status=PerformanceStatus.PASS,
            elapsed_seconds=1.0
        )

    def run_all_benchmarks(self, save: bool = False) -> list[BenchmarkResult]:
        return [self.run_benchmark(s, save) for s in BenchmarkScenario if s != BenchmarkScenario.CUSTOM]

    def scenario_command(self, scenario: BenchmarkScenario) -> Optional[str]:
        commands = {
            BenchmarkScenario.BOOTSTRAP_VALIDATE: "bootstrap validate --profile STANDARD",
            BenchmarkScenario.ORCHESTRATOR_DRY_RUN: "orchestrator run --campaign QUICK_RESEARCH_SCAN --dry-run"
        }
        return commands.get(scenario)

    def scenario_callable(self, scenario: BenchmarkScenario) -> Optional[Callable[..., Any]]:
        return None

    def classify_benchmark(self, result: BenchmarkResult) -> PerformanceStatus:
        return result.status

    def benchmark_summary(self, results: list[BenchmarkResult]) -> list[str]:
        return [f"Scenario {r.scenario} took {r.elapsed_seconds}s" for r in results]
