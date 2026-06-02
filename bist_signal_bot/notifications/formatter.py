
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
    return "\n".join(msg)
