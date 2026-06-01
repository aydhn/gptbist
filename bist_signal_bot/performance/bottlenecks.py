import uuid
from typing import Any, Optional

from bist_signal_bot.performance.models import (
    BenchmarkResult,
    BottleneckFinding,
    PerformanceProfile,
    PerformanceStatus,
    ResourceKind,
)
from bist_signal_bot.core.exceptions import BistSignalBotError

class BottleneckAnalysisError(BistSignalBotError):
    pass

class BottleneckAnalyzer:
    def __init__(self, settings: Any = None, base_dir: Any = None):
        self.settings = settings
        self.base_dir = base_dir

    def analyze_profile(self, profile: PerformanceProfile) -> list[BottleneckFinding]:
        findings = []

        runtime = self.detect_runtime_bottleneck(profile)
        if runtime:
            findings.append(runtime)

        memory = self.detect_memory_bottleneck(profile)
        if memory:
            findings.append(memory)

        cache = self.detect_cache_bottleneck(profile)
        if cache:
            findings.append(cache)

        return findings

    def analyze_benchmarks(self, results: list[BenchmarkResult]) -> list[BottleneckFinding]:
        findings = []

        for r in results:
            if r.status in [PerformanceStatus.SLOW, PerformanceStatus.FAIL, PerformanceStatus.DEGRADED]:
                finding = BottleneckFinding(
                    finding_id=str(uuid.uuid4()),
                    module_name=f"benchmark_{r.scenario.value.lower()}",
                    resource_kind=ResourceKind.RUNTIME,
                    severity="HIGH" if r.status == PerformanceStatus.FAIL else "MEDIUM",
                    message=f"Benchmark scenario {r.scenario.value} resulted in {r.status.value} status",
                    status=r.status
                )
                finding.suggested_action = self.suggest_action(finding)
                findings.append(finding)

        return findings

    def detect_runtime_bottleneck(self, profile: PerformanceProfile) -> Optional[BottleneckFinding]:
        for timing in profile.timings:
            if timing.status in [PerformanceStatus.SLOW, PerformanceStatus.FAIL, PerformanceStatus.DEGRADED]:
                finding = BottleneckFinding(
                    finding_id=str(uuid.uuid4()),
                    module_name=profile.module_name,
                    resource_kind=ResourceKind.RUNTIME,
                    severity="HIGH" if timing.status == PerformanceStatus.FAIL else "MEDIUM",
                    message=f"Timing '{timing.name}' is excessively slow ({timing.elapsed_seconds}s)",
                    evidence_refs=[timing.timing_id],
                    status=timing.status
                )
                finding.suggested_action = self.suggest_action(finding)
                return finding
        return None

    def detect_memory_bottleneck(self, profile: PerformanceProfile) -> Optional[BottleneckFinding]:
        for res in profile.resources:
            if res.resource_kind == ResourceKind.MEMORY and res.status in [PerformanceStatus.SLOW, PerformanceStatus.FAIL, PerformanceStatus.DEGRADED]:
                finding = BottleneckFinding(
                    finding_id=str(uuid.uuid4()),
                    module_name=profile.module_name,
                    resource_kind=ResourceKind.MEMORY,
                    severity="HIGH" if res.status == PerformanceStatus.FAIL else "MEDIUM",
                    message=f"Memory usage is unusually high ({res.value}MB)",
                    evidence_refs=[res.measurement_id],
                    status=res.status
                )
                finding.suggested_action = self.suggest_action(finding)
                return finding
        return None

    def detect_cache_bottleneck(self, profile: PerformanceProfile) -> Optional[BottleneckFinding]:
        if not profile.cache_results:
            return None

        misses = len([c for c in profile.cache_results if c.status.value == "MISS"])
        total = len(profile.cache_results)

        if total > 0 and (misses / total) > 0.8:
            finding = BottleneckFinding(
                finding_id=str(uuid.uuid4()),
                module_name=profile.module_name,
                resource_kind=ResourceKind.CACHE,
                severity="MEDIUM",
                message=f"High cache miss rate ({misses}/{total}) detected",
                status=PerformanceStatus.DEGRADED
            )
            finding.suggested_action = self.suggest_action(finding)
            return finding

        return None

    def suggest_action(self, finding: BottleneckFinding) -> Optional[str]:
        if finding.resource_kind == ResourceKind.RUNTIME:
            return "use sampling or split campaign into smaller run"
        elif finding.resource_kind == ResourceKind.MEMORY:
            return "reduce symbol universe or use chunking"
        elif finding.resource_kind == ResourceKind.CACHE:
            return "enable local cache or refresh stale cache"
        return "inspect data catalog profile"
