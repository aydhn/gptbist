import uuid
from bist_signal_bot.final_handoff.models import MaintenanceTask, MaintenanceCadence
from bist_signal_bot.final_handoff.reporting import format_maintenance_markdown

class MaintenanceCadenceBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def build_tasks(self) -> list[MaintenanceTask]:
        tasks = []
        if getattr(self.settings, "FINAL_HANDOFF_DAILY_ROUTINE_ENABLED", True):
            tasks.extend(self.daily_tasks())
        if getattr(self.settings, "FINAL_HANDOFF_WEEKLY_ROUTINE_ENABLED", True):
            tasks.extend(self.weekly_tasks())
        if getattr(self.settings, "FINAL_HANDOFF_MONTHLY_ROUTINE_ENABLED", True):
            tasks.extend(self.monthly_tasks())
        tasks.extend(self.on_demand_tasks())
        return tasks

    def daily_tasks(self) -> list[MaintenanceTask]:
        return [
            MaintenanceTask(
                task_id=str(uuid.uuid4()),
                title="Daily Healthcheck",
                cadence=MaintenanceCadence.DAILY,
                command_hint="python -m bist_signal_bot healthcheck --ops --bootstrap --data-catalog",
                owner_area="ops",
                expected_output="Healthcheck PASS",
                requires_confirm=False
            )
        ]

    def weekly_tasks(self) -> list[MaintenanceTask]:
        return [
            MaintenanceTask(
                task_id=str(uuid.uuid4()),
                title="Weekly QA Gate",
                cadence=MaintenanceCadence.WEEKLY,
                command_hint="python -m bist_signal_bot qa release-gate --include-final-audit",
                owner_area="qa",
                expected_output="Release Gate PASS",
                requires_confirm=False
            )
        ]

    def monthly_tasks(self) -> list[MaintenanceTask]:
        return [
            MaintenanceTask(
                task_id=str(uuid.uuid4()),
                title="Monthly Final Audit",
                cadence=MaintenanceCadence.MONTHLY,
                command_hint="python -m bist_signal_bot final-audit run",
                owner_area="final_audit",
                expected_output="Final Audit PASS",
                requires_confirm=False
            )
        ]

    def on_demand_tasks(self) -> list[MaintenanceTask]:
        return [
            MaintenanceTask(
                task_id=str(uuid.uuid4()),
                title="Backup Restore Dry-Run",
                cadence=MaintenanceCadence.ON_DEMAND,
                command_hint="python -m bist_signal_bot maintenance restore --dry-run",
                owner_area="maintenance",
                expected_output="Restore Dry-Run SUCCESS",
                requires_confirm=True
            )
        ]

    def render_markdown(self, tasks: list[MaintenanceTask]) -> str:
        return format_maintenance_markdown(tasks)
