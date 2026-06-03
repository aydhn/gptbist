import os

def create_change_control():
    content = """import uuid
from typing import Any, Dict, List
from bist_signal_bot.release_policy.models import (
    ChangeRequest, ChangeType, ChangeRiskLevel, VersionBumpType, ReleasePolicyStatus
)

class ChangeControlManager:
    def __init__(self) -> None:
        pass

    def create_change_request(self, title: str, description: str, change_type: ChangeType, affected_modules: List[str], risk_level: ChangeRiskLevel = ChangeRiskLevel.MEDIUM) -> ChangeRequest:
        req_migration = change_type in [ChangeType.BREAKING, ChangeType.SCHEMA, ChangeType.CLI_CONTRACT, ChangeType.DATA_CONTRACT]
        req_deprecation = change_type == ChangeType.DEPRECATION
        req_docs = change_type in [ChangeType.FEATURE, ChangeType.BREAKING, ChangeType.DOCS]
        req_tests = change_type not in [ChangeType.DOCS]

        bump = VersionBumpType.NONE
        if change_type == ChangeType.BREAKING:
            bump = VersionBumpType.MAJOR
        elif change_type in [ChangeType.FEATURE, ChangeType.DEPRECATION]:
            bump = VersionBumpType.MINOR
        elif change_type in [ChangeType.BUGFIX, ChangeType.SECURITY, ChangeType.PERFORMANCE]:
            bump = VersionBumpType.PATCH

        return ChangeRequest(
            change_id=str(uuid.uuid4()),
            title=title,
            description=description,
            change_type=change_type,
            risk_level=risk_level,
            affected_modules=affected_modules,
            proposed_version_bump=bump,
            requires_migration=req_migration,
            requires_deprecation_notice=req_deprecation,
            requires_docs_update=req_docs,
            requires_tests_update=req_tests,
            status=ReleasePolicyStatus.DRAFT
        )

    def classify_change(self, description: str, affected_modules: List[str]) -> ChangeType:
        d = description.lower()
        if "break" in d: return ChangeType.BREAKING
        if "fix" in d: return ChangeType.BUGFIX
        if "sec" in d or "vuln" in d: return ChangeType.SECURITY
        if "feat" in d or "add" in d: return ChangeType.FEATURE
        if "schema" in d: return ChangeType.SCHEMA
        return ChangeType.CUSTOM

    def estimate_risk(self, change_type: ChangeType, affected_modules: List[str]) -> ChangeRiskLevel:
        if change_type in [ChangeType.SECURITY, ChangeType.BREAKING]:
            return ChangeRiskLevel.CRITICAL
        if change_type in [ChangeType.SCHEMA, ChangeType.DATA_CONTRACT]:
            return ChangeRiskLevel.HIGH
        if change_type in [ChangeType.DOCS, ChangeType.TEST]:
            return ChangeRiskLevel.LOW
        return ChangeRiskLevel.MEDIUM

    def required_artifacts(self, change: ChangeRequest) -> Dict[str, bool]:
        return {
            "migration_notes": change.requires_migration,
            "deprecation_notice": change.requires_deprecation_notice,
            "changelog": True,
            "docs": change.requires_docs_update,
            "tests": change.requires_tests_update
        }

    def validate_change_request(self, change: ChangeRequest) -> List[str]:
        errors = []
        if change.change_type == ChangeType.BREAKING and not change.requires_migration:
            errors.append("Breaking change must require migration notes.")
        if change.risk_level == ChangeRiskLevel.CRITICAL and change.change_type not in [ChangeType.SECURITY, ChangeType.BREAKING]:
             pass
        return errors

    def change_summary(self, change: ChangeRequest) -> Dict[str, Any]:
        return {
            "id": change.change_id,
            "title": change.title,
            "type": change.change_type.value,
            "risk": change.risk_level.value,
            "status": change.status.value
        }
"""
    with open("bist_signal_bot/release_policy/change_control.py", "w") as f:
        f.write(content)


def create_changelog():
    content = """import uuid
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
        return "\\n".join(lines)

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
"""
    with open("bist_signal_bot/release_policy/changelog.py", "w") as f:
        f.write(content)


def create_migrations():
    content = """import uuid
from typing import Any, Dict, List, Optional
from bist_signal_bot.release_policy.models import ChangeRequest, MigrationNote, ReleasePolicyStatus, ChangeType

class MigrationNoteBuilder:
    def __init__(self) -> None:
        pass

    def build_migration_notes(self, changes: List[ChangeRequest], from_version: str, to_version: str) -> List[MigrationNote]:
        notes = []
        for c in changes:
            if c.requires_migration:
                note = self.note_from_change(c, from_version, to_version)
                if note:
                    notes.append(note)
        return notes

    def note_from_change(self, change: ChangeRequest, from_version: str, to_version: str) -> Optional[MigrationNote]:
        if not change.requires_migration:
            return None
        return MigrationNote(
            migration_id=str(uuid.uuid4()),
            from_version=from_version,
            to_version=to_version,
            title=f"Migration for {change.title}",
            steps=self.default_migration_steps(change),
            affected_files=[],
            required=True,
            status=ReleasePolicyStatus.DRAFT
        )

    def default_migration_steps(self, change: ChangeRequest) -> List[str]:
        if change.change_type == ChangeType.SCHEMA:
            return ["Run schema migration scripts.", "Verify table integrity."]
        elif change.change_type == ChangeType.CONFIG:
            return ["Update .env variables.", "Review default configurations."]
        return ["Review change details.", "Apply required updates manually."]

    def validate_migration_note(self, note: MigrationNote) -> List[str]:
        errors = []
        if note.required and not note.steps:
            errors.append(f"Migration {note.migration_id} is required but has empty steps.")
        if any("broker" in s.lower() or "deployment approval" in s.lower() for s in note.steps):
             errors.append("Migration note cannot contain broker or deployment approval claims.")
        return errors

    def format_migration_markdown(self, notes: List[MigrationNote]) -> str:
        lines = ["# Migration Notes\n"]
        for note in notes:
            lines.append(f"## {note.from_version} -> {note.to_version}: {note.title}")
            for step in note.steps:
                lines.append(f"- {step}")
            lines.append(f"\\n> *{note.disclaimer}*\\n")
        return "\\n".join(lines)
"""
    with open("bist_signal_bot/release_policy/migrations.py", "w") as f:
        f.write(content)


def create_deprecations():
    content = """import uuid
from typing import Any, Dict, List, Optional
from bist_signal_bot.release_policy.models import DeprecationNotice, ReleasePolicyStatus

class DeprecationPolicyManager:
    def __init__(self) -> None:
        self._active: List[DeprecationNotice] = []

    def default_deprecations(self) -> List[DeprecationNotice]:
        return self._active

    def create_deprecation(self, feature_name: str, deprecated_since: str, reason: str, replacement: Optional[str] = None, removal_target_version: Optional[str] = None) -> DeprecationNotice:
        notice = DeprecationNotice(
            deprecation_id=str(uuid.uuid4()),
            feature_name=feature_name,
            deprecated_since=deprecated_since,
            removal_target_version=removal_target_version,
            replacement=replacement,
            reason=reason,
            status=ReleasePolicyStatus.DRAFT
        )
        self._active.append(notice)
        return notice

    def validate_deprecation_notice(self, notice: DeprecationNotice) -> List[str]:
        errors = []
        if notice.removal_target_version and not self._is_valid_semver_target(notice.removal_target_version):
            errors.append(f"Invalid removal target version: {notice.removal_target_version}")
        if "live" in notice.feature_name.lower() or "broker" in notice.feature_name.lower():
            errors.append("Deprecated feature names cannot imply live/broker capabilities.")
        return errors

    def _is_valid_semver_target(self, target: str) -> bool:
        # Simple check for X.Y format
        import re
        return bool(re.match(r"^([0-9]+)\.([0-9]+)(?:\.[0-9]+)?$", target))

    def active_deprecations(self) -> List[DeprecationNotice]:
        return self._active

    def format_deprecations_markdown(self, notices: List[DeprecationNotice]) -> str:
        lines = ["# Deprecation Notices\n"]
        for notice in notices:
            lines.append(f"## {notice.feature_name} (since {notice.deprecated_since})")
            lines.append(f"Reason: {notice.reason}")
            if notice.replacement:
                lines.append(f"Replacement: {notice.replacement}")
            if notice.removal_target_version:
                lines.append(f"Target removal: {notice.removal_target_version}")
            lines.append(f"\\n> *{notice.disclaimer}*\\n")
        return "\\n".join(lines)
"""
    with open("bist_signal_bot/release_policy/deprecations.py", "w") as f:
        f.write(content)

if __name__ == "__main__":
    create_change_control()
    create_changelog()
    create_migrations()
    create_deprecations()
    print("Part 3 complete.")
