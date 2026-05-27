import pytest
from datetime import datetime

from bist_signal_bot.events.models import MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity
from bist_signal_bot.events.calendar import EventCalendar
from bist_signal_bot.events.windows import EventWindowBuilder
from bist_signal_bot.events.blackout import BlackoutPolicyManager
from bist_signal_bot.events.risk import EventRiskEngine

def test_portfolio_event_concentration():
    # Simulate a portfolio builder checking event risk
    event1 = MarketEvent(
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

    event2 = MarketEvent(
        event_id="test-2",
        event_type=MarketEventType.MACRO_DATA,
        scope=MarketEventScope.MARKET,
        status=MarketEventStatus.CONFIRMED,
        title="CPI Release",
        event_date=datetime.now(),
        severity=EventSeverity.HIGH,
        source="TEST"
    )

    calendar = EventCalendar()
    calendar.add_event(event1)
    calendar.add_event(event2)

    engine = EventRiskEngine(calendar, EventWindowBuilder(), BlackoutPolicyManager())

    assessments = engine.assess_portfolio(["THYAO", "ASELS", "GARAN"])

    # THYAO has both earnings and macro
    assert assessments["THYAO"].risk_score > assessments["ASELS"].risk_score
    # ASELS and GARAN have macro
    assert assessments["ASELS"].risk_score > 0
