import uuid
from datetime import datetime, timezone
from bist_signal_bot.maintenance_automation.models import MaintenancePlan, MaintenanceRun, MaintenanceActionResult, MaintenanceStatus, MaintenanceAction

class MaintenanceRunner:
    def run_plan(self, plan: MaintenancePlan, save: bool = False) -> MaintenanceRun:
        run_id = str(uuid.uuid4())
        results = []
        for action in plan.actions:
            results.append(self.run_action(action, plan.dry_run, plan.confirm))

        overall_status = self.run_status(results)
        return MaintenanceRun(
            run_id=run_id,
            plan=plan,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            status=overall_status,
            results=results
        )

    def run_action(self, action: MaintenanceAction, dry_run: bool = True, confirm: bool = False) -> MaintenanceActionResult:
        status = MaintenanceStatus.PASS
        skipped = False
        msg = f"Executed {action.name}"

        if action.destructive and not confirm:
            status = MaintenanceStatus.SKIPPED
            skipped = True
            msg = "Skipped destructive action (no confirm)"
        elif any("BLOCKED" in w for w in action.warnings):
            status = MaintenanceStatus.BLOCKED
            skipped = True
            msg = "Blocked unsafe command"

        return MaintenanceActionResult(
            result_id=str(uuid.uuid4()),
            action_id=action.action_id,
            action_type=action.action_type,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            status=status,
            skipped=skipped,
            dry_run=dry_run,
            message=msg
        )

    def run_status(self, results: list[MaintenanceActionResult]) -> MaintenanceStatus:
        if not results:
            return MaintenanceStatus.PASS
        if any(r.status == MaintenanceStatus.FAIL for r in results):
            return MaintenanceStatus.FAIL
        if any(r.status == MaintenanceStatus.BLOCKED for r in results):
            return MaintenanceStatus.BLOCKED
        if any(r.status == MaintenanceStatus.WATCH for r in results):
            return MaintenanceStatus.WATCH
        return MaintenanceStatus.PASS
