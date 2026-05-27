import pytest
from datetime import datetime

from bist_signal_bot.events.models import MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity
from bist_signal_bot.events.calendar import EventCalendar
from bist_signal_bot.events.windows import EventWindowBuilder
from bist_signal_bot.events.blackout import BlackoutPolicyManager
from bist_signal_bot.events.risk import EventRiskEngine

def test_scanner_metadata_production():
    # Mocking what scanner engine does with event risk checking

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

    # Simulate scanner assessing a signal
    assessment = engine.assess_signal({"symbol": "THYAO", "signal_id": "sig-1"})

    assert assessment.risk_score > 0
    assert assessment.decision.value != "ALLOW"
