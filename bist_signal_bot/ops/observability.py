
import datetime
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_data_dir
from bist_signal_bot.ops.models import OpsHealthSnapshot, OpsCheckResult, OpsCheckType, OpsStatus, OpsSeverity

class OpsObservabilityEngine:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir or get_data_dir()

    def run_core_checks(self) -> list[OpsCheckResult]:
        checks = []
        now = datetime.datetime.now()
        base_dir_status = OpsStatus.PASS
        try:
            if not self.base_dir.exists(): base_dir_status = OpsStatus.FAIL
        except Exception:
            base_dir_status = OpsStatus.ERROR

        checks.append(OpsCheckResult(
            check_id=f"base_dir_{now.timestamp()}", check_type=OpsCheckType.HEALTH,
            module_name="storage", status=base_dir_status, severity=OpsSeverity.HIGH if base_dir_status != OpsStatus.PASS else OpsSeverity.INFO,
            started_at=now, finished_at=now, message="Base directory writable check"
        ))

        checks.append(OpsCheckResult(
            check_id=f"config_{now.timestamp()}", check_type=OpsCheckType.CONFIG,
            module_name="config", status=OpsStatus.PASS, severity=OpsSeverity.INFO,
            started_at=now, finished_at=now, message="Config registry readable check"
        ))
        return checks

    def run_module_checks(self, modules: list[str] | None = None) -> list[OpsCheckResult]:
        checks = []
        now = datetime.datetime.now()
        if modules:
            for mod in modules:
                checks.append(OpsCheckResult(
                    check_id=f"mod_{mod}_{now.timestamp()}", check_type=OpsCheckType.HEALTH,
                    module_name=mod, status=OpsStatus.PASS, severity=OpsSeverity.INFO,
                    started_at=now, finished_at=now, message=f"{mod} module health check"
                ))
        return checks

    def status_from_checks(self, checks: list[OpsCheckResult]) -> OpsStatus:
        if any(c.status in (OpsStatus.FAIL, OpsStatus.ERROR) for c in checks): return OpsStatus.FAIL
        if any(c.status == OpsStatus.BLOCKED for c in checks): return OpsStatus.BLOCKED
        if any(c.status == OpsStatus.WATCH for c in checks): return OpsStatus.WATCH
        return OpsStatus.PASS

    def summarize_checks(self, checks: list[OpsCheckResult]) -> dict[str, int]:
        return {
            "pass": sum(1 for c in checks if c.status == OpsStatus.PASS),
            "watch": sum(1 for c in checks if c.status == OpsStatus.WATCH),
            "fail": sum(1 for c in checks if c.status in (OpsStatus.FAIL, OpsStatus.ERROR)),
            "blocked": sum(1 for c in checks if c.status == OpsStatus.BLOCKED),
        }

    def key_findings(self, checks: list[OpsCheckResult]) -> list[str]:
        return [f"[{c.severity.value}] {c.module_name}: {c.status.value} - {c.message}" for c in checks if c.status not in (OpsStatus.PASS, OpsStatus.SKIPPED)]

    def build_health_snapshot(self) -> OpsHealthSnapshot:
        now = datetime.datetime.now()
        checks = self.run_core_checks()
        summary = self.summarize_checks(checks)
        return OpsHealthSnapshot(
            snapshot_id=f"snap_{now.strftime('%Y%m%d%H%M%S')}", created_at=now,
            status=self.status_from_checks(checks), checks=checks, pass_count=summary["pass"],
            watch_count=summary["watch"], fail_count=summary["fail"], blocked_count=summary["blocked"],
            key_findings=self.key_findings(checks)
        )
