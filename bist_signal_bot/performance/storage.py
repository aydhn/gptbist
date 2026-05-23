import csv
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.models import (
    ProfileResult, BenchmarkRunResult, PerformanceBaseline, PerformanceRegressionResult, BenchmarkType
)
from bist_signal_bot.storage.paths import get_performance_dir

class PerformanceStore:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or get_performance_dir(self.settings)

    def _date_str(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")

    def save_profile(self, profile: ProfileResult) -> Dict[str, Path]:
        if not getattr(self.settings, 'PERFORMANCE_SAVE_PROFILES', True):
            return {}

        date_folder = self.base_dir / "profiles" / self._date_str() / profile.profile_id
        date_folder.mkdir(parents=True, exist_ok=True)

        json_path = date_folder / "profile_result.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(profile.model_dump_json(indent=2))

        # Append to master CSV
        csv_path = self.base_dir / "profiles.csv"
        file_exists = csv_path.exists()
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["profile_id", "benchmark_type", "started_at", "elapsed_seconds", "status"])
            writer.writerow([
                profile.profile_id,
                profile.benchmark_type.value,
                profile.started_at.isoformat(),
                profile.elapsed_seconds,
                profile.status.value
            ])

        return {"json": json_path, "csv": csv_path}

    def save_benchmark(self, result: BenchmarkRunResult) -> Dict[str, Path]:
        if not getattr(self.settings, 'PERFORMANCE_SAVE_BENCHMARKS', True):
            return {}

        date_folder = self.base_dir / "benchmarks" / self._date_str() / result.benchmark_id
        date_folder.mkdir(parents=True, exist_ok=True)

        json_path = date_folder / "benchmark_result.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        # Link latest for benchmark type
        latest_dir = self.base_dir / "benchmarks" / "latest"
        latest_dir.mkdir(parents=True, exist_ok=True)
        latest_path = latest_dir / f"{result.request.benchmark_type.value}.json"

        # Soft-copy for compatibility
        import shutil
        shutil.copy2(json_path, latest_path)

        return {"json": json_path}

    def load_benchmark(self, benchmark_id: str) -> Optional[BenchmarkRunResult]:
        benchmarks_dir = self.base_dir / "benchmarks"
        if not benchmarks_dir.exists():
            return None

        for date_dir in benchmarks_dir.iterdir():
            if date_dir.is_dir() and date_dir.name != "latest":
                target_dir = date_dir / benchmark_id
                if target_dir.exists():
                    try:
                        with open(target_dir / "benchmark_result.json", "r", encoding="utf-8") as f:
                            return BenchmarkRunResult.model_validate_json(f.read())
                    except Exception:
                        pass
        return None

    def load_latest_benchmark(self, benchmark_type: Optional[BenchmarkType] = None) -> Optional[BenchmarkRunResult]:
        if not benchmark_type:
            return None # Requires type to load specific latest

        latest_path = self.base_dir / "benchmarks" / "latest" / f"{benchmark_type.value}.json"
        if not latest_path.exists():
            return None

        try:
            with open(latest_path, "r", encoding="utf-8") as f:
                return BenchmarkRunResult.model_validate_json(f.read())
        except Exception:
            return None

    def save_baseline(self, baseline: PerformanceBaseline) -> Path:
        # Relies on BaselineManager usually, but putting here for completeness
        from bist_signal_bot.performance.baseline import PerformanceBaselineManager
        mgr = PerformanceBaselineManager(self.settings, self.base_dir)
        return mgr.save_baseline(baseline)

    def load_latest_baseline(self, benchmark_type: Optional[BenchmarkType] = None) -> Optional[PerformanceBaseline]:
        from bist_signal_bot.performance.baseline import PerformanceBaselineManager
        mgr = PerformanceBaselineManager(self.settings, self.base_dir)
        return mgr.load_latest_baseline(benchmark_type)

    def save_regression(self, result: PerformanceRegressionResult) -> Dict[str, Path]:
        date_folder = self.base_dir / "regressions" / self._date_str() / result.regression_id
        date_folder.mkdir(parents=True, exist_ok=True)

        json_path = date_folder / "regression_result.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        return {"json": json_path}

    def list_recent_benchmarks(self, limit: int = 20) -> List[Dict[str, Any]]:
        benchmarks_dir = self.base_dir / "benchmarks"
        if not benchmarks_dir.exists():
            return []

        all_b = []
        for date_dir in benchmarks_dir.iterdir():
            if date_dir.is_dir() and date_dir.name != "latest":
                for b_dir in date_dir.iterdir():
                    if b_dir.is_dir():
                        json_path = b_dir / "benchmark_result.json"
                        if json_path.exists():
                            all_b.append((json_path.stat().st_mtime, json_path))

        all_b.sort(key=lambda x: x[0], reverse=True)

        results = []
        for _, path in all_b[:limit]:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = BenchmarkRunResult.model_validate_json(f.read())
                    results.append(data.summary())
            except Exception:
                pass

        return results

