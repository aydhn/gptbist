import uuid
from typing import List, Optional
from bist_signal_bot.final_handoff.models import FinalCommandMapEntry, HandoffAudience
from bist_signal_bot.config.settings import Settings

class FinalCommandMapBuilder:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def build_command_map(self) -> List[FinalCommandMapEntry]:
        entries = self.core_command_entries()
        entries.extend(self.entries_from_cli_registry())
        return entries

    def entries_from_cli_registry(self) -> List[FinalCommandMapEntry]:
        # In a real implementation, this would dynamically fetch commands from cli_ux/command_registry.py
        # For now, return an empty list as we define the core groups manually
        return []

    def core_command_entries(self) -> List[FinalCommandMapEntry]:
        return [
            FinalCommandMapEntry(
                entry_id=str(uuid.uuid4()),
                command="bootstrap",
                category="setup",
                audience=HandoffAudience.USER,
                purpose="Initializes local MVP packaging and demo profiles.",
                safe_mode=True,
                dry_run_supported=True,
                json_supported=True
            ),
            FinalCommandMapEntry(
                entry_id=str(uuid.uuid4()),
                command="healthcheck",
                category="ops",
                audience=HandoffAudience.OPERATOR,
                purpose="Checks system health across multiple modules.",
                safe_mode=True,
                json_supported=True
            ),
            FinalCommandMapEntry(
                entry_id=str(uuid.uuid4()),
                command="doctor",
                category="ops",
                audience=HandoffAudience.OPERATOR,
                purpose="Diagnoses offline configuration and data issues.",
                safe_mode=True,
                json_supported=True
            ),
            FinalCommandMapEntry(
                entry_id=str(uuid.uuid4()),
                command="qa",
                category="governance",
                audience=HandoffAudience.QA,
                purpose="Runs release gates and test suites.",
                safe_mode=True,
                json_supported=True
            ),
            FinalCommandMapEntry(
                entry_id=str(uuid.uuid4()),
                command="ops",
                category="ops",
                audience=HandoffAudience.OPERATOR,
                purpose="Manages reliability, backups, and readiness.",
                safe_mode=False,
                dry_run_supported=True,
                json_supported=True
            ),
             FinalCommandMapEntry(
                entry_id=str(uuid.uuid4()),
                command="final-handoff",
                category="governance",
                audience=HandoffAudience.ALL,
                purpose="Builds, shows, and exports final MVP handoff artifacts.",
                safe_mode=True,
                dry_run_supported=False,
                json_supported=True
            )
        ]

    def filter_by_audience(self, entries: List[FinalCommandMapEntry], audience: HandoffAudience) -> List[FinalCommandMapEntry]:
        if audience == HandoffAudience.ALL:
            return entries
        return [e for e in entries if e.audience in (audience, HandoffAudience.ALL)]

    def render_markdown(self, entries: List[FinalCommandMapEntry]) -> str:
        lines = ["# Final Command Map\n"]
        for entry in entries:
            lines.append(f"## {entry.command}")
            lines.append(f"- **Category**: {entry.category}")
            lines.append(f"- **Audience**: {entry.audience.value}")
            lines.append(f"- **Purpose**: {entry.purpose}")
            lines.append(f"- **Safe Mode**: {entry.safe_mode}")
            lines.append(f"- **Dry-Run Supported**: {entry.dry_run_supported}")
            lines.append(f"- **JSON Supported**: {entry.json_supported}")
            lines.append(f"\n> *Disclaimer*: {entry.disclaimer}\n")
        return "\n".join(lines)
