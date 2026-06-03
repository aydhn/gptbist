import uuid
from typing import Any, Dict, List
from bist_signal_bot.release_policy.models import ChangeRequest, ChangelogEntry, ChangeType
from datetime import datetime

class ChangelogBuilder:
    def __init__(self) -> None:
        pass

    def build_changelog_entries(self, changes: List[ChangeRequest], version: str) -> List[ChangelogEntry]:
        return [self.entry_from_change(c, version) for c in changes]

    def entry_from_change(self, change: ChangeRequest, version: str) -> ChangelogEntry:
        return ChangelogEntry(
            entry_id=str(uuid.uuid4()),
            version=version,
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            change_type=change.change_type,
            title=change.title,
            description=change.description,
            affected_modules=change.affected_modules,
            migration_required=change.requires_migration,
            deprecation_related=change.requires_deprecation_notice
        )

    def format_changelog_markdown(self, entries: List[ChangelogEntry]) -> str:
        lines = ["# Changelog\n"]
        for e in entries:
            mark = " (BREAKING)" if e.change_type == ChangeType.BREAKING else ""
            lines.append(f"## [{e.version}] - {e.date}")
            lines.append(f"### {e.change_type.value}{mark}: {e.title}")
            lines.append(f"{e.description}\n")
            if e.migration_required:
                lines.append("**Migration Required**\n")
        return "\n".join(lines)

    def validate_changelog(self, entries: List[ChangelogEntry]) -> List[str]:
        errors = []
        for e in entries:
            if not e.title:
                errors.append(f"Entry {e.entry_id} missing title")
            if "investment advice" in e.description.lower():
                errors.append(f"Entry {e.entry_id} contains unsafe claims")
        return errors

    def changelog_summary(self, entries: List[ChangelogEntry]) -> Dict[str, Any]:
        return {
            "total_entries": len(entries),
            "breaking_changes": len([e for e in entries if e.change_type == ChangeType.BREAKING])
        }
