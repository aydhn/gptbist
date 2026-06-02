import os

with open("bist_signal_bot/performance/bottlenecks.py", "w") as f:
    f.write("""
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
""")

with open("bist_signal_bot/performance/regression.py", "w") as f:
    f.write("""
import uuid
from typing import Optional
from bist_signal_bot.performance.models import PerformanceRegressionFinding, BenchmarkResult, PerformanceStatus, BenchmarkScenario

class PerformanceRegressionDetector:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def detect_regressions(self, current: list[BenchmarkResult], baseline: Optional[list[BenchmarkResult]] = None) -> list[PerformanceRegressionFinding]:
        if not baseline:
            return [PerformanceRegressionFinding(
                regression_id=uuid.uuid4().hex,
                scenario=BenchmarkScenario.CUSTOM,
                threshold_pct=10.0,
                message="No baseline available",
                status=PerformanceStatus.WATCH
            )]
        regressions = []
        for c in current:
            for b in baseline:
                if c.scenario == b.scenario:
                    regressions.append(self.compare_result(c, b))
        return regressions

    def load_baseline(self) -> list[BenchmarkResult]:
        return []

    def compare_result(self, current: BenchmarkResult, baseline: BenchmarkResult) -> PerformanceRegressionFinding:
        delta = self.delta_pct(current.elapsed_seconds, baseline.elapsed_seconds)
        status = self.classify_regression(delta, 25.0)
        return PerformanceRegressionFinding(
            regression_id=uuid.uuid4().hex,
            scenario=current.scenario,
            baseline_value=baseline.elapsed_seconds,
            current_value=current.elapsed_seconds,
            delta_pct=delta,
            threshold_pct=25.0,
            status=status,
            message="Comparison complete"
        )

    def delta_pct(self, current: Optional[float], baseline: Optional[float]) -> Optional[float]:
        if current is None or baseline is None or baseline == 0:
            return None
        return ((current - baseline) / baseline) * 100.0

    def classify_regression(self, delta_pct: Optional[float], threshold_pct: float) -> PerformanceStatus:
        if delta_pct is None:
            return PerformanceStatus.UNKNOWN
        if delta_pct > threshold_pct:
            return PerformanceStatus.DEGRADED
        return PerformanceStatus.PASS
""")

with open("bist_signal_bot/performance/storage.py", "w") as f:
    f.write("""
import os
import json
from pathlib import Path
from typing import Optional
from bist_signal_bot.performance.models import (
    PerformanceProfile, BenchmarkResult, BottleneckFinding,
    PerformanceRegressionFinding, ResourceBudget, CacheEntry, PerformanceReport, BenchmarkScenario
)

class PerformanceStore:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir or Path("data/performance")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def append_profile(self, profile: PerformanceProfile) -> Path:
        p = self.base_dir / "profiles" / "performance_profiles.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as f:
            f.write(profile.model_dump_json() + "\\n")
        return p

    def load_profiles(self, module_name: Optional[str] = None, limit: int = 1000) -> list[PerformanceProfile]:
        p = self.base_dir / "profiles" / "performance_profiles.jsonl"
        if not p.exists(): return []
        res = []
        with p.open("r") as f:
            for line in f:
                prof = PerformanceProfile.model_validate_json(line)
                if module_name is None or prof.module_name == module_name:
                    res.append(prof)
        return res[:limit]

    def append_benchmark(self, result: BenchmarkResult) -> Path:
        p = self.base_dir / "benchmarks" / "benchmark_results.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as f:
            f.write(result.model_dump_json() + "\\n")
        return p

    def load_benchmarks(self, scenario: Optional[BenchmarkScenario] = None, limit: int = 1000) -> list[BenchmarkResult]:
        p = self.base_dir / "benchmarks" / "benchmark_results.jsonl"
        if not p.exists(): return []
        res = []
        with p.open("r") as f:
            for line in f:
                bm = BenchmarkResult.model_validate_json(line)
                if scenario is None or bm.scenario == scenario:
                    res.append(bm)
        return res[:limit]

    def append_bottlenecks(self, findings: list[BottleneckFinding]) -> Path:
        p = self.base_dir / "bottlenecks" / "bottleneck_findings.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as f:
            for finding in findings:
                f.write(finding.model_dump_json() + "\\n")
        return p

    def load_bottlenecks(self, limit: int = 1000) -> list[BottleneckFinding]:
        return []

    def append_regressions(self, findings: list[PerformanceRegressionFinding]) -> Path:
        p = self.base_dir / "regressions" / "performance_regressions.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as f:
            for finding in findings:
                f.write(finding.model_dump_json() + "\\n")
        return p

    def load_regressions(self, limit: int = 1000) -> list[PerformanceRegressionFinding]:
        return []

    def save_budgets(self, budgets: list[ResourceBudget]) -> Path:
        p = self.base_dir / "budgets" / "resource_budgets.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w") as f:
            f.write(json.dumps([b.model_dump(mode='json') for b in budgets]))
        return p

    def load_budgets(self) -> list[ResourceBudget]:
        return []

    def append_cache_entry(self, entry: CacheEntry) -> Path:
        p = self.base_dir / "cache" / "cache_index.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as f:
            f.write(entry.model_dump_json() + "\\n")
        return p

    def load_cache_entries(self, namespace: Optional[str] = None, limit: int = 10000) -> list[CacheEntry]:
        return []

    def save_report(self, report: PerformanceReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        p = self.base_dir / "reports" / date_str / "performance_report.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w") as f:
            f.write(markdown_text)
        return {"markdown": p}
""")

with open("bist_signal_bot/storage/paths.py", "w") as f:
    f.write("""
from pathlib import Path

def get_performance_dir(settings=None) -> Path:
    return Path("data/performance")
""")
