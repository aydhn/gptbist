import pytest
from datetime import datetime, timedelta

from bist_signal_bot.events.models import MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity, BlackoutPolicy, EventRiskDecision
from bist_signal_bot.events.windows import EventWindowBuilder

def test_build_window_with_policy():
    event = MarketEvent(
        event_id="test-1",
        event_type=MarketEventType.EARNINGS,
        scope=MarketEventScope.SYMBOL,
        status=MarketEventStatus.SCHEDULED,
        title="THYAO Earnings",
        symbol="THYAO",
        event_date=datetime(2024, 5, 15),
        severity=EventSeverity.HIGH,
        source="TEST"
    )

    policy = BlackoutPolicy(
        policy_id="test-policy",
        name="Test",
        event_types=[MarketEventType.EARNINGS],
        pre_event_days=1,
        post_event_days=1,
        severity_threshold=EventSeverity.MEDIUM,
        decision=EventRiskDecision.WARN
    )

    builder = EventWindowBuilder()
    windows = builder.build_windows([event], [policy])

    assert len(windows) == 1
    w = windows[0]
    assert w.starts_at == datetime(2024, 5, 14)
    assert w.ends_at == datetime(2024, 5, 16)
    assert w.decision == EventRiskDecision.WARN
