"""Local resource sampler (read-only diagnostics, no network, no orders)."""
import datetime
import os
import shutil

from pydantic import BaseModel, Field


class ResourceSnapshot(BaseModel):
    captured_at: datetime.datetime
    cpu_percent: float | None = None
    memory_rss_mb: float | None = None
    disk_free_mb: float | None = None
    gpu_available: bool = False
    gpu_name: str | None = None
    gpu_utilization_percent: float | None = None
    warnings: list[str] = Field(default_factory=list)


class ResourceSampler:
    def __init__(self, settings=None, path: str | None = None):
        self.settings = settings
        self.path = path or os.getcwd()

    def snapshot(self) -> ResourceSnapshot:
        snap = ResourceSnapshot(captured_at=datetime.datetime.now(datetime.timezone.utc))
        try:
            import psutil  # optional
            snap.cpu_percent = psutil.cpu_percent(interval=None)
            snap.memory_rss_mb = psutil.Process().memory_info().rss / (1024 * 1024)
        except Exception:
            snap.warnings.append("psutil unavailable: CPU/memory not sampled")
        try:
            snap.disk_free_mb = shutil.disk_usage(self.path).free / (1024 * 1024)
        except Exception as e:
            snap.warnings.append(f"disk usage unavailable: {e}")
        return snap
