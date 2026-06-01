import json
import os
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, UTC

from bist_signal_bot.performance.models import (
    BenchmarkResult,
    BottleneckFinding,
    CacheEntry,
    PerformanceProfile,
    PerformanceRegressionFinding,
    ResourceBudget,
    PerformanceReport,
)
from bist_signal_bot.core.exceptions import BistSignalBotError

class PerformanceStorageError(BistSignalBotError):
    pass

class PerformanceStore:
    def __init__(self, settings: Any = None, base_dir: Optional[Path] = None):
        self.settings = settings
        if base_dir:
            self.base_dir = base_dir
        else:
            try:
                from bist_signal_bot.storage.paths import get_performance_dir
                self.base_dir = get_performance_dir(self.settings)
            except (ImportError, AttributeError):
                self.base_dir = Path("data/performance")

        self.profiles_path = self.base_dir / "profiles" / "performance_profiles.jsonl"
        self.benchmarks_path = self.base_dir / "benchmarks" / "benchmark_results.jsonl"
        self.bottlenecks_path = self.base_dir / "bottlenecks" / "bottleneck_findings.jsonl"
        self.regressions_path = self.base_dir / "regressions" / "performance_regressions.jsonl"
        self.budgets_path = self.base_dir / "budgets" / "resource_budgets.json"
        self.cache_index_path = self.base_dir / "cache" / "cache_index.jsonl"

        self._ensure_dirs()

    def _ensure_dirs(self):
        for p in [self.profiles_path, self.benchmarks_path, self.bottlenecks_path,
                  self.regressions_path, self.budgets_path, self.cache_index_path]:
            p.parent.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, file_path: Path, item: Any) -> Path:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(item.model_dump_json() + "\n")
        return file_path

    def _load_jsonl(self, file_path: Path, model_cls: Any, limit: int) -> list[Any]:
        if not file_path.exists():
            return []
        items = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(model_cls.model_validate_json(line))
        return items[-limit:]

    def append_profile(self, profile: PerformanceProfile) -> Path:
        return self._append_jsonl(self.profiles_path, profile)

    def load_profiles(self, module_name: Optional[str] = None, limit: int = 1000) -> list[PerformanceProfile]:
        profiles = self._load_jsonl(self.profiles_path, PerformanceProfile, limit)
        if module_name:
            profiles = [p for p in profiles if p.module_name == module_name]
        return profiles

    def append_benchmark(self, result: BenchmarkResult) -> Path:
        return self._append_jsonl(self.benchmarks_path, result)

    def load_benchmarks(self, scenario: Optional[Any] = None, limit: int = 1000) -> list[BenchmarkResult]:
        benchmarks = self._load_jsonl(self.benchmarks_path, BenchmarkResult, limit)
        if scenario:
            benchmarks = [b for b in benchmarks if b.scenario == scenario]
        return benchmarks

    def append_bottlenecks(self, findings: list[BottleneckFinding]) -> Path:
        for finding in findings:
            self._append_jsonl(self.bottlenecks_path, finding)
        return self.bottlenecks_path

    def load_bottlenecks(self, limit: int = 1000) -> list[BottleneckFinding]:
        return self._load_jsonl(self.bottlenecks_path, BottleneckFinding, limit)

    def append_regressions(self, findings: list[PerformanceRegressionFinding]) -> Path:
        for finding in findings:
            self._append_jsonl(self.regressions_path, finding)
        return self.regressions_path

    def load_regressions(self, limit: int = 1000) -> list[PerformanceRegressionFinding]:
        return self._load_jsonl(self.regressions_path, PerformanceRegressionFinding, limit)

    def save_budgets(self, budgets: list[ResourceBudget]) -> Path:
        data = [b.model_dump() for b in budgets]
        with open(self.budgets_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return self.budgets_path

    def load_budgets(self) -> list[ResourceBudget]:
        if not self.budgets_path.exists():
            return []
        with open(self.budgets_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [ResourceBudget.model_validate(b) for b in data]

    def append_cache_entry(self, entry: CacheEntry) -> Path:
        return self._append_jsonl(self.cache_index_path, entry)

    def load_cache_entries(self, namespace: Optional[str] = None, limit: int = 10000) -> list[CacheEntry]:
        entries = self._load_jsonl(self.cache_index_path, CacheEntry, limit)
        if namespace:
            entries = [e for e in entries if e.namespace == namespace]
        return entries

    def save_report(self, report: PerformanceReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self.base_dir / "reports" / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        md_path = report_dir / "performance_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        json_path = report_dir / "performance_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        return {"markdown": md_path, "json": json_path}

