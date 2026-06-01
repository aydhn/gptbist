import uuid
from bist_signal_bot.final_handoff.models import FinalCommandMapEntry, HandoffAudience
from bist_signal_bot.final_handoff.reporting import format_command_map_text

class FinalCommandMapBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def build_command_map(self) -> list[FinalCommandMapEntry]:
        entries = self.core_command_entries()
        entries.extend(self.entries_from_cli_registry())
        return entries

    def entries_from_cli_registry(self) -> list[FinalCommandMapEntry]:
        # Mocking CLI registry extraction for final handoff scope
        return [
            FinalCommandMapEntry(
                entry_id=str(uuid.uuid4()),
                command="python -m bist_signal_bot final-handoff build",
                category="final-handoff",
                audience=HandoffAudience.DEVELOPER,
                purpose="Build the final handoff manifest.",
                safe_mode=True,
                dry_run_supported=False,
                json_supported=True
            ),
            FinalCommandMapEntry(
                entry_id=str(uuid.uuid4()),
                command="python -m bist_signal_bot healthcheck --final-handoff",
                category="healthcheck",
                audience=HandoffAudience.OPERATOR,
                purpose="Run healthcheck including final handoff status.",
                safe_mode=True,
                dry_run_supported=False,
                json_supported=True
            )
        ]

    def core_command_entries(self) -> list[FinalCommandMapEntry]:
        core_groups = ["bootstrap", "healthcheck", "doctor", "qa", "ops", "docs-hub",
                       "data-catalog", "feature-store", "model-registry", "monitoring",
                       "leaderboard", "orchestrator", "final-audit", "final-handoff", "reports"]

        entries = []
        for g in core_groups:
            entries.append(FinalCommandMapEntry(
                entry_id=str(uuid.uuid4()),
                command=f"python -m bist_signal_bot {g}",
                category=g,
                audience=HandoffAudience.ALL,
                purpose=f"Core command for {g}",
                safe_mode=True,
                dry_run_supported=True,
                json_supported=True
            ))
        return entries

    def filter_by_audience(self, entries: list[FinalCommandMapEntry], audience: HandoffAudience) -> list[FinalCommandMapEntry]:
        if audience == HandoffAudience.ALL:
            return entries
        return [e for e in entries if e.audience in (audience, HandoffAudience.ALL)]

    def render_markdown(self, entries: list[FinalCommandMapEntry]) -> str:
        return format_command_map_text(entries)
