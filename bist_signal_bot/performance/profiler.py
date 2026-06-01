import uuid
from datetime import datetime, UTC
from typing import Any, Callable, Optional
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from bist_signal_bot.performance.models import (
    PerformanceProfile,
    PerformanceStatus,
    ResourceKind,
    ResourceMeasurement,
    TimingMeasurement,
)
from bist_signal_bot.performance.timers import PerformanceTimer
from bist_signal_bot.core.exceptions import BistSignalBotError

class PerformanceProfilerError(BistSignalBotError):
    pass

class LocalPerformanceProfiler:
    def __init__(self, settings: Any = None, base_dir: Any = None):
        self.settings = settings
        self.timer = PerformanceTimer()

    def profile_command(self, command: str, dry_run: bool = True) -> PerformanceProfile:
        started_at = datetime.now(UTC)
        timings = []
        resources = []

        measurement = self.timer.start(f"command:{command}")

        if self.settings and not getattr(self.settings, "PERFORMANCE_PROFILE_COMMANDS", True):
            self.timer.finish(measurement, PerformanceStatus.SKIPPED)
            timings.append(measurement)
            return PerformanceProfile(
                profile_id=str(uuid.uuid4()),
                created_at=started_at,
                module_name="cli_command",
                command=command,
                timings=timings,
                resources=resources,
                cache_results=[],
                status=PerformanceStatus.SKIPPED
            )

        # Mock the run for testing/profiling
        self.timer.finish(measurement, PerformanceStatus.PASS)
        timings.append(measurement)
        resources = self.collect_resource_measurements("cli_command", command)

        status = self.classify_profile(timings, resources)

        return PerformanceProfile(
            profile_id=str(uuid.uuid4()),
            created_at=started_at,
            module_name="cli_command",
            command=command,
            timings=timings,
            resources=resources,
            cache_results=[],
            status=status
        )

    def profile_module(self, module_name: str) -> PerformanceProfile:
        started_at = datetime.now(UTC)
        timings = []

        measurement = self.timer.start(f"module:{module_name}")
        self.timer.finish(measurement, PerformanceStatus.PASS)
        timings.append(measurement)

        resources = self.collect_resource_measurements(module_name)
        status = self.classify_profile(timings, resources)

        return PerformanceProfile(
            profile_id=str(uuid.uuid4()),
            created_at=started_at,
            module_name=module_name,
            timings=timings,
            resources=resources,
            cache_results=[],
            status=status
        )

    def profile_callable(self, name: str, fn: Callable[..., Any], *args, **kwargs) -> PerformanceProfile:
        started_at = datetime.now(UTC)
        timings = []

        measurement = self.timer.start(f"callable:{name}")

        try:
            fn(*args, **kwargs)
            self.timer.finish(measurement, PerformanceStatus.PASS)
        except Exception as e:
            measurement.warnings.append(str(e))
            self.timer.finish(measurement, PerformanceStatus.FAIL)

        timings.append(measurement)
        resources = self.collect_resource_measurements(name)
        status = self.classify_profile(timings, resources)

        return PerformanceProfile(
            profile_id=str(uuid.uuid4()),
            created_at=started_at,
            module_name=name,
            timings=timings,
            resources=resources,
            cache_results=[],
            status=status
        )

    def collect_resource_measurements(self, module_name: str, command: Optional[str] = None) -> list[ResourceMeasurement]:
        measurements = []
        now = datetime.now(UTC)

        collect_resources = True
        if self.settings and not getattr(self.settings, "PERFORMANCE_COLLECT_RESOURCE_USAGE", True):
            collect_resources = False

        if not collect_resources:
            return measurements

        # CPU
        if HAS_PSUTIL:
            cpu_pct = psutil.cpu_percent(interval=None)
            measurements.append(
                ResourceMeasurement(
                    measurement_id=str(uuid.uuid4()),
                    resource_kind=ResourceKind.CPU,
                    module_name=module_name,
                    command=command,
                    value=cpu_pct,
                    unit="pct",
                    status=PerformanceStatus.PASS,
                    measured_at=now
                )
            )
        else:
            measurements.append(
                ResourceMeasurement(
                    measurement_id=str(uuid.uuid4()),
                    resource_kind=ResourceKind.CPU,
                    module_name=module_name,
                    command=command,
                    value=None,
                    unit="pct",
                    status=PerformanceStatus.WATCH,
                    measured_at=now,
                    warnings=["psutil not available"]
                )
            )

        # Memory
        if HAS_PSUTIL:
            mem = psutil.virtual_memory()
            measurements.append(
                ResourceMeasurement(
                    measurement_id=str(uuid.uuid4()),
                    resource_kind=ResourceKind.MEMORY,
                    module_name=module_name,
                    command=command,
                    value=float(mem.used) / (1024 * 1024),
                    unit="MB",
                    status=PerformanceStatus.PASS,
                    measured_at=now
                )
            )
        else:
            measurements.append(
                ResourceMeasurement(
                    measurement_id=str(uuid.uuid4()),
                    resource_kind=ResourceKind.MEMORY,
                    module_name=module_name,
                    command=command,
                    value=None,
                    unit="MB",
                    status=PerformanceStatus.WATCH,
                    measured_at=now,
                    warnings=["psutil not available"]
                )
            )

        return measurements

    def profile_summary(self, profile: PerformanceProfile) -> list[str]:
        summary = [f"Profile: {profile.module_name} (Status: {profile.status.value})"]
        if profile.command:
            summary.append(f"Command: {profile.command}")

        for t in profile.timings:
            val = f"{t.elapsed_seconds:.4f}s" if t.elapsed_seconds is not None else "N/A"
            summary.append(f"Timing {t.name}: {val} [{t.status.value}]")

        for r in profile.resources:
            val = f"{r.value:.2f}{r.unit}" if r.value is not None else "N/A"
            summary.append(f"Resource {r.resource_kind.value}: {val} [{r.status.value}]")

        return summary

    def classify_profile(self, timings: list[TimingMeasurement], resources: list[ResourceMeasurement]) -> PerformanceStatus:
        all_statuses = [t.status for t in timings] + [r.status for r in resources]

        if not all_statuses:
            return PerformanceStatus.UNKNOWN

        if PerformanceStatus.FAIL in all_statuses:
            return PerformanceStatus.FAIL
        if PerformanceStatus.DEGRADED in all_statuses:
            return PerformanceStatus.DEGRADED
        if PerformanceStatus.SLOW in all_statuses:
            return PerformanceStatus.SLOW
        if PerformanceStatus.WATCH in all_statuses:
            return PerformanceStatus.WATCH
        if PerformanceStatus.SKIPPED in all_statuses:
            return PerformanceStatus.SKIPPED

        return PerformanceStatus.PASS

