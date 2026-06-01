import uuid
from datetime import datetime
from bist_signal_bot.final_handoff.models import OperatorPlaybook
from bist_signal_bot.final_handoff.reporting import format_operator_playbook_markdown

class OperatorPlaybookBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def build_playbook(self) -> OperatorPlaybook:
        return OperatorPlaybook(
            playbook_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            title="Final MVP Operator Playbook",
            daily_routine=self.daily_routine(),
            weekly_routine=self.weekly_routine(),
            monthly_routine=self.monthly_routine(),
            emergency_checks=self.emergency_checks(),
            sections=self.troubleshooting_sections()
        )

    def daily_routine(self) -> list[str]:
        return [
            "python -m bist_signal_bot healthcheck --ops --bootstrap --data-catalog",
            "python -m bist_signal_bot ops status",
            "python -m bist_signal_bot reports daily --dry-run --include-ops --include-data-catalog"
        ]

    def weekly_routine(self) -> list[str]:
        return [
            "python -m bist_signal_bot qa release-gate --include-final-audit",
            "python -m bist_signal_bot orchestrator run --campaign QUICK_RESEARCH_SCAN --dry-run",
            "python -m bist_signal_bot monitoring status",
            "python -m bist_signal_bot leaderboard report"
        ]

    def monthly_routine(self) -> list[str]:
        return [
            "python -m bist_signal_bot final-audit run",
            "python -m bist_signal_bot docs-hub coverage",
            "python -m bist_signal_bot feature-store drift --set scanner_core_v1 --json",
            "python -m bist_signal_bot model-registry report"
        ]

    def emergency_checks(self) -> list[str]:
        return [
            "python -m bist_signal_bot ops incident list",
            "python -m bist_signal_bot doctor --all"
        ]

    def troubleshooting_sections(self) -> list[dict]:
        return [
            {"title": "Stale Data", "hint": "Check data-catalog and yfinance adapter logs."}
        ]

    def render_markdown(self, playbook: OperatorPlaybook) -> str:
        return format_operator_playbook_markdown(playbook)
