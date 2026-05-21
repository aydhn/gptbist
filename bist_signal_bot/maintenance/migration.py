import time
from pathlib import Path
from bist_signal_bot.maintenance.models import (
    MigrationPlan,
    MigrationResult,
    MigrationStatus
)
from bist_signal_bot.core.exceptions import MigrationError
from bist_signal_bot.config.settings import get_settings

class MigrationManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.settings = get_settings()

    def current_schema_version(self) -> str:
        version_file = self.base_dir / ".schema_version"
        if version_file.exists():
            return version_file.read_text().strip()
        return "1.0.0"

    def target_schema_version(self) -> str:
        return getattr(self.settings, "SCHEMA_VERSION", "1.0.0")

    def plan_migration(self, to_version: str | None = None) -> MigrationPlan:
        from_v = self.current_schema_version()
        to_v = to_version or self.target_schema_version()

        status = MigrationStatus.PLANNED
        steps = []
        if from_v == to_v:
            status = MigrationStatus.NOT_REQUIRED
        else:
            # MVP: just a no-op step for structural readiness
            steps.append({
                "type": "no-op",
                "description": f"Ready to migrate from {from_v} to {to_v}"
            })

        return MigrationPlan(
            migration_id=f"mig_{int(time.time())}",
            from_schema_version=from_v,
            to_schema_version=to_v,
            status=status,
            steps=steps,
            requires_backup=getattr(self.settings, "MIGRATION_REQUIRE_BACKUP", True),
            destructive=False
        )

    def apply_migration(self, plan: MigrationPlan, confirm: bool = False, backup_id: str | None = None) -> MigrationResult:
        if not confirm:
            raise MigrationError("Migration can be destructive. 'confirm' must be True to proceed.")

        if plan.requires_backup and not backup_id:
             raise MigrationError("This migration requires a backup_id to proceed safely.")

        start_time = time.time()

        if plan.status == MigrationStatus.NOT_REQUIRED:
            return MigrationResult(
                migration_id=plan.migration_id,
                status=MigrationStatus.NOT_REQUIRED,
                elapsed_seconds=0
            )

        # MVP: Apply the no-op migration
        applied = 0
        for step in plan.steps:
            applied += 1

        self.write_schema_version(plan.to_schema_version, confirm=True)

        return MigrationResult(
            migration_id=plan.migration_id,
            status=MigrationStatus.APPLIED,
            backup_id=backup_id,
            applied_steps=applied,
            elapsed_seconds=time.time() - start_time
        )

    def write_schema_version(self, version: str, confirm: bool = False) -> Path:
        if not confirm:
             raise MigrationError("Confirm required to update schema version")
        version_file = self.base_dir / ".schema_version"
        version_file.write_text(version)
        return version_file
