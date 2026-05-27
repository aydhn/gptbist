import csv
import json
from pathlib import Path
from datetime import datetime
import uuid
from typing import Any

from bist_signal_bot.events.models import (
    MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity, EventImportResult
)

class EventImporter:
    def __init__(self, calendar=None):
        self.calendar = calendar

    def import_file(self, path: Path, confirm: bool = False) -> EventImportResult:
        if not path.exists():
            raise FileNotFoundError(f"Event file not found: {path}")

        events = []
        if path.suffix == ".csv":
            events = self.parse_csv(path)
        elif path.suffix == ".json":
            events = self.parse_json(path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        errors = self.validate_events(events)
        valid_events, duplicates = self.deduplicate_events(events)

        imported_count = 0
        if confirm and self.calendar:
            for ev in valid_events:
                self.calendar.add_event(ev, confirm=True)
                imported_count += 1

        return EventImportResult(
            import_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            source_path=str(path),
            rows_seen=len(events),
            events_imported=imported_count if confirm else 0,
            events_skipped=len(events) - len(valid_events),
            duplicate_count=len(duplicates),
            errors=errors
        )

    def parse_csv(self, path: Path) -> list[MarketEvent]:
        events = []
        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    event = MarketEvent(
                        event_id=str(uuid.uuid4()),
                        event_type=MarketEventType(row.get('event_type', 'UNKNOWN')),
                        scope=MarketEventScope(row.get('scope', 'UNKNOWN')),
                        status=MarketEventStatus(row.get('status', 'UNKNOWN')),
                        title=row.get('title', ''),
                        symbol=row.get('symbol') or None,
                        sector=row.get('sector') or None,
                        index_name=row.get('index_name') or None,
                        event_date=datetime.fromisoformat(row['event_date']),
                        start_at=datetime.fromisoformat(row['start_at']) if row.get('start_at') else None,
                        end_at=datetime.fromisoformat(row['end_at']) if row.get('end_at') else None,
                        severity=EventSeverity(row.get('severity', 'UNKNOWN')),
                        source=row.get('source', 'CSV_IMPORT'),
                        source_ref=row.get('source_ref') or None,
                        confidence=float(row['confidence']) if row.get('confidence') else None,
                        tags=row.get('tags', '').split(',') if row.get('tags') else []
                    )
                    events.append(event)
                except Exception as e:
                    # Skip broken rows
                    pass
        return events

    def parse_json(self, path: Path) -> list[MarketEvent]:
        events = []
        with open(path, mode='r', encoding='utf-8') as f:
            data = json.load(f)
            for row in data:
                try:
                    row['event_id'] = str(uuid.uuid4())
                    row['event_date'] = datetime.fromisoformat(row['event_date'])
                    if row.get('start_at'):
                        row['start_at'] = datetime.fromisoformat(row['start_at'])
                    if row.get('end_at'):
                        row['end_at'] = datetime.fromisoformat(row['end_at'])

                    event = MarketEvent(**row)
                    events.append(event)
                except Exception as e:
                    pass
        return events

    def validate_events(self, events: list[MarketEvent]) -> list[str]:
        errors = []
        for i, ev in enumerate(events):
            if not ev.title:
                errors.append(f"Row {i}: Title is empty")
        return errors

    def deduplicate_events(self, events: list[MarketEvent]) -> tuple[list[MarketEvent], list[MarketEvent]]:
        seen = set()
        valid = []
        duplicates = []

        for ev in events:
            if not ev.title:
                continue

            key = f"{ev.symbol}_{ev.event_type}_{ev.event_date.date()}_{ev.title}"
            if key in seen:
                duplicates.append(ev)
            else:
                seen.add(key)
                valid.append(ev)

        return valid, duplicates
