import uuid
import datetime
import time
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pynvml
    HAS_PYNVML = True
except ImportError:
    HAS_PYNVML = False

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.models import ResourceSnapshot
from bist_signal_bot.core.exceptions import ResourceSamplingError

class ResourceSampler:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self._use_psutil = getattr(self.settings, 'PERFORMANCE_USE_PSUTIL', True) and HAS_PSUTIL
        self._use_gpu = getattr(self.settings, 'PERFORMANCE_USE_GPU_SAMPLING', True)

        global HAS_PYNVML
        if self._use_gpu and HAS_PYNVML:
            try:
                pynvml.nvmlInit()
            except Exception:
                self._use_gpu = False
                HAS_PYNVML = False

    def memory_rss_mb(self) -> Optional[float]:
        if self._use_psutil:
            try:
                process = psutil.Process()
                return process.memory_info().rss / (1024 * 1024)
            except Exception:
                pass
        return None

    def cpu_percent(self) -> Optional[float]:
        if self._use_psutil:
            try:
                return psutil.cpu_percent(interval=None)
            except Exception:
                pass
        return None

    def disk_free_mb(self, path: Optional[Path] = None) -> Optional[float]:
        try:
            path_str = str(path.absolute()) if path else "/"
            total, used, free = shutil.disk_usage(path_str)
            return free / (1024 * 1024)
        except Exception:
            pass
        return None

    def gpu_snapshot(self) -> Dict[str, Any]:
        if not self._use_gpu:
            return {"gpu_available": False}

        if HAS_PYNVML:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(handle)
                # Decode if needed (pynvml might return bytes)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')

                meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)

                return {
                    "gpu_available": True,
                    "gpu_name": name,
                    "gpu_memory_used_mb": meminfo.used / (1024 * 1024),
                    "gpu_memory_total_mb": meminfo.total / (1024 * 1024),
                    "gpu_utilization_percent": float(util.gpu)
                }
            except Exception:
                pass

        # Fallback to nvidia-smi
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
                timeout=2.0
            ).decode('utf-8').strip().split('\n')[0].split(',')

            return {
                "gpu_available": True,
                "gpu_name": output[0].strip(),
                "gpu_memory_used_mb": float(output[1].strip()),
                "gpu_memory_total_mb": float(output[2].strip()),
                "gpu_utilization_percent": float(output[3].strip())
            }
        except Exception:
            return {"gpu_available": False}

    def snapshot(self) -> ResourceSnapshot:
        gpu_info = self.gpu_snapshot()
        warnings = []
        if not self._use_psutil:
            warnings.append("psutil not available or disabled, CPU metrics may be missing")

        return ResourceSnapshot(
            snapshot_id=str(uuid.uuid4()),
            captured_at=datetime.datetime.now(datetime.timezone.utc),
            cpu_percent=self.cpu_percent(),
            memory_rss_mb=self.memory_rss_mb(),
            disk_free_mb=self.disk_free_mb(),
            gpu_available=gpu_info.get("gpu_available", False),
            gpu_name=gpu_info.get("gpu_name"),
            gpu_memory_used_mb=gpu_info.get("gpu_memory_used_mb"),
            gpu_memory_total_mb=gpu_info.get("gpu_memory_total_mb"),
            gpu_utilization_percent=gpu_info.get("gpu_utilization_percent"),
            warnings=warnings
        )

    def sample_during(self, func: Callable, interval_seconds: float = 0.5) -> Tuple[Any, List[ResourceSnapshot]]:
        snapshots = []
        stop_event = threading.Event()

        def sampler_loop():
            # Initial snapshot
            snapshots.append(self.snapshot())
            while not stop_event.is_set():
                if stop_event.wait(interval_seconds):
                    break
                # Only keep up to a max to prevent memory leak on very long runs
                if len(snapshots) < getattr(self.settings, 'PERFORMANCE_MAX_RESOURCE_SNAPSHOTS', 500):
                    snapshots.append(self.snapshot())

        sampler_thread = threading.Thread(target=sampler_loop, daemon=True)
        sampler_thread.start()

        try:
            result = func()
        finally:
            stop_event.set()
            sampler_thread.join(timeout=1.0)
            # Final snapshot
            snapshots.append(self.snapshot())

        return result, snapshots

