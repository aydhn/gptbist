import uuid
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
            lines.append(f"\n> *{note.disclaimer}*\n")
        return "\n".join(lines)
