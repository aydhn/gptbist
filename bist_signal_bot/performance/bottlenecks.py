import uuid
from typing import List, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.models import (
    BenchmarkRunResult, ProfileResult, ProfileSpan, BottleneckFinding,
    PerformanceSeverity, BenchmarkType
)

class BottleneckAnalyzer:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def slowest_spans(self, profile: ProfileResult, top_n: int = 10) -> List[ProfileSpan]:
        # Filter spans to find those taking the most time
        # Ideally, we only look at leaf nodes or non-overlapping time, but simple sort by elapsed works for basic analysis
        sorted_spans = sorted(profile.spans, key=lambda s: s.elapsed_seconds, reverse=True)
        return sorted_spans[:top_n]

    def memory_growth_findings(self, profile: ProfileResult) -> List[BottleneckFinding]:
        findings = []
        warn_mb = getattr(self.settings, 'PERFORMANCE_MEMORY_DELTA_WARN_MB', 250.0)
        fail_mb = getattr(self.settings, 'PERFORMANCE_MEMORY_DELTA_FAIL_MB', 750.0)

        for span in profile.spans:
            if span.memory_delta_mb is not None and span.memory_delta_mb > warn_mb:
                severity = PerformanceSeverity.HIGH if span.memory_delta_mb > fail_mb else PerformanceSeverity.MEDIUM
                findings.append(BottleneckFinding(
                    finding_id=str(uuid.uuid4()),
                    name=f"High memory growth in {span.name}",
                    benchmark_type=profile.benchmark_type,
                    severity=severity,
                    message=f"Span '{span.name}' consumed {span.memory_delta_mb:.1f} MB during execution.",
                    evidence={"span_id": span.span_id, "memory_delta_mb": span.memory_delta_mb}
                ))
        return findings

    def throughput_findings(self, result: BenchmarkRunResult) -> List[BottleneckFinding]:
        findings = []
        # Look for unusually low throughput. Values are arbitrary for now unless we have baselines.
        if result.throughput_items_per_second is not None and result.throughput_items_per_second < 1.0:
            findings.append(BottleneckFinding(
                finding_id=str(uuid.uuid4()),
                name="Low throughput detected",
                benchmark_type=result.request.benchmark_type,
                severity=PerformanceSeverity.MEDIUM,
                message=f"Throughput is {result.throughput_items_per_second:.2f} items/sec, which is very slow.",
                evidence={"throughput": result.throughput_items_per_second}
            ))
        return findings

    def analyze_profile(self, profile: ProfileResult) -> List[BottleneckFinding]:
        findings = []
        findings.extend(self.memory_growth_findings(profile))

        warn_sec = getattr(self.settings, 'PERFORMANCE_SLOW_SPAN_WARN_SECONDS', 2.0)
        fail_sec = getattr(self.settings, 'PERFORMANCE_SLOW_SPAN_FAIL_SECONDS', 10.0)

        for span in self.slowest_spans(profile):
            if span.elapsed_seconds > warn_sec:
                severity = PerformanceSeverity.HIGH if span.elapsed_seconds > fail_sec else PerformanceSeverity.MEDIUM
                findings.append(BottleneckFinding(
                    finding_id=str(uuid.uuid4()),
                    name=f"Slow execution in {span.name}",
                    benchmark_type=profile.benchmark_type,
                    severity=severity,
                    message=f"Span '{span.name}' took {span.elapsed_seconds:.2f} seconds.",
                    evidence={"span_id": span.span_id, "elapsed_seconds": span.elapsed_seconds}
                ))
        return findings

    def analyze_benchmark(self, result: BenchmarkRunResult) -> List[BottleneckFinding]:
        findings = []
        findings.extend(self.throughput_findings(result))
        for p in result.profiles:
            findings.extend(self.analyze_profile(p))

        # Deduplicate by name and message
        unique_findings = {}
        for f in findings:
            key = f"{f.name}-{f.message}"
            if key not in unique_findings:
                unique_findings[key] = f

        return list(unique_findings.values())
