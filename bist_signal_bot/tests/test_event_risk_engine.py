import pytest
from datetime import datetime

from bist_signal_bot.events.models import MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity, EventRiskDecision
from bist_signal_bot.events.calendar import EventCalendar
from bist_signal_bot.events.windows import EventWindowBuilder
from bist_signal_bot.events.blackout import BlackoutPolicyManager
from bist_signal_bot.events.risk import EventRiskEngine

def test_risk_engine_no_events():
    engine = EventRiskEngine(EventCalendar(), EventWindowBuilder(), BlackoutPolicyManager())
    assessment = engine.assess_symbol("MISSING", as_of=datetime.now())

    assert assessment.risk_score == 0.0
    assert assessment.decision == EventRiskDecision.ALLOW

def test_risk_engine_with_critical_event():
    event = MarketEvent(
        event_id="test-critical",
        event_type=MarketEventType.TRADING_HALT,
        scope=MarketEventScope.SYMBOL,
        status=MarketEventStatus.CONFIRMED,
        title="Trading Halt",
        symbol="HALT",
        event_date=datetime.now(),
        severity=EventSeverity.CRITICAL,
        source="TEST"
    )

    calendar = EventCalendar()
    calendar.add_event(event)
    engine = EventRiskEngine(calendar, EventWindowBuilder(), BlackoutPolicyManager())

    assessment = engine.assess_symbol("HALT", as_of=event.event_date)

    assert assessment.risk_score > 40.0
    assert assessment.decision in [EventRiskDecision.REQUIRE_REVIEW, EventRiskDecision.RESEARCH_BLOCK, EventRiskDecision.WARN]
