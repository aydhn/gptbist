from typing import Any
from bist_signal_bot.performance.models import (
    TimingMeasurement,
    ResourceMeasurement,
    ResourceBudget,
    CacheEntry,
    CacheLookupResult,
    PerformanceProfile,
    BenchmarkResult,
    BottleneckFinding,
    PerformanceRegressionFinding,
    PerformanceReport,
)

def timing_to_dict(measurement: TimingMeasurement) -> dict[str, Any]:
    return measurement.model_dump()

def resource_to_dict(measurement: ResourceMeasurement) -> dict[str, Any]:
    return measurement.model_dump()

def budget_to_dict(budget: ResourceBudget) -> dict[str, Any]:
    return budget.model_dump()

def cache_entry_to_dict(entry: CacheEntry) -> dict[str, Any]:
    return entry.model_dump()

def cache_lookup_to_dict(result: CacheLookupResult) -> dict[str, Any]:
    return result.model_dump()

def profile_to_dict(profile: PerformanceProfile) -> dict[str, Any]:
    return profile.model_dump()

def benchmark_to_dict(result: BenchmarkResult) -> dict[str, Any]:
    return result.model_dump()

def bottleneck_to_dict(finding: BottleneckFinding) -> dict[str, Any]:
    return finding.model_dump()

def regression_to_dict(finding: PerformanceRegressionFinding) -> dict[str, Any]:
    return finding.model_dump()

def performance_report_to_dict(report: PerformanceReport) -> dict[str, Any]:
    return report.model_dump()

def format_profile_text(profile: PerformanceProfile) -> str:
    lines = [f"Profile: {profile.module_name} (Status: {profile.status.value})"]
    if profile.command:
        lines.append(f"Command: {profile.command}")

    for t in profile.timings:
        val = f"{t.elapsed_seconds:.4f}s" if t.elapsed_seconds is not None else "N/A"
        lines.append(f"Timing {t.name}: {val} [{t.status.value}]")

    for r in profile.resources:
        val = f"{r.value:.2f}{r.unit}" if r.value is not None else "N/A"
        lines.append(f"Resource {r.resource_kind.value}: {val} [{r.status.value}]")

    return "\n".join(lines)

def format_benchmark_text(result: BenchmarkResult) -> str:
    lines = [
        f"Benchmark: {result.scenario.value}",
        f"Status: {result.status.value}",
    ]
    if result.elapsed_seconds is not None:
        lines.append(f"Elapsed: {result.elapsed_seconds:.4f}s")
    if result.memory_mb is not None:
        lines.append(f"Memory: {result.memory_mb:.2f}MB")
    lines.append(f"Cache Hits: {result.cache_hit_count}, Misses: {result.cache_miss_count}")
    return "\n".join(lines)

def format_bottlenecks_text(findings: list[BottleneckFinding]) -> str:
    if not findings:
        return "No bottlenecks detected."
    lines = ["Bottlenecks:"]
    for f in findings:
        lines.append(f"- [{f.severity}] {f.module_name} ({f.resource_kind.value}): {f.message}")
        if f.suggested_action:
            lines.append(f"  Suggested: {f.suggested_action}")
    return "\n".join(lines)

def format_regressions_text(findings: list[PerformanceRegressionFinding]) -> str:
    if not findings:
        return "No performance regressions detected."
    lines = ["Regressions:"]
    for f in findings:
        lines.append(f"- [{f.status.value}] {f.scenario.value}: {f.message}")
    return "\n".join(lines)

def format_cache_text(entries: list[CacheEntry]) -> str:
    if not entries:
        return "No cache entries."
    lines = ["Cache Entries:"]
    for e in entries:
        size = f"{e.size_bytes} bytes" if e.size_bytes is not None else "Unknown size"
        lines.append(f"- {e.namespace}:{e.key} ({e.status.value}) - {size}")
    return "\n".join(lines)

def format_performance_report_markdown(report: PerformanceReport) -> str:
    lines = [
        "# BIST Signal Bot Performance Report",
        f"**Generated At:** {report.generated_at.isoformat()}",
        "",
        "## Disclaimer",
        f"_{report.disclaimer}_",
        ""
    ]

    if report.key_findings:
        lines.append("## Key Findings")
        for k in report.key_findings:
            lines.append(f"- {k}")
        lines.append("")

    lines.append("## Benchmark Results")
    if report.benchmarks:
        for b in report.benchmarks:
            lines.append(f"### {b.scenario.value}")
            lines.append(format_benchmark_text(b))
            lines.append("")
    else:
        lines.append("No benchmark results.")
        lines.append("")

    lines.append("## Bottlenecks")
    lines.append(format_bottlenecks_text(report.bottlenecks))
    lines.append("")

    lines.append("## Regressions")
    lines.append(format_regressions_text(report.regressions))
    lines.append("")

    return "\n".join(lines)
