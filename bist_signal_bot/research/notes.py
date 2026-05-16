import logging
import uuid
from datetime import datetime

from ..config.settings import Settings, get_settings
from .models import ResearchNote, ResearchTag
from .storage import ResearchStore
from ..core.exceptions import ResearchNoteError

class ResearchNoteManager:
    def __init__(self, storage: ResearchStore, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.storage = storage
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)

    def add_note(self, title: str, body: str, related_run_ids: list[str] | None = None,
                 related_symbols: list[str] | None = None, related_strategies: list[str] | None = None,
                 tags: list[str] | None = None) -> ResearchNote:

        parsed_tags = [ResearchTag(tag=t) for t in (tags or [])]

        note = ResearchNote(
            note_id=f"not_{uuid.uuid4().hex[:8]}",
            title=title,
            body=body,
            related_run_ids=related_run_ids or [],
            related_symbols=related_symbols or [],
            related_strategies=related_strategies or [],
            tags=parsed_tags
        )

        self.storage.append_note(note)
        self.logger.info(f"Added research note: {note.note_id}")
        return note

    def list_notes(self, limit: int = 50, tag: str | None = None) -> list[ResearchNote]:
        notes = self.storage.load_notes(limit=1000)
        if not tag:
            return notes[:limit]

        filtered = []
        for n in notes:
            if any(t.tag == tag for t in n.tags):
                filtered.append(n)
                if len(filtered) >= limit:
                    break
        return filtered

    def show_note(self, note_id: str) -> ResearchNote | None:
        notes = self.storage.load_notes(limit=1000)
        for n in notes:
            if n.note_id == note_id:
                return n
        return None

    def delete_note(self, note_id: str, confirm: bool = False) -> bool:
        if not confirm:
            raise ResearchNoteError("Confirm is required to delete a note.")

        notes = self.storage.load_notes(limit=5000)
        new_notes = [n for n in notes if n.note_id != note_id]

        if len(new_notes) == len(notes):
             raise ResearchNoteError(f"Note {note_id} not found.")

        # Rewrite the notes file (a deletion violates pure append-only, but allowed for notes with confirmation)
        try:
             # Just clear the file and write new
             open(self.storage.notes_file, "w").close()
             for n in new_notes:
                 self.storage.append_note(n)
             return True
        except Exception as e:
             raise ResearchNoteError(f"Failed to delete note: {e}")
