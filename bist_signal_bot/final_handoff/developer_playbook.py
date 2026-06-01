import uuid
from datetime import datetime
from bist_signal_bot.final_handoff.models import DeveloperPlaybook
from bist_signal_bot.final_handoff.reporting import format_developer_playbook_markdown

class DeveloperPlaybookBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def build_playbook(self) -> DeveloperPlaybook:
        return DeveloperPlaybook(
            playbook_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            title="Final MVP Developer Playbook",
            extension_points=self.extension_points(),
            coding_standards=self.coding_standards(),
            test_standards=self.test_standards(),
            release_standards=self.release_standards(),
            sections=[{"title": "New Module Flow", "steps": self.new_module_flow()}]
        )

    def extension_points(self) -> list[str]:
        return [
            "Data Adapters",
            "Scanner Strategies",
            "CLI Commands",
            "Report Sections"
        ]

    def coding_standards(self) -> list[str]:
        return [
            "Use Type hints.",
            "JSON serialization required for all payloads.",
            "Use PathGuard for file operations.",
            "Secret redaction required in logs."
        ]

    def test_standards(self) -> list[str]:
        return [
            "Tests must be deterministic.",
            "No external network calls (yfinance, Telegram) in tests.",
            "No broker/order/live commands.",
            "Existing tests must not break."
        ]

    def release_standards(self) -> list[str]:
        return [
            "Must pass QA Release Gate.",
            "Must pass Final Audit.",
            "Output safe-language disclaimer required."
        ]

    def new_module_flow(self) -> list[str]:
        return [
            "Define Pydantic models.",
            "Add storage adapter.",
            "Create CLI parser.",
            "Write deterministic tests.",
            "Add to FinalModuleMap."
        ]

    def render_markdown(self, playbook: DeveloperPlaybook) -> str:
        return format_developer_playbook_markdown(playbook)
