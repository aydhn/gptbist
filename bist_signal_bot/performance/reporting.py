import pandas as pd
from typing import Any
from bist_signal_bot.performance.models import (
    ResourceSnapshot, WorkloadProfileResult, CacheReport, PerformanceBenchmarkResult,
    PerformanceMetric, CacheEntryInfo
)

def resource_snapshot_to_dict(snapshot: ResourceSnapshot) -> dict[str, Any]:
    return {
        "timestamp": snapshot.timestamp.isoformat(),
        "cpu_count": snapshot.cpu_count,
        "cpu_percent": snapshot.cpu_percent,
        "memory_total_mb": snapshot.memory_total_mb,
        "memory_used_mb": snapshot.memory_used_mb,
        "memory_available_mb": snapshot.memory_available_mb,
        "memory_percent": snapshot.memory_percent,
        "disk_total_mb": snapshot.disk_total_mb,
        "disk_used_mb": snapshot.disk_used_mb,
        "disk_free_mb": snapshot.disk_free_mb,
        "disk_percent": snapshot.disk_percent,
        "gpu_detected": snapshot.gpu_detected,
        "gpu_name": snapshot.gpu_name,
        "gpu_memory_used_mb": snapshot.gpu_memory_used_mb,
        "metadata": snapshot.metadata
    }

def workload_profile_to_dict(result: WorkloadProfileResult) -> dict[str, Any]:
    return {
        "request": {
            "workload_type": result.request.workload_type.value,
            "symbols": result.request.symbols,
            "source": result.request.source,
            "concurrency_mode": result.request.concurrency_mode.value,
            "max_workers": result.request.max_workers
        },
        "status": result.status.value,
        "started_at": result.started_at.isoformat(),
        "elapsed_seconds": result.elapsed_seconds,
        "timer_results": [
            {
                "name": t.name,
                "elapsed_seconds": t.elapsed_seconds
            } for t in result.timer_results
        ],
        "resource_before": resource_snapshot_to_dict(result.resource_before) if result.resource_before else None,
        "resource_after": resource_snapshot_to_dict(result.resource_after) if result.resource_after else None,
        "recommendations": result.recommendations,
        "disclaimer": result.disclaimer
    }

def cache_report_to_dict(report: CacheReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "total_size_mb": report.total_size_mb,
        "entry_count": report.entry_count,
        "safe_delete_size_mb": report.safe_delete_size_mb,
        "safe_delete_count": report.safe_delete_count,
        "policy": report.policy.value,
        "dry_run": report.dry_run,
        "deleted_files": report.deleted_files,
        "issues": report.issues,
        "disclaimer": report.disclaimer
    }

def benchmark_result_to_dict(result: PerformanceBenchmarkResult) -> dict[str, Any]:
    return {
        "benchmark_id": result.benchmark_id,
        "workload_type": result.workload_type.value,
        "status": result.status.value,
        "iterations": result.iterations,
        "average_seconds": result.average_seconds,
        "median_seconds": result.median_seconds,
        "min_seconds": result.min_seconds,
        "max_seconds": result.max_seconds,
        "throughput_per_second": result.throughput_per_second,
        "disclaimer": result.disclaimer
    }

def performance_metrics_to_dataframe(metrics: list[PerformanceMetric]) -> pd.DataFrame:
    data = []
    for m in metrics:
        data.append({
            "Metric": m.metric_name,
            "Value": m.value,
            "Unit": m.unit,
            "Status": m.status.value
        })
    return pd.DataFrame(data)

def cache_entries_to_dataframe(entries: list[CacheEntryInfo]) -> pd.DataFrame:
    data = []
    for e in entries:
        data.append({
            "Path": e.path,
            "Size_MB": e.size_mb,
            "Age_Days": e.age_days,
            "Category": e.category,
            "Safe_Delete": e.safe_to_delete
        })
    return pd.DataFrame(data)

def format_resource_snapshot_text(snapshot: ResourceSnapshot) -> str:
    lines = [
        "--- RESOURCE SNAPSHOT ---",
        f"CPU Cores: {snapshot.cpu_count}",
        f"CPU Usage: {snapshot.cpu_percent}%" if snapshot.cpu_percent is not None else "CPU Usage: N/A",
        f"Memory Usage: {snapshot.memory_percent}%" if snapshot.memory_percent is not None else "Memory Usage: N/A",
        f"Memory Free: {snapshot.memory_available_mb:.1f} MB" if snapshot.memory_available_mb is not None else "Memory Free: N/A",
        f"Disk Usage: {snapshot.disk_percent}%" if snapshot.disk_percent is not None else "Disk Usage: N/A",
        f"GPU Detected: {'Yes (' + str(snapshot.gpu_name) + ')' if snapshot.gpu_detected else 'No'}"
    ]
    return "\n".join(lines)

def format_workload_profile_text(result: WorkloadProfileResult) -> str:
    lines = [
        f"--- PROFILE: {result.request.workload_type.value} ---",
        f"Status: {result.status.value}",
        f"Elapsed: {result.elapsed_seconds:.4f}s",
        f"Timers: {len(result.timer_results)}",
        f"Recommendations: {len(result.recommendations)}",
        f"\nDisclaimer: {result.disclaimer}"
    ]
    return "\n".join(lines)

def format_cache_report_text(report: CacheReport) -> str:
    lines = [
        "--- CACHE REPORT ---",
        f"Policy: {report.policy.value} | Dry Run: {report.dry_run}",
        f"Total Size: {report.total_size_mb:.1f} MB ({report.entry_count} entries)",
        f"Safe Delete: {report.safe_delete_size_mb:.1f} MB ({report.safe_delete_count} entries)",
        f"Deleted: {len(report.deleted_files)} files",
        f"\nDisclaimer: {report.disclaimer}"
    ]
    return "\n".join(lines)

def format_benchmark_result_text(result: PerformanceBenchmarkResult) -> str:
    lines = [
        f"--- BENCHMARK: {result.benchmark_id} ---",
        f"Workload: {result.workload_type.value}",
        f"Status: {result.status.value}",
        f"Iterations: {result.iterations}",
        f"Average: {result.average_seconds:.4f}s",
        f"Min/Max: {result.min_seconds:.4f}s / {result.max_seconds:.4f}s",
        f"\nDisclaimer: {result.disclaimer}"
    ]
    return "\n".join(lines)

def format_performance_markdown(result: WorkloadProfileResult) -> str:
    return f"""# Performance Profile Report
**Workload:** {result.request.workload_type.value}
**Status:** {result.status.value}
**Elapsed Time:** {result.elapsed_seconds:.4f} seconds
**Started At:** {result.started_at.isoformat()}

## Recommendations
{chr(10).join(f"- {r}" for r in result.recommendations) if result.recommendations else "No specific recommendations."}

## Timers
{chr(10).join(f"- {t.name}: {t.elapsed_seconds:.4f}s" for t in result.timer_results)}

## Resources
{format_resource_snapshot_text(result.resource_after) if result.resource_after else "N/A"}

*{result.disclaimer}*
"""
