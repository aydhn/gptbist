import pandas as pd
from typing import Any, Dict, List, Optional

from bist_signal_bot.performance.models import (
    PerformanceMetric, ResourceSnapshot, ProfileResult, BenchmarkRunResult,
    PerformanceBaseline, PerformanceRegressionResult, BottleneckFinding,
    PerformanceRecommendation, ProfileSpan
)

def performance_metric_to_dict(metric: PerformanceMetric) -> Dict[str, Any]:
    return metric.model_dump()

def resource_snapshot_to_dict(snapshot: ResourceSnapshot) -> Dict[str, Any]:
    return snapshot.model_dump()

def profile_result_to_dict(profile: ProfileResult) -> Dict[str, Any]:
    return profile.model_dump()

def benchmark_result_to_dict(result: BenchmarkRunResult) -> Dict[str, Any]:
    return result.model_dump()

def baseline_to_dict(baseline: PerformanceBaseline) -> Dict[str, Any]:
    return baseline.model_dump()

def regression_result_to_dict(result: PerformanceRegressionResult) -> Dict[str, Any]:
    return result.model_dump()

def bottleneck_to_dict(finding: BottleneckFinding) -> Dict[str, Any]:
    return finding.model_dump()

def recommendation_to_dict(rec: PerformanceRecommendation) -> Dict[str, Any]:
    return rec.model_dump()

def metrics_to_dataframe(metrics: List[PerformanceMetric]) -> pd.DataFrame:
    data = []
    for m in metrics:
        data.append({
            "Name": m.name,
            "Value": m.value,
            "Unit": m.unit,
            "Status": m.status.value
        })
    return pd.DataFrame(data)

def spans_to_dataframe(spans: List[ProfileSpan]) -> pd.DataFrame:
    data = []
    for s in spans:
        data.append({
            "Name": s.name,
            "Elapsed (s)": s.elapsed_seconds,
            "Mem Delta (MB)": s.memory_delta_mb,
            "Module": s.module
        })
    return pd.DataFrame(data)

def format_profile_text(profile: ProfileResult) -> str:
    lines = [
        "=== PERFORMANCE PROFILE ===",
        f"Benchmark Type: {profile.benchmark_type.value}",
        f"Status: {profile.status.value}",
        f"Elapsed Seconds: {profile.elapsed_seconds:.2f}",
        f"Spans Recorded: {len(profile.spans)}",
        "",
        profile.disclaimer
    ]
    return "\n".join(lines)

def format_benchmark_text(result: BenchmarkRunResult) -> str:
    lines = [
        "=== BENCHMARK RESULT ===",
        f"Type: {result.request.benchmark_type.value}",
        f"Status: {result.status.value}",
        f"Median Elapsed (s): {result.median_elapsed_seconds:.2f}" if result.median_elapsed_seconds else "Median Elapsed (s): N/A",
        f"P95 Elapsed (s): {result.p95_elapsed_seconds:.2f}" if result.p95_elapsed_seconds else "P95 Elapsed (s): N/A",
        f"Max Memory Peak (MB): {result.max_memory_peak_mb:.1f}" if result.max_memory_peak_mb else "Max Memory Peak (MB): N/A",
        f"Throughput (items/sec): {result.throughput_items_per_second:.2f}" if result.throughput_items_per_second else "Throughput (items/sec): N/A",
        "",
        result.disclaimer
    ]
    return "\n".join(lines)

def format_regression_text(result: PerformanceRegressionResult) -> str:
    lines = [
        "=== PERFORMANCE REGRESSION ===",
        f"Status: {result.status.value}",
        ""
    ]
    if result.regressions:
        lines.append("Regressions Detected:")
        for r in result.regressions:
            lines.append(f"- {r}")
        lines.append("")
    if result.improvements:
        lines.append("Improvements Detected:")
        for i in result.improvements:
            lines.append(f"- {i}")
        lines.append("")
    lines.append(result.disclaimer)
    return "\n".join(lines)

def format_bottlenecks_text(findings: List[BottleneckFinding]) -> str:
    if not findings:
        return "No bottlenecks found."
    lines = ["=== BOTTLENECKS ==="]
    for f in findings:
        lines.append(f"[{f.severity.value}] {f.name}: {f.message}")
    return "\n".join(lines)

def format_performance_report_markdown(result: BenchmarkRunResult, findings: Optional[List[BottleneckFinding]] = None, recommendations: Optional[List[PerformanceRecommendation]] = None) -> str:
    lines = [
        "# Performance Report",
        "",
        "## Benchmark Summary",
        f"- **Type**: {result.request.benchmark_type.value}",
        f"- **Status**: {result.status.value}",
        f"- **Median Elapsed**: {result.median_elapsed_seconds:.2f} s" if result.median_elapsed_seconds else "- **Median Elapsed**: N/A",
        f"- **P95 Elapsed**: {result.p95_elapsed_seconds:.2f} s" if result.p95_elapsed_seconds else "- **P95 Elapsed**: N/A",
        f"- **Peak Memory**: {result.max_memory_peak_mb:.1f} MB" if result.max_memory_peak_mb else "- **Peak Memory**: N/A",
        "",
        "## Findings",
    ]
    if findings:
        for f in findings:
            lines.append(f"- **[{f.severity.value}]** {f.name}: {f.message}")
    else:
        lines.append("No significant bottlenecks detected.")

    lines.append("")
    lines.append("## Recommendations")
    if recommendations:
        for r in recommendations:
            lines.append(f"- **{r.title}**: {r.action} (Impact: {r.expected_impact})")
    else:
        lines.append("No recommendations.")

    lines.extend([
        "",
        "---",
        f"*{result.disclaimer}*"
    ])

    return "\n".join(lines)
