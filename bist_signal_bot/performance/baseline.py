import uuid
import datetime
import hashlib
import platform
try:
    import psutil
except ImportError:
    psutil = None
from typing import Optional, List
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.models import (
    BenchmarkRunResult, PerformanceBaseline, BenchmarkType
)
from bist_signal_bot.core.exceptions import PerformanceBaselineError

class PerformanceBaselineManager:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings or Settings()
        from bist_signal_bot.storage.paths import get_performance_dir
        self.base_dir = base_dir or get_performance_dir(self.settings)

    def environment_hash(self) -> str:
        # Create a hash of the environment (OS, CPU count, total RAM)
        # Avoids secrets. Safe operational metadata.
        env_str = f"{platform.system()}-{platform.machine()}-{platform.python_version()}"
        try:
            env_str += f"-{psutil.cpu_count() if psutil else 'unk'}-{psutil.virtual_memory().total if psutil else 'unk'}"
        except Exception:
            pass
        return hashlib.sha256(env_str.encode('utf-8')).hexdigest()[:12]

    def create_baseline(self, result: BenchmarkRunResult, notes: Optional[str] = None, confirm: bool = False) -> PerformanceBaseline:
        if not confirm:
            raise PerformanceBaselineError("Creating a baseline requires explicit confirmation.")

        metrics = {
            "median_elapsed_seconds": result.median_elapsed_seconds or 0.0,
            "p95_elapsed_seconds": result.p95_elapsed_seconds or 0.0
        }
        if result.max_memory_peak_mb:
            metrics["max_memory_peak_mb"] = result.max_memory_peak_mb
        if result.throughput_items_per_second:
            metrics["throughput_items_per_second"] = result.throughput_items_per_second

        return PerformanceBaseline(
            baseline_id=str(uuid.uuid4()),
            created_at=datetime.datetime.now(datetime.timezone.utc),
            benchmark_type=result.request.benchmark_type,
            environment_hash=self.environment_hash(),
            metrics=metrics,
            sample_size=result.request.sample_size,
            iterations=result.request.iterations,
            notes=notes
        )

    def save_baseline(self, baseline: PerformanceBaseline) -> Path:
        baseline_dir = self.base_dir / "baselines" / baseline.benchmark_type.value
        baseline_dir.mkdir(parents=True, exist_ok=True)
        file_path = baseline_dir / f"{baseline.baseline_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(baseline.model_dump_json(indent=2))

        # Update latest symlink/file
        latest_path = baseline_dir / "latest.json"
        if latest_path.exists() or latest_path.is_symlink():
            latest_path.unlink()
        try:
            latest_path.symlink_to(file_path.name)
        except OSError:
            # Fallback to copying if symlinks aren't supported (e.g. some Windows)
            import shutil
            shutil.copy2(file_path, latest_path)

        return file_path

    def load_latest_baseline(self, benchmark_type: Optional[BenchmarkType] = None) -> Optional[PerformanceBaseline]:
        if not benchmark_type:
            # Simplification: we expect a type usually. If none, grab the most recently modified file in any type dir.
            all_latest = []
            baselines_dir = self.base_dir / "baselines"
            if not baselines_dir.exists():
                return None
            for btype_dir in baselines_dir.iterdir():
                if btype_dir.is_dir():
                    l_path = btype_dir / "latest.json"
                    if l_path.exists():
                        all_latest.append((l_path.stat().st_mtime, l_path))
            if not all_latest:
                return None
            all_latest.sort(key=lambda x: x[0], reverse=True)
            latest_path = all_latest[0][1]
        else:
            latest_path = self.base_dir / "baselines" / benchmark_type.value / "latest.json"
            if not latest_path.exists():
                return None

        try:
            with open(latest_path, "r", encoding="utf-8") as f:
                return PerformanceBaseline.model_validate_json(f.read())
        except Exception:
            return None

    def list_baselines(self, limit: int = 20) -> List[PerformanceBaseline]:
        baselines = []
        baselines_dir = self.base_dir / "baselines"
        if not baselines_dir.exists():
            return baselines

        # Collect all json except latest
        all_files = []
        for btype_dir in baselines_dir.iterdir():
            if btype_dir.is_dir():
                for f in btype_dir.glob("*.json"):
                    if f.name != "latest.json":
                        all_files.append((f.stat().st_mtime, f))

        all_files.sort(key=lambda x: x[0], reverse=True)
        for _, path in all_files[:limit]:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    baselines.append(PerformanceBaseline.model_validate_json(f.read()))
            except Exception:
                pass

        return baselines
