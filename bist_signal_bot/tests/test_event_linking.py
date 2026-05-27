import pytest
from datetime import datetime

from bist_signal_bot.events.models import MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity, EventRiskAssessment, EventRiskDecision
from bist_signal_bot.events.linking import EventLinker

def test_link_events_to_signal():
    event = MarketEvent(
        event_id="e1",
        event_type=MarketEventType.EARNINGS,
        scope=MarketEventScope.SYMBOL,
        status=MarketEventStatus.CONFIRMED,
        title="Earnings",
        symbol="ASELS",
        event_date=datetime.now(),
        severity=EventSeverity.HIGH,
        source="test"
    )

    assessment = EventRiskAssessment(
        assessment_id="a1",
        symbol="ASELS",
        strategy_name="test_strat",
        signal_id="sig1",
        assessed_at=datetime.now(),
        matching_events=[event],
        severity=EventSeverity.HIGH,
        decision=EventRiskDecision.WARN
    )

    linker = EventLinker()
    links = linker.link_events_to_signal({"signal_id": "sig1", "symbol": "ASELS"}, assessment)

    assert len(links) == 1
    assert links[0].linked_object_id == "sig1"
    assert links[0].linked_object_type == "SIGNAL"
    assert links[0].event_id == "e1"
