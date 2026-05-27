import pytest
from datetime import datetime

from bist_signal_bot.events.models import MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity
from bist_signal_bot.events.calendar import EventCalendar
from bist_signal_bot.events.windows import EventWindowBuilder
from bist_signal_bot.events.blackout import BlackoutPolicyManager
from bist_signal_bot.events.risk import EventRiskEngine

def test_validation_cohorts():
    event = MarketEvent(
        event_id="test-1",
        event_type=MarketEventType.MACRO_DATA,
        scope=MarketEventScope.MARKET,
        status=MarketEventStatus.CONFIRMED,
        title="Macro",
        event_date=datetime.now(),
        severity=EventSeverity.HIGH,
        source="TEST"
    )

    calendar = EventCalendar()
    calendar.add_event(event)
    engine = EventRiskEngine(calendar, EventWindowBuilder(), BlackoutPolicyManager())

    # Macro event affects all symbols
    assessment = engine.assess_symbol("ANY_SYMBOL")

    assert assessment.risk_score > 0
    assert assessment.severity == EventSeverity.HIGH
