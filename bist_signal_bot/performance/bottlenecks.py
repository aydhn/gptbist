from bist_signal_bot.performance.models import BottleneckFinding, PerformanceProfile, BenchmarkResult, ResourceKind, PerformanceStatus
import datetime

class BottleneckAnalyzer:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def analyze_profile(self, profile: PerformanceProfile) -> list[BottleneckFinding]:
        findings = []
        r_bottleneck = self.detect_runtime_bottleneck(profile)
        if r_bottleneck:
            findings.append(r_bottleneck)
        c_bottleneck = self.detect_cache_bottleneck(profile)
        if c_bottleneck:
            findings.append(c_bottleneck)
        return findings

    def analyze_benchmarks(self, results: list[BenchmarkResult]) -> list[BottleneckFinding]:
        return []

    def detect_runtime_bottleneck(self, profile: PerformanceProfile) -> BottleneckFinding | None:
        total_time = sum(t.elapsed_seconds for t in profile.timings if t.elapsed_seconds)
        if total_time > 30.0:
            return BottleneckFinding(
                finding_id=f"bn_rt_{profile.profile_id}",
                module_name=profile.module_name,
                resource_kind=ResourceKind.RUNTIME,
                severity="HIGH",
                message=f"Runtime bottleneck detected: {total_time}s",
                status=PerformanceStatus.SLOW,
                suggested_action=self.suggest_action("runtime")
            )
        return None

    def detect_memory_bottleneck(self, profile: PerformanceProfile) -> BottleneckFinding | None:
        return None

    def detect_cache_bottleneck(self, profile: PerformanceProfile) -> BottleneckFinding | None:
        return None

    def suggest_action(self, finding_type: str | BottleneckFinding) -> str | None:
        if isinstance(finding_type, str):
            ftype = finding_type
        else:
            ftype = finding_type.resource_kind.value.lower()

        if "runtime" in ftype:
            return "use sampling"
        elif "cache" in ftype:
            return "enable local cache"
        return "use dry-run first"
