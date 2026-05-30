import uuid
from datetime import datetime
from typing import Optional

from bist_signal_bot.docs_hub.models import CommandCookbook, CommandCookbookEntry

class CommandCookbookBuilder:
    def __init__(self, settings=None, base_dir=None):
        pass

    def build_cookbook(self) -> CommandCookbook:
        entries = self.entries_from_cli_registry() + self.entries_from_bootstrap_recipes()
        return CommandCookbook(
            cookbook_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            entries=entries,
            profile_names=["STANDARD"],
            module_names=["docs_hub", "scanner", "qa"]
        )

    def entries_from_cli_registry(self) -> list[CommandCookbookEntry]:
        return [
            CommandCookbookEntry(
                entry_id=str(uuid.uuid4()),
                title="Index Local Docs",
                command="python -m bist_signal_bot docs-hub index",
                purpose="Build the documentation index",
                profile_names=["STANDARD"],
                module_names=["docs_hub"],
                expected_output="JSON representation of docs index",
                risk_level="LOW",
                requires_confirm=False,
                tags=["docs"]
            )
        ]

    def entries_from_bootstrap_recipes(self) -> list[CommandCookbookEntry]:
        return [
             CommandCookbookEntry(
                entry_id=str(uuid.uuid4()),
                title="Offline Demo",
                command="python -m bist_signal_bot bootstrap demo",
                purpose="Run the offline demo",
                profile_names=["STANDARD"],
                module_names=["bootstrap"],
                expected_output="Demo completed",
                risk_level="LOW",
                requires_confirm=False,
                tags=["demo"]
            )
        ]

    def filter_entries(self, cookbook: CommandCookbook, profile: Optional[str] = None,
                      module: Optional[str] = None, tag: Optional[str] = None) -> CommandCookbook:
        entries = cookbook.entries
        if profile:
            entries = [e for e in entries if profile in e.profile_names]
        if module:
            entries = [e for e in entries if module in e.module_names]
        if tag:
            entries = [e for e in entries if tag in e.tags]

        return CommandCookbook(
            cookbook_id=cookbook.cookbook_id,
            created_at=cookbook.created_at,
            entries=entries,
            profile_names=cookbook.profile_names,
            module_names=cookbook.module_names
        )

    def render_markdown(self, cookbook: CommandCookbook) -> str:
        lines = [f"# Command Cookbook ({cookbook.created_at})", ""]
        for entry in cookbook.entries:
            lines.append(f"## {entry.title}")
            lines.append(f"**Command:** `{entry.command}`")
            lines.append(f"**Purpose:** {entry.purpose}")
            lines.append("")
        return "\n".join(lines)
