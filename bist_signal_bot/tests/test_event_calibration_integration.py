import pytest
from datetime import datetime

from bist_signal_bot.events.models import MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity
from bist_signal_bot.events.calendar import EventCalendar
from bist_signal_bot.events.windows import EventWindowBuilder
from bist_signal_bot.events.blackout import BlackoutPolicyManager
from bist_signal_bot.events.risk import EventRiskEngine

def test_calibration_cohort_metadata():
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
    engine = EventRiskEngine(calendar, EventWindowBuilder(), BlackoutPolicyManager())

    # Calibration outcomes check if they happened during an event window
    assessment = engine.assess_symbol("THYAO")

    assert assessment.matching_windows != []
    assert assessment.severity == EventSeverity.HIGH
