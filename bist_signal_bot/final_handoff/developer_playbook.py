import uuid
from typing import List, Optional
from bist_signal_bot.final_handoff.models import DeveloperPlaybook
from bist_signal_bot.config.settings import Settings

class DeveloperPlaybookBuilder:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def build_playbook(self) -> DeveloperPlaybook:
        return DeveloperPlaybook(
            playbook_id=str(uuid.uuid4()),
            title="Local Developer Playbook",
            extension_points=self.extension_points(),
            coding_standards=self.coding_standards(),
            test_standards=self.test_standards(),
            release_standards=self.release_standards(),
            sections=[{"topic": "New Module Flow", "steps": self.new_module_flow()}]
        )

    def extension_points(self) -> List[str]:
        return [
            "Data Adapters: Implement `DataImportStrategy` in `bist_signal_bot.data`",
            "Trading Signals: Subclass `BaseSignalGenerator` in `bist_signal_bot.signals`",
            "ML Features: Add builders to `bist_signal_bot.feature_store`",
            "Reports: Add sections to `bist_signal_bot.reports.sections`"
        ]

    def coding_standards(self) -> List[str]:
        return [
            "Type hints everywhere.",
            "Pydantic or Dataclasses for domain models.",
            "PathGuard usage for all file operations.",
            "Secret redaction via Governance gates.",
            "JSON serialization compatibility."
        ]

    def test_standards(self) -> List[str]:
        return [
            "Deterministic tests only.",
            "No external calls in tests (use tmp_path, mocks).",
            "Existing tests must not break.",
            "Test offline without broker/internet."
        ]

    def release_standards(self) -> List[str]:
        return [
            "No broker/order/live command in codebase.",
            "Safe-language disclaimers required on all outputs.",
            "Pass Final Audit before release."
        ]

    def new_module_flow(self) -> List[str]:
         return [
            "Create module directory and `__init__.py`.",
            "Define domain models (`models.py`).",
            "Implement core logic with deterministic behavior.",
            "Write offline tests in `tests/`.",
            "Add CLI integration in `cli/`.",
            "Update Module Map and Command Map in `final_handoff`."
         ]

    def render_markdown(self, playbook: DeveloperPlaybook) -> str:
        lines = [f"# {playbook.title}\n"]

        lines.append("## Coding Standards")
        for std in playbook.coding_standards:
            lines.append(f"- {std}")
        lines.append("")

        lines.append("## Test Standards")
        for std in playbook.test_standards:
            lines.append(f"- {std}")
        lines.append("")

        lines.append("## Release Standards")
        for std in playbook.release_standards:
            lines.append(f"- {std}")
        lines.append("")

        lines.append("## Extension Points")
        for ep in playbook.extension_points:
            lines.append(f"- {ep}")
        lines.append("")

        lines.append("## Developer Flows")
        for section in playbook.sections:
             lines.append(f"### {section.get('topic')}")
             for step in section.get('steps', []):
                 lines.append(f"1. {step}")
             lines.append("")

        lines.append(f"\n> *Disclaimer*: {playbook.disclaimer}\n")
        return "\n".join(lines)
