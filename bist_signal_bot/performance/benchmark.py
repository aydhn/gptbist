import uuid
from datetime import datetime, UTC
from typing import Any, Callable, Optional

from bist_signal_bot.performance.models import (
    BenchmarkResult,
    BenchmarkScenario,
    PerformanceStatus,
)
from bist_signal_bot.performance.profiler import LocalPerformanceProfiler
from bist_signal_bot.core.exceptions import BistSignalBotError

class PerformanceBenchmarkError(BistSignalBotError):
    pass

class PerformanceBenchmarkRunner:
    def __init__(self, settings: Any = None, base_dir: Any = None):
        self.settings = settings
        self.base_dir = base_dir
        self.profiler = LocalPerformanceProfiler(settings, base_dir)

        self.enabled = True
        self.save_results = True
        if self.settings:
            self.enabled = getattr(self.settings, "PERFORMANCE_BENCHMARK_ENABLED", self.enabled)
            self.save_results = getattr(self.settings, "PERFORMANCE_BENCHMARK_SAVE_RESULTS", self.save_results)

    def run_benchmark(self, scenario: BenchmarkScenario, save: bool = False) -> BenchmarkResult:
        started_at = datetime.now(UTC)

        if not self.enabled:
            return BenchmarkResult(
                benchmark_id=str(uuid.uuid4()),
                scenario=scenario,
                created_at=started_at,
                cache_hit_count=0,
                cache_miss_count=0,
                status=PerformanceStatus.DISABLED,
                warnings=["Benchmarks are disabled via settings"]
            )

        command = self.scenario_command(scenario)
        profile = None

        if command:
            profile = self.profiler.profile_command(command, dry_run=True)
        else:
            callable_fn = self.scenario_callable(scenario)
            if callable_fn:
                profile = self.profiler.profile_callable(scenario.value, callable_fn)

        if not profile:
            return BenchmarkResult(
                benchmark_id=str(uuid.uuid4()),
                scenario=scenario,
                created_at=started_at,
                cache_hit_count=0,
                cache_miss_count=0,
                status=PerformanceStatus.SKIPPED,
                warnings=[f"No command or callable found for scenario: {scenario.value}"]
            )

        # Extract metrics
        elapsed = sum(t.elapsed_seconds for t in profile.timings if t.elapsed_seconds is not None)
        memory_mb = next((r.value for r in profile.resources if r.resource_kind.value == "MEMORY"), None)
        disk_mb = next((r.value for r in profile.resources if r.resource_kind.value == "DISK"), None)

        cache_hits = len([c for c in profile.cache_results if c.status.value == "HIT"])
        cache_misses = len([c for c in profile.cache_results if c.status.value == "MISS"])

        result = BenchmarkResult(
            benchmark_id=str(uuid.uuid4()),
            scenario=scenario,
            created_at=started_at,
            command=command,
            elapsed_seconds=elapsed,
            memory_mb=memory_mb,
            disk_mb=disk_mb,
            cache_hit_count=cache_hits,
            cache_miss_count=cache_misses,
            status=profile.status,
            warnings=profile.warnings
        )

        return result

    def run_all_benchmarks(self, save: bool = False) -> list[BenchmarkResult]:
        results = []
        for scenario in BenchmarkScenario:
            if scenario != BenchmarkScenario.CUSTOM:
                results.append(self.run_benchmark(scenario, save))
        return results

    def scenario_command(self, scenario: BenchmarkScenario) -> Optional[str]:
        commands = {
            BenchmarkScenario.BOOTSTRAP_VALIDATE: "bootstrap validate --profile STANDARD",
            BenchmarkScenario.OFFLINE_DEMO: "bootstrap demo --dry-run",
            BenchmarkScenario.DATA_CATALOG_GATE: "data-catalog validate",
            BenchmarkScenario.ORCHESTRATOR_DRY_RUN: "orchestrator run --campaign QUICK_RESEARCH_SCAN --dry-run",
            BenchmarkScenario.REPORT_DAILY_DRY_RUN: "reports daily --dry-run",
            BenchmarkScenario.FINAL_AUDIT_GO_NO_GO: "final-audit run --dry-run"
        }
        return commands.get(scenario)

    def scenario_callable(self, scenario: BenchmarkScenario) -> Optional[Callable[..., Any]]:
        # Return a dummy callable for testing scenarios without CLI commands
        def dummy_callable():
            import time
            time.sleep(0.01)

        callables = {
            BenchmarkScenario.FEATURE_COMPUTE: dummy_callable,
            BenchmarkScenario.FEATURE_SERVE: dummy_callable,
            BenchmarkScenario.MODEL_GOVERNANCE: dummy_callable,
            BenchmarkScenario.MONITORING_STATUS: dummy_callable,
            BenchmarkScenario.LEADERBOARD_BUILD: dummy_callable,
        }
        return callables.get(scenario)

    def classify_benchmark(self, result: BenchmarkResult) -> PerformanceStatus:
        if result.elapsed_seconds is None:
            return PerformanceStatus.UNKNOWN
        if result.elapsed_seconds > 60.0:
            return PerformanceStatus.SLOW
        return PerformanceStatus.PASS

    def benchmark_summary(self, results: list[BenchmarkResult]) -> list[str]:
        summary = []
        for r in results:
            elapsed = f"{r.elapsed_seconds:.2f}s" if r.elapsed_seconds is not None else "N/A"
            mem = f"{r.memory_mb:.2f}MB" if r.memory_mb is not None else "N/A"
            summary.append(f"[{r.scenario.value}] Status: {r.status.value}, Elapsed: {elapsed}, Memory: {mem}")
        return summary


