import pytest
from datetime import datetime

from bist_signal_bot.events.models import MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity
from bist_signal_bot.events.calendar import EventCalendar
from bist_signal_bot.events.windows import EventWindowBuilder
from bist_signal_bot.events.blackout import BlackoutPolicyManager
from bist_signal_bot.events.risk import EventRiskEngine

def test_evidence_card_includes_event_risk():
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

    assessment = engine.assess_symbol("THYAO")

    # Simulated evidence card dict
    card = {
        "symbol": "THYAO",
        "event_risk": {
            "score": assessment.risk_score,
            "decision": assessment.decision.value,
            "upcoming_events": [e.title for e in assessment.matching_events]
        }
    }

    assert card["event_risk"]["decision"] in ["REQUIRE_REVIEW", "RESEARCH_BLOCK", "WARN", "WATCH"]
    assert "THYAO Earnings" in card["event_risk"]["upcoming_events"]
