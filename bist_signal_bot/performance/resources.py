import os
import shutil
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bist_signal_bot.performance.models import (
    ResourceSnapshot, ResourceLevel, PerformanceMetric, PerformanceStatus
)
from bist_signal_bot.config.settings import Settings

class ResourceMonitor:
    def __init__(self, settings: Settings | None = None, logger: logging.Logger | None = None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger("bist_signal_bot.performance.resources")
        self._psutil_available = False
        if self.settings.PERFORMANCE_USE_PSUTIL_IF_AVAILABLE:
            try:
                import psutil
                self._psutil_available = True
            except ImportError:
                self.logger.debug("psutil not available, falling back to stdlib.")

    def snapshot(self) -> ResourceSnapshot:
        snapshot = ResourceSnapshot(timestamp=datetime.now(timezone.utc))

        if self._psutil_available:
            import psutil
            snapshot.cpu_count = psutil.cpu_count(logical=True)
            snapshot.cpu_percent = psutil.cpu_percent(interval=0.1)

            mem = psutil.virtual_memory()
            snapshot.memory_total_mb = mem.total / (1024 * 1024)
            snapshot.memory_used_mb = mem.used / (1024 * 1024)
            snapshot.memory_available_mb = mem.available / (1024 * 1024)
            snapshot.memory_percent = mem.percent

            # Use root dir for overall disk snapshot
            disk = psutil.disk_usage(os.path.abspath(os.sep))
            snapshot.disk_total_mb = disk.total / (1024 * 1024)
            snapshot.disk_used_mb = disk.used / (1024 * 1024)
            snapshot.disk_free_mb = disk.free / (1024 * 1024)
            snapshot.disk_percent = disk.percent
        else:
            snapshot.cpu_count = os.cpu_count()

            disk = shutil.disk_usage(os.path.abspath(os.sep))
            snapshot.disk_total_mb = disk.total / (1024 * 1024)
            snapshot.disk_used_mb = disk.used / (1024 * 1024)
            snapshot.disk_free_mb = disk.free / (1024 * 1024)
            if disk.total > 0:
                snapshot.disk_percent = (disk.used / disk.total) * 100.0

        if self.settings.PERFORMANCE_CHECK_GPU:
            self._check_gpu(snapshot)

        return snapshot

    def _check_gpu(self, snapshot: ResourceSnapshot) -> None:
        if not shutil.which("nvidia-smi"):
            snapshot.gpu_detected = False
            return

        try:
            cmd = ["nvidia-smi", "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader,nounits"]
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=self.settings.PERFORMANCE_GPU_CHECK_TIMEOUT_SECONDS
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(',')
                if len(parts) >= 3:
                    snapshot.gpu_detected = True
                    snapshot.gpu_name = parts[0].strip()
                    snapshot.gpu_memory_total_mb = float(parts[1].strip())
                    snapshot.gpu_memory_used_mb = float(parts[2].strip())
        except Exception as e:
            self.logger.debug(f"Failed to check GPU: {e}")
            snapshot.gpu_detected = False

    def classify_memory_level(self, snapshot: ResourceSnapshot) -> ResourceLevel:
        if snapshot.memory_percent is None:
            return ResourceLevel.UNKNOWN

        if snapshot.memory_percent >= self.settings.PERFORMANCE_MEMORY_CRITICAL_PCT:
            return ResourceLevel.CRITICAL
        elif snapshot.memory_percent >= self.settings.PERFORMANCE_MEMORY_WARN_PCT:
            return ResourceLevel.HIGH
        elif snapshot.memory_percent <= 50.0:
            return ResourceLevel.LOW
        return ResourceLevel.NORMAL

    def classify_disk_level(self, snapshot: ResourceSnapshot) -> ResourceLevel:
        if snapshot.disk_percent is None:
            return ResourceLevel.UNKNOWN

        if snapshot.disk_percent >= self.settings.PERFORMANCE_DISK_CRITICAL_PCT:
            return ResourceLevel.CRITICAL
        elif snapshot.disk_percent >= self.settings.PERFORMANCE_DISK_WARN_PCT:
            return ResourceLevel.HIGH
        elif snapshot.disk_percent <= 50.0:
            return ResourceLevel.LOW
        return ResourceLevel.NORMAL

    def resource_metrics(self, snapshot: ResourceSnapshot) -> list[PerformanceMetric]:
        metrics = []
        if snapshot.cpu_percent is not None:
            metrics.append(PerformanceMetric("cpu_percent", snapshot.cpu_percent, "%"))
        if snapshot.memory_percent is not None:
            status = PerformanceStatus.PASS
            if snapshot.memory_percent >= self.settings.PERFORMANCE_MEMORY_CRITICAL_PCT:
                status = PerformanceStatus.CRITICAL if hasattr(PerformanceStatus, 'CRITICAL') else PerformanceStatus.ERROR
            elif snapshot.memory_percent >= self.settings.PERFORMANCE_MEMORY_WARN_PCT:
                status = PerformanceStatus.WARN
            metrics.append(PerformanceMetric("memory_percent", snapshot.memory_percent, "%", status=status))
        if snapshot.disk_percent is not None:
            status = PerformanceStatus.PASS
            if snapshot.disk_percent >= self.settings.PERFORMANCE_DISK_CRITICAL_PCT:
                status = PerformanceStatus.CRITICAL if hasattr(PerformanceStatus, 'CRITICAL') else PerformanceStatus.ERROR
            elif snapshot.disk_percent >= self.settings.PERFORMANCE_DISK_WARN_PCT:
                status = PerformanceStatus.WARN
            metrics.append(PerformanceMetric("disk_percent", snapshot.disk_percent, "%", status=status))
        return metrics

    def resource_summary_text(self, snapshot: ResourceSnapshot) -> str:
        mem_level = self.classify_memory_level(snapshot).value
        disk_level = self.classify_disk_level(snapshot).value

        parts = []
        parts.append(f"CPU Cores: {snapshot.cpu_count or 'Unknown'}")
        if snapshot.cpu_percent is not None:
            parts.append(f"CPU Usage: {snapshot.cpu_percent:.1f}%")

        parts.append(f"Memory: {mem_level}")
        if snapshot.memory_percent is not None:
            parts.append(f"({snapshot.memory_percent:.1f}%)")

        parts.append(f"Disk: {disk_level}")
        if snapshot.disk_percent is not None:
            parts.append(f"({snapshot.disk_percent:.1f}%)")

        if snapshot.gpu_detected:
            parts.append(f"GPU: {snapshot.gpu_name}")

        return " | ".join(parts)
