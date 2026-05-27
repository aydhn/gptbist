import pytest
from datetime import datetime
import uuid

from bist_signal_bot.events.models import EventCalendarSnapshot
from bist_signal_bot.events.reporting import format_event_calendar_report_markdown

def test_format_event_calendar_report_markdown():
    snapshot = EventCalendarSnapshot(
        snapshot_id=str(uuid.uuid4()),
        created_at=datetime.now(),
        events_count=10,
        upcoming_count=2,
        high_severity_count=1
    )

    md = format_event_calendar_report_markdown(snapshot, upcoming=[], assessments=[])

    assert "# Event Calendar Report" in md
    assert "Total Events: 10" in md
    assert "Market event record is operational research metadata only" in md
