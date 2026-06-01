import uuid
from typing import List, Optional
from bist_signal_bot.final_handoff.models import MaintenanceTask, MaintenanceCadence
from bist_signal_bot.config.settings import Settings

class MaintenanceCadenceBuilder:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def build_tasks(self) -> List[MaintenanceTask]:
        tasks = []
        if self.settings.FINAL_HANDOFF_DAILY_ROUTINE_ENABLED:
            tasks.extend(self.daily_tasks())
        if self.settings.FINAL_HANDOFF_WEEKLY_ROUTINE_ENABLED:
            tasks.extend(self.weekly_tasks())
        if self.settings.FINAL_HANDOFF_MONTHLY_ROUTINE_ENABLED:
            tasks.extend(self.monthly_tasks())
        tasks.extend(self.on_demand_tasks())
        return tasks

    def daily_tasks(self) -> List[MaintenanceTask]:
        return [
            MaintenanceTask(
                task_id=str(uuid.uuid4()),
                title="System Healthcheck",
                cadence=MaintenanceCadence.DAILY,
                command_hint="python -m bist_signal_bot healthcheck --ops --bootstrap --data-catalog",
                owner_area="ops",
                expected_output="All critical modules return PASS status."
            ),
             MaintenanceTask(
                task_id=str(uuid.uuid4()),
                title="Daily Reports",
                cadence=MaintenanceCadence.DAILY,
                command_hint="python -m bist_signal_bot reports daily --dry-run --include-ops --include-data-catalog",
                owner_area="reporting",
                expected_output="JSON/Markdown reports generated in daily folder."
            )
        ]

    def weekly_tasks(self) -> List[MaintenanceTask]:
         return [
            MaintenanceTask(
                task_id=str(uuid.uuid4()),
                title="Release Gate Validation",
                cadence=MaintenanceCadence.WEEKLY,
                command_hint="python -m bist_signal_bot qa release-gate --include-final-audit",
                owner_area="qa",
                expected_output="Release gate passes with no blockers."
            ),
             MaintenanceTask(
                task_id=str(uuid.uuid4()),
                title="Quick Research Scan",
                cadence=MaintenanceCadence.WEEKLY,
                command_hint="python -m bist_signal_bot orchestrator run --campaign QUICK_RESEARCH_SCAN --dry-run",
                owner_area="research",
                expected_output="Batch scanner completes without fatal errors."
            )
        ]

    def monthly_tasks(self) -> List[MaintenanceTask]:
         return [
            MaintenanceTask(
                task_id=str(uuid.uuid4()),
                title="Final Pre-Release Audit",
                cadence=MaintenanceCadence.MONTHLY,
                command_hint="python -m bist_signal_bot final-audit run",
                owner_area="governance",
                expected_output="Audit status is PASS, ready for release candidate."
            ),
             MaintenanceTask(
                task_id=str(uuid.uuid4()),
                title="Feature Store Drift Check",
                cadence=MaintenanceCadence.MONTHLY,
                command_hint="python -m bist_signal_bot feature-store drift --set scanner_core_v1 --json",
                owner_area="ml",
                expected_output="No significant drift detected in core features."
            )
        ]

    def on_demand_tasks(self) -> List[MaintenanceTask]:
         return [
            MaintenanceTask(
                task_id=str(uuid.uuid4()),
                title="Manual Backup Create",
                cadence=MaintenanceCadence.ON_DEMAND,
                command_hint="python -m bist_signal_bot maintenance backup-create",
                owner_area="maintenance",
                expected_output="Local backup tarball generated.",
                requires_confirm=True
            )
        ]

    def render_markdown(self, tasks: List[MaintenanceTask]) -> str:
        lines = ["# Maintenance Cadence\n"]
        for task in tasks:
            lines.append(f"## {task.title}")
            lines.append(f"- **Cadence**: {task.cadence.value}")
            lines.append(f"- **Owner**: {task.owner_area}")
            lines.append(f"- **Command**: `{task.command_hint}`")
            lines.append(f"- **Expected Output**: {task.expected_output}")
            lines.append(f"- **Requires Confirm**: {task.requires_confirm}")
            lines.append(f"\n> *Disclaimer*: {task.disclaimer}\n")
        return "\n".join(lines)
