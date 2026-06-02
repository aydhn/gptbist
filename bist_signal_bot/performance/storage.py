import json
from pathlib import Path
from bist_signal_bot.performance.models import (
    PerformanceProfile, BenchmarkResult, BottleneckFinding,
    PerformanceRegressionFinding, ResourceBudget, CacheEntry, PerformanceReport,
    BenchmarkScenario
)

class PerformanceStore:
    def __init__(self, settings=None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir or Path("data/performance")
        self.profiles_dir = self.base_dir / "profiles"
        self.benchmarks_dir = self.base_dir / "benchmarks"
        self.bottlenecks_dir = self.base_dir / "bottlenecks"
        self.regressions_dir = self.base_dir / "regressions"
        self.budgets_dir = self.base_dir / "budgets"
        self.cache_dir = self.base_dir / "cache"
        self.reports_dir = self.base_dir / "reports"

        for d in [self.profiles_dir, self.benchmarks_dir, self.bottlenecks_dir,
                  self.regressions_dir, self.budgets_dir, self.cache_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def append_profile(self, profile: PerformanceProfile) -> Path:
        path = self.profiles_dir / "performance_profiles.jsonl"
        with open(path, "a") as f:
            f.write(profile.model_dump_json() + "\n")
        return path

    def load_profiles(self, module_name: str | None = None, limit: int = 1000) -> list[PerformanceProfile]:
        path = self.profiles_dir / "performance_profiles.jsonl"
        if not path.exists():
            return []

        profiles = []
        with open(path, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                try:
                    p = PerformanceProfile.model_validate_json(line)
                    if module_name is None or p.module_name == module_name:
                        profiles.append(p)
                        if len(profiles) >= limit:
                            break
                except Exception:
                    pass
        return profiles

    def append_benchmark(self, result: BenchmarkResult) -> Path:
        path = self.benchmarks_dir / "benchmark_results.jsonl"
        with open(path, "a") as f:
            f.write(result.model_dump_json() + "\n")
        return path

    def load_benchmarks(self, scenario: BenchmarkScenario | None = None, limit: int = 1000) -> list[BenchmarkResult]:
        path = self.benchmarks_dir / "benchmark_results.jsonl"
        if not path.exists():
            return []

        results = []
        with open(path, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                try:
                    r = BenchmarkResult.model_validate_json(line)
                    if scenario is None or r.scenario == scenario:
                        results.append(r)
                        if len(results) >= limit:
                            break
                except Exception:
                    pass
        return results

    def append_bottlenecks(self, findings: list[BottleneckFinding]) -> Path:
        path = self.bottlenecks_dir / "bottleneck_findings.jsonl"
        with open(path, "a") as f:
            for finding in findings:
                f.write(finding.model_dump_json() + "\n")
        return path

    def load_bottlenecks(self, limit: int = 1000) -> list[BottleneckFinding]:
        return []

    def append_regressions(self, findings: list[PerformanceRegressionFinding]) -> Path:
        path = self.regressions_dir / "performance_regressions.jsonl"
        with open(path, "a") as f:
            for finding in findings:
                f.write(finding.model_dump_json() + "\n")
        return path

    def load_regressions(self, limit: int = 1000) -> list[PerformanceRegressionFinding]:
        return []

    def save_budgets(self, budgets: list[ResourceBudget]) -> Path:
        path = self.budgets_dir / "resource_budgets.json"
        with open(path, "w") as f:
            json.dump([b.model_dump(mode="json") for b in budgets], f)
        return path

    def load_budgets(self) -> list[ResourceBudget]:
        return []

    def append_cache_entry(self, entry: CacheEntry) -> Path:
        path = self.cache_dir / "cache_index.jsonl"
        with open(path, "a") as f:
            f.write(entry.model_dump_json() + "\n")
        return path

    def load_cache_entries(self, namespace: str | None = None, limit: int = 10000) -> list[CacheEntry]:
        return []

    def save_report(self, report: PerformanceReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        daily_dir = self.reports_dir / date_str
        daily_dir.mkdir(parents=True, exist_ok=True)

        md_path = daily_dir / "performance_report.md"
        json_path = daily_dir / "performance_report.json"

        with open(md_path, "w") as f:
            f.write(markdown_text)

        with open(json_path, "w") as f:
            f.write(report.model_dump_json())

        return {"markdown": md_path, "json": json_path}
