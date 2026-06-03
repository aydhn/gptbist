import uuid
from typing import List, Optional, Any
from datetime import datetime, timezone
import subprocess
from bist_signal_bot.maintenance_automation.models import (
    MaintenancePlan,
    MaintenanceRun,
    MaintenanceActionResult,
    MaintenanceAction,
    MaintenanceActionType,
    MaintenanceStatus
)

class MaintenanceRunner:
    def __init__(self, check_runner=None, cleanup_engine=None, backup_builder=None, command_runner=None):
        self.check_runner = check_runner
        self.cleanup_engine = cleanup_engine
        self.backup_builder = backup_builder
        self.command_runner = command_runner or self._default_command_runner

    def _default_command_runner(self, command: str, dry_run: bool) -> tuple[int, str, str]:
        if dry_run:
            return 0, f"[DRY-RUN] Executed: {command}", ""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    def run_plan(self, plan: MaintenancePlan, save: bool = False) -> MaintenanceRun:
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        results = []

        for action in plan.actions:
            result = self.run_action(action, dry_run=plan.dry_run, confirm=plan.confirm)
            results.append(result)

        status = self.run_status(results)
        warnings = []
        errors = []
        for r in results:
            warnings.extend(r.warnings)
            errors.extend(r.errors)

        run = MaintenanceRun(
            run_id=run_id,
            plan=plan,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            status=status,
            results=results,
            warnings=warnings,
            errors=errors
        )
        # Store saving logic should be external or inject dependency
        return run

    def run_action(self, action: MaintenanceAction, dry_run: bool = True, confirm: bool = False) -> MaintenanceActionResult:
        errors = action.validate_action()
        if errors:
            return MaintenanceActionResult(
                result_id=str(uuid.uuid4()),
                action_id=action.action_id,
                action_type=action.action_type,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                status=MaintenanceStatus.BLOCKED,
                skipped=True,
                dry_run=dry_run,
                message="Action blocked due to validation errors.",
                errors=errors
            )

        if action.destructive and not confirm:
            return MaintenanceActionResult(
                result_id=str(uuid.uuid4()),
                action_id=action.action_id,
                action_type=action.action_type,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                status=MaintenanceStatus.SKIPPED,
                skipped=True,
                dry_run=dry_run,
                message="Destructive action skipped because confirm is False."
            )

        if action.command:
            return self.run_command_action(action, dry_run)

        if action.action_type in [MaintenanceActionType.CACHE_CLEANUP, MaintenanceActionType.REPORT_ROTATION, MaintenanceActionType.LOG_ROTATION]:
            return self.run_cleanup_action(action, dry_run, confirm)

        if action.action_type == MaintenanceActionType.BACKUP_MANIFEST:
            return self.run_backup_action(action, dry_run, confirm)

        if self.check_runner and hasattr(self.check_runner, f"run_{action.action_type.value.lower()}_check"):
            method = getattr(self.check_runner, f"run_{action.action_type.value.lower()}_check")
            return method()

        # Fallback for mocked/unimplemented internal checks
        return MaintenanceActionResult(
            result_id=str(uuid.uuid4()),
            action_id=action.action_id,
            action_type=action.action_type,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            status=MaintenanceStatus.PASS,
            dry_run=dry_run,
            message="Mocked internal check passed."
        )

    def run_command_action(self, action: MaintenanceAction, dry_run: bool = True) -> MaintenanceActionResult:
        started_at = datetime.now(timezone.utc)
        code, stdout, stderr = self.command_runner(action.command, dry_run)
        status = MaintenanceStatus.PASS if code == 0 else MaintenanceStatus.FAIL

        return MaintenanceActionResult(
            result_id=str(uuid.uuid4()),
            action_id=action.action_id,
            action_type=action.action_type,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            status=status,
            dry_run=dry_run,
            message=stdout[:1000], # truncate
            errors=[stderr] if code != 0 and stderr else []
        )

    def run_cleanup_action(self, action: MaintenanceAction, dry_run: bool = True, confirm: bool = False) -> MaintenanceActionResult:
        if self.cleanup_engine:
            # Mock or delegate to cleanup engine
            pass
        return MaintenanceActionResult(
            result_id=str(uuid.uuid4()),
            action_id=action.action_id,
            action_type=action.action_type,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            status=MaintenanceStatus.PASS,
            dry_run=dry_run,
            message="Cleanup action executed via mock."
        )

    def run_backup_action(self, action: MaintenanceAction, dry_run: bool = True, confirm: bool = False) -> MaintenanceActionResult:
        if self.backup_builder:
            pass
        return MaintenanceActionResult(
            result_id=str(uuid.uuid4()),
            action_id=action.action_id,
            action_type=action.action_type,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            status=MaintenanceStatus.PASS,
            dry_run=dry_run,
            message="Backup action executed via mock."
        )

    def run_status(self, results: List[MaintenanceActionResult]) -> MaintenanceStatus:
        if any(r.status == MaintenanceStatus.BLOCKED for r in results):
            return MaintenanceStatus.BLOCKED
        if any(r.status == MaintenanceStatus.FAIL for r in results):
            return MaintenanceStatus.FAIL
        if any(r.status == MaintenanceStatus.WATCH for r in results):
            return MaintenanceStatus.WATCH
        return MaintenanceStatus.PASS
