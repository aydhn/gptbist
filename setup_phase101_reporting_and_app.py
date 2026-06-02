import os

with open("bist_signal_bot/performance/reporting.py", "w") as f:
    f.write("""
from typing import Any
from bist_signal_bot.performance.models import (
    TimingMeasurement, ResourceMeasurement, ResourceBudget, CacheEntry,
    CacheLookupResult, PerformanceProfile, BenchmarkResult, BottleneckFinding,
    PerformanceRegressionFinding, PerformanceReport
)

def timing_to_dict(measurement: TimingMeasurement) -> dict[str, Any]:
    return measurement.model_dump(mode='json')

def resource_to_dict(measurement: ResourceMeasurement) -> dict[str, Any]:
    return measurement.model_dump(mode='json')

def budget_to_dict(budget: ResourceBudget) -> dict[str, Any]:
    return budget.model_dump(mode='json')

def cache_entry_to_dict(entry: CacheEntry) -> dict[str, Any]:
    return entry.model_dump(mode='json')

def cache_lookup_to_dict(result: CacheLookupResult) -> dict[str, Any]:
    return result.model_dump(mode='json')

def profile_to_dict(profile: PerformanceProfile) -> dict[str, Any]:
    return profile.model_dump(mode='json')

def benchmark_to_dict(result: BenchmarkResult) -> dict[str, Any]:
    return result.model_dump(mode='json')

def bottleneck_to_dict(finding: BottleneckFinding) -> dict[str, Any]:
    return finding.model_dump(mode='json')

def regression_to_dict(finding: PerformanceRegressionFinding) -> dict[str, Any]:
    return finding.model_dump(mode='json')

def performance_report_to_dict(report: PerformanceReport) -> dict[str, Any]:
    return report.model_dump(mode='json')

def format_profile_text(profile: PerformanceProfile) -> str:
    return f"Profile {profile.profile_id}: {profile.module_name} -> {profile.status.value}"

def format_benchmark_text(result: BenchmarkResult) -> str:
    return f"Benchmark {result.scenario.value}: {result.elapsed_seconds}s -> {result.status.value}"

def format_bottlenecks_text(findings: list[BottleneckFinding]) -> str:
    return "\\n".join([f"Bottleneck in {f.module_name}: {f.message}" for f in findings])

def format_regressions_text(findings: list[PerformanceRegressionFinding]) -> str:
    return "\\n".join([f"Regression in {f.scenario.value}: {f.message}" for f in findings])

def format_cache_text(entries: list[CacheEntry]) -> str:
    return f"Cache Entries: {len(entries)}"

def format_performance_report_markdown(report: PerformanceReport) -> str:
    lines = [
        "# Performance Report",
        f"Generated at: {report.generated_at.isoformat()}",
        f"Disclaimer: {report.disclaimer}"
    ]
    return "\\n".join(lines)
""")

with open("bist_signal_bot/app/performance_app.py", "w") as f:
    f.write("""
from pathlib import Path
from bist_signal_bot.performance.storage import PerformanceStore
from bist_signal_bot.performance.timers import PerformanceTimer
from bist_signal_bot.performance.profiler import LocalPerformanceProfiler
from bist_signal_bot.performance.resource_budget import ResourceBudgetManager
from bist_signal_bot.performance.cache import LocalCacheManager
from bist_signal_bot.performance.benchmark import PerformanceBenchmarkRunner
from bist_signal_bot.performance.bottlenecks import BottleneckAnalyzer
from bist_signal_bot.performance.regression import PerformanceRegressionDetector

def create_performance_store(settings=None, base_dir: Path | None = None) -> PerformanceStore:
    return PerformanceStore(settings=settings, base_dir=base_dir)

def create_performance_timer(settings=None) -> PerformanceTimer:
    return PerformanceTimer(settings=settings)

def create_local_performance_profiler(settings=None, base_dir: Path | None = None) -> LocalPerformanceProfiler:
    return LocalPerformanceProfiler(settings=settings, base_dir=base_dir)

def create_resource_budget_manager(settings=None, base_dir: Path | None = None) -> ResourceBudgetManager:
    return ResourceBudgetManager(settings=settings, base_dir=base_dir)

def create_local_cache_manager(settings=None, base_dir: Path | None = None) -> LocalCacheManager:
    return LocalCacheManager(settings=settings, base_dir=base_dir)

def create_performance_benchmark_runner(settings=None, base_dir: Path | None = None) -> PerformanceBenchmarkRunner:
    return PerformanceBenchmarkRunner(settings=settings, base_dir=base_dir)

def create_bottleneck_analyzer(settings=None, base_dir: Path | None = None) -> BottleneckAnalyzer:
    return BottleneckAnalyzer(settings=settings, base_dir=base_dir)

def create_performance_regression_detector(settings=None, base_dir: Path | None = None) -> PerformanceRegressionDetector:
    return PerformanceRegressionDetector(settings=settings, base_dir=base_dir)
""")

with open("bist_signal_bot/notifications/formatter.py", "w") as f:
    f.write("""
from bist_signal_bot.performance.models import (
    PerformanceProfile, BenchmarkResult, BottleneckFinding,
    PerformanceRegressionFinding, PerformanceReport
)

def format_performance_profile(profile: PerformanceProfile) -> str:
    return f"Performance Profile {profile.module_name}: {profile.status.value}"

def format_benchmark_result(result: BenchmarkResult) -> str:
    return f"Benchmark {result.scenario.value} elapsed {result.elapsed_seconds}s"

def format_bottleneck_findings(findings: list[BottleneckFinding]) -> str:
    return f"Found {len(findings)} bottlenecks"

def format_performance_regressions(findings: list[PerformanceRegressionFinding]) -> str:
    return f"Found {len(findings)} regressions"

def format_performance_report(report: PerformanceReport) -> str:
    msg = [
        "BIST Bot Performance Özeti",
        f"Profiles: {len(report.profiles)}",
        f"Benchmarks: {len(report.benchmarks)}",
        f"Bottlenecks: {len(report.bottlenecks)}",
        "Bu çıktı yerel yazılım performans özetidir.",
        "Yatırım tavsiyesi değildir.",
        "İşlem uygunluğu anlamına gelmez.",
        "Gerçek emir gönderilmedi."
    ]
    return "\\n".join(msg)
""")

with open("bist_signal_bot/core/audit.py", "w") as f:
    f.write("""
class AuditEvents:
    PERFORMANCE_PROFILE_CREATED = "PERFORMANCE_PROFILE_CREATED"
    RESOURCE_BUDGET_EVALUATED = "RESOURCE_BUDGET_EVALUATED"
    CACHE_ENTRY_CREATED = "CACHE_ENTRY_CREATED"
    CACHE_ENTRY_INVALIDATED = "CACHE_ENTRY_INVALIDATED"
    PERFORMANCE_BENCHMARK_RUN = "PERFORMANCE_BENCHMARK_RUN"
    BOTTLENECKS_ANALYZED = "BOTTLENECKS_ANALYZED"
    PERFORMANCE_REGRESSION_DETECTED = "PERFORMANCE_REGRESSION_DETECTED"
    PERFORMANCE_REPORT_CREATED = "PERFORMANCE_REPORT_CREATED"
""")
