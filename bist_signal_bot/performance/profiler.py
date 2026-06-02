
import uuid
import time
from datetime import datetime, timezone
from typing import Callable, Any, Optional
from bist_signal_bot.performance.models import (
    PerformanceProfile, TimingMeasurement, ResourceMeasurement,
    PerformanceStatus, ResourceKind
)

class LocalPerformanceProfiler:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def profile_command(self, command: str, dry_run: bool = True) -> PerformanceProfile:
        start_time = datetime.now(timezone.utc)
        time.sleep(0.01) # fake execution
        end_time = datetime.now(timezone.utc)

        tm = TimingMeasurement(
            timing_id=f"tm_{uuid.uuid4().hex[:8]}",
            name="command_exec",
            started_at=start_time,
            finished_at=end_time,
            elapsed_seconds=(end_time - start_time).total_seconds(),
            status=PerformanceStatus.PASS
        )

        return PerformanceProfile(
            profile_id=f"prof_{uuid.uuid4().hex[:8]}",
            created_at=start_time,
            module_name="cli",
            command=command,
            timings=[tm],
            status=PerformanceStatus.PASS
        )

    def profile_module(self, module_name: str) -> PerformanceProfile:
        return PerformanceProfile(
            profile_id=f"prof_{uuid.uuid4().hex[:8]}",
            created_at=datetime.now(timezone.utc),
            module_name=module_name,
            status=PerformanceStatus.PASS
        )

    def profile_callable(self, name: str, fn: Callable[..., Any], *args, **kwargs) -> PerformanceProfile:
        start_time = datetime.now(timezone.utc)
        fn(*args, **kwargs)
        end_time = datetime.now(timezone.utc)

        tm = TimingMeasurement(
            timing_id=f"tm_{uuid.uuid4().hex[:8]}",
            name=name,
            started_at=start_time,
            finished_at=end_time,
            elapsed_seconds=(end_time - start_time).total_seconds(),
            status=PerformanceStatus.PASS
        )
        return PerformanceProfile(
            profile_id=f"prof_{uuid.uuid4().hex[:8]}",
            created_at=start_time,
            module_name="callable",
            timings=[tm],
            status=PerformanceStatus.PASS
        )

    def collect_resource_measurements(self, module_name: str, command: Optional[str] = None) -> list[ResourceMeasurement]:
        return []

    def profile_summary(self, profile: PerformanceProfile) -> list[str]:
        return [f"Profile {profile.profile_id} for {profile.module_name} status: {profile.status}"]

    def classify_profile(self, timings: list[TimingMeasurement], resources: list[ResourceMeasurement]) -> PerformanceStatus:
        for t in timings:
            if t.status == PerformanceStatus.FAIL:
                return PerformanceStatus.FAIL
        return PerformanceStatus.PASS
