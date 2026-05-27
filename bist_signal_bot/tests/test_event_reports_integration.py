import pytest
from datetime import datetime

from bist_signal_bot.events.models import MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity, EventCalendarSnapshot
from bist_signal_bot.events.calendar import EventCalendar
from bist_signal_bot.events.reporting import format_event_calendar_report_markdown

def test_daily_report_includes_events():
    event = MarketEvent(
        event_id="test-1",
        event_type=MarketEventType.EARNINGS,
        scope=MarketEventScope.SYMBOL,
        status=MarketEventStatus.CONFIRMED,
        title="THYAO Earnings",
        symbol="THYAO",
        event_date=datetime.now(),
        severity=EventSeverity.HIGH,
        source="TEST"
    )

    calendar = EventCalendar()
    calendar.add_event(event)
    snapshot = calendar.snapshot()

    md = format_event_calendar_report_markdown(snapshot, [event])

    assert "THYAO Earnings" in md
    assert "High Severity Events: 1" in md
