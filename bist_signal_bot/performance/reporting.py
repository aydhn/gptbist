from bist_signal_bot.performance.models import (
    PerformanceProfile, BenchmarkResult, BottleneckFinding,
    PerformanceRegressionFinding, ResourceBudget, CacheEntry, CacheLookupResult,
    PerformanceReport, TimingMeasurement, ResourceMeasurement
)
from typing import Any

def timing_to_dict(measurement: TimingMeasurement) -> dict[str, Any]:
    return measurement.model_dump(mode="json")

def resource_to_dict(measurement: ResourceMeasurement) -> dict[str, Any]:
    return measurement.model_dump(mode="json")

def budget_to_dict(budget: ResourceBudget) -> dict[str, Any]:
    return budget.model_dump(mode="json")

def cache_entry_to_dict(entry: CacheEntry) -> dict[str, Any]:
    return entry.model_dump(mode="json")

def cache_lookup_to_dict(result: CacheLookupResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def profile_to_dict(profile: PerformanceProfile) -> dict[str, Any]:
    return profile.model_dump(mode="json")

def benchmark_to_dict(result: BenchmarkResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def bottleneck_to_dict(finding: BottleneckFinding) -> dict[str, Any]:
    return finding.model_dump(mode="json")

def regression_to_dict(finding: PerformanceRegressionFinding) -> dict[str, Any]:
    return finding.model_dump(mode="json")

def performance_report_to_dict(report: PerformanceReport) -> dict[str, Any]:
    return report.model_dump(mode="json")

def format_profile_text(profile: PerformanceProfile) -> str:
    lines = [f"Performance Profile: {profile.module_name}", f"Status: {profile.status.value}"]
    for t in profile.timings:
        lines.append(f"- {t.name}: {t.elapsed_seconds}s ({t.status.value})")
    lines.append(f"\nDisclaimer: {profile.disclaimer}")
    return "\n".join(lines)

def format_benchmark_text(result: BenchmarkResult) -> str:
    return f"Benchmark {result.scenario.value}: {result.status.value} ({result.elapsed_seconds}s)\nDisclaimer: {result.disclaimer}"

def format_bottlenecks_text(findings: list[BottleneckFinding]) -> str:
    if not findings:
        return "No bottlenecks found."
    return "\n".join(f"- {f.module_name} ({f.resource_kind.value}): {f.message} (Action: {f.suggested_action})" for f in findings)

def format_regressions_text(findings: list[PerformanceRegressionFinding]) -> str:
    if not findings:
        return "No regressions found."
    return "\n".join(f"- {f.scenario.value}: {f.message} ({f.status.value})" for f in findings)

def format_cache_text(entries: list[CacheEntry]) -> str:
    if not entries:
        return "Cache is empty."
    return "\n".join(f"- {e.namespace}/{e.key}: {e.status.value} (Expires: {e.expires_at})" for e in entries)

def format_performance_report_markdown(report: PerformanceReport) -> str:
    lines = [
        f"# Performance Report ({report.generated_at.isoformat()})",
        "",
        "## Summary",
    ]
    for k in report.key_findings:
        lines.append(f"- {k}")

    lines.extend(["", "## Disclaimer", f"*{report.disclaimer}*"])
    return "\n".join(lines)
