
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
    return "\n".join([f"Bottleneck in {f.module_name}: {f.message}" for f in findings])

def format_regressions_text(findings: list[PerformanceRegressionFinding]) -> str:
    return "\n".join([f"Regression in {f.scenario.value}: {f.message}" for f in findings])

def format_cache_text(entries: list[CacheEntry]) -> str:
    return f"Cache Entries: {len(entries)}"

def format_performance_report_markdown(report: PerformanceReport) -> str:
    lines = [
        "# Performance Report",
        f"Generated at: {report.generated_at.isoformat()}",
        f"Disclaimer: {report.disclaimer}"
    ]
    return "\n".join(lines)
