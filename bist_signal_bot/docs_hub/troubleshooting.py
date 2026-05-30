import uuid
from datetime import datetime
from typing import Optional

from bist_signal_bot.docs_hub.models import (
    TroubleshootingKnowledgeBase, TroubleshootingEntry, TroubleshootingSeverity
)

class TroubleshootingKBBuilder:
    def __init__(self, settings=None):
        pass

    def build_kb(self) -> TroubleshootingKnowledgeBase:
        return TroubleshootingKnowledgeBase(
            kb_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            entries=self.default_entries()
        )

    def default_entries(self) -> list[TroubleshootingEntry]:
        return [
            TroubleshootingEntry(
                entry_id=str(uuid.uuid4()),
                title="QA Blocked",
                symptom="Release gate failed due to coverage",
                likely_causes=["Missing documentation", "Failing tests"],
                checks=["Check docs-hub coverage"],
                suggested_commands=["python -m bist_signal_bot docs-hub coverage"],
                safe_resolution_steps=["Add missing docs"],
                severity=TroubleshootingSeverity.HIGH,
                related_modules=["qa", "docs_hub"]
            ),
            TroubleshootingEntry(
                entry_id=str(uuid.uuid4()),
                title="Store JSONL invalid",
                symptom="Error reading local JSONL store",
                likely_causes=["File corrupted", "Interrupted write"],
                checks=["Check file integrity"],
                suggested_commands=["python -m bist_signal_bot ops doctor"],
                safe_resolution_steps=["Restore from backup or clear file"],
                severity=TroubleshootingSeverity.CRITICAL,
                related_modules=["ops", "store"]
            )
        ]

    def entry_for_error(self, error_type: str) -> Optional[TroubleshootingEntry]:
        for entry in self.default_entries():
            if error_type.lower() in entry.title.lower():
                return entry
        return None

    def search_entries(self, query: str, kb: Optional[TroubleshootingKnowledgeBase] = None) -> list[TroubleshootingEntry]:
        if not kb:
            kb = self.build_kb()
        query = query.lower()
        return [e for e in kb.entries if query in e.title.lower() or query in e.symptom.lower()]

    def render_entry_markdown(self, entry: TroubleshootingEntry) -> str:
        return f"## {entry.title}\n**Symptom:** {entry.symptom}\n**Suggested Fix:** {', '.join(entry.safe_resolution_steps)}"

    def render_kb_markdown(self, kb: TroubleshootingKnowledgeBase) -> str:
        lines = [f"# Troubleshooting KB ({kb.created_at})", ""]
        for entry in kb.entries:
            lines.append(self.render_entry_markdown(entry))
            lines.append("")
        return "\n".join(lines)
