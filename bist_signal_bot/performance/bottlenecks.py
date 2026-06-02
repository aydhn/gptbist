
import uuid
from typing import Optional
from bist_signal_bot.performance.models import BottleneckFinding, PerformanceProfile, BenchmarkResult, ResourceKind, PerformanceStatus

class BottleneckAnalyzer:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def analyze_profile(self, profile: PerformanceProfile) -> list[BottleneckFinding]:
        findings = []
        rb = self.detect_runtime_bottleneck(profile)
        if rb: findings.append(rb)
        mb = self.detect_memory_bottleneck(profile)
        if mb: findings.append(mb)
        cb = self.detect_cache_bottleneck(profile)
        if cb: findings.append(cb)
        return findings

    def analyze_benchmarks(self, results: list[BenchmarkResult]) -> list[BottleneckFinding]:
        return []

    def detect_runtime_bottleneck(self, profile: PerformanceProfile) -> Optional[BottleneckFinding]:
        for t in profile.timings:
            if t.elapsed_seconds and t.elapsed_seconds > 60.0:
                return BottleneckFinding(
                    finding_id=uuid.uuid4().hex,
                    module_name=profile.module_name,
                    resource_kind=ResourceKind.RUNTIME,
                    severity="HIGH",
                    message="Runtime exceeds 60s",
                    status=PerformanceStatus.SLOW
                )
        return None

    def detect_memory_bottleneck(self, profile: PerformanceProfile) -> Optional[BottleneckFinding]:
        return None

    def detect_cache_bottleneck(self, profile: PerformanceProfile) -> Optional[BottleneckFinding]:
        if any(c.status.name == "MISS" for c in profile.cache_results):
            return BottleneckFinding(
                finding_id=uuid.uuid4().hex,
                module_name=profile.module_name,
                resource_kind=ResourceKind.CACHE,
                severity="LOW",
                message="High cache miss rate",
                status=PerformanceStatus.WATCH
            )
        return None

    def suggest_action(self, finding: BottleneckFinding) -> Optional[str]:
        if finding.resource_kind == ResourceKind.RUNTIME:
            return "use sampling"
        if finding.resource_kind == ResourceKind.CACHE:
            return "enable local cache"
        return None
