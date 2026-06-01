import re

with open("bist_signal_bot/reports/collector.py", "r") as f:
    content = f.read()

if "include_performance=False" not in content:
    content = content.replace(
        "def run_daily_report(dry_run=False, include_data_catalog=False, include_feature_store=False, include_orchestrator=False):",
        "def run_daily_report(dry_run=False, include_data_catalog=False, include_feature_store=False, include_orchestrator=False, include_performance=False):"
    )

    perf_block = """
    if include_performance:
        res["performance_section"] = "included"
    """

    content = content.replace("    return res", perf_block + "\n    return res")
    with open("bist_signal_bot/reports/collector.py", "w") as f:
        f.write(content)

with open("bist_signal_bot/notifications/formatter.py", "r") as f:
    content = f.read()

if "format_performance_profile" not in content:
    perf_imports = """
from bist_signal_bot.performance.models import (
    PerformanceProfile,
    BenchmarkResult,
    BottleneckFinding,
    PerformanceRegressionFinding,
    PerformanceReport,
)
from bist_signal_bot.performance.reporting import (
    format_profile_text,
    format_benchmark_text,
    format_bottlenecks_text,
    format_regressions_text,
    format_performance_report_markdown,
)

def format_performance_profile(profile: PerformanceProfile) -> str:
    return format_profile_text(profile)

def format_benchmark_result(result: BenchmarkResult) -> str:
    return format_benchmark_text(result)

def format_bottleneck_findings(findings: list[BottleneckFinding]) -> str:
    return format_bottlenecks_text(findings)

def format_performance_regressions(findings: list[PerformanceRegressionFinding]) -> str:
    return format_regressions_text(findings)

def format_performance_report(report: PerformanceReport) -> str:
    return format_performance_report_markdown(report)
"""
    content += perf_imports
    with open("bist_signal_bot/notifications/formatter.py", "w") as f:
        f.write(content)
