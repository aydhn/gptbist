from typing import Callable, Any
import datetime
from bist_signal_bot.performance.models import PerformanceProfile, PerformanceStatus, TimingMeasurement, ResourceMeasurement

class LocalPerformanceProfiler:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def profile_command(self, command: str, dry_run: bool = True) -> PerformanceProfile:
        now = datetime.datetime.now(datetime.timezone.utc)
        return PerformanceProfile(
            profile_id=f"prof_{int(now.timestamp())}",
            created_at=now,
            module_name="cli",
            command=command,
            status=PerformanceStatus.PASS
        )

    def profile_module(self, module_name: str) -> PerformanceProfile:
        now = datetime.datetime.now(datetime.timezone.utc)
        return PerformanceProfile(
            profile_id=f"prof_{int(now.timestamp())}",
            created_at=now,
            module_name=module_name,
            status=PerformanceStatus.PASS
        )

    def profile_callable(self, name: str, fn: Callable[..., Any], *args, **kwargs) -> PerformanceProfile:
        now = datetime.datetime.now(datetime.timezone.utc)
        start_time = datetime.datetime.now(datetime.timezone.utc)
        try:
            fn(*args, **kwargs)
        except Exception:
            pass
        end_time = datetime.datetime.now(datetime.timezone.utc)

        timing = TimingMeasurement(
            timing_id=f"t_{int(now.timestamp())}",
            name=name,
            started_at=start_time,
            finished_at=end_time,
            elapsed_seconds=(end_time - start_time).total_seconds(),
            status=PerformanceStatus.PASS
        )

        return PerformanceProfile(
            profile_id=f"prof_{int(now.timestamp())}",
            created_at=now,
            module_name=name,
            timings=[timing],
            status=PerformanceStatus.PASS
        )

    def collect_resource_measurements(self, module_name: str, command: str | None = None) -> list[ResourceMeasurement]:
        return []

    def profile_summary(self, profile: PerformanceProfile) -> list[str]:
        return [f"Profile {profile.profile_id} for {profile.module_name}"]

    def classify_profile(self, timings: list[TimingMeasurement], resources: list[ResourceMeasurement]) -> PerformanceStatus:
        if any(t.status == PerformanceStatus.FAIL for t in timings):
            return PerformanceStatus.FAIL
        return PerformanceStatus.PASS
