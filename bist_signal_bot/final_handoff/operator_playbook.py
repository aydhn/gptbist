import uuid
from typing import List, Optional, Dict, Any
from bist_signal_bot.final_handoff.models import OperatorPlaybook
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.final_handoff.maintenance import MaintenanceCadenceBuilder
from bist_signal_bot.final_handoff.models import MaintenanceCadence

class OperatorPlaybookBuilder:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.maintenance_builder = MaintenanceCadenceBuilder(self.settings)

    def build_playbook(self) -> OperatorPlaybook:
        tasks = self.maintenance_builder.build_tasks()
        return OperatorPlaybook(
            playbook_id=str(uuid.uuid4()),
            title="Local Operator Playbook",
            daily_routine=[t.command_hint for t in tasks if t.cadence == MaintenanceCadence.DAILY],
            weekly_routine=[t.command_hint for t in tasks if t.cadence == MaintenanceCadence.WEEKLY],
            monthly_routine=[t.command_hint for t in tasks if t.cadence == MaintenanceCadence.MONTHLY],
            emergency_checks=self.emergency_checks(),
            sections=self.troubleshooting_sections()
        )

    def daily_routine(self) -> List[str]:
        tasks = self.maintenance_builder.daily_tasks()
        return [t.command_hint for t in tasks]

    def weekly_routine(self) -> List[str]:
        tasks = self.maintenance_builder.weekly_tasks()
        return [t.command_hint for t in tasks]

    def monthly_routine(self) -> List[str]:
        tasks = self.maintenance_builder.monthly_tasks()
        return [t.command_hint for t in tasks]

    def emergency_checks(self) -> List[str]:
        return [
            "python -m bist_signal_bot doctor --full",
            "python -m bist_signal_bot ops status",
            "python -m bist_signal_bot maintenance backup-verify"
        ]

    def troubleshooting_sections(self) -> List[Dict[str, Any]]:
        return [
            {
                "topic": "Data Staleness",
                "check": "python -m bist_signal_bot ops staleness",
                "resolution": "Check network connectivity and rerun fundamentals import."
            },
             {
                "topic": "Model Drift",
                "check": "python -m bist_signal_bot feature-store drift",
                "resolution": "If drift > threshold, rebuild ML dataset and retrain model offline."
            }
        ]

    def render_markdown(self, playbook: OperatorPlaybook) -> str:
        lines = [f"# {playbook.title}\n"]

        lines.append("## Daily Routine")
        for cmd in playbook.daily_routine:
            lines.append(f"- `{cmd}`")
        lines.append("")

        lines.append("## Weekly Routine")
        for cmd in playbook.weekly_routine:
            lines.append(f"- `{cmd}`")
        lines.append("")

        lines.append("## Monthly Routine")
        for cmd in playbook.monthly_routine:
            lines.append(f"- `{cmd}`")
        lines.append("")

        lines.append("## Emergency Checks")
        for cmd in playbook.emergency_checks:
            lines.append(f"- `{cmd}`")
        lines.append("")

        lines.append("## Troubleshooting")
        for section in playbook.sections:
            lines.append(f"### {section.get('topic')}")
            lines.append(f"**Check**: `{section.get('check')}`")
            lines.append(f"**Resolution**: {section.get('resolution')}")
            lines.append("")

        lines.append(f"\n> *Disclaimer*: {playbook.disclaimer}\n")
        return "\n".join(lines)
