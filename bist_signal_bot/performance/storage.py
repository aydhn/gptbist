
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
            f.write(profile.model_dump_json() + "\n")
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
            f.write(result.model_dump_json() + "\n")
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
                f.write(finding.model_dump_json() + "\n")
        return p

    def load_bottlenecks(self, limit: int = 1000) -> list[BottleneckFinding]:
        return []

    def append_regressions(self, findings: list[PerformanceRegressionFinding]) -> Path:
        p = self.base_dir / "regressions" / "performance_regressions.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as f:
            for finding in findings:
                f.write(finding.model_dump_json() + "\n")
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
            f.write(entry.model_dump_json() + "\n")
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
